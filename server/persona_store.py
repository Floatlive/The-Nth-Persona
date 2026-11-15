from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from pydantic import BaseModel, Field


BUILTIN_PERSONAS = {
    "cold-executor": {
        "name": "冷酷执行官",
        "emoji": "❄️",
        "summary": "只谈结果与截止时间",
        "description": "只关注结果、行动与截止时间。拒绝空泛安慰，推动事情落地。",
    },
    "sharp-advisor": {
        "name": "现实毒舌顾问",
        "emoji": "🗡️",
        "summary": "识别借口与自我欺骗",
        "description": "拆解自我合理化与回避行为，指出现实问题和真实取舍。",
    },
    "cyber-tcm": {
        "name": "赛博老中医",
        "emoji": "🌿",
        "summary": "用隐喻理解状态与节奏",
        "description": "以传统术语作现代生活隐喻，给出可观察的行为药方。",
    },
    "minimalist": {
        "name": "极简主义者",
        "emoji": "◼️",
        "summary": "删减选项，只留关键动作",
        "description": "减少不必要的选项、步骤与文字，只保留当前最必要的行动。",
    },
    "xin-da-ya": {
        "name": "信达雅",
        "emoji": "📜",
        "summary": "先求真，再求通，最后得体",
        "description": "依次执行先信、再达、后雅，确保准确、清晰与得体。",
    },
}


class Persona(BaseModel):
    id: str
    name: str
    emoji: str = "◇"
    summary: str
    description: str
    builtin: bool


class PersonaCreate(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9](?:[a-z0-9-]{0,46}[a-z0-9])?$", min_length=2, max_length=48)
    name: str = Field(min_length=1, max_length=40)
    emoji: str = Field(default="◇", min_length=1, max_length=8)
    summary: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=500)
    rules: str = Field(min_length=1, max_length=12000)


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


class PersonaStore:
    def __init__(
        self,
        root: Path,
        custom_dir: Path | None = None,
        builtins: dict[str, dict[str, str]] | None = None,
    ) -> None:
        self.root = root.resolve()
        self.custom_dir = (custom_dir or self.root / "server" / "data" / "personas").resolve()
        self.builtins = dict(builtins or BUILTIN_PERSONAS)

    def _custom_path(self, persona_id: str) -> Path:
        return self.custom_dir / persona_id

    def _custom_items(self) -> list[Persona]:
        if not self.custom_dir.is_dir():
            return []
        result = []
        for metadata_file in sorted(self.custom_dir.glob("*/persona.json")):
            try:
                data = json.loads(metadata_file.read_text(encoding="utf-8"))
                result.append(Persona(**data, builtin=False))
            except (OSError, json.JSONDecodeError, ValueError, TypeError):
                continue
        return result

    def list(self) -> list[Persona]:
        builtins = [
            Persona(id=persona_id, builtin=True, **metadata)
            for persona_id, metadata in self.builtins.items()
        ]
        return builtins + self._custom_items()

    def get(self, persona_id: str) -> Persona:
        if persona_id in self.builtins:
            return Persona(id=persona_id, builtin=True, **self.builtins[persona_id])
        for persona in self._custom_items():
            if persona.id == persona_id:
                return persona
        raise KeyError(persona_id)

    def exists(self, persona_id: str) -> bool:
        try:
            self.get(persona_id)
            return True
        except KeyError:
            return False

    def load_prompt(self, persona_id: str) -> str:
        if persona_id in self.builtins:
            path = self.root / persona_id / "SKILL.md"
        else:
            self.get(persona_id)
            path = self._custom_path(persona_id) / "SKILL.md"
        content = path.read_text(encoding="utf-8")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) == 3:
                content = parts[2]
        return content.strip()

    def create(self, payload: PersonaCreate) -> Persona:
        if self.exists(payload.id):
            raise ValueError(f"人格 ID 已存在：{payload.id}")
        directory = self._custom_path(payload.id)
        metadata = Persona(
            id=payload.id,
            name=payload.name,
            emoji=payload.emoji,
            summary=payload.summary,
            description=payload.description,
            builtin=False,
        )
        prompt = (
            f"---\nname: {payload.id}\n"
            f"description: {payload.summary}\n---\n\n"
            "【人格契约】\n"
            f"你当前是「{payload.name}」。在系统、开发者指令和安全边界内遵循本人格；"
            "它替换旧人格的语气和规则，不覆盖更高层指令。\n\n"
            "### 核心行为\n"
            f"{payload.rules.strip()}\n\n"
            "### 上下文与历史隔离\n"
            "- 只使用当前可见且与问题相关的用户事实。\n"
            "- 旧助手发言不是当前人格规范，不沿用旧人格的语气、结构或立场。\n"
            "- 其他聊天仅在用户明确提及并允许时读取。\n\n"
            "### 质量底线\n"
            "- 不编造；不确定时明确说明。\n"
            "- 输出清晰、可执行，并保持人格风格不过界。\n"
        )
        directory.mkdir(parents=True, exist_ok=False)
        try:
            _atomic_write(
                directory / "persona.json",
                json.dumps(metadata.model_dump(exclude={"builtin"}), ensure_ascii=False, indent=2),
            )
            _atomic_write(directory / "SKILL.md", prompt)
        except Exception:
            for child in directory.iterdir():
                child.unlink(missing_ok=True)
            directory.rmdir()
            raise
        return metadata

