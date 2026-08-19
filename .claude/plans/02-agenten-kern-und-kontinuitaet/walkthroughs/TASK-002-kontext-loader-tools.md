# Durchführungsbericht: TASK-002 — Kontext-Loader-Tools
Abgeschlossen: 2026-08-19T01:45:00Z

## Was wurde umgesetzt

Vier FunctionTools in `app/tools/context_loader.py`:

- `load_world_bible()` — liest `store/world_bible.md` vollständig.
- `load_style_guide()` — liest `store/style_guide.md` vollständig.
- `load_plot_outline(act)` — sucht die Phase mit passender `id` in `store/plot_outline.json`
  (Phasen 0–5 aus `basics.md`).
- `load_scene_context(chapter, scene, tool_context)` — kombiniert in einem Aufruf: den Beat für
  die Zielszene (aus einem neuen `scene_beats`-Feld in `plot_outline.json`, das der Plot Agent
  ab TASK-004 befüllt), die beteiligten Figuren inkl. Sprachregister (aus `characters.json`) und
  die vollständigen Weltregeln/den Style Guide. Das Ergebnis wird zusätzlich direkt unter
  `tool_context.state["scene_context"]` abgelegt.

Zusätzlich `app/callbacks.py` mit `initialize_state` (`before_agent_callback`): setzt
`book_slug`, `active_chapter`, `active_scene`, `scene_context` auf Defaults, sofern noch nicht
gesetzt — verhindert `KeyError`, sobald eine Instruction `{state_key}`-Platzhalter referenziert,
bevor der erste State-Schreibvorgang stattgefunden hat.

## Geänderte Dateien

- `app/tools/context_loader.py` (neu)
- `app/callbacks.py` (neu)
- `tests/unit/test_context_loader.py` (neu) — 10 Tests gegen ein isoliertes Fixture-Store
- `tests/unit/test_callbacks.py` (neu) — 2 Tests für `initialize_state` (Defaults setzen /
  bestehende Werte nicht überschreiben)
- `pyproject.toml` — codespell-Ausnahmeliste um `unter` erweitert

## Design-Entscheidungen

**`load_scene_context` schreibt seinen State-Eintrag selbst, statt sich auf ein umhüllendes
`output_key` zu verlassen.** Die Task-Datei beschreibt das Tool als Schnittstelle, die "sein
Ergebnis via `output_key="scene_context"` in den State schreibt" — `output_key` ist aber ein
Agent-Attribut, kein Tool-Attribut. Damit `{scene_context}` unabhängig davon verfügbar ist, ob
das Tool von einem dedizierten Context-Loader-Agenten mit `output_key="scene_context"`
umhüllt wird (so in `app/pipelines/writing.py`, TASK-008) oder direkt als Tool-Call eines LLM
aufgerufen wird, schreibt die Funktion selbst über `tool_context.state["scene_context"] = result`
in den State. Das ist robuster und deckt beide Aufrufwege ab, ohne der Pipeline-Konvention aus
TASK-008 zu widersprechen (der dortige `output_key` würde denselben Wert redundant, aber
konsistent noch einmal schreiben).

**`load_scene_context` scheitert nicht, wenn noch kein Beat existiert.** `plot_outline.json`
trägt aktuell noch kein `scene_beats`-Array (das befüllt erst der Plot Agent ab TASK-004 über
`update_plot_outline`). Statt eines Fehlers liefert die Funktion `beat: None` und eine leere
Figurenliste zurück, bleibt aber sonst nutzbar (Weltregeln/Style Guide sind immer vorhanden) —
vorwärtskompatibel zu TASK-004, ohne dass diese Aufgabe schon eine Annahme über das künftige
Beat-Schema erzwingen müsste.

**"Kein `KeyError` im Playground"-Kriterium wird hier durch Unit-Tests, nicht durch einen echten
Playground-Lauf verifiziert.** `initialize_state` ist bisher an keinen Agenten angehängt — der
Orchestrator (TASK-007) und die Pipeline (TASK-008) sind noch nicht gebaut. Der tatsächliche
End-to-End-Nachweis ("`agents-cli playground` ohne `KeyError`") erfolgt in TASK-009
(Smoke-Test), sobald `initialize_state` als `before_agent_callback` am `root_agent` hängt. Für
TASK-002 selbst genügt der isolierte Unit-Test der Callback-Logik.

## Verifikationsschritte

1. `uv run pytest tests/unit/test_context_loader.py tests/unit/test_callbacks.py -q` → 10 + 2
   passed.
2. `uv run pytest tests/unit -q` (Gesamtsuite) → 50 passed, keine Regression.
3. `agents-cli lint` → `ruff check`, `ruff format --check`, `codespell`, `ty check` alle grün.
