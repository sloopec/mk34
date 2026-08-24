# Status: Agenten-Kern und Kontinuität (Plan 2)
Aktualisiert: 2026-08-17T00:00:00Z

| Task-ID  | Titel                                                  | Status         | Gestartet | Abgeschlossen |
|----------|--------------------------------------------------------|----------------|-----------|---------------|
| TASK-001 | Manuskript-Tools (read/write/list/stats)               | ✅ erledigt     | 2026-08-19T00:00:00Z | 2026-08-19T01:00:00Z |
| TASK-002 | Kontext-Loader-Tools                                   | ✅ erledigt     | 2026-08-19T01:15:00Z | 2026-08-19T01:45:00Z |
| TASK-003 | Eval-Grundgerüst und Judge-Bibliothek                  | ✅ erledigt (`eval grade`-Score blockiert durch agents-cli-Bug, siehe Walkthrough) | 2026-08-19T02:00:00Z | 2026-08-24T12:15:00Z |
| TASK-004 | Plot Agent                                             | ✅ erledigt     | 2026-08-24T12:30:00Z | 2026-08-24T13:00:00Z |
| TASK-005 | Character Agent und Figuren-Tools                      | ⏳ ausstehend   | —         | —             |
| TASK-006 | Editor Agent (Lektorat)                                | ⏳ ausstehend   | —         | —             |
| TASK-007 | Orchestrator als Coordinator-Root-Agent                | ⏳ ausstehend   | —         | —             |
| TASK-008 | Schreib-Pipeline-Gerüst (ohne Szenen-Schritt)          | ⏳ ausstehend   | —         | —             |
| TASK-009 | Smoke-Test und Lint                                    | ⏳ ausstehend   | —         | —             |
| TASK-010 | Eval für Multi-Agent-Trajektorie                       | ⏳ ausstehend   | —         | —             |
| TASK-011 | Continuity Agent mit Retrieval                         | ⏳ ausstehend   | —         | —             |
| TASK-012 | Timeline- und Character-State-Tracking                 | ⏳ ausstehend   | —         | —             |
| TASK-013 | World-Rules-Engine                                     | ⏳ ausstehend   | —         | —             |

Statuswerte: `⏳ ausstehend` → `🔄 in Bearbeitung` → `✅ erledigt` oder `❌ abgebrochen`

## Plan-übergreifende Abhängigkeiten

- Voraussetzung: `01-fundament-und-kontext/TASK-002` (Router) und `TASK-003` (Store).
- Nachgelagert: `03-szenen-und-lokales-llm/` baut auf TASK-001/002 (Tools), TASK-003 (Eval-Gerüst), TASK-007/008 (Orchestrator/Pipeline) und TASK-012/013 auf.
- `04-qualitaet-workflow-und-export/TASK-004` (Observability) kann ab TASK-008 parallel starten.
