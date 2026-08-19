# Plan 4: Qualität, Workflow und Export

> Teil 4 von 4 des mk34-Book-Writing-Systems. Gesamtübersicht, Entscheidungen E1–E6 und Model-Routing-Matrix: [`../README.md`](../README.md).
> Stand: 2026-08-17 · hervorgegangen aus `mk34-book-writing-system/` (aufgelöst)

Dieser Plan macht aus dem funktionierenden System einen Autoren-Arbeitsplatz: Qualitätssicherung für lokal generierte Szenen, der iterative Schreib-Workflow mit eigener `mk34`-CLI, Export in Publikationsformate und die Observability-Querschnittsaufgabe.

## Task-Mapping (alt → neu)

| Alt (Gesamtplan) | Neu | Anmerkung |
|---|---|---|
| TASK-019 Qualitätssicherung für lokale Outputs | TASK-001 | Editor-Referenz jetzt Gemini Pro statt Opus (E6); Claude als spätere Option |
| TASK-020 Workflow und Iteration (Feedback, Varianten, CLI) | TASK-002 | unverändert |
| TASK-021 Export und finaler Polish | TASK-003 | unverändert |
| TASK-022 Observability und Logging | TASK-004 | unverändert; kann früh parallel starten |

## Ziele

- Lokal generierte Szenen sind stilistisch nicht von Cloud-Szenen unterscheidbar („die Naht ist unsichtbar"), ohne den Inhalt zu entschärfen.
- Professioneller Autoren-Workflow: Feedback-Loop, Varianten, Rewrite-Modes, Session-Rewind, Statistiken — über eine dünne `mk34`-CLI (Typer) auf dem ADK-`Runner`.
- Publikationsfertiger Export (EPUB/PDF/DOCX via Pandoc) mit finalem Lektorat und Style-Transfer.
- Nachvollziehbarkeit: pro Szene ein Lauf-Protokoll (Modell, Route, Iterationen, Kosten), Judge-Kosten pro Stufe.

## Nicht-Ziele

- Kein Deployment, kein Multi-User, keine Web-UI (unverändert).
- Kein Versuch, das lokale 26B-Modell auf Frontier-Niveau zu heben — Angleichung, nicht Aufwertung.

## Architekturübersicht

Keine neuen Systemteile — dieser Plan veredelt Bestehendes:
- **TASK-001** hängt sich an den Editor-Loop (Plan 2/TASK-006, Plan 3/TASK-003): Pflicht-Durchlauf für lokale Szenen, Stil-Fingerprint als deterministisches Tool, Schwellen-Gate.
- **TASK-002** legt die `mk34`-CLI als dünnen Typer-Wrapper über den ADK-`Runner` — keine Agentenlogik in der CLI. Session-Rewind via `runner.rewind_async` (Voraussetzung `DatabaseSessionService` steht seit Plan 1, E3).
- **TASK-003** ergänzt `app/tools/export.py` (Pandoc) und den Style Agent (`model_for("style")`).
- **TASK-004** registriert Logging-Plugins am `App` und schreibt Lauf-Protokolle als JSON-Zeilen neben das Manuskript.

## Komponenten-Verantwortlichkeiten

| Komponente | Task | Modell (Start, E6) |
|---|---|---|
| Editor-Variante für lokale Outputs, `style_fingerprint.py` | TASK-001 | `gemini-3.1-pro-preview` |
| `app/cli/` (`mk34 feedback|write|rewrite|stats`), Rewrite-Agent | TASK-002 | bestehende Rollen |
| `app/tools/export.py`, `app/agents/style_agent.py` | TASK-003 | `gemini-3.1-pro-preview` |
| `app/app_utils/observability.py`, Logging-Plugins | TASK-004 | — |

## Ablaufsequenz

1. TASK-004 kann früh starten (braucht nur das Pipeline-Gerüst aus Plan 2).
2. TASK-001 nach Plan 3/TASK-004 (es braucht lokal generierte Szenen).
3. TASK-002 → TASK-003 sequenziell.
4. Fehlerpfade: Szene unter Qualitätsschwelle → `.draft.md` statt Übernahme; Rewind ändert keine Manuskriptdateien (Datei-Rollback via Git); Export bricht bei fehlendem Pandoc mit Installationshinweis ab.

## Konfiguration

Keine neuen Modell-Variablen. Neu: ggf. `MK34_LOG_DIR` (Lauf-Protokolle, TASK-004). Pandoc als dokumentierte Systemabhängigkeit (TASK-003). `pyproject.toml` erhält das Console-Script `mk34` (TASK-002).

## Tooling

| Zweck | Kommando |
|---|---|
| Autoren-Workflow (ab TASK-002) | `mk34 feedback|write|rewrite|stats` |
| Lokaler Run / Debug | `agents-cli run [-v]` · `agents-cli playground` |
| Eval-Regressionsgate | `agents-cli eval run` · `agents-cli eval compare` gegen die Plan-3-Baseline |
| Lint / Tests | `agents-cli lint` · `uv run pytest` |
| Export | `mk34 export --format epub|pdf|docx` (Pandoc) |

## Evaluationsplan

Dieser Plan führt keine neuen Datasets ein, sondern verschärft bestehende Gates:

| Gate | Task |
|---|---|
| `character_voice_consistency` ≥ 4/5 und `show_dont_tell` ≥ 4/5 auf **lokal generierten** Cases, **nach** Editor-Durchlauf | TASK-001 |
| Stil-Fingerprint-Streuung lokal vs. Cloud unter definierter Schwelle | TASK-001/003 |
| Keine Regression gegenüber der Plan-3-Baseline bei jedem Task-Abschluss (`agents-cli eval compare`) | alle |
| Finaler Gesamtlauf grün vor Export-Abnahme | TASK-003 |

Judge-Kosten pro Stufe (fast/craft) aus TASK-004 validieren die E4-Aufteilung — bei Auffälligkeiten wird eine Rubrik umgestuft (Ein-Zeilen-Änderung im `tier`-Frontmatter).

## Entschieden

- **E10 (2026-08-17, vormals Offene Frage #2) — entschieden mit beobachtetem Risiko:** Gemini-first gilt auch für den Editor über unzensierte lokale Szenen. Die benannten Fallbacks bleiben stehen und werden **gezogen, falls Gemini-Safety in der Praxis eingreift**: (a) Claude-Umschaltung der Editor-Rolle per `.env` oder (b) Editor-Durchlauf auf der lokalen Route. TASK-001 prüft das Verhalten als erstes und definiert den Auslöser für den Fallback-Zug. (Gesamtliste E1–E10: [`../README.md`](../README.md).)

## Offene Fragen

1. **Batch-/Nacht-Modus für Varianten (übernommen):** lokal 2–5 Min pro Szene → 6–15 Min für `--variants 3`. Akzeptabel oder braucht TASK-002 einen Queue-Modus?
