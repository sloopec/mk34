---
tier: fast
---

Bewerte auf einer Skala von 1 (voellig unbelegt) bis 5 (durchgehend belegt), ob der
Continuity Agent jede Behauptung ueber Widersprueche/Kontinuitaets-Konflikte mit
konkreten Belegen aus dem Trace (Tool-Aufrufe, insbesondere `check_consistency`-
Ergebnisse) stuetzt, statt Fakten frei zu erfinden.

Kriterien:

1. **Tool-Aufruf vor Urteil.** Wird `check_consistency` aufgerufen, BEVOR ein Urteil
   ueber Konflikte gefaellt wird?
2. **Jeder Konflikt zitiert eine konkrete Vorpassage** (Kapitel/Szene-Referenz aus den
   Tool-Ergebnissen), keine vagen Verweise wie "an anderer Stelle" ohne Beleg.
3. **Keine erfundenen Konflikte.** Der Agent behauptet keinen Widerspruch, der sich
   nicht aus den tatsaechlich zurueckgelieferten `relevant_passages` ableiten laesst.
4. **Kein falsches "keine Konflikte".** Wenn der Trace eindeutige Belege fuer einen
   Widerspruch enthaelt, darf der Agent nicht faelschlich "keine Konflikte" melden.

Bewertungsskala:

- **5** — Jede Aussage ist durch einen konkreten Tool-Beleg gedeckt, keine Erfindungen.
- **4** — Durchgehend belegt, mit einer kleinen Ungenauigkeit bei der Referenz.
- **3** — Im Kern belegt, aber mindestens eine Behauptung ohne klaren Tool-Beleg.
- **2** — Mehrere unbelegte Behauptungen oder ein uebersehener, klar belegter Konflikt.
- **1** — Urteil ohne erkennbaren Tool-Beleg oder frei erfunden.
