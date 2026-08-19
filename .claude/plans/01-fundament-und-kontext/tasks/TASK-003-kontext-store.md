# TASK-003: Kontext-Store aus basics.md aufbauen
Status: ✅ erledigt
Abhängig von: [TASK-001]
Parallel: ja

## Beschreibung
Die Buchgrundlagen liegen als Fliesstext in `books/life_link/idea/basics.md` (Praemisse, Technologie, Figuren, Handlungsphasen 0–5, Themen, ELI5-Beispiele, Beispielszenen A–E). Daraus wird ein strukturierter, git-versionierter Store abgeleitet.

Zielstruktur:
```
books/life_link/
├── idea/basics.md          # Quelle, read-only
├── store/
│   ├── characters.json     # David, Elena, Dr. Sarah Lin, Dr. Elias Voss,
│   │                       # Dr. Aris, Ronan, Vorstand, Markus, Sophie
│   ├── plot_outline.json   # Phase 0–5 als Akte/Szenen/Beats
│   ├── world_bible.md      # Waechter-Naniten, LifeLink, AGB-Klausel,
│   │                       # Schwarmintelligenz, Uebertragungsweg, Regeln
│   ├── timeline.json       # zunaechst leer/Skelett
│   └── style_guide.md      # Sprachregister pro Figur, Ton, POV-Regeln
└── manuscript/             # zunaechst leer
```

Pflicht-Inhalte im `style_guide.md`, weil sie spaeter Eval-Metriken sind:
- David: Laienbegriffe („Nanobots", „Chips", „Programmierung")
- Sarah/Voss/Aris: praezise Terminologie („Naniten", „Assembler", „Emergenz")
- Ton: klinische Distanz trifft poetische Verzweiflung (vgl. Szene E)
- Edutainment: Wissenschaft ausschliesslich als Metapher im Dialog

`world_bible.md` enthaelt die harten Naniten-Regeln als pruefbare Constraints (kein zentraler Server, Kommunikation koerperintern und bei physischer Naehe, Reproduktion braucht biologisches Rohmaterial, keine mechanischen „Metallmaennchen").

Extraktion darf einmalig LLM-gestuetzt erfolgen, das Ergebnis wird aber **vom Autor geprueft und eingecheckt** — der Store ist ab dann die Wahrheit, nicht `basics.md`.

## Akzeptanzkriterien
- [x] Alle Dateien existieren, sind valides JSON/Markdown und eingecheckt
- [x] `characters.json` enthaelt pro Figur: `name`, `role`, `language_register`, `motivation`, `arc`, `knowledge_state`, `first_appearance`
- [x] `plot_outline.json` bildet Phase 0–5 aus `basics.md` vollstaendig ab
- [x] `world_bible.md` listet die Naniten-Regeln als nummerierte, pruefbare Constraints
- [x] `style_guide.md` enthaelt die Sprachregister-Tabelle pro Figur
- [x] Keine Referenz auf den nicht existierenden Pfad `src/setup/basics.md` irgendwo im Repo (der einzige verbleibende Treffer in `docs/PLAN.md` steht bereits im eigenen Korrektur-Hinweis dieses eingefrorenen Dokuments)

Details und Verifikationsschritte: `walkthroughs/TASK-003-kontext-store.md`.

## Betroffene Dateien
- `books/life_link/store/characters.json`
- `books/life_link/store/plot_outline.json`
- `books/life_link/store/world_bible.md`
- `books/life_link/store/timeline.json`
- `books/life_link/store/style_guide.md`
- `books/life_link/manuscript/.gitkeep`
