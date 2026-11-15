from urllib.parse import quote

import httpx

from server.providers.base import ProviderReply


class GeminiAdapter:
    name = "gemini"

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
        contents = [
            {
                "role": "model" if item["role"] == "assistant" else "user",
                "parts": [{"text": item["content"]}],
            }
            for item in messages
        ]
        payload = {"contents": contents}
        if system_prompt:
            payload["system_instruction"] = {"parts": [{"text": system_prompt}]}
        response = await client.post(
            f"{api_base.rstrip('/')}/models/{quote(model, safe='')}:generateContent",
            json=payload,
            headers={
                "x-goog-api-key": api_key,
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        body = response.json()
        parts = body["candidates"][0]["content"]["parts"]
        text = "".join(
            part["text"] for part in parts if isinstance(part.get("text"), str)
        )
        if not text:
            raise ValueError("Gemini 返回的回复内容格式不正确")
        return ProviderReply(text=text, model=model)

