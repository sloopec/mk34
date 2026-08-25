# Durchführungsbericht: TASK-001 — Lokales LLM im Model-Router
Abgeschlossen: 2026-08-24T00:00:00Z

## Was wurde umgesetzt

Der Router (`app/models/router.py`) bindet die lokale Route (`supergemma4-26b-abliterated`
via llama.cpp/llama-server, SSH-Tunnel `localhost:8080`) an — ausschließlich für die Rolle
`scene`, wie im Plan festgelegt.

- `local_model_available(settings=None) -> bool`: Preflight-Health-Check gegen
  `MK34_LOCAL_HEALTH_URL` über `urllib.request` (Standardbibliothek, keine neue Abhängigkeit).
  Liefert garantiert `bool`, nie eine Exception — fängt `URLError`, `OSError` und `ValueError`
  (ungültige URL) ab.
- `model_for(role, settings=None, route=None)`: neuer optionaler `route`-Parameter
  (`"local"` | `"cloud"` | `None`). Ohne `route` bleibt die Rolle `scene` auf der Cloud-Route
  (`MK34_MODEL_SCENE`) — das ist Stufe A (TASK-002/003), noch ohne Classifier. Ist
  `MK34_MODEL_SCENE` selbst literal `"local"` gesetzt, wirkt das als Config-Force auch ohne
  explizites `route`-Argument (z. B. bevor der Classifier aus TASK-004 existiert).
- Kein stiller Cloud-Fallback: ist die VM bei `route=="local"` nicht erreichbar, bricht
  `model_for` mit `RuntimeError` und einer konkreten Handlungsanweisung ab („VM starten,
  siehe docs/LOCAL_MODEL_VM_SETUP.md, `scripts/start_local_model.sh`, SSH-Tunnel
  `ssh -f -N mk34-vm-tunnel`"). Nur bei explizitem `MK34_ALLOW_CLOUD_FALLBACK=true` fällt der
  Router mit `warnings.warn(...)` auf die Cloud-Route zurück.
- Rollen-Guard: jede Rolle außer `scene`, die die lokale Route anfordert (explizit über
  `route="local"` oder indirekt über eine hypothetische Tier-Config), erhält einen klaren
  `ValueError`.
- `app/config.py`: neue Settings-Felder `mk34_local_model`, `mk34_local_api_base`,
  `mk34_local_api_key`, `mk34_local_health_url`, `mk34_allow_cloud_fallback` — Defaults
  identisch zu den bereits in `.env.example` dokumentierten Werten (die dort schon aus Plan 1
  vorbereitet waren, keine Änderung an `.env.example` nötig).

## Architektur-Hinweis für TASK-004 (wichtig für Folge-Tasks)

`Agent.model` wird laut ADK (`LlmAgent.canonical_model`) einmalig bei der Agent-Konstruktion
aufgelöst — es gibt keinen Callable-/Late-Binding-Support. `state["route"]` wird aber erst zur
Laufzeit vom Classifier gesetzt (TASK-004), mitten in der `writing_pipeline`. `model_for()`
selbst bleibt deshalb bewusst zustandslos/rein (Rolle + optionale explizite `route` →
Modell) — die eigentliche Pro-Turn-Neuauflösung (State lesen, `model_for` erneut aufrufen,
frische `Agent`-Instanz bauen) muss der Aufrufer zur Laufzeit übernehmen. Für TASK-002/003
ist das irrelevant (`route=None` → immer Cloud). TASK-004 wird dafür einen
`BaseAgent`-Wrapper in `app/pipelines/writing.py` einführen (analog zu den bereits
vorhandenen `BaseAgent`-Subklassen `_SceneSlotFixture`/`QualityChecker`), der
`ctx.session.state.get("route")` liest und den Scene-Agent-Schritt entsprechend neu
konstruiert. Dies ist im Router-Docstring dokumentiert.

## Geänderte Dateien

- `app/models/router.py` — `local_model_available`, `route`-Parameter auf `model_for`,
  `_resolve_local_scene_model`, `_resolve_cloud_model` (Refactor der bestehenden
  Gemini/Anthropic-Logik in eine wiederverwendbare Hilfsfunktion), Rollen-Guard.
- `app/config.py` — fünf neue `MK34_LOCAL_*`/`MK34_ALLOW_CLOUD_FALLBACK`-Settings-Felder.
- `tests/unit/test_router_local.py` (neu) — Health-Check-Verhalten (online/offline/Fehlerfälle),
  Routing-Zweige, Fallback-Verbot inkl. Warnung, Rollen-Guard für alle acht Nicht-`scene`-Rollen.
- `tests/unit/test_router.py` — der alte Plan-1-Test, der `NotImplementedError` für
  `mk34_model_scene="local"` erwartete, ist durch das neue Verhalten überholt (TASK-001 baut
  genau diesen Platzhalter aus) und wurde durch einen Test ersetzt, der den neuen
  `RuntimeError`-Pfad (VM nicht erreichbar) fixiert.
- `pyproject.toml` — `codespell`-`ignore-words-list` um die deutschen Wörter `egal` und
  `alternativ` ergänzt (bestehende Projekt-Konvention für deutschsprachige Kommentare, siehe
  Kommentar direkt über der Liste).

## Design-Entscheidungen

- Health-Check über `urllib.request` (Standardbibliothek) statt einer neuen Abhängigkeit
  (`httpx`/`requests`) — das Projekt hat aktuell keine synchrone HTTP-Client-Bibliothek in
  `pyproject.toml`, und ein einzelner GET-Request mit Timeout braucht keine.
- `route` als expliziter Parameter statt eines impliziten State-Lookups in `model_for` selbst:
  hält den Router frei von ADK-Kenntnis (`InvocationContext`/`Session`) und einfach
  unit-testbar — konsistent mit dem bestehenden `settings`-Parameter-Muster in `model_for`.
- Edge-Case `MK34_MODEL_SCENE=local` + `route="cloud"` explizit angefordert: klarer
  `ValueError` statt stiller Fehlinterpretation, da kein separates Cloud-Modell für diesen
  Fall existiert.

## Verifikationsschritte

1. `uv run pytest tests/unit/test_router.py tests/unit/test_router_local.py -q` — 41 Tests,
   alle grün (Health-Check on/off/Fehlerfälle, Routing-Zweige, Fallback-Verbot mit/ohne
   Opt-in, Rollen-Guard für alle acht Nicht-`scene`-Rollen, Config-Force-Fall).
2. `agents-cli lint` — grün (`ruff check`, `ruff format --check`, `codespell`, `ty check`).
3. **Manueller Preflight (VM-Status heute geprüft):** `curl -m 3 http://localhost:8080/health`
   → `Failed to connect ... Couldn't connect to server` — VM/SSH-Tunnel läuft aktuell nicht.
   Das ist der laut Plan **erwartete, korrekte Zustand** (die VM wird nicht dauerhaft
   betrieben) und wurde zusätzlich end-to-end gegen den echten Prozess-Environment
   (`.env` via `source`, Inhalt nie gelesen/inspiziert) verifiziert:
   `model_for("scene", route="local")` liefert exakt den dokumentierten `RuntimeError` mit
   Handlungsanweisung („VM starten ... docs/LOCAL_MODEL_VM_SETUP.md").
4. **Offen (ehrlich dokumentiert, kein Fake-Nachweis):** der volle Roundtrip gegen das
   tatsächlich laufende lokale Modell (`agents-cli run` mit `route="local"` bei erreichbarer
   VM) ist mangels laufender VM in dieser Session nicht durchführbar und bleibt analog zum
   Muster aus Plan 2 als offene Live-Verifikation dokumentiert — nachzuholen, sobald die VM
   gestartet ist (siehe `docs/LOCAL_MODEL_VM_SETUP.md`).
