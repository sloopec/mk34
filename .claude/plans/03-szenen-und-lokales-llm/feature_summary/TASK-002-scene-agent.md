# Feature-Zusammenfassung: TASK-002 — Scene Agent (Start Gemini, Ziel lokal)

## Was wurde umgesetzt

Das System kann jetzt tatsächlich Szenentext schreiben: der neue Scene Agent nimmt Beat,
Figuren-Brief und Weltregeln entgegen und liefert eine ausformulierte Szene im korrekten
Sprachregister der beteiligten Figuren, ohne Meta-Kommentar oder Platzhalter. Er startet auf
Gemini (`gemini-3.1-pro-preview`), ist aber so formuliert, dass derselbe Prompt später ohne
Anpassung auch mit dem lokalen, unzensierten Modell funktioniert (TASK-004).

Ein Live-Test hat den Agenten direkt (noch außerhalb der vollständigen Schreib-Pipeline)
angewiesen, „Kapitel 1, Szene 1" zu schreiben. Das Ergebnis ist die erste tatsächlich
geschriebene Szene des Buchs (`books/life_link/manuscript/chapter_01.md`) — eine Labor-Szene
mit Sarah, Voss und Ronan, die die kanonische Terminologie (Sarah: „Naniten", Ronan:
„Nanobots") und eine bereits im Weltenbau-Dokument hinterlegte Metapher korrekt einsetzt,
obwohl für dieses Kapitel noch kein expliziter Plot-Beat vorlag.

## Geänderte Dateien

- `mk34-book-agent/app/agents/scene_agent.py` (neu)
- `mk34-book-agent/app/prompts/scene.py` (neu)
- `mk34-book-agent/tests/unit/test_scene_agent.py` (neu)
- `mk34-book-agent/pyproject.toml`
- `books/life_link/manuscript/chapter_01.md` (neu, erste geschriebene Szene)

## Nächster Schritt

TASK-003 hängt den Scene Agent in den bereits vorbereiteten Szenen-Slot der Schreib-Pipeline
ein und ersetzt damit das Platzhalter-Fixture aus Plan 2 — ab dann läuft „Schreibe Kapitel N,
Szene M" als vollständige Kette (Kontext → Beat → Figuren-Brief → Szene → Kontinuitätsprüfung
→ Lektorats-Schleife → finales Speichern) end-to-end über den Orchestrator.
