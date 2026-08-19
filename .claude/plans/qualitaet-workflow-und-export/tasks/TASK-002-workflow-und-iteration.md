# TASK-002: Workflow und Iteration (Feedback, Varianten, CLI)
Status: ⏳ ausstehend
Abhängig von: [TASK-001]
Parallel: nein
*(vormals TASK-020 im Gesamtplan)*

## Beschreibung
Der Autoren-Workflow. Erst hier kommt die eigene CLI; bis dahin genuegten `agents-cli run` und `agents-cli playground`.

**1. Feedback-Loop**
`mk34 feedback --chapter 3 "Dialog klingt steif, mehr Umgangssprache"` — der Editor ueberarbeitet gezielt den genannten Aspekt, Diff-Ansicht alt/neu.

**2. Varianten-System**
`mk34 write --chapter 3 --scene 2 --variants 3` — drei Fassungen derselben Szene plus Vergleich mit Staerken/Schwaechen.
Achtung Laufzeit auf der lokalen Route: 2–5 Min pro Szene → 6–15 Min fuer drei Varianten (siehe `plan.md` → Offene Frage #1: Batch-/Nacht-Modus?). Auf der Gemini-Route ist das unkritisch.

**3. Rewrite-Modes**
`--mode tighter` (kuerzen), `--mode expand` (ausbauen), `--mode pov-switch --character Sarah` (Perspektivwechsel).

**4. Session-Rewind**
```python
await runner.rewind_async(user_id=..., session_id=...,
                          rewind_before_invocation_id=...)
```
Setzt Session-State und Artifacts zurueck, **nicht** app-/user-scoped State und **nicht** die Manuskriptdateien. Dateiseitige Rueckabwicklung laeuft ueber Git — Branching fuer alternative Plot-Straenge, Snapshot-Commit vor grossen Aenderungen.

Die Vorbedingung steht seit Plan 1 (E3): `DatabaseSessionService` auf SQLite. Keine Migration noetig; alle seit Plan 1 entstandenen Sessions sind rewindbar.

**5. Manuskript-Statistiken**
Wortzahl pro Kapitel/gesamt, Figuren-Auftritte, Spannungskurve (Plot-Agent bewertet Pacing), Lesezeit-Schaetzung.

**6. CLI** — duenner Typer-Wrapper ueber den ADK-`Runner`. Enthaelt **keine** Agentenlogik; jedes Kommando mappt auf einen Runner-Aufruf.

## Akzeptanzkriterien
- [ ] `mk34 feedback|write|rewrite|stats` implementiert, alle ueber den ADK-Runner
- [ ] Diff-Ansicht alt/neu funktioniert
- [ ] Varianten-Generierung liefert n Fassungen plus Vergleichsanalyse
- [ ] Alle drei Rewrite-Modes funktionieren
- [ ] `rewind_async` funktioniert gegen die seit Plan 1 persistente SQLite-Session; Grenzen (keine Dateiruecknahme, kein app-/user-scoped State) sind dokumentiert
- [ ] Git-Branching-Workflow fuer Plot-Alternativen ist in `docs/` beschrieben
- [ ] Statistiken sind korrekt gegen ein Fixture-Manuskript (pytest)
- [ ] `agents-cli eval compare` zeigt keine Regression gegenueber der Plan-3-Baseline

## Betroffene Dateien
- `app/cli/__init__.py`, `app/cli/main.py`
- `app/tools/manuscript.py` (Statistiken, Diff)
- `app/agents/rewrite_agent.py`
- `pyproject.toml` (Console-Script `mk34`)
- `docs/WORKFLOW.md`
