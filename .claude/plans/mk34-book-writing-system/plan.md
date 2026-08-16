# mk34 — AI Book Writing System (Google ADK)

> Ueberarbeitete, maßgebliche Version des urspruenglichen `docs/PLAN.md`.
> Stand: 2026-08-16 · Quelle der ADK-/Tooling-Konventionen: `.claude/skills/google-agents-cli-*` (agents-cli v1.3.1)
> Buchgrundlagen: `books/life_link/idea/basics.md` · Lokales Modell: `docs/LOCAL_MODEL_VM_SETUP.md`

---

## Goals

- Ein Multi-Agenten-System auf Google ADK, das die Funktionalitaet von Sudowrite und NovelCrafter vereint und um modell-agnostisches Routing, unzensierte lokale Modelle und strukturiertes Manuskript-Management erweitert.
- Erstes Zielprojekt: der Techno-Thriller **"Life Link"** (`books/life_link/`).
- Spezialisierte Agenten (Plot, Figuren, Szene, Lektorat, Continuity, Recherche, Stil) arbeiten ueber einen Orchestrator zusammen; Kontext (Figuren, Plot, Weltregeln, Timeline) ist persistent und git-versioniert.
- Bewusste Modell-Heterogenitaet: Cloud-Modelle (Claude via LiteLLM) fuer Reasoning/Lektorat, **lokales unzensiertes Modell** fuer Szenen, die Cloud-Anbieter ablehnen wuerden.
- Qualitaet wird messbar gemacht: jede Phase hat einen `agents-cli eval`-Gate, nicht nur „liest sich gut".

## Non-Goals

- **Keine Cloud-Deployment-Phase im Erstausbau.** Das System laeuft lokal (Prototype-Scaffold). `agents-cli deploy` / `publish` / Agent Runtime / Gemini Enterprise sind explizit Non-Goals, bis der Autoren-Workflow steht. Der Upgrade-Pfad ist dokumentiert (siehe *Tooling*), wird aber nicht umgesetzt.
- Kein Multi-User-Betrieb, keine Auth, keine Web-UI ausser dem mitgelieferten `agents-cli playground`.
- Keine automatische Veroeffentlichung/Distribution des Manuskripts.
- Kein Feintuning eigener Modelle.
- Keine `safety`-Guardrails auf dem Scene Agent — das widerspraeche dem Kern-Use-Case (siehe *Evaluation Plan*).

---

## Architecture Overview

### Aenderungen gegenueber `docs/PLAN.md` (Begruendung)

| # | Aenderung | Begruendung |
|---|---|---|
| 1 | Projektstruktur kommt aus `agents-cli scaffold create --prototype`, nicht handgebaut | Skill `google-agents-cli-scaffold`: manuelles Setup verliert Eval-Boilerplate, `agents-cli-manifest.yaml`, `fast_api_app.py`, Dockerfile, CI-Konventionen. Agent-Code liegt in `app/`, nicht `src/agents/`. |
| 2 | `src/setup/basics.md` → `books/life_link/idea/basics.md` | Pfad im Originalplan existiert nicht. Realer Repo-Stand. |
| 3 | Lokales Modell = **llama.cpp / `supergemma4-26b-abliterated`** ueber OpenAI-kompatiblen Endpoint, nicht Ollama/Mistral/Llama-3 | `docs/LOCAL_MODEL_VM_SETUP.md` beschreibt bereits die konkrete Ziel-Infrastruktur (verschluesselte Parallels-VM, `llama-server`, SSH-Tunnel auf `localhost:8080/v1`). Der Plan war hier veraltet. Ollama bleibt als optionale Alternative. |
| 4 | Claude-Modell-IDs aktualisiert: `claude-opus-5`, `claude-sonnet-5`, `claude-haiku-4-5` | Die im Plan genannten „Opus/Sonnet" ohne Version sind nicht mehr aufloesbar. LiteLLM-Praefix: `anthropic/<model-id>`. |
| 5 | Konkrete ADK-Primitives statt generischer „Agent"-Kaesten | `LlmAgent`/`Agent`, `SequentialAgent`, `LoopAgent`, `AgentTool`, `FunctionTool`, `Runner`, `Session`/`State`, `output_key`, Callbacks, `App`. |
| 6 | Eigene CLI (`mk34 write-scene ...`) wird von Phase 1 auf Phase 5 verschoben | `agents-cli run` / `agents-cli playground` decken Phase 1–4 vollstaendig ab. Eine eigene CLI vor dem Eval-Gate ist verfrueht. |
| 7 | Continuity-Agent liest nicht „das gesamte Manuskript" per Prompt | Bei >30 Kapiteln sprengt das jedes Kontextfenster und jedes Budget. Stattdessen: Retrieval (Recipe `rag-vector-search`) + `ContextCacheConfig` + `EventsCompactionConfig`. |
| 8 | Neue Pflichtsektionen **Tooling** und **Evaluation Plan** | Vorgabe der Architekten-Baseline. Ohne Eval-Gate ist „Qualitaet" nicht pruefbar. |
| 9 | Phasenlogik, Model-Routing-Grundidee und Agenten-Zuschnitt bleiben unveraendert | Bewusste User-Entscheidung; dies ist eine Ueberarbeitung, kein Neuentwurf. |
| 10 | **Eval laeuft vollstaendig lokal** — nur `custom_metrics` mit `custom_function` (`execution: local`), LLM-Judge ist ein direkter Claude-API-Aufruf | Entscheidung des Users: kein GCP-Projekt. Konsequenz: die managed Built-in-Metriken (`multi_turn_task_success`, `final_response_quality`, `hallucination`, …) laufen server-seitig im Agent Platform Eval Service und stehen damit **nicht** zur Verfuegung; sie werden als lokale Judge-Funktionen nachgebaut. |
| 11 | **Retrieval fuer Continuity laeuft lokal** — SQLite FTS5/BM25 ueber Szenen-Chunks, optional sqlite-vec + lokales Embedding-Modell | Entscheidung des Users: kein Vertex AI Vector Search. Passt zur Local-First-Haltung (verschluesselte VM, unzensierter Stoff verlaesst die Maschine nicht) und zur Korpusgroesse (ein Roman ≈ 100k Woerter, nicht Millionen Dokumente). |

### Komponentendiagramm (textuell)

```
┌───────────────────────────────────────────────────────────────────────┐
│  Entrypoints                                                          │
│  agents-cli playground (Web)  ·  agents-cli run "..."  ·  mk34 CLI(P5)│
└───────────────────────────┬───────────────────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────────────┐
│  app/agent.py  —  root_agent: LlmAgent "orchestrator"                 │
│  Coordinator-Pattern: sub_agents (LLM-Delegation) + AgentTool(...)    │
└───┬───────────┬───────────┬───────────┬───────────┬───────────┬───────┘
    │           │           │           │           │           │
┌───▼───┐  ┌────▼────┐  ┌───▼────┐  ┌───▼────┐  ┌───▼─────┐ ┌──▼──────┐
│ Plot  │  │Character│  │ Scene  │  │ Editor │  │Continui-│ │Research │
│Agent  │  │ Agent   │  │ Agent  │  │ Agent  │  │ty Agent │ │ + Style │
│Opus 5 │  │ Opus 5  │  │ LOKAL  │  │ Opus 5 │  │Sonnet 5 │ │Sonnet/  │
│       │  │         │  │ /Opus  │  │        │  │         │ │Opus 5   │
└───┬───┘  └────┬────┘  └───┬────┘  └───┬────┘  └───┬─────┘ └──┬──────┘
    │           │           │           │           │           │
┌───▼───────────▼───────────▼───────────▼───────────▼───────────▼───────┐
│  app/tools/  —  FunctionTools                                         │
│  manuscript.py · context_loader.py · consistency.py · timeline.py     │
│  characters.py · export.py                                            │
└───────────────────────────┬───────────────────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────────────┐
│  Persistenz (git-versioniert, ausserhalb von app/)                    │
│  books/life_link/idea/basics.md            (Quelle, read-only)        │
│  books/life_link/store/characters.json     plot_outline.json          │
│                       world_bible.md       timeline.json              │
│                       style_guide.md                                  │
│  books/life_link/manuscript/kapitel_NN.md                             │
├───────────────────────────────────────────────────────────────────────┤
│  Session/State (ADK)  —  DatabaseSessionService (SQLite, ab Phase 1)  │
│                          sqlite:///./data/sessions.db  (gitignored)   │
├───────────────────────────────────────────────────────────────────────┤
│  Model Layer  —  app/models/router.py                                 │
│  LiteLlm("anthropic/claude-opus-5" | "claude-sonnet-5")               │
│  LiteLlm("openai/supergemma4", api_base="http://localhost:8080/v1")   │
└───────────────────────────────────────────────────────────────────────┘
```

**Warum getrennte Persistenz-Ebene:** ADK-`State` ist session-gebunden. Das Manuskript und der Story-Kanon muessen git-versioniert und ueber Sessions hinweg stabil sein. Regel: **Files = Wahrheit, State = Arbeitskopie der aktuellen Szene.**

**Session-Persistenz (entschieden): `DatabaseSessionService` mit SQLite ab dem ersten Setup**, nicht `InMemorySessionService`.

```python
from google.adk.sessions import DatabaseSessionService
session_service = DatabaseSessionService(db_url="sqlite:///./data/sessions.db")
```

Begruendung:
- **Voraussetzung fuer `runner.rewind_async(...)`** (Phase 5). Rewind auf einer In-Memory-Session ist wertlos, sobald der Prozess endet — und genau das passiert zwischen zwei `agents-cli run`-Aufrufen.
- **Sitzungsuebergreifendes Weiterarbeiten:** ein Kapitel entsteht ueber Tage. `agents-cli run --session-id <id>` kann eine Session fortsetzen, statt bei jedem Aufruf den Kontext neu aufzubauen.
- **Local-First, konsistent mit dem Rest des Projekts:** eine Datei neben dem Projekt, kein Server, kein Cloud SQL.
- **Trivialer Konfigurationsaufwand:** eine Zeile. Es gibt keinen Grund, erst in Phase 5 zu migrieren und dabei alle bis dahin entstandenen Sessions zu verlieren.

`data/sessions.db` ist gitignored. Nur der Manuskript- und Kanon-Stand gehoert ins Repo, nicht die Gespraechshistorie.

### Orchestrierungs-Pattern

Drei Muster nebeneinander, jeweils dort wo sie hingehoeren:

1. **LLM-Delegation** (`sub_agents=[...]` am Orchestrator) — fuer freie Nutzeranfragen im Playground („entwickle Akt 2 weiter").
2. **`SequentialAgent`** — fuer die deterministische Schreib-Pipeline:
   `context_loader → plot_beat → character_brief → scene_writer → editor`, Datenfluss ueber `output_key` + `{state_key}`-Injection in den Instructions.
3. **`LoopAgent`** — fuer die Lektorats-Iteration: `editor → quality_checker(BaseAgent, escalate=True bei „pass")`, `max_iterations=3`.

Spezialisten, die *innerhalb* eines Zuges konsultiert werden (Character, Research, Continuity), werden als **`AgentTool`** eingebunden — der aufrufende Agent behaelt die Kontrolle und bekommt eine Antwort zurueck, statt den Turn abzugeben.

### Reference Recipes (Phase 1 der agents-cli-Lifecycle)

Vor Implementierung zu klonen und zu studieren (`git clone --filter=blob:none --depth 1 --sparse https://github.com/google/adk-samples`):

| Bedarf | Recipe |
|---|---|
| Continuity-Agent: Retrieval ueber das eigene Manuskript | `core/python/rag-vector-search` — **nur Chunking- und Query-Muster uebernehmen**, nicht die Vertex-Infrastruktur (`infra/terraform/`, KFP-Ingestion). Backend ist lokal, siehe unten. |
| Kritik→Refine-Schleife bis Qualitaetsschwelle + Recherche mit Quellen | `core/python/deep-search` |
| Cross-Session-Gedaechtnis (Autor-Praeferenzen, Stilentscheidungen) | `core/python/cross-session-memory` |
| Sub-Agent-Delegation mit isolierten Kontextfenstern, Model-Routing, Skills, Langlaeufer | `core/python/long-horizon-harness` |

---

## Component Responsibilities

### `app/agent.py` — Orchestrator (root_agent)
- Nimmt High-Level-Befehle entgegen und routet an Sub-Agents bzw. startet die Schreib-Pipeline.
- Kein kreatives Output. Modell: `claude-sonnet-5` (Routing-Entscheidungen).
- `before_agent_callback=initialize_state` — initialisiert `book_slug`, `active_chapter`, `active_scene`, `style_profile`, damit `{state_key}`-Injection nicht mit `KeyError` bricht.
- `App(name="app", ...)` — **Name muss dem Agent-Verzeichnis entsprechen**, sonst „Session not found" im Eval.

### Plot Agent
- Input: Akt-Nummer oder grobe Idee. Output: Szenen-Beats, Wendepunkte, Spannungsbogen.
- Tools: `read_plot_outline()`, `update_plot_outline(...)`, `read_chapter_summaries()`.
- Modell: `claude-opus-5` (braucht Gesamtueberblick).
- `output_schema` (Pydantic `SceneBeat`) fuer strukturierte Beats — **Achtung:** `output_schema` deaktiviert Tool-Calling; daher zweistufig (Agent mit Tools sammelt Kontext → Sub-Agent mit `output_schema` formalisiert).

### Character Agent
- Input: Figurenname + Szenenkontext. Output: figurengerechte Dialogvorschlaege, Reaktionen, innere Konflikte.
- Tools: `get_character(name)`, `update_character(name, development)`, `get_character_arc(name)`.
- Validiert Verhalten gegen die bisherige Entwicklung (David = Laie/„Nanobots", Sarah = praezise/„Naniten" — Sprachregister aus `basics.md`).
- Modell: `claude-opus-5`. Eingebunden als `AgentTool`.

### Scene Agent
- Input: Beat + Figuren-Brief + Weltregeln. Output: Szenentext (Markdown).
- Tools: `read_manuscript(chapter)`, `write_scene(chapter, scene, text)`.
- Modell: **routing-abhaengig** — lokal (`supergemma4-26b-abliterated`) oder `claude-opus-5`, entschieden vom Content-Classifier (Phase 4) oder per Override.
- **Keine `safety`-Callbacks/Plugins auf diesem Agent** (bewusste Entscheidung, siehe Non-Goals).

### Editor Agent (Lektor)
- Input: Rohtext. Output: ueberarbeitete Fassung + Anmerkungen.
- Prueft Stilkonsistenz, Sprachregister pro Figur, Pacing, Show-don't-tell.
- Modell: `claude-opus-5`. Laeuft auch ueber lokal generierte Szenen (Qualitaetsangleichung).

### Continuity Agent
- Prueft neue Szenen gegen Timeline, Ortswechsel, Figurenpositionen, etablierte Fakten.
- **Nicht** „liest das ganze Manuskript" — sondern: Retrieval der k relevantesten Vorpassagen + `timeline.json` + Character-State.
- Tool: `check_consistency(new_text, context_refs[]) -> {conflicts: [...]}`.
- Modell: `claude-sonnet-5` (schnell, faktenbasiert).

#### Retrieval-Backend (entschieden: lokal)

Kein Vertex AI Vector Search, keine Cloud-Ingestion. Begruendung: der Korpus ist klein (ein Roman ≈ 100k Woerter ≈ 200–400 Szenen-Chunks), die Suchanfragen sind stark entitaetenlastig (Figurennamen, Orte, Fachbegriffe wie „Naniten", „LifeLink", „Tote Zone") — genau der Fall, in dem lexikalische Suche stark ist —, und der Stoff soll die Maschine nicht verlassen (dieselbe Begruendung wie fuer die verschluesselte VM des lokalen Modells).

**Stufe 1 (Baseline, Phase 3):** SQLite **FTS5** mit BM25-Ranking.
- Index: `books/life_link/.index/manuscript.db`, gitignored, jederzeit aus dem Manuskript rebuildbar.
- Chunk-Grenze = **Szene**, nicht fixe Tokenzahl. Jeder Chunk traegt Metadaten: `chapter`, `scene`, `pov_character`, `characters_present`, `location`, `timestamp`.
- Query = Metadaten-Filter (beteiligte Figuren/Ort) **plus** BM25-Volltext ueber die Entitaeten der neuen Szene.
- Null zusaetzliche Infrastruktur, stdlib-`sqlite3`, deutschsprachig unproblematisch (Unicode61-Tokenizer).

**Stufe 2 (optionaler Ausbau, nur wenn Stufe 1 die Recall-Schwelle auf `continuity.json` reisst):** hybrides Retrieval mit **`sqlite-vec`** im selben DB-File plus einem lokalen Embedding-Modell (mehrsprachig, z. B. `bge-m3` oder `multilingual-e5` via `sentence-transformers`, oder eine zweite `llama.cpp`-Instanz mit `/v1/embeddings`). Reciprocal-Rank-Fusion ueber BM25- und Vektor-Treffer.

**Nicht** das Generierungsmodell (`supergemma4-26b`) fuer Embeddings zweckentfremden — dafuer ein dediziertes, kleines Embedding-Modell.

Entscheidungskriterium fuer Stufe 2 ist messbar: Recall auf `tests/eval/datasets/continuity.json`. Erst bauen, wenn Stufe 1 dort durchfaellt.

### Research Agent
- Wissenschaftliche Plausibilitaet (Naniten, CRISPR, Neurochemie) — Grundlage fuer die Edutainment-/ELI5-Ebene des Buchs.
- Tool: `google_search` **oder** FunctionTools — nicht beides im selben Agent (Built-in-Search deaktiviert Automatic Function Calling). Daher eigener Sub-Agent nur mit Search.
- Modell: `claude-sonnet-5`.

### Style Agent
- Feinschliff, literarische Qualitaet, Angleichung von Passagen unterschiedlicher Modellherkunft.
- Liest `style_guide.md`. Modell: `claude-opus-5`.

### `app/models/router.py`
- Zentrale Modellauswahl: `model_for(role: str) -> BaseLlm`.
- Kapselt `LiteLlm`-Konstruktion inkl. `api_base`/`api_key` fuer das lokale Modell.
- Health-Check gegen `http://localhost:8080/health`; Fallback auf Cloud mit expliziter Warnung, wenn die VM nicht laeuft.

### `app/tools/*`
Reine FunctionTools, alle mit Typannotationen ohne Defaults, dict-Return und Docstrings (ADK-Toolregeln):
- `manuscript.py` — `read_manuscript`, `write_scene`, `list_chapters`, `chapter_stats`
- `context_loader.py` — `load_world_bible`, `load_style_guide`, `load_plot_outline`
- `characters.py` — `get_character`, `update_character`, `get_character_arc`
- `consistency.py` — `check_consistency`, `validate_world_rules`
- `timeline.py` — `read_timeline`, `append_event`, `validate_chronology`
- `export.py` — `export_markdown`, `export_epub`, `export_docx` (Pandoc)

---

## Sequence Flow

### Happy Path — „Schreibe Kapitel 3, Szene 2"

1. Nutzer gibt den Auftrag im `agents-cli playground` (oder via `agents-cli run "..."`).
2. **Orchestrator** parst Kapitel/Szene, schreibt `active_chapter`/`active_scene` in `session.state`, startet die `SequentialAgent`-Pipeline.
3. **context_loader** (FunctionTool-Aufrufe): laedt `world_bible.md`, `style_guide.md`, den Plot-Beat und die betroffenen Figuren → `output_key="scene_context"`.
4. **Plot Agent** liefert bzw. bestaetigt den Beat fuer 3.2 → `output_key="scene_beat"`.
5. **Character Agent** (als `AgentTool`) liefert Figuren-Brief inkl. Sprachregister → `output_key="character_brief"`.
6. **Content-Classifier** (Phase 4) bewertet den Beat → `state["route"] = "local" | "cloud"`.
7. **Scene Agent** schreibt die Szene mit `{scene_context}`, `{scene_beat}`, `{character_brief}` in der Instruction, auf dem geroutenen Modell → `output_key="scene_draft"`.
8. **Continuity Agent** prueft `scene_draft` gegen Retrieval-Treffer + Timeline → `output_key="continuity_report"`.
9. **LoopAgent(Editor + QualityChecker, max_iterations=3)**: Editor ueberarbeitet unter Beruecksichtigung von `continuity_report`; QualityChecker (`BaseAgent`) setzt `EventActions(escalate=True)`, sobald die Rubrik bestanden ist.
10. `write_scene(...)` schreibt nach `books/life_link/manuscript/kapitel_03.md`; `append_event(...)` aktualisiert `timeline.json`; `update_character(...)` aktualisiert den Figurenzustand.
11. Orchestrator gibt Diff-Zusammenfassung + offene Continuity-Hinweise aus. Git-Commit bleibt beim Autor.

### Error Paths

| Fehlerfall | Verhalten |
|---|---|
| Lokales Modell nicht erreichbar (`/health` fail) | Router meldet es explizit; Abbruch mit Handlungsanweisung („VM starten") **oder** — nur bei explizitem `--allow-cloud-fallback` — Cloud-Fallback mit Warnung. Kein stiller Fallback: eine unzensierte Szene auf einem Cloud-Modell endet sonst in einer Refusal oder abgeschwaechtem Text. |
| Cloud-Refusal (`stop_reason: refusal`) | Als Signal behandeln: Szene auf lokales Modell umrouten, Klassifikations-Regel nachschaerfen, Fall in der Eval-Suite ergaenzen. |
| Continuity-Konflikt gefunden | Szene wird **nicht** geschrieben; Konfliktliste mit Referenzen wird ausgegeben; Autor entscheidet (Retcon vs. Korrektur). |
| Editor-Loop erreicht `max_iterations` ohne Pass | Beste Fassung wird als `*.draft.md` abgelegt, mit Rubrik-Verdikt als Frontmatter. Nie stillschweigend als „fertig" markieren. |
| Tool-Schreibfehler (Datei gesperrt/Pfad falsch) | Tool gibt `{"status": "error", ...}` zurueck; Agent bricht ab statt zu halluzinieren, dass geschrieben wurde. |
| Kontextfenster laeuft voll (lange Session) | `EventsCompactionConfig` am `App` fasst aeltere Events zusammen; Kanon bleibt in den Dateien, nicht in der History. |

---

## Configuration

Pydantic-Settings + `.env` im Projektroot. Secrets **nie** im Repo (`.env` ist gitignored).

| Variable | Zweck | Beispiel |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude via LiteLLM | `sk-ant-...` |
| `MK34_CLOUD_HEAVY_MODEL` | Reasoning-/Lektorats-Modell | `anthropic/claude-opus-5` |
| `MK34_CLOUD_FAST_MODEL` | Routing/Continuity/Recherche | `anthropic/claude-sonnet-5` |
| `MK34_LOCAL_MODEL` | LiteLLM-Name des lokalen Modells | `openai/supergemma4` |
| `MK34_LOCAL_API_BASE` | llama-server ueber SSH-Tunnel | `http://localhost:8080/v1` |
| `MK34_LOCAL_API_KEY` | llama-server braucht keinen Key | `not-needed` |
| `MK34_LOCAL_HEALTH_URL` | Preflight-Check | `http://localhost:8080/health` |
| `MK34_BOOK_SLUG` | aktives Buchprojekt | `life_link` |
| `MK34_BOOK_ROOT` | Wurzel der Buchdaten | `books/life_link` |
| `MK34_ALLOW_CLOUD_FALLBACK` | Cloud-Fallback bei lokalem Ausfall | `false` |
| `MK34_JUDGE_MODEL_FAST` | Judge fuer deterministiknahe Rubriken (Mehrheit der Metriken) | `claude-sonnet-5` |
| `MK34_JUDGE_MODEL_CRAFT` | Judge fuer die zwei sprachlich-handwerklichen Rubriken | `claude-opus-5` |
| `MK34_INDEX_PATH` | lokaler Retrieval-Index (gitignored, rebuildbar) | `books/life_link/.index/manuscript.db` |
| `MK34_SESSION_DB_URL` | persistente ADK-Sessions (SQLite, gitignored) | `sqlite:///./data/sessions.db` |
| `GOOGLE_CLOUD_PROJECT` / `GOOGLE_CLOUD_LOCATION` / `GOOGLE_GENAI_USE_VERTEXAI` | vom Scaffold erzeugt — **wird nicht gebraucht.** Kein GCP-Projekt im Projektumfang: Eval laeuft lokal, Retrieval laeuft lokal, kein Deployment. Zeilen in `.env` belassen (Scaffold-Konvention), aber leer/ungenutzt. | — |

**Nicht anfassen** (vom Scaffold erzeugt): `agents-cli-manifest.yaml`, `app/__init__.py`, `app/fast_api_app.py`, `app/app_utils/`, `Dockerfile`, `Makefile`.

### Model-Routing-Matrix (aktualisiert)

| Agent | Primaeres Modell | LiteLLM-String | Grund |
|---|---|---|---|
| Orchestrator | Claude Sonnet 5 | `anthropic/claude-sonnet-5` | Routing, kein kreatives Output |
| Plot Agent | Claude Opus 5 | `anthropic/claude-opus-5` | Gesamtueberblick, komplexes Reasoning |
| Character Agent | Claude Opus 5 | `anthropic/claude-opus-5` | psychologische Tiefe, Konsistenz |
| Scene Agent | **lokal** / Opus 5 | `openai/supergemma4` @ `localhost:8080/v1` | kreative Freiheit vs. Qualitaet — Kernentscheidung des Projekts |
| Editor Agent | Claude Opus 5 | `anthropic/claude-opus-5` | Sprachgefuehl, Stilkritik |
| Continuity Agent | Claude Sonnet 5 | `anthropic/claude-sonnet-5` | schnell, faktenbasiert |
| Research Agent | Claude Sonnet 5 (+ Search) | `anthropic/claude-sonnet-5` | Fakten-Check |
| Style Agent | Claude Opus 5 | `anthropic/claude-opus-5` | Feinschliff |
| Content-Classifier (P4) | Claude Haiku 4.5 | `anthropic/claude-haiku-4-5` | billige, haeufige Ja/Nein-Entscheidung |

Hinweis: ADK/agents-cli scaffolden per Default Gemini-Modelle. Die Abweichung auf Claude+lokal ist eine bewusste Entscheidung; sie wird beim Scaffolding explizit ueberschrieben (siehe Open Questions #1).

---

## Tooling

Alles laeuft ueber `agents-cli` (v1.3.1). Keine handgebauten Skripte, wo die CLI zustaendig ist.

| Zweck | Kommando |
|---|---|
| Version/Diagnose | `agents-cli info` · `agents-cli cmd-info` |
| Auth | `agents-cli login` — **entfaellt.** Kein GCP im Projektumfang; benoetigt wird nur `ANTHROPIC_API_KEY`. |
| **Scaffolding** | `agents-cli scaffold create mk34-book-agent --agent adk --prototype --agent-guidance-filename CLAUDE.md` |
| Struktur nachruesten (spaeter, optional) | `agents-cli scaffold enhance . --deployment-target cloud_run` |
| CLI-Version anheben | `agents-cli scaffold upgrade --dry-run` → `agents-cli scaffold upgrade` |
| **Lokaler Run (interaktiv)** | `agents-cli playground` |
| **Lokaler Run (Smoke-Test)** | `agents-cli run "Schreibe Kapitel 1, Szene 1"` · `-v` fuer volle Event-JSONs · `--start-server` + `--session-id` fuer Serien |
| Lint | `agents-cli lint` |
| **Eval (Standardpfad)** | `agents-cli eval run` — laeuft vollstaendig lokal, da `metrics_to_run` nur lokale `custom_function`-Metriken enthaelt |
| Eval zweistufig (Debug) | `agents-cli eval generate` → `agents-cli eval grade --config tests/eval/eval_config.yaml` |
| Eval-Vergleich (Regressionsgate) | `agents-cli eval compare artifacts/grade_results/<alt>.json artifacts/grade_results/<neu>.json` |
| Metrik-Katalog | `agents-cli eval metric list` — nur informativ; die gelisteten Built-ins sind ohne GCP nicht nutzbar |
| Fehleranalyse | `agents-cli eval analyze` — **nicht verfuegbar** (nur `global`-Endpoint, braucht GCP). Ersatz: die `.html`-Reports in `artifacts/grade_results/` plus die `explanation`-Felder der eigenen Judge-Funktionen. |
| Prompt-Optimierung (nur auf Zuruf, teuer) | `agents-cli eval optimize --dataset ... --target-metric ...` |
| Observability | siehe Open Questions #3 — lokal genuegt `agents-cli run -v` + strukturierte Logs; Cloud Trace scheidet mit E1 aus |
| Deploy / Publish | **Non-Goal.** Pfad dokumentiert: `agents-cli scaffold enhance . --deployment-target cloud_run` → `agents-cli deploy`. |

Python-Ausfuehrung immer ueber `uv` (`uv sync`, `uv run ...`).

**Kein pytest auf LLM-Output.** pytest prueft Code-Korrektheit (Tools lesen/schreiben die richtigen Pfade, JSON-Schemas, Router liefert die richtige `BaseLlm`-Instanz). Verhalten wird ausschliesslich per `agents-cli eval` geprueft.

---

## Evaluation Plan

Eval ist der Gate jeder Phase. Erwartung laut Skill: **5–10+ Iterationen pro Case**, bevor er besteht.

### Datasets (`tests/eval/datasets/`)

| Datei | Inhalt | Ab Phase |
|---|---|---|
| `basic-dataset.json` | 2 Cases: „Schreibe Kapitel 1, Szene 1", „Wer ist Dr. Elias Voss?" | 1 |
| `scene-writing.json` | 5–8 Cases entlang der Beispielszenen aus `basics.md` (Vanilla-Pitch, kaltes Schlafzimmer, Diagnose, analoges Abendessen) | 1–2 |
| `multi-agent.json` | Multi-Turn: Plot-Beat → Figuren-Brief → Szene → Lektorat; prueft Tool-Trajektorie | 2 |
| `continuity.json` | Cases mit *absichtlich* eingebauten Widerspruechen (Figur weiss etwas zu frueh, Zeitsprung, Naniten verhalten sich regelwidrig) | 3 |
| `uncensored-routing.json` | Cases, die auf lokal geroutet werden muessen (Szene B/E aus `basics.md`) | 4 |

Schema: `eval_cases[].prompt = {role: "user", parts: [{text: "..."}]}` (Inference-Input). Traces erzeugt `eval generate`, nicht handgeschrieben.

### Grading-Architektur (entschieden: vollstaendig lokal)

**Kein GCP-Projekt.** Konsequenz, die man kennen muss: `agents-cli eval grade` fuehrt die **Built-in-Metriken server-seitig** im Agent Platform Eval Service aus. Ohne GCP stehen `multi_turn_task_success`, `multi_turn_tool_use_quality`, `multi_turn_trajectory_quality`, `final_response_quality`, `hallucination` und `safety` damit **nicht** zur Verfuegung. Ebenso entfaellt `agents-cli eval analyze` (nur `global`-Endpoint).

Was weiterhin lokal funktioniert:
- `agents-cli eval generate` — laeuft den Agenten lokal gegen das Dataset, schreibt Traces nach `artifacts/traces/`. Braucht kein GCP.
- `agents-cli eval grade` — solange `metrics_to_run` **ausschliesslich** `custom_metrics` mit `custom_function` enthaelt. Die laufen per Default `execution: local`, in-process, ohne Projekt und ohne Region.
- `agents-cli eval compare` — reine JSON-Diff-Operation.

Alle Metriken sind daher `custom_metrics` mit `custom_function`. Der LLM-Judge ist ein **direkter Claude-API-Aufruf innerhalb der Funktion** (`anthropic`-SDK) — kein Vertex, kein `LLMMetric`-Typ.

**Judge-Modell pro Rubrik (Entscheidung E4, verbindlich ab TASK-008):** zweistufig statt eines einheitlichen Opus-Judges. Jeder Eval-Lauf feuert n Cases × m Rubriken Judge-Aufrufe; ein pauschaler Opus-Judge macht die Suite teuer, ohne dort Qualitaet zu kaufen, wo die Rubrik ohnehin nahe an einer mechanischen Pruefung liegt.

- **`MK34_JUDGE_MODEL_FAST` = `claude-sonnet-5`** — deterministiknahe Rubriken: Der Judge prueft gegen den Trace bzw. gegen explizite Regeln („wurde das Ziel erreicht", „wurde das richtige Tool mit den richtigen Argumenten gerufen", „steht diese Behauptung in einem Tool-Output"). Die Antwort ist weitgehend nachpruefbar; Sprachgefuehl spielt keine Rolle.
- **`MK34_JUDGE_MODEL_CRAFT` = `claude-opus-5`** — nur `character_voice_consistency` und `show_dont_tell`. Beide bewerten literarisches Handwerk; hier ist der Judge naeher an einem Lektor als an einem Regelpruefer, und ein schwaecheres Urteil wuerde genau die Metriken entwerten, die den Kern des Projekts absichern.

Die Zuordnung liegt **an der Rubrik**, nicht am Aufrufort — jede Rubrik registriert ihre Stufe (`fast` | `craft`), `judge()` loest daraus das Modell auf. So kann eine Rubrik nicht versehentlich mit dem falschen Judge laufen, und eine spaetere Umstufung ist eine Ein-Zeilen-Aenderung.

### Metrik-Katalog

| Metrik | Art | Judge-Modell | Prueft | Ab Phase |
|---|---|---|---|---|
| `task_success` | LLM-Judge | **fast** (`claude-sonnet-5`) | Wurde die Aufgabe des Nutzers erfuellt? Catch-all fuer den Orchestrator. Ersatz fuer `multi_turn_task_success`. | 1 |
| `tool_use_quality` | LLM-Judge | **fast** | Richtige Tools, richtige Argumente, keine ueberfluessigen Aufrufe. Ersatz fuer `multi_turn_tool_use_quality`. | 2 |
| `trajectory_quality` | LLM-Judge | **fast** | Logischer, effizienter Weg — schreibt der Scene Agent, *bevor* er Kontext geladen hat? Ersatz fuer `multi_turn_trajectory_quality`. | 2 |
| `grounding` | LLM-Judge | **fast** | Behauptet der Agent Fakten, die in keinem Tool-Output stehen? Ersatz fuer `hallucination`; kritisch fuer Continuity und Research. | 3 |
| `world_rule_compliance` | LLM-Judge | **fast** | Verhalten sich die Naniten regelkonform (kein zentraler Server, Verbreitung ueber Koerperfluessigkeiten, keine „Metallmaennchen mit Zangen")? Prueft gegen die nummerierten Constraints der World Bible. | 3 |
| `eli5_quality` | LLM-Judge | **fast** | Sind Wissenschaftserklaerungen als Metapher im Dialog verpackt, nicht als Lexikoneintrag? | 2 |
| **`character_voice_consistency`** | LLM-Judge | **craft** (`claude-opus-5`) | Register pro Figur: David = Laienbegriffe („Nanobots", „Chips"), Sarah/Voss/Aris = praezise Terminologie („Naniten", „Assembler", „Emergenz"). Rubrik 1–5. | 1 |
| **`show_dont_tell`** | LLM-Judge | **craft** | Wird Emotion gezeigt statt benannt? | 2 |
| `scene_word_count_in_range` | deterministisch | — | Zielkorridor pro Szene (Open Question #4). | 1 |
| `pov_character_present` | deterministisch | — | Kommt die POV-Figur des Beats vor? | 2 |
| `no_placeholder_text` | deterministisch | — | Kein „[TODO]", „[Name einsetzen]", „Lorem". | 1 |
| `terminology_leak` | deterministisch | — | David benutzt nie „Naniten"; Wissenschaftler nie „Nanobots". | 1 |

Warum `world_rule_compliance` und `eli5_quality` auf **fast** liegen, obwohl sie inhaltlich wirken: beide pruefen gegen explizit niedergeschriebene Vorgaben (nummerierte Weltregeln bzw. „Metapher im Dialog statt Lexikoneintrag"). Das ist Regelabgleich, kein Stilurteil. Nur die zwei Rubriken, bei denen der Judge tatsaechlich wie ein Lektor urteilen muss, laufen auf **craft**.

```yaml
metrics_to_run:
  - task_success
  - tool_use_quality
  - trajectory_quality
  - grounding
  - character_voice_consistency
  - world_rule_compliance
  - show_dont_tell
  - eli5_quality
  - no_placeholder_text
  - terminology_leak
  - scene_word_count_in_range
  # `safety` bewusst NICHT — siehe unten

custom_metrics:
  - name: character_voice_consistency        # Stufe `craft` -> MK34_JUDGE_MODEL_CRAFT
    custom_function: |
      def evaluate(instance):
          from mk34_eval.judge import judge   # Modell kommt aus der Rubrik-Registrierung
          return judge(rubric="character_voice_consistency",
                       prompt=instance["prompt"],
                       response=instance["response"],
                       agent_data=instance.get("agent_data"))

  - name: task_success                       # Stufe `fast` -> MK34_JUDGE_MODEL_FAST
    custom_function: |
      def evaluate(instance):
          from mk34_eval.judge import judge   # identischer Call-Site, anderes Modell
          return judge(rubric="task_success",
                       prompt=instance["prompt"],
                       response=instance["response"],
                       agent_data=instance.get("agent_data"))
```

Der Call-Site ist bei beiden identisch — die Stufe steht ausschliesslich in der Rubrik-Registrierung. Damit kann eine Metrik nicht versehentlich auf dem falschen Judge landen.

Gemeinsame Helferbibliothek `tests/eval/mk34_eval/`:
- `judge.py` — ein Claude-Aufruf mit Rubrik, `output_config.format` (JSON-Schema `{score: 1-5, explanation: str}`), Retry, Kostenzaehler **pro Stufe** (fast/craft getrennt, damit die Aufteilung validierbar bleibt).
- `rubrics/` — je Metrik eine Markdown-Rubrik mit Frontmatter-Feld `tier: fast | craft`; versioniert und reviewbar.
- `trace.py` — Zugriff auf `instance["agent_data"]["turns"]` fuer die Trajektorie-/Tool-Metriken.

Vorteil dieser Bauweise, ueber die Zwangslage hinaus: die Rubriken sind versionierbarer Projekttext statt einer Blackbox, die Judge-Kosten sind steuerbar, und `character_voice_consistency` haette ohnehin als Custom-Metrik gebaut werden muessen.

**`safety` wird bewusst NICHT eingesetzt** — der unzensierte Scene Agent wuerde sie per Definition reissen. Der Punkt gilt unabhaengig vom Grading-Backend; es wird auch keine lokale Nachbildung gebaut.

### Schwellenwerte & Gates

| Phase | Gate |
|---|---|
| 1 | `task_success` ≥ 4/5 auf `basic-dataset.json`; alle deterministischen Metriken pass |
| 2 | `tool_use_quality` ≥ 4/5 und `trajectory_quality` ≥ 4/5 auf `multi-agent.json`; `character_voice_consistency` ≥ 4/5 |
| 3 | Alle Cases in `continuity.json` werden erkannt (0 False Negatives); `grounding` ≥ 4/5 |
| 4 | `uncensored-routing.json`: 100 % korrekte Route; `character_voice_consistency` auf lokalen Outputs ≥ 4/5 **nach** Editor-Durchlauf |
| 5–6 | Keine Regression gegenueber der Phase-4-Baseline (`agents-cli eval compare`) |

**Regel (aus dem Eval-Skill):** Schwellen werden nicht gesenkt, um einen Case zu bestehen. Flaky Cases sind ein Symptom von Nichtdeterminismus im Agenten — `temperature=0` fuer nicht-kreative Agenten, rubrikbasierte Metriken fuer kreative.

**Nichtdeterminismus-Hinweis:** Kreatives Schreiben ist per Design nicht reproduzierbar. Deshalb: keine Golden-Answer-Vergleiche fuer Szenentext, ausschliesslich Rubriken + deterministische Struktur-Checks.

---

## Implementierungsphasen

### Phase 1: Foundation — TASK-001 … TASK-008
Lauffaehiges Grundgeruest: scaffoldetes Projekt, Model-Router (Cloud + lokal), Kontext-Store aus `basics.md`, Manuskript-Tools, ein einzelner Scene Agent, erster gruener Eval-Lauf.
**Ergebnis:** `agents-cli run "Schreibe Kapitel 1, Szene 1"` erzeugt eine kontextbasierte Szene; `agents-cli eval run` ist gruen.

### Phase 2: Multi-Agent Core — TASK-009 … TASK-014
Plot-, Character-, Editor-Agent; Orchestrator als Coordinator; `SequentialAgent`-Pipeline + Editor-`LoopAgent`; Eval auf Tool-Trajektorie.
**Ergebnis:** Plot definiert was passiert, Character liefert figurengerechte Details, Scene schreibt, Editor poliert.

### Phase 3: Konsistenz & Continuity — TASK-015 … TASK-017
Continuity-Agent mit Retrieval, Timeline-Management, Character-State-Tracking, World-Rules-Engine.
**Ergebnis:** Keine Plot-Holes, keine Charakterbrueche, keine Technologie-Logikfehler.

### Phase 4: Lokale & unzensierte Modelle — TASK-018, TASK-019
Content-Klassifikation, automatisches Routing lokal/Cloud, manueller Override, Qualitaetssicherung lokaler Outputs durch den Opus-Editor, Streaming + Quantisierungs-/Performance-Tuning.
**Ergebnis:** Volle kreative Freiheit ohne Cloud-Zensur bei erhaltener Stilkonsistenz.

### Phase 5: Workflow & Iteration — TASK-020
Feedback-Loop, Varianten-System, Rewrite-Modes, Session-Rewind (`runner.rewind_async`), Git-Branching fuer Plot-Alternativen, Manuskript-Statistiken, duenne `mk34`-CLI (Typer) ueber den ADK-`Runner`.
**Ergebnis:** Professioneller Autoren-Workflow mit KI-Unterstuetzung statt KI-Abhaengigkeit.

### Phase 6: Export & Polish — TASK-021
Pandoc-Export (EPUB/PDF/DOCX) mit Kapitel-Metadaten, Gesamtmanuskript-Review, Style-Transfer ueber modellheterogene Passagen.
**Ergebnis:** Publikationsfertiges Manuskript.

---

## Technologie-Stack

| Komponente | Technologie |
|---|---|
| Framework | Google ADK (Python), scaffoldet via `agents-cli` 1.3.1 |
| Paket-/Env-Management | `uv` |
| Model-Routing | `google.adk.models.lite_llm.LiteLlm` |
| Cloud-Modelle | Claude Opus 5 / Sonnet 5 / Haiku 4.5 (Anthropic API via LiteLLM) |
| Lokales Modell | llama.cpp `llama-server`, `supergemma4-26b-abliterated-Q4_K_M.gguf`, OpenAI-kompatibel, verschluesselte Parallels-VM + SSH-Tunnel |
| Persistenz (Kanon/Manuskript) | JSON + Markdown, git-versioniert |
| Sessions | `DatabaseSessionService` auf SQLite (`data/sessions.db`, gitignored), ab Phase 1 |
| Retrieval | SQLite FTS5/BM25 (Stufe 1) · optional sqlite-vec + lokales Embedding-Modell (Stufe 2) |
| Eval | `agents-cli eval` mit ausschliesslich lokalen `custom_function`-Metriken; LLM-Judge via Anthropic-SDK, zweistufig (`claude-sonnet-5` / `claude-opus-5`) |
| CLI (Phase 5) | Typer |
| Export | Pandoc |
| Versionierung | Git (Branching fuer Plot-Alternativen) |

---

## Entschieden

| # | Frage | Entscheidung | Auswirkung |
|---|---|---|---|
| E1 | Eval-Grading: GCP-LLM-Judge vs. lokal | **Lokal.** Kein GCP-Projekt. Ausschliesslich `custom_metrics` mit `custom_function` (`execution: local`); LLM-Judge ist ein direkter Claude-API-Aufruf. | *Evaluation Plan* neu gefasst; managed Built-ins und `eval analyze` entfallen und werden lokal nachgebaut. Entblockt **TASK-008**. |
| E2 | Retrieval-Backend fuer Continuity | **Lokal.** Stufe 1: SQLite FTS5/BM25 ueber Szenen-Chunks. Stufe 2 (nur bei Recall-Failure): sqlite-vec + lokales Embedding-Modell, RRF-Hybrid. Kein Vertex Vector Search. | *Continuity Agent → Retrieval-Backend* ergaenzt. Entblockt **TASK-015**. |
| E3 | Session-Persistenz | **`DatabaseSessionService` mit SQLite ab dem ersten Setup**, nicht `InMemorySessionService` und nicht erst in Phase 5. | *Architecture → Session-Persistenz* ergaenzt; `MK34_SESSION_DB_URL` in *Configuration*; Acceptance Criteria in TASK-001 und TASK-013; TASK-020 verweist darauf, dass die Voraussetzung fuer `rewind_async` bereits steht. |
| E4 | Judge-Modell pro Rubrik | **Zweistufig, verbindlich ab TASK-008** (nicht erst ab einer Suite-Groesse): `claude-sonnet-5` fuer die deterministiknahen Rubriken, `claude-opus-5` nur fuer `character_voice_consistency` und `show_dont_tell`. | Zwei Variablen `MK34_JUDGE_MODEL_FAST` / `MK34_JUDGE_MODEL_CRAFT`; Judge-Spalte in den Metrik-Tabellen; `judge()` waehlt anhand der Rubrik-Registrierung, nicht am Call-Site. |

## Open Questions

1. **Scaffold-Default vs. Modellwahl.** `agents-cli scaffold create` erzeugt Agenten mit Gemini-Default; der Code-Preservation-Grundsatz sagt „Modell nie ungefragt aendern". Hier *ist* die Aenderung gewuenscht — der Umbau auf `LiteLlm(...)` in TASK-002 ist explizit beauftragt. Bestaetigen.
   *(Betrifft nur die Produktiv-Agenten. Die Eval-Judges laufen ueber den Anthropic-SDK direkt, nicht ueber ADK/LiteLLM — siehe E4.)*
2. **Buch-Datenverzeichnis.** Bleibt `books/life_link/` ausserhalb des scaffoldeten Agent-Projekts (Vorschlag: ja, Trennung Code/Content) oder wandert es unter das Agent-Verzeichnis? Betrifft alle Tool-Pfade.
3. **Observability lokal.** Reicht `agents-cli run -v` + strukturierte Logs? Cloud Trace / BigQuery Agent Analytics scheiden mit E1 faktisch aus (kein GCP) — die Minimalvariante aus TASK-022 duerfte damit gesetzt sein; bestaetigen.
4. **Wortzahl-Korridore.** Fuer `scene_word_count_in_range` fehlen Zielwerte pro Szenentyp. Vom Autor zu setzen.
5. **Hardware-Realitaet.** `docs/LOCAL_MODEL_VM_SETUP.md` rechnet mit 5–15 tok/s → 2–5 Min pro Szene. Bei Varianten-Generierung (Phase 5, `--variants 3`) sind das 6–15 Min. Akzeptabel oder braucht es einen Batch-/Nacht-Modus?
