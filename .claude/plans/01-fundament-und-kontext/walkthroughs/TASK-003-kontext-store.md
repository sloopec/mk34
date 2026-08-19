# Durchführungsbericht: TASK-003 — Kontext-Store aus basics.md aufbauen
Abgeschlossen: 2026-08-19T00:00:00Z

## Was wurde umgesetzt

Aus dem Fließtext `books/life_link/idea/basics.md` (Prämisse, Technologie, Figuren,
Handlungsphasen 0–5, Themen, ELI5-Beispiele, Beispielszenen A–E) wurde die im Task spezifizierte
Zielstruktur `books/life_link/store/` aufgebaut, direkt und sorgfältig aus `basics.md` extrahiert
(keine LLM-gestützte Extraktion nach Aufgabenstellung dieser Umsetzung).

`characters.json` enthält alle neun in `basics.md` genannten Figuren (David, Elena, Dr. Sarah Lin,
Dr. Elias Voss, Dr. Aris, Ronan, Vorstand als Kollektivfigur, Markus, Sophie), jeweils mit
`name`, `role`, `language_register`, `motivation`, `arc`, `knowledge_state`, `first_appearance`.

`plot_outline.json` bildet alle sechs Phasen (0–5) aus Abschnitt 4 von `basics.md` vollständig ab,
inklusive der jeweiligen Beats und der Zuordnung der Beispielszenen A–D zu ihrer Phase. Szene E
("Das Protokoll der Sehnsucht") ist in `basics.md` keiner Phase explizit zugeordnet und wurde
deshalb als `standalone_example_scenes`-Eintrag mit `phase: null` und einer erklärenden Notiz
(Bezug zu Entscheidung E8, Editor-Loop-Fixture in Plan 2/TASK-008) modelliert, statt sie
künstlich einer Phase zuzuweisen.

`world_bible.md` listet die zehn Naniten-Regeln aus `basics.md` als nummerierte, prüfbare
Constraints (Abschnitt 3), inklusive der vier explizit im Task geforderten Kernregeln (kein
zentraler Server, körperinterne/physische-Nähe-Kommunikation, Reproduktion braucht biologisches
Rohmaterial, keine mechanischen "Metallmännchen") sowie sechs weiterer Regeln aus dem Fließtext
(Terminologie-Konsistenz, Optimierungs- statt Zerstörungsziel, kein zentraler Steuerungs-Reset
mehr möglich, vererbbare Keimbahn-Veränderung, beobachtbare Symptome). Zusätzlich dokumentiert
sind Konzernstruktur und die sechs kanonischen ELI5-Metaphern aus `basics.md`, damit spätere
Szenen sie konsistent wiederverwenden können.

`style_guide.md` enthält die geforderte Sprachregister-Tabelle pro Figur (David: Laienbegriffe;
Sarah/Voss/Aris: präzise Terminologie; plus die übrigen Figuren), die Ton-Vorgabe "klinische
Distanz trifft poetische Verzweiflung" mit Bezug auf Szene E, die Edutainment-Regel
(Wissenschaft ausschließlich als Dialog-Metapher, nie als Erzähler-Exposition) sowie POV-Regeln
pro Figurengruppe.

`timeline.json` ist als Skelett angelegt (leeres `events`-Array plus erklärender Hinweis), da
`basics.md` keinen konkreten Kalender vorgibt — wird ab Plan 2/TASK-012 befüllt.

`books/life_link/manuscript/.gitkeep` legt das laut Zielstruktur vorgesehene, zunächst leere
Manuskript-Verzeichnis git-versioniert an.

Zusätzlich wurde geprüft, ob der in den Akzeptanzkriterien genannte ungültige Pfad
`src/setup/basics.md` noch im Repo referenziert wird: Ein Treffer existiert in `docs/PLAN.md`,
dort aber bereits im eingefrorenen historischen Dokument, unmittelbar unter dessen eigenem
Korrektur-Hinweis am Dateianfang ("der Pfad `src/setup/basics.md` existiert nicht (real:
`books/life_link/idea/basics.md`)") — das Akzeptanzkriterium ist damit bereits erfüllt, keine
weitere Änderung nötig.

## Geänderte Dateien

- `books/life_link/store/characters.json` (neu)
- `books/life_link/store/plot_outline.json` (neu)
- `books/life_link/store/world_bible.md` (neu)
- `books/life_link/store/style_guide.md` (neu)
- `books/life_link/store/timeline.json` (neu, Skelett)
- `books/life_link/manuscript/.gitkeep` (neu)

## Design-Entscheidungen

**Szene E ohne Phasenzuordnung modelliert, statt sie zu erzwingen.** `basics.md` benennt Szene E
explizit als "ausformuliertes Beispiel" losgelöst von der Phasenliste. Eine künstliche Zuordnung
(z. B. zu Phase 1, weil sie thematisch zur selben Zeit wie Davids Entdeckung spielen könnte) wäre
eine Erfindung gewesen, die nicht durch den Quelltext gedeckt ist. Stattdessen wurde ein
`standalone_example_scenes`-Feld mit `phase: null` und einer erklärenden Notiz ergänzt.

**Vorstand als Kollektivfigur in `characters.json` behandelt.** `basics.md` beschreibt "Der
Vorstand" durchgängig als kollektiv handelnde Instanz, nicht als benannte Einzelperson (im
Unterschied zu den namentlich genannten Figuren). Da das Akzeptanzkriterium "pro Figur" fordert
und `basics.md` den Vorstand als eigenständigen Akteur mit eigener Motivation/eigenem Arc führt,
wurde er als eigener Eintrag mit `role: "Konzernführung von OmniCorp (Kollektivfigur)"`
aufgenommen statt weggelassen.

**Keine LLM-gestützte Extraktion genutzt.** Die Aufgabenstellung erlaubte eine einmalige
LLM-gestützte Extraktion, verlangte aber sorgfältige direkte Arbeit aus `basics.md` für diese
Umsetzung (kein Autoren-Review als Gate). Alle Store-Dateien wurden direkt aus dem gelesenen
Volltext von `basics.md` erstellt, mit wörtlichen Zitaten/Paraphrasen an den Stellen, wo
`basics.md` bereits explizite Formulierungen liefert (z. B. Naniten-Regeln, ELI5-Metaphern).

## Verifikationsschritte

1. `python3 -c "import json; json.load(open(f))"` für alle drei `.json`-Dateien im Store — alle
   valide.
2. `grep -rn "src/setup/basics.md" books/ mk34-book-agent/` — keine Treffer (der einzige
   verbleibende Repo-Treffer liegt im bereits disclaimten `docs/PLAN.md`).
3. `find books/life_link -type f` — bestätigt vollständige Zielstruktur
   (`idea/basics.md`, `manuscript/.gitkeep`, `store/{characters,plot_outline}.json`,
   `store/{world_bible,style_guide}.md`, `store/timeline.json`).
4. `~/.local/bin/agents-cli lint` (aus `mk34-book-agent/`) — weiterhin grün, keine Regression
   durch TASK-003 (reine Daten-/Doku-Dateien außerhalb des Agent-Projekts).
