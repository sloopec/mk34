# Plan 1: Fundament und Kontext

> Teil 1 von 4 des mk34-Book-Writing-Systems. Gesamtübersicht, Entscheidungen E1–E6 und die vollständige Model-Routing-Matrix: [`../README.md`](../README.md).
> Stand: 2026-08-17 · hervorgegangen aus `mk34-book-writing-system/` (aufgelöst)

## Task-Mapping (alt → neu)

| Alt (Gesamtplan) | Neu | Status |
|---|---|---|
| TASK-001 Projekt scaffolden | TASK-001 (unverändert, inkl. `walkthroughs/` und `feature_summary/`) | ✅ erledigt |
| TASK-002 Model-Router (Claude via LiteLLM + lokales Modell) | TASK-002 — **umgebaut auf Gemini-first (E6)**; der lokale-LLM-Anteil ist herausgetrennt nach `03-szenen-und-lokales-llm/TASK-001` | ✅ erledigt |
| TASK-003 Kontext-Store | TASK-003 (unverändert) | ✅ erledigt |

---

## Ziele

- Lauffähiges, scaffoldetes ADK-Projekt (`mk34-book-agent/`) mit persistenten Sessions — **erledigt**.
- Zentraler Model-Router `model_for(role)` mit **Gemini als Startprovider** (E6): ADK-native Modell-Strings, kein LiteLLM-Umweg für Gemini. Claude und das lokale Modell sind als konfigurierbare Alternativen im Design angelegt (Umschaltung pro Agent per `.env`, ohne Code-Änderung), werden hier aber nicht angebunden.
- Strukturierter, git-versionierter Kontext-Store (`books/life_link/store/`) aus `basics.md`.
- Nachgeholter Live-Smoke-Test aus TASK-001 — jetzt mit Gemini möglich, da `GEMINI_API_KEY` in der `.env` des Agent-Projekts liegt.

## Nicht-Ziele

- Keine Anbindung des lokalen LLM (→ Plan 3/TASK-001) und keine Claude-Anbindung im Erstausbau — nur die Router-Schnittstelle dafür.
- Keine Agenten über den Scaffold-Default hinaus (→ Plan 2/3).
- Kein Deployment, kein CI/CD, kein GCP-Projekt (E1).

## Architekturübersicht

Der Router ist die einzige Stelle, die Provider kennt. Rollen → Modelle wird zweistufig aufgelöst:

```
model_for(role: str) -> str | BaseLlm
  1. Rolle → Tier            (plot/character/scene/editor/style → heavy;
                              orchestrator/continuity/research → fast; classifier → lite)
  2. Tier  → Modell-String   (aus .env: MK34_MODEL_HEAVY | _FAST | _LITE | _SCENE)
  3. Provider-Erkennung am String:
     - "gemini-*"      → String direkt zurückgeben (ADK-nativ)
     - "anthropic/*"   → LiteLlm(model=...)                     [vorgesehen, später]
     - "local"         → LiteLlm("openai/supergemma4", api_base=...)  [Plan 3]
```

Damit ist E6 („zunächst nur Gemini") eine reine Konfigurationsfrage und die spätere Umschaltung einzelner Agenten auf Claude/lokal eine `.env`-Zeile.

Die `.env` des Agent-Projekts wird **nicht gelesen oder geöffnet** (strikte Regel in `mk34-book-agent/CLAUDE.md`); dass `GEMINI_API_KEY` gesetzt ist, gilt als gegeben.

## Komponenten-Verantwortlichkeiten

### `app/models/router.py` (TASK-002)
- `model_for(role)` wie oben; keine Modell-Strings ausserhalb des Routers/der Settings.
- Aktualisiert den Scaffold-Default `gemini-3.6-flash` in `app/agent.py` auf die Zielmodelle — im Rahmen von E6 explizit beauftragt (Code-Preservation-Ausnahme).
- Die lokale Provider-Erkennung (`"local"`) wirft in diesem Plan noch `NotImplementedError` mit Verweis auf Plan 3 — die Schnittstelle existiert, die Anbindung nicht.

### `books/life_link/store/` (TASK-003)
- `characters.json`, `plot_outline.json`, `world_bible.md`, `timeline.json`, `style_guide.md` — abgeleitet aus `books/life_link/idea/basics.md`, vom Autor geprüft und eingecheckt. Ab dann ist der Store die Wahrheit, nicht `basics.md`.
- Liegt gemäss E5 im Repo-Root, ausserhalb von `mk34-book-agent/`.

## Ablaufsequenz

1. TASK-002: Router implementieren, Root-Agent auf `model_for("orchestrator")` umstellen, Live-Smoke-Test mit Gemini nachholen (`agents-cli playground`, `agents-cli run --session-id` über zwei Prozesse).
2. TASK-003 (parallel möglich): Store aus `basics.md` extrahieren, Autor-Review, Commit.
3. Fehlerpfad: fehlender/ungültiger `GEMINI_API_KEY` → klare Fehlermeldung des Routers beim Start, kein stiller Fallback auf ein anderes Modell.

## Konfiguration

Ziel-Variablen (Dokumentation — die Anpassung von `.env.example` ist Implementierung und Teil von TASK-002; die `.env` selbst wird nicht angefasst):

| Variable | Startwert (Gemini, E6) | Später (Claude/lokal) |
|---|---|---|
| `GEMINI_API_KEY` | vorhanden (lt. User) | — |
| `MK34_MODEL_HEAVY` | `gemini-3.1-pro-preview` | `anthropic/claude-opus-5` |
| `MK34_MODEL_FAST` | `gemini-3.7-flash` | `anthropic/claude-sonnet-5` |
| `MK34_MODEL_LITE` | `gemini-3.5-flash-lite` | `anthropic/claude-haiku-4-5` |
| `MK34_MODEL_SCENE` | `gemini-3.1-pro-preview` | `local` (→ Plan 3) |
| `MK34_JUDGE_MODEL_FAST` | `gemini-3.7-flash` | `claude-sonnet-5` |
| `MK34_JUDGE_MODEL_CRAFT` | `gemini-3.1-pro-preview` | `claude-opus-5` |
| `MK34_BOOK_SLUG` / `MK34_BOOK_ROOT` | `life_link` / `books/life_link` (relativ zum Repo-Root, E5) | — |
| `MK34_SESSION_DB_URL` | `sqlite+aiosqlite:///./data/sessions.db` (E3, bereits umgesetzt) | — |
| `ANTHROPIC_API_KEY` | leer/ungenutzt | nötig bei Claude-Umschaltung |
| `MK34_LOCAL_*` | dokumentiert, ungenutzt | → Plan 3 |
| `GOOGLE_CLOUD_*` / `GOOGLE_GENAI_USE_VERTEXAI` | leer/ungenutzt (kein GCP, E1; Gemini läuft über den AI-Studio-Pfad mit `GEMINI_API_KEY`) | — |

Die alten Variablen `MK34_CLOUD_HEAVY_MODEL`/`MK34_CLOUD_FAST_MODEL` sind durch das provider-neutrale Schema `MK34_MODEL_*` ersetzt.

## Tooling

| Zweck | Kommando |
|---|---|
| Scaffolding | erledigt (`agents-cli scaffold create mk34-book-agent --agent adk --prototype --agent-guidance-filename CLAUDE.md`) |
| Lokaler Run | `agents-cli playground` · `agents-cli run "..." [-v] [--session-id <id>]` |
| Lint | `agents-cli lint` |
| Unit-Tests | `uv run pytest` (Router-Mapping, Provider-Erkennung) |
| Eval | noch nicht in diesem Plan (Grundgerüst → Plan 2/TASK-003) |

## Evaluationsplan

Dieser Plan hat noch keine Eval-Suite (die entsteht in Plan 2/TASK-003). Gate für Plan 1 ist stattdessen:
- `agents-cli lint` grün, `uv run pytest` grün (Router-Mapping, Provider-Erkennung, Settings).
- Live-Smoke-Test: `agents-cli playground` antwortet über Gemini; Session-Persistenz über Prozess-Neustart via `agents-cli run --session-id` nachgewiesen (nachgeholtes Kriterium aus TASK-001).
- Kontext-Store: valide Dateien, Autor-Review dokumentiert.

## Entschieden

- **E7 (2026-08-17, vormals Offene Frage #1):** `gemini-3.1-pro-preview` ist für alle Heavy-Rollen freigegeben, trotz Preview-Status. Bei Instabilität ist die Umschaltung auf `gemini-3.7-flash` eine `.env`-Zeile. Die Startwerte in *Konfiguration* und TASK-002 gelten damit verbindlich. (Gesamtliste E1–E10: [`../README.md`](../README.md).)

## Offene Fragen

1. **Wortzahl-Korridore** für `scene_word_count_in_range` (wirkt erst in Plan 3, vom Autor zu setzen — hier geführt, weil der Autor sie beim Store-Review in TASK-003 gleich mitliefern könnte).
