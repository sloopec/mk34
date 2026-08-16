# TASK-001: Projekt mit agents-cli scaffolden (Prototype)
Status: ✅ erledigt
Parallel: nein

## Beschreibung
Das Repo enthaelt bisher nur `docs/`, `books/`, `README.md`. Statt einer handgebauten `src/`-Struktur wird das ADK-Projekt mit `agents-cli` erzeugt — sonst fehlen Eval-Boilerplate, `agents-cli-manifest.yaml`, `fast_api_app.py`, Dockerfile und die Projektkonventionen, die alle weiteren `agents-cli`-Kommandos voraussetzen.

Prototype-First: kein Deployment-Target, kein CI/CD (Non-Goal des Plans).

```bash
agents-cli info                      # Version/Installation pruefen
agents-cli scaffold create mk34-book-agent \
  --agent adk \
  --prototype \
  --agent-guidance-filename CLAUDE.md
```

Wichtig:
- Verzeichnis **nicht** vorher mit `mkdir` anlegen — sonst faellt die CLI in den Enhance-Modus.
- Projektname ≤ 26 Zeichen, lowercase, nur Buchstaben/Ziffern/Bindestriche.
- Danach entscheiden (Offene Frage #3), ob das scaffoldete Projekt ins Repo-Root gemergt wird oder als Unterverzeichnis bleibt; `books/` bleibt in jedem Fall ausserhalb von `app/`.
- `App(name=...)` in `app/__init__.py` muss dem Agent-Verzeichnisnamen entsprechen (`app`), sonst „Session not found" im Eval.

**Entscheidung E3: persistente Sessions ab dem ersten Setup.** Der Scaffold liefert `InMemorySessionService`. Direkt beim Setup auf SQLite umstellen — nicht erst in Phase 5, sonst gehen alle bis dahin entstandenen Sessions bei der Migration verloren:

```python
from google.adk.sessions import DatabaseSessionService
session_service = DatabaseSessionService(db_url=settings.session_db_url)
# sqlite:///./data/sessions.db
```

Das Session-Setup lebt in `app/app_utils/services.py` (vom Scaffold erzeugt). `data/` und `data/sessions.db` gehoeren in `.gitignore` — nur Manuskript und Kanon gehoeren ins Repo, nicht die Gespraechshistorie.

## Akzeptanzkriterien
- [x] `agents-cli info` meldet aus dem Projektverzeichnis ein gefundenes Agent-Projekt
- [x] `agents-cli-manifest.yaml`, `app/agent.py`, `app/fast_api_app.py`, `tests/eval/` existieren
- [x] `uv sync` laeuft fehlerfrei durch (via `agents-cli install`)
- [~] `agents-cli playground` startet und der Default-Agent antwortet — **verschoben auf TASK-002** (siehe `walkthroughs/TASK-001-scaffold-projekt.md`, Abschnitt *Verifikation*: kein `ANTHROPIC_API_KEY`/`GEMINI_API_KEY` in dieser Umgebung verfuegbar; User-Entscheidung, den Live-CLI-Smoke-Test nach TASK-002 nachzuholen, sobald der Root-Agent auf Claude geroutet ist. Acceptance Criterion in TASK-002 ergaenzt.)
- [x] `.env` ist gitignored; `.env.example` mit den Variablen aus dem Plan-Abschnitt *Configuration* ist eingecheckt
- [x] **`DatabaseSessionService` mit SQLite ist konfiguriert; `InMemorySessionService` kommt im Code nicht mehr vor** (URL-Schema von `sqlite:///` auf `sqlite+aiosqlite:///` angepasst — ADK 2.7 `DatabaseSessionService` verlangt einen async SQLAlchemy-Treiber; siehe Walkthrough *Design decisions*)
- [x] **`data/sessions.db` wird beim ersten Lauf angelegt und eine Session ueberlebt einen Prozess-Neustart** — verifiziert per direktem Python-Test gegen `get_session_service()` (zwei getrennte `uv run python`-Prozesse, gleiche `session_id`, Session in Prozess 2 lesbar); der CLI-basierte Nachweis (`agents-cli run --session-id <id>`) folgt in TASK-002 zusammen mit dem Live-Smoke-Test
- [x] `data/` steht in `.gitignore`
- [x] Ablage-Entscheidung (Offene Frage #2) ist in `plan.md` als beantwortet vermerkt (jetzt Entscheidung **E5**)

## Betroffene Dateien
- `agents-cli-manifest.yaml` (generiert)
- `app/` (generiert)
- `app/app_utils/services.py` (Session-Service auf SQLite umstellen)
- `tests/eval/` (generiert)
- `pyproject.toml`, `Makefile`, `Dockerfile` (generiert)
- `.env.example`, `.gitignore`
