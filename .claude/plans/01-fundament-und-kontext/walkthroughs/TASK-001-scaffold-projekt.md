# Durchführungsbericht: TASK-001 — Projekt mit agents-cli scaffolden (Prototype)
Abgeschlossen: 2026-08-16T00:00:00Z

## Was wurde umgesetzt

Das ADK-Projekt wurde ueber `agents-cli scaffold create` erzeugt (kein manuelles `mkdir`), als
eigenstaendiges Unterverzeichnis `mk34-book-agent/` im Repo-Root, getrennt von `books/` und
`docs/`:

```bash
agents-cli scaffold create mk34-book-agent \
  --agent adk \
  --prototype \
  --agent-guidance-filename CLAUDE.md
```

Prototype-Modus (`deployment_target=none`, `cicd_runner=skip`), wie im Plan als Non-Goal
festgelegt. Danach `agents-cli install` (uv sync) ausgefuehrt.

Anschliessend wurde die Session-Persistenz gemaess Entscheidung E3 umgestellt: der generierte
`app/app_utils/services.py`-Code faellt bisher standardmaessig auf `InMemorySessionService`
zurueck; jetzt liefert `get_session_service()` immer eine `DatabaseSessionService`-Instanz gegen
eine lokale SQLite-Datei, ausser wenn `SESSION_SERVICE_URI` oder
`GOOGLE_CLOUD_AGENT_ENGINE_ID` gesetzt sind (Cloud-/Deployment-Pfade bleiben unveraendert
erhalten).

`.env.example` wurde um alle im Plan-Abschnitt *Configuration* gelisteten `MK34_*`-Variablen
ergaenzt (Modell-Router-, Buch-, Judge-, Retrieval- und Session-Variablen) — auch die, die erst
in spaeteren Tasks (TASK-002 ff.) verdrahtet werden, wie von den Acceptance Criteria gefordert.
`data/` wurde in `.gitignore` ergaenzt.

`plan.md` wurde um Entscheidung **E5** ergaenzt (Buch-Datenverzeichnis bleibt im Repo-Root,
ausserhalb des Agent-Projekts) und aus den *Offene Fragen* entfernt; `status.md` wurde
entsprechend angepasst.

## Geänderte Dateien

- `mk34-book-agent/` (neu, generiert via `agents-cli scaffold create`) — vollstaendiges
  Scaffold: `agents-cli-manifest.yaml`, `app/agent.py`, `app/__init__.py`, `app/fast_api_app.py`,
  `app/app_utils/{a2a,typing}.py`, `Dockerfile`, `pyproject.toml`, `tests/eval/`,
  `tests/integration/`, `tests/unit/`, `.gitignore`, `.env`, `.env.example`, `README.md`,
  `CLAUDE.md`
- `mk34-book-agent/app/app_utils/services.py` — `get_session_service()` liefert jetzt immer
  `DatabaseSessionService` (Default: `sqlite+aiosqlite:///./data/sessions.db`, ueberschreibbar
  via `MK34_SESSION_DB_URL`) statt `InMemorySessionService`; neue Hilfsfunktion
  `_ensure_sqlite_parent_dir()` legt `data/` beim ersten Zugriff an, da SQLite das nicht
  selbststaendig tut
- `mk34-book-agent/pyproject.toml` — `google-adk[gcp,otel-gcp,db]` (Extra `db` fuer
  `sqlalchemy`) und `greenlet` als explizite Abhaengigkeit ergaenzt (beide fuer
  `DatabaseSessionService` mit async-SQLite noetig, siehe *Design-Entscheidungen*)
- `mk34-book-agent/.env.example` — alle `MK34_*`-Variablen aus *Configuration* ergaenzt,
  gruppiert und kommentiert; GCP-Zeilen als "vom Scaffold, ungenutzt" markiert
- `mk34-book-agent/.gitignore` — `data/` ergaenzt (mk34-spezifisch: persistente
  ADK-Sessions, nicht git-versioniert)
- `.claude/plans/mk34-book-writing-system/plan.md` — Entscheidung E5 (Buch-Datenverzeichnis)
  in *Entschieden* aufgenommen, aus *Offene Fragen* entfernt, verbleibende Fragen
  umnummeriert (#2–#5 → #1–#4)
- `.claude/plans/mk34-book-writing-system/status.md` — TASK-001 auf `✅ done`, Blocker-Sektion
  um E5 ergaenzt, Hinweis auf Offene Frage #2 aktualisiert
- `.claude/plans/mk34-book-writing-system/tasks/TASK-001-scaffold-projekt.md` — Status,
  Acceptance Criteria abgehakt/kommentiert
- `.claude/plans/mk34-book-writing-system/tasks/TASK-002-model-router.md` — Acceptance
  Criterion ergaenzt: nachgeholter Live-Smoke-Test aus TASK-001

## Design-Entscheidungen

**`sqlite+aiosqlite://` statt `sqlite://` (Abweichung von der woertlichen Formulierung in
plan.md/TASK-001).** Die installierte ADK-Version (2.7.0) verlangt fuer
`DatabaseSessionService` zwingend einen async-SQLAlchemy-Treiber
(`sqlalchemy.exc.InvalidRequestError: The asyncio extension requires an async driver ...` beim
Versuch mit dem synchronen `sqlite:///`-Schema/`pysqlite`). `sqlite+aiosqlite:///./data/sessions.db`
zeigt auf dieselbe Datei, denselben Pfad, dieselbe `.gitignore`-Regel — nur der Treiber ist ein
anderer. Zusaetzlich fehlten zur Laufzeit `sqlalchemy` (Extra `db` nachgezogen) und `greenlet`
(SQLAlchemys asyncio-Bridge braucht es auch mit async-Treiber fuer bestimmte Codepfade wie
Tabellen-Introspektion). Beide als Abhaengigkeit ergaenzt. Das ist eine Implementierungsdetail-
Korrektur, keine Architekturaenderung — die Entscheidung E3 (persistente SQLite-Sessions ab
Tag 1) bleibt unveraendert; nur der Verbindungsstring musste an die tatsaechliche API angepasst
werden.

**Directory-Auto-Create fuer den SQLite-Pfad.** `data/` ist gitignored und existiert auf einem
frischen Checkout nicht. SQLite (weder `pysqlite` noch `aiosqlite`) legt das Elternverzeichnis
einer DB-Datei nicht selbst an ("unable to open database file"). `_ensure_sqlite_parent_dir()`
parst die URL mit `sqlalchemy.engine.make_url` und ruft `Path.mkdir(parents=True,
exist_ok=True)`, bevor die Engine erzeugt wird — nur fuer file-basierte SQLite-URLs, nicht fuer
`:memory:` oder andere Backends.

**`MK34_SESSION_DB_URL` als Override-Variable eingefuehrt**, obwohl TASK-002 (Model-Router,
Pydantic-Settings) die Variable formal erst zentral verdrahtet. Das ist konsistent mit der
Plan-Konfigurationstabelle (Zeile `MK34_SESSION_DB_URL`) und macht `get_session_service()`
bereits jetzt ueberschreibbar, ohne auf TASK-002 zu warten.

**Live-CLI-Smoke-Test auf TASK-002 verschoben (User-Entscheidung).** Diese Umgebung hat weder
`GEMINI_API_KEY` noch GCP-ADC-Credentials noch `ANTHROPIC_API_KEY` gesetzt. Der scaffoldete
Default-Agent (`app/agent.py`, Modell `gemini-3.6-flash`) kann daher weder ueber
`agents-cli playground` noch ueber `agents-cli run` tatsaechlich antworten — ein Live-Aufruf
wuerde nur an fehlenden Credentials scheitern, nicht am Scaffold oder an der Session-Logik. Der
Nutzer hat entschieden, den Live-Smoke-Test (Playground antwortet; Session ueberlebt
Prozess-Neustart via zwei `agents-cli run --session-id <id>`-Aufrufen) auf TASK-002 zu
verschieben, sobald der Root-Agent dort auf `LiteLlm(anthropic/...)` umgestellt und
`ANTHROPIC_API_KEY` gesetzt ist. Ein entsprechendes Acceptance Criterion wurde in
`tasks/TASK-002-model-router.md` ergaenzt. Um die Session-Persistenz trotzdem fuer TASK-001
nachzuweisen, wurde sie **direkt gegen den Python-Code** verifiziert (siehe *Verification
steps*) — das deckt die Session-Service-Logik vollstaendig ab, nicht aber den End-to-End-Pfad
ueber die CLI/den Serving-Layer.

## Verifikationsschritte

1. `~/.local/bin/agents-cli info` (aus `mk34-book-agent/`) — meldet Version 1.3.1 und ein
   gefundenes Agent-Projekt.
2. `~/.local/bin/agents-cli scaffold create mk34-book-agent --agent adk --prototype
   --agent-guidance-filename CLAUDE.md` — Scaffold erfolgreich erzeugt (GCP-Auth-Warnung
   erwartet/unkritisch, siehe Non-Goals).
3. `~/.local/bin/agents-cli install` — `uv sync` laeuft fehlerfrei durch (auch nach Hinzufuegen
   von `db`-Extra und `greenlet`).
4. `~/.local/bin/agents-cli lint` — `ruff check`, `ruff format --check`, `codespell`, `ty check`
   alle gruen.
5. Direkter Python-Test der Session-Persistenz (ersetzt den CLI-Live-Smoke-Test, der mangels
   Credentials nicht moeglich war):
   ```bash
   uv run python -c "
   from app.app_utils.services import get_session_service
   import asyncio
   svc = get_session_service()
   async def main():
       s = await svc.create_session(app_name='app', user_id='u1', session_id='fixed-session-001')
       print('process 1 created session', s.id)
   asyncio.run(main())
   "
   # fresh interpreter, separater uv run-Aufruf:
   uv run python -c "
   from app.app_utils.services import get_session_service
   import asyncio
   svc = get_session_service()
   async def main():
       s = await svc.get_session(app_name='app', user_id='u1', session_id='fixed-session-001')
       print('process 2 retrieved session:', s.id if s else None)
   asyncio.run(main())
   "
   ```
   Ergebnis: `data/sessions.db` wird beim ersten Aufruf angelegt (inkl. `data/`-Verzeichnis);
   Prozess 2 (frischer Interpreter, kein gemeinsamer State) liest dieselbe Session erfolgreich
   zurueck → Session uebersteht einen Prozess-Neustart.
6. `grep -rn "InMemorySessionService" app/` — keine Treffer mehr.
7. **Nicht durchgefuehrt (User-Entscheidung, siehe *Design-Entscheidungen*):** `agents-cli playground`
   / `agents-cli run --session-id <id>` mit echtem Modellaufruf — verschoben auf TASK-002.
