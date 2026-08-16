# TASK-012: Orchestrator als Coordinator-Root-Agent
Status: ⏳ ausstehend
Abhängig von: [TASK-009, TASK-010, TASK-011]
Parallel: nein

## Beschreibung
`root_agent` wird vom Scene Agent auf den Orchestrator umgestellt (ADK Coordinator-Pattern).

```python
root_agent = Agent(
    name="orchestrator",
    model=model_for("orchestrator"),        # anthropic/claude-sonnet-5
    description="Koordiniert die Buch-Agenten.",
    instruction=ORCHESTRATOR_INSTRUCTION,
    sub_agents=[plot_agent, scene_agent, editor_agent],
    tools=[AgentTool(character_agent), list_chapters, chapter_stats],
    before_agent_callback=initialize_state,
)
app = App(name="app", root_agent=root_agent)
```

Zwei Einbindungsarten bewusst getrennt:
- **`sub_agents`** — Agenten, die einen ganzen Turn uebernehmen duerfen (Plot, Scene, Editor).
- **`AgentTool`** — Spezialisten, die innerhalb eines Turns konsultiert werden und antworten (Character, spaeter Continuity/Research).

Der Orchestrator produziert **keinen** kreativen Text. Instruction muss das explizit sagen, sonst schreibt Sonnet die Szene selbst statt zu delegieren.

Zustandsuebergaben laufen ueber `session.state` (`active_chapter`, `active_scene`, `scene_context`, `scene_beat`, `character_brief`, `scene_draft`), nicht ueber Prosa im Prompt.

`App(name="app")` muss dem Agent-Verzeichnis entsprechen — sonst „Session not found" beim Eval.

## Akzeptanzkriterien
- [ ] `root_agent` ist der Orchestrator; `agents-cli playground` zeigt Delegation an die richtigen Sub-Agents
- [ ] „Entwickle Akt 2" geht an den Plot Agent, „Schreibe 3.2" an die Pipeline, „Ueberarbeite 3.2" an den Editor
- [ ] Der Orchestrator schreibt selbst keinen Szenentext
- [ ] `initialize_state` verhindert `KeyError` auf allen `{state_key}`-Injections
- [ ] Sub-Agents werden ueber Factory-Funktionen instanziiert (kein „agent already has a parent")

## Betroffene Dateien
- `app/agent.py`
- `app/prompts/orchestrator.py`
- `app/callbacks.py`
