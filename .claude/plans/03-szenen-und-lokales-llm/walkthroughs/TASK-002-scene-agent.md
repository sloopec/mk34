# Durchführungsbericht: TASK-002 — Scene Agent (Start Gemini, Ziel lokal)
Abgeschlossen: 2026-08-24T00:00:00Z

## Was wurde umgesetzt

`app/agents/scene_agent.py::create_scene_agent()` — der Agent, für den es dieses Projekt gibt.
Stufe A: Modell kommt aus `model_for("scene")` ohne `route`-Argument, was laut TASK-001 immer
auf die Cloud-Route (`MK34_MODEL_SCENE`, Start `gemini-3.1-pro-preview`) auflöst.

- Tools: `read_manuscript`, `write_scene`, `load_scene_context` (exakt wie im Task-Sketch).
- `output_key="scene_draft"` — fängt die finale Antwort in den Session-State, analog zum
  bisherigen `_SceneSlotFixture`-Platzhalter aus Plan 2/TASK-008, den TASK-003 ersetzen wird.
- Keine Safety-Callbacks/-Plugins (Kern-Use-Case-Entscheidung, per Test fixiert).
- `app/prompts/scene.py::SCENE_INSTRUCTION`: dual-mode Instruction, analog zum bereits
  etablierten Editor-Agent-Muster (`{scene_context?}`/`{scene_beat?}`/`{character_brief?}` mit
  ADKs optionaler Template-Syntax). Zwei Aufrufwege:
  - **Pipeline-Aufruf** (TASK-003): Kontext ist bereits im State gesetzt → der Agent schreibt
    NUR den Szenentext als Antwort, ruft `write_scene` bewusst NICHT selbst auf (die Pipeline
    persistiert erst nach dem Editor-Loop, `_persist_or_draft`).
  - **Direkter Aufruf** (dieser Task, `agents-cli run "Schreibe Kapitel 1, Szene 1"` ohne
    Pipeline): Kontext ist leer → der Agent lädt ihn selbst via `load_scene_context` und
    persistiert die fertige Szene selbst via `write_scene` (kein nachgelagerter Editor-Loop in
    diesem Modus).
- Der Prompt ist bewusst modellagnostisch (keine Gemini- oder llama.cpp-spezifischen Tricks),
  damit er unverändert auf `openai/supergemma4` (Stufe B, TASK-004) weiterfunktioniert.

## Live-Verifikation (InMemoryRunner, echte Gemini-API)

Da `scene_agent` in diesem Task noch nicht in den Orchestrator/die Pipeline eingehängt ist
(das ist TASK-003), wurde die Live-Verifikation -- analog zum etablierten Muster aus Plan 2
(Editor Agent, TASK-006) -- direkt gegen `create_scene_agent()` per `InMemoryRunner`
durchgeführt, nicht über `agents-cli run` gegen die volle App:

```python
agent = create_scene_agent()
runner = InMemoryRunner(agent=agent, app_name="scene_smoke")
# Prompt: "Schreibe Kapitel 1, Szene 1."
```

Ergebnis:
- Tool-Aufrufe (sichtbar im Event-Trace): `load_scene_context` → `write_scene`, in dieser
  Reihenfolge -- der Kontext-Loader-Pfad des direkten Aufrufmodus greift wie vorgesehen.
- Kapitel 1 enthielt noch keinen `scene_beats`-Eintrag in `plot_outline.json` (Plot Agent hat
  für Kapitel 1 noch keinen Beat geschrieben) -- `load_scene_context` lieferte `beat: None`,
  Weltregeln und Style Guide waren trotzdem geladen. Der Agent hat daraus plausibel eine Szene
  mit Sarah, Voss und Ronan im Labor entwickelt (thematisch konsistent mit Phase 0/1 aus
  `basics.md`), statt eine leere/Platzhalter-Antwort zu liefern.
- Sprachregister eingehalten: Sarah sagt durchgehend „Naniten" und korrigiert Ronan aktiv
  ("„Naniten“, korrigierte Sarah scharf."), Ronan sagt durchgehend „Nanobots" -- kein
  Registerbruch in der Stichprobe.
- Weltregel „kein zentraler Server" korrekt referenziert ("Es gibt keinen zentralen Server.").
- Kanonische ELI5-Metapher aus `world_bible.md` Abschnitt 5 korrekt wiederverwendet
  ("Türsteher im Gehirn, dem man einen Drink gibt").
- Kein Meta-Kommentar, keine Überschrift ("Hier ist die Szene:" o. Ä.), keine Platzhalter
  (`[TODO]`, `[Name]`) -- per `grep` gegen die geschriebene Datei verifiziert.
- `write_scene` hat den Text tatsächlich persistiert: `books/life_link/manuscript/chapter_01.md`
  wurde neu angelegt, mit `<!-- scene:1 -->`-Marker (siehe `app/tools/manuscript.py`-Format).

**Lokale Route (Stufe B) nicht live testbar:** die VM/der SSH-Tunnel läuft aktuell nicht
(siehe TASK-001-Walkthrough) -- der identische Prompt gegen `openai/supergemma4` bleibt daher
offen und wird nachgeholt, sobald die VM verfügbar ist. Der Prompt selbst enthält bewusst keine
Gemini-spezifischen Formulierungen, die das verhindern würden.

**Offene Frage #1 aus plan.md (Kreativqualität von Gemini):** die erzeugte Stichprobenszene
liest sich stilistisch stimmig (Registerhaltung, ELI5-Metapher-Wiederverwendung, kein
Info-Dump). Kein Anlass, eigenmächtig auf `MK34_MODEL_SCENE=anthropic/claude-opus-5"
umzuschalten -- bleibt eine Entscheidung für den User, falls spätere `scene-writing.json`-Läufe
(TASK-005) etwas anderes zeigen.

## Geänderte Dateien

- `app/agents/scene_agent.py` (neu)
- `app/prompts/scene.py` (neu)
- `tests/unit/test_scene_agent.py` (neu) — Struktur-/Tool-/Callback-Tests, kein Live-LLM-Aufruf
- `pyproject.toml` — codespell-Ignore-Liste um `assistent` ergänzt (deutsches Wort,
  fälschlich als "Assistant"-Tippfehler erkannt)
- `books/life_link/manuscript/chapter_01.md` (neu, aus dem Live-Smoke-Test) — die erste
  tatsächlich geschriebene Szene des Manuskripts, bewusst nicht verworfen: sie belegt das
  TASK-002-Akzeptanzkriterium "Text landet über `write_scene` im Manuskript" konkret und ist
  gleichzeitig ein echter erster Beitrag zum Buchprojekt

## Design-Entscheidungen

- Dual-Mode-Instruction statt zwei separater Agenten (Pipeline- vs. Standalone-Variante):
  konsistent mit dem bereits etablierten Editor-Agent-Muster, ein Agent-Modul reicht.
- `write_scene` bleibt als Tool auf dem Agenten (wie im Task-Sketch vorgegeben), obwohl das
  im Pipeline-Modus ein theoretisches Risiko eines vorzeitigen Schreibens birgt -- über die
  Instruction klar unterbunden ("rufe `write_scene` NICHT auf, wenn `scene_context` gesetzt
  ist"). TASK-003 verifiziert dieses Verhalten zusätzlich strukturell (Editor-Loop läuft nach
  dem Szenen-Slot, `_persist_or_draft` ist die einzige Stelle, die im Pipeline-Pfad final
  speichert).

## Verifikationsschritte

1. `uv run pytest tests/unit/test_scene_agent.py -q` — 6 Tests grün.
2. `agents-cli lint` — grün (ruff check/format, codespell, ty check).
3. Live-Smoke-Test via `InMemoryRunner` (siehe oben) — echte Gemini-API, Tool-Trajektorie,
   Registerhaltung und Persistenz alle wie erwartet.
