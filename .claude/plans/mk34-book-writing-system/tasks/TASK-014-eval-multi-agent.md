# TASK-014: Eval fuer Multi-Agent-Trajektorie
Status: ⏳ ausstehend
Abhängig von: [TASK-013]
Parallel: nein

## Beschreibung
Phase-2-Gate. Die Eval-Suite wird von „liefert der Agent eine gute Antwort" auf „nimmt das System den richtigen Weg" erweitert.

**Neues Dataset** `tests/eval/datasets/multi-agent.json` — Multi-Turn-Cases entlang der Beispielszenen aus `basics.md`:
- Szene A „Vanilla-Pitch" (Voss & Ronan, AR-Demo, Halo-Effekt)
- Szene B „Das kalte Schlafzimmer" (David & Elena, Horror-Moment)
- Szene C „Die Diagnose" (Dr. Aris, „Dein Blut hat jetzt W-LAN")
- Szene D „Das analoge Abendessen" (Sarah & David, angebrannter Eintopf)

**Neue Metriken in `eval_config.yaml`** — alle als lokale `custom_function`-Metriken ueber `mk34_eval.judge` (E1, kein GCP), Judge-Stufe pro Rubrik gemaess E4:

| Metrik | Stufe | Prueft |
|---|---|---|
| `tool_use_quality` | `fast` | richtige Tools, richtige Argumente, keine ueberfluessigen Aufrufe (liest `instance["agent_data"]["turns"]`) |
| `trajectory_quality` | `fast` | schreibt der Scene Agent, *bevor* Kontext geladen ist? |
| `eli5_quality` | `fast` | Wissenschaft als Metapher im Dialog statt Lexikoneintrag |
| `character_voice_consistency` | `craft` | jetzt scharf geschaltet |
| `show_dont_tell` | `craft` | Emotion gezeigt statt benannt |

Rubrikbasierte Bewertung statt harter Sequenz-Matches — der Agent darf Hilfs-Tools in anderer Reihenfolge aufrufen. Die Rubriken liegen als versionierte Markdown-Dateien in `tests/eval/mk34_eval/rubrics/`, jeweils mit `tier`-Frontmatter.

Von den fuenf neuen Rubriken laufen drei auf `claude-sonnet-5` — die Suite waechst hier deutlich, und der Kostenunterschied schlaegt ab dieser Phase erstmals real durch.

```bash
agents-cli eval run
agents-cli eval compare artifacts/grade_results/<phase1>.json artifacts/grade_results/<neu>.json
```

`agents-cli eval analyze` steht ohne GCP nicht zur Verfuegung. Ersatz fuer die Fehleranalyse: der `.html`-Report in `artifacts/grade_results/` plus die `explanation`-Felder der eigenen Judge-Funktionen — die sind ohnehin praeziser, weil die Rubrik projektspezifisch ist.

Erwartung: 5–10+ Iterationen pro Case. Fixes gehen in Instructions und Tool-Descriptions, nicht in die Schwellenwerte.

## Akzeptanzkriterien
- [ ] `multi-agent.json` enthaelt mindestens 4 Multi-Turn-Cases
- [ ] `tool_use_quality` ≥ 4/5 und `trajectory_quality` ≥ 4/5
- [ ] `character_voice_consistency` ≥ 4/5
- [ ] Der gesamte Lauf funktioniert weiterhin ohne GCP-Projekt
- [ ] Jede neue Rubrik traegt ein `tier`-Frontmatter; `show_dont_tell` und `character_voice_consistency` laufen auf `craft`, die uebrigen drei auf `fast`
- [ ] Das Kostenprotokoll weist die Aufteilung fast/craft fuer den vollen Lauf aus
- [ ] `agents-cli eval compare` zeigt keine Regression gegenueber der Phase-1-Baseline
- [ ] Score-Tabelle dokumentiert
- [ ] Eine Task-Liste der gefixten/offenen Cases wird waehrend der Iteration gefuehrt

## Betroffene Dateien
- `tests/eval/datasets/multi-agent.json`
- `tests/eval/eval_config.yaml`
- `tests/eval/mk34_eval/rubrics/` (neue Rubriken)
- `tests/eval/mk34_eval/trace.py` (Trajektorie-/Tool-Auswertung)
- `app/prompts/*` (Fixes aus der Eval-Schleife)
