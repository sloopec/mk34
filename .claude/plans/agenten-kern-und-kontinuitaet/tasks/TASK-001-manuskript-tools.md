# TASK-001: Manuskript-Tools (read/write/list/stats)
Status: ⏳ ausstehend
Abhängig von (plan-übergreifend): fundament-und-kontext/TASK-003
Parallel: ja
*(vormals TASK-004 im Gesamtplan)*

## Beschreibung
FunctionTools fuer den Manuskript-Zugriff in `app/tools/manuscript.py`.

- `read_manuscript(chapter: int) -> dict` — Kapiteltext oder `{"status": "not_found"}`
- `write_scene(chapter: int, scene: int, text: str) -> dict` — schreibt/ersetzt eine Szene innerhalb der Kapiteldatei; niemals stilles Ueberschreiben eines ganzen Kapitels
- `list_chapters() -> dict` — vorhandene Kapitel mit Szenenzahl
- `chapter_stats(chapter: int) -> dict` — Wortzahl, Szenen, auftretende Figuren

ADK-Toolregeln: Typannotationen **ohne** Defaults, JSON-serialisierbarer dict-Return, aussagekraeftiger Docstring (geht an das LLM), `tool_context` nicht im Docstring erwaehnen.

Szenengrenzen werden ueber Markdown-Marker realisiert (z. B. `<!-- scene:2 -->`), damit `write_scene` idempotent einzelne Szenen ersetzen kann.

Sicherheit: alle Pfade gegen `MK34_BOOK_ROOT` kanonisieren und Traversal (`..`, absolute Pfade) ablehnen — Kapitel-/Szenennummern kommen aus Modell-Output. `MK34_BOOK_ROOT` zeigt gemaess E5 auf `books/life_link/` im Repo-Root, ausserhalb von `mk34-book-agent/`.

Hinweis zur Planaufteilung: die Tools sind szenen-agnostisch (Dateizugriff) und gehoeren deshalb hierher; der Agent, der `write_scene` kreativ befuellt, kommt erst in `szenen-und-lokales-llm/TASK-002`.

## Akzeptanzkriterien
- [ ] Alle vier Tools implementiert, mit Docstrings, dict-Return, `{"status": ...}`-Konvention
- [ ] `write_scene` ersetzt eine bestehende Szene idempotent und legt fehlende Kapiteldateien an
- [ ] Pfad-Traversal wird abgelehnt (pytest)
- [ ] Fehlerfaelle liefern `{"status": "error", "message": ...}` statt Exceptions
- [ ] pytest deckt read/write/list/stats gegen ein Fixture-Manuskript ab

## Betroffene Dateien
- `app/tools/__init__.py`
- `app/tools/manuscript.py`
- `tests/unit/test_manuscript_tools.py`
