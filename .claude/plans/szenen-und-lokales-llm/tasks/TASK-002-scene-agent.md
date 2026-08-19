# TASK-002: Scene Agent (Start Gemini, Ziel lokal)
Status: ⏳ ausstehend
Abhängig von (plan-übergreifend): fundament-und-kontext/TASK-002, agenten-kern-und-kontinuitaet/TASK-001, agenten-kern-und-kontinuitaet/TASK-002
Parallel: ja
*(vormals TASK-006 im Gesamtplan)*

## Beschreibung
Der Agent, fuer den es dieses Projekt gibt: aus Kontext eine Szene schreiben.

```python
from google.adk.agents import Agent

scene_agent = Agent(
    name="scene_agent",
    model=model_for("scene"),          # Start: gemini-3.1-pro-preview (E6); ab TASK-004 routing-abhaengig lokal/Cloud
    description="Schreibt eine einzelne Szene aus Beat, Figuren-Brief und Weltregeln.",
    instruction=SCENE_INSTRUCTION,     # nutzt {scene_context}, {scene_beat}, {character_brief}
    tools=[read_manuscript, write_scene, load_scene_context],
    output_key="scene_draft",
)
```

**Stufe A (dieser Task):** Der Agent laeuft auf `gemini-3.1-pro-preview` — der Schreib-Workflow ist damit sofort testbar, ohne dass die VM laeuft. **Stufe B (TASK-004):** der Classifier routet auf das lokale Modell; am Agenten aendert sich dann nichts, nur `model_for("scene")` liefert eine andere Instanz.

System-Prompt-Anforderungen:
- Kreatives Schreiben, keine Code-/Assistenten-Bias, kein Meta-Kommentar, keine Ueberschriften wie „Hier ist die Szene:".
- Sprachregister pro Figur strikt einhalten (David: „Nanobots"; Sarah/Voss/Aris: „Naniten").
- Show-don't-tell; Wissenschaft nur als Metapher im Dialog.
- Weltregeln aus der World Bible sind harte Constraints.
- Keine Platzhalter (`[TODO]`, `[Name]`).
- Der Prompt muss auf **beiden** Zielmodellen funktionieren (Gemini Pro und supergemma4-26b) — keine modellspezifischen Tricks; was das 26B-Modell nicht versteht, fliegt raus.

**Keine Safety-Callbacks/Plugins auf diesem Agent** — bewusste Projektentscheidung (Kern-Use-Case). Fuer die Gemini-Stufe heisst das auch: Safety-Einstellungen der Generierung so permissiv, wie die API es erlaubt; ein Safety-Block auf einer harmlosen Szene ist ein Bug im Prompt oder ein Fall fuer die lokale Route (TASK-004).

## Akzeptanzkriterien
- [ ] `agents-cli run "Schreibe Kapitel 1, Szene 1"` erzeugt eine Szene, die den Kontext aus dem Store nachweislich verwendet (Tool-Calls im `-v`-Output)
- [ ] Der Text landet ueber `write_scene` in `books/life_link/manuscript/kapitel_01.md`
- [ ] Kein Meta-Kommentar, keine Ueberschrift, keine Platzhalter im Output
- [ ] Sprachregister wird eingehalten (stichprobenhaft manuell; Eval-Metrik folgt in TASK-005)
- [ ] Modellwahl kommt ausschliesslich aus `model_for("scene")`
- [ ] Der identische Prompt liefert auf dem lokalen Modell (manueller Testlauf, sofern VM verfuegbar) eine strukturell gueltige Szene — Feinqualitaet ist Gegenstand von Plan 4

## Betroffene Dateien
- `app/agents/scene_agent.py`
- `app/prompts/scene.py`
- `app/agents/__init__.py`
