# Durchführungsbericht: TASK-004 — Plot Agent
Abgeschlossen: 2026-08-24T13:00:00Z

## Was wurde umgesetzt

Der Plot Agent (`app/agents/plot_agent.py`) als zweistufiger `SequentialAgent`:

1. **`plot_context_gatherer`** — hat Zugriff auf `load_plot_outline(act)` und die neu ergänzte
   `read_chapter_summaries()`; sammelt den vollständigen Kontext einer Phase (Titel, Fokusfiguren,
   bestehende Beats, bereits geschriebene Kapitel) und schreibt einen freien Fließtext-Entwurf
   nach `output_key="plot_raw"`.
2. **`plot_formalizer`** — `output_schema=SceneBeatList` (Liste von `SceneBeat`, siehe
   `app/schemas.py`), formalisiert den Entwurf in strukturierte Beat-Objekte
   (`output_key="plot_beats"`). Da `output_schema` Tool-Calling deaktiviert, hat dieser Schritt
   bewusst keine Tools.

Ein `after_agent_callback` (`_persist_plot_beats`) schreibt die formalisierten Beats
**deterministisch** — nicht über einen vom Modell aufgerufenen Tool-Call — via
`update_plot_outline(...)` nach `plot_outline.json`. Persistenz hängt damit nie davon ab, dass
das Modell sich an einen Speicher-Tool-Call "erinnert".

`update_plot_outline` und `read_chapter_summaries` wurden in `app/tools/context_loader.py`
ergänzt (dort, wo `load_scene_context` sie bereits vorwärtskompatibel erwartete, siehe
TASK-002-Walkthrough). `update_plot_outline` ist idempotent pro `(chapter, scene)` und klemmt
`tension_level` auf den Bereich 1–10; bestehende `phases` in `plot_outline.json` bleiben
unangetastet.

## Geänderte Dateien

- `app/agents/__init__.py`, `app/agents/plot_agent.py` (neu)
- `app/prompts/__init__.py`, `app/prompts/plot.py` (neu)
- `app/schemas.py` (neu) — `SceneBeat`, `SceneBeatList`, sowie `EditorVerdict` bereits für
  TASK-006 vorbereitet angelegt (wird dort erst verwendet, hier nur definiert, um das Modul nicht
  zweimal aufzumachen)
- `app/tools/context_loader.py` (`update_plot_outline`, `read_chapter_summaries` ergänzt)
- `tests/unit/test_plot_tools.py`, `tests/unit/test_plot_agent.py` (neu)
- `pyproject.toml` (codespell-Ausnahmeliste erweitert)

## Design-Entscheidungen

**`SceneBeatList`-Wrapper statt `list[SceneBeat]` direkt als `output_schema`.** ADK erwartet für
`output_schema` ein einzelnes Pydantic-Modell; der Plot Agent liefert aber eine variable Anzahl
Beats pro Phase. Der Wrapper (`beats: list[SceneBeat]`) löst das ohne Sonderfall im ADK-Aufruf.

**Persistenz per `after_agent_callback`, nicht per Tool-Call des formalisierenden Agenten.** Der
Formalisierer hat wegen `output_schema` ohnehin keine Tools; selbst wenn er welche hätte, wäre
ein Tool-Aufruf zum Speichern ein weiterer Punkt, an dem das Modell "vergessen" könnte, zu
speichern. Der Callback läuft nach jedem erfolgreichen Lauf der `SequentialAgent`-Pipeline
garantiert und deterministisch.

**`SequentialAgent` trotz Deprecation-Warnung verwendet.** ADK meldet
`SequentialAgent is deprecated in favor of Workflow and will be removed in a future version.
Workflow cannot yet be used as an LlmAgent sub-agent.` — da der Plot Agent in TASK-007 als
`sub_agent` eines `Agent` (Orchestrator) eingebunden wird und `Workflow` das laut eigener
ADK-Warnung noch nicht unterstützt, ist `SequentialAgent` hier die einzig kompatible Wahl. Wird
bei einem künftigen ADK-Upgrade zu prüfen sein, ist aber kein Fehler in diesem Task.

**Live-Verifikation über `InMemoryRunner`, nicht über `agents-cli run`.** `root_agent` wird erst
in TASK-007 auf den Orchestrator umgestellt; ein Wechsel des `root_agent` allein für diesen Task
und ein Zurückwechseln danach hätte unnötigen Verlauf in `app/agent.py` erzeugt. Stattdessen
wurde `create_plot_agent()` direkt per `google.adk.runners.InMemoryRunner` mit dem Prompt
"Entwickle Phase 2 in Szenen-Beats" gegen die echte Gemini-API getestet (siehe
Verifikationsschritte) — funktional identisch zu `agents-cli run`, nur ohne den
`root_agent`-Umweg. Der volle `agents-cli run`-Nachweis über den Orchestrator folgt in TASK-009.

**Store-Verschmutzung durch den Live-Smoke-Test rückgängig gemacht.** Der Smoke-Lauf hat
(erwartungsgemäß, da der Callback deterministisch speichert) reale, testgenerierte Beats nach
`books/life_link/store/plot_outline.json` geschrieben. Das wurde unmittelbar per
`git checkout -- books/life_link/store/plot_outline.json` rückgängig gemacht, damit der
kanonische Store aus Plan 1/TASK-003 unverändert bleibt — spekulative Test-Beats gehören nicht in
den kanonischen Story-Kanon.

## Verifikationsschritte

1. `uv run pytest tests/unit/test_plot_tools.py tests/unit/test_plot_agent.py -q` → 11 passed.
2. `uv run pytest tests/unit -q` (Gesamtsuite) → 73 passed, keine Regression.
3. `agents-cli lint` → `ruff check`, `ruff format --check`, `codespell`, `ty check` alle grün.
4. Live-Smoke-Test (`InMemoryRunner`, echte Gemini-API, Prompt "Entwickle Phase 2 in
   Szenen-Beats"): liefert eine vollständige, in sich konsistente Beat-Liste, grounded in Phase 2
   ("Die Recherche") — u. a. David/Dr. Aris-Diagnose-Szene und die Boardroom-Eskalation, beides
   korrekt aus `basics.md`/`plot_outline.json` referenziert, keine erfundenen Figuren. Kein
   Schema-Validierungsfehler. Anschließend `git checkout -- books/life_link/store/plot_outline.json`
   (siehe Design-Entscheidungen).
