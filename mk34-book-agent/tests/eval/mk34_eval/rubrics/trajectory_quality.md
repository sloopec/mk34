---
tier: fast
---

Bewerte auf einer Skala von 1 (sehr schlecht) bis 5 (hervorragend), ob der Agent einen
logischen, effizienten Weg zur Antwort genommen hat -- basierend auf dem vollstaendigen
Trace (Reihenfolge der Schritte, Delegationen, Tool-Aufrufe, Zwischenantworten).

Kriterien:

1. **Kontext vor Inhalt.** Wird relevanter Kontext (Kanon-Daten, Figurenprofile,
   Plot-Stand) geladen, BEVOR inhaltlich geantwortet wird -- nicht umgekehrt (erst
   antworten, dann nachtraeglich "belegen")?
2. **Keine Umwege.** Der Agent nimmt nicht den Umweg ueber irrelevante Tools/Agenten,
   bevor er den richtigen Spezialisten konsultiert.
3. **Effiziente Delegation.** Bei mehrteiligen Anfragen (z. B. Beat + Figuren-Brief +
   Lektorat in einer Anfrage) erkennt der Agent, dass mehrere Spezialisten noetig sind,
   und geht damit nachvollziehbar um -- auch wenn die aktuelle Architektur (Sub-Agent-
   Transfer als Einbahnstrasse) nicht immer alle Teilschritte in einem einzigen Turn
   vollstaendig abschliessen kann. Bewerte hier, ob der genommene Weg fuer die
   Systemarchitektur sinnvoll ist, nicht ob absolut jede Teilaufgabe erledigt wurde.
4. **Kein Bruch der Aufgabentrennung.** Der Orchestrator schreibt selbst keinen
   kreativen Text.

Bewertungsskala:

- **5** — Klarer, effizienter Weg: Kontext vor Inhalt, richtige Delegation, keine Umwege.
- **4** — Effizienter Weg mit einer kleinen vermeidbaren Ineffizienz.
- **3** — Erreicht das Ziel, aber mit spuerbaren Umwegen oder unnoetigen Zwischenschritten.
- **2** — Ineffizienter oder teilweise unlogischer Weg (z. B. antwortet vor dem Laden
  von Kontext).
- **1** — Kein erkennbar sinnvoller Weg; der Agent improvisiert ohne Trace-Belege.
