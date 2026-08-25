"""mk34 Autoren-Agenten: Plot, Character, Editor (Plan 2).

Jedes Modul exportiert eine `create_x_agent()`-Factory -- Factory-Funktionen
werden aufgerufen (`create_plot_agent()`), nicht referenziert, damit
Sub-Agent-Baeume nicht denselben Agenten-Instance mehrfach referenzieren
("agent already has a parent").
"""
