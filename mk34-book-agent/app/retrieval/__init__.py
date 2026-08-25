"""mk34 lokales Retrieval (Entscheidung E2, TASK-011).

Stufe 1 (hier gebaut): SQLite FTS5 mit BM25-Ranking ueber Szenen-Chunks,
stdlib `sqlite3`, kein Netzwerkaufruf. Stufe 2 (hybrides Retrieval mit
`sqlite-vec` + lokalem Embedding-Modell) wird nur gebaut, falls die
Recall-Schwelle auf `continuity.json` unterschritten wird -- siehe
`.claude/plans/02-agenten-kern-und-kontinuitaet/tasks/TASK-011-continuity-agent.md`.

`index.py` -- Ingestion (Index aus dem Manuskript aufbauen).
`query.py` -- Query (Metadaten-Filter + BM25-Volltext).
"""
