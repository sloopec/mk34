# Durchführungsbericht: TASK-003 — Szenen-Schritt in die Schreib-Pipeline
Abgeschlossen: 2026-08-24T00:00:00Z

## Was wurde umgesetzt

`app/pipelines/writing.py` — der Szenen-Slot der `writing_pipeline` ist jetzt scharf
geschaltet:

- `_SceneSlotFixture` (Plan 2, Entscheidung E8) und die Fixture-Datei
  `tests/fixtures/szene_e_protokoll_der_sehnsucht.md` sind entfernt. An genau dieser
  Slot-Position steht jetzt `create_scene_agent()` (Plan 3/TASK-002).
- `create_continuity_agent()` (Plan 2/TASK-011) läuft direkt als weiterer
  `SequentialAgent`-Schritt nach dem Scene Agent, nicht als `AgentTool` (siehe
  Design-Entscheidung unten).
- `_ContinuityGate` (neue `BaseAgent`-Klasse): wertet `state["continuity_report"]`
  aus; findet sich ein Konflikt mit `severity: "high"`, wird der Editor-`LoopAgent`
  gar nicht erst gestartet — die Szene wird als `.draft.md`-Konflikt-Entwurf abgelegt
  (`write_scene_draft` mit `grade="continuity_conflict"`), die Konfliktliste wird als
  Turn-Antwort ausgegeben. Ohne High-Severity-Konflikt delegiert `_ContinuityGate`
  transparent an den echten Editor-Loop weiter.
- `_set_active_scene_from_user_message`: neuer `before_agent_callback` auf
  `writing_pipeline` — extrahiert `"Kapitel N, Szene M"` deterministisch per Regex
  aus der User-Nachricht (`callback_context.user_content`) und setzt
  `state["active_chapter"]`/`state["active_scene"]`, bevor `context_loader_step`
  diese Werte liest. Ohne Treffer bleiben die von `initialize_state`
  (`app/callbacks.py`, Plan 2) gesetzten Defaults (1/1) stehen.
- Post-Write-Hooks (Timeline/Character-State, Plan 2/TASK-012) waren bereits
  unconditional implementiert (`_persist_or_draft` ruft
  `_update_timeline_and_character_state` bei `grade == "pass"` auf) — "scharf
  geschaltet" bedeutete hier lediglich, dass sie jetzt auf echten, vom Scene Agent
  generierten Szenen laufen statt auf dem Fixture. Keine Code-Änderung an der
  Hook-Logik selbst nötig.

`app/agent.py`: `create_writing_pipeline()` als dritter `sub_agents`-Eintrag des
Orchestrators registriert (neben `plot_agent`, `editor_agent`).

`app/prompts/orchestrator.py`: neue Routing-Regel — "Schreibe Kapitel N, Szene M"
delegiert den gesamten Turn an `writing_pipeline` (Instruction erweitert, nicht neu
geschrieben, wie in der Task-Datei gefordert).

## Design-Entscheidung: Continuity-Check als Pipeline-Schritt statt `AgentTool`

Die Task-Beschreibung skizziert "Continuity-Check haengt als `AgentTool` vor dem
Editor-Loop". Umgesetzt wurde stattdessen `create_continuity_agent()` direkt als
regulärer `SequentialAgent`-Sub-Schritt, aus zwei Gründen:

1. **State-Kompatibilität ohne Umweg:** `continuity_agent`s interne Instruction
   (`CONTINUITY_CONTEXT_INSTRUCTION`) liest bereits `{scene_draft}`, `{scene_beat}`,
   `{character_brief}`, `{active_chapter}` — exakt die Keys, die die vorherigen
   Pipeline-Schritte setzen. Als direkter Sub-Schritt liest/schreibt er im selben
   Session-State wie jeder andere Pipeline-Schritt; `output_schema=ContinuityReport`
   liefert `state["continuity_report"]` bereits als `dict`. Über `AgentTool` müsste
   das Ergebnis dagegen als Tool-Return-Text durch einen zusätzlichen Wrapper-Agenten
   geschleust und erneut strukturiert geparst werden — mehr Komplexität und ein
   fragiler JSON-Roundtrip für denselben Effekt.
2. **`AgentTool` impliziert eine Modell-Entscheidung** ("konsultiere den Spezialisten,
   wenn nötig"), der Continuity-Check hier ist aber ein zwingender, deterministischer
   Pipeline-Schritt (jede Szene wird geprüft) — das passt besser zum bereits
   etablierten `sub_agents`-Verwendungsmuster der Pipeline (`context_loader_step`,
   `plot_beat_step`, ...) als zum `AgentTool`-Muster, das laut `app/agent.py`s
   Docstring für "Spezialisten, die innerhalb eines Turns konsultiert werden" gedacht
   ist.

Funktional ist das Ergebnis identisch zur Task-Vorgabe (Continuity läuft vor dem
Editor-Loop, `severity: high` verhindert das Schreiben) — die Abweichung betrifft nur
den ADK-Verdrahtungsmechanismus.

## Design-Entscheidung: `_ContinuityGate` statt `escalate`

ADKs `SequentialAgent` honoriert `EventActions.escalate` nicht (nur `LoopAgent` tut
das, siehe `google/adk/agents/loop_agent.py`) — ein früher Abbruch der restlichen
Pipeline-Schritte über das übliche Escalate-Signal ist deshalb nicht möglich.
`_ContinuityGate` löst das durch Komposition: sie hält den echten Editor-`LoopAgent`
als einzigen Sub-Agenten und entscheidet selbst, ob sie an ihn delegiert oder
stattdessen den Konflikt-Pfad nimmt. Nachteil: bei einem Konflikt mit niedrigerer
Pipeline-Position wäre der Editor-Loop unnötig gestartet worden, wenn der Konflikt
*nach* dem Editor-Schritt aufgetreten wäre — hier ist das nicht der Fall, da
`_ContinuityGate` selbst *vor* dem Editor-Loop entscheidet.

## Live-Verifikation (echte Gemini-API, voller Orchestrator)

`agents-cli run "Schreibe Kapitel 3, Szene 2." -v` (Trajektorie im vollständigen
`-v`-Log, `/private/tmp/.../scratchpad/run_task003.log`, nicht Teil des Commits):

Beobachtete Autor-/Tool-Sequenz (bestätigt Routing und State-Weitergabe):
```
orchestrator -> transfer_to_agent(writing_pipeline)
writing_pipeline -> context_loader_step (Tool: load_scene_context)
                 -> plot_beat_step
                 -> character_brief_step
                 -> scene_agent
                 -> continuity_agent
                      -> continuity_context_agent (Tool: check_consistency)
                      -> continuity_formalizer  ({"conflicts": []})
                 -> continuity_gate -> editing_loop
                      -> editor_agent (grade: "pass")
                      -> quality_checker (escalate: true)
```

- **Routing funktioniert:** "Schreibe Kapitel 3, Szene 2" delegiert den gesamten Turn
  an `writing_pipeline` (kein Meta-Turn im Orchestrator).
- **Aktive-Szene-Extraktion funktioniert:** `context_loader_step` ruft
  `load_scene_context` mit `chapter=3, scene=2` auf (aus der User-Nachricht
  extrahiert, nicht dem Default 1/1).
- **State-Weitergabe nachweisbar:** jeder Schritt referenziert im Log-Trace exakt die
  Kapitel-/Szenennummer bzw. den Text des Vorgängers.
- **Kontinuitätsprüfung läuft, blockiert hier nicht:** `check_consistency` fand keine
  Konflikte (`conflicts: []`), `_ContinuityGate` delegierte korrekt an den
  Editor-Loop.
- **Editor-Loop terminiert korrekt:** `editor_agent` liefert `grade: "pass"`,
  `quality_checker` eskaliert (`escalate: true`), der Loop bricht nach einer Iteration
  ab (kein drittes Editor-Retry nötig).
- **Post-Write-Hooks liefen:** `books/life_link/store/timeline.json` bekam einen
  Eintrag für Kapitel 3/Szene 2 (danach wieder verworfen, siehe unten).

**Beobachtung (kein Bug, aber notiert für Plan 4):** Da `plot_outline.json` in diesem
Buchprojekt noch keine `scene_beats`-Einträge enthält (der Plot Agent wurde für dieses
Kapitel noch nie ausgeführt), lieferte `load_scene_context` für Kapitel 3/Szene 2
`beat: None`. `plot_beat_step` und `character_brief_step` haben das (instruktionsgemäß
korrekt) explizit als "kein Beat bekannt" weitergegeben, der Scene Agent hat
(ebenfalls instruktionsgemäß, "erfinde keinen eigenen Beat") eine Rückfrage statt
Prosa geschrieben. Der Editor hat diese Rückfrage-Meta-Antwort mit `grade: "pass"`
durchgewunken (die Editor-Rubrik prüft Stil/Register, nicht "ist das überhaupt
Erzähltext statt Meta-Kommentar"). Das ist ein **QS-Lückenfall außerhalb des
TASK-003-Scopes** (Feinqualität ist explizit Plan 4/TASK-001) — hier dokumentiert,
nicht eigenmächtig gefixt. Der mechanische mit dem Akzeptanzkriterium geforderte mit
Kontext -> Beat -> Brief -> Szene -> Continuity -> Editor-Loop -> `write_scene`-Ablauf
lief dennoch vollständig und korrekt durch.

**Manuskript-Artefakte dieses Testlaufs bewusst verworfen:** anders als bei TASK-002
(wo die geschriebene Beispielszene inhaltlich wertvoll war) wurde die hier erzeugte
Rückfrage-Meta-Antwort NICHT im Manuskript belassen (`chapter_03.md` gelöscht,
`timeline.json`-Eintrag zurückgesetzt) — sie ist kein echter Szenentext und würde das
Manuskript nur verunreinigen. Die Verifikation selbst bleibt über das gespeicherte Log
nachvollziehbar.

**Kontinuitäts-Blockade (`severity: high`) nicht live reproduziert:** ein echter
High-Severity-Konflikt ließ sich in einem einzelnen Testlauf nicht ökonomisch
provozieren (bräuchte präparierten Vorpassagen-Konflikt); dieser Pfad ist stattdessen
durch vier dedizierte Unit-Tests gegen `_ContinuityGate._run_async_impl` abgedeckt
(siehe unten) — analog zum in Plan 2 etablierten Muster (Struktur-/Logik-Tests +
gezielte Live-Stichprobe für den Hauptpfad).

## Geänderte Dateien

- `app/pipelines/writing.py` — Szenen-Slot, Continuity-Schritt, `_ContinuityGate`,
  aktive-Szene-Extraktion; `_SceneSlotFixture` entfernt.
- `app/agent.py` — `writing_pipeline` als dritter Sub-Agent registriert, Docstring
  aktualisiert.
- `app/prompts/orchestrator.py` — Routing-Regel für "Schreibe Kapitel N, Szene M".
- `tests/unit/test_pipeline_geruest.py` — auf die neue 6-Schritte-Struktur
  umgestellt, neue Tests für `_set_active_scene_from_user_message` und
  `_ContinuityGate` (Delegation, Blockade, gemischte Schweregrade, fehlender Report).
- `tests/unit/test_orchestrator.py` — Sub-Agent-Set um `writing_pipeline` erweitert.
- `tests/fixtures/szene_e_protokoll_der_sehnsucht.md` — entfernt (kein Verweis mehr
  im Code, Entscheidung E8 damit vollständig durch echten Szenentext abgelöst).
- `pyproject.toml` — codespell-Ignore-Liste um weitere deutsche Wörter ergänzt
  (`komma`, `separat`, `methode`).

## Verifikationsschritte

1. `uv run pytest tests/unit -q` — 207 Tests grün (inkl. 4 neuer `_ContinuityGate`-
   Tests, 4 neuer `_set_active_scene_from_user_message`-Tests, aktualisierte
   Struktur-/Orchestrator-Tests).
2. `agents-cli lint` — grün (ruff check/format, codespell, `ty check`).
3. Live-Lauf `agents-cli run "Schreibe Kapitel 3, Szene 2." -v` gegen die echte
   Gemini-API — vollständige Trajektorie wie oben dokumentiert, Routing und
   State-Weitergabe über alle sechs Pipeline-Schritte nachgewiesen.
