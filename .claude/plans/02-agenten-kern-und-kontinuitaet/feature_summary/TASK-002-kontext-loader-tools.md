# Feature-Zusammenfassung: TASK-002 — Kontext-Loader-Tools

## Was wurde umgesetzt

Die Agenten bekommen Zugriff auf den kompletten Story-Kanon des Buchprojekts: Weltenbau,
Sprachregeln pro Figur, Plot-Phasen und — als zentrale Schnittstelle für die spätere
Schreib-Pipeline — eine kombinierte Szenen-Kontext-Abfrage, die Beat, beteiligte Figuren und
Weltregeln in einem einzigen Aufruf zusammenführt.

Ergänzend sorgt ein Initialisierungs-Callback dafür, dass Agenten-Instructions, die auf
Zustandsvariablen wie „aktuelles Kapitel" oder „Szenenkontext" verweisen, beim allerersten
Gesprächsschritt nicht mit einem Fehler abbrechen — auch wenn noch kein Tool aufgerufen wurde,
das diese Werte gesetzt hätte.

## Geänderte Dateien

- `app/tools/context_loader.py`
- `app/callbacks.py`
- `tests/unit/test_context_loader.py`
- `tests/unit/test_callbacks.py`
- `pyproject.toml`

## Nächster Schritt

TASK-003 (Eval-Grundgerüst und Judge-Bibliothek) — ab hier hat jeder weitere Task in Plan 2 ein
messbares Qualitäts-Gate. Die hier gebauten Tools werden erstmals in TASK-007 (Orchestrator) und
TASK-008 (Pipeline-Gerüst) tatsächlich an einen Agenten angehängt; dort wird auch das bisher nur
unit-getestete `initialize_state`-Callback im echten Playground verifiziert.
