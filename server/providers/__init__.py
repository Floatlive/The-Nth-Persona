from server.providers.base import ProviderAdapter, ProviderReply
from server.providers.claude import ClaudeAdapter
from server.providers.gemini import GeminiAdapter
from server.providers.openai_compatible import OpenAICompatibleAdapter


_PROVIDERS: dict[str, ProviderAdapter] = {
    "openai": OpenAICompatibleAdapter("openai"),
    "deepseek": OpenAICompatibleAdapter("deepseek"),
    "doubao": OpenAICompatibleAdapter("doubao"),
    "claude": ClaudeAdapter(),
    "gemini": GeminiAdapter(),
}


def get_provider(name: str) -> ProviderAdapter:
    try:
        return _PROVIDERS[name]
    except KeyError as exc:
        raise ValueError(f"不支持的 AI：{name}") from exc


__all__ = ["ProviderAdapter", "ProviderReply", "get_provider"]
