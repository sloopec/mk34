# Status: mk34 — AI Book Writing System
Updated: 2026-08-16T00:00:00Z

| Task ID  | Title                                              | Status         | Started    | Completed  |
|----------|----------------------------------------------------|----------------|------------|------------|
| TASK-001 | Projekt mit agents-cli scaffolden (Prototype)      | ⏳ pending      | —          | —          |
| TASK-002 | Model-Router (Claude via LiteLLM + lokales Modell) | ⏳ pending      | —          | —          |
| TASK-003 | Kontext-Store aus basics.md aufbauen               | ⏳ pending      | —          | —          |
| TASK-004 | Manuskript-Tools (read/write/list/stats)           | ⏳ pending      | —          | —          |
| TASK-005 | Kontext-Loader-Tools                               | ⏳ pending      | —          | —          |
| TASK-006 | Scene Agent (erster Agent)                         | ⏳ pending      | —          | —          |
| TASK-007 | Lokaler Smoke-Test und Lint                        | ⏳ pending      | —          | —          |
| TASK-008 | Eval-Baseline (Dataset, Config, erster Lauf)       | ⏳ pending      | —          | —          |
| TASK-009 | Plot Agent                                         | ⏳ pending      | —          | —          |
| TASK-010 | Character Agent und Figuren-Tools                  | ⏳ pending      | —          | —          |
| TASK-011 | Editor Agent (Lektorat)                            | ⏳ pending      | —          | —          |
| TASK-012 | Orchestrator als Coordinator-Root-Agent            | ⏳ pending      | —          | —          |
| TASK-013 | Schreib-Pipeline (SequentialAgent + LoopAgent)     | ⏳ pending      | —          | —          |
| TASK-014 | Eval fuer Multi-Agent-Trajektorie                  | ⏳ pending      | —          | —          |
| TASK-015 | Continuity Agent mit Retrieval                     | ⏳ pending      | —          | —          |
| TASK-016 | Timeline- und Character-State-Tracking             | ⏳ pending      | —          | —          |
| TASK-017 | World-Rules-Engine                                 | ⏳ pending      | —          | —          |
| TASK-018 | Content-Klassifikation und lokales Routing         | ⏳ pending      | —          | —          |
| TASK-019 | Qualitaetssicherung fuer lokale Outputs            | ⏳ pending      | —          | —          |
| TASK-020 | Workflow und Iteration (Feedback, Varianten, CLI)  | ⏳ pending      | —          | —          |
| TASK-021 | Export und finaler Polish                          | ⏳ pending      | —          | —          |
| TASK-022 | Observability und Logging (optional)               | ⏳ pending      | —          | —          |

Status values: `⏳ pending` → `🔄 in-progress` → `✅ done` or `❌ aborted`

## Phasen-Zuordnung

- **Phase 1 (Foundation):** TASK-001 … TASK-008
- **Phase 2 (Multi-Agent Core):** TASK-009 … TASK-014
- **Phase 3 (Konsistenz & Continuity):** TASK-015 … TASK-017
- **Phase 4 (Lokale & unzensierte Modelle):** TASK-018, TASK-019
- **Phase 5 (Workflow & Iteration):** TASK-020
- **Phase 6 (Export & Polish):** TASK-021
- **Querschnitt:** TASK-022

## Blocker

Keine. Die drei blockierenden Fragen sind entschieden (siehe `plan.md` → *Entschieden*):

- **E1 — Eval-Grading lokal** (kein GCP; nur `custom_function`-Metriken mit eigenem Claude-Judge) → entblockt **TASK-008**
- **E2 — Retrieval lokal** (SQLite FTS5/BM25, optional sqlite-vec-Hybrid) → entblockt **TASK-015**
- **E3 — persistente Sessions ab Phase 1** (`DatabaseSessionService` auf SQLite) → betrifft **TASK-001**, **TASK-013**, **TASK-020**
- **E4 — zweistufiger Eval-Judge** (`claude-sonnet-5` fuer deterministiknahe Rubriken, `claude-opus-5` nur fuer `character_voice_consistency` und `show_dont_tell`) → betrifft **TASK-008**, **TASK-014**, **TASK-022**

Verbleibende offene Fragen sind nicht blockierend; die naechstwichtigste ist Open Question #2 (Ablage von `books/life_link/`), da sie alle Tool-Pfade in TASK-004/005 betrifft.
