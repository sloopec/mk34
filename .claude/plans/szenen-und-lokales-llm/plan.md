# Plan 3: Szenen und lokales LLM

> Teil 3 von 4 des mk34-Book-Writing-Systems. Gesamtübersicht, Entscheidungen E1–E6 und Model-Routing-Matrix: [`../README.md`](../README.md).
> Stand: 2026-08-17 · hervorgegangen aus `mk34-book-writing-system/` (aufgelöst) · lokale Infrastruktur: `docs/LOCAL_MODEL_VM_SETUP.md`

Dieser Plan bündelt **alle Szenen-Anteile** des Systems: den Scene Agent, die Anbindung des lokalen LLM an den Router, den Szenen-Schritt der Schreib-Pipeline, die Content-Klassifikation mit lokalem Routing sowie die szenenspezifischen Evals. Er ist der Grund, warum es dieses Projekt gibt — hier entsteht der Text.

## Task-Mapping (alt → neu)

| Alt (Gesamtplan) | Neu | Anmerkung zur Trennung |
|---|---|---|
| TASK-002 Model-Router (nur der lokale-LLM-Anteil) | TASK-001 | Health-Check, `MK34_LOCAL_*`, Fallback-Verbot — herausgetrennt aus `fundament-und-kontext/TASK-002` |
| TASK-006 Scene Agent | TASK-002 | Start auf Gemini (E6), Ziel lokal |
| TASK-013 Schreib-Pipeline (nur der Szenen-Schritt) | TASK-003 | füllt den in `agenten-kern-und-kontinuitaet/TASK-008` dokumentierten Szenen-Slot |
| TASK-018 Content-Klassifikation und Routing | TASK-004 | unverändert in der Substanz; Classifier startet auf Gemini |
| TASK-008/TASK-014 (nur die Szenen-Eval-Anteile) | TASK-005 | `scene-writing.json`, `uncensored-routing.json`, deterministische Szenen-Metriken, `show_dont_tell` |

## Ziele

- Der Scene Agent schreibt kontextbasierte Szenen — **Start auf `gemini-3.1-pro-preview`** (E6), damit der Schreib-Workflow sofort testbar ist, ohne dass die VM läuft.
- Das lokale unzensierte Modell (`supergemma4-26b-abliterated` via llama.cpp, verschlüsselte Parallels-VM, SSH-Tunnel) ist als Provider `local` im Router angebunden — **nur für den Scene Agent vorgesehen**, wie von Anfang an entschieden.
- Content-Klassifikation routet Szenen automatisch lokal/Cloud; manueller Override; kein stiller Fallback.
- Szenenspezifische Eval-Suite: Beispielszenen A–E aus `basics.md`, Routing-Dataset, Szenen-Metriken.

## Nicht-Ziele

- Keine Qualitäts-Angleichung lokaler Outputs über den Pflicht-Editor-Lauf hinaus (Stil-Fingerprint, QS-Schwellen → Plan 4/TASK-001).
- Keine Varianten-/Rewrite-Workflows (→ Plan 4/TASK-002).
- Keine `safety`-Guardrails oder -Metriken auf dem Scene Agent — Kern-Use-Case-Entscheidung, gilt unverändert.

## Architekturübersicht

```
Orchestrator ── "Schreibe Kapitel N, Szene M" ──▶ writing_pipeline
  context_loader → plot_beat → character_brief
       → content_classifier (TASK-004)  → state["route"] = "local" | "cloud"
       → scene_agent (TASK-002)         → model_for("scene") liest state["route"]
       → continuity_check (AgentTool, aus Plan 2)
       → LoopAgent(editor, quality_checker)
       → write_scene(...) + Post-Write (Timeline/Character-State, aus Plan 2)

model_for("scene")  [TASK-001 erweitert den Router aus Plan 1]:
  route=="cloud" → MK34_MODEL_SCENE          (Start: gemini-3.1-pro-preview)
  route=="local" → LiteLlm("openai/supergemma4", api_base=MK34_LOCAL_API_BASE)
                   nach Preflight gegen MK34_LOCAL_HEALTH_URL
```

**Zwei bewusste Migrationsstufen für den Scene Agent:**
1. **Stufe A (TASK-002/003):** alles auf Gemini — der komplette Szenen-Workflow inkl. Pipeline, Continuity und Editor-Loop ist end-to-end lauffähig und eval-bar, ohne VM-Abhängigkeit.
2. **Stufe B (TASK-004):** das lokale Modell wird produktiv, der Classifier entscheidet die Route. Gemini bleibt die Cloud-Route für unkritische Szenen. Wichtig: Szenen, die auf `local` klassifiziert sind, werden bei nicht erreichbarer VM **nicht** still auf Gemini geschrieben — eine unzensierte Szene auf einem Cloud-Modell endet in einer Refusal oder in abgeschwächtem Text. Cloud-Refusals (bei Gemini: Safety-Block/`blocked`-Finish) sind ein Signal, die Klassifikationsregel nachzuschärfen.

## Komponenten-Verantwortlichkeiten

| Komponente | Task | Modell |
|---|---|---|
| Router-Erweiterung `local`-Provider, Health-Check | TASK-001 | — |
| `app/agents/scene_agent.py`, `app/prompts/scene.py` | TASK-002 | Start `gemini-3.1-pro-preview`; Ziel `openai/supergemma4` |
| Szenen-Schritt in `app/pipelines/writing.py` | TASK-003 | — |
| `app/agents/classifier_agent.py` | TASK-004 | `gemini-3.5-flash-lite`; später `anthropic/claude-haiku-4-5` |
| Szenen-Evals (`scene-writing.json`, `uncensored-routing.json`, Metriken) | TASK-005 | Judges gemäß E4/E6 |

## Ablaufsequenz

1. TASK-002 (Scene Agent auf Gemini) und TASK-001 (lokales LLM im Router) sind parallel bearbeitbar — TASK-002 braucht die VM nicht.
2. TASK-003: Szenen-Schritt in den Pipeline-Slot einsetzen; ab hier läuft „Schreibe Kapitel N, Szene M" end-to-end.
3. TASK-005 (Stufe A): Szenen-Evals auf der Gemini-Route grün.
4. TASK-004: Classifier + Routing; danach TASK-005 (Stufe B): `uncensored-routing.json` grün, Szenen-Metriken auch auf lokal generierten Outputs.

Fehlerpfade: VM nicht erreichbar → Abbruch mit Handlungsanweisung („VM starten"), Cloud-Fallback nur bei explizitem `MK34_ALLOW_CLOUD_FALLBACK=true` mit Warnung. Continuity-Konflikt oder World-Rule-Verletzung → Szene wird nicht geschrieben. Editor-Loop ohne Pass → `.draft.md` mit Verdikt.

## Konfiguration

| Variable | Wert | Task |
|---|---|---|
| `MK34_MODEL_SCENE` | Start `gemini-3.1-pro-preview`; ab TASK-004 ist `local` der Zielwert für geroutete Szenen | TASK-002/004 |
| `MK34_LOCAL_MODEL` | `openai/supergemma4` (LiteLLM, OpenAI-kompatibler Endpoint) | TASK-001 |
| `MK34_LOCAL_API_BASE` | `http://localhost:8080/v1` (llama-server über SSH-Tunnel) | TASK-001 |
| `MK34_LOCAL_API_KEY` | `not-needed` | TASK-001 |
| `MK34_LOCAL_HEALTH_URL` | `http://localhost:8080/health` | TASK-001 |
| `MK34_ALLOW_CLOUD_FALLBACK` | `false` (Default) | TASK-001/004 |

## Tooling

| Zweck | Kommando |
|---|---|
| Lokaler Run | `agents-cli run "Schreibe Kapitel 1, Szene 1" [-v]` · `agents-cli playground` |
| VM-Preflight (manuell) | `curl http://localhost:8080/health` (VM-Setup: `docs/LOCAL_MODEL_VM_SETUP.md`) |
| Lint / Tests | `agents-cli lint` · `uv run pytest` |
| Eval | `agents-cli eval run` · `agents-cli eval compare` (Regressionsgate gegen Plan-2-Baseline) |

## Evaluationsplan

| Dataset | Cases | Stufe |
|---|---|---|
| `scene-writing.json` | 5–8 Cases entlang der Beispielszenen aus `basics.md` (A Vanilla-Pitch, B kaltes Schlafzimmer, C Diagnose, D analoges Abendessen, E Protokoll der Sehnsucht) | A (Gemini), später B |
| `uncensored-routing.json` | Cases, die auf `local` geroutet werden müssen (mindestens Szene B und E) | B |

| Metrik | Art | Judge-Stufe (E4/E6) | Prüft |
|---|---|---|---|
| `show_dont_tell` | LLM-Judge | craft (`gemini-3.1-pro-preview`) | Emotion gezeigt statt benannt |
| `character_voice_consistency` | LLM-Judge | craft | jetzt auf echtem Szenentext |
| `scene_word_count_in_range` | deterministisch | — | Zielkorridor pro Szene (Korridore: Offene Frage Plan 1 #2) |
| `pov_character_present` | deterministisch | — | POV-Figur des Beats kommt vor |
| `terminology_leak` | deterministisch | — | David nie „Naniten"; Wissenschaftler nie „Nanobots" |

Gates:
- **Stufe A:** alle `scene-writing.json`-Cases mit `task_success` ≥ 4/5, `character_voice_consistency` ≥ 4/5, deterministische Metriken pass — auf der Gemini-Route.
- **Stufe B:** `uncensored-routing.json` 100 % korrekt geroutet; deterministische Szenen-Metriken bestehen auch auf lokal generierten Outputs (die craft-Schwelle **nach** Editor-Durchlauf ist Gegenstand von Plan 4/TASK-001).
- Keine Regression gegen die Plan-2-Baseline (`agents-cli eval compare`).
- `safety` wird weiterhin nicht eingesetzt.

## Entschieden

- **E9 (2026-08-17, vormals Offene Frage #2):** Die „Refusal als Routing-Signal"-Logik in TASK-004 deckt verbindlich **beide** Provider-Signalformen ab — Gemini: Safety-Block/`finish_reason` (u. a. `SAFETY`/`PROHIBITED_CONTENT`) und leere Kandidaten mit `prompt_feedback.block_reason`; Claude (später): `stop_reason: refusal`. Als Akzeptanzkriterium in TASK-004 verankert. (Gesamtliste E1–E10: [`../README.md`](../README.md).)

## Offene Fragen

1. **Kreativqualität von Gemini für Szenen (Stufe A):** Ob `gemini-3.1-pro-preview` den gewünschten literarischen Ton trifft, zeigt der erste `scene-writing.json`-Lauf. Falls nicht, ist die dokumentierte Alternative die Claude-Umschaltung (`MK34_MODEL_SCENE=anthropic/claude-opus-5`) — vor der VM-Inbetriebnahme.
2. **Hardware-Realität (übernommen):** 5–15 tok/s → 2–5 Min pro Szene lokal. Akzeptabel für den Einzellauf; für Varianten-Generierung siehe Plan 4.
