# TASK-003: Eval-Grundgerüst und Judge-Bibliothek
Status: ⏳ ausstehend
Abhängig von: [TASK-001, TASK-002]
Parallel: nein
*(vormals TASK-008 im Gesamtplan — hier ohne die Szenen-Anteile; die liegen in `03-szenen-und-lokales-llm/TASK-005`)*

## Beschreibung
Die lokale Eval-Infrastruktur, die alle vier Plaene nutzen. Klein anfangen: 1–2 Cases, iterieren, erst dann erweitern.

**Entscheidung E1: Grading laeuft vollstaendig lokal.** Kein GCP-Projekt, kein `agents-cli login`. Die managed Built-in-Metriken stehen ohne GCP **nicht** zur Verfuegung; `metrics_to_run` enthaelt ausschliesslich `custom_metrics` mit `custom_function` (`execution: local`, Default). `agents-cli eval analyze` entfaellt ebenfalls.

**Entscheidung E4 + E6: zweistufiger Judge, Start auf Gemini.** Die Zuordnung liegt an der Rubrik (`tier`-Frontmatter), nicht am Call-Site:
- **`fast` → `MK34_JUDGE_MODEL_FAST` = `gemini-3.7-flash`** — deterministiknahe Rubriken (Regelabgleich gegen Trace oder niedergeschriebene Vorgaben).
- **`craft` → `MK34_JUDGE_MODEL_CRAFT` = `gemini-3.1-pro-preview`** — nur `character_voice_consistency` und (spaeter) `show_dont_tell`.
- Claude-Judges (`claude-sonnet-5`/`claude-opus-5`) bleiben als dokumentierte Alternative — Umschaltung ist eine `.env`-Zeile.

**Judge-Bibliothek** `tests/eval/mk34_eval/` — **provider-agnostisch**:
- `judge.py` — `judge(rubric, prompt, response, agent_data) -> {"score": 1-5, "explanation": str}`. Das Modell wird aus dem `tier`-Feld der Rubrik aufgeloest; der Provider aus dem Modell-String (`gemini-*` → `google-genai`-SDK mit `GEMINI_API_KEY`; `claude-*` → `anthropic`-SDK). Structured Output erzwingt das Score-Schema (Gemini: `response_schema`; Claude: `output_config.format`). Retry; Kostenzaehler getrennt nach Stufe.
- `rubrics/*.md` — je Metrik eine versionierte, reviewbare Rubrik mit Frontmatter-Feld `tier: fast | craft`.
- `trace.py` — Zugriff auf `instance["agent_data"]["turns"]` fuer Tool-/Trajektorie-Metriken.

**Dataset** `tests/eval/datasets/basic-dataset.json` — ohne Szenen-Case (der liegt in Plan 3):
```json
{"eval_cases": [
  {"eval_case_id": "character_lookup",
   "prompt": {"role": "user", "parts": [{"text": "Wer ist Dr. Elias Voss?"}]}},
  {"eval_case_id": "plot_question",
   "prompt": {"role": "user", "parts": [{"text": "Fasse Phase 2 des Plots zusammen."}]}}
]}
```

**Config** `tests/eval/eval_config.yaml` — nur `custom_metrics`:

| Metrik | Art | Stufe |
|---|---|---|
| `task_success` | LLM-Judge (Ersatz fuer `multi_turn_task_success`) | `fast` |
| `character_voice_consistency` | LLM-Judge, Rubrik 1–5 (hier auf Dialogvorschlaegen/Antworten) | `craft` |
| `no_placeholder_text` | deterministisch — kein `[TODO]`, `[Name`, `Lorem` | — |

**`safety` bewusst NICHT** — widerspricht dem unzensierten Szenen-Use-Case (Plan 3); auch keine lokale Nachbildung. Begruendungskommentar in der YAML.

```bash
agents-cli eval run                    # generate (lokal) + grade (in-process)
agents-cli eval compare artifacts/grade_results/<alt>.json artifacts/grade_results/<neu>.json
```

Bei Failures: Instruction/Tool-Descriptions fixen — **niemals** die Schwelle senken oder den Case loeschen. Bei schwankenden Judge-Scores wird die Rubrik geschaerft.

## Akzeptanzkriterien
- [ ] `basic-dataset.json` und `eval_config.yaml` sind eingecheckt
- [ ] **`agents-cli eval run` laeuft ohne `GOOGLE_CLOUD_PROJECT` und ohne `agents-cli login` durch** — Nachweis fuer E1; Gemini-Judges laufen ueber `GEMINI_API_KEY`
- [ ] `metrics_to_run` enthaelt ausschliesslich Eintraege aus `custom_metrics`; kein Built-in-Name
- [ ] `mk34_eval.judge` liefert schema-validierte `{score, explanation}` — auf Gemini **und** (per Unit-Test mit gestubbtem Client) auf Claude, ohne Codeaenderung am Call-Site
- [ ] Judge-Modell wird aus dem `tier`-Feld aufgeloest: `task_success` laeuft auf `MK34_JUDGE_MODEL_FAST`, `character_voice_consistency` auf `MK34_JUDGE_MODEL_CRAFT` (im Kostenprotokoll verifizierbar)
- [ ] Judge-Kosten werden getrennt nach Stufe protokolliert
- [ ] Beide Cases erreichen `task_success` ≥ 4/5; Score-Tabelle im PR/Commit dokumentiert
- [ ] `safety` steht nicht in `metrics_to_run`, mit Begruendungskommentar

## Betroffene Dateien
- `tests/eval/datasets/basic-dataset.json`
- `tests/eval/eval_config.yaml`
- `tests/eval/mk34_eval/judge.py`, `tests/eval/mk34_eval/trace.py`
- `tests/eval/mk34_eval/rubrics/*.md` (je mit `tier: fast | craft`)
- `tests/unit/test_judge.py`
