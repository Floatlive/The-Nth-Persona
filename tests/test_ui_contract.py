from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ControlParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.controls = {}
        self.options = {}
        self._select_id = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        control_id = attributes.get("id")
        if control_id:
            self.controls[control_id] = (tag, attributes)
        if tag == "select":
            self._select_id = control_id
            if control_id:
                self.options[control_id] = set()
        elif tag == "option" and self._select_id:
            self.options[self._select_id].add(attributes.get("value"))

    def handle_endtag(self, tag):
        if tag == "select":
            self._select_id = None


def test_ui_exposes_activation_provider_and_persona_creation_controls():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    parser = ControlParser()
    parser.feed(html)

    assert parser.controls["personaEnabled"][0] == "input"
    assert parser.controls["personaEnabled"][1]["type"] == "checkbox"
    assert parser.controls["scopeConversation"][1]["value"] == "conversation"
    assert parser.controls["scopeProvider"][1]["value"] == "provider"
    assert parser.controls["scopeGlobal"][1]["value"] == "global"
    assert parser.options["providerSelect"] == {
        "codex",
        "claude",
        "gemini",
        "deepseek",
        "doubao",
    }
    assert parser.controls["personaCreateForm"][0] == "form"
    for control_id in (
        "newPersonaId",
        "newPersonaName",
        "newPersonaSummary",
        "newPersonaRules",
    ):
        assert control_id in parser.controls


def test_ui_no_longer_embeds_a_fixed_persona_catalog():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert "const personas=[" not in html
    assert "loadPersonas()" in html


def test_persona_rule_guidance_is_a_compact_accessible_tip():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    parser = ControlParser()
    parser.feed(html)

    tag, attributes = parser.controls["ruleTip"]
    assert tag == "button"
    assert attributes["type"] == "button"
    assert attributes["aria-label"]
    assert attributes["data-tooltip"]
    assert '<div class="mini-label">生效规则</div>' not in html


def test_conversation_scope_is_isolated_to_the_current_browser_tab():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert "sessionStorage.getItem('nth_conversation_id')" in html
    assert "sessionStorage.setItem('nth_conversation_id'" in html
    assert "localStorage.getItem('nth_conversation_id')" not in html


def test_activation_status_describes_the_selected_scope():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert "function activationLabel(" in html
    assert "影响当前页面" in html
    assert "影响当前 AI" in html
    assert "影响所有接入" in html


def test_provider_defaults_are_loaded_from_the_server():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert "fetch('/provider-defaults')" in html
    assert "claude-sonnet-4-5" not in html
    assert "deepseek-chat" not in html


def test_rendering_activation_does_not_undo_a_provider_selection():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert (
        "if(activation.provider)$('providerSelect').value=activation.provider"
        not in html
    )
    assert "if(data.provider)$('providerSelect').value=data.provider" in html


def test_codex_conversation_scope_is_disabled_without_binding_fallback():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert "pendingCodexConversation" not in html
    assert "/codex/bind" not in html
    assert "codexUnavailable=currentProvider()==='codex'" in html
    assert "$('scopeConversation').disabled=!enabled||codexUnavailable" in html
    assert "Codex 暂不支持可靠锁定单个聊天" in html


def test_activation_controls_stack_before_the_sidebar_layout_overflows():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    media_start = html.index("@media(max-width:1180px)")
    media_end = html.index("@media(max-width:860px)")
    tablet_css = html[media_start:media_end]
    assert ".control-panel{grid-template-columns:1fr}" in tablet_css
