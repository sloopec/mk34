# TASK-017: World-Rules-Engine
Status: ⏳ pending
Depends-on: [TASK-015]
Parallel: yes

## Description
Die Naniten-Regeln aus `world_bible.md` werden zu harten, pruefbaren Constraints — nicht nur zu Prompt-Prosa.

Regelbasis aus `basics.md`:
1. Waechter-Naniten sind passiv und haben keine eigene Intelligenz, sie fuehren nur Reparatur-Skripte aus.
2. Es gibt **keinen zentralen Server** — Kommunikation erfolgt koerperintern und bei physischer Naehe von Koerper zu Koerper.
3. Reproduktion braucht biologisches Rohmaterial und Energie; intensivster Austausch beim Sex.
4. Gesteigertes Verlangen ist Verbreitungsstrategie, keine Nebenwirkung.
5. Naniten sind molekulare Maschinen / kuenstliche Enzyme — **keine** mechanischen Roboter mit Zangen.
6. Die Naniten veraendern die DNA der Keimbahn (ab Phase 4).
7. Terminologie: Bevoelkerung/Medien „Nanobots", Wissenschaftler „Naniten".

Tool `validate_world_rules(text: str) -> dict` prueft einen Szenentext gegen diese Liste und liefert `{"violations": [{"rule_id", "evidence", "explanation"}]}`.

Zweistufig: deterministische Checks (Terminologie, verbotene Begriffe) in Python; semantische Checks (verhaelt sich die Technologie logisch konsistent?) per LLM-Judge auf `claude-sonnet-5`.

Ergebnis fliesst in `check_consistency` und in die Eval-Metrik `world_rule_compliance`.

## Acceptance Criteria
- [ ] Alle 7 Regeln sind in `world_bible.md` nummeriert und maschinenlesbar referenzierbar
- [ ] `validate_world_rules` erkennt Testverletzungen (z. B. „die Naniten meldeten sich beim Server", „winzige Metallmaennchen")
- [ ] Terminologie-Check ist deterministisch und figurenbezogen
- [ ] Verletzungen blockieren das Schreiben genauso wie Continuity-Konflikte
- [ ] Eval-Metrik `world_rule_compliance` ist in `eval_config.yaml` aktiv

## Affected Files
- `books/life_link/store/world_bible.md`
- `app/tools/consistency.py`
- `tests/eval/metrics/world_rule_compliance.py`
- `tests/unit/test_world_rules.py`
