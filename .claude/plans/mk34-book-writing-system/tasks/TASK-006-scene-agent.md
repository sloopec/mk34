# TASK-006: Scene Agent (erster Agent)
Status: ⏳ ausstehend
Abhängig von: [TASK-002, TASK-004, TASK-005]
Parallel: nein

## Beschreibung
Erster produktiver Agent — der einfachste vollstaendige Use-Case: aus Kontext eine Szene schreiben.

```python
from google.adk.agents import Agent

scene_agent = Agent(
    name="scene_agent",
    model=model_for("scene"),          # lokal oder Cloud, siehe TASK-002
    description="Schreibt eine einzelne Szene aus Beat, Figuren-Brief und Weltregeln.",
    instruction=SCENE_INSTRUCTION,     # nutzt {scene_context}, {scene_beat}, {character_brief}
    tools=[read_manuscript, write_scene, load_scene_context],
    output_key="scene_draft",
)
```

System-Prompt-Anforderungen:
- Kreatives Schreiben, keine Code-/Assistenten-Bias, kein Meta-Kommentar, keine Ueberschriften wie „Hier ist die Szene:".
- Sprachregister pro Figur strikt einhalten (David: „Nanobots"; Sarah/Voss/Aris: „Naniten").
- Show-don't-tell; Wissenschaft nur als Metapher im Dialog.
- Weltregeln aus der World Bible sind harte Constraints.
- Keine Platzhalter (`[TODO]`, `[Name]`).

In Phase 1 laeuft der Scene Agent als `root_agent`, damit `agents-cli run` / `playground` ihn direkt ansprechen. Der Orchestrator kommt erst in TASK-012.

**Keine Safety-Callbacks/Plugins auf diesem Agent** — bewusste Projektentscheidung (Plan: Non-Goals).

## Akzeptanzkriterien
- [ ] `agents-cli run "Schreibe Kapitel 1, Szene 1"` erzeugt eine Szene, die den Kontext aus dem Store nachweislich verwendet
- [ ] Der Text landet ueber `write_scene` in `books/life_link/manuscript/kapitel_01.md`
- [ ] Kein Meta-Kommentar, keine Ueberschrift, keine Platzhalter im Output
- [ ] Sprachregister wird eingehalten (stichprobenhaft manuell geprueft, spaeter per Eval-Metrik)
- [ ] Modellwahl kommt ausschliesslich aus `model_for("scene")`

## Betroffene Dateien
- `app/agent.py`
- `app/agents/__init__.py`
- `app/agents/scene_agent.py`
- `app/prompts/scene.py`
