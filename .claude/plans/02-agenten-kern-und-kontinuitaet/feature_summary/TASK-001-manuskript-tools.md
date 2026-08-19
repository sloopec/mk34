# Feature-Zusammenfassung: TASK-001 — Manuskript-Tools (read/write/list/stats)

## Was wurde umgesetzt

Der Agenten-Kern bekommt seinen ersten Baustein: vier Werkzeuge, mit denen jeder spätere Agent
(Plot, Character, Editor, Orchestrator, Pipeline) sicher auf das Manuskript-Verzeichnis des
Buchprojekts zugreifen kann, ohne selbst Dateiformat oder Pfadsicherheit zu kennen.

- Ein Kapitel lesen (`read_manuscript`), auch wenn es noch nicht existiert.
- Genau eine Szene innerhalb eines Kapitels schreiben oder ersetzen (`write_scene`), ohne dabei
  versehentlich andere Szenen desselben Kapitels zu verlieren.
- Alle vorhandenen Kapitel mit ihrer Szenenzahl auflisten (`list_chapters`).
- Statistiken zu einem Kapitel abrufen (`chapter_stats`): Wortzahl, Szenenzahl, welche Figuren
  vorkommen.

Alle vier Werkzeuge sind bewusst „dumm" im kreativen Sinn — sie schreiben oder lesen nur, was
ihnen gegeben wird, und erzeugen keinen Text selbst. Der Agent, der Szenen tatsächlich inhaltlich
verfasst, kommt erst in Plan 3.

Zusätzlich abgesichert: Kapitel- und Szenennummern, die letztlich aus Modell-Output stammen
können, werden gegen Pfad-Traversal-Versuche (`../../etc/passwd` u. Ä.) geprüft, bevor daraus ein
Dateipfad gebaut wird.

## Geänderte Dateien

- `app/tools/_paths.py` — neues, wiederverwendbares Hilfsmodul für Pfadauflösung/-sicherheit
- `app/tools/manuscript.py` — die vier Manuskript-Tools
- `app/tools/__init__.py`
- `tests/unit/test_manuscript_tools.py`
- `pyproject.toml` (codespell-Ausnahmeliste erweitert)

## Nächster Schritt

TASK-002 (Kontext-Loader-Tools) — parallel zu diesem Task geplant, baut auf demselben
`app/tools/_paths.py`-Hilfsmodul auf und liefert den Story-Kanon (World Bible, Style Guide, Plot,
Szenenkontext) an die Agenten aus. Ab TASK-003 hat jeder weitere Task ein Eval-Gate.
