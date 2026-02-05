"""
Pydantic Models
Gemeinsame Datenmodelle für API Requests und Responses
"""
from typing import Any
from pydantic import BaseModel


# ============== Chat Models ==============

class ChatRequest(BaseModel):
    """Request für Chat-Endpoints"""
    message: str
    agent: str = "support"
    sessionId: str | None = None
    chat_history: list[dict] | None = None
    debug: bool = False


class ChatResponse(BaseModel):
    """Response von Chat-Endpoints"""
    response: str
    suggestions: list[str] | None = None
    escalate: bool = False
    debug_info: dict[str, Any] | None = None
    structured_data: dict[str, Any] | None = None


# ============== Ticket Models ==============

class EscalateRequest(BaseModel):
    """Request für Ticket-Erstellung"""
    message: str
    chat_history: list[dict] | None = None


class EscalateResponse(BaseModel):
    """Response nach Ticket-Erstellung"""
    ticket_id: int
    message: str


class SupportResponseRequest(BaseModel):
    """Request für Support-Antwort auf Ticket"""
    message: str
    support_name: str = "Support"


# ============== Feedback Models ==============

class FeedbackRequest(BaseModel):
    """Request für Message-Feedback"""
    agent_slug: str
    user_message: str
    assistant_response: str
    feedback_type: str
    feedback_comment: str | None = None
    session_id: str | None = None


class FeedbackResponse(BaseModel):
    """Response nach Feedback-Speicherung"""
    success: bool
    id: str | None = None
    message: str | None = None


# ============== Agent Response ==============

class AgentResponse(BaseModel):
    """Standard-Response Format für Agents"""
    response: str
    suggestions: list[str] | None = None
    escalate: bool = False
