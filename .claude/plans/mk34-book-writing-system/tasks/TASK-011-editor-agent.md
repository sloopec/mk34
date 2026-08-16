# TASK-011: Editor Agent (Lektorat)
Status: ⏳ pending
Depends-on: [TASK-008]
Parallel: yes

## Description
Lektorats-Agent — prueft und ueberarbeitet Rohtext.

- **Input:** roher Szenentext (`{scene_draft}` aus dem State) + `{scene_context}` + optional `{continuity_report}`
- **Output:** ueberarbeitete Fassung + strukturierte Anmerkungen
- **Modell:** `model_for("editor")` → `anthropic/claude-opus-5`

Prueft:
- Stilkonsistenz gegen `style_guide.md`
- Sprachregister pro Figur (David = Laie, Sarah = wissenschaftlich)
- Pacing und Spannungsbogen
- Show-don't-tell
- ELI5-Qualitaet: Wissenschaft als Metapher im Dialog, nicht als Lexikoneintrag

Der Editor laeuft **auch ueber lokal generierte Szenen** — das ist der Mechanismus, der die Stilkonsistenz ueber Modellgrenzen hinweg sichert (Phase 4).

Zusaetzlich ein `QualityChecker` (`BaseAgent`), der `EventActions(escalate=True)` setzt, sobald die Rubrik bestanden ist — Basis fuer den `LoopAgent` in TASK-013.

```python
class QualityChecker(BaseAgent):
    async def _run_async_impl(self, ctx):
        verdict = ctx.session.state.get("editor_verdict")
        if verdict and verdict.get("grade") == "pass":
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            yield Event(author=self.name)
```

## Acceptance Criteria
- [ ] Editor liefert ueberarbeiteten Text **und** ein strukturiertes Verdikt (`grade`, `issues[]`)
- [ ] Registerverletzungen werden zuverlaessig erkannt und korrigiert (Testfall: David sagt „Naniten")
- [ ] `QualityChecker` eskaliert korrekt bei `pass` und nicht bei `needs_revision`
- [ ] Editor aendert keine Handlungsfakten, nur Sprache/Stil/Pacing — Plotaenderungen werden als Anmerkung ausgegeben
- [ ] Der Editor laeuft nachweislich auch ueber lokal generierten Text

## Affected Files
- `app/agents/editor_agent.py`
- `app/agents/quality_checker.py`
- `app/prompts/editor.py`
- `app/schemas.py` (`EditorVerdict`)
