"""
Request Logger
Speichert alle Agent-Requests in der Datenbank für Monitoring.
"""
from __future__ import annotations

from .database import get_supabase
from .debug_tracker import DebugTracker
from .logger import db_logger


async def log_request(
    tracker: DebugTracker,
    user_message: str,
    response: str | None = None
) -> bool:
    """
    Speichert einen Request in der agent_requests Tabelle.
    """
    try:
        supabase = get_supabase()
        debug_info = tracker.to_dict()

        llm_call = debug_info.get("llm_call", {})
        grounding = debug_info.get("grounding", {})

        data = {
            "request_id": debug_info.get("request_id"),
            "agent": debug_info.get("agent"),
            "user_message": user_message[:5000] if user_message else None,
            "response": response[:10000] if response else None,
            "processing_time_ms": debug_info.get("processing_time_ms"),
            "model": llm_call.get("model"),
            "input_tokens": llm_call.get("input_tokens"),
            "output_tokens": llm_call.get("output_tokens"),
            "cost_usd": llm_call.get("cost_usd"),
            "confidence": grounding.get("confidence"),
            "hallucination_risk": grounding.get("hallucination_risk"),
            "data_points_count": grounding.get("data_points_count"),
            "debug_info": debug_info
        }

        data = {k: v for k, v in data.items() if v is not None}

        supabase.table("agent_requests").insert(data).execute()
        return True

    except Exception as e:
        db_logger.warning(f"Error logging request to database: {e}")
        return False
