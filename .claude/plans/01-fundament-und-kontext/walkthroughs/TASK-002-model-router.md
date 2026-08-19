# Durchführungsbericht: TASK-002 — Model-Router (Gemini-first, provider-agnostisch)
Abgeschlossen: 2026-08-19T00:00:00Z

## Was wurde umgesetzt

Zentraler Model-Router `app/models/router.py` mit `model_for(role, settings=None)`:
Rolle → Tier → Modell-String → Provider, wie in `plan.md`/`tasks/TASK-002-model-router.md`
spezifiziert. `ROLE_TIERS` deckt alle neun Rollen ab (`orchestrator`/`continuity`/`research` →
`fast`, `plot`/`character`/`editor`/`style` → `heavy`, `classifier` → `lite`, `scene` → eigener
Tier `scene`). Gemini-Modelle (`gemini-*`) liefern einen nackten String zurück (ADK-nativ, kein
Wrapper); `anthropic/*` liefert eine `LiteLlm`-Instanz; `local` wirft `NotImplementedError` mit
Verweis auf `03-szenen-und-lokales-llm/TASK-001`; unbekannte Rollen/Provider werfen `ValueError`.

Neu geschaffen: `app/config.py` mit einer `pydantic-settings`-`Settings`-Klasse (bisher gab es
keine zentrale Settings-Klasse im Scaffold). Sie liest `MK34_MODEL_HEAVY/_FAST/_LITE/_SCENE`,
`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, die Judge-Modell- und Buchprojekt-Variablen aus der
Umgebung/`.env` (via `pydantic-settings`' eigenem `env_file`-Loading, analog zum bereits
vorhandenen `load_dotenv()` in `app/fast_api_app.py` — die `.env` selbst wurde von mir zu keinem
Zeitpunkt gelesen oder inspiziert, siehe *Design-Entscheidungen*).

`app/agent.py`: Root-Agent-Modell auf `model_for("orchestrator")` umgestellt (bewusst beauftragte
Modelländerung, E6 — Code-Preservation-Ausnahme dokumentiert im Code-Kommentar). Da `model_for`
für Gemini einen nackten String liefert, wird dieser weiterhin in `Gemini(...)` mit den
bestehenden `retry_options` gewrappt (nur falls das Ergebnis ein `str` ist — ein zukünftiger
`LiteLlm`-Rückgabewert würde direkt an `Agent(model=...)` durchgereicht, ADK akzeptiert beides).

`.env.example`: Der alte `MK34_CLOUD_HEAVY_MODEL`/`MK34_CLOUD_FAST_MODEL`-Block wurde durch das
neue `MK34_MODEL_HEAVY/_FAST/_LITE/_SCENE`-Schema ersetzt, inklusive Kommentar zu den
GEMINI_API_KEY-Anforderungen und den späteren Claude-/`local`-Werten.

`tests/unit/test_router.py`: 21 pytest-Fälle für Rollen-Mapping (alle neun Rollen), Tier-Auflösung
(`Settings.model_for_tier`), und Provider-Erkennung (Gemini-String, `LiteLlm`-Instanz ohne echten
API-Call, `local` → `NotImplementedError`, unbekannte Rolle/Tier/Provider → `ValueError`, fehlender
`GEMINI_API_KEY` → `RuntimeError`). Kein LLM-Output wird getestet.

Zusätzlich wurde der nachgeholte Live-Smoke-Test aus TASK-001 durchgeführt: `agents-cli playground`
und zwei getrennte `agents-cli run --session-id <id>`-Prozesse, beide über echtes Gemini (siehe
*Verifikationsschritte*).

## Geänderte Dateien

- `mk34-book-agent/app/config.py` (neu) — `Settings`-Klasse (`pydantic-settings`), liest
  `MK34_MODEL_*`, API-Keys, Judge-Modelle, Buchprojekt-Pfade aus `.env`/Umgebung
- `mk34-book-agent/app/models/__init__.py` (neu) — Re-Export von `model_for`, `ROLE_TIERS`
- `mk34-book-agent/app/models/router.py` (neu) — `model_for(role)`, Rollen-Tier-Mapping,
  Provider-Erkennung (Gemini/Claude/lokal)
- `mk34-book-agent/app/agent.py` — `MODEL = model_for("orchestrator")` statt hartcodiertem
  `"gemini-3.6-flash"`; `Gemini(...)`-Wrapper nur noch bedingt (falls `MODEL` ein `str` ist)
- `mk34-book-agent/.env.example` — `MK34_CLOUD_HEAVY_MODEL`/`MK34_CLOUD_FAST_MODEL` ersetzt durch
  `MK34_MODEL_HEAVY/_FAST/_LITE/_SCENE`, inkl. Kommentarblock zu Later-Werten
- `mk34-book-agent/app/fast_api_app.py` — GCP-Auth (`google.auth.default()`,
  `google.cloud.logging.Client()`) und `otel_to_cloud` jetzt an `GOOGLE_GENAI_USE_VERTEXAI`
  gekoppelt statt bedingungslos (siehe *Design-Entscheidungen* — Abweichung von der
  Betroffene-Dateien-Liste, aber notwendig für das Live-Smoke-Test-Akzeptanzkriterium)
- `mk34-book-agent/tests/unit/test_router.py` (neu) — 21 Testfälle, Code-Korrektheit
- `mk34-book-agent/pyproject.toml` — `pydantic-settings` als Dependency, `google-adk[...,
  extensions]` (für `LiteLlm`/`litellm`), `codespell`-`ignore-words-list` um haeufige deutsche
  Woerter erweitert (siehe *Design-Entscheidungen*)
- `mk34-book-agent/uv.lock` — durch `agents-cli install` aktualisiert

## Design-Entscheidungen

**`fast_api_app.py`-Fix war notwendig, obwohl nicht in der Betroffene-Dateien-Liste des Tasks.**
Der Scaffold-Default rief unconditional `google.auth.default()` (fuer `project_id`),
`google.cloud.logging.Client()` und `otel_to_cloud=True` auf — alle drei setzen GCP Application
Default Credentials voraus. In diesem Setup (Entscheidung E1: kein GCP-Projekt) existiert weder
`gcloud` noch eine ADC-Datei; jeder Aufruf von `agents-cli run`/`agents-cli playground` schlug
dadurch fehl, unabhaengig vom Router. Das blockierte das explizite Akzeptanzkriterium
"nachgeholter Live-Smoke-Test". Fix: GCP-Auth/Logging/Telemetry nur noch aktiv, wenn
`GOOGLE_GENAI_USE_VERTEXAI` truthy ist (das Flag, an dem auch ADK's eigener `Gemini`-Client
Vertex- vs. AI-Studio-Pfad entscheidet) — nicht an der bloßen Anwesenheit von
`GOOGLE_CLOUD_PROJECT`, da ein dort stehender, unbenutzter Wert sonst faelschlich den ADC-Pfad
erzwingen wuerde. Ohne Vertex faellt der Logger auf eine kleine `_LocalLogger`-Fallback-Klasse
zurueck (`log_struct`-kompatibel, nutzt Standard-`logging`), damit die `/feedback`-Route weiter
funktioniert.

**`.env` wurde zu keinem Zeitpunkt gelesen.** Ich habe ausschliesslich Anwesenheits-Checks
(`[ -n "$VAR" ]`) verwendet, nie den Inhalt. Waehrend der Umsetzung stellte sich heraus, dass die
reale `.env` (anders als in `plan.md`s Konfigurationstabelle dokumentiert) noch einen nicht-leeren
`GOOGLE_CLOUD_PROJECT`-Wert enthielt; das wurde ausschliesslich ueber die Anwesenheits-Pruefung
sichtbar, nie als Wert gesehen — die Router-/`fast_api_app.py`-Logik wurde so gebaut, dass sie
robust gegen genau diesen Fall ist (Gate auf `GOOGLE_GENAI_USE_VERTEXAI`, nicht auf
`GOOGLE_CLOUD_PROJECT`-Anwesenheit).

**`model_for(role, settings=None)` statt reinem `model_for(role)`.** Das optionale
`settings`-Argument macht die Funktion ohne Monkeypatching von Umgebungsvariablen testbar (Tests
konstruieren `Settings(...)` direkt mit `_env_file=None`, isoliert von der echten `.env`) und
aendert nichts am beauftragten Aufrufmuster `model_for("orchestrator")` in `app/agent.py`.

**`codespell`-Ignore-Liste um deutsche Woerter erweitert (`ist`, `als`, `oder`, `modell`,
`lokale`, `lokales`, `explizit`, `hart`).** Diese haeufigen deutschen Woerter matchen zufaellig
codespells englisches Tippfehler-Woerterbuch (z. B. `ist`→`is`). Analog zum bereits vorhandenen
Eintrag `rouge` (bestehende Konvention im Projekt) fuer False Positives bei nicht-englischem Text
in Code-Kommentaren.

**`google-adk[extensions]`-Extra ergaenzt.** `LiteLlm` importiert `litellm` nur bei tatsaechlicher
Nutzung (Anthropic-Zweig des Routers), aber das Paket muss installiert sein, damit der Import in
Tests und im Fehlerpfad ueberhaupt ladbar ist (`ImportError: LiteLLM support requires: pip install
google-adk[extensions]` sonst).

## Verifikationsschritte

1. `uv run pytest tests/unit -v` — 22 Tests gruen (21 Router-Tests + bestehender `test_dummy`).
2. `~/.local/bin/agents-cli lint` — `ruff check`, `ruff format --check`, `codespell`, `ty check`
   alle gruen.
3. `grep -rn "gemini-" app/` — nur Treffer in `app/config.py` (Settings-Defaults) und
   `app/models/router.py` (Docstring/Praefix-Check); kein Agent-Modul haelt einen Modell-String.
4. `set -a && source .env && set +a && [ -n "$GEMINI_API_KEY" ]` — bestaetigt (Anwesenheit,
   nicht Wert): `GEMINI_API_KEY` ist gesetzt.
5. **Live-Smoke-Test, Teil 1 (Session-Persistenz ueber zwei getrennte Prozesse):**
   ```
   agents-cli run "Merke dir bitte die Zahl 4217. Antworte nur mit 'OK'."
   # -> [root_agent]: OK
   # -> Session: 4e7c953e-dbd1-4954-a8bf-345d6e36892e (Server startet + stoppt, one-off)
   agents-cli run "Welche Zahl habe ich dir eben genannt? Antworte nur mit der Zahl." \
     --session-id 4e7c953e-dbd1-4954-a8bf-345d6e36892e
   # -> [root_agent]: 4217 (neuer Server-Prozess, andere PID/Port)
   ```
   Der zweite, komplett neue Serverprozess erinnert sich korrekt an die Zahl aus dem ersten
   Prozess — Session uebersteht den Prozess-Neustart via `DatabaseSessionService`/SQLite,
   end-to-end ueber echtes Gemini.
6. **Live-Smoke-Test, Teil 2 (`agents-cli playground`):** `agents-cli playground` gestartet,
   `curl` gegen `/apps/app/users/.../sessions` (Session angelegt) und `/run_sse` mit der Anweisung
   "Antworte nur mit dem Wort PLAYGROUND-OK." → Antwort `"PLAYGROUND-OK"` von Gemini erhalten,
   Server danach gestoppt (`pkill -f "adk web ."`).
7. `data/sessions.db` und `.google-agents-cli/` sind gitignored (`git status --porcelain` zeigt
   keine Test-Artefakte).
