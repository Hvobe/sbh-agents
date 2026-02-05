"""
Financial Agents API Server
FastAPI Backend - Support Agent
"""
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Shared imports
from shared.config import validate_config
from shared.logger import api_logger
from shared.database import get_supabase
from shared.models import (
    ChatRequest,
    ChatResponse,
    EscalateRequest,
    EscalateResponse,
    SupportResponseRequest,
    FeedbackRequest,
    FeedbackResponse,
)

# Agent imports
from agents.support import get_response as get_support_response

load_dotenv()

app = FastAPI(
    title="Financial Agents API",
    description="AI-basierte Support Agent",
    version="1.0.0"
)

# CORS für Frontend
frontend_urls = os.getenv("FRONTEND_URL", "")
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
if frontend_urls:
    for url in frontend_urls.split(","):
        url = url.strip()
        if url:
            allowed_origins.append(url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)


# ============== Startup Event ==============

@app.on_event("startup")
async def startup_event():
    """Validiert Konfiguration beim Server-Start"""
    validate_config()
    api_logger.info("Config validated successfully - Server ready")


# ============== Root & Health ==============

@app.get("/")
async def root():
    """API Info Endpoint"""
    return {
        "name": "Financial Agents API",
        "version": "1.0.0",
        "agents": ["support"],
        "endpoints": {
            "/chat": "POST - Chat mit Support Agent",
            "/escalate": "POST - Support-Ticket erstellen",
            "/tickets": "GET - Alle Tickets abrufen",
            "/health": "GET - Health Check",
        }
    }


@app.get("/health")
async def health():
    """Health Check"""
    return {"status": "ok", "version": "1.0.0"}


# ============== Chat Endpoint ==============

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat Endpoint für Support Agent

    Args:
        request.message: Die Nutzerfrage
        request.agent: Muss "support" sein
        request.chat_history: Bisheriger Chatverlauf für Memory
        request.debug: Wenn True, werden Debug-Infos zurückgegeben
    """
    try:
        if request.agent != "support":
            raise HTTPException(
                status_code=400,
                detail=f"Agent '{request.agent}' nicht verfügbar. Nur 'support' ist aktiviert."
            )

        result = await get_support_response(
            request.message,
            request.chat_history,
            debug=request.debug
        )

        return ChatResponse(
            response=result["response"],
            suggestions=result.get("suggestions"),
            escalate=result.get("escalate", False),
            debug_info=result.get("debug_info") if request.debug else None,
            structured_data=result.get("structured_data")
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail="Es gab einen Fehler bei der Verarbeitung deiner Anfrage."
        )


# ============== Ticket Endpoints ==============

@app.post("/escalate", response_model=EscalateResponse)
async def escalate(request: EscalateRequest):
    """Erstellt ein Support-Ticket"""
    try:
        supabase = get_supabase()
        result = supabase.table("support_tickets").insert({
            "user_message": request.message,
            "chat_history": request.chat_history,
            "status": "open"
        }).execute()

        ticket_id = result.data[0]["id"]
        return EscalateResponse(
            ticket_id=ticket_id,
            message=f"Ticket #{ticket_id} wurde erstellt. Unser Support-Team meldet sich bei dir!"
        )
    except Exception as e:
        api_logger.error(f"Error creating ticket: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ticket konnte nicht erstellt werden."
        )


@app.get("/tickets")
async def get_tickets(status: str | None = None):
    """Alle Tickets abrufen (optional gefiltert nach Status)"""
    try:
        supabase = get_supabase()
        query = supabase.table("support_tickets").select("*").order("created_at", desc=True)

        if status:
            query = query.eq("status", status)

        result = query.execute()
        return {"tickets": result.data, "count": len(result.data)}
    except Exception as e:
        api_logger.error(f"Error fetching tickets: {e}")
        raise HTTPException(status_code=500, detail="Tickets konnten nicht geladen werden.")


@app.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: int):
    """Einzelnes Ticket abrufen"""
    try:
        supabase = get_supabase()
        result = supabase.table("support_tickets").select("*").eq("id", ticket_id).single().execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Ticket nicht gefunden")
        return result.data
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Error fetching ticket: {e}")
        raise HTTPException(status_code=500, detail="Ticket konnte nicht geladen werden.")


@app.patch("/tickets/{ticket_id}")
async def update_ticket(ticket_id: int, status: str):
    """Ticket-Status aktualisieren"""
    try:
        supabase = get_supabase()
        update_data = {"status": status}
        if status == "resolved":
            update_data["resolved_at"] = datetime.utcnow().isoformat()

        result = supabase.table("support_tickets").update(update_data).eq("id", ticket_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Ticket nicht gefunden")

        return {"message": f"Ticket #{ticket_id} wurde auf '{status}' gesetzt"}
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Error updating ticket: {e}")
        raise HTTPException(status_code=500, detail="Ticket konnte nicht aktualisiert werden.")


@app.post("/tickets/{ticket_id}/respond")
async def respond_to_ticket(ticket_id: int, request: SupportResponseRequest):
    """Support-Mitarbeiter antwortet auf ein Ticket"""
    try:
        supabase = get_supabase()

        # Ticket laden
        ticket_result = supabase.table("support_tickets").select("*").eq("id", ticket_id).single().execute()
        if not ticket_result.data:
            raise HTTPException(status_code=404, detail="Ticket nicht gefunden")

        ticket = ticket_result.data
        chat_history = ticket.get("chat_history") or []

        # Support-Antwort hinzufügen
        chat_history.append({
            "role": "support",
            "content": request.message,
            "support_name": request.support_name
        })

        # Ticket updaten
        supabase.table("support_tickets").update({
            "chat_history": chat_history,
            "status": "in_progress"
        }).eq("id", ticket_id).execute()

        return {"message": "Antwort gesendet", "chat_history": chat_history}
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Error responding to ticket: {e}")
        raise HTTPException(status_code=500, detail="Antwort konnte nicht gesendet werden.")


# ============== Feedback Endpoint ==============

@app.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """
    Speichert Feedback zu einer Chat-Antwort in der Datenbank.
    """
    try:
        if request.feedback_type not in ["positive", "negative"]:
            raise HTTPException(
                status_code=400,
                detail="feedback_type muss 'positive' oder 'negative' sein"
            )

        supabase = get_supabase()
        result = supabase.table("message_feedback").insert({
            "agent_slug": request.agent_slug,
            "user_message": request.user_message,
            "assistant_response": request.assistant_response,
            "feedback_type": request.feedback_type,
            "feedback_comment": request.feedback_comment,
            "session_id": request.session_id
        }).execute()

        feedback_id = result.data[0]["id"] if result.data else None
        api_logger.info(f"Feedback saved: {request.feedback_type} for {request.agent_slug}")

        return FeedbackResponse(
            success=True,
            id=str(feedback_id) if feedback_id else None,
            message="Feedback gespeichert"
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Error saving feedback: {e}")
        return FeedbackResponse(
            success=False,
            message="Feedback konnte nicht gespeichert werden"
        )


# ============== Server Start ==============

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
