"""mk34 lokale Eval-Judge-Bibliothek (Plan 2, TASK-003).

Provider-agnostisch: `judge.judge(rubric, prompt, response, agent_data)`
loest das Modell aus dem `tier`-Feld der Rubrik auf (`app.config.get_settings`)
und waehlt den Provider anhand des Modell-Prefixes (`gemini-*` ->
`google-genai`, `claude-*` -> `anthropic`). Siehe Entscheidung E1 (Grading
laeuft vollstaendig lokal) und E4 (zweistufiger Judge: fast/craft).
"""
