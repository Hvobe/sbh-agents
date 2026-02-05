"""
Support Agent - Hauptlogik
BörsennewsApp Support Agent mit FAQ-basierter Antwortgenerierung
"""
from __future__ import annotations

import numpy as np
from shared.database import get_supabase
from shared.llm_client import (
    create_embedding,
    chat_completion_with_usage,
    parse_json_response
)
from shared.debug_tracker import DebugTracker
from shared.request_logger import log_request
from shared.chat_memory import build_context_messages
from .prompts import SYSTEM_PROMPT
from .config import (
    FAQ_TABLE,
    FAQ_SIMILARITY_THRESHOLD,
    FAQ_RESULT_LIMIT,
    LLM_MODEL,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
)


def cosine_similarity(vec1: list, vec2: list) -> float:
    """Berechnet Kosinus-Ähnlichkeit zwischen zwei Vektoren"""
    a = np.array(vec1)
    b = np.array(vec2)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def search_faqs(question: str, tracker: DebugTracker | None = None) -> list:
    """
    Semantic Search für ähnliche FAQs
    """
    step = tracker.start_step("faq_search") if tracker else None

    try:
        supabase = get_supabase()

        # 1. Embedding für die Frage erstellen
        query_embedding = create_embedding(question)

        # 2. Alle Dokumente mit Embeddings laden
        result = supabase.table(FAQ_TABLE).select(
            "id, question, answer, source_url, embedding"
        ).execute()

        if not result.data:
            if step:
                step.stop({"matches": 0, "error": "Keine FAQs in Datenbank"})
            return []

        # 3. Similarity berechnen und filtern
        scored_docs = []
        for doc in result.data:
            if doc.get("embedding"):
                try:
                    if isinstance(doc["embedding"], str):
                        emb_str = doc["embedding"].strip("[]")
                        doc_embedding = [float(x) for x in emb_str.split(",")]
                    else:
                        doc_embedding = doc["embedding"]

                    similarity = cosine_similarity(query_embedding, doc_embedding)
                    if similarity >= FAQ_SIMILARITY_THRESHOLD:
                        scored_docs.append({
                            "id": doc["id"],
                            "question": doc["question"],
                            "answer": doc["answer"],
                            "source_url": doc.get("source_url"),
                            "similarity": round(similarity, 4)
                        })
                except (ValueError, TypeError):
                    continue

        # 4. Nach Similarity sortieren und limitieren
        scored_docs.sort(key=lambda x: x["similarity"], reverse=True)
        results = scored_docs[:FAQ_RESULT_LIMIT]

        if step:
            step.stop({
                "total_faqs": len(result.data),
                "matches_above_threshold": len(scored_docs),
                "returned": len(results),
                "top_score": results[0]["similarity"] if results else 0,
                "threshold": FAQ_SIMILARITY_THRESHOLD
            })

        return results

    except Exception as e:
        if step:
            step.stop({"error": str(e), "matches": 0})
        return []


def format_faq_context(faqs: list) -> str:
    """FAQs als Kontext für das LLM formatieren"""
    if not faqs:
        return "Keine passenden FAQs gefunden."

    context = "Relevante FAQs aus der Wissensbasis:\n\n"
    for i, faq in enumerate(faqs, 1):
        context += f"--- FAQ {i} (Relevanz: {faq['similarity']:.0%}) ---\n"
        context += f"Frage: {faq['question']}\n"
        context += f"Antwort: {faq['answer']}\n"
        if faq.get('source_url'):
            context += f"Quelle: {faq['source_url']}\n"
        context += "\n"
    return context


async def get_response(
    user_question: str,
    chat_history: list[dict] | None = None,
    debug: bool = False
) -> dict:
    """
    Hauptfunktion des Support Agents

    1. FAQ suchen via Semantic Search
    2. LLM-Antwort basierend auf FAQs generieren (mit Chat-History)
    3. JSON Response parsen und zurückgeben
    """
    tracker = DebugTracker(agent="support")

    try:
        # 1. Relevante FAQs finden
        faqs = search_faqs(user_question, tracker)
        faq_context = format_faq_context(faqs)

        # Grounding: FAQ-Matches tracken
        if faqs:
            for faq in faqs:
                tracker.grounding.add_data_point(
                    f"FAQ Match: {faq['question'][:40]}...",
                    f"{faq['similarity']:.0%}"
                )
        else:
            tracker.grounding.add_missing_data("Keine passenden FAQs gefunden")

        # 2. Messages aufbauen (mit Smart Memory)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Chat-History mit intelligenter Kontextverwaltung
        context_messages, history_summary = build_context_messages(chat_history)
        messages.extend(context_messages)
        tracker.set_chat_history(history_summary)

        # Aktuelle Frage mit FAQ-Kontext
        user_message = f"{faq_context}\n\n---\n\nNutzer-Frage: {user_question}"
        messages.append({"role": "user", "content": user_message})

        # 3. LLM fragen (mit Usage Tracking)
        llm_response = chat_completion_with_usage(
            messages=messages,
            model=LLM_MODEL,
            max_tokens=LLM_MAX_TOKENS,
            temperature=LLM_TEMPERATURE,
            json_mode=True
        )

        # LLM Call tracken
        tracker.track_llm_call(
            model=llm_response.model,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_message,
            response=llm_response.content,
            input_tokens=llm_response.input_tokens,
            output_tokens=llm_response.output_tokens,
            response_time_ms=llm_response.response_time_ms
        )

        # 4. JSON parsen
        result = parse_json_response(llm_response.content)

        response = {
            "response": result.get("response", "Entschuldigung, etwas ist schiefgelaufen."),
            "suggestions": result.get("suggestions"),
            "escalate": result.get("escalate", False)
        }

        if debug:
            response["debug_info"] = tracker.to_dict()

        # Request loggen für Monitoring
        await log_request(tracker, user_question, response.get("response"))

        return response

    except Exception as e:
        tracker.add_data("error", str(e))

        response = {
            "response": "Es tut mir leid, es ist ein technischer Fehler aufgetreten. "
                       "Bitte versuchen Sie es erneut oder kontaktieren Sie unseren Support.",
            "suggestions": [
                "Wie kann ich mein Passwort zurücksetzen?",
                "Wie ändere ich meine E-Mail-Adresse?",
                "Wie kontaktiere ich den Support?"
            ],
            "escalate": True
        }

        if debug:
            response["debug_info"] = tracker.to_dict()

        await log_request(tracker, user_question, response.get("response"))

        return response


# Für direktes Testen
if __name__ == "__main__":
    import asyncio

    test_question = "Wie kann ich mein Passwort zurücksetzen?"
    print(f"Frage: {test_question}\n")

    answer = asyncio.run(get_response(test_question, debug=True))
    print(f"Antwort:\n{answer}")
