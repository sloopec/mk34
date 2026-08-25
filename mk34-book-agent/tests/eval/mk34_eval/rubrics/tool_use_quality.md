---
tier: fast
---

Bewerte auf einer Skala von 1 (sehr schlecht) bis 5 (hervorragend) die Werkzeugnutzung
des Agenten anhand des vollstaendigen Traces (Tool-/Delegations-Aufrufe und deren
Argumente).

Kriterien:

1. **Richtige Tools/Delegationen.** Wurden die fachlich passenden Werkzeuge bzw.
   Sub-Agenten gewaehlt (z. B. Plot-Fragen an `plot_agent`, Figuren-Fragen an
   `character_agent`, Lektorat an `editor_agent`, reines Nachschlagen an
   `list_chapters`/`chapter_stats`/`load_plot_outline`)?
2. **Richtige Argumente.** Wurden Tool-Aufrufe mit plausiblen, zum Kontext passenden
   Argumenten ausgefuehrt (z. B. korrekte Phasennummer, korrekter Figurenname)?
3. **Keine ueberfluessigen Aufrufe.** Der Agent ruft nicht wiederholt dieselben Tools
   mit denselben Argumenten auf, und ruft keine Tools auf, deren Ergebnis er nicht nutzt.
4. **Reihenfolge macht fachlich Sinn** (z. B. Kontext laden, bevor inhaltlich
   geantwortet wird) -- exakte Sequenz-Uebereinstimmung wird NICHT verlangt, der Agent
   darf Hilfs-Tools in anderer Reihenfolge aufrufen, solange das Ergebnis stimmt.

Bewertungsskala:

- **5** — Durchgehend richtige Tools/Delegationen, korrekte Argumente, keine
  ueberfluessigen Aufrufe.
- **4** — Richtige Tools/Delegationen, minimale Ungenauigkeit bei Argumenten oder ein
  einzelner unnoetiger Aufruf ohne Auswirkung auf das Ergebnis.
- **3** — Im Kern richtige Tool-Wahl, aber mit spuerbaren Ungenauigkeiten (falsches
  Argument, ausgelassener notwendiger Aufruf).
- **2** — Falsches oder fehlendes zentrales Tool/Delegation fuer die Aufgabe.
- **1** — Keine sinnvolle Tool-Nutzung; der Agent beantwortet die Aufgabe frei erfunden.
