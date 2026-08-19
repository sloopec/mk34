# mk34 — Planübersicht

Das Projekt „AI Book Writing System" (Google ADK, Buchprojekt *Life Link*) ist in **vier eigenständige Pläne** aufgeteilt. Der frühere Gesamtplan `mk34-book-writing-system/` wurde am 2026-08-17 aufgelöst; seine Inhalte sind vollständig auf die vier Pläne verteilt (Mapping-Tabellen jeweils im `plan.md`).

## Die vier Pläne und ihre Reihenfolge

| # | Plan | Inhalt | Status |
|---|---|---|---|
| 1 | [`01-fundament-und-kontext/`](01-fundament-und-kontext/plan.md) | Scaffold (✅), Model-Router (Gemini-first), Kontext-Store aus `basics.md` | in Arbeit (1/3 erledigt) |
| 2 | [`02-agenten-kern-und-kontinuitaet/`](02-agenten-kern-und-kontinuitaet/plan.md) | Tools, Eval-Grundgerüst, Plot-/Character-/Editor-Agent, Orchestrator, Pipeline-Gerüst, Continuity/Timeline/World-Rules — **ohne Szenen-Anteile** | ausstehend |
| 3 | [`03-szenen-und-lokales-llm/`](03-szenen-und-lokales-llm/plan.md) | Alles rund um das Szenenschreiben: Scene Agent, lokales LLM im Router, Szenen-Schritt der Pipeline, Content-Klassifikation/Routing, Szenen-Evals | ausstehend |
| 4 | [`04-qualitaet-workflow-und-export/`](04-qualitaet-workflow-und-export/plan.md) | Qualitätssicherung lokaler Outputs, Autoren-Workflow/CLI, Export/Polish, Observability | ausstehend |

Empfohlene Reihenfolge: **1 → 2 → 3 → 4**. Plan 3 kann teilweise parallel zu den späten Plan-2-Tasks laufen (siehe Abhängigkeiten unten).

## Plan-übergreifende Abhängigkeiten

```
Plan 1                     Plan 2                          Plan 3                     Plan 4
──────                     ──────                          ──────                     ──────
TASK-001 Scaffold ✅
TASK-002 Router ──────────▶ (alle Tasks nutzen model_for) ─▶ TASK-001 Lokales LLM
TASK-003 Kontext-Store ───▶ TASK-001/002 Tools ───────────▶ TASK-002 Scene Agent
                           TASK-003 Eval-Grundgeruest ────▶ TASK-005 Szenen-Evals
                           TASK-008 Pipeline-Geruest ─────▶ TASK-003 Szenen-Schritt ─▶ TASK-004 Observability*
                           TASK-012/013 Timeline/Rules ───▶ TASK-004 Klassifikation ─▶ TASK-001 QS lokal
                                                                                       TASK-002 Workflow/CLI
                                                                                       TASK-003 Export
```
\* Observability (Plan 4/TASK-004) braucht nur das Pipeline-Gerüst und kann früh parallel starten.

In den Task-Dateien sind plan-übergreifende Abhängigkeiten explizit markiert, z. B. `Abhängig von (plan-übergreifend): 01-fundament-und-kontext/TASK-002`.

## Verbindliche Entscheidungen (gelten über alle vier Pläne)

| # | Entscheidung |
|---|---|
| E1 | **Eval-Grading vollständig lokal.** Kein GCP-Projekt. Nur `custom_metrics` mit `custom_function` (`execution: local`); managed Built-in-Metriken und `agents-cli eval analyze` entfallen und werden als lokale Judge-Funktionen nachgebaut. |
| E2 | **Retrieval für Continuity lokal.** Stufe 1: SQLite FTS5/BM25 über Szenen-Chunks; Stufe 2 (nur bei Recall-Failure): sqlite-vec + lokales Embedding-Modell. Kein Vertex Vector Search. |
| E3 | **Persistente Sessions ab dem ersten Setup.** `DatabaseSessionService` auf SQLite (`sqlite+aiosqlite:///./data/sessions.db`), nicht `InMemorySessionService`. Umgesetzt in Plan 1/TASK-001. |
| E4 | **Zweistufiger Eval-Judge.** `MK34_JUDGE_MODEL_FAST` für deterministiknahe Rubriken, `MK34_JUDGE_MODEL_CRAFT` nur für `character_voice_consistency` und `show_dont_tell`. Zuordnung über `tier`-Frontmatter der Rubrik, nicht am Call-Site. |
| E5 | **Buch-Datenverzeichnis** `books/life_link/` bleibt im Repo-Root, außerhalb des Agent-Projekts `mk34-book-agent/`. |
| E6 | **Gemini-first (neu, 2026-08-17).** Der User testet zunächst ausschließlich mit Gemini (`GEMINI_API_KEY` liegt in der `.env` des Agent-Projekts). Gemini-Modelle laufen ADK-nativ als Modell-String, ohne LiteLLM-Umweg. Claude (via LiteLLM) und das lokale Modell (nur Scene Agent) bleiben als **konfigurierbare Alternativen** im Router-Design — Umschaltung pro Agent per Konfiguration, ohne Code-Änderung. Auch die Eval-Judges (E4) starten auf Gemini (fast=Flash, craft=Pro); die Judge-Bibliothek ist provider-agnostisch. |
| E7 | **Preview-Modell freigegeben (2026-08-17).** `gemini-3.1-pro-preview` ist für alle Heavy-Rollen (Plot, Character, Editor, Style, Scene-Start, Judge-craft) akzeptiert, trotz Preview-Status. Bei Instabilität ist die Umschaltung auf `gemini-3.7-flash` eine `.env`-Zeile. (Löst Offene Frage Plan 1 #1.) |
| E8 | **Editor-Loop-Fixture (2026-08-17).** Szene E „Protokoll der Sehnsucht" aus `books/life_link/idea/basics.md` ist das Fixture für das szenenfreie Pipeline-Gerüst in Plan 2/TASK-008. (Löst Offene Frage Plan 2 #1.) |
| E9 | **Gemini-Refusal-Erkennung (2026-08-17).** Die „Refusal als Routing-Signal"-Logik deckt Gemini-Signale (Safety-Block/Finish-Reason) ab, nicht nur Claudes `stop_reason: refusal`. Verankert als Akzeptanzkriterium in Plan 3/TASK-004. (Löst Offene Frage Plan 3 #2.) |
| E10 | **Editor-Safety-Risiko akzeptiert (2026-08-17).** Gemini-first gilt auch für den Editor über unzensierte lokale Szenen. Die benannten Fallbacks (Claude-Editor via `.env` oder Editor-Durchlauf auf der lokalen Route) bleiben in Plan 4/TASK-001 stehen und werden **gezogen, falls Gemini-Safety in der Praxis eingreift** — entschieden mit beobachtetem Risiko. (Löst Offene Frage Plan 4 #2.) |

## Model-Routing-Matrix (Gemini-first, Stand 2026-08-17)

Modell-IDs verifiziert gegen `ai.google.dev/gemini-api/docs/models` (2026-08-17). Der Scaffold pinnt aktuell `gemini-3.6-flash`; die Umstellung auf die Zielmodelle erfolgt in Plan 1/TASK-002.

| Agent | Start (Gemini) | Später (Claude / lokal) | Grund |
|---|---|---|---|
| Orchestrator | `gemini-3.7-flash` | `anthropic/claude-sonnet-5` | Routing, kein kreatives Output |
| Plot Agent | `gemini-3.1-pro-preview` | `anthropic/claude-opus-5` | Gesamtüberblick, komplexes Reasoning |
| Character Agent | `gemini-3.1-pro-preview` | `anthropic/claude-opus-5` | psychologische Tiefe, Konsistenz |
| Scene Agent | `gemini-3.1-pro-preview` | **lokal** `openai/supergemma4` (Ziel) / `anthropic/claude-opus-5` | kreative Freiheit vs. Qualität — nur hier ist ein lokales LLM vorgesehen |
| Editor Agent | `gemini-3.1-pro-preview` | `anthropic/claude-opus-5` | Sprachgefühl, Stilkritik |
| Continuity Agent | `gemini-3.7-flash` | `anthropic/claude-sonnet-5` | schnell, faktenbasiert |
| Research Agent | `gemini-3.7-flash` (+ `google_search`) | `anthropic/claude-sonnet-5` | Fakten-Check; `google_search` ist mit Gemini nativ nutzbar |
| Style Agent | `gemini-3.1-pro-preview` | `anthropic/claude-opus-5` | Feinschliff |
| Content-Classifier | `gemini-3.5-flash-lite` | `anthropic/claude-haiku-4-5` | billige, häufige Ja/Nein-Entscheidung |
| Eval-Judge `fast` | `gemini-3.7-flash` | `claude-sonnet-5` | Regelabgleich gegen Trace/Vorgaben |
| Eval-Judge `craft` | `gemini-3.1-pro-preview` | `claude-opus-5` | Lektorats-Urteil (Stimme, Show-don't-tell) |

Hinweis: `gemini-3.1-pro-preview` ist das derzeit stärkste Reasoning-Modell, trägt aber Preview-Status — siehe Offene Frage in Plan 1.

## Konventionen

- Plan-Artefakte auf Deutsch; Fachbegriffe und Datei-/Ordnernamen englisch.
- Statuswerte: `⏳ ausstehend` → `🔄 in Bearbeitung` → `✅ erledigt` / `❌ abgebrochen`.
- Pro erledigtem Task: `walkthroughs/TASK-NNN-*.md` und `feature_summary/TASK-NNN-*.md` im jeweiligen Plan-Ordner; eine Gesamt-`feature_summary.md` neben `plan.md` erst bei Planabschluss.
- Historischer Ursprung: `docs/PLAN.md` (eingefroren, verweist hierher).
