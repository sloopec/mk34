# Durchführungsbericht: TASK-005 — Character Agent und Figuren-Tools
Abgeschlossen: 2026-08-24T13:30:00Z

## Was wurde umgesetzt

Vier Figuren-Tools in `app/tools/characters.py` gegen `store/characters.json`:

- `get_character(name)` — vollständiges Figurenprofil.
- `update_character(name, development)` — hängt idempotent an ein neues `development_log`-Feld
  an, überschreibt nie das bestehende `arc`-Feld.
- `get_character_arc(name)` — `arc` plus `development_log`.
- `get_knowledge_state(name, chapter)` — liefert das vorhandene `knowledge_state`-Fließtextfeld;
  echtes kapitelweises Tracking kommt erst mit TASK-012 (im Docstring vermerkt).

Der Character Agent (`app/agents/character_agent.py`) ist ein einstufiger `Agent` mit allen vier
Tools, gedacht zur Einbindung als `AgentTool` in Orchestrator/Editor (TASK-007) — er übernimmt nie
den ganzen Turn, sondern liefert einen kompakten Figuren-Brief (Register, Motivation,
Wissensstand, Dialogvorschläge, innere Konflikte) zurück. Die Instruction verpflichtet ihn
explizit, zu widersprechen, wenn eine angefragte Szene der Figur Wissen unterstellt, das sie laut
`knowledge_state` zu diesem Zeitpunkt nicht haben kann.

## Geänderte Dateien

- `app/tools/characters.py` (neu)
- `app/agents/character_agent.py` (neu)
- `app/prompts/character.py` (neu)
- `tests/unit/test_character_tools.py`, `test_character_agent.py` (neu)
- `pyproject.toml` (codespell-Ausnahmeliste erweitert)

## Design-Entscheidungen

**`update_character` schreibt in ein separates `development_log`-Feld statt `arc` zu
überschreiben.** `arc` ist der aus `basics.md` extrahierte kanonische Entwicklungsbogen (Plan
1/TASK-003) — ihn zu überschreiben würde Kanon durch Laufzeit-Beobachtungen ersetzen. Ein
zusätzliches Log-Feld trennt "was der Kanon vorsieht" von "was während des Schreibens tatsächlich
passiert ist", ohne Informationsverlust.

**Live-Verifikation der `AgentTool`-Einbindung über einen minimalen Wrapper-Agenten, nicht über
`root_agent`.** Wie bei TASK-004: `root_agent` bleibt bis TASK-007 unverändert. Ein einmaliger
`Agent(tools=[AgentTool(create_character_agent())])` wurde per `InMemoryRunner` gegen die echte
Gemini-API getestet, um sowohl den sichtbaren Tool-Call (Akzeptanzkriterium: "Tool-Call im
`-v`-Output sichtbar") als auch die inhaltliche Qualität des Figuren-Briefs nachzuweisen.

## Verifikationsschritte

1. `uv run pytest tests/unit/test_character_tools.py tests/unit/test_character_agent.py -q` →
   12 passed.
2. `uv run pytest tests/unit -q` (Gesamtsuite) → 85 passed, keine Regression.
3. `agents-cli lint` → `ruff check`, `ruff format --check`, `codespell`, `ty check` alle grün.
4. Live-Smoke-Test (`InMemoryRunner`, echte Gemini-API, minimaler Wrapper-Agent mit
   `AgentTool(create_character_agent())`), Prompt: "Wie reagiert David in Kapitel 1, wenn seine
   Frau von 'Naniten' statt 'Nanobots' spricht?" — Ergebnis:
   - Sichtbarer Tool-Call `character_agent` mit dem weitergereichten Request (Nachweis für
     `AgentTool`-Delegation).
   - Figuren-Brief korrekt im Laien-Register ("Nanobots", "Chips"), mit explizitem
     Wissensstand-Hinweis ("David ist in Kapitel 1 / Phase 1 noch absolut ahnungslos") — der Agent
     erkennt und benennt damit korrekt den Terminologie-/Wissenskonflikt, den der Prompt
     unterstellt.
   - Keine Schreibzugriffe auf `books/life_link/store/` in diesem Szenario (reine
     Lese-Tool-Aufrufe), daher keine Store-Bereinigung nötig.
