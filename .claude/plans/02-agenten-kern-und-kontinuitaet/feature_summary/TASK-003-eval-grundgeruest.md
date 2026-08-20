# Feature-Zusammenfassung: TASK-003 — Eval-Grundgerüst und Judge-Bibliothek

## Was wurde umgesetzt

Ab diesem Task hat jeder weitere Schritt im Buch-Agenten-Projekt ein messbares Qualitäts-Gate:
eine lokale, provider-unabhängige Bewertungs-Bibliothek, die Agenten-Antworten automatisch gegen
schriftlich festgelegte Kriterien (Rubriken) beurteilt — auf einer Skala von 1 bis 5, mit
Begründung. Die Bewertung läuft komplett auf der eigenen Maschine, ohne Google-Cloud-Projekt.

Zwei erste Prüfkriterien sind eingerichtet: "Erreicht der Agent das Ziel des Users?" und "Bleibt
eine Figur in ihrem korrekten Sprachregister?" (Laie vs. Wissenschaftler:in). Ein drittes,
rein technisches Kriterium prüft automatisch auf liegen gebliebenen Platzhaltertext wie `[TODO]`.

Damit die beiden ersten Testfragen ("Wer ist Dr. Elias Voss?", "Fasse Phase 2 zusammen") tatsächlich
sinnvoll beantwortbar sind, wurde der bestehende Agent vorübergehend mit den in TASK-002 gebauten
Kontext-Loader-Werkzeugen ausgestattet — eine Übergangslösung bis zum vollständigen Orchestrator
in TASK-007.

## Geänderte Dateien

- `tests/eval/mk34_eval/` (Judge-Bibliothek, Rubriken)
- `tests/eval/eval_config.yaml`, `tests/eval/datasets/basic-dataset.json`
- `tests/eval/task_success_metric.py`, `character_voice_consistency_metric.py`
- `app/agent.py`
- `tests/unit/test_judge.py`
- `pyproject.toml`

## Bekannte Einschränkung

Der reale Testlauf (`agents-cli eval run`) konnte am Umsetzungstag nicht zu Ende geführt werden:
Das kostenlose Tageskontingent des verwendeten Gemini-API-Schlüssels ist erschöpft (20 Anfragen/Tag
für `gemini-3.7-flash`). Das ist eine externe Ressourcengrenze, kein Fehler im gebauten System —
alle Unit-Tests und die statische Qualitätsprüfung (Lint) sind grün. Der Score-Nachweis für die
beiden Testfragen wird nachgeholt, sobald das Kontingent zurückgesetzt ist.

## Nächster Schritt

TASK-004/005/006 (Plot-, Character-, Editor-Agent) — parallel geplant, jeweils mit eigenem
Eval-Case gegen dieselbe Judge-Bibliothek. Die Live-Verifikation dieser und aller folgenden
Tasks mit einem `agents-cli eval`/`run`/`playground`-Gate ist an dieselbe Kontingent-Grenze
gebunden; siehe Rückmeldung an den User zu diesem Blocker.
