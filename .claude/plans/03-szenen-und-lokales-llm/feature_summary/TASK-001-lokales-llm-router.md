# Feature-Zusammenfassung: TASK-001 — Lokales LLM im Model-Router

## Was wurde umgesetzt

Der zentrale Model-Router kann jetzt tatsächlich auf das lokale, unzensierte LLM
(`supergemma4-26b-abliterated`, angebunden über eine verschlüsselte Parallels-VM und einen
SSH-Tunnel auf `localhost:8080`) routen — bisher war das nur ein `NotImplementedError`-Platzhalter
aus Plan 1. Die Anbindung ist bewusst eng begrenzt: ausschließlich die Rolle `scene` (der
Szenen-Schreib-Agent) darf die lokale Route nutzen, jede andere Rolle wird mit einer klaren
Fehlermeldung abgewiesen.

Zwei Sicherheitsmechanismen sind zentral:
- Ein Health-Check (`local_model_available()`) prüft vor jeder lokalen Anfrage, ob die VM/der
  Tunnel überhaupt erreichbar ist — ohne jemals selbst abzustürzen.
- Ist die VM nicht erreichbar, bricht das System kontrolliert ab und sagt der Autorin/dem Autor
  genau, was zu tun ist („VM starten"). Ein unbemerktes Ausweichen auf die Cloud ist nur möglich,
  wenn das explizit per Konfigurationsschalter erlaubt wurde — und dann mit einer deutlichen
  Warnung, weil eine als „lokal" eingestufte (unzensierte) Szene auf einem Cloud-Modell
  wahrscheinlich verweigert oder abgeschwächt wird.

Ohne aktive VM (heutiger Stand) bleibt die Szenen-Rolle automatisch auf der bereits laufenden
Cloud-Route (Gemini) — der Schreib-Workflow ist dadurch in den folgenden Tasks (TASK-002/003)
sofort nutzbar, ganz ohne dass die VM je gestartet werden muss.

## Geänderte Dateien

- `mk34-book-agent/app/models/router.py`
- `mk34-book-agent/app/config.py`
- `mk34-book-agent/tests/unit/test_router_local.py` (neu)
- `mk34-book-agent/tests/unit/test_router.py`
- `mk34-book-agent/pyproject.toml`

## Nächster Schritt

TASK-002 (Scene Agent, Start auf Gemini) kann direkt auf `model_for("scene")` aufbauen — ohne
`route`-Argument liefert das zuverlässig die Cloud-Route. Die tatsächliche dynamische
Umschaltung lokal/Cloud pro Anfrage (abhängig vom Classifier-Ergebnis aus TASK-004) erfordert
zusätzlich einen Laufzeit-Wrapper in der Schreib-Pipeline, da ADK das Modell eines Agenten nur
einmal bei dessen Konstruktion auflöst — dieser Punkt ist im Router-Docstring für TASK-004
vorbereitet. Der volle Live-Roundtrip gegen das tatsächlich laufende lokale Modell steht noch
aus (VM aktuell nicht gestartet) und sollte nachgeholt werden, sobald die VM läuft.
