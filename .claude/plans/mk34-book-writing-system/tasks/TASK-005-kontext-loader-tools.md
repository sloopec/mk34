# TASK-005: Kontext-Loader-Tools
Status: ⏳ ausstehend
Abhängig von: [TASK-003]
Parallel: ja

## Beschreibung
FunctionTools, die den Story-Kanon in den Agenten-Kontext holen — `app/tools/context_loader.py`.

- `load_world_bible() -> dict` — Naniten-Regeln und Weltenbau
- `load_style_guide() -> dict` — Sprachregister pro Figur, Ton, POV-Regeln
- `load_plot_outline(act: int) -> dict` — Beats fuer einen Akt/eine Phase
- `load_scene_context(chapter: int, scene: int) -> dict` — kombinierter Kontext: Beat + beteiligte Figuren + relevante Weltregeln + Stilprofil

`load_scene_context` ist die Hauptschnittstelle fuer die Pipeline und schreibt sein Ergebnis via `output_key="scene_context"` in den State, damit nachgelagerte Agenten es per `{scene_context}` in der Instruction injizieren koennen.

Wichtig: der State wird ueber ein `before_agent_callback` vorinitialisiert, damit `{scene_context}` beim ersten Turn nicht mit `KeyError` bricht.

Bei grossem Kanon: `ContextCacheConfig` am `App` erwaegen, damit die stabilen Teile (World Bible, Style Guide) nicht in jedem Turn neu bezahlt werden.

## Akzeptanzkriterien
- [ ] Alle vier Tools implementiert, dict-Return, Docstrings
- [ ] `load_scene_context` liefert Beat, Figurenliste inkl. Sprachregister und die anwendbaren Weltregeln in einem Aufruf
- [ ] `initialize_state`-Callback setzt `book_slug`, `active_chapter`, `active_scene`, `scene_context` auf Defaults
- [ ] Kein `KeyError` beim ersten Turn im Playground
- [ ] pytest deckt die Loader gegen den Fixture-Store ab

## Betroffene Dateien
- `app/tools/context_loader.py`
- `app/callbacks.py`
- `tests/unit/test_context_loader.py`
