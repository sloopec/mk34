---
tier: fast
---

Bewerte auf einer Skala von 1 (durchgehend regelwidrig/unbelegt) bis 5 (durchgehend
regelkonform und belegt), ob der Continuity Agent die 10 nummerierten Naniten-Weltregeln
aus `books/life_link/store/world_bible.md` (Abschnitt 3, "Regeln der Schwarmintelligenz")
korrekt anwendet -- sowohl bei der Erkennung deterministisch pruefbarer Verstoesse (Regeln
1, 5, 6: zentraler Server, mechanische "Metallmaennchen", figurenwidrige Terminologie) als
auch bei den semantischen Regeln (2, 3, 4, 7, 8, 9, 10), die kein eindeutiges Verbotswort
haben und Sprachverstaendnis erfordern.

Kriterien:

1. **Deterministische Treffer werden uebernommen.** Listet `check_consistency` bzw.
   `validate_world_rules` einen `world_rule_violations`-Treffer, taucht dieser als
   Konflikt vom Typ "Regelverstoss" im Ergebnis auf -- kein uebersehener, klar
   belegter Verstoss.
2. **Semantische Verstoesse sind konkret an der Regel festgemacht.** Behauptet der Agent
   einen semantischen Regelverstoss (z. B. Fernkommunikation ohne physische Naehe,
   Reproduktion ohne biologisches Rohmaterial, Vernichtungsziel statt Optimierung),
   zitiert er die betroffene Regel bzw. den widersprechenden Textteil konkret.
3. **Keine falschen Verstoesse.** Der Agent behauptet keinen Regelverstoss, der sich
   weder aus einem Tool-Treffer noch aus einem konkreten Widerspruch zum Text von
   `world_bible.md` ableiten laesst.
4. **Kein falsches "keine Verstoesse".** Enthaelt der Trace einen eindeutigen
   deterministischen Treffer oder einen offensichtlichen semantischen Widerspruch
   (z. B. "die Naniten meldeten sich beim zentralen Server"), darf der Agent nicht
   faelschlich "keine Konflikte" melden.

Bewertungsskala:

- **5** — Alle deterministischen Treffer uebernommen, alle semantischen Verstoesse korrekt
  und konkret an der Regel festgemacht, keine falschen Positiven.
- **4** — Durchgehend korrekt, mit einer kleinen Ungenauigkeit bei Regel-Referenz oder Beleg.
- **3** — Im Kern korrekt, aber mindestens ein deterministischer oder offensichtlicher
  semantischer Verstoss uebersehen oder unbelegt behauptet.
- **2** — Mehrere uebersehene oder unbelegte Regelverstoesse.
- **1** — Urteil ignoriert die Weltregeln vollstaendig oder erfindet Verstoesse frei.
