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

Der reale Testlauf (`agents-cli eval run`) konnte auch nach Austausch des API-Schlüssels nicht
zu Ende geführt werden — `eval generate` läuft erfolgreich durch, `eval grade` scheitert
reproduzierbar an einem verifizierten Bug in `agents-cli` selbst (in beiden geprüften Versionen
1.3.1 und 1.4.0, auf unterschiedliche Weise — siehe Walkthrough für die vollständige
Root-Cause-Analyse). Zwei eigene Bugs im lokalen `custom_function`-Pfad (fehlender `__file__` im
`exec()`-Kontext, unbeabsichtigter `google-adk`-Import über `app.config`) wurden dabei gefunden
und gefixt. Die Judge-Bibliothek selbst ist vollständig unit-getestet (Gemini **und** Claude, 12
Tests). Der Score-Nachweis über den `agents-cli`-Befehlspfad ist erst möglich, wenn der
Drittanbieter-Bug behoben ist.

## Nächster Schritt

TASK-004/005/006 (Plot-, Character-, Editor-Agent) — parallel geplant, jeweils mit eigenem
Eval-Case gegen dieselbe Judge-Bibliothek. `agents-cli eval run`/`eval grade` bleiben bis zu
einem Upstream-Fix blockiert; `agents-cli run`/`playground` (Smoke-Tests) sind ein anderer
Codepfad und davon nicht betroffen.
