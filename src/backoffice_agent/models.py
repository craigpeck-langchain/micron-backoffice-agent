"""Shared chat-model construction, routed through the LangSmith LLM Gateway
when BASE_URL is set (same pattern as the REI/banking-concierge demos)."""

from __future__ import annotations

import os

from langchain_openai import ChatOpenAI


def make_chat_model(*, temperature: float = 0.2) -> ChatOpenAI:
    model_name = os.getenv("BACKOFFICE_MODEL", "gpt-4o-mini")
    base_url = os.getenv("BASE_URL")
    if base_url:
        # Route through the LangSmith LLM Gateway: callers authenticate with
        # LC_GATEWAY_KEY, a machine/deployment-scoped service key
        # (lsv2_sk_...), separate from a personal workspace token.
        gateway_key = os.environ["LC_GATEWAY_KEY"]
        return ChatOpenAI(model=model_name, temperature=temperature, base_url=base_url, api_key=gateway_key)
    return ChatOpenAI(model=model_name, temperature=temperature)
