# Plan 2: Agenten-Kern und Kontinuität

> Teil 2 von 4 des mk34-Book-Writing-Systems. Gesamtübersicht, Entscheidungen E1–E6 und Model-Routing-Matrix: [`../README.md`](../README.md).
> Stand: 2026-08-17 · hervorgegangen aus `mk34-book-writing-system/` (aufgelöst)

Dieser Plan baut das Multi-Agenten-System **ohne die Szenen-Anteile**: Tools, Eval-Grundgerüst, die Autoren-Agenten (Plot, Character, Editor), den Orchestrator, das Pipeline-Gerüst sowie Continuity/Timeline/World-Rules. Alles, was Szenentext erzeugt oder das lokale LLM berührt, liegt in Plan 3 (`03-szenen-und-lokales-llm/`).

## Task-Mapping (alt → neu)

| Alt (Gesamtplan) | Neu | Anmerkung zur Trennung |
|---|---|---|
| TASK-004 Manuskript-Tools | TASK-001 | unverändert — die Tools sind szenen-agnostisch (lesen/schreiben Dateien) |
| TASK-005 Kontext-Loader-Tools | TASK-002 | unverändert |
| TASK-008 Eval-Baseline | TASK-003 | **geteilt:** Judge-Bibliothek, `basic-dataset.json` (ohne Szenen-Case), `task_success`/`character_voice_consistency`/`no_placeholder_text` hier; szenenspezifische Metriken und Datasets → Plan 3/TASK-005 |
| TASK-009 Plot Agent | TASK-004 | unverändert |
| TASK-010 Character Agent | TASK-005 | unverändert |
| TASK-011 Editor Agent | TASK-006 | unverändert (der Bezug „läuft auch über lokal generierte Szenen" wirkt erst ab Plan 3/4) |
| TASK-012 Orchestrator | TASK-007 | Sub-Agent-Liste ohne Scene Agent; der wird in Plan 3/TASK-003 nachregistriert |
| TASK-013 Schreib-Pipeline | TASK-008 | **geteilt:** Pipeline-Gerüst (Kontext → Beat → Brief → Editor-Loop) hier; der Szenen-Schritt (`create_scene_agent()`-Slot, `write_scene`-Persistenz, Draft-Pfad) → Plan 3/TASK-003 |
| TASK-007 Smoke-Test und Lint | TASK-009 | ohne Szenen-Prompts; Prompt-Set auf Plot/Character/Editor umgestellt |
| TASK-014 Eval Multi-Agent | TASK-010 | **geteilt:** Trajektorie-/Tool-Metriken und Nicht-Szenen-Cases hier; die vier Beispielszenen-Cases (A–D) und `show_dont_tell` auf Szenentext → Plan 3/TASK-005 |
| TASK-015 Continuity Agent | TASK-011 | unverändert |
| TASK-016 Timeline/Character-State | TASK-012 | unverändert |
| TASK-017 World-Rules-Engine | TASK-013 | unverändert |

## Ziele

- Alle Nicht-Szenen-Agenten laufen auf Gemini (E6) über `model_for(...)` aus Plan 1.
- Lokale Eval-Infrastruktur (E1/E4) steht: Judge-Bibliothek `mk34_eval`, Rubriken mit `tier`-Frontmatter, deterministische Metriken.
- Orchestrator-Coordinator + `SequentialAgent`-Pipeline-Gerüst mit Editor-`LoopAgent`; der Szenen-Schritt ist ein definierter, in Plan 3 zu füllender Slot.
- Continuity-System (lokales FTS5-Retrieval, E2), Timeline- und Character-State-Tracking, World-Rules-Engine.

## Nicht-Ziele

- Kein Szenentext-Schreiben, kein Scene Agent, kein lokales LLM, keine Content-Klassifikation (→ Plan 3).
- Keine eigene `mk34`-CLI, kein Export (→ Plan 4).
- Kein GCP (E1), kein Deployment.

## Architekturübersicht

Wie im Gesamtsystem ([`../README.md`](../README.md)), reduziert um den Scene-Zweig:

```
root_agent "orchestrator" (gemini-3.7-flash)
 ├─ sub_agents: plot_agent · editor_agent · writing_pipeline(Gerüst)
 ├─ AgentTool: character_agent · continuity_agent
 └─ writing_pipeline = SequentialAgent[
      context_loader → plot_beat → character_brief → [SZENEN-SLOT, Plan 3] → LoopAgent(editor, quality_checker)
    ]
```

Der Szenen-Slot ist im Gerüst als bewusste Lücke ausgeführt: die Pipeline endet in diesem Plan damit, dass der Editor-Loop über einen **vorgegebenen** Text läuft — gemäß E8 die Szene E „Protokoll der Sehnsucht" aus `basics.md` als eingechecktes Fixture — so sind Loop, State-Fluss und Abbruchpfade testbar, bevor es einen Scene Agent gibt.

Orchestrierung, State-Konventionen (`output_key` → `{state_key}`), Fehlerpfade (Continuity-Konflikt blockiert das Schreiben, Editor-Loop legt `.draft.md` ab) und das Retrieval-Design (SQLite FTS5/BM25, Stufe-2-Kriterium) sind unverändert aus dem Gesamtplan übernommen — Details in den Task-Dateien.

## Komponenten-Verantwortlichkeiten

| Komponente | Task | Modell (Start, E6) |
|---|---|---|
| `app/tools/manuscript.py` | TASK-001 | — |
| `app/tools/context_loader.py`, `app/callbacks.py` | TASK-002 | — |
| `tests/eval/mk34_eval/` (Judge, Rubriken, Trace) | TASK-003 | Judges: `gemini-3.7-flash` / `gemini-3.1-pro-preview` |
| `app/agents/plot_agent.py` (+ `SceneBeat`-Schema) | TASK-004 | `gemini-3.1-pro-preview` |
| `app/agents/character_agent.py`, `app/tools/characters.py` | TASK-005 | `gemini-3.1-pro-preview` |
| `app/agents/editor_agent.py`, `quality_checker.py` | TASK-006 | `gemini-3.1-pro-preview` |
| `app/agent.py` (Orchestrator) | TASK-007 | `gemini-3.7-flash` |
| `app/pipelines/writing.py` (Gerüst) | TASK-008 | — |
| `app/agents/continuity_agent.py`, `app/retrieval/` | TASK-011 | `gemini-3.7-flash` |
| `app/tools/timeline.py`, Character-State | TASK-012 | — |
| World-Rules (`validate_world_rules`) | TASK-013 | semantischer Check: `gemini-3.7-flash` |

## Ablaufsequenz

1. TASK-001/002 (parallel): Tools gegen den Store aus Plan 1/TASK-003.
2. TASK-003: Eval-Grundgerüst — ab hier hat jeder weitere Task ein messbares Gate.
3. TASK-004/005/006 (parallel): die drei Autoren-Agenten.
4. TASK-007 → TASK-008: Orchestrator, dann Pipeline-Gerüst.
5. TASK-009: Smoke-Test/Lint über das Gesamtgebilde.
6. TASK-010: Multi-Agent-Eval (Trajektorie).
7. TASK-011 → TASK-012/013: Continuity-Block.

## Konfiguration

Keine neuen Variablen gegenüber Plan 1; genutzt werden `MK34_MODEL_*`, `MK34_JUDGE_MODEL_*` (Gemini-Startwerte, siehe Plan 1 → Konfiguration), `MK34_BOOK_ROOT`, `MK34_INDEX_PATH`, `MK34_SESSION_DB_URL`.

## Tooling

| Zweck | Kommando |
|---|---|
| Lokaler Run | `agents-cli playground` · `agents-cli run "..." [-v]` |
| Lint | `agents-cli lint` |
| Eval | `agents-cli eval run` (vollständig lokal, E1) · `agents-cli eval compare <alt>.json <neu>.json` |
| Unit-Tests | `uv run pytest` |
| Recipe-Studium | `rag-vector-search` (nur Chunking-/Query-Muster) vor TASK-011 klonen |

## Evaluationsplan

Datasets und Metriken dieses Plans (Judge-Stufen gemäss E4, Judges auf Gemini gemäss E6):

| Dataset | Task | Cases |
|---|---|---|
| `basic-dataset.json` | TASK-003 | `character_lookup` („Wer ist Dr. Elias Voss?"), `plot_question` („Fasse Phase 2 zusammen") — **ohne** Szenen-Case |
| `multi-agent.json` | TASK-010 | Multi-Turn: Beat entwickeln → Figuren-Brief → Editor überarbeitet vorgelegten Text; prüft Trajektorie und Tool-Nutzung |
| `continuity.json` | TASK-011 | absichtlich eingebaute Widersprüche (Wissen zu früh, Zeitsprung, regelwidrige Naniten) |

| Metrik | Art | Stufe | Ab Task |
|---|---|---|---|
| `task_success` | LLM-Judge | fast | TASK-003 |
| `character_voice_consistency` | LLM-Judge | craft | TASK-003 (auf Dialogvorschlägen/Editor-Output) |
| `no_placeholder_text` | deterministisch | — | TASK-003 |
| `tool_use_quality` | LLM-Judge | fast | TASK-010 |
| `trajectory_quality` | LLM-Judge | fast | TASK-010 |
| `eli5_quality` | LLM-Judge | fast | TASK-010 |
| `grounding` | LLM-Judge | fast | TASK-011 |
| `world_rule_compliance` | LLM-Judge | fast | TASK-013 |

Szenenspezifische Metriken (`scene_word_count_in_range`, `pov_character_present`, `terminology_leak` auf Szenentext, `show_dont_tell`) und die Datasets `scene-writing.json`/`uncensored-routing.json` liegen in **Plan 3/TASK-005**.

Gates: TASK-003 `task_success` ≥ 4/5; TASK-010 `tool_use_quality` und `trajectory_quality` ≥ 4/5; TASK-011 0 False Negatives auf `continuity.json`, `grounding` ≥ 4/5. Schwellen werden nie gesenkt; `safety` wird nicht eingesetzt (Begründung im README/E-Katalog — unzensierter Scene-Use-Case in Plan 3).

## Entschieden

- **E8 (2026-08-17, vormals Offene Frage #1):** Szene E „Protokoll der Sehnsucht" aus `books/life_link/idea/basics.md` ist das Fixture für den Editor-Loop im Pipeline-Gerüst (TASK-008). Details und Begründung in der Task-Datei. (Gesamtliste E1–E10: [`../README.md`](../README.md).)

## Offene Fragen

1. **Judge-Qualität auf Gemini (Folge aus E6):** Ob `gemini-3.1-pro-preview` als craft-Judge das Lektorats-Urteil trägt, zeigt sich ab TASK-003. Bei systematisch unplausiblen `character_voice_consistency`-Scores ist die dokumentierte Alternative die Claude-Umschaltung der Judge-Variablen.
