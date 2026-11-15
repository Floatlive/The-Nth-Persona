import asyncio
import json

import httpx
import pytest

from server.providers import get_provider


def run_adapter(provider_name, response_body, *, api_base="https://example.test/v1"):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=response_body)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await get_provider(provider_name).complete(
                client=client,
                api_base=api_base,
                api_key="secret-key",
                model="model-1",
                system_prompt="PERSONA RULE",
                messages=[
                    {"role": "user", "content": "问题"},
                    {"role": "assistant", "content": "回答"},
                ],
            )

    reply = asyncio.run(run())
    return captured, reply


@pytest.mark.parametrize("provider_name", ["deepseek", "doubao", "openai"])
def test_openai_compatible_providers_send_system_message(provider_name):
    captured, reply = run_adapter(
        provider_name,
        {"choices": [{"message": {"content": "兼容回复"}}]},
    )

    assert captured["request"].url.path.endswith("/chat/completions")
    assert captured["request"].headers["authorization"] == "Bearer secret-key"
    assert captured["body"]["messages"][0] == {
        "role": "system",
        "content": "PERSONA RULE",
    }
    assert reply.text == "兼容回复"


def test_claude_uses_top_level_system_and_anthropic_headers():
    captured, reply = run_adapter(
        "claude",
        {"content": [{"type": "text", "text": "Claude 回复"}]},
    )

    assert captured["request"].url.path.endswith("/messages")
    assert captured["request"].headers["x-api-key"] == "secret-key"
    assert captured["request"].headers["anthropic-version"] == "2023-06-01"
    assert captured["body"]["system"] == "PERSONA RULE"
    assert captured["body"]["messages"][0]["role"] == "user"
    assert reply.text == "Claude 回复"


def test_gemini_uses_system_instruction_and_model_role():
    captured, reply = run_adapter(
        "gemini",
        {"candidates": [{"content": {"parts": [{"text": "Gemini 回复"}]}}]},
        api_base="https://generativelanguage.googleapis.com/v1beta",
    )

    assert captured["request"].url.path.endswith(
        "/models/model-1:generateContent"
    )
    assert captured["request"].headers["x-goog-api-key"] == "secret-key"
    assert captured["body"]["system_instruction"]["parts"] == [
        {"text": "PERSONA RULE"}
    ]
    assert captured["body"]["contents"][1]["role"] == "model"
    assert reply.text == "Gemini 回复"


def test_adapter_omits_system_field_when_persona_is_disabled():
    captured, _reply = run_adapter(
        "claude",
        {"content": [{"type": "text", "text": "普通回复"}]},
    )
    assert "system" in captured["body"]

    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200, json={"content": [{"type": "text", "text": "普通回复"}]}
        )

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            await get_provider("claude").complete(
                client=client,
                api_base="https://example.test/v1",
                api_key="secret-key",
                model="model-1",
                system_prompt="",
                messages=[{"role": "user", "content": "问题"}],
            )

    asyncio.run(run())
    assert "system" not in captured["body"]
