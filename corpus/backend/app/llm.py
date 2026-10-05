"""Every AI call goes through call_llm(). Providers: 'mock' (offline) or 'anthropic' (set ANTHROPIC_API_KEY).
The anthropic path is written but not tested here; try it with your own key."""
import httpx

from . import config

MOCK_REPLY = '{"note": "mock llm reply"}'


async def call_llm(system: str, prompt: str, json_mode: bool = False) -> str:
    if config.LLM_PROVIDER == "mock":
        return MOCK_REPLY
    if config.LLM_PROVIDER == "anthropic":
        if json_mode:
            system += "\nReply with valid JSON only, no other text."
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": config.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"},
                json={"model": config.LLM_MODEL, "max_tokens": 1000, "system": system,
                      "messages": [{"role": "user", "content": prompt}]})
            r.raise_for_status()
            return r.json()["content"][0]["text"]
    raise NotImplementedError(f"LLM provider '{config.LLM_PROVIDER}' is not supported")
