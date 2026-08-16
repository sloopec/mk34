# TASK-002: Model-Router (Claude via LiteLLM + lokales Modell)
Status: ⏳ pending
Depends-on: [TASK-001]
Parallel: yes

## Description
Zentrale Modellauswahl in `app/models/router.py`. Kapselt `LiteLlm`-Konstruktion, damit kein Agent Modell-Strings hartcodiert.

```python
from google.adk.models.lite_llm import LiteLlm

# Cloud
LiteLlm(model="anthropic/claude-opus-5")
LiteLlm(model="anthropic/claude-sonnet-5")
LiteLlm(model="anthropic/claude-haiku-4-5")

# Lokal: llama-server (OpenAI-kompatibel) hinter SSH-Tunnel
LiteLlm(model="openai/supergemma4",
        api_base="http://localhost:8080/v1",
        api_key="not-needed")
```

Rollen-Mapping laut Plan-Matrix: `orchestrator`, `plot`, `character`, `scene`, `editor`, `continuity`, `research`, `style`, `classifier`.

Zusaetzlich:
- `local_model_available() -> bool` gegen `MK34_LOCAL_HEALTH_URL`.
- Kein stiller Cloud-Fallback: bei Ausfall Fehler + Handlungsanweisung, Fallback nur wenn `MK34_ALLOW_CLOUD_FALLBACK=true`.
- Pydantic-Settings liest alle Werte aus `.env`.

**Hinweis zur Code-Preservation:** Der Scaffold liefert Gemini-Defaults. Das Ersetzen durch `LiteLlm` ist hier ausdruecklich beauftragt (Open Question #1) und keine ungefragte Modelloption.

## Acceptance Criteria
- [ ] `model_for("scene")` liefert je nach `state["route"]` bzw. Override die lokale oder die Cloud-`BaseLlm`-Instanz
- [ ] Alle Modell-IDs und Endpoints kommen aus Settings, nichts ist hartcodiert
- [ ] `local_model_available()` liefert `False`, wenn die VM/der Tunnel nicht laeuft — ohne Exception
- [ ] pytest deckt Router-Mapping und Health-Check-Fallback ab (Code-Korrektheit, kein LLM-Output)
- [ ] Ein Roundtrip gegen das lokale Modell ist manuell verifiziert (`curl http://localhost:8080/health` + ein `agents-cli run`)

## Affected Files
- `app/models/__init__.py`
- `app/models/router.py`
- `app/config.py`
- `.env.example`
- `tests/unit/test_router.py`
