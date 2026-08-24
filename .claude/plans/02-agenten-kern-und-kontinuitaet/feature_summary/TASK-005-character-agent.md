# Feature-Zusammenfassung: TASK-005 — Character Agent und Figuren-Tools

## Was wurde umgesetzt

Der zweite Autoren-Agent: Der Character Agent ist der Spezialist, den andere Agenten befragen,
wenn es um eine bestimmte Figur geht — "Wie würde David in dieser Situation reagieren?". Er
antwortet mit einem kompakten Brief: welches Sprachregister die Figur nutzt, was sie motiviert,
was sie zu diesem Zeitpunkt der Handlung weiß (und was nicht), sowie konkreten
Dialogvorschlägen. Besonders wichtig: Er widerspricht aktiv, wenn eine Szene der Figur Wissen
unterstellt, das sie zu diesem Zeitpunkt noch nicht haben kann — ein zentraler Baustein für
Kontinuität im späteren Buch.

Ein echter Testlauf hat bestätigt: Der Agent wird korrekt als Werkzeug eines anderen Agenten
aufgerufen (nicht als Delegation des gesamten Gesprächs), bleibt im richtigen Sprachregister und
erkennt einen absichtlich eingebauten Wissenskonflikt korrekt.

## Geänderte Dateien

- `app/tools/characters.py`
- `app/agents/character_agent.py`
- `app/prompts/character.py`
- `tests/unit/test_character_tools.py`, `test_character_agent.py`

## Nächster Schritt

TASK-006 (Editor Agent) — der letzte der drei Autoren-Agenten, bevor in TASK-007 der
Orchestrator alle drei zusammenführt (Plot/Editor als Sub-Agents, Character als `AgentTool`,
genau wie hier bereits getestet).
