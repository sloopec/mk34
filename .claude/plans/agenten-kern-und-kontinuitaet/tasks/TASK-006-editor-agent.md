# TASK-006: Editor Agent (Lektorat)
Status: ⏳ ausstehend
Abhängig von: [TASK-003]
Parallel: ja
*(vormals TASK-011 im Gesamtplan)*

## Beschreibung
Lektorats-Agent — prueft und ueberarbeitet Rohtext.

- **Input:** roher Szenentext (`{scene_draft}` aus dem State) + `{scene_context}` + optional `{continuity_report}`
- **Output:** ueberarbeitete Fassung + strukturierte Anmerkungen
- **Modell:** `model_for("editor")` → Start `gemini-3.1-pro-preview` (E6); spaeter `anthropic/claude-opus-5`

Prueft:
- Stilkonsistenz gegen `style_guide.md`
- Sprachregister pro Figur (David = Laie, Sarah = wissenschaftlich)
- Pacing und Spannungsbogen
- Show-don't-tell
- ELI5-Qualitaet: Wissenschaft als Metapher im Dialog, nicht als Lexikoneintrag

In diesem Plan laeuft der Editor ueber **vorgelegten** Text (Fixture bzw. Autoren-Rohtext) — der Scene Agent existiert noch nicht. Ab Plan 3 uebernimmt er zusaetzlich die Szenen-Drafts; ab Plan 4 ist er der Qualitaetsanker fuer lokal generierte Szenen (Angleichung ueber Modellgrenzen hinweg).

Zusaetzlich ein `QualityChecker` (`BaseAgent`), der `EventActions(escalate=True)` setzt, sobald die Rubrik bestanden ist — Basis fuer den `LoopAgent` in TASK-008.

```python
class QualityChecker(BaseAgent):
    async def _run_async_impl(self, ctx):
        verdict = ctx.session.state.get("editor_verdict")
        if verdict and verdict.get("grade") == "pass":
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            yield Event(author=self.name)
```

## Akzeptanzkriterien
- [ ] Editor liefert ueberarbeiteten Text **und** ein strukturiertes Verdikt (`grade`, `issues[]`)
- [ ] Registerverletzungen werden zuverlaessig erkannt und korrigiert (Testfall: David sagt „Naniten")
- [ ] `QualityChecker` eskaliert korrekt bei `pass` und nicht bei `needs_revision`
- [ ] Editor aendert keine Handlungsfakten, nur Sprache/Stil/Pacing — Plotaenderungen werden als Anmerkung ausgegeben
- [ ] Modellwahl kommt ausschliesslich aus `model_for("editor")`

## Betroffene Dateien
- `app/agents/editor_agent.py`
- `app/agents/quality_checker.py`
- `app/prompts/editor.py`
- `app/schemas.py` (`EditorVerdict`)
