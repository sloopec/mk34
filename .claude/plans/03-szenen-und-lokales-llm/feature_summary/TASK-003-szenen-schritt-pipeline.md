# Feature-Zusammenfassung: TASK-003 — Szenen-Schritt in die Schreib-Pipeline

## Was wurde umgesetzt

Ab sofort funktioniert der komplette Schreib-Befehl end-to-end: sagt man dem System
„Schreibe Kapitel 3, Szene 2", lädt es selbstständig den passenden Kontext, ermittelt
den Beat und die richtige Figuren-Perspektive, lässt den Scene Agent den Text
schreiben, prüft ihn automatisch auf Widersprüche zum bisherigen Manuskript und
schickt ihn durch eine Lektorats-Schleife, bevor er final im Manuskript landet. Bisher
stand an der Stelle des eigentlichen Schreibens nur ein Platzhaltertext (Plan 2); jetzt
schreibt der echte Scene Agent (TASK-002) die Szene.

Neu ist außerdem eine Sicherheitsprüfung: findet die Kontinuitätsprüfung einen
schwerwiegenden Widerspruch zum bisherigen Kanon (z. B. eine Figur weiß etwas, das sie
zu diesem Zeitpunkt der Handlung noch nicht wissen kann), wird die Szene NICHT
gespeichert — stattdessen bekommt man die Konfliktliste als Antwort und die Szene
landet als Entwurf mit Vermerk, statt fälschlich im finalen Manuskript zu erscheinen.

Ein Live-Test mit „Schreibe Kapitel 3, Szene 2" hat den kompletten Ablauf bestätigt:
Routing, Kapitel-/Szenennummer-Erkennung aus der Anfrage, Kontextübergabe zwischen
allen Schritten, Kontinuitätsprüfung und Lektorats-Abschluss funktionieren wie
vorgesehen. Da für dieses spezielle Kapitel noch kein Plot-Beat im System hinterlegt
ist, hat das System ehrlich nachgefragt statt eine Szene zu erfinden — ein erwartetes,
korrektes Verhalten, aber auch ein Hinweis, dass die Feinabstimmung der Editor-Prüfung
(erkennt der Editor eine Rückfrage als "kein echter Szenentext"?) noch offen ist und in
Plan 4 aufgegriffen werden sollte.

## Geänderte Dateien

- `mk34-book-agent/app/pipelines/writing.py`
- `mk34-book-agent/app/agent.py`
- `mk34-book-agent/app/prompts/orchestrator.py`
- `mk34-book-agent/tests/unit/test_pipeline_geruest.py`
- `mk34-book-agent/tests/unit/test_orchestrator.py`
- `mk34-book-agent/pyproject.toml`
- `mk34-book-agent/tests/fixtures/szene_e_protokoll_der_sehnsucht.md` (entfernt)

## Nächster Schritt

TASK-005 (Stufe A) kann jetzt die Szenen-Evals (`scene-writing.json`) gegen die
Gemini-Route dieser vollständigen Pipeline laufen lassen. TASK-004 (Content-
Klassifikation + lokales Routing) baut ebenfalls direkt hierauf auf — der
Kontinuitäts-/Editor-Ablauf steht bereits, es fehlt nur noch die Entscheidung
lokal/Cloud vor dem Scene-Agent-Schritt.
