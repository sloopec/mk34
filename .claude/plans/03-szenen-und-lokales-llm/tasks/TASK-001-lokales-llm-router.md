# TASK-001: Lokales LLM im Model-Router
Status: ⏳ ausstehend
Abhängig von (plan-übergreifend): 01-fundament-und-kontext/TASK-002
Parallel: ja
*(herausgetrennt aus dem frueheren TASK-002 des Gesamtplans — dort verblieb der Gemini-first-Router)*

## Beschreibung
Der Router aus Plan 1 kennt den Provider `local` bisher nur als `NotImplementedError`. Dieser Task bindet das lokale unzensierte Modell an — **ausschliesslich fuer die Rolle `scene`**, wie von Anfang an entschieden.

```python
# in model_for(), Zweig "local":
LiteLlm(model=settings.local_model,          # "openai/supergemma4"
        api_base=settings.local_api_base,    # "http://localhost:8080/v1"
        api_key=settings.local_api_key)      # "not-needed"
```

Infrastruktur laut `docs/LOCAL_MODEL_VM_SETUP.md`: llama.cpp `llama-server` mit `supergemma4-26b-abliterated-Q4_K_M.gguf` in einer verschluesselten Parallels-VM, erreichbar ueber SSH-Tunnel auf `localhost:8080` (OpenAI-kompatible API).

Zusaetzlich:
- `local_model_available() -> bool` gegen `MK34_LOCAL_HEALTH_URL` — liefert `False` ohne Exception, wenn VM/Tunnel nicht laufen.
- **Kein stiller Cloud-Fallback:** ist `state["route"] == "local"` und die VM nicht erreichbar, bricht der Lauf mit Handlungsanweisung („VM starten: scripts in docs/LOCAL_MODEL_VM_SETUP.md") ab. Fallback nur bei `MK34_ALLOW_CLOUD_FALLBACK=true`, mit expliziter Warnung.
- `model_for("scene")` liest `state["route"]` (gesetzt vom Classifier in TASK-004 bzw. per Override); Default bis dahin: Cloud-Route (`MK34_MODEL_SCENE`).
- Andere Rollen als `scene` duerfen `local` nicht anfordern (Guard mit klarer Fehlermeldung).

## Akzeptanzkriterien
- [ ] `model_for("scene")` liefert bei `route=="local"` die konfigurierte `LiteLlm`-Instanz, bei `route=="cloud"` das Modell aus `MK34_MODEL_SCENE`
- [ ] `local_model_available()` liefert `False` ohne Exception, wenn VM/Tunnel nicht laufen
- [ ] Nicht erreichbare VM bei `route=="local"` → Abbruch mit Handlungsanweisung; Fallback nur bei `MK34_ALLOW_CLOUD_FALLBACK=true` und mit Warnung
- [ ] `local` fuer eine andere Rolle als `scene` wird mit klarer Fehlermeldung abgelehnt
- [ ] pytest deckt Routing-Zweige und Health-Check-Verhalten ab (ohne laufende VM, via Mock)
- [ ] Ein manueller Roundtrip gegen das lokale Modell ist verifiziert (`curl http://localhost:8080/health` + ein `agents-cli run` mit erzwungener lokaler Route)

## Betroffene Dateien
- `app/models/router.py`
- `app/config.py`
- `.env.example` (`MK34_LOCAL_*`, `MK34_ALLOW_CLOUD_FALLBACK` aktivieren)
- `tests/unit/test_router_local.py`
