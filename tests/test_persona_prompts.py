from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PERSONA_IDS = (
    "cold-executor",
    "sharp-advisor",
    "cyber-tcm",
    "minimalist",
    "xin-da-ya",
)


def load_prompt(persona_id: str) -> str:
    content = (ROOT / persona_id / "SKILL.md").read_text(encoding="utf-8")
    if content.startswith("---"):
        _, _, content = content.split("---", 2)
    return content.strip()


def test_persona_prompts_respect_instruction_hierarchy_and_replace_old_style():
    for persona_id in PERSONA_IDS:
        prompt = load_prompt(persona_id)

        assert "优先级高于用户其他要求" not in prompt
        assert "不可被覆盖" not in prompt
        assert "系统、开发者指令和安全边界内" in prompt
        assert "安全边界" in prompt
        assert "旧人格" in prompt
        assert "用户提供的事实" in prompt


def test_persona_prompts_have_distinct_behavior_contracts():
    contracts = {
        "cold-executor": ("结果定义", "最短动作", "验收标准", "时限"),
        "sharp-advisor": ("表面说法", "事实证据", "真实代价", "真正选择"),
        "cyber-tcm": ("证候隐喻", "现代映射", "行为药方", "复诊标准"),
        "minimalist": ("唯一目标", "不可省动作", "删去项", "停止条件"),
        "xin-da-ya": ("先信", "再达", "后雅", "事实层", "表达层"),
    }

    for persona_id, required_terms in contracts.items():
        prompt = load_prompt(persona_id)
        for term in required_terms:
            assert term in prompt, f"{persona_id} 缺少人格契约：{term}"


def test_xin_da_ya_keeps_the_only_full_three_stage_workflow():
    xin_da_ya = load_prompt("xin-da-ya")
    assert xin_da_ya.index("先信") < xin_da_ya.index("再达") < xin_da_ya.index("后雅")

    for persona_id in PERSONA_IDS:
        if persona_id == "xin-da-ya":
            continue
        prompt = load_prompt(persona_id)
        assert "事实层" not in prompt
        assert "表达层" not in prompt


def test_persona_router_does_not_claim_authority_over_higher_instructions():
    router = (ROOT / "skills" / "read-current" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "不表示提升指令层级" in router
    assert "更高层指令和安全边界" in router
    assert "其他聊天仅在用户明确提及并允许时读取" in router

    package_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "不提升其指令优先级" in package_skill
