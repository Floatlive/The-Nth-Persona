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
