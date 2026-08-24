# Status: Szenen und lokales LLM (Plan 3)
Aktualisiert: 2026-08-17T00:00:00Z

| Task-ID  | Titel                                                | Status         | Gestartet | Abgeschlossen |
|----------|------------------------------------------------------|----------------|-----------|---------------|
| TASK-001 | Lokales LLM im Model-Router (Live-Roundtrip gg. laufende VM offen) | ✅ erledigt | 2026-08-24T00:00:00Z | 2026-08-24T00:00:00Z |
| TASK-002 | Scene Agent (Start Gemini, Ziel lokal, lokale Route live offen) | ✅ erledigt | 2026-08-24T00:00:00Z | 2026-08-24T00:00:00Z |
| TASK-003 | Szenen-Schritt in die Schreib-Pipeline                | ✅ erledigt | 2026-08-24T00:00:00Z | 2026-08-24T00:00:00Z |
| TASK-004 | Content-Klassifikation und lokales Routing           | ⏳ ausstehend   | —         | —             |
| TASK-005 | Szenen-Evals (Datasets und Metriken) — Stufe A        | 🔄 in Bearbeitung | 2026-08-24T00:00:00Z | —           |

Statuswerte: `⏳ ausstehend` → `🔄 in Bearbeitung` → `✅ erledigt` oder `❌ abgebrochen`

## Plan-übergreifende Abhängigkeiten

- Voraussetzung aus Plan 1: `01-fundament-und-kontext/TASK-002` (Router-Schnittstelle) und `TASK-003` (Store).
- Voraussetzung aus Plan 2: `02-agenten-kern-und-kontinuitaet/TASK-001/002` (Tools), `TASK-003` (Eval-Gerüst), `TASK-007/008` (Orchestrator/Pipeline-Slot), für TASK-004 zusätzlich `TASK-012/013` (Timeline/World-Rules).
- Nachgelagert: `04-qualitaet-workflow-und-export/TASK-001` (QS lokale Outputs) setzt TASK-004 voraus.
