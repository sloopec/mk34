# TASK-013: Schreib-Pipeline (SequentialAgent + LoopAgent)
Status: ⏳ pending
Depends-on: [TASK-012]
Parallel: no

## Description
Die deterministische Kette „Szene schreiben" als Workflow-Agent — nicht als LLM-Delegation, weil die Reihenfolge fest ist und nicht vom Modell entschieden werden soll.

```python
writing_pipeline = SequentialAgent(
    name="writing_pipeline",
    sub_agents=[
        create_context_loader(),      # output_key="scene_context"
        create_plot_beat_agent(),     # output_key="scene_beat"
        create_character_brief(),     # output_key="character_brief"
        create_scene_agent(),         # output_key="scene_draft"
        LoopAgent(
            name="editing_loop",
            sub_agents=[create_editor_agent(), QualityChecker(name="quality_checker")],
            max_iterations=3,
        ),
    ],
)
```

Datenfluss ausschliesslich ueber `output_key` → `{state_key}`-Injection in der naechsten Instruction.

Persistenz erst am Ende: `write_scene(...)` schreibt die finale Fassung; ein abgebrochener Loop schreibt `kapitel_NN.scene_M.draft.md` mit dem Verdikt als Frontmatter — nie stillschweigend als fertig markieren.

Factory-Funktionen **aufrufen**, nicht referenzieren (`create_x()`, nicht `create_x`) — sonst `ValidationError`.

## Acceptance Criteria
- [ ] Die Pipeline laeuft end-to-end fuer „Schreibe Kapitel 3, Szene 2"
- [ ] Jeder Schritt liest nachweislich den State des Vorgaengers (im `-v`-Output sichtbar)
- [ ] Der Editor-Loop terminiert bei `pass` vorzeitig (nicht immer 3 Durchlaeufe)
- [ ] Bei `max_iterations` ohne Pass entsteht eine `.draft.md` mit Verdikt, keine finale Datei
- [ ] `EventsCompactionConfig` am `App` gesetzt, damit lange Sessions nicht das Kontextfenster sprengen
- [ ] Eine Pipeline-Session ueberlebt einen Prozess-Neustart und laesst sich per `--session-id` fortsetzen (setzt den `DatabaseSessionService` aus TASK-001 voraus)
- [ ] `ResumabilityConfig(is_resumable=True)` am `App` gesetzt, damit unterbrochene Laeufe fortsetzbar sind

## Affected Files
- `app/pipelines/__init__.py`
- `app/pipelines/writing.py`
- `app/agent.py`
- `app/tools/manuscript.py` (Draft-Pfad)
