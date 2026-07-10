"""
LLM client abstraction.

Every module that needs an LLM call (resume parsing, JD parsing, the
interview engine, evaluation, report generation) imports `get_llm_json`
from here instead of calling the OpenAI SDK directly. That means
swapping providers later (Anthropic, a local model, etc.) is a
one-file change.
"""

import json
from openai import OpenAI

from app.config import settings

_client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL)


def get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def get_llm_json(system_prompt: str, user_prompt: str) -> dict:
    """Call the configured LLM and parse its response as JSON.

    The system prompt should instruct the model to return ONLY raw JSON
    (no markdown fences, no commentary) for this to work reliably.
    """
    if settings.LLM_PROVIDER != "openai":
        raise NotImplementedError(
            f"LLM provider '{settings.LLM_PROVIDER}' is not implemented yet. "
            "Add a branch here when swapping providers."
        )

    client = get_openai_client()
    response = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    return json.loads(raw)
