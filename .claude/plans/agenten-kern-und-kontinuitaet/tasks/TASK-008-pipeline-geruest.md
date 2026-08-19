# TASK-008: Schreib-Pipeline-Gerüst (ohne Szenen-Schritt)
Status: ⏳ ausstehend
Abhängig von: [TASK-007]
Parallel: nein
*(vormals TASK-013 im Gesamtplan — hier nur das Geruest; der Szenen-Schritt liegt in `szenen-und-lokales-llm/TASK-003`)*

## Beschreibung
Die deterministische Kette „Szene schreiben" als Workflow-Agent — nicht als LLM-Delegation, weil die Reihenfolge fest ist und nicht vom Modell entschieden werden soll.

```python
writing_pipeline = SequentialAgent(
    name="writing_pipeline",
    sub_agents=[
        create_context_loader(),      # output_key="scene_context"
        create_plot_beat_agent(),     # output_key="scene_beat"
        create_character_brief(),     # output_key="character_brief"
        # --- SZENEN-SLOT: create_scene_agent() wird in Plan 3/TASK-003 eingesetzt ---
        LoopAgent(
            name="editing_loop",
            sub_agents=[create_editor_agent(), QualityChecker(name="quality_checker")],
            max_iterations=3,
        ),
    ],
)
```

**Szenen-Slot als bewusste Luecke:** In diesem Plan wird `scene_draft` nicht von einem Agenten erzeugt, sondern als Fixture in den State gelegt. **Entscheidung E8: das Fixture ist Szene E „Protokoll der Sehnsucht"** aus `books/life_link/idea/basics.md` (Abschnitt 7, „Log-Eintrag #47"), abgelegt als `tests/fixtures/szene_e_protokoll_der_sehnsucht.md` — die einzige ausformulierte Szene des Quellmaterials, mit beiden Registern (KI-Analyse klinisch, Markus' Perspektive erzaehlend), dadurch ideal, um Register-Checks und Editor-Verdikt realistisch zu treiben. Damit sind Loop-Terminierung, State-Fluss und Abbruchpfade testbar, bevor es einen Scene Agent gibt. Der Slot ist im Code als kommentierte Stelle + Test dokumentiert, damit Plan 3 ihn eindeutig fuellt (und das Fixture wieder entfernt).

Datenfluss ausschliesslich ueber `output_key` → `{state_key}`-Injection in der naechsten Instruction.

Persistenz-Konvention (wirkt voll erst mit Plan 3): die finale Fassung geht ueber `write_scene(...)`; ein abgebrochener Loop schreibt `kapitel_NN.scene_M.draft.md` mit dem Verdikt als Frontmatter — nie stillschweigend als fertig markieren. Der Draft-Pfad in `app/tools/manuscript.py` wird bereits hier implementiert und gegen das Fixture getestet.

Factory-Funktionen **aufrufen**, nicht referenzieren (`create_x()`, nicht `create_x`) — sonst `ValidationError`.

## Akzeptanzkriterien
- [ ] Die Pipeline laeuft end-to-end mit dem Szene-E-Fixture als `scene_draft` (Kontext → Beat → Brief → Editor-Loop) — Fixture eingecheckt unter `tests/fixtures/` (E8)
- [ ] Jeder Schritt liest nachweislich den State des Vorgaengers (im `-v`-Output sichtbar)
- [ ] Der Editor-Loop terminiert bei `pass` vorzeitig (nicht immer 3 Durchlaeufe)
- [ ] Bei `max_iterations` ohne Pass entsteht eine `.draft.md` mit Verdikt, keine finale Datei
- [ ] Der Szenen-Slot ist als dokumentierte Erweiterungsstelle ausgefuehrt (Kommentar + Test, der die Slot-Position fixiert)
- [ ] `EventsCompactionConfig` am `App` gesetzt, damit lange Sessions nicht das Kontextfenster sprengen
- [ ] Eine Pipeline-Session ueberlebt einen Prozess-Neustart und laesst sich per `--session-id` fortsetzen (`DatabaseSessionService` aus Plan 1, E3)
- [ ] `ResumabilityConfig(is_resumable=True)` am `App` gesetzt

## Betroffene Dateien
- `app/pipelines/__init__.py`
- `app/pipelines/writing.py`
- `app/agent.py`
- `app/tools/manuscript.py` (Draft-Pfad)
- `tests/fixtures/szene_e_protokoll_der_sehnsucht.md` (E8)
- `tests/unit/test_pipeline_geruest.py`
