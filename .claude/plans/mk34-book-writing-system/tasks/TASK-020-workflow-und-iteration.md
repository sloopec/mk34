# TASK-020: Workflow und Iteration (Feedback, Varianten, CLI)
Status: ⏳ ausstehend
Abhängig von: [TASK-019]
Parallel: nein

## Beschreibung
Phase 5 — der Autoren-Workflow. Erst hier kommt die eigene CLI; bis dahin genuegten `agents-cli run` und `agents-cli playground`.

**1. Feedback-Loop**
`mk34 feedback --chapter 3 "Dialog klingt steif, mehr Umgangssprache"` — der Editor ueberarbeitet gezielt den genannten Aspekt, Diff-Ansicht alt/neu.

**2. Varianten-System**
`mk34 write --chapter 3 --scene 2 --variants 3` — drei Fassungen derselben Szene plus Vergleich mit Staerken/Schwaechen.
Achtung Laufzeit: lokal 2–5 Min pro Szene → 6–15 Min fuer drei Varianten (Offene Frage #8: Batch-/Nacht-Modus?).

**3. Rewrite-Modes**
`--mode tighter` (kuerzen), `--mode expand` (ausbauen), `--mode pov-switch --character Sarah` (Perspektivwechsel).

**4. Session-Rewind**
Korrekter ADK-Mechanismus:
```python
await runner.rewind_async(user_id=..., session_id=...,
                          rewind_before_invocation_id=...)
```
Setzt Session-State und Artifacts zurueck, **nicht** app-/user-scoped State und **nicht** die Manuskriptdateien. Dateiseitige Rueckabwicklung laeuft ueber Git — Branching fuer alternative Plot-Straenge, Snapshot-Commit vor grossen Aenderungen.

Die Vorbedingung steht bereits: `DatabaseSessionService` auf SQLite ist laut Entscheidung E3 seit TASK-001 aktiv. In dieser Phase ist daher **keine Migration** noetig — und alle seit Phase 1 entstandenen Sessions sind rewindbar, statt erst ab dem Umstellungszeitpunkt.

**5. Manuskript-Statistiken**
Wortzahl pro Kapitel/gesamt, Figuren-Auftritte, Spannungskurve (Plot-Agent bewertet Pacing), Lesezeit-Schaetzung.

**6. CLI** — duenner Typer-Wrapper ueber den ADK-`Runner`. Enthaelt **keine** Agentenlogik; jedes Kommando mappt auf einen Runner-Aufruf.

## Akzeptanzkriterien
- [ ] `mk34 feedback|write|rewrite|stats` implementiert, alle ueber den ADK-Runner
- [ ] Diff-Ansicht alt/neu funktioniert
- [ ] Varianten-Generierung liefert n Fassungen plus Vergleichsanalyse
- [ ] Alle drei Rewrite-Modes funktionieren
- [ ] `rewind_async` funktioniert gegen die seit Phase 1 persistente SQLite-Session; Grenzen (keine Dateiruecknahme, kein app-/user-scoped State) sind dokumentiert
- [ ] Keine Session-Migration noetig — bestehende Sessions aus fruehen Phasen sind rewindbar
- [ ] Git-Branching-Workflow fuer Plot-Alternativen ist in `docs/` beschrieben
- [ ] Statistiken sind korrekt gegen ein Fixture-Manuskript (pytest)
- [ ] `agents-cli eval compare` zeigt keine Regression gegenueber Phase 4

## Betroffene Dateien
- `app/cli/__init__.py`, `app/cli/main.py`
- `app/tools/manuscript.py` (Statistiken, Diff)
- `app/agents/rewrite_agent.py`
- `app/app_utils/services.py` (Session-Service-Wahl)
- `pyproject.toml` (Console-Script `mk34`)
- `docs/WORKFLOW.md`
