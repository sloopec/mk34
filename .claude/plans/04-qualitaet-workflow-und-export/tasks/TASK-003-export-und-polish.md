# TASK-003: Export und finaler Polish
Status: ⏳ ausstehend
Abhängig von: [TASK-002]
Parallel: nein
*(vormals TASK-021 im Gesamtplan)*

## Beschreibung
Vom Manuskript zum fertigen Buch.

**1. Export-Formate** (`app/tools/export.py`, via Pandoc):
- Markdown → EPUB
- Markdown → PDF (LaTeX oder Pandoc)
- Markdown → DOCX (Verlagsformat)
- Kapitel-Metadaten im Frontmatter: Titel, POV-Character, Zeitpunkt, Ort

**2. Finales Lektorat**
Gesamtmanuskript-Review durch `model_for("editor")` (Start `gemini-3.1-pro-preview`, E6): Redundanzen, vergessene Subplot-Straenge (Voss' Konflikt mit dem Vorstand, Markus/Sophie aus Szene E), Pacing-Probleme, Vorschlaege zur Kapitelreihenfolge.
Wegen Manuskriptlaenge kapitelweise plus aggregierender Durchlauf ueber die Kapitelzusammenfassungen — nicht als ein Riesen-Prompt.

**3. Style-Transfer**
Gesamtes Manuskript auf einheitlichen Stil pruefen; Szenen aus unterschiedlichen Modellherkuenften (Gemini/lokal/ggf. Claude) angleichen — nutzt den Stil-Fingerprint aus TASK-001; Sprachregister pro Figur final validieren. Style Agent: `model_for("style")`.

## Akzeptanzkriterien
- [ ] Alle drei Exportformate erzeugen valide Dateien mit korrekten Kapitel-Metadaten
- [ ] Pandoc-Abhaengigkeit ist dokumentiert und im Setup geprueft (klare Fehlermeldung bei fehlendem Pandoc)
- [ ] Gesamtreview liefert eine priorisierte Liste (Redundanzen, offene Subplots, Pacing)
- [ ] Style-Transfer-Lauf reduziert die Fingerprint-Streuung messbar
- [ ] Sprachregister-Validierung ueber das Gesamtmanuskript ist fehlerfrei
- [ ] Finaler `agents-cli eval run` zeigt keine Regression

## Betroffene Dateien
- `app/tools/export.py`
- `app/agents/style_agent.py`
- `app/prompts/style.py`
- `docs/EXPORT.md`
