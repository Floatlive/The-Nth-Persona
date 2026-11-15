import httpx

from server.providers.base import ProviderReply


class OpenAICompatibleAdapter:
    def __init__(self, name: str) -> None:
        self.name = name

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
        payload_messages = list(messages)
        if system_prompt:
            payload_messages.insert(0, {"role": "system", "content": system_prompt})
        response = await client.post(
            f"{api_base.rstrip('/')}/chat/completions",
            json={
                "model": model,
                "messages": payload_messages,
                "temperature": 0.7,
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        body = response.json()
        text = body["choices"][0]["message"]["content"]
        if not isinstance(text, str):
            raise ValueError("上游 API 返回的回复内容格式不正确")
        return ProviderReply(text=text, model=model)
