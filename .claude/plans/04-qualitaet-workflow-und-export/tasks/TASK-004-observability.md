# TASK-004: Observability und Logging
Status: ⏳ ausstehend
Abhängig von (plan-übergreifend): 02-agenten-kern-und-kontinuitaet/TASK-008
Parallel: ja
*(vormals TASK-022 im Gesamtplan — kann frueh parallel zu Plan 3 starten)*

## Beschreibung
Querschnittsaufgabe. Mit E1 (kein GCP-Projekt) scheiden Cloud Trace und BigQuery Agent Analytics aus — die Minimalvariante ist gesetzt.

**Minimalvariante:**
- `agents-cli run -v` fuer Ad-hoc-Debugging (volle Event-JSONs, Tool-Calls, Zwischenschritte)
- ADK `LoggingPlugin` / `DebugLoggingPlugin` am `App` fuer strukturierte Logs
- Pro Szene ein Lauf-Protokoll: gewaehltes Modell (Gemini/lokal/ggf. Claude), Routing-Begruendung, Editor-Iterationen, Continuity-Konflikte, Token-/Zeitverbrauch — als JSON-Zeile neben dem Manuskript
- Kosten-Tracking pro Szene: Cloud-Tokens (Gemini; spaeter Claude) vs. lokale Laufzeit
- **Judge-Kosten pro Eval-Lauf, getrennt nach Stufe** (`fast` / `craft`) — validiert die E4-Aufteilung: ist der Schnitt richtig, oder muesste eine Rubrik umgestuft werden?

**Ausbauvariante (ausgeschlossen im aktuellen Umfang):**
Cloud Trace, Prompt-Response-Logging, BigQuery Agent Analytics (`BigQueryAgentAnalyticsPlugin`) setzen ein GCP-Projekt voraus. Mit E1 und dem Deployment-Non-Goal entfaellt das.

Bewusst nicht geloggt: der volle Szenentext im Klartext in externe Systeme — der Stoff ist teils explizit, und das lokale Modell laeuft genau deshalb in einer verschluesselten VM (`docs/LOCAL_MODEL_VM_SETUP.md`). Das gilt auch fuer Gemini-seitige Logging-Features.

## Akzeptanzkriterien
- [ ] Strukturiertes Lauf-Protokoll pro Szene wird geschrieben (Modell, Route, Iterationen, Konflikte, Kosten)
- [ ] Judge-Kosten pro Eval-Lauf werden erfasst, getrennt nach Stufe `fast` / `craft`
- [ ] Aus den Daten laesst sich beantworten, ob die E4-Aufteilung richtig geschnitten ist (Anteil craft an den Gesamtkosten, Auffaelligkeiten bei einzelnen Rubriken)
- [ ] `LoggingPlugin` bzw. Aequivalent ist am `App` registriert
- [ ] Kein Szenentext verlaesst die lokale Umgebung ueber Logging-Kanaele
- [ ] Kosten pro Kapitel sind aus den Logs ableitbar

## Betroffene Dateien
- `app/app_utils/observability.py`
- `app/agent.py` (Plugin-Registrierung)
- `docs/OBSERVABILITY.md`
