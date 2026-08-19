# TASK-011: Continuity Agent mit Retrieval
Status: ⏳ ausstehend
Abhängig von: [TASK-010]
Parallel: nein
*(vormals TASK-015 im Gesamtplan)*

## Beschreibung
Faktencheck neuer Szenen gegen das bisherige Manuskript.

**Wichtige Korrektur gegenueber dem Originalplan:** Der Agent liest **nicht** „das gesamte bisherige Manuskript". Bei 30+ Kapiteln sprengt das jedes Kontextfenster und Budget. Stattdessen Retrieval:

1. Neue Szene wird gechunkt (Chunk-Grenze = Szene, nicht fixe Tokenzahl).
2. Retrieval der k relevantesten Vorpassagen zu den beteiligten Figuren/Orten/Fakten.
3. Pruefung gegen diese Treffer + `timeline.json` + `knowledge_state` der Figuren.

**Entscheidung E2: Retrieval laeuft lokal.** Kein Vertex AI Vector Search, keine Cloud-Ingestion — der Stoff verlaesst die Maschine nicht, und der Korpus ist klein (ein Roman ≈ 200–400 Szenen-Chunks).

**Stufe 1 — Baseline, in diesem Task zu bauen:** SQLite **FTS5** mit BM25-Ranking.
- Index unter `MK34_INDEX_PATH` (`books/life_link/.index/manuscript.db`), **gitignored**, jederzeit aus dem Manuskript rebuildbar.
- Chunk-Grenze = **Szene**. Jeder Chunk traegt `chapter`, `scene`, `pov_character`, `characters_present`, `location`, `timestamp`.
- Query = Metadaten-Filter (beteiligte Figuren/Ort aus dem neuen Beat) **plus** BM25-Volltext ueber die Entitaeten der neuen Szene.
- Stdlib-`sqlite3`, keine zusaetzliche Infrastruktur, Unicode61-Tokenizer fuer Deutsch.

**Stufe 2 — nur bauen, wenn Stufe 1 die Recall-Schwelle auf `continuity.json` reisst:** hybrides Retrieval mit `sqlite-vec` im selben DB-File plus lokalem Embedding-Modell (mehrsprachig, z. B. `bge-m3` oder `multilingual-e5` via `sentence-transformers`), Fusion per Reciprocal Rank. **Nicht** das Generierungsmodell fuer Embeddings zweckentfremden.

Vom Recipe `core/python/rag-vector-search` werden nur die **Chunking- und Query-Muster** uebernommen, nicht die Infrastruktur (`infra/terraform/`, KFP-Ingestion):

```bash
[ -d /tmp/adk-samples ] || git clone --filter=blob:none --depth 1 --sparse \
  https://github.com/google/adk-samples /tmp/adk-samples
cd /tmp/adk-samples && git sparse-checkout add core/python/rag-vector-search
cat core/python/rag-vector-search/AGENTS.md
```

**Agent:**
- Modell: `model_for("continuity")` → Start `gemini-3.7-flash` (E6); spaeter `anthropic/claude-sonnet-5`
- Tool: `check_consistency(new_text: str, context_refs: list[str]) -> dict` mit `{"conflicts": [{"type", "evidence", "reference", "severity"}]}`
- Einbindung als `AgentTool` (in Plan 3 in der Pipeline vor dem Editor-Loop)

Bei gefundenem Konflikt wird die Szene **nicht** geschrieben — Konfliktliste raus, Autor entscheidet.

Da in diesem Plan noch kein Szenentext generiert wird, laeuft die Continuity-Pruefung hier gegen Fixture-Szenen (inkl. der absichtlich fehlerhaften aus `continuity.json`). Die Pipeline-Integration folgt mit dem Szenen-Schritt in Plan 3.

## Akzeptanzkriterien
- [ ] SQLite-FTS5-Index wird aus dem Manuskript reproduzierbar aufgebaut (`make index` o. Ae.), Index ist gitignored
- [ ] Chunk-Grenze ist die Szene; alle Metadatenfelder sind pro Chunk gesetzt
- [ ] Query kombiniert Metadaten-Filter und BM25; Treffer enthalten `chapter`/`scene`-Referenz
- [ ] Kein Netzwerkaufruf im Retrieval-Pfad (nachweisbar offline lauffaehig)
- [ ] `check_consistency` liefert Konflikte mit Referenz auf die widersprechende Vorpassage
- [ ] Der Agent behauptet keine Fakten ohne Tool-Beleg (`grounding`-Metrik ≥ 4/5)
- [ ] `tests/eval/datasets/continuity.json` mit absichtlich eingebauten Widerspruechen erkennt 100 % der Faelle (0 False Negatives)
- [ ] Recall von Stufe 1 ist gemessen und dokumentiert; Stufe 2 wird nur bei Unterschreitung gebaut (Entscheidung im Plan vermerken)

## Betroffene Dateien
- `app/agents/continuity_agent.py`
- `app/tools/consistency.py`
- `app/retrieval/index.py` (FTS5-Ingestion), `app/retrieval/query.py`
- `.gitignore` (`books/life_link/.index/`)
- `tests/eval/datasets/continuity.json`
- `tests/unit/test_retrieval.py`
