# Status: mk34 — AI Book Writing System
Aktualisiert: 2026-08-16T00:00:00Z

| Task-ID  | Titel                                              | Status           | Gestartet  | Abgeschlossen |
|----------|----------------------------------------------------|------------------|------------|---------------|
| TASK-001 | Projekt mit agents-cli scaffolden (Prototype)      | ✅ erledigt         | 2026-08-16T00:00:00Z | 2026-08-16T00:00:00Z |
| TASK-002 | Model-Router (Claude via LiteLLM + lokales Modell) | ⏳ ausstehend      | —          | —          |
| TASK-003 | Kontext-Store aus basics.md aufbauen               | ⏳ ausstehend      | —          | —          |
| TASK-004 | Manuskript-Tools (read/write/list/stats)           | ⏳ ausstehend      | —          | —          |
| TASK-005 | Kontext-Loader-Tools                               | ⏳ ausstehend      | —          | —          |
| TASK-006 | Scene Agent (erster Agent)                         | ⏳ ausstehend      | —          | —          |
| TASK-007 | Lokaler Smoke-Test und Lint                        | ⏳ ausstehend      | —          | —          |
| TASK-008 | Eval-Baseline (Dataset, Config, erster Lauf)       | ⏳ ausstehend      | —          | —          |
| TASK-009 | Plot Agent                                         | ⏳ ausstehend      | —          | —          |
| TASK-010 | Character Agent und Figuren-Tools                  | ⏳ ausstehend      | —          | —          |
| TASK-011 | Editor Agent (Lektorat)                            | ⏳ ausstehend      | —          | —          |
| TASK-012 | Orchestrator als Coordinator-Root-Agent            | ⏳ ausstehend      | —          | —          |
| TASK-013 | Schreib-Pipeline (SequentialAgent + LoopAgent)     | ⏳ ausstehend      | —          | —          |
| TASK-014 | Eval fuer Multi-Agent-Trajektorie                  | ⏳ ausstehend      | —          | —          |
| TASK-015 | Continuity Agent mit Retrieval                     | ⏳ ausstehend      | —          | —          |
| TASK-016 | Timeline- und Character-State-Tracking             | ⏳ ausstehend      | —          | —          |
| TASK-017 | World-Rules-Engine                                 | ⏳ ausstehend      | —          | —          |
| TASK-018 | Content-Klassifikation und lokales Routing         | ⏳ ausstehend      | —          | —          |
| TASK-019 | Qualitaetssicherung fuer lokale Outputs            | ⏳ ausstehend      | —          | —          |
| TASK-020 | Workflow und Iteration (Feedback, Varianten, CLI)  | ⏳ ausstehend      | —          | —          |
| TASK-021 | Export und finaler Polish                          | ⏳ ausstehend      | —          | —          |
| TASK-022 | Observability und Logging (optional)               | ⏳ ausstehend      | —          | —          |

Statuswerte: `⏳ ausstehend` → `🔄 in Bearbeitung` → `✅ erledigt` oder `❌ abgebrochen`

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
- **E5 — Buch-Datenverzeichnis** (`books/life_link/` bleibt im Repo-Root, ausserhalb von `mk34-book-agent/`) → entschieden in **TASK-001**, betrifft alle Tool-Pfade in **TASK-004/005**

Verbleibende offene Fragen (siehe `plan.md` → *Offene Fragen* #1–#4) sind nicht blockierend.
