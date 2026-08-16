# TASK-008: Eval-Baseline (Dataset, Config, erster Lauf)
Status: ⏳ pending
Depends-on: [TASK-007]
Parallel: no

## Description
Der Qualitaets-Gate fuer Phase 1. Klein anfangen: 1–2 Cases, iterieren, erst dann erweitern.

**Entscheidung E1: Grading laeuft vollstaendig lokal.** Kein GCP-Projekt, kein `agents-cli login`. Konsequenz: die managed Built-in-Metriken (`final_response_quality`, `multi_turn_tool_use_quality`, `hallucination`, …) laufen server-seitig im Agent Platform Eval Service und stehen **nicht** zur Verfuegung. `metrics_to_run` enthaelt ausschliesslich `custom_metrics` mit `custom_function` (`execution: local`, Default) — dann grade't `agents-cli eval grade` in-process ohne Projekt und ohne Region. `agents-cli eval analyze` entfaellt ebenfalls (nur `global`-Endpoint).

**Dataset** `tests/eval/datasets/basic-dataset.json`:
```json
{"eval_cases": [
  {"eval_case_id": "scene_1_1",
   "prompt": {"role": "user", "parts": [{"text": "Schreibe Kapitel 1, Szene 1."}]}},
  {"eval_case_id": "character_lookup",
   "prompt": {"role": "user", "parts": [{"text": "Wer ist Dr. Elias Voss?"}]}}
]}
```

**Entscheidung E4: zweistufiger Judge, verbindlich ab diesem Task.** Nicht ein einheitliches Judge-Modell, sondern zwei Stufen — die Zuordnung liegt an der Rubrik, nicht am Aufrufort:
- **`fast` → `MK34_JUDGE_MODEL_FAST` = `claude-sonnet-5`** fuer deterministiknahe Rubriken (Regelabgleich gegen Trace oder niedergeschriebene Vorgaben): `task_success`, spaeter `tool_use_quality`, `trajectory_quality`, `grounding`, `world_rule_compliance`, `eli5_quality`.
- **`craft` → `MK34_JUDGE_MODEL_CRAFT` = `claude-opus-5`** ausschliesslich fuer `character_voice_consistency` und (ab TASK-014) `show_dont_tell` — die beiden Rubriken, bei denen der Judge wie ein Lektor urteilen muss.

**Judge-Bibliothek** `tests/eval/mk34_eval/` — wird in diesem Task angelegt und von allen spaeteren Metriken genutzt:
- `judge.py` — `judge(rubric, prompt, response, agent_data) -> {"score": 1-5, "explanation": str}`. Direkter Anthropic-SDK-Aufruf; **das Modell wird aus der Rubrik-Registrierung aufgeloest** (`tier: fast | craft`), nicht am Call-Site uebergeben. `output_config.format` mit JSON-Schema erzwingt die Score-Struktur; Retry; Kostenzaehler **getrennt nach Stufe**.
- `rubrics/*.md` — je Metrik eine versionierte, reviewbare Rubrik mit Frontmatter-Feld `tier`.
- `trace.py` — Zugriff auf `instance["agent_data"]["turns"]` fuer Tool-/Trajektorie-Metriken.

**Config** `tests/eval/eval_config.yaml` — nur `custom_metrics`:

| Metrik | Art | Stufe |
|---|---|---|
| `task_success` | LLM-Judge (Ersatz fuer `multi_turn_task_success`) | `fast` |
| `character_voice_consistency` | LLM-Judge, Rubrik 1–5 | `craft` |
| `no_placeholder_text` | deterministisch — kein `[TODO]`, `[Name`, `Lorem` | — |
| `terminology_leak` | deterministisch — David nie „Naniten", Wissenschaftler nie „Nanobots" | — |
| `scene_word_count_in_range` | deterministisch — Korridor aus Open Question #4 | — |

**`safety` bewusst NICHT** — widerspricht dem unzensierten Scene Agent; auch keine lokale Nachbildung.

```bash
agents-cli eval run                    # generate (lokal) + grade (in-process)
agents-cli eval compare artifacts/grade_results/<alt>.json artifacts/grade_results/<neu>.json
```

Ergebnisse liegen in `artifacts/grade_results/results_<ts>.{json,html}`. Bei Failures: Instruction/Tool-Descriptions fixen — **niemals** die Schwelle senken oder den Case loeschen.

Judge-Determinismus: der Judge-Aufruf laeuft mit fixer Rubrik und erzwungenem JSON-Schema; bei schwankenden Scores wird die Rubrik geschaerft, nicht die Schwelle gesenkt.

## Acceptance Criteria
- [ ] `tests/eval/datasets/basic-dataset.json` und `tests/eval/eval_config.yaml` sind eingecheckt
- [ ] **`agents-cli eval run` laeuft ohne gesetztes `GOOGLE_CLOUD_PROJECT` und ohne `agents-cli login` erfolgreich durch** — das ist der eigentliche Nachweis fuer E1
- [ ] `metrics_to_run` enthaelt ausschliesslich Eintraege aus `custom_metrics`; kein Built-in-Name
- [ ] `mk34_eval.judge` ist implementiert und liefert schema-validierte `{score, explanation}`
- [ ] **Das Judge-Modell wird aus dem `tier`-Feld der Rubrik aufgeloest, nicht am Call-Site uebergeben** — nachweisbar dadurch, dass `task_success` und `character_voice_consistency` denselben `judge(...)`-Aufruf verwenden und trotzdem auf unterschiedlichen Modellen laufen
- [ ] `character_voice_consistency` laeuft auf `MK34_JUDGE_MODEL_CRAFT`, `task_success` auf `MK34_JUDGE_MODEL_FAST` (im Kostenprotokoll verifizierbar)
- [ ] Judge-Kosten werden **getrennt nach Stufe** protokolliert
- [ ] Beide Cases erreichen `task_success` ≥ 4/5
- [ ] Alle deterministischen Metriken bestehen
- [ ] Die Score-Tabelle ist im PR/Commit dokumentiert (Nachweis statt Behauptung)
- [ ] `safety` steht nicht in `metrics_to_run`, mit Begruendungskommentar in der YAML

## Affected Files
- `tests/eval/datasets/basic-dataset.json`
- `tests/eval/eval_config.yaml`
- `tests/eval/mk34_eval/judge.py`, `tests/eval/mk34_eval/trace.py`
- `tests/eval/mk34_eval/rubrics/*.md` (je mit `tier: fast | craft`)
- `.env.example` (`MK34_JUDGE_MODEL_FAST`, `MK34_JUDGE_MODEL_CRAFT`)
