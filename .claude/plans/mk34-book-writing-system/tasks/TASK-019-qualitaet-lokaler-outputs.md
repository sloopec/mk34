# TASK-019: Qualitaetssicherung fuer lokale Outputs
Status: ⏳ ausstehend
Abhängig von: [TASK-018]
Parallel: nein

## Beschreibung
Ein 26B-Q4-Modell schreibt anders als Opus 5. Ohne Angleichung liest sich das Manuskript stellenweise wie zwei Buecher.

Massnahmen:
1. **Editor-Durchlauf ist Pflicht** fuer jede lokal generierte Szene — `claude-opus-5` reviewt und glaettet, ohne den Inhalt zu entschaerfen. Die Instruction muss explizit sagen: Stil und Sprache angleichen, Inhalt und Explizitheit unveraendert lassen.
2. **Qualitaetsschwelle:** faellt eine lokale Szene unter die Rubrik-Schwelle, wird sie markiert (`.draft.md` + Verdikt) statt uebernommen. Optional: Regenerierung mit angepasstem Prompt.
3. **Stil-Fingerprint:** deterministische Kennzahlen (Satzlaenge, Absatzlaenge, Dialoganteil, Adverbdichte) gegen den Manuskript-Durchschnitt. Ausreisser markieren.
4. **Eval:** `character_voice_consistency` und `show_dont_tell` laufen getrennt auf lokal-generierten Cases — Schwelle gilt **nach** dem Editor-Durchlauf.

Nicht loesen wollen: das lokale Modell auf Opus-Niveau zu bringen. Ziel ist, dass die Naht nicht sichtbar ist.

## Akzeptanzkriterien
- [ ] Jede lokal generierte Szene durchlaeuft zwingend den Editor
- [ ] Der Editor-Prompt fuer lokale Outputs entschaerft den Inhalt nachweislich nicht
- [ ] Stil-Fingerprint-Tool implementiert; Ausreisser werden gemeldet
- [ ] `character_voice_consistency` ≥ 4/5 auf lokalen Cases nach Editor-Durchlauf
- [ ] Unterschreitet eine Szene die Schwelle, entsteht eine `.draft.md`, keine finale Datei

## Betroffene Dateien
- `app/agents/editor_agent.py`
- `app/prompts/editor.py` (Variante fuer lokale Outputs)
- `app/tools/style_fingerprint.py`
- `tests/eval/eval_config.yaml`
