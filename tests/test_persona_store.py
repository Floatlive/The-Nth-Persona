import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from server.persona_store import PersonaCreate, PersonaStore


def make_store(tmp_path: Path) -> PersonaStore:
    root = tmp_path / "project"
    root.mkdir()
    built_in = root / "minimalist"
    built_in.mkdir()
    built_in.joinpath("SKILL.md").write_text(
        "---\nname: minimalist\n---\n\n【人格契约】\n只保留必要动作。",
        encoding="utf-8",
    )
    return PersonaStore(
        root=root,
        custom_dir=root / "server" / "data" / "personas",
        builtins={
            "minimalist": {
                "name": "极简主义者",
                "emoji": "◼",
                "summary": "只留关键动作",
                "description": "减少不必要步骤。",
            }
        },
    )


def test_store_lists_builtins_and_loads_prompt(tmp_path):
    store = make_store(tmp_path)

    personas = store.list()

    assert [item.id for item in personas] == ["minimalist"]
    assert personas[0].builtin is True
    assert store.load_prompt("minimalist") == "【人格契约】\n只保留必要动作。"


def test_custom_persona_is_readable_immediately_after_creation(tmp_path):
    store = make_store(tmp_path)

    created = store.create(
        PersonaCreate(
            id="clear-teacher",
            name="清晰教练",
            emoji="◎",
            summary="先澄清，再行动",
            description="把复杂问题拆成可验证步骤。",
            rules="先复述目标；再指出关键假设；最后给出下一步。",
        )
    )

    assert created.id == "clear-teacher"
    assert created.builtin is False
    assert store.get("clear-teacher").name == "清晰教练"
    prompt = store.load_prompt("clear-teacher")
    assert "当前是「清晰教练」" in prompt
    assert "先复述目标；再指出关键假设；最后给出下一步。" in prompt


def test_store_rejects_duplicate_or_builtin_ids(tmp_path):
    store = make_store(tmp_path)
    payload = PersonaCreate(
        id="minimalist",
        name="覆盖",
        summary="不允许",
        description="不应覆盖内置人格。",
        rules="无",
    )

    with pytest.raises(ValueError, match="已存在"):
        store.create(payload)


@pytest.mark.parametrize("persona_id", ["../escape", "A-B", "a_b", "a", "a/" + "b" * 48])
def test_persona_id_rejects_path_traversal_and_invalid_names(persona_id):
    with pytest.raises(ValidationError):
        PersonaCreate(
            id=persona_id,
            name="测试人格",
            summary="测试",
            description="测试描述",
            rules="测试规则",
        )


def test_store_ignores_custom_metadata_with_invalid_or_mismatched_id(tmp_path):
    store = make_store(tmp_path)
    custom_dir = store.custom_dir / "safe-folder"
    custom_dir.mkdir(parents=True)
    custom_dir.joinpath("persona.json").write_text(
        json.dumps(
            {
                "id": "../outside",
                "name": "损坏人格",
                "emoji": "◇",
                "summary": "不应载入",
                "description": "目录名和 ID 不一致。",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    custom_dir.joinpath("SKILL.md").write_text("不应读取", encoding="utf-8")

    assert [item.id for item in store.list()] == ["minimalist"]
    with pytest.raises(KeyError):
        store.get("../outside")


def test_store_rejects_custom_prompt_symlink_outside_persona_directory(
    monkeypatch, tmp_path
):
    store = make_store(tmp_path)
    created = store.create(
        PersonaCreate(
            id="safe-persona",
            name="安全人格",
            summary="只读自身规则",
            description="拒绝目录外规则。",
            rules="保持边界。",
        )
    )
    prompt_path = store.custom_dir / created.id / "SKILL.md"
    original_is_symlink = Path.is_symlink

    def fake_is_symlink(path):
        if path == prompt_path:
            return True
        return original_is_symlink(path)

    monkeypatch.setattr(Path, "is_symlink", fake_is_symlink)

    with pytest.raises(OSError, match="人格提示词路径不安全"):
        store.load_prompt(created.id)
