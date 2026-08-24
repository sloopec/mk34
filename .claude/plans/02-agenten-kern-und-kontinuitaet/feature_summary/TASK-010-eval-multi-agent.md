# Feature-Zusammenfassung: TASK-010 — Eval für Multi-Agent-Trajektorie

## Was wurde umgesetzt

Die Qualitätsprüfung wächst von "liefert der Agent eine gute Antwort" zu "nimmt das System den
richtigen Weg dorthin": drei neue Prüfkriterien wurden angelegt — nutzt der Agent die richtigen
Werkzeuge mit den richtigen Argumenten, ist der eingeschlagene Weg logisch und effizient, und wird
Wissenschaft verständlich statt trocken vermittelt. Vier neue Testfälle decken die
charakteristischen Mehr-Schritt-Anfragen an das System ab: Handlungsentwicklung, Figurenreaktion,
Lektorat und eine zusammengesetzte Anfrage, die alle drei Spezialisten in einem Zug fordert.

Beim Versuch, diese Testfälle tatsächlich auszuführen, wurde ein zweiter, unabhängiger Fehler im
eingesetzten Kommandozeilenwerkzeug (`agents-cli`) gefunden, der die komplette
Bewertungs-Befehlskette lahmlegt — zusätzlich zu dem bereits zuvor gefundenen. Beide Fehler
liegen nachweislich im Drittanbieter-Werkzeug, nicht im hier gebauten System.

## Geänderte Dateien

- `tests/eval/datasets/multi-agent.json`
- `tests/eval/mk34_eval/rubrics/tool_use_quality.md`, `trajectory_quality.md`, `eli5_quality.md`
- `tests/eval/tool_use_quality_metric.py`, `trajectory_quality_metric.py`, `eli5_quality_metric.py`
- `tests/eval/eval_config.yaml`

## Nächster Schritt

TASK-011 (Continuity Agent mit Retrieval) — dieser Task hat ebenfalls ein Eval-Gate
(`continuity.json`, 0 falsch-negative Erkennungen), das auf denselben blockierten
`agents-cli eval`-Befehlspfad trifft. Diese Einschränkung wurde dem User als eigener Punkt
gemeldet.
