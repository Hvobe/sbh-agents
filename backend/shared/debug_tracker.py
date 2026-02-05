"""
Debug Tracker für Observability
Trackt Timing, Tokens und Kosten für jeden Request
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import Any
from dataclasses import dataclass, field

from .grounding_tracker import GroundingInfo
from .config import PRICING


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Berechnet die Kosten für einen LLM-Call"""
    pricing = PRICING.get(model, PRICING["gpt-4o"])
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 6)


@dataclass
class DebugStep:
    """Ein einzelner Schritt im Debug-Flow"""
    name: str
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    data: dict = field(default_factory=dict)

    def stop(self, data: dict | None = None):
        self.end_time = time.time()
        if data:
            self.data.update(data)

    @property
    def duration_ms(self) -> int:
        if self.end_time:
            return int((self.end_time - self.start_time) * 1000)
        return 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "duration_ms": self.duration_ms,
            **self.data
        }


@dataclass
class LLMCallInfo:
    """Informationen zu einem LLM-Call"""
    model: str = ""
    system_prompt: str = ""
    user_prompt: str = ""
    response: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    response_time_ms: int = 0

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "system_prompt": self.system_prompt[:500] + "..." if len(self.system_prompt) > 500 else self.system_prompt,
            "user_prompt": self.user_prompt[:1000] + "..." if len(self.user_prompt) > 1000 else self.user_prompt,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": self.cost_usd,
            "response_time_ms": self.response_time_ms
        }


class DebugTracker:
    """Trackt alle Schritte eines Agent-Requests für Debug-Zwecke."""

    def __init__(self, agent: str):
        self.request_id = f"req_{uuid.uuid4().hex[:8]}"
        self.agent = agent
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.start_time = time.time()
        self.steps: list[DebugStep] = []
        self.llm_call: LLMCallInfo | None = None
        self.chat_history_used: list[dict] = []
        self.extra_data: dict[str, Any] = {}
        self.grounding = GroundingInfo()

    def start_step(self, name: str) -> DebugStep:
        """Startet einen neuen Tracking-Schritt"""
        step = DebugStep(name=name)
        self.steps.append(step)
        return step

    def track_llm_call(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        response: str,
        input_tokens: int,
        output_tokens: int,
        response_time_ms: int
    ):
        """Trackt einen LLM-Call mit allen Details"""
        self.llm_call = LLMCallInfo(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response=response,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=calculate_cost(model, input_tokens, output_tokens),
            response_time_ms=response_time_ms
        )

    def set_chat_history(self, history: list[dict]):
        """Setzt die verwendete Chat-History"""
        self.chat_history_used = history

    def add_data(self, key: str, value: Any):
        """Fügt zusätzliche Debug-Daten hinzu"""
        self.extra_data[key] = value

    @property
    def total_time_ms(self) -> int:
        """Gesamtzeit des Requests in Millisekunden"""
        return int((time.time() - self.start_time) * 1000)

    def to_dict(self) -> dict:
        """Gibt alle Debug-Infos als Dictionary zurück"""
        result = {
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "agent": self.agent,
            "processing_time_ms": self.total_time_ms,
        }

        for step in self.steps:
            result[step.name] = step.to_dict()

        if self.llm_call:
            result["llm_call"] = self.llm_call.to_dict()

        if self.chat_history_used:
            result["chat_history_used"] = self.chat_history_used

        result["grounding"] = self.grounding.to_dict()
        result.update(self.extra_data)

        return result
