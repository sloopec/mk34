> ⚠️ **HINWEIS: Dieses Dokument ist der urspruengliche Entwurf und wird nicht mehr gepflegt.**
>
> Die maßgebliche, gepflegte Planung liegt seit 2026-08-17 in **vier Plaenen** unter `.claude/plans/`
> (Einstieg und Gesamtuebersicht: **`.claude/plans/README.md`**):
>
> 1. `01-fundament-und-kontext/` — Scaffold (erledigt), Model-Router, Kontext-Store
> 2. `02-agenten-kern-und-kontinuitaet/` — Tools, Eval-Grundgeruest, Plot/Character/Editor, Orchestrator, Pipeline, Continuity
> 3. `03-szenen-und-lokales-llm/` — Scene Agent, lokales LLM, Content-Routing, Szenen-Evals
> 4. `04-qualitaet-workflow-und-export/` — QS lokaler Outputs, Autoren-Workflow/CLI, Export, Observability
>
> Jeder Plan enthaelt `plan.md`, `status.md` und `tasks/TASK-NNN-*.md`, inklusive Mapping auf die
> alte Task-Nummerierung des aufgeloesten Gesamtplans.
>
> Wesentliche Korrekturen gegenueber dem Text unten: Projektstruktur kommt aus
> `agents-cli scaffold` (nicht handgebautes `src/`), der Pfad `src/setup/basics.md`
> existiert nicht (real: `books/life_link/idea/basics.md`), das lokale Modell ist
> llama.cpp/`supergemma4-26b-abliterated` laut `docs/LOCAL_MODEL_VM_SETUP.md`
> (nicht Ollama/Mistral) — und die Modellstrategie ist inzwischen **Gemini-first**:
> gestartet wird mit Gemini-Modellen (ADK-nativ), Claude via LiteLLM und das lokale
> Modell (nur Scene Agent) sind konfigurierbare Alternativen.
> Die Phasenlogik und die Routing-Grundidee bleiben unveraendert.

---

# MK34 - AI Book Writing System

## Vision

Ein Multi-Agenten-System auf Basis von Google ADK, das die Funktionalitaet von Sudowrite und NovelCrafter vereint, verbessert und um modell-agnostisches Routing, unzensierte lokale Modelle und strukturiertes Manuskript-Management erweitert.

## Architektur

```
┌─────────────────────────────────────────────────────────┐
│                    CLI / Orchestrator                     │
│            (Google ADK - Agent Coordinator)               │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │ Plot     │  │ Figuren  │  │ Szenen   │  │ Lektor │  │
│  │ Agent    │  │ Agent    │  │ Agent    │  │ Agent  │  │
│  │ (Opus)   │  │ (Opus)   │  │ (lokal/  │  │ (Opus) │  │
│  │          │  │          │  │ unzens.) │  │        │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘  │
│                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │Continuity│  │ Research │  │ Style    │              │
│  │ Agent    │  │ Agent    │  │ Agent    │              │
│  │ (Sonnet) │  │ (Sonnet) │  │ (Opus)   │              │
│  └──────────┘  └──────────┘  └──────────┘              │
│                                                           │
├─────────────────────────────────────────────────────────┤
│              Shared Context Store (JSON/MD)               │
│  characters.json | plot.md | world.md | manuscript/*.md  │
├─────────────────────────────────────────────────────────┤
│              Model Router (LiteLLM / Direct APIs)         │
│  Claude Opus | Claude Sonnet | Ollama (local) | Gemini   │
└─────────────────────────────────────────────────────────┘
```

## Projekt-Struktur

```
mk34/
├── docs/
│   └── PLAN.md
├── src/
│   ├── setup/                    # Bereits vorhanden (Buch-Grundlagen)
│   ├── agents/                   # Agent-Definitionen
│   │   ├── __init__.py
│   │   ├── orchestrator.py       # Koordinator / Root-Agent
│   │   ├── plot_agent.py         # Plot-Entwicklung & Akt-Struktur
│   │   ├── character_agent.py    # Figurenkonsistenz & Entwicklung
│   │   ├── scene_agent.py        # Szenen schreiben
│   │   ├── editor_agent.py       # Lektorat & Stilkontrolle
│   │   ├── continuity_agent.py   # Fakten-Check gegen Manuskript
│   │   ├── research_agent.py     # Wissenschaftliche Recherche
│   │   └── style_agent.py        # Sprachstil & Ton
│   ├── tools/                    # Custom Tools fuer Agents
│   │   ├── __init__.py
│   │   ├── manuscript.py         # Lesen/Schreiben von Kapiteln
│   │   ├── context_loader.py     # Kontext-Injektion (Figuren, Plot)
│   │   ├── consistency.py        # Konsistenz-Pruefungen
│   │   └── export.py             # Export (Markdown, EPUB, PDF)
│   ├── models/                   # Model-Routing & Konfiguration
│   │   ├── __init__.py
│   │   ├── router.py             # Model-Auswahl pro Task
│   │   └── config.py             # API-Keys, Endpoints, Ollama-Config
│   ├── store/                    # Persistenter Kontext
│   │   ├── characters.json       # Figuren-Datenbank
│   │   ├── plot_outline.json     # Plot-Struktur (Akte, Szenen, Beats)
│   │   ├── world_bible.md        # Weltenbau, Regeln, Technologie
│   │   ├── timeline.json         # Chronologie der Ereignisse
│   │   └── style_guide.md        # Stilregeln, Sprachregister
│   └── manuscript/               # Das eigentliche Manuskript
│       ├── kapitel_01.md
│       ├── kapitel_02.md
│       └── ...
├── tests/
├── pyproject.toml
└── README.md
```

---

## Implementierungsphasen

---

### Phase 1: Foundation

**Ziel:** Lauffaehiges Grundgeruest mit einem einzelnen Agenten, der Text generieren kann.

**Tasks:**

1. Python-Projekt aufsetzen (`pyproject.toml`, Dependencies: `google-adk`, `litellm`, `anthropic`)
2. Model-Router implementieren
   - Claude Opus/Sonnet via Anthropic API
   - Lokale Modelle via Ollama/LiteLLM
   - Konfiguration ueber `config.py` (API-Keys, Endpoints)
3. Shared Context Store anlegen
   - `characters.json` mit bestehendem Figuren-Setup befuellen
   - `plot_outline.json` aus `src/setup/basics.md` extrahieren
   - `world_bible.md` (Naniten-Technologie, Regeln)
4. Erster Agent: **Scene Agent** (einfachster Use-Case)
   - System-Prompt: kreatives Schreiben, keine Code-Bias
   - Tool: `write_scene(chapter, scene_number, context)` -> Markdown
   - Tool: `read_manuscript(chapter)` -> bisheriger Text
5. CLI-Entry-Point: `python -m mk34 write-scene --chapter 1 --scene 1`

**Ergebnis:** Man kann eine Szene generieren lassen, die auf dem Kontext (Figuren, Plot) basiert.

**Abhaengigkeiten:** API-Key fuer Claude, optional Ollama installiert.

---

### Phase 2: Multi-Agent Core

**Ziel:** Spezialisierte Agenten mit Handoff-Logik.

**Tasks:**

1. **Plot Agent**
   - Input: Grobe Idee oder Akt-Nummer
   - Output: Detaillierte Szenen-Beats, Wendepunkte, Spannungsbogen
   - Modell: Opus (braucht Gesamtueberblick)
   - Tools: `read_plot_outline()`, `update_plot_outline()`, `read_all_chapters_summary()`

2. **Character Agent**
   - Input: Figurenname + Kontext der Szene
   - Output: Charakter-konsistente Dialog-Vorschlaege, Reaktionen, innere Konflikte
   - Tools: `get_character(name)`, `update_character(name, development)`, `get_character_arc(name)`
   - Validierung: Prueft ob Verhalten zur bisherigen Entwicklung passt

3. **Editor Agent (Lektor)**
   - Input: Roher Szenentext
   - Output: Ueberarbeitete Version mit Anmerkungen
   - Prueft: Stilkonsistenz, Sprachregister (David=Laie, Sarah=wissenschaftlich), Pacing, Show-don't-tell

4. **Orchestrator** (ADK Coordinator Pattern)
   - Nimmt High-Level-Befehle entgegen
   - Routet an passenden Sub-Agent
   - Managed Kontext-Uebergaben zwischen Agenten

5. CLI erweitern:
   - `mk34 plot develop --act 2`
   - `mk34 character arc --name "David"`
   - `mk34 write --chapter 3 --scene 2`
   - `mk34 edit --chapter 3`

**Ergebnis:** Spezialisierte Agenten arbeiten zusammen. Plot-Agent definiert was passiert, Character-Agent liefert figurengerechte Details, Scene-Agent schreibt, Editor-Agent poliert.

---

### Phase 3: Konsistenz & Continuity

**Ziel:** Das System vergisst nichts und widerspricht sich nicht.

**Tasks:**

1. **Continuity Agent**
   - Liest gesamtes bisheriges Manuskript (Sonnet fuer Speed)
   - Prueft neue Szenen gegen: Timeline, Ortswechsel, Figurenpositionen, etablierte Fakten
   - Output: Liste von Widerspruechen mit Zeilenreferenz
   - Tool: `check_consistency(new_text, context_chapters[])`

2. **Timeline-Management**
   - Automatische Extraktion von Zeitangaben aus geschriebenen Szenen
   - Chronologische Validierung
   - Warnung bei Zeitspruengen oder Parallelitaets-Konflikten

3. **Character State Tracking**
   - Pro Kapitel: Wo ist die Figur? Was weiss sie? Emotionaler Zustand?
   - Automatisches Update nach jeder geschriebenen Szene
   - Warnung wenn Figur Wissen verwendet, das sie noch nicht haben kann

4. **World-Rules Engine**
   - Naniten-Regeln aus `world_bible.md` als harte Constraints
   - Agent kann pruefen: "Ist dieses Verhalten der Naniten physikalisch/logisch konsistent?"

**Ergebnis:** Keine Plot-Holes, keine Charakterbrueche, keine Logikfehler in der Technologie.

---

### Phase 4: Lokale & Unzensierte Modelle

**Ziel:** Volle kreative Freiheit fuer Szenen die Cloud-Modelle ablehnen wuerden.

**Tasks:**

1. **Ollama-Integration vertiefen**
   - Modell-Empfehlungen fuer kreatives Schreiben (z.B. Mistral-Large, Llama 3 70B, oder spezialisierte Fine-Tunes)
   - Automatisches Model-Routing: Szenen mit Gewalt/Erotik/Kontroversem -> lokales Modell
   - Fallback-Logik: Wenn lokales Modell Qualitaet unter Schwelle -> Warnung

2. **Content-Klassifikation**
   - Vor dem Schreiben: Szene analysieren (Plot-Beat, involvierte Figuren, erwarteter Inhalt)
   - Automatische Entscheidung: Cloud oder Lokal?
   - Manueller Override per CLI-Flag: `--model local` oder `--model opus`

3. **Qualitaetssicherung fuer lokale Outputs**
   - Editor-Agent (auf Opus) reviewt auch lokal generierte Szenen
   - Stilkonsistenz sicherstellen trotz unterschiedlicher Modelle

4. **Performance-Optimierung**
   - Quantisierte Modelle fuer schwaecher Hardware (Q4, Q5)
   - Streaming-Output fuer lange Szenen
   - Caching von Kontext-Embeddings

**Ergebnis:** Komplette kreative Freiheit ohne Cloud-Zensur, bei gleichzeitiger Qualitaetskontrolle durch Opus-Review.

---

### Phase 5: Workflow & Iteration

**Ziel:** Effizientes iteratives Arbeiten am Manuskript.

**Tasks:**

1. **Feedback-Loop**
   - `mk34 feedback --chapter 3 "Dialog klingt steif, mehr Umgangssprache"`
   - Agent ueberarbeitet gezielt den genannten Aspekt
   - Diff-Ansicht: Alt vs. Neu

2. **Varianten-System**
   - `mk34 write --chapter 3 --scene 2 --variants 3`
   - Generiert 3 verschiedene Versionen derselben Szene
   - Vergleichsansicht mit Staerken/Schwaechen-Analyse

3. **Rewrite-Modes**
   - `mk34 rewrite --chapter 3 --mode tighter` (kuerzen)
   - `mk34 rewrite --chapter 3 --mode expand` (ausbauen)
   - `mk34 rewrite --chapter 3 --mode pov-switch --character Sarah` (Perspektivwechsel)

4. **Session-Management (ADK Rewind)**
   - Aenderungen rueckgaengig machen
   - Branching: Alternative Plot-Straenge ausprobieren (git-basiert)
   - Snapshots vor grossen Aenderungen

5. **Manuskript-Statistiken**
   - Wortanzahl pro Kapitel/Gesamt
   - Figuren-Auftritte pro Kapitel
   - Spannungskurve (Plot-Agent bewertet Pacing)
   - Lesezeit-Schaetzung

**Ergebnis:** Professioneller Autoren-Workflow mit KI-Unterstuetzung statt KI-Abhaengigkeit.

---

### Phase 6: Export & Polish

**Ziel:** Vom Manuskript zum fertigen Buch.

**Tasks:**

1. **Export-Formate**
   - Markdown -> EPUB (via Pandoc)
   - Markdown -> PDF (via LaTeX oder Pandoc)
   - Markdown -> Word (.docx) fuer Verlage
   - Kapitel-Metadaten (Titel, POV-Character, Zeitpunkt)

2. **Finales Lektorat**
   - Gesamtmanuskript-Review durch Opus
   - Pruefung auf: Redundanzen, vergessene Subplot-Straenge, Pacing-Probleme
   - Vorschlaege fuer Kapitelreihenfolge-Aenderungen

3. **Style-Transfer**
   - Gesamtes Manuskript auf einheitlichen Stil pruefen
   - Szenen die von verschiedenen Modellen stammen angleichen
   - Sprachregister pro Figur final validieren

**Ergebnis:** Publikationsfertiges Manuskript in gaengigen Formaten.

---

## Model-Routing Matrix

| Agent | Primaeres Modell | Grund |
|-------|-----------------|-------|
| Plot Agent | Claude Opus | Braucht Gesamtueberblick, komplexes Reasoning |
| Character Agent | Claude Opus | Psychologische Tiefe, Konsistenz |
| Scene Agent | Lokal (Mistral/Llama) oder Opus | Kreative Freiheit vs. Qualitaet |
| Editor Agent | Claude Opus | Sprachgefuehl, Stilkritik |
| Continuity Agent | Claude Sonnet | Schnell, faktenbasiert, braucht kein kreatives Reasoning |
| Research Agent | Claude Sonnet + Web | Fakten-Check, wissenschaftliche Grundlagen |
| Style Agent | Claude Opus | Feinschliff, literarische Qualitaet |
| Orchestrator | Claude Sonnet | Routing-Entscheidungen, kein kreatives Output |

---

## Technologie-Stack

| Komponente | Technologie |
|-----------|-------------|
| Framework | Google ADK (Python) |
| Model-Routing | LiteLLM + direkte APIs |
| Cloud-Modelle | Claude Opus, Claude Sonnet, optional Gemini |
| Lokale Modelle | Ollama (Mistral, Llama 3, Fine-Tunes) |
| Persistenz | JSON + Markdown (git-versioniert) |
| CLI | Python (Click oder Typer) |
| Export | Pandoc |
| Versionierung | Git (Branching fuer Plot-Alternativen) |

---

## Naechster Schritt

Phase 1 beginnen: Projekt-Setup, Model-Router, erster Scene-Agent.
