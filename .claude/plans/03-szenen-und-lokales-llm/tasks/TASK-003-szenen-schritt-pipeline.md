# TASK-003: Szenen-Schritt in die Schreib-Pipeline
Status: ⏳ ausstehend
Abhängig von: [TASK-002]
Abhängig von (plan-übergreifend): 02-agenten-kern-und-kontinuitaet/TASK-008
Parallel: nein
*(der Szenen-Anteil des frueheren TASK-013 — das Geruest liegt in `02-agenten-kern-und-kontinuitaet/TASK-008`)*

## Beschreibung
Der in Plan 2 dokumentierte Szenen-Slot der `writing_pipeline` wird gefuellt:

```python
writing_pipeline = SequentialAgent(
    name="writing_pipeline",
    sub_agents=[
        create_context_loader(),
        create_plot_beat_agent(),
        create_character_brief(),
        create_scene_agent(),         # <-- ersetzt das Fixture aus Plan 2
        LoopAgent(name="editing_loop", sub_agents=[...], max_iterations=3),
    ],
)
```

Zusaetzlich:
- Das Fixture-`scene_draft` aus Plan 2 wird entfernt; der Slot-Test aus `02-agenten-kern-und-kontinuitaet/TASK-008` wird auf den echten Agenten umgestellt.
- Der Orchestrator (Plan 2/TASK-007) bekommt das Routing „Schreibe Kapitel N, Szene M → writing_pipeline"; die Pipeline wird als Sub-Agent registriert, die Instruction erweitert (nicht neu geschrieben).
- Continuity-Check (Plan 2/TASK-011) haengt als `AgentTool` vor dem Editor-Loop; bei `severity: high` wird die Szene nicht geschrieben.
- Post-Write-Hooks (Timeline/Character-State, Plan 2/TASK-012) werden scharf geschaltet: nach erfolgreichem `write_scene` laufen `append_event` und `update_character` automatisch.

## Akzeptanzkriterien
- [ ] „Schreibe Kapitel 3, Szene 2" laeuft end-to-end: Kontext → Beat → Brief → Szene → Continuity → Editor-Loop → `write_scene`
- [ ] Jeder Schritt liest nachweislich den State des Vorgaengers (im `-v`-Output sichtbar)
- [ ] Continuity-Konflikt (`severity: high`) verhindert das Schreiben; Konfliktliste wird ausgegeben
- [ ] Editor-Loop ohne Pass → `.draft.md` mit Verdikt, keine finale Datei
- [ ] Timeline und Character-State werden nach erfolgreichem Write automatisch aktualisiert
- [ ] Das Plan-2-Fixture ist entfernt; kein toter Code im Slot

## Betroffene Dateien
- `app/pipelines/writing.py`
- `app/agent.py` (Orchestrator-Registrierung + Instruction-Erweiterung)
- `app/prompts/orchestrator.py`
- `tests/unit/test_pipeline_geruest.py` (Umstellung auf echten Szenen-Schritt)
