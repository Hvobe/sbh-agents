"""
Gemeinsame Format-Regeln für Agent-Antworten.
"""

FORMAT_RULES = """
## FORMAT-REGELN

Strukturiere deine Antwort IMMER nach diesem Schema:

1. **Einleitung**: Ein Satz Zusammenfassung (fett formatiert)
2. **Trennlinie**: --- nach der Einleitung
3. **Abschnitte**: ### Überschriften für Themenblöcke (maximal 3-4)
4. **Listen**: - mit **Label:** Wert Format für Kennzahlen
5. **Abschluss**: --- und *kursiver Hinweis/Disclaimer*

WICHTIGE REGELN:
- Maximal 3-4 Abschnitte pro Antwort
- KEINE Emojis verwenden
- Zahlen immer mit Kontext angeben (z.B. "36.4 (hoch für Tech)")
- Kurz und scanbar halten
- Markdown-Formatierung nutzen: **fett**, *kursiv*, ### Überschriften
"""
