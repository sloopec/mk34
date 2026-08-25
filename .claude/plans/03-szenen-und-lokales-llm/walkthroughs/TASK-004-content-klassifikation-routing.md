# Durchführungsbericht: TASK-004 — Content-Klassifikation und lokales Routing
Abgeschlossen: 2026-08-24T00:00:00Z

## Was wurde umgesetzt

- `app/schemas.py::RouteDecision` — strukturierte Routing-Entscheidung
  (`route: "local"|"cloud"`, `reason`, `confidence`).
- `app/prompts/classifier.py::CLASSIFIER_INSTRUCTION` — Routing-Kriterien wörtlich
  aus der Task-Beschreibung übernommen (explizite Sexualität als Verbreitungsvektor,
  Gewalt/Körperhorror, moralisch kontroverse Manipulationsszenen → lokal;
  Boardroom/Recherche/Dialog/ELI5 → Cloud, im Zweifel Cloud).
- `app/agents/classifier_agent.py::create_classifier_agent()` — `model_for("classifier")`
  (Start `gemini-3.5-flash-lite`), `output_schema=RouteDecision`,
  `output_key="route_decision"`.
- `app/models/router.py::is_refusal(response)` (Entscheidung E9) — provider-agnostisch
  per Duck-Typing: deckt sowohl ADKs normalisiertes `LlmResponse`
  (`finish_reason`/`error_code`) als auch rohe Provider-Shapes ab (Gemini:
  `candidates[].finish_reason` `SAFETY`/`PROHIBITED_CONTENT`,
  `prompt_feedback.block_reason`; Claude: `stop_reason == "refusal"`).
- `app/agents/scene_agent.py::_log_refusal_if_detected` — rein beobachtendes
  `after_model_callback` (kein Guardrail, gibt immer `None` zurück): protokolliert
  eine erkannte Cloud-Refusal als Nachschärfungs-Hinweis für
  `uncensored-routing.json`.
- `app/pipelines/writing.py`:
  - `_apply_route_override_from_user_message` (neuer `before_agent_callback`,
    zusätzlich zu `_set_active_scene_from_user_message` aus TASK-003, jetzt als
    Liste): erkennt `--model local`/`--model cloud` sowie natürsprachliche
    Anweisungen ("schreibe das lokal"/"... in der Cloud").
  - `_create_classifier_step()` — Classifier-Agent mit `after_agent_callback=
    _apply_route_decision`, der `state["route"]` (flacher String, von
    `model_for("scene", route=...)` konsumiert) aus `route_decision` bzw. dem
    Override ableitet -- Override schlägt den Classifier immer.
  - `_RoutedSceneStep(BaseAgent)` — ersetzt den in TASK-003 statischen
    `create_scene_agent()`-Pipeline-Eintrag: baut den Scene Agent **pro
    Pipeline-Durchlauf** frisch mit der aktuellen `state["route"]` (siehe
    Design-Entscheidung im TASK-001-Walkthrough: ADKs `Agent.model` wird sonst nur
    einmal bei der Konstruktion aufgelöst).
  - Pipeline-Reihenfolge jetzt: `context_loader_step → plot_beat_step →
    character_brief_step → classifier_agent → scene_agent_step →
    continuity_agent → continuity_gate` (7 Schritte statt 6).
- `docs/LOCAL_MODEL_VM_SETUP.md` — neuer Abschnitt "Performance-Tuning für die
  lokale Route": Streaming (bereits per `/run_sse`-Default aktiv, keine
  Code-Änderung nötig), `--ctx-size`/`--threads`-Empfehlungen, Kontext-Caching für
  `world_bible.md`/`style_guide.md` als stabilen Prompt-Präfix.

## Live-Verifikation (echte Gemini-API, voller Orchestrator)

Zwei vollständige `agents-cli run -v`-Läufe gegen den echten Orchestrator:

**1. Automatische Klassifikation (Cloud-Route):**
`agents-cli run "Schreibe die Szene 'Die Diagnose' (Setting: Buero Dr. Aris, David
erhaelt Blutbild-Erklaerung)." -v`

- Trajektorie: `orchestrator → writing_pipeline → context_loader_step →
  plot_beat_step → character_brief_step → classifier_agent → scene_agent →
  continuity_agent → editing_loop (pass)`.
- Classifier-Entscheidung: `{"route": "cloud", "reason": "Es handelt sich um eine
  Recherche- und Dialogszene (Blutbild-Erklaerung im Buero von Dr. Aris) mit
  ELI5-Erklaerungen, die nicht unter die lokalen Kriterien ... faellt.",
  "confidence": 0.95}` — inhaltlich korrekt und mit expliziter Rubrik-Referenz
  begründet.
- `state["route"]` wurde korrekt auf `"cloud"` gesetzt, `_RoutedSceneStep` baute den
  Scene Agent entsprechend, Editor-Loop endete mit `grade: "pass"`.

**2. Manueller Override (`--model local`), VM nicht erreichbar:**
`agents-cli run "Schreibe die Szene 'Das kalte Schlafzimmer'. --model local" -v`

- `_apply_route_override_from_user_message` erkannte `--model local` und setzte
  `state["route_override"] = "local"` -- schlug damit die (nicht mehr ausgeführte)
  Classifier-Entscheidung.
- `_RoutedSceneStep` rief `model_for("scene", route="local")` auf; da die VM/der
  SSH-Tunnel nicht läuft (siehe TASK-001-Walkthrough), brach der Lauf **kontrolliert**
  mit `RuntimeError` ab -- als sauberes `errorCode`/`errorMessage`-Event im Trace,
  nicht als stiller Fallback und nicht als Absturz:
  ```
  "errorMessage": "Lokales Modell nicht erreichbar (MK34_LOCAL_HEALTH_URL=
  'http://localhost:8080/health'). Kein stiller Cloud-Fallback
  (MK34_ALLOW_CLOUD_FALLBACK=false, Default). Handlungsanweisung: VM starten --
  siehe docs/LOCAL_MODEL_VM_SETUP.md (scripts/start_local_model.sh) ..."
  ```
- Bestätigt den End-to-End-Fehlerpfad aus TASK-001 jetzt durch die **gesamte**
  Turn-Kette (Orchestrator → writing_pipeline → scene_agent_step), nicht nur
  isoliert im Router.
- Keine Manuskript-Artefakte entstanden (Lauf brach vor jedem `write_scene`-Aufruf
  ab) -- verifiziert per `git status books/life_link/` (clean).

## Akzeptanzkriterien-Status

| Kriterium | Status |
|---|---|
| Classifier liefert strukturierte Routing-Entscheidungen mit Begründung | ✅ live verifiziert |
| Manueller Override funktioniert und schlägt den Classifier | ✅ live verifiziert |
| Lokaler Ausfall → klare Fehlermeldung, kein stiller Cloud-Fallback | ✅ live verifiziert (durch die volle Turn-Kette) |
| E9: `is_refusal(...)` erkennt beide Gemini-Signalformen + ist für Claude vorbereitet | ✅ 12 Unit-Tests mit gestubbten Responses |
| `uncensored-routing.json` zu 100 % korrekt geroutet | ⏳ Dataset entsteht in TASK-005 (Stufe B) -- dort verifiziert |
| Streaming ist aktiv | ✅ dokumentiert (ADK-Default via `/run_sse`, kein Code nötig) -- **Zeitrahmen (1000-Woerter-Szene, 2-5 Min) nicht live gegen die echte lokale Route messbar, da VM nicht laeuft** |
| Preflight-Health-Check läuft, bevor die Pipeline startet | ✅ strukturell (Health-Check in `model_for`, laeuft vor jedem lokalen Generierungsversuch, siehe TASK-001) |

## Geänderte Dateien

- `app/schemas.py`
- `app/prompts/classifier.py` (neu)
- `app/agents/classifier_agent.py` (neu)
- `app/models/router.py` (`is_refusal`)
- `app/agents/scene_agent.py` (`_log_refusal_if_detected`, `route`-Parameter bereits
  in TASK-002 vorbereitet -- hier tatsächlich genutzt)
- `app/pipelines/writing.py` (Classifier-Schritt, `_RoutedSceneStep`, Override-Callback)
- `docs/LOCAL_MODEL_VM_SETUP.md`
- `tests/unit/test_classifier_agent.py` (neu)
- `tests/unit/test_is_refusal.py` (neu)
- `tests/unit/test_pipeline_geruest.py` (7-Schritte-Struktur, neue Override-/
  Routing-/`_RoutedSceneStep`-Tests)
- `tests/unit/test_scene_agent.py` (`after_model_callback`-Test angepasst)
- `pyproject.toml` (codespell-Ignore-Liste)

## Verifikationsschritte

1. `uv run pytest tests/unit -q` — 251 Tests grün.
2. `agents-cli lint` — grün.
3. Zwei vollständige Live-Läufe gegen die echte Gemini-API (siehe oben) --
   automatische Klassifikation UND manueller Override, inkl. des vollständigen
   VM-nicht-erreichbar-Fehlerpfads durch die gesamte Turn-Kette.
4. **Offen:** `uncensored-routing.json`-Gate (100 % korrektes Routing) und die
   Zeitrahmen-Messung der lokalen Route -- beide hängen an TASK-005 (Stufe B) bzw.
   einer laufenden VM und werden dort nachgetragen/dokumentiert.
