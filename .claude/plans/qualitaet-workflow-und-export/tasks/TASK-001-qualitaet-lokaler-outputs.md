# TASK-001: Qualitätssicherung für lokale Outputs
Status: ⏳ ausstehend
Abhängig von (plan-übergreifend): szenen-und-lokales-llm/TASK-004
Parallel: nein
*(vormals TASK-019 im Gesamtplan)*

## Beschreibung
Ein 26B-Q4-Modell schreibt anders als ein Frontier-Cloud-Modell. Ohne Angleichung liest sich das Manuskript stellenweise wie zwei Buecher.

Massnahmen:
1. **Editor-Durchlauf ist Pflicht** fuer jede lokal generierte Szene — der Editor (`model_for("editor")`, Start `gemini-3.1-pro-preview`, E6) reviewt und glaettet, ohne den Inhalt zu entschaerfen. Die Instruction muss explizit sagen: Stil und Sprache angleichen, Inhalt und Explizitheit unveraendert lassen. **Entscheidung E10 — Gemini-first bleibt auch hier, mit beobachtetem Risiko:** der Editor verarbeitet unzensierten Input. Die benannten Fallbacks bleiben stehen und werden gezogen, falls Gemini-Safety in der Praxis eingreift: (a) Claude-Umschaltung der Editor-Rolle per `.env` oder (b) Editor-Durchlauf auf der lokalen Route. Dieses Verhalten wird **als erstes** geprueft (Testfall mit explizitem Input, z. B. Szene B/E); Ausloeser fuer den Fallback-Zug: ein Safety-Block oder eine nachweisliche inhaltliche Entschaerfung im Editor-Output — beides wird per `is_refusal(...)` (E9) bzw. Diff-Pruefung erkannt und geloggt.
2. **Qualitaetsschwelle:** faellt eine lokale Szene unter die Rubrik-Schwelle, wird sie markiert (`.draft.md` + Verdikt) statt uebernommen. Optional: Regenerierung mit angepasstem Prompt.
3. **Stil-Fingerprint:** deterministische Kennzahlen (Satzlaenge, Absatzlaenge, Dialoganteil, Adverbdichte) gegen den Manuskript-Durchschnitt. Ausreisser markieren.
4. **Eval:** `character_voice_consistency` und `show_dont_tell` laufen getrennt auf lokal-generierten Cases — Schwelle gilt **nach** dem Editor-Durchlauf.

Nicht loesen wollen: das lokale Modell auf Frontier-Niveau zu bringen. Ziel ist, dass die Naht nicht sichtbar ist.

## Akzeptanzkriterien
- [ ] Jede lokal generierte Szene durchlaeuft zwingend den Editor
- [ ] Der Editor-Prompt fuer lokale Outputs entschaerft den Inhalt nachweislich nicht (Testfall mit expliziter Szene, als erster Schritt des Tasks)
- [ ] **E10:** Safety-Eingriffe des Gemini-Editors werden erkannt (via `is_refusal(...)`/Diff-Pruefung) und geloggt; tritt ein Eingriff auf, wird einer der beiden benannten Fallbacks gezogen und die Entscheidung im Plan vermerkt
- [ ] Stil-Fingerprint-Tool implementiert; Ausreisser werden gemeldet
- [ ] `character_voice_consistency` ≥ 4/5 und `show_dont_tell` ≥ 4/5 auf lokalen Cases nach Editor-Durchlauf
- [ ] Unterschreitet eine Szene die Schwelle, entsteht eine `.draft.md`, keine finale Datei

## Betroffene Dateien
- `app/agents/editor_agent.py`
- `app/prompts/editor.py` (Variante fuer lokale Outputs)
- `app/tools/style_fingerprint.py`
- `tests/eval/eval_config.yaml`
