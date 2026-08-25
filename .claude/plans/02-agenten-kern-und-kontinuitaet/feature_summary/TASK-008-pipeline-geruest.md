# Feature-Zusammenfassung: TASK-008 — Schreib-Pipeline-Gerüst (ohne Szenen-Schritt)

## Was wurde umgesetzt

Das Grundgerüst der eigentlichen Schreib-Kette steht: Kontext laden → Beat bestätigen →
Figuren-Brief holen → (Platzhalter für die noch fehlende Szenen-Generierung) → Lektorats-Schleife
mit automatischem Abbruch, sobald der Text "fertig" ist. Diese Kette läuft deterministisch in
fester Reihenfolge, nicht als freie Entscheidung eines Modells — Verlässlichkeit ist hier
wichtiger als Flexibilität.

Da der eigentliche Text-generierende Agent erst in einem späteren Bauabschnitt entsteht, wird an
dieser Stelle testweise eine bereits vorhandene, sorgfältig geschriebene Beispielszene aus der
Buchvorlage eingesetzt — so lässt sich schon jetzt die komplette Lektorats-Logik (inklusive
Abbruch bei Erfolg und Notfall-Speicherung bei Misserfolg) unter realen Bedingungen prüfen.

Ein echter Testlauf hat die komplette Kette von Anfang bis Ende bestätigt: Alle Schritte laufen
in der richtigen Reihenfolge, der Zustand wird korrekt weitergereicht, und die
Lektorats-Entscheidung wird zuverlässig persistiert.

## Geänderte Dateien

- `app/pipelines/writing.py`
- `app/agent.py`
- `app/tools/manuscript.py`
- `tests/fixtures/szene_e_protokoll_der_sehnsucht.md`
- `tests/unit/test_pipeline_geruest.py`, `test_manuscript_tools.py`

## Nächster Schritt

TASK-009 (Smoke-Test und Lint) — verifiziert das gesamte bisher gebaute Multi-Agenten-System noch
einmal im Zusammenspiel, bevor in TASK-010 die formale Multi-Agent-Eval aufgesetzt wird.
