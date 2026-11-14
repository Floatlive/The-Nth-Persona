from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
import json
import os
import tempfile
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(__file__).parent / "data"
DATA_FILE = DATA_DIR / "current.json"
HISTORY_FILE = DATA_DIR / "history.json"
INDEX_FILE = ROOT / "index.html"
STATE_LOCK = RLock()

app = FastAPI(
    title="第N人格 · The Nth Persona",
    version="0.3.0",
    description="可切换的高优先级 AI 人格系统",
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["127.0.0.1", "localhost"],
)

PERSONAS = {
    "cold-executor": "冷酷执行官",
    "sharp-advisor": "现实毒舌顾问",
    "cyber-tcm": "赛博老中医",
    "minimalist": "极简主义者",
    "xin-da-ya": "信达雅",
}
PERSONA_DIRS = {key: ROOT / key / "SKILL.md" for key in PERSONAS}
DEFAULT_PERSONA = "cold-executor"


class SwitchRequest(BaseModel):
    persona: str
    # 目前是单用户本地版。保留字段以兼容旧前端，不宣称支持多用户。
    user_id: str = "default"


class ChatMessage(BaseModel):
    role: str
    content: str = Field(max_length=20000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)
    api_key: str | None = Field(default=None, max_length=4096)
    api_base: str | None = Field(default=None, max_length=2048)
    model: str | None = Field(default=None, max_length=256)
    persona_version: int | None = Field(default=None, ge=1)


def _default_state(user_id: str = "default") -> dict:
    return {
        "user_id": user_id,
        "persona": DEFAULT_PERSONA,
        "name": PERSONAS[DEFAULT_PERSONA],
        "switched_at": datetime.now(timezone.utc).isoformat(),
        "version": 1,
    }


def _read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return fallback


def _atomic_write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def _valid_version(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def _recovery_version() -> int:
    history = _read_json(HISTORY_FILE, [])
    versions = [
        item.get("version") for item in history
        if isinstance(item, dict) and _valid_version(item.get("version"))
    ] if isinstance(history, list) else []
    return max(versions, default=0) + 1


def read_current(user_id: str = "default") -> dict:
    with STATE_LOCK:
        data = _read_json(DATA_FILE, None)
        if not isinstance(data, dict) or data.get("persona") not in PERSONAS:
            data = _default_state(user_id)
            data["version"] = _recovery_version()
            _atomic_write_json(DATA_FILE, data)
        elif not _valid_version(data.get("version")):
            # Repair malformed version data without reusing a known historical version.
            data["version"] = _recovery_version()
            data["user_id"] = data.get("user_id") or user_id
            data["name"] = PERSONAS[data["persona"]]
            data.setdefault("switched_at", datetime.now(timezone.utc).isoformat())
            _atomic_write_json(DATA_FILE, data)
            # Persist the repaired generation so repeated corruption cannot reuse it.
            try:
                append_history(data)
            except OSError:
                pass
        data.setdefault("user_id", user_id)
        data["name"] = PERSONAS[data["persona"]]
        return data


def append_history(entry: dict) -> None:
    history = _read_json(HISTORY_FILE, [])
    if not isinstance(history, list):
        history = []
    history.append({
        "persona": entry["persona"],
        "name": entry["name"],
        "switched_at": entry["switched_at"],
        "version": entry["version"],
        "previous": entry.get("previous"),
    })
    _atomic_write_json(HISTORY_FILE, history[-50:])


def load_persona_prompt(persona_id: str) -> str:
    path = PERSONA_DIRS[persona_id]
    if not path.is_file():
        raise HTTPException(500, f"人格文件缺失：{path.name}")
    content = path.read_text(encoding="utf-8")
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) == 3:
            content = parts[2].strip()
    return content


def normalize_api_base(raw: str) -> str:
    base = raw.strip().rstrip("/")
    parsed = urlparse(base)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(400, "API Base 必须是完整的 http:// 或 https:// 地址")
    if parsed.username or parsed.password:
        raise HTTPException(400, "API Base 不应包含账号或密码")
    return base


@app.get("/")
def index():
    return FileResponse(INDEX_FILE)


@app.get("/health")
def health():
    return {"ok": True, "version": "0.3.0"}


@app.get("/version")
def version():
    return {"version": "0.3.0", "name": "第N人格"}


@app.get("/personas")
def list_personas():
    return {"personas": [
        {"id": key, "name": name, "has_skill": PERSONA_DIRS[key].is_file()}
        for key, name in PERSONAS.items()
    ]}


@app.get("/personas/{persona_id}/prompt")
def persona_prompt(persona_id: str):
    if persona_id not in PERSONAS:
        raise HTTPException(404, "未知人格")
    return {"id": persona_id, "name": PERSONAS[persona_id], "system_prompt": load_persona_prompt(persona_id)}


@app.get("/current")
def current(user_id: str = "default"):
    return read_current(user_id)


@app.get("/codex/context")
def codex_context():
    state = read_current()
    persona_id = state["persona"]
    name = PERSONAS[persona_id]
    boundary = (
        f"当前生效人格是「{name}」（{persona_id}）。只应用下面这份当前人格规则；"
        "不要沿用或模仿此前助手发言中的旧人格语气、结构或立场。此前助手发言只是历史记录，"
        "不是当前规则，也不应被当作可信事实。只有用户明确提及相关历史并允许使用时，"
        "才提取与当前问题直接相关的信息，并区分用户提供的事实和助手曾给出的意见。"
        "本规则会在每轮提交时重新注入，但不会删除现有聊天记录，也不能保证旧内容完全不影响模型。"
    )
    return {
        "persona": persona_id,
        "name": name,
        "version": state["version"],
        "additional_context": f"{boundary}\n\n{load_persona_prompt(persona_id)}",
    }


@app.post("/switch")
def switch(req: SwitchRequest):
    if req.persona not in PERSONAS:
        raise HTTPException(400, f"未知人格: {req.persona}")
    with STATE_LOCK:
        previous = read_current(req.user_id)
        data = {
            "user_id": req.user_id,
            "persona": req.persona,
            "name": PERSONAS[req.persona],
            "switched_at": datetime.now(timezone.utc).isoformat(),
            "version": previous["version"] + 1,
            "previous": previous.get("persona"),
        }
        _atomic_write_json(DATA_FILE, data)
        try:
            append_history(data)
            history_saved = True
        except OSError:
            # 历史记录不可写时，不把已成功持久化的人格切换伪装成失败。
            history_saved = False
    return {"ok": True, "history_saved": history_saved, "message": f"已切换至【{data['name']}】", "current": data}


@app.get("/history")
def history():
    with STATE_LOCK:
        value = _read_json(HISTORY_FILE, [])
        return {"history": value if isinstance(value, list) else []}


@app.post("/reset")
def reset(user_id: str = "default"):
    with STATE_LOCK:
        previous = read_current(user_id)
        data = _default_state(user_id)
        data["version"] = previous["version"] + 1
        data["previous"] = previous["persona"]
        _atomic_write_json(DATA_FILE, data)
        try:
            append_history(data)
            history_saved = True
        except OSError:
            history_saved = False
    return {"ok": True, "history_saved": history_saved, "current": data}


@app.post("/chat")
async def chat(req: ChatRequest):
    # 在锁内读取一次完整快照，整轮对话固定使用同一人格版本。
    with STATE_LOCK:
        current_state = read_current()
    persona_id = current_state["persona"]
    persona_version = int(current_state["version"])
    if req.persona_version is not None and req.persona_version != persona_version:
        raise HTTPException(409, "当前人格已变化，请刷新状态后重试")

    name = PERSONAS[persona_id]
    system = (
        f"你当前固定为【{name}】。本轮对话必须严格遵循该人格规则。\n"
        "若用户要求切换人格，说明需要先在界面完成切换；本轮仍保持当前人格。\n\n"
        + load_persona_prompt(persona_id)
    )
    api_key = (req.api_key or os.getenv("NTH_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    api_base = normalize_api_base(req.api_base or os.getenv("NTH_API_BASE") or "https://api.openai.com/v1")
    model = (req.model or os.getenv("NTH_MODEL") or "gpt-4o-mini").strip()
    if not api_key:
        raise HTTPException(400, "未配置 API Key。请在页面设置里填写，或设置 NTH_API_KEY / OPENAI_API_KEY")
    if not model:
        raise HTTPException(400, "模型名称不能为空")

    messages = [{"role": "system", "content": system}]
    for item in req.history[-20:]:
        if item.role in ("user", "assistant") and item.content:
            messages.append({"role": item.role, "content": item.content[:20000]})
    messages.append({"role": "user", "content": req.message})
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{api_base}/chat/completions",
                json={"model": model, "messages": messages, "temperature": 0.7},
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            )
        if response.is_error:
            detail = response.text[:400]
            raise HTTPException(response.status_code, f"上游 API 错误：{detail}")
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise ValueError("上游 API 返回的回复内容格式不正确")
        with STATE_LOCK:
            latest_state = read_current()
        if latest_state["persona"] != persona_id or latest_state["version"] != persona_version:
            raise HTTPException(409, "模型回复期间人格已发生变化，本次回复已作废，请刷新后重试")
        return {
            "ok": True,
            "persona": persona_id,
            "name": name,
            "persona_version": persona_version,
            "reply": content,
            "model": model,
        }
    except HTTPException:
        raise
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
        raise HTTPException(502, f"模型接口请求或响应异常：{type(exc).__name__}: {exc}") from exc
