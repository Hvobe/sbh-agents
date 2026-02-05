"""
LLM Client
Abstraction Layer für OpenAI GPT
"""
from __future__ import annotations

import os
import json
import time
from dataclasses import dataclass
from openai import OpenAI
from dotenv import load_dotenv

from .config import DEFAULT_MODEL, FAST_MODEL, LLM_TIMEOUT_SECONDS
from .logger import llm_logger

load_dotenv()

_openai_client: OpenAI | None = None


def get_openai_client() -> OpenAI:
    """Gibt den OpenAI Client zurück (Singleton Pattern)"""
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY muss in .env gesetzt sein")
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def create_embedding(text: str, model: str = "text-embedding-3-small") -> list[float]:
    """Erstellt ein Embedding für den gegebenen Text"""
    client = get_openai_client()
    response = client.embeddings.create(model=model, input=text)
    return response.data[0].embedding


@dataclass
class LLMResponse:
    """Detaillierte Antwort von einem LLM-Call"""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    response_time_ms: int


def chat_completion(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    max_tokens: int = 500,
    temperature: float = 0.3,
    json_mode: bool = False
) -> str:
    """Führt eine Chat Completion durch (gibt nur String zurück)"""
    result = chat_completion_with_usage(messages, model, max_tokens, temperature, json_mode)
    return result.content


def chat_completion_with_usage(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    max_tokens: int = 500,
    temperature: float = 0.3,
    json_mode: bool = False
) -> LLMResponse:
    """Führt eine Chat Completion durch und gibt detaillierte Infos zurück"""
    client = get_openai_client()

    kwargs = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    kwargs["timeout"] = LLM_TIMEOUT_SECONDS

    start_time = time.time()
    response = client.chat.completions.create(**kwargs)
    response_time_ms = int((time.time() - start_time) * 1000)

    return LLMResponse(
        content=response.choices[0].message.content,
        model=model,
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
        response_time_ms=response_time_ms
    )


def parse_json_response(content: str, default: dict | None = None) -> dict:
    """
    Parst JSON aus einer LLM-Antwort mit Fallback.
    Entfernt automatisch ```json Codeblöcke wenn vorhanden.
    """
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    cleaned = content.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        llm_logger.warning(
            f"JSON parse failed after cleanup: {e}. "
            f"Content preview: {content[:200]}..."
        )
        return default or {"response": content, "suggestions": None, "escalate": False}


async def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str = FAST_MODEL,
    temperature: float = 0.3,
    max_tokens: int = 1000,
    json_mode: bool = False
) -> str:
    """Async wrapper für LLM calls"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    return chat_completion(messages, model, max_tokens, temperature, json_mode)
