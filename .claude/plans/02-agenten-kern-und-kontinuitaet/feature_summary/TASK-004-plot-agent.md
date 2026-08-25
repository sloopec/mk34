# Feature-Zusammenfassung: TASK-004 — Plot Agent

## Was wurde umgesetzt

Der erste der drei Autoren-Agenten: Der Plot Agent entwickelt auf Zuruf ("Entwickle Phase 2 in
Szenen-Beats") eine vollständige, strukturierte Liste von Szenen-Beats für eine Handlungsphase —
inklusive Schauplatz, POV-Figur, Spannungslevel und Wendepunkt-Markierung. Er arbeitet zweistufig:
zuerst sammelt er den vorhandenen Kanon (Phase, bisherige Kapitel), dann formalisiert er seinen
Entwurf in ein maschinenlesbares Format. Die fertigen Beats werden automatisch und zuverlässig in
den Plot-Store geschrieben, ohne dass sich der Agent selbst darum "kümmern" muss.

Ein echter Testlauf gegen die Gemini-API hat gezeigt: Der Agent produziert plausible, im
Buch-Kanon verankerte Beats (z. B. die Diagnose-Szene bei Dr. Aris, die Vorstands-Eskalation bei
OmniCorp) und erfindet keine neuen Figuren.

## Geänderte Dateien

- `app/agents/plot_agent.py`
- `app/prompts/plot.py`
- `app/schemas.py`
- `app/tools/context_loader.py`
- `tests/unit/test_plot_tools.py`, `test_plot_agent.py`

## Nächster Schritt

TASK-005 (Character Agent) und TASK-006 (Editor Agent) — parallel geplant, nutzen dieselbe
Zweistufigkeits-Konvention (Kontext sammeln → formalisieren) bzw. binden den Character Agent
später als `AgentTool` ein. TASK-007 (Orchestrator) verdrahtet den Plot Agent erstmals über
`agents-cli run` end-to-end.
