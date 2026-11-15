from dataclasses import dataclass


PROVIDERS = {"codex", "claude", "gemini", "deepseek", "doubao"}
SCOPES = {"off", "conversation", "provider", "global"}


@dataclass(frozen=True)
class ActivationDecision:
    active: bool
    reason: str


def resolve_activation(
    state: dict, provider: str, conversation_id: str | None = None
) -> ActivationDecision:
    if state.get("binding_pending"):
        return ActivationDecision(False, "binding_pending")
    if not state.get("enabled", True) or state.get("scope") == "off":
        return ActivationDecision(False, "disabled")
    scope = state.get("scope", "global")
    if scope == "global":
        return ActivationDecision(True, "global")
    if provider != state.get("provider"):
        return ActivationDecision(False, "provider_mismatch")
    if scope == "provider":
        return ActivationDecision(True, "provider")
    if scope == "conversation":
        expected = state.get("conversation_id")
        if expected and conversation_id and expected == conversation_id:
            return ActivationDecision(True, "conversation")
        return ActivationDecision(False, "conversation_mismatch")
    return ActivationDecision(False, "invalid_scope")
