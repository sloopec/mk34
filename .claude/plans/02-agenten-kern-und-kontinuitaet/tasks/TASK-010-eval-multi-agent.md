# TASK-010: Eval für Multi-Agent-Trajektorie
Status: ⏳ ausstehend
Abhängig von: [TASK-009]
Parallel: nein
*(vormals TASK-014 im Gesamtplan — ohne die Szenen-Cases; die vier Beispielszenen-Cases A–D und `show_dont_tell` auf Szenentext liegen in `03-szenen-und-lokales-llm/TASK-005`)*

## Beschreibung
Plan-2-Gate. Die Eval-Suite wird von „liefert der Agent eine gute Antwort" auf „nimmt das System den richtigen Weg" erweitert.

**Neues Dataset** `tests/eval/datasets/multi-agent.json` — Multi-Turn-Cases ohne Szenengenerierung:
- Beat-Entwicklung: „Entwickle die Beats fuer Phase 3 (Die Flucht)" → Plot Agent + `update_plot_outline`
- Figuren-Brief: „Wie reagiert David in Beat X? Beruecksichtige seinen Wissensstand" → Character-`AgentTool`
- Lektorat: „Ueberarbeite diesen Text: <Fixture>" → Editor + Verdikt
- Kombination: Beat → Brief → Lektorat des Fixtures in einer Session (prueft State-Uebergaben)

**Neue Metriken in `eval_config.yaml`** — alle als lokale `custom_function`-Metriken ueber `mk34_eval.judge` (E1), Judge-Stufe gemaess E4, Judges auf Gemini gemaess E6:

| Metrik | Stufe | Prueft |
|---|---|---|
| `tool_use_quality` | `fast` | richtige Tools, richtige Argumente, keine ueberfluessigen Aufrufe (liest `instance["agent_data"]["turns"]`) |
| `trajectory_quality` | `fast` | logischer, effizienter Weg — wird Kontext geladen, *bevor* inhaltlich geantwortet wird? |
| `eli5_quality` | `fast` | Wissenschaft als Metapher im Dialog statt Lexikoneintrag |

`character_voice_consistency` (craft) laeuft weiter auf den Dialog-/Editor-Outputs. `show_dont_tell` kommt erst mit echtem Szenentext in Plan 3/TASK-005.

Rubrikbasierte Bewertung statt harter Sequenz-Matches — der Agent darf Hilfs-Tools in anderer Reihenfolge aufrufen. Rubriken mit `tier`-Frontmatter in `tests/eval/mk34_eval/rubrics/`.

```bash
agents-cli eval run
agents-cli eval compare artifacts/grade_results/<baseline>.json artifacts/grade_results/<neu>.json
```

`agents-cli eval analyze` steht ohne GCP nicht zur Verfuegung (E1). Ersatz: `.html`-Report + `explanation`-Felder der Judge-Funktionen.

Erwartung: 5–10+ Iterationen pro Case. Fixes gehen in Instructions und Tool-Descriptions, nicht in die Schwellenwerte.

## Akzeptanzkriterien
- [ ] `multi-agent.json` enthaelt mindestens 4 Multi-Turn-Cases (ohne Szenengenerierung)
- [ ] `tool_use_quality` ≥ 4/5 und `trajectory_quality` ≥ 4/5
- [ ] `character_voice_consistency` ≥ 4/5
- [ ] Der gesamte Lauf funktioniert weiterhin ohne GCP-Projekt
- [ ] Jede neue Rubrik traegt ein `tier`-Frontmatter
- [ ] Das Kostenprotokoll weist die Aufteilung fast/craft fuer den vollen Lauf aus
- [ ] `agents-cli eval compare` zeigt keine Regression gegenueber der TASK-003-Baseline
- [ ] Score-Tabelle dokumentiert; Task-Liste der gefixten/offenen Cases wird waehrend der Iteration gefuehrt

## Betroffene Dateien
- `tests/eval/datasets/multi-agent.json`
- `tests/eval/eval_config.yaml`
- `tests/eval/mk34_eval/rubrics/` (neue Rubriken)
- `tests/eval/mk34_eval/trace.py` (Trajektorie-/Tool-Auswertung)
- `app/prompts/*` (Fixes aus der Eval-Schleife)
