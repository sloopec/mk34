# TASK-009: Plot Agent
Status: ⏳ ausstehend
Abhängig von: [TASK-008]
Parallel: ja

## Beschreibung
Agent fuer Plot-Entwicklung und Akt-Struktur.

- **Input:** grobe Idee oder Akt-/Phasennummer (Phase 0–5 aus `basics.md`)
- **Output:** detaillierte Szenen-Beats, Wendepunkte, Spannungsbogen
- **Modell:** `model_for("plot")` → `anthropic/claude-opus-5`
- **Tools:** `load_plot_outline(act)`, `update_plot_outline(...)`, `read_chapter_summaries()`

Strukturierte Beats via Pydantic:
```python
class SceneBeat(BaseModel):
    chapter: int
    scene: int
    pov_character: str
    location: str
    beat: str
    turning_point: bool
    tension_level: int   # 1-10
    characters_present: list[str]
```

**Fallstrick:** `output_schema` deaktiviert Tool-Calling und Delegation. Daher zweistufig — ein Agent mit Tools sammelt den Kontext (`output_key="plot_raw"`), ein nachgelagerter Agent mit `output_schema=SceneBeat` formalisiert. Beide in einem `SequentialAgent`.

Die Beats werden nach `books/life_link/store/plot_outline.json` zurueckgeschrieben; die Datei bleibt die Wahrheit.

## Akzeptanzkriterien
- [ ] Plot Agent liefert fuer eine Phase aus `basics.md` eine vollstaendige Beat-Liste
- [ ] Beats validieren gegen das `SceneBeat`-Schema
- [ ] `update_plot_outline` schreibt idempotent nach `plot_outline.json`, ohne bestehende Akte zu zerstoeren
- [ ] Beats widersprechen nicht dem etablierten Kanon (manuelle Durchsicht + spaeter Continuity-Eval)
- [ ] `agents-cli run "Entwickle Phase 2 in Szenen-Beats"` funktioniert

## Betroffene Dateien
- `app/agents/plot_agent.py`
- `app/prompts/plot.py`
- `app/schemas.py`
- `app/tools/context_loader.py` (`update_plot_outline`, `read_chapter_summaries`)
