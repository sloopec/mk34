# TASK-009: Smoke-Test und Lint
Status: ⏳ ausstehend
Abhängig von: [TASK-008]
Parallel: nein
*(vormals TASK-007 im Gesamtplan — ohne Szenen-Prompts und ohne den VM-Check; beides liegt in Plan 3)*

## Beschreibung
Verifizieren, dass das Multi-Agenten-Geruest laeuft — bevor die Multi-Agent-Eval aufgesetzt wird.

```bash
agents-cli lint
agents-cli run "Wer ist Dr. Elias Voss und was ist seine Rolle?" -v
agents-cli run "Entwickle Phase 2 in Szenen-Beats" -v
agents-cli run "Ueberarbeite diesen Absatz: <Fixture-Auszug aus Szene E>" -v
agents-cli playground        # interaktive Durchsicht der Delegation
```

`-v` gibt die vollstaendigen Event-JSONs aus — damit pruefen, ob die Tools tatsaechlich aufgerufen werden und mit welchen Argumenten (haeufigster Frueh-Fehler: das Modell erfindet Kontext statt die Loader-Tools aufzurufen), und ob die Delegation beim richtigen Sub-Agent landet.

Dies ist ein Smoke-Test, **kein** Verhaltenstest. Keine pytest-Assertions auf LLM-Textinhalte.

Der Check „lokale VM nicht erreichbar → klare Fehlermeldung" entfaellt hier — das lokale LLM wird erst in `szenen-und-lokales-llm/TASK-001` angebunden und dort geprueft.

## Akzeptanzkriterien
- [ ] `agents-cli lint` ist gruen
- [ ] `uv run pytest` (Unit-Tests aus TASK-001/002/008 sowie Plan 1) ist gruen
- [ ] Alle drei `agents-cli run`-Prompts liefern plausible Antworten ueber den jeweils richtigen Sub-Agent
- [ ] Im `-v`-Output sind die erwarteten Tool-Calls mit korrekten Argumenten sichtbar
- [ ] `agents-cli playground` startet und die Delegation ist nachvollziehbar

## Betroffene Dateien
- keine Codeaenderung erwartet; ggf. Fixes an `app/prompts/*`, `app/tools/*`
