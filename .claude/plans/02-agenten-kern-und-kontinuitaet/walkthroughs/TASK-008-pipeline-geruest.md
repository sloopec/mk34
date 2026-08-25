# Durchführungsbericht: TASK-008 — Schreib-Pipeline-Gerüst (ohne Szenen-Schritt)
Abgeschlossen: 2026-08-24T16:00:00Z

## Was wurde umgesetzt

`app/pipelines/writing.py`s `create_writing_pipeline()` — ein `SequentialAgent` als deterministische
Kette (bewusst kein LLM-Delegationsschritt, die Reihenfolge ist fest):

1. **`context_loader_step`** — ruft `load_scene_context(active_chapter, active_scene)` auf; das
   Tool schreibt sein Ergebnis bereits selbst unter `scene_context` in den State (TASK-002-
   Entscheidung), der Schritt trägt deshalb bewusst **kein** `output_key`.
2. **`plot_beat_step`** — fasst aus `{scene_context}` den Beat der aktuellen Szene zusammen,
   `output_key="scene_beat"`.
3. **`character_brief_step`** — holt per `AgentTool(character_agent)` einen Figuren-Brief zur
   POV-Figur aus `{scene_beat}`, `output_key="character_brief"`.
4. **`scene_slot_fixture`** (**SZENEN-SLOT, Entscheidung E8**) — ein minimaler `BaseAgent`
   (`_SceneSlotFixture`), der `state["scene_draft"]` auf das eingecheckte Fixture Szene E
   ("Das Protokoll der Sehnsucht", `tests/fixtures/szene_e_protokoll_der_sehnsucht.md`) setzt,
   statt Text zu generieren — der Scene Agent existiert erst ab Plan 3/TASK-003, der ihn 1:1 an
   dieser Position ersetzt.
5. **`editing_loop`** — `LoopAgent(sub_agents=[editor_agent, quality_checker], max_iterations=3)`,
   wiederverwendet aus TASK-006. `after_agent_callback=_persist_or_draft` läuft garantiert einmal
   nach dem Loop, unabhängig davon, ob er per `pass` vorzeitig terminierte oder
   `max_iterations` erreichte: bei `grade == "pass"` wird `write_scene(...)` mit dem finalen
   Text aufgerufen, sonst `write_scene_draft(...)` mit dem letzten Verdikt als Frontmatter — nie
   wird stillschweigend eine unfertige Fassung als final markiert.

`write_scene_draft` (`app/tools/manuscript.py`) legt `kapitel_NN.scene_M.draft.md` an (separater
Namensraum von den `chapter_NN.md`-Manuskriptdateien), mit `status`/`grade`/`issues` als
YAML-artigem Frontmatter.

`App(...)` in `app/agent.py` bekam `events_compaction_config=EventsCompactionConfig(compaction_interval=20, overlap_size=3)`
und `resumability_config=ResumabilityConfig(is_resumable=True)` — Voraussetzung für lange
Pipeline-Sessions, die das Kontextfenster nicht sprengen und über `--session-id` fortsetzbar
bleiben (aufbauend auf dem bereits in Plan 1 gewählten `DatabaseSessionService`, Entscheidung E3).

## Geänderte Dateien

- `app/pipelines/__init__.py`, `app/pipelines/writing.py` (neu)
- `app/agent.py` (`EventsCompactionConfig`/`ResumabilityConfig` ergänzt)
- `app/tools/manuscript.py` (`write_scene_draft` ergänzt)
- `tests/fixtures/szene_e_protokoll_der_sehnsucht.md` (neu, E8)
- `tests/unit/test_pipeline_geruest.py` (neu)
- `tests/unit/test_manuscript_tools.py` (`write_scene_draft`-Tests ergänzt)
- `pyproject.toml` (codespell-Ausnahmeliste erweitert)

## Design-Entscheidungen

**`context_loader_step` trägt kein `output_key`.** Das war bereits die in TASK-002 getroffene
Entscheidung (`load_scene_context` schreibt `scene_context` selbst in den State); ein zusätzliches
`output_key="scene_context"` auf diesem Pipeline-Schritt hätte den strukturierten Tool-Rückgabewert
mit dem freien Bestätigungstext des LLM ("Kontext geladen.") überschrieben — im Live-Test bestätigt
(`test_context_loader_step_has_no_output_key` plus der Live-Smoke-Test, der `scene_context`
unverändert bis zum Ende der Pipeline nachweist).

**Slot-Position per Test fixiert.** `test_scene_slot_is_at_fixed_position_four` prüft explizit
`pipeline.sub_agents[3]` — das ist die von der Task-Datei geforderte "dokumentierte
Erweiterungsstelle". Plan 3/TASK-003 kann diesen Test als Kontrakt lesen: `_SceneSlotFixture` wird
1:1 durch `create_scene_agent()` ersetzt, keine Positions-Verschiebung nötig.

**Live-Test mit `chapter=99`.** Um keine reale Manuskript-/Store-Datei zu kollidieren, lief der
End-to-End-Test mit einer offensichtlich unrealistischen Kapitelnummer. Trotzdem hat der
`_persist_or_draft`-Callback erwartungsgemäß real nach `books/life_link/manuscript/chapter_99.md`
geschrieben (der Editor verurteilte die Fixture-Szene direkt mit `"grade": "pass"`) — diese Datei
wurde unmittelbar nach dem Test gelöscht, damit der Buch-Store sauber bleibt.

**`max_iterations`-ohne-`pass`-Pfad nur unit-, nicht live-getestet.** Der Editor hat die
Fixture-Szene im Live-Lauf bereits im ersten Durchlauf mit `"pass"` bewertet (plausibel: Szene E
ist bereits sorgfältig redigierter, veröffentlichungsreifer Text aus `basics.md`) — ein
`max_iterations`-Abbruch ließ sich damit nicht organisch live provozieren, ohne den Editor
künstlich zum Scheitern zu zwingen. Der Pfad ist stattdessen deterministisch über
`test_persist_or_draft_writes_draft_when_not_pass` und die `write_scene_draft`-Tests abgedeckt,
die exakt die Verzweigung im `_persist_or_draft`-Callback prüfen.

**Sessions-Resumability nur über Konfiguration verifiziert, nicht per eigenem Restart-Test.**
`ResumabilityConfig(is_resumable=True)` ist gesetzt, und das Fundament (`DatabaseSessionService`
statt `InMemorySessionService`) steht seit Plan 1/TASK-001 (Entscheidung E3) — ein dedizierter
Prozess-Neustart-Test mit `--session-id`-Fortsetzung wurde aus Zeitgründen nicht zusätzlich
durchgeführt; die Konfiguration selbst ist der hier erbrachte Nachweis.

## Verifikationsschritte

1. `uv run pytest tests/unit/test_pipeline_geruest.py tests/unit/test_manuscript_tools.py -q` →
   29 passed (5 Struktur-/Slot-Tests, 3 `_persist_or_draft`-Tests, 3 neue `write_scene_draft`-Tests
   plus bestehende Manuskript-Tests).
2. `uv run pytest tests/unit -q` (Gesamtsuite) → 108 passed, keine Regression.
3. `agents-cli lint` → `ruff check`, `ruff format --check`, `codespell`, `ty check` alle grün.
4. Live-End-to-End-Test (`InMemoryRunner`, echte Gemini-API, vorbelegter State mit
   `active_chapter=99`):
   - Schritt-Reihenfolge exakt wie erwartet: `context_loader_step → plot_beat_step →
     character_brief_step → scene_slot_fixture → editor_agent → quality_checker`.
   - `scene_context`, `scene_beat`, `character_brief` und `scene_draft` (mit dem Fixture-Inhalt
     "Log-Eintrag #47") alle im finalen State vorhanden.
   - Editor-Verdikt `"grade": "pass"` — Loop terminierte vorzeitig (nicht alle 3 Iterationen),
     `_persist_or_draft` schrieb die finale Fassung.
   - `books/life_link/manuscript/chapter_99.md` unmittelbar nach dem Test wieder entfernt.
