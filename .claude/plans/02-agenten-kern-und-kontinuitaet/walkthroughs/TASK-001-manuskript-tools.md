# Durchführungsbericht: TASK-001 — Manuskript-Tools (read/write/list/stats)
Abgeschlossen: 2026-08-19T01:00:00Z

## Was wurde umgesetzt

Vier FunctionTools in `app/tools/manuscript.py`, wie in der Task-Datei spezifiziert:

- `read_manuscript(chapter)` — liest eine Kapiteldatei vollständig; liefert `{"status": "not_found"}`
  statt einer Exception, wenn das Kapitel noch nicht existiert.
- `write_scene(chapter, scene, text)` — ersetzt/legt genau eine Szene innerhalb einer Kapiteldatei
  an, ohne die übrigen Szenen zu berühren; legt fehlende Kapiteldateien idempotent an.
- `list_chapters()` — listet alle vorhandenen Kapitel mit Szenenzahl, aufsteigend sortiert.
- `chapter_stats(chapter)` — Wortzahl, Szenenzahl und die im Kapiteltext auftretenden Figuren
  (Abgleich gegen `store/characters.json`).

Szenengrenzen werden über Markdown-Marker (`<!-- scene:N -->`) realisiert; ein Regex-Parser
(`_parse_scenes`) zerlegt eine Kapiteldatei in ein `{szenennummer: text}`-Dict, ein Renderer
(`_render_chapter`) baut daraus wieder eine sortierte, konsistent formatierte Kapiteldatei —
das ist die Grundlage für die geforderte Idempotenz von `write_scene`.

Ein neues, wiederverwendbares Modul `app/tools/_paths.py` löst `MK34_BOOK_ROOT` (Entscheidung E5:
liegt außerhalb von `mk34-book-agent/`, im Repo-Root) zu einem absoluten Pfad auf und stellt
`resolve_within(base, relative_name)` bereit — eine generische Traversal-Schutzfunktion, die jede
Pfadkonstruktion aus Modell-Output gegen `..`/absolute Pfade absichert. Dieses Modul wird auch von
den in TASK-002/005/011/012 folgenden Tools wiederverwendet werden (Store-Zugriff), daher hier
bewusst als eigenständiges, generisches Hilfsmodul angelegt statt als private Funktion nur in
`manuscript.py`.

Kapitel-/Szenennummern werden zusätzlich über `_validate_number` explizit gegen `int()` geprüft,
bevor sie in einen Dateinamen einfließen — das blockiert Traversal-Versuche bereits auf
Typ-Ebene (ein String wie `"../../etc/passwd"` scheitert an `int(...)`), bevor `resolve_within`
überhaupt greifen müsste.

## Geänderte Dateien

- `app/tools/_paths.py` (neu) — `book_root()`, `manuscript_dir()`, `store_dir()`, `resolve_within()`
- `app/tools/manuscript.py` (neu) — die vier Manuskript-Tools
- `app/tools/__init__.py` (neu) — Paket-Docstring, verweist auf `manuscript`/`context_loader`
- `tests/unit/test_manuscript_tools.py` (neu) — 18 Tests gegen ein isoliertes Fixture-Manuskript
  (`tmp_path`, `monkeypatch` auf `manuscript_dir`/`store_dir`)
- `pyproject.toml` — `codespell`-`ignore-words-list` um `szene,sie,alle` erweitert (bestehende
  Konvention aus Plan 1 für deutsche Wörter, die codespells englisches Wörterbuch fälschlich
  triggern)

## Design-Entscheidungen

**Pfadsicherheit über zwei unabhängige Schichten.** Erstens die `int()`-Konvertierung in
`_validate_number` (blockiert bereits die meisten Traversal-Strings), zweitens `resolve_within`
als generischer, wiederverwendbarer Schutz für alle künftigen Store-Zugriffe (auch dort, wo
später ggf. Strings statt Ints in Pfade einfließen, z. B. Figurennamen in `characters.py`).
Beide Schichten sind unabhängig testbar (`test_resolve_within_rejects_dot_dot` prüft die
Kernfunktion isoliert, die `test_*_rejects_path_traversal`-Tests prüfen das Gesamtverhalten der
Tools).

**`chapter_stats` liest über `read_manuscript`, nicht über eigenen Dateizugriff.** Vermeidet
doppelte Not-Found-/Fehlerbehandlung und stellt sicher, dass beide Tools bei fehlendem Kapitel
exakt dasselbe `{"status": "not_found", ...}` liefern.

**Figuren-Erkennung nutzt Voll- und Teilnamen.** `_characters_mentioned` prüft sowohl den vollen
Namen (`"Dr. Sarah Lin"`) als auch jedes einzelne Namens-Token (`"Sarah"`, `"Lin"`), damit
Dialog-Erwähnungen wie „Sarah sagte…" ebenfalls als Auftritt der Figur zählen — passend zur
Prosa-Realität des Life-Link-Manuskripts, in dem Figuren selten mit vollem Namen angesprochen
werden.

## Verifikationsschritte

1. `uv run pytest tests/unit/test_manuscript_tools.py -q` → 18 passed.
2. `uv run pytest tests/unit -q` (Gesamtsuite inkl. Plan-1-Tests) → 40 passed, keine Regression.
3. `agents-cli lint` (aus `mk34-book-agent/`) → `ruff check`, `ruff format --check`, `codespell`,
   `ty check` alle grün.
