# Feature-Zusammenfassung: TASK-006 — Editor Agent (Lektorat)

## Was wurde umgesetzt

Der dritte und letzte Autoren-Agent: Der Editor liest einen Rohtext und liefert eine
überarbeitete Fassung samt strukturiertem Urteil ("fertig" oder "braucht Überarbeitung", plus
Liste der gefundenen/behobenen Probleme). Er greift dabei niemals in die Handlung ein — nur in
Sprache, Stil und Tempo. Ein `QualityChecker` daneben entscheidet automatisch, wann eine spätere
Überarbeitungsschleife (TASK-008) aufhören darf: sobald der Editor "fertig" sagt.

Ein echter Testlauf mit einem absichtlich fehlerhaften Text (eine Laienfigur benutzt
fälschlicherweise Fachvokabular) hat gezeigt: Der Editor erkennt den Fehler zuverlässig, behebt
ihn mit einer passenden, laienverständlichen Formulierung und dokumentiert genau, was er warum
geändert hat — ohne die eigentliche Szene zu verändern.

## Geänderte Dateien

- `app/agents/editor_agent.py`
- `app/agents/quality_checker.py`
- `app/prompts/editor.py`
- `tests/unit/test_editor_agent.py`

## Nächster Schritt

TASK-007 (Orchestrator) — führt Plot Agent und Editor Agent als delegierbare Sub-Agenten sowie
den Character Agent als Werkzeug zusammen. Damit steht erstmals ein `root_agent`, gegen den sich
`agents-cli run`/`playground` sinnvoll testen lässt.
