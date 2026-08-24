# Durchführungsbericht: TASK-007 — Orchestrator als Coordinator-Root-Agent
Abgeschlossen: 2026-08-24T15:00:00Z

## Was wurde umgesetzt

`app/agent.py`s `root_agent` wurde vollständig vom TASK-003-Interims-Scaffold (Wetter-Agent plus
angeflanschte Kontext-Loader-Tools) auf den Orchestrator umgestellt:

```python
root_agent = Agent(
    name="orchestrator",
    model=_wrap_model(model_for("orchestrator")),
    sub_agents=[create_plot_agent(), create_editor_agent()],
    tools=[AgentTool(create_character_agent()), list_chapters, chapter_stats, load_plot_outline],
    before_agent_callback=initialize_state,
)
```

Zwei Einbindungsarten bewusst getrennt: `sub_agents` (Plot, Editor — dürfen den ganzen Turn
übernehmen) vs. `AgentTool` (Character — wird konsultiert, Orchestrator behält die Kontrolle). Die
Instruction (`app/prompts/orchestrator.py`) verpflichtet den Orchestrator explizit, selbst
keinen kreativen Text zu schreiben, und legt die Routing-Regeln fest.

**Zusätzlich zum in der Task-Datei skizzierten Tool-Set** wurde `load_plot_outline` aufgenommen
(siehe Design-Entscheidungen) — rein faktische Plot-Nachfragen sollen als Nachschlagen
beantwortet werden, nicht über eine Delegation an den Plot Agent, der als Nebenwirkung
spekulative Beats persistieren würde.

## Geänderte Dateien

- `app/agent.py` (root_agent vollständig ersetzt)
- `app/prompts/orchestrator.py` (neu)
- `app/prompts/editor.py` (Bugfix, siehe unten)
- `tests/unit/test_orchestrator.py` (neu)

## Ein während der Live-Verifikation gefundener und gefixter Bug

Der Live-Test "Überarbeite diesen Text: ..." deckte auf: Der Orchestrator delegiert korrekt per
Sub-Agent-Transfer an `editor_agent` (`transfer_to_agent` sichtbar im `-v`-Output,
`nodeInfo.path: "orchestrator@1/editor_agent@1"`), aber `editor_agent` scheiterte danach mit
`KeyError: 'Context variable not found: \`scene_draft\`.'` — die TASK-006-Instruction
referenzierte `{scene_draft}` (ohne `?`, also nicht optional). Das funktioniert innerhalb der
künftigen Schreib-Pipeline (TASK-008, wo ein vorheriger Schritt `state["scene_draft"]` setzt),
bricht aber bei direkter Delegation via Chat, wo der Text nur in der User-Nachricht steht und
`scene_draft` im State leer ist.

**Fix:** `{scene_draft?}` und `{scene_context?}` (beide optional per ADKs `?`-Suffix), plus eine
explizite Anweisung in der Instruction, bei leerem State-Wert den Text aus dem zuletzt genannten
User-Prompt zu nehmen. Nach dem Fix lief derselbe Prompt fehlerfrei durch den Orchestrator zum
Editor und lieferte ein korrektes Verdikt.

Das ist eine Nachbesserung an TASK-006, ausgelöst durch die hier in TASK-007 erstmals mögliche
End-to-End-Verifikation über den echten Routing-Pfad — nicht Scope-Creep, sondern der in der
Eval-/Iterations-Konvention vorgesehene Fall "Instruction fixen, wenn ein echter Lauf einen Fehler
aufdeckt".

## Design-Entscheidungen

**`load_plot_outline` zusätzlich zum Orchestrator-Tool-Set.** Ohne dieses Tool hätte "Fasse Phase
2 des Plots zusammen" (TASK-003/`basic-dataset.json`) entweder an den generativen Plot Agent
delegiert werden müssen (der als Nebenwirkung immer neue, spekulative Beats nach
`plot_outline.json` schreibt — falsch für eine reine Zusammenfassungs-Anfrage) oder gar nicht
beantwortbar gewesen sein. Ein zusätzliches Read-Only-Tool ist die sauberere Lösung und
widerspricht keinem Akzeptanzkriterium dieses Tasks.

**Store-Verschmutzung durch Live-Tests konsequent zurückgesetzt.** Wie in TASK-004 hat der
"Entwickle Akt 2"-Testlauf reale, testgenerierte Beats nach `books/life_link/store/plot_outline.json`
geschrieben (der `after_agent_callback` aus TASK-004 arbeitet erwartungsgemäß deterministisch,
auch hier). Jeweils per `git checkout -- books/life_link/store/plot_outline.json` rückgängig
gemacht.

## Verifikationsschritte

1. `uv run pytest tests/unit/test_orchestrator.py -q` → 6 passed.
2. `uv run pytest tests/unit -q` (Gesamtsuite) → 97 passed, keine Regression.
3. `uv run --env-file .env pytest tests/integration/test_agent.py -q` → 1 passed (generische
   Frage "Why is the sky blue?" wird vom Orchestrator direkt beantwortet, ohne Delegation nötig).
4. `agents-cli lint` → `ruff check`, `ruff format --check`, `codespell`, `ty check` alle grün.
5. `agents-cli run "Entwickle Akt 2" -v` → Delegation an `plot_agent` sichtbar
   (`nodeInfo.path: "orchestrator@1/plot_agent@1"`), vollständige, kanon-konsistente Beat-Liste
   im `stateDelta.plot_beats`. Store-Schreibzugriff anschließend zurückgesetzt.
6. `agents-cli run "Ueberarbeite diesen Text: David starrte Elena an. Er sagte, dass die Naniten
   jetzt ein Mesh-Netzwerk bilden wuerden." -v` — **erster Versuch**: `KeyError` (siehe Bugfix
   oben); **nach Fix**: Delegation an `editor_agent` sichtbar
   (`nodeInfo.path: "orchestrator@1/editor_agent@1"`), Verdikt `"grade": "pass"` mit korrekt
   behobenem Registerverstoß ("Naniten" → "Nanobots") und dokumentiertem `issues`-Log.
7. `initialize_state` als `before_agent_callback` bestätigt (`test_root_agent_has_initialize_state_callback`)
   — kein `KeyError` auf `book_slug`/`active_chapter`/`active_scene`/`scene_context` in beiden
   Live-Läufen.
