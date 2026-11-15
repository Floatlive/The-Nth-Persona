import httpx

from server.providers.base import ProviderReply


class ClaudeAdapter:
    name = "claude"

    async def complete(
        self,
        *,
        client: httpx.AsyncClient,
        api_base: str,
        api_key: str,
        model: str,
        system_prompt: str,
        messages: list[dict[str, str]],
    ) -> ProviderReply:
        payload = {
            "model": model,
            "max_tokens": 2048,
            "messages": messages,
        }
        if system_prompt:
            payload["system"] = system_prompt
        response = await client.post(
            f"{api_base.rstrip('/')}/messages",
            json=payload,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        body = response.json()
        text = "".join(
            part["text"]
            for part in body["content"]
            if part.get("type") == "text" and isinstance(part.get("text"), str)
        )
        if not text:
            raise ValueError("Claude 返回的回复内容格式不正确")
        return ProviderReply(text=text, model=model)
