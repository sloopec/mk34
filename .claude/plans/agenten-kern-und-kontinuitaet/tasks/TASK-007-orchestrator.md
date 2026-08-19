# TASK-007: Orchestrator als Coordinator-Root-Agent
Status: ⏳ ausstehend
Abhängig von: [TASK-004, TASK-005, TASK-006]
Parallel: nein
*(vormals TASK-012 im Gesamtplan)*

## Beschreibung
`root_agent` wird auf den Orchestrator umgestellt (ADK Coordinator-Pattern).

```python
root_agent = Agent(
    name="orchestrator",
    model=model_for("orchestrator"),        # Start: gemini-3.7-flash (E6)
    description="Koordiniert die Buch-Agenten.",
    instruction=ORCHESTRATOR_INSTRUCTION,
    sub_agents=[plot_agent, editor_agent],  # scene_agent kommt in Plan 3 dazu
    tools=[AgentTool(character_agent), list_chapters, chapter_stats],
    before_agent_callback=initialize_state,
)
app = App(name="app", root_agent=root_agent)
```

Zwei Einbindungsarten bewusst getrennt:
- **`sub_agents`** — Agenten, die einen ganzen Turn uebernehmen duerfen (Plot, Editor; ab Plan 3 auch Scene/Pipeline).
- **`AgentTool`** — Spezialisten, die innerhalb eines Turns konsultiert werden und antworten (Character, spaeter Continuity/Research).

Der Orchestrator produziert **keinen** kreativen Text. Instruction muss das explizit sagen, sonst schreibt das Modell die Antwort selbst statt zu delegieren.

Zustandsuebergaben laufen ueber `session.state` (`active_chapter`, `active_scene`, `scene_context`, `scene_beat`, `character_brief`, `scene_draft`), nicht ueber Prosa im Prompt.

`App(name="app")` muss dem Agent-Verzeichnis entsprechen — sonst „Session not found" beim Eval.

Hinweis zur Planaufteilung: die Registrierung des Scene Agent als Sub-Agent und das Routing „Schreibe 3.2 → Pipeline mit Szenen-Schritt" erfolgen in `szenen-und-lokales-llm/TASK-003`; die Instruction wird dort erweitert, nicht neu geschrieben.

## Akzeptanzkriterien
- [ ] `root_agent` ist der Orchestrator; `agents-cli playground` zeigt Delegation an die richtigen Sub-Agents
- [ ] „Entwickle Akt 2" geht an den Plot Agent, „Ueberarbeite diesen Text: ..." an den Editor
- [ ] Der Orchestrator schreibt selbst keinen kreativen Text
- [ ] `initialize_state` verhindert `KeyError` auf allen `{state_key}`-Injections
- [ ] Sub-Agents werden ueber Factory-Funktionen instanziiert (kein „agent already has a parent")
- [ ] Modellwahl kommt ausschliesslich aus `model_for("orchestrator")`

## Betroffene Dateien
- `app/agent.py`
- `app/prompts/orchestrator.py`
- `app/callbacks.py`
