# Feature-Zusammenfassung: TASK-003 — Kontext-Store aus basics.md aufbauen

## Was wurde umgesetzt

Aus den freien Buchgrundlagen (`books/life_link/idea/basics.md`) ist jetzt ein strukturierter,
git-versionierter "Kontext-Store" entstanden, der ab sofort die maßgebliche Referenz fuer alle
zukuenftigen Agenten (Plot, Character, Editor, Continuity …) ist — nicht mehr der freie Text:

- **Figuren** (`characters.json`): alle neun Figuren des Buchs mit Rolle, Sprachregister,
  Motivation, Entwicklungsbogen, Wissensstand und erstem Auftritt.
- **Handlung** (`plot_outline.json`): alle sechs Phasen der Geschichte mit ihren Beats und den
  zugehoerigen Beispielszenen.
- **Weltregeln** (`world_bible.md`): die harten, ueberpruefbaren Regeln, wie sich die Naniten
  verhalten duerfen und wie nicht (z. B. keine zentrale Kontrollinstanz, Uebertragung nur bei
  koerperlicher Naehe) — das ist die Grundlage fuer spaetere automatisierte
  Konsistenz-Pruefungen.
- **Stilrichtlinien** (`style_guide.md`): wer wie spricht (Laienbegriffe vs. Fachterminologie),
  der grundlegende Ton des Buchs und die Regel, dass Wissenschaft nur ueber Dialoge vermittelt
  wird, nie ueber erklaerende Erzaehler-Passagen.
- **Zeitleiste** (`timeline.json`): als leeres Geruest angelegt, wird erst befuellt, sobald
  tatsaechliche Kapitel geschrieben werden.
- **Manuskript-Ordner**: angelegt, aber noch leer — hier entstehen die eigentlichen Kapitel in
  spaeteren Plaenen.

## Geänderte Dateien

- `books/life_link/store/characters.json` (neu)
- `books/life_link/store/plot_outline.json` (neu)
- `books/life_link/store/world_bible.md` (neu)
- `books/life_link/store/style_guide.md` (neu)
- `books/life_link/store/timeline.json` (neu)
- `books/life_link/manuscript/.gitkeep` (neu)

## Nächster Schritt

Damit sind beide Tasks aus Plan 1 abgeschlossen (Model-Router und Kontext-Store); Plan 1 ist
damit vollstaendig erledigt. Plan 2 (`02-agenten-kern-und-kontinuitaet/`) baut direkt auf diesem
Store auf: Die dortigen Agenten (Plot, Character, Editor, Continuity) lesen `characters.json`,
`plot_outline.json`, `world_bible.md` und `style_guide.md` als Kontext, statt `basics.md` selbst
zu parsen.
