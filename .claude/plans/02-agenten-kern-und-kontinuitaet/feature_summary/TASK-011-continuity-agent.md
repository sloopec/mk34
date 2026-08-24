# Feature-Zusammenfassung: TASK-011 — Continuity Agent mit Retrieval

## Was wurde umgesetzt

Ein lokaler SQLite-FTS5-Retrieval-Index über das gesamte Manuskript (netzwerkfrei, jederzeit aus
dem Manuskript reproduzierbar) sowie ein zweistufiger Continuity Agent, der neue Szenentexte auf
Widersprüche zum bisherigen Manuskript prüft: zu früh bekanntes Wissen, Zeitsprünge,
Parallelitäts-Konflikte und Verstöße gegen die Naniten-Weltregeln (z. B. "kein zentraler
Server"). Der Agent sammelt zunächst per BM25-Retrieval relevante Vorpassagen als Beleg und
formalisiert anschließend gefundene Konflikte in ein strukturiertes Verdikt
(`ContinuityReport` mit Typ, Beleg, Referenz und Schweregrad je Konflikt).

Der Retrieval-Ansatz weicht bewusst von der wörtlichen Tool-Spezifikation ab: `check_consistency`
liefert Beleg-Passagen statt bereits fertiger Konfliktlisten, weil die eigentliche
Konflikterkennung Sprachverständnis erfordert und daher dem nachgelagerten LLM-Formalisierer
obliegt — ein eingebetteter LLM-Aufruf im Tool selbst hätte gegen die Netzwerkfreiheits-Vorgabe
für den Retrieval-Pfad verstoßen.

Die Einbindung in die Schreib-Pipeline (Slot vor dem Editor-Loop) ist laut Planung erst Teil von
Plan 3; dieser Task liefert den fertigen, eigenständig nutzbaren Agenten.

## Geänderte Dateien

- `app/retrieval/index.py`, `app/retrieval/query.py` — FTS5-Index-Aufbau und BM25-Abfrage.
- `app/tools/consistency.py` — `check_consistency`-Tool.
- `app/schemas.py` — `ContinuityConflict`, `ContinuityReport`.
- `app/agents/continuity_agent.py`, `app/prompts/continuity.py` — zweistufiger Agent.
- `app/config.py` — Index-Pfad-Einstellung.
- `tests/unit/test_retrieval.py`, `tests/unit/test_continuity_agent.py` — 18 neue Unit-Tests
  (126 Unit-Tests insgesamt grün).
- `tests/eval/datasets/continuity.json`, `mk34_eval/rubrics/grounding.md`,
  `tests/eval/grounding_metric.py` — Eval-Vorbereitung (Ausführung derzeit durch bekannten
  `agents-cli`-Bug blockiert, siehe unten).

## Nächster Schritt

Zwei offene Punkte, beide außerhalb des Projekt-Codes begründet und dokumentiert:

1. Die Live-Verifikation über die echte Gemini-API konnte in diesem Task nicht abgeschlossen
   werden — drei Versuche hingen im ersten API-Aufruf fest, ein Minimaltest ohne ADK bestätigte
   ein transientes Netzwerkproblem statt eines Code-Defekts. Sollte nachgeholt werden, sobald die
   Verbindung wieder stabil ist; kein Code-Änderungsbedarf erwartet.
2. Die automatisierte Eval-Ausführung (`agents-cli eval generate`/`grade`) bleibt durch den bereits
   in TASK-003/TASK-010 dokumentierten `agents-cli`-Bug blockiert (siehe
   `docs/known-issues/agents-cli-eval-generate-missing-content.md`) — betrifft jeden Agentenbaum
   mit `before_agent_callback`, also auch den Continuity Agent, sobald er in Plan 3 an den
   Root-Orchestrator angebunden wird.

Fachlich folgt als Nächstes TASK-012 (Timeline- und Character-State-Tracking), das den
Continuity Agent um `timeline.json` und figurenbezogenen Wissensstand als zusätzliche
Retrieval-/Prüfquellen erweitern soll.
