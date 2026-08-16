# TASK-004: Manuskript-Tools (read/write/list/stats)
Status: ⏳ pending
Depends-on: [TASK-003]
Parallel: yes

## Description
FunctionTools fuer den Manuskript-Zugriff in `app/tools/manuscript.py`.

- `read_manuscript(chapter: int) -> dict` — Kapiteltext oder `{"status": "not_found"}`
- `write_scene(chapter: int, scene: int, text: str) -> dict` — schreibt/ersetzt eine Szene innerhalb der Kapiteldatei; niemals stilles Ueberschreiben eines ganzen Kapitels
- `list_chapters() -> dict` — vorhandene Kapitel mit Szenenzahl
- `chapter_stats(chapter: int) -> dict` — Wortzahl, Szenen, auftretende Figuren

ADK-Toolregeln: Typannotationen **ohne** Defaults, JSON-serialisierbarer dict-Return, aussagekraeftiger Docstring (geht an das LLM), `tool_context` nicht im Docstring erwaehnen.

Szenengrenzen werden ueber Markdown-Marker realisiert (z. B. `<!-- scene:2 -->`), damit `write_scene` idempotent einzelne Szenen ersetzen kann.

Sicherheit: alle Pfade gegen `MK34_BOOK_ROOT` kanonisieren und Traversal (`..`, absolute Pfade) ablehnen — Kapitel-/Szenennummern kommen aus Modell-Output.

## Acceptance Criteria
- [ ] Alle vier Tools implementiert, mit Docstrings, dict-Return, `{"status": ...}`-Konvention
- [ ] `write_scene` ersetzt eine bestehende Szene idempotent und legt fehlende Kapiteldateien an
- [ ] Pfad-Traversal wird abgelehnt (pytest)
- [ ] Fehlerfaelle liefern `{"status": "error", "message": ...}` statt Exceptions
- [ ] pytest deckt read/write/list/stats gegen ein Fixture-Manuskript ab

## Affected Files
- `app/tools/__init__.py`
- `app/tools/manuscript.py`
- `tests/unit/test_manuscript_tools.py`
