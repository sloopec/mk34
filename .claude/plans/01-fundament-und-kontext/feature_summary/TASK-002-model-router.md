# Feature-Zusammenfassung: TASK-002 — Model-Router (Gemini-first, provider-agnostisch)

## Was wurde umgesetzt

mk34 hat jetzt eine einzige, zentrale Stelle, die Modelle fuer Agenten waehlt:
`model_for(role)` in `mk34-book-agent/app/models/router.py`. Jede Agentenrolle (Orchestrator,
Plot, Character, Editor, Style, Continuity, Research, Classifier, Scene) wird ueber ein
Tier-System (`heavy`/`fast`/`lite`/`scene`) auf ein konkretes Modell abgebildet, konfigurierbar
ausschliesslich ueber `.env`-Variablen (`MK34_MODEL_HEAVY/_FAST/_LITE/_SCENE`) — kein Agent-Modul
haelt jemals einen eigenen Modell-String.

Gestartet wird ausschliesslich mit Gemini (Entscheidung E6): Gemini-Modelle laufen ADK-nativ als
einfacher String, ohne Umweg ueber LiteLLM. Der Router ist aber bereits so gebaut, dass eine
spaetere Umschaltung auf Claude (via LiteLLM) oder das lokale Modell (nur fuer die Szenen-Rolle,
kommt in einem spaeteren Plan) eine reine `.env`-Aenderung waere, keine Code-Aenderung. Fehlt der
noetige `GEMINI_API_KEY`, bricht der Router mit einer klaren Fehlermeldung ab statt still auf ein
anderes Modell auszuweichen.

Der Root-Agent des Scaffolds nutzt jetzt `model_for("orchestrator")` statt eines hartcodierten
Testmodells — eine bewusst im Rahmen dieses Tasks beauftragte Modelländerung.

Ausserdem wurde ein Problem im generierten Scaffold behoben, das den lokalen Testbetrieb ganz
grundsaetzlich blockiert hatte: Der Server versuchte bislang immer, sich gegen Google Cloud zu
authentifizieren (auch wenn gar kein GCP-Projekt genutzt wird), und schlug deshalb auf jeder
Maschine ohne GCP-Setup fehl. Das laeuft jetzt nur noch, wenn tatsaechlich Vertex AI aktiviert
ist — im Standardfall (reiner Gemini-API-Key, kein GCP) startet der Server sauber durch.

Der lang aufgeschobene End-to-End-Test aus TASK-001 wurde nachgeholt: Der Agent antwortet
tatsaechlich ueber Gemini, sowohl im interaktiven Playground als auch per Kommandozeile — und eine
Unterhaltung bleibt ueber einen kompletten Server-Neustart hinweg erhalten (dank der bereits in
TASK-001 eingerichteten dauerhaften SQLite-Sitzungsspeicherung).

## Geänderte Dateien

- `mk34-book-agent/app/config.py` (neu) — zentrale Konfiguration (Modell-Variablen, API-Keys,
  Buchprojekt-Pfade)
- `mk34-book-agent/app/models/router.py`, `mk34-book-agent/app/models/__init__.py` (neu) —
  der Model-Router selbst
- `mk34-book-agent/app/agent.py` — Root-Agent nutzt jetzt den Router
- `mk34-book-agent/.env.example` — aktualisiertes Variablen-Schema fuer Modell-Auswahl
- `mk34-book-agent/app/fast_api_app.py` — GCP-Abhaengigkeit beim lokalen Start entfernt
  (nur noch aktiv, wenn Vertex AI tatsaechlich genutzt wird)
- `mk34-book-agent/tests/unit/test_router.py` (neu) — automatisierte Tests fuer die
  Rollen-/Modell-Zuordnung
- `mk34-book-agent/pyproject.toml`, `mk34-book-agent/uv.lock` — neue Abhaengigkeit
  (`pydantic-settings`), LiteLLM-Unterstuetzung ergaenzt

## Nächster Schritt

TASK-003 (Kontext-Store aus `basics.md`) — unabhaengig von TASK-002, wird im Anschluss in
derselben Session umgesetzt. Spaetere Plaene (Plan 2 ff.) bauen alle Agenten auf diesem Router auf;
die Claude- und Lokal-LLM-Anbindung selbst folgt erst in spaeteren Tasks (Plan 3/TASK-001).
