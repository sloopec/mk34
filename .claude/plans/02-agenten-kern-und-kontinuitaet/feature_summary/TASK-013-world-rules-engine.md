# Feature-Zusammenfassung: TASK-013 — World-Rules-Engine

## Was wurde umgesetzt

Die 10 nummerierten Naniten-Weltregeln aus `world_bible.md` wurden zu prüfbaren Constraints
gemacht. Ein neues Tool `validate_world_rules` prüft deterministisch drei Regeln mit eindeutigen
Signalwörtern: kein zentraler Server, keine mechanischen "Metallmännchen", und figurenbezogene
Terminologie-Konsistenz (Wissenschaftler:innen sagen "Naniten", Laien sagen "Nanobots" — die
falsche Wortwahl der jeweiligen Figur wird erkannt). Die übrigen sieben Regeln erfordern
Sprachverständnis und werden vom bereits bestehenden Continuity Agent (TASK-011) semantisch
gegen den vollständigen Weltregel-Text geprüft — das Tool liefert die harten Fälle, der Agent die
weichen.

Das Ergebnis fließt automatisch in `check_consistency` (TASK-011/012) ein, sodass der Continuity
Agent Weltregel-Verstöße als regulären Konflikttyp "Regelverstoss" im selben strukturierten
Bericht meldet wie Wissenslücken, Zeitsprünge oder Parallelitäts-Konflikte — sie werden also
identisch behandelt, sobald Plan 3 den Continuity-Schritt als Schreib-Gate verdrahtet.

Ergänzend wurde eine neue Eval-Metrik `world_rule_compliance` (LLM-Judge, Stufe "fast")
eingerichtet, die künftig bewertet, ob der Continuity Agent Weltregel-Treffer korrekt übernimmt
und semantische Verstöße konkret belegt.

## Geänderte Dateien

- `app/tools/consistency.py` — `validate_world_rules` und Integration in `check_consistency`.
- `app/agents/continuity_agent.py`, `app/prompts/continuity.py` — Continuity Agent nutzt das
  neue Tool und prüft die semantischen Regeln selbst.
- `tests/unit/test_world_rules.py` — 17 neue Unit-Tests (171 insgesamt grün).
- `tests/eval/mk34_eval/rubrics/world_rule_compliance.md`,
  `tests/eval/world_rule_compliance_metric.py`, `tests/eval/eval_config.yaml` — neue Eval-Metrik.

## Nächster Schritt

Mit TASK-013 ist Plan 2 ("Agenten-Kern und Kontinuität") vollständig umgesetzt. Offene Punkte,
die sich nicht aus dem Projekt-Code, sondern aus externen Faktoren ergeben, sind in den
jeweiligen Walkthroughs (TASK-003, TASK-010, TASK-011, TASK-012, TASK-013) dokumentiert: zwei
`agents-cli`-Bugs blockieren die automatisierte Eval-Ausführung, und ein transientes
Netzwerkproblem verhindert aktuell die Live-Bestätigung des Continuity-Agent-Komplexes. Beide
sind für Plan 3 relevant und werden in der übergreifenden `feature_summary.md` zusammengefasst.
Fachlich baut Plan 3 ("Szenen und lokales LLM") auf allen 13 Tasks dieses Plans auf: dem
Orchestrator/der Pipeline (TASK-007/008), dem Scene Agent, der den `_SceneSlotFixture`-Platzhalter
ersetzt, sowie der scharfen Schaltung des Continuity-Schritts und des deterministischen
Post-Write-Hooks (TASK-011/012/013).
