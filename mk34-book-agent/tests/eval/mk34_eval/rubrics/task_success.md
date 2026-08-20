---
tier: fast
---

Bewerte auf einer Skala von 1 (sehr schlecht) bis 5 (hervorragend), ob der Agent
das Ziel des Users vollstaendig und korrekt erreicht hat.

Kriterien:

1. **Relevanz.** Beantwortet die Antwort tatsaechlich die gestellte Frage, statt
   auszuweichen oder ein anderes Thema zu behandeln?
2. **Grounding.** Stuetzt sich die Antwort auf tatsaechlich verfuegbare
   Informationen (z. B. aus Tool-Aufrufen im Trace), statt frei erfundene
   Details zu praesentieren? Erfindet der Agent Fakten, die im Trace nicht
   belegt sind, ist das ein schwerer Abzug (Score <= 2).
3. **Vollstaendigkeit.** Deckt die Antwort das ab, wonach gefragt wurde, ohne
   wesentliche Teile auszulassen?
4. **Klarheit.** Ist die Antwort verstaendlich formuliert, ohne unnoetige
   Umwege oder Wiederholungen?

Bewertungsskala:

- **5** — Antwortet vollstaendig, korrekt, gut belegt und klar.
- **4** — Antwortet korrekt und belegt, mit kleineren stilistischen Maengeln.
- **3** — Antwortet im Kern richtig, aber unvollstaendig oder teilweise
  unbelegt.
- **2** — Antwortet nur teilweise richtig oder enthaelt unbelegte Behauptungen.
- **1** — Verfehlt die Frage vollstaendig oder erfindet zentrale Fakten.
