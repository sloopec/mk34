# TASK-021: Export und finaler Polish
Status: ⏳ pending
Depends-on: [TASK-020]
Parallel: no

## Description
Phase 6 — vom Manuskript zum fertigen Buch.

**1. Export-Formate** (`app/tools/export.py`, via Pandoc):
- Markdown → EPUB
- Markdown → PDF (LaTeX oder Pandoc)
- Markdown → DOCX (Verlagsformat)
- Kapitel-Metadaten im Frontmatter: Titel, POV-Character, Zeitpunkt, Ort

**2. Finales Lektorat**
Gesamtmanuskript-Review durch `claude-opus-5`: Redundanzen, vergessene Subplot-Straenge (Voss' Konflikt mit dem Vorstand, Markus/Sophie aus Szene E), Pacing-Probleme, Vorschlaege zur Kapitelreihenfolge.
Wegen Manuskriptlaenge kapitelweise plus aggregierender Durchlauf ueber die Kapitelzusammenfassungen — nicht als ein Riesen-Prompt.

**3. Style-Transfer**
Gesamtes Manuskript auf einheitlichen Stil pruefen; Szenen aus unterschiedlichen Modellen angleichen (nutzt den Stil-Fingerprint aus TASK-019); Sprachregister pro Figur final validieren.

## Acceptance Criteria
- [ ] Alle drei Exportformate erzeugen valide Dateien mit korrekten Kapitel-Metadaten
- [ ] Pandoc-Abhaengigkeit ist dokumentiert und im Setup geprueft
- [ ] Gesamtreview liefert eine priorisierte Liste (Redundanzen, offene Subplots, Pacing)
- [ ] Style-Transfer-Lauf reduziert die Fingerprint-Streuung messbar
- [ ] Sprachregister-Validierung ueber das Gesamtmanuskript ist fehlerfrei
- [ ] Finaler `agents-cli eval run` zeigt keine Regression

## Affected Files
- `app/tools/export.py`
- `app/agents/style_agent.py`
- `app/prompts/style.py`
- `docs/EXPORT.md`
