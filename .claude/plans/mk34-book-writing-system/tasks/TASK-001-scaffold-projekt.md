# TASK-001: Projekt mit agents-cli scaffolden (Prototype)
Status: ⏳ pending
Parallel: no

## Description
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
- Danach entscheiden (Open Question #3), ob das scaffoldete Projekt ins Repo-Root gemergt wird oder als Unterverzeichnis bleibt; `books/` bleibt in jedem Fall ausserhalb von `app/`.
- `App(name=...)` in `app/__init__.py` muss dem Agent-Verzeichnisnamen entsprechen (`app`), sonst „Session not found" im Eval.

**Entscheidung E3: persistente Sessions ab dem ersten Setup.** Der Scaffold liefert `InMemorySessionService`. Direkt beim Setup auf SQLite umstellen — nicht erst in Phase 5, sonst gehen alle bis dahin entstandenen Sessions bei der Migration verloren:

```python
from google.adk.sessions import DatabaseSessionService
session_service = DatabaseSessionService(db_url=settings.session_db_url)
# sqlite:///./data/sessions.db
```

Das Session-Setup lebt in `app/app_utils/services.py` (vom Scaffold erzeugt). `data/` und `data/sessions.db` gehoeren in `.gitignore` — nur Manuskript und Kanon gehoeren ins Repo, nicht die Gespraechshistorie.

## Acceptance Criteria
- [ ] `agents-cli info` meldet aus dem Projektverzeichnis ein gefundenes Agent-Projekt
- [ ] `agents-cli-manifest.yaml`, `app/agent.py`, `app/fast_api_app.py`, `tests/eval/` existieren
- [ ] `uv sync` laeuft fehlerfrei durch
- [ ] `agents-cli playground` startet und der Default-Agent antwortet
- [ ] `.env` ist gitignored; `.env.example` mit den Variablen aus dem Plan-Abschnitt *Configuration* ist eingecheckt
- [ ] **`DatabaseSessionService` mit `sqlite:///./data/sessions.db` ist konfiguriert; `InMemorySessionService` kommt im Code nicht mehr vor**
- [ ] **`data/sessions.db` wird beim ersten Lauf angelegt und eine Session ueberlebt einen Prozess-Neustart** (nachweisbar via `agents-cli run --session-id <id>` in zwei getrennten Aufrufen)
- [ ] `data/` steht in `.gitignore`
- [ ] Ablage-Entscheidung (Open Question #2) ist in `plan.md` als beantwortet vermerkt

## Affected Files
- `agents-cli-manifest.yaml` (generiert)
- `app/` (generiert)
- `app/app_utils/services.py` (Session-Service auf SQLite umstellen)
- `tests/eval/` (generiert)
- `pyproject.toml`, `Makefile`, `Dockerfile` (generiert)
- `.env.example`, `.gitignore`
