"""
Chat Memory Utilities
"""
from __future__ import annotations

from .config import MAX_RECENT_MESSAGES, MAX_OLDER_MESSAGES


def build_context_messages(
    chat_history: list[dict] | None,
    max_recent: int = MAX_RECENT_MESSAGES,
    max_older: int = MAX_OLDER_MESSAGES
) -> tuple[list[dict], list[dict]]:
    """
    Builds context messages from chat history with smart summarization.
    """
    if not chat_history:
        return [], []

    messages = []
    history_summary = []

    total_messages = len(chat_history)

    if total_messages <= max_recent:
        recent = chat_history
        older = []
    else:
        recent = chat_history[-max_recent:]
        older = chat_history[:-max_recent][-max_older:]

    if older:
        topics = extract_topics(older)
        if topics:
            summary_note = f"[Vorheriger Kontext: User sprach über {', '.join(topics)}]"
            messages.append({
                "role": "system",
                "content": summary_note
            })
            history_summary.append({
                "role": "system",
                "content": f"Zusammenfassung: {', '.join(topics)}"
            })

    for msg in recent:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role in ["user", "assistant"] and content:
            messages.append({"role": role, "content": content})
            history_summary.append({
                "role": role,
                "content": content[:200]
            })

    return messages, history_summary


def extract_topics(messages: list[dict]) -> list[str]:
    """Extracts key topics from a list of messages."""
    topics = []
    keywords_found = set()

    topic_patterns = {
        "passwort": "Kontoverwaltung",
        "password": "Kontoverwaltung",
        "login": "Anmeldung",
        "anmelden": "Anmeldung",
        "watchlist": "Watchlist",
        "chart": "Charts",
        "alarm": "Alarme",
        "benachrichtigung": "Benachrichtigungen",
        "email": "E-Mail-Einstellungen",
        "einstellung": "Einstellungen",
        "settings": "Einstellungen",
    }

    for msg in messages:
        content = msg.get("content", "").lower()
        for keyword, topic in topic_patterns.items():
            if keyword in content and topic not in keywords_found:
                keywords_found.add(topic)
                topics.append(topic)

    return topics[:4]
