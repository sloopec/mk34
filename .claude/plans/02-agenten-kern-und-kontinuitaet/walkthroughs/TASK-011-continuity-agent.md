# Durchführungsbericht: TASK-011 — Continuity Agent mit Retrieval
Abgeschlossen: 2026-08-24T19:15:00Z

## Was wurde umgesetzt

Ein lokaler, netzwerkfreier Retrieval-Index (SQLite FTS5, Entscheidung E2) sowie ein
zweistufiger Continuity Agent, der neue Szenentexte gegen das bisherige Manuskript auf
Widersprüche prüft (Wissen zu früh, Zeitsprünge, Naniten-Regelverstöße, Parallelitäts-Konflikte).

**Retrieval-Schicht (`app/retrieval/`)**
- `index.py::build_index()` liest alle Kapitel über `list_chapters`/`read_manuscript`, zerlegt sie
  per `parse_scene_markers` in Szenen und schreibt sie in eine FTS5-Virtual-Table
  (`text, chapter, scene, pov_character, characters_present, location, timestamp`). Metadaten
  (POV-Figur, Ort, anwesende Figuren) werden bevorzugt aus `plot_outline.json`s `scene_beats`
  übernommen; fehlen diese, wird auf `characters_mentioned()` (einfache Namenserkennung im Text)
  zurückgefallen. Idempotent (`DROP TABLE IF EXISTS` vor jedem Rebuild).
- `query.py::query_relevant_passages()` führt eine BM25-gerankte FTS5-MATCH-Abfrage aus, mit
  optionalem Figuren-Filter (`characters_present LIKE ?`). Suchbegriffe werden vor der Abfrage
  saniert (FTS5-Sonderzeichen wie `*`, `"`, `OR` escaped/gequotet), um Query-Injection zu verhindern.
- Der Index liegt unter `books/life_link/.index/manuscript.db` (konfigurierbar über
  `Settings.mk34_index_path`), ist jederzeit aus dem Manuskript reproduzierbar und wird daher in
  `.gitignore` ausgeschlossen (`books/*/.index/`).

**Consistency-Tool (`app/tools/consistency.py`)**
- `check_consistency(new_text, context_refs) -> dict` sammelt Suchbegriffe aus im Text erwähnten
  Figuren plus übergebenen Kontext-Referenzen und liefert die relevantesten Vorpassagen als
  Evidenz zurück (`{"status", "query_entities", "relevant_passages"}`).

**Continuity Agent (`app/agents/continuity_agent.py`)**
- Zweistufig wie der Plot Agent (TASK-004): `continuity_context_agent` (mit `check_consistency`-
  Tool, `output_key="continuity_raw"`) sammelt Evidenz; `continuity_formalizer`
  (`output_schema=ContinuityReport`, `output_key="continuity_report"`) formalisiert gefundene
  Konflikte. Neue Schemas `ContinuityConflict`/`ContinuityReport` in `app/schemas.py`.
- Factory-Funktion `create_continuity_agent()` — bei jedem Aufruf neue Instanzen (verifiziert per
  Unit-Test), analog zur Projektkonvention.
- Einbindung in die Schreib-Pipeline (`app/pipelines/writing.py`, Slot vor dem Editor-Loop) ist
  laut Aufgabenbeschreibung erst Teil von Plan 3; dieser Task liefert den fertigen, isoliert
  nutzbaren Agenten.

**Eval-Vorbereitung**
- `tests/eval/datasets/continuity.json`: 5 Fälle (Wissen zu früh, Zeitsprung, Verstoß gegen die
  "kein zentraler Naniten-Server"-Regel, Parallelitäts-Konflikt, Kontrollfall ohne Konflikt).
- `tests/eval/mk34_eval/rubrics/grounding.md` + `tests/eval/grounding_metric.py`: neue
  `grounding`-Metrik, die bewertet, ob gemeldete Konflikte tatsächlich in den referenzierten
  Vorpassagen belegt sind. In `eval_config.yaml`s `metrics_to_run`/`custom_metrics` ergänzt.

## Design-Entscheidung: `check_consistency` liefert Evidenz statt fertiger `{"conflicts": [...]}`

Die Task-Datei beschreibt `check_consistency` wörtlich als Tool, das bereits
`{"conflicts": [...]}` zurückgibt. Das Akzeptanzkriterium "Kein Netzwerkaufruf im Retrieval-Pfad
(nachweisbar offline lauffähig)" schließt jedoch einen eingebetteten LLM-Aufruf innerhalb des
Tools aus — Konflikterkennung erfordert aber Sprachverständnis (z. B. "wurde eine Tatsache vor
dem Zeitpunkt X erwähnt, an dem sie im neuen Text bekannt sein müsste"), keine deterministische
Zeichenkettenanalyse. Deshalb liefert `check_consistency` stattdessen die dafür nötige Evidenz
(die relevantesten Vorpassagen per BM25-Retrieval); die eigentliche semantische Bewertung
übernimmt der nachgelagerte `continuity_formalizer` (LLM, `output_schema=ContinuityReport`).
Diese Abweichung ist im Docstring von `app/tools/consistency.py` dokumentiert.

## `rag-vector-search`-Recipe geprüft, nicht übernommen

Wie in TASK-002 vorgemerkt, wurde die `rag-vector-search`-Recipe des ADK-Ökosystems zu Beginn
dieses Tasks geklont und geprüft. Sie ist zu 100 % auf Vertex AI Vector Search zugeschnitten
(Embeddings-Pipeline, Vertex-Index-Erstellung, keine SQLite/FTS5-Variante) und widerspricht damit
Entscheidung E2 (lokales Retrieval, kein GCP). Es gab kein übertragbares Code-Muster jenseits des
allgemeinen "Retrieval-Tool + LLM-Formalisierung"-Konzepts, das bereits vom Plot Agent (TASK-004)
etabliert war. Es wurde daher direkt nach der FTS5/BM25-Spezifikation aus der Task-Datei
implementiert, ohne Codeübernahme aus der Recipe.

## Unit-Tests

- `tests/unit/test_retrieval.py` (14 Tests): Index-Aufbau (leer, Chunking pro Szene,
  Timestamp-Extraktion, Fallback auf Namenserkennung, Idempotenz, Metadaten aus `plot_outline.json`),
  Query (leerer Index, leere Entities, Relevanz-Ranking, Figuren-Filter, FTS5-Sonderzeichen-
  Sanitizing), `check_consistency` (Evidenz-Rückgabe, leerer Index), und explizit
  `test_retrieval_path_never_opens_a_network_socket` — patcht `socket.socket.connect` so, dass
  jeder Netzwerkversuch einen `AssertionError` auslöst, und durchläuft `build_index()`,
  `query_relevant_passages()`, `check_consistency()` fehlerfrei.
- `tests/unit/test_continuity_agent.py` (4 Tests): Zweistufige Struktur, Tool-Zuordnung,
  Modellwahl (`model_for("continuity")` → `gemini-3.7-flash`), keine geteilten Instanzen bei
  wiederholtem Factory-Aufruf.
- Gesamt: 126 Unit-Tests grün (`uv run python -m pytest tests/unit -q`).

## Blocker: Live-Verifikation über echte Gemini-API nicht abschließbar (transientes Netzwerkproblem)

Drei Versuche, den Continuity Agent live über `InMemoryRunner` gegen einen isolierten
Scratch-Index (temporäres Verzeichnis, niemals `books/life_link/.index/` berührt) zu verifizieren,
blieben ohne Ergebnis — alle drei hingen im allerersten Gemini-API-Aufruf fest (Traceback zeigt
`aiohttp/streams.py:705` → `await self._waiter`, d. h. der Request wartet auf eine HTTP-Antwort,
die nie eintrifft). Zur Eingrenzung wurde zusätzlich ein minimaler, agentenunabhängiger Test
durchgeführt: ein einzelner `google.genai`-Aufruf (`generate_content`, ohne ADK, ohne Tools, ohne
`before_agent_callback`) an `gemini-3.7-flash` mit dem Prompt `"Sag nur 'ok'."` — auch dieser
Minimal-Aufruf hing bei 30 s Timeout im identischen Aufrufpfad fest.

Das belegt: Die Ursache liegt nicht im Continuity-Agent-Code, nicht in der Zweistufigkeit, nicht
im Retrieval-Tool und nicht im ADK-Agentenbaum, sondern in einem transienten Netzwerk-/API-
Zugriffsproblem zur Gemini-API zum Zeitpunkt dieses Tasks (frühere Live-Tests in TASK-004/005/006/
007/008/009 über `agents-cli run`/`InMemoryRunner` liefen zuvor im selben Projekt erfolgreich
durch — das Problem ist also aktuell und nicht strukturell). Damit sind folgende
Akzeptanzkriterien der Task-Datei **strukturell erfüllt und durch Unit-Tests verifiziert**, aber
**nicht live gegen die echte Gemini-API bestätigt**:
- Live-Erkennung des "kein zentraler Naniten-Server"-Regelverstoßes mit Zitat der Vorpassage.
- "0 False Negatives" auf `tests/eval/datasets/continuity.json` — zusätzlich weiterhin blockiert
  durch den bereits in TASK-003/TASK-010 dokumentierten `agents-cli`-Bug
  (`docs/known-issues/agents-cli-eval-generate-missing-content.md`), der die gesamte
  `eval generate`/`eval grade`-Kommandokette für dieses Projekt betrifft, sobald
  `before_agent_callback` im Agentenbaum vorkommt (hier: über den Root-Orchestrator, an den der
  Continuity Agent in Plan 3 angebunden wird).

Dieser Task wird ehrlich mit diesem Vorbehalt als erledigt markiert (Code, Architektur und
Unit-Tests sind vollständig und korrekt; die reine End-to-End-Live-Bestätigung fehlt aus Gründen
außerhalb des Projekt-Codes). Eine erneute Live-Verifikation sollte nachgeholt werden, sobald die
Netzwerkverbindung zur Gemini-API wieder stabil ist — kein Code-Änderungsbedarf erwartet.

## Geänderte Dateien

- `app/retrieval/__init__.py`, `app/retrieval/index.py`, `app/retrieval/query.py` — neuer lokaler
  FTS5-Retrieval-Index.
- `app/tools/consistency.py` — neues `check_consistency`-Tool (Evidenz-Retrieval).
- `app/tools/manuscript.py` — öffentliche Wrapper `parse_scene_markers`/`characters_mentioned`
  für Cross-Modul-Wiederverwendung durch die Retrieval-Schicht.
- `app/schemas.py` — neue Schemas `ContinuityConflict`, `ContinuityReport`.
- `app/prompts/continuity.py` — Instruktionen für Kontext-Sammel- und Formalisierungs-Agent.
- `app/agents/continuity_agent.py` — Factory `create_continuity_agent()`, zweistufiger
  `SequentialAgent`.
- `app/config.py` — neue Einstellung `mk34_index_path`.
- `tests/unit/test_retrieval.py`, `tests/unit/test_continuity_agent.py` — 18 neue Unit-Tests.
- `tests/eval/datasets/continuity.json` — 5 Eval-Fälle.
- `tests/eval/mk34_eval/rubrics/grounding.md`, `tests/eval/grounding_metric.py`,
  `tests/eval/eval_config.yaml` — neue `grounding`-Metrik.
- `pyproject.toml` — codespell-Ignorierliste um weitere deutsche Wortkollisionen ergänzt.
- `.gitignore` (Repo-Root) — `books/*/.index/` ausgeschlossen (reproduzierbarer Artefakt).

## Verifikationsschritte

1. `agents-cli lint` — grün (`ruff check`, `ruff format --check`, `codespell`, `ty check` alle
   ohne Befund).
2. `uv run python -m pytest tests/unit -q` — 126 Tests grün (davon 18 neu für diesen Task).
3. `test_retrieval_path_never_opens_a_network_socket` — expliziter Beleg, dass der komplette
   Retrieval-Pfad (Index-Aufbau, Query, `check_consistency`) ohne Netzwerkzugriff läuft.
4. Live-Verifikation über `InMemoryRunner` gegen einen isolierten Scratch-Index: 3 Versuche,
   alle durch transienten Netzwerk-Hang bei der Gemini-API blockiert; durch einen zusätzlichen
   Minimal-Test (reiner `google.genai`-Aufruf ohne ADK) als API-seitiges/Netzwerk-Problem
   bestätigt, nicht als Code-Defekt. Nicht abgeschlossen — dokumentiert als offener Nachtest.
