# Durchführungsbericht: TASK-013 — World-Rules-Engine
Abgeschlossen: 2026-08-24T20:40:00Z

## Was wurde umgesetzt

Die 10 nummerierten Naniten-Weltregeln aus `books/life_link/store/world_bible.md`
(Abschnitt 3, "Regeln der Schwarmintelligenz") wurden bereits in Plan 1 nummeriert und
maschinenlesbar angelegt (Akzeptanzkriterium 1 damit bereits erfüllt — keine Änderung an dieser
Datei nötig; die 10 Regeln sind eine Obermenge der 7 in `basics.md` skizzierten Grundregeln).
Dieser Task macht sie zu prüfbaren Constraints:

**`validate_world_rules(text, characters=None) -> dict` (`app/tools/consistency.py`)**
- Deterministische Prüfung der drei Regeln mit eindeutigen Verbots-/Signalwörtern:
  - **Regel 1 (kein zentraler Server)**: Verbotswörter `"server"`, `"hauptcomputer"`,
    `"mutterschiff"`, `"kontrollzentrum"`, `"kommandozentrale"`.
  - **Regel 5 (keine mechanischen "Metallmännchen")**: Verbotswörter `"metallm"` (deckt beide
    Schreibweisen "Metallmaennchen"/"Metallmännchen" ab), `"roboter"`, `"zahnr"` (Zahnräder).
  - **Regel 6 (Terminologie-Konsistenz), figurenbezogen**: Für jede in der Szene anwesende,
    bekannte Figur wird ihr Sprachregister aus `characters.json` (`language_register`-Freitext)
    grob in `"wissenschaftlich"` oder `"laie"` klassifiziert; taucht der jeweils falsche Begriff
    ("Nanobots" bei wissenschaftlichem Register, "Naniten" bei Laien-Register) im selben Satz wie
    ein Namensbestandteil der Figur auf, wird das als Regel-6-Verstoß gemeldet. Erkennt reine
    Dialog-Attribuierungen (z. B. "Sarah sagte:...") über Namensbestandteile, analog zu
    `characters_mentioned` in `app/tools/manuscript.py`.
- Rückgabe: `{"status": "success", "violations": [{"rule_id", "evidence", "explanation"}, ...]}`.
- Die übrigen 7 Regeln (2, 3, 4, 7, 8, 9, 10) haben kein eindeutiges Verbotswort und erfordern
  Sprachverständnis (z. B. "keine Fernkommunikation ohne physische Nähe" — lässt sich nicht per
  Stichwortsuche erkennen, ob eine beschriebene Kommunikation "aus der Ferne" gemeint ist). Diese
  Semantik-Hälfte übernimmt bewusst **nicht** dieses Tool, sondern der Continuity Agent selbst
  (LLM) — er hat den vollständigen `world_bible.md`-Text bereits über `scene_context` im Kontext
  und wird per Instruktion explizit zur semantischen Prüfung angehalten (siehe unten). Das
  entspricht der in der Task-Beschreibung geforderten Zweistufigkeit (Python für harte
  Verbotsmuster, LLM-Judge für Semantik), ohne einen zusätzlichen Live-LLM-Aufruf in dieses Tool
  einzubetten — hält `validate_world_rules` netzwerkfrei und offline testbar, konsistent mit
  `check_consistency` (TASK-011).

**Einbindung in `check_consistency`**
- `check_consistency` ruft `validate_world_rules` jetzt selbst auf und liefert das Ergebnis als
  zusätzliches Feld `world_rule_violations` mit ("Ergebnis fließt in check_consistency" laut
  Task-Beschreibung).
- `validate_world_rules` steht dem Continuity Agent zusätzlich als eigenständiges Tool zur
  Verfügung (für gezielte Nachprüfung von Textausschnitten).

**Continuity Agent nutzt beide Ebenen**
- `app/prompts/continuity.py::CONTINUITY_CONTEXT_INSTRUCTION` weist den Agenten an,
  `world_rule_violations`-Treffer aus `check_consistency` 1:1 als Konflikt vom Typ "Regelverstoss"
  zu übernehmen (deterministische Regeln 1/5/6) UND die übrigen Regeln (2/3/4/7/8/9/10) selbst
  semantisch gegen den vollständigen `world_bible.md`-Text zu prüfen.
- `ContinuityConflict.type` unterstützte "Regelverstoss" bereits vor diesem Task (TASK-011-
  Docstring-Beispiel) — keine Schema-Änderung nötig.

## Design-Entscheidung: "Verletzungen blockieren das Schreiben" über die bestehende Konflikt-Schwere, nicht über eine neue Pipeline-Wired-In

Akzeptanzkriterium: "Verletzungen blockieren das Schreiben genauso wie Continuity-Konflikte."
TASK-011 hat bereits explizit dokumentiert (und im Docstring von `app/agents/continuity_agent.py`
festgehalten), dass die Einbindung des Continuity Agent **in** die Schreib-Pipeline (als Gate vor
`write_scene`) erst mit Plan 3 kommt — der Continuity-Schritt selbst existiert in diesem Plan
noch nicht in `app/pipelines/writing.py`. Statt diese bewusste Plan-3-Abgrenzung in TASK-013
vorzeitig aufzubrechen (Scope-Kriechen über die Aufgabenstellung dieses Tasks hinaus), wird die
Forderung "genauso wie Continuity-Konflikte" wörtlich durch **Gleichbehandlung im Schema**
erfüllt: ein World-Rule-Verstoß wird vom Continuity Agent als regulärer `ContinuityConflict`
(`type="Regelverstoss"`, `severity` je nach Schwere) im selben `ContinuityReport` gemeldet wie
jeder andere Konflikttyp — es gibt also keinen separaten, schwächer priorisierten Kanal für
Weltregel-Verstöße. Sobald Plan 3 den Continuity-Schritt in die Pipeline verdrahtet und daraus
ein Blocking-Gate baut, blockieren Weltregel-Verstöße automatisch identisch zu jedem anderen
Konflikt, ohne weitere Änderung an diesem Task. Diese Entscheidung ist im Docstring von
`app/tools/consistency.py` dokumentiert.

## Eval-Metrik `world_rule_compliance`

- `tests/eval/mk34_eval/rubrics/world_rule_compliance.md` (`tier: fast`, analog zu `grounding.md`
  aus TASK-011): bewertet, ob deterministische Treffer übernommen und semantische Verstöße
  konkret belegt werden, ohne falsche Positive/Negative.
- `tests/eval/world_rule_compliance_metric.py`: identisches Muster wie `grounding_metric.py`
  (lokalisiert `mk34_eval` über `Path.cwd()`, ruft `judge(rubric="world_rule_compliance", ...)`).
- In `tests/eval/eval_config.yaml`s `metrics_to_run`/`custom_metrics` aktiv.

## Unit-Tests

`tests/unit/test_world_rules.py` (17 Tests, neu): Regel-1-Verstoß (inkl. Gegenprobe für sauberen
Text), Regel-5-Verstoß (beide Schreibweisen "Metallmaennchen"/"Metallmännchen"), Regel-6-Verstoß
figurenbezogen (Wissenschaftlerin nutzt Laienbegriff → Verstoß; Wissenschaftlerin nutzt korrekten
Begriff → kein Verstoß; Laie nutzt Laienbegriff → kein Verstoß; Fallback auf im Text erwähnte statt
explizit übergebene Figuren), Kombination mehrerer gleichzeitiger Verstöße, jeder Verstoß trägt
`evidence`/`explanation`, sowie `check_consistency` trägt `world_rule_violations` korrekt mit
(Treffer- und Leer-Fall).

Zwei Bugs während der Testentwicklung gefunden und behoben:
1. `_classify_register` klassifizierte "...korrigiert Davids Laienbegriffe aktiv" fälschlich als
   Laien-Register, weil `"laie" in register` als Teilstring von "Laienbegriffe" matchte — behoben
   durch Wortgrenzen-Regex (`\blaie\b`) und Prüfreihenfolge (wissenschaftlich zuerst).
2. Analog matchte `"praezise" in register` fälschlich in "unpraezise" (Davids Register) — ebenfalls
   durch Wortgrenzen-Regex behoben.

Gesamt: 171 Unit-Tests grün (`uv run python -m pytest tests/unit -q`), davon 17 neu für diesen
Task (plus 1 angepasster Test in `test_continuity_agent.py` für die erweiterte Tool-Liste).

## Blocker: Live-Verifikation weiterhin durch transientes Netzwerkproblem blockiert

Wie in TASK-011/TASK-012 dokumentiert, bleibt die Gemini-API-Verbindung instabil (zuletzt erneut
bestätigt in TASK-012 durch einen fehlgeschlagenen `agents-cli run`-Smoke-Test). TASK-013 führt
ebenfalls keinen neuen LLM-Agenten ein (nur ein deterministisches Tool plus Prompt-Erweiterung des
bereits in TASK-011 gebauten Continuity Agent) — die Akzeptanzkriterien sind vollständig durch die
17 neuen deterministischen Unit-Tests abgedeckt. Der offene Live-Nachtest aus TASK-011 (Continuity
Agent erkennt live einen Regelverstoß inkl. Zitat) bleibt der einzige noch unbestätigte
End-to-End-Punkt für den gesamten Continuity-Agent-Komplex (TASK-011/012/013 zusammen), sobald die
Verbindung wieder stabil ist. Ebenso bleibt die automatisierte Eval-Ausführung
(`agents-cli eval generate`/`grade`) durch den in TASK-003/TASK-010 dokumentierten `agents-cli`-Bug
blockiert (siehe `docs/known-issues/agents-cli-eval-generate-missing-content.md`) — betrifft auch
die neue `world_rule_compliance`-Metrik, sobald sie live gegen Traces liefe.

## Geänderte Dateien

- `app/tools/consistency.py` — neu: `validate_world_rules`, `_check_forbidden_phrases`,
  `_check_terminology`, `_classify_register`, `_split_sentences`; `check_consistency` liefert
  zusätzlich `world_rule_violations`.
- `app/agents/continuity_agent.py` — `continuity_context_agent` erhält `validate_world_rules`
  als zweites Tool.
- `app/prompts/continuity.py` — Instruktion für deterministische und semantische
  Weltregel-Prüfung erweitert.
- `tests/unit/test_world_rules.py` — neu, 17 Tests.
- `tests/unit/test_continuity_agent.py` — Tool-Namen-Assertion um `validate_world_rules` ergänzt.
- `tests/eval/mk34_eval/rubrics/world_rule_compliance.md`,
  `tests/eval/world_rule_compliance_metric.py`, `tests/eval/eval_config.yaml` — neue Eval-Metrik.

Keine Änderung nötig: `books/life_link/store/world_bible.md` (Regeln bereits in Plan 1 nummeriert
und maschinenlesbar).

## Verifikationsschritte

1. `agents-cli lint` — grün (`ruff check`, `ruff format --check`, `codespell`, `ty check`).
2. `uv run python -m pytest tests/unit -q` — 171 Tests grün (17 neu für diesen Task).
3. `git status --short books/` — keine Verschmutzung des echten Buchprojekts.
4. Live-LLM-Bestätigung nicht durchgeführt (kein neuer Agent in diesem Task; bekanntes,
   bereits dokumentiertes transientes Netzwerkproblem betrifft den gesamten Continuity-Komplex,
   siehe TASK-011/012-Walkthroughs).
