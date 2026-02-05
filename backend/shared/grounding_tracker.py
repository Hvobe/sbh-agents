"""
Grounding Tracker
Trackt welche Daten verwendet wurden und erkennt Halluzinationsrisiken.
"""
from dataclasses import dataclass, field
from typing import Any


MISSING_DATA_KEYWORDS = {
    "historisch": "Historische Daten nicht verfuegbar",
    "geschichte": "Historische Daten nicht verfuegbar",
    "entwicklung": "Historische Entwicklung nicht verfuegbar",
    "prognose": "Zukunftsprognosen nicht verfuegbar",
    "vorhersage": "Zukunftsprognosen nicht verfuegbar",
    "zukunft": "Zukunftsprognosen nicht verfuegbar",
}


@dataclass
class GroundingInfo:
    """Tracking-Info für Daten-Grounding."""
    data_used: list[str] = field(default_factory=list)
    data_missing: list[str] = field(default_factory=list)
    confidence: float = 1.0
    hallucination_risk: str = "low"
    ungrounded_claims: list[str] = field(default_factory=list)

    def add_data_point(self, key: str, value: Any):
        """Registriert einen verwendeten Datenpunkt."""
        if value is not None:
            if isinstance(value, float):
                if value > 1_000_000_000:
                    formatted = f"{value/1_000_000_000:.1f}B"
                elif value > 1_000_000:
                    formatted = f"{value/1_000_000:.1f}M"
                else:
                    formatted = f"{value:.2f}"
            else:
                formatted = str(value)

            self.data_used.append(f"{key}: {formatted}")
            self._recalculate_confidence()

    def add_missing_data(self, description: str):
        """Registriert fehlende Daten."""
        if description not in self.data_missing:
            self.data_missing.append(description)
            self._recalculate_confidence()

    def check_question_for_missing_data(self, question: str):
        """Prüft eine Frage auf Keywords die auf fehlende Daten hindeuten."""
        question_lower = question.lower()
        for keyword, missing_description in MISSING_DATA_KEYWORDS.items():
            if keyword in question_lower:
                self.add_missing_data(missing_description)

    def add_ungrounded_claim(self, claim: str):
        """Registriert eine Aussage ohne Datengrundlage."""
        self.ungrounded_claims.append(claim)
        self.hallucination_risk = "high"
        self._recalculate_confidence()

    def _recalculate_confidence(self):
        """Berechnet Confidence basierend auf Datenqualität"""
        if not self.data_used and not self.data_missing:
            self.confidence = 0.5
            self.hallucination_risk = "low"
            return

        if not self.data_used:
            self.confidence = 0.0
            self.hallucination_risk = "high"
            return

        if self.ungrounded_claims:
            self.confidence = 0.2
            self.hallucination_risk = "high"
            return

        total = len(self.data_used) + len(self.data_missing)
        if total == 0:
            self.confidence = 1.0
            self.hallucination_risk = "low"
            return

        ratio = len(self.data_used) / total
        self.confidence = round(ratio, 2)

        if self.confidence >= 0.8:
            self.hallucination_risk = "low"
        elif self.confidence >= 0.5:
            self.hallucination_risk = "medium"
        else:
            self.hallucination_risk = "high"

    def to_dict(self) -> dict:
        """Gibt Grounding-Info als Dictionary zurück"""
        return {
            "data_used": self.data_used,
            "data_missing": self.data_missing,
            "confidence": self.confidence,
            "hallucination_risk": self.hallucination_risk,
            "ungrounded_claims": self.ungrounded_claims,
            "data_points_count": len(self.data_used),
            "missing_count": len(self.data_missing)
        }
