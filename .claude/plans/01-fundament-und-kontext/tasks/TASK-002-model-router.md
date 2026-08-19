# TASK-002: Model-Router (Gemini-first, provider-agnostisch)
Status: ✅ erledigt
Abhängig von: [TASK-001]
Parallel: ja

## Beschreibung
Zentrale Modellauswahl in `app/models/router.py`. Kein Agent hartcodiert Modell-Strings.

**Entscheidung E6 (Gemini-first):** Der Start erfolgt ausschliesslich mit Gemini — ADK-nativ als Modell-String, **ohne** LiteLLM-Umweg. Claude (via LiteLLM) und das lokale Modell bleiben als konfigurierbare Alternativen im Design; die Umschaltung pro Agent ist eine `.env`-Zeile, keine Code-Änderung.

```python
def model_for(role: str) -> str | BaseLlm:
    """Rolle -> Tier -> Modell-String -> Provider."""
    tier = ROLE_TIERS[role]           # heavy | fast | lite | scene
    model_id = settings.model_for_tier(tier)   # MK34_MODEL_HEAVY | _FAST | _LITE | _SCENE
    if model_id.startswith("gemini-"):
        return model_id               # ADK-nativ, kein Wrapper
    if model_id.startswith("anthropic/"):
        from google.adk.models.lite_llm import LiteLlm
        return LiteLlm(model=model_id)             # vorgesehen, spaeter
    if model_id == "local":
        raise NotImplementedError("Lokales LLM: 03-szenen-und-lokales-llm/TASK-001")
    raise ValueError(f"Unbekannter Provider: {model_id}")
```

Rollen-Mapping: `orchestrator`/`continuity`/`research` → fast, `plot`/`character`/`editor`/`style` → heavy, `classifier` → lite, `scene` → eigene Variable `MK34_MODEL_SCENE` (einzige Rolle mit vorgesehenem lokalem LLM).

Startwerte (verifiziert 2026-08-17, siehe `../README.md` → Model-Routing-Matrix): heavy `gemini-3.1-pro-preview`, fast `gemini-3.7-flash`, lite `gemini-3.5-flash-lite`, scene `gemini-3.1-pro-preview`.

Zusätzlich:
- Root-Agent (`app/agent.py`, aktuell `MODEL = "gemini-3.6-flash"` aus dem Scaffold) auf `model_for("orchestrator")` umstellen — die Modelländerung ist im Rahmen von E6 explizit beauftragt (Code-Preservation-Ausnahme dokumentieren).
- Pydantic-Settings lesen alle Werte aus `.env`; `.env.example` auf das neue `MK34_MODEL_*`-Schema aktualisieren (die alten `MK34_CLOUD_*_MODEL`-Zeilen ersetzen). **Die `.env` selbst wird nicht gelesen oder geändert** (Regel in `mk34-book-agent/CLAUDE.md`); `GEMINI_API_KEY` ist laut User vorhanden.
- Fehlender `GEMINI_API_KEY` → klare Fehlermeldung, kein stiller Fallback.
- Der lokale-LLM-Anteil des früheren Router-Tasks (Health-Check, `MK34_LOCAL_*`, Fallback-Logik) ist **herausgetrennt**: → `03-szenen-und-lokales-llm/TASK-001`.

## Akzeptanzkriterien
- [x] `model_for(role)` liefert für alle neun Rollen den korrekten Wert; Gemini-Rollen liefern einen nackten String, kein Wrapper-Objekt
- [x] Provider-Erkennung: `anthropic/*` liefert eine `LiteLlm`-Instanz (Testfall mit umgestellter Settings-Variable, ohne echten API-Call); `local` wirft `NotImplementedError` mit Verweis auf Plan 3
- [x] Alle Modell-IDs kommen aus Settings; `grep -r "gemini-" app/` trifft nur Router/Settings-Defaults
- [x] pytest deckt Rollen-Mapping, Tier-Auflösung und Provider-Erkennung ab (Code-Korrektheit, kein LLM-Output)
- [x] **Nachgeholter Live-Smoke-Test aus TASK-001, jetzt mit Gemini** (siehe `walkthroughs/TASK-001-scaffold-projekt.md`, Abschnitt *Verifikation*):
  - `agents-cli playground` startet und der Agent antwortet über Gemini
  - Session-Persistenz über einen Prozess-Neustart via zwei getrennten `agents-cli run --session-id <id>`-Aufrufen nachgewiesen (End-to-End-Ergänzung zur bereits erfolgten Python-Verifikation von `DatabaseSessionService`)
- [x] `.env.example` dokumentiert das `MK34_MODEL_*`-Schema inkl. der Später-Werte (Claude/`local`) als Kommentar

Details, Abweichungen (u. a. notwendiger Fix in `app/fast_api_app.py` fuer den GCP-freien
Lokalbetrieb) und Verifikationsschritte: `walkthroughs/TASK-002-model-router.md`.

## Betroffene Dateien
- `app/models/__init__.py`
- `app/models/router.py`
- `app/config.py`
- `app/agent.py` (Root-Agent auf `model_for("orchestrator")`)
- `.env.example`
- `tests/unit/test_router.py`
