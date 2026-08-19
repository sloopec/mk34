# TASK-005: Character Agent und Figuren-Tools
Status: ⏳ ausstehend
Abhängig von: [TASK-003]
Parallel: ja
*(vormals TASK-010 im Gesamtplan)*

## Beschreibung
Agent fuer Figurenkonsistenz und -entwicklung, plus die zugehoerigen Tools in `app/tools/characters.py`.

**Tools:**
- `get_character(name: str) -> dict`
- `update_character(name: str, development: str) -> dict`
- `get_character_arc(name: str) -> dict`
- `get_knowledge_state(name: str, chapter: int) -> dict` — was weiss die Figur zu diesem Zeitpunkt?

**Agent:**
- Input: Figurenname + Szenenkontext
- Output: figurengerechte Dialogvorschlaege, Reaktionen, innere Konflikte
- Modell: `model_for("character")` → Start `gemini-3.1-pro-preview` (E6); spaeter `anthropic/claude-opus-5`
- Validierung: passt das Verhalten zur bisherigen Entwicklung und zum Wissensstand?

Sprachregister ist hier zentral und stammt aus `style_guide.md`:
David = Laienbegriffe, Sarah/Voss/Aris = praezise wissenschaftliche Terminologie.

Einbindung: als **`AgentTool`** in Orchestrator/Editor (und ab Plan 3 im Scene Agent) — der aufrufende Agent behaelt die Kontrolle und bekommt einen Figuren-Brief zurueck, statt den Turn abzugeben.

```python
from google.adk.tools import AgentTool
tools=[AgentTool(character_agent), ...]
```

## Akzeptanzkriterien
- [ ] Alle vier Tools implementiert, dict-Return, Docstrings, Pfadsicherung
- [ ] Character Agent liefert einen Figuren-Brief mit Register, Motivation, aktuellem Wissensstand
- [ ] `AgentTool`-Einbindung funktioniert (Tool-Call im `-v`-Output sichtbar)
- [ ] `update_character` schreibt idempotent nach `characters.json`
- [ ] Der Agent widerspricht explizit, wenn eine Szene Wissen voraussetzt, das die Figur nicht haben kann
- [ ] Modellwahl kommt ausschliesslich aus `model_for("character")`

## Betroffene Dateien
- `app/agents/character_agent.py`
- `app/prompts/character.py`
- `app/tools/characters.py`
- `tests/unit/test_character_tools.py`
