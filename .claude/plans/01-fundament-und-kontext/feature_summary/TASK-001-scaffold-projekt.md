# Feature-Zusammenfassung: TASK-001 — Projekt mit agents-cli scaffolden (Prototype)

## Was wurde umgesetzt

Das ADK-Agentenprojekt wurde als eigenständiges Verzeichnis `mk34-book-agent/` im Repo-Root
per `agents-cli scaffold create --agent adk --prototype --agent-guidance-filename CLAUDE.md`
erzeugt — bewusst kein handgebautes Setup, damit Eval-Boilerplate, Manifest, FastAPI-App,
Dockerfile und Projektkonventionen aus einer Hand kommen. Das Projekt bleibt getrennt von
`books/` und `docs/`, die weiterhin im Repo-Root liegen (siehe Entscheidung unten).

Die Session-Persistenz wurde direkt beim Setup auf `DatabaseSessionService` (SQLite) umgestellt,
statt wie vom Scaffold vorgesehen bei `InMemorySessionService` zu bleiben. Das ist eine bewusste
Vorentscheidung für spätere Phasen: eine Session soll über mehrere `agents-cli run`-Aufrufe
und Tage hinweg erhalten bleiben, und die Grundlage für Session-Rewind (spätere Phase) soll
nicht erst nachträglich migriert werden. Dabei zeigte sich, dass die installierte ADK-Version
einen asynchronen Datenbanktreiber verlangt statt des im Plan ursprünglich genannten
synchronen — das wurde entsprechend korrigiert (gleiche Datei, gleicher Pfad, anderer Treiber),
inklusive automatischer Anlage des Datenverzeichnisses beim ersten Zugriff.

Die Beispielkonfiguration (`.env.example`) wurde um alle im Plan vorgesehenen Umgebungsvariablen
ergänzt (Modell-Auswahl, Buchprojekt-Pfade, Eval-Judge-Modelle, Retrieval-Index,
Session-Datenbank) — auch die, deren Verdrahtung erst in späteren Tasks folgt.

**Offen geblieben und bewusst verschoben:** Der Nachweis, dass der Agent tatsächlich über die
Kommandozeile antwortet und eine Session einen Prozess-Neustart übersteht, konnte in dieser
Umgebung nicht geführt werden, weil kein Modell-Zugangsschlüssel verfügbar war. Diese
Prüfung wird nachgeholt, sobald im nächsten Task der Agent auf das Zielmodell (Claude)
umgestellt ist. Ersatzweise wurde die Session-Speicherung direkt auf Code-Ebene überprüft und
nachgewiesen, dass eine Sitzung tatsächlich einen Prozessneustart übersteht.

## Entscheidung zum Buch-Datenverzeichnis (vormals offene Frage)

Es wurde festgelegt, dass die Buchinhalte (`books/life_link/`) dauerhaft außerhalb des
Agentenprojekts im Repo-Root verbleiben — eine klare Trennung von Code und Inhalt. Werkzeuge,
die später auf Manuskript und Kontext zugreifen, verweisen relativ auf dieses Verzeichnis.

## Geänderte Dateien

- `mk34-book-agent/` (neu, generiert von `agents-cli scaffold create`)
- `mk34-book-agent/app/app_utils/services.py` — `DatabaseSessionService` (SQLite) statt `InMemorySessionService`
- `mk34-book-agent/pyproject.toml` — `google-adk[gcp,otel-gcp,db]`, `greenlet`
- `mk34-book-agent/.env.example` — vollständiger `MK34_*`-Variablensatz
- `mk34-book-agent/.gitignore` — `data/` ergänzt

## Nächster Schritt

Der Modell-Router (TASK-002): Umstellung von den Google-Standardmodellen auf Claude über LiteLLM
sowie Anbindung des lokalen, unzensierten Modells — inklusive Nachholen des in TASK-001
verschobenen Live-Tests.
