from dataclasses import dataclass
from typing import Protocol

import httpx


@dataclass(frozen=True)
class ProviderReply:
    text: str
    model: str


class ProviderAdapter(Protocol):
    name: str

    async def complete(
        self,
        *,
        client: httpx.AsyncClient,
        api_base: str,
        api_key: str,
        model: str,
        system_prompt: str,
        messages: list[dict[str, str]],
    ) -> ProviderReply: ...
