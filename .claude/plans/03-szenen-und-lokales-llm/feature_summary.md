# Feature-Zusammenfassung: Plan 3 — Szenen und lokales LLM

Abgeschlossen: 2026-08-24 · Branch: `feature/plan03-szenen-und-lokales-llm` (5 Commits,
einer pro Task, TASK-005 in zwei Commits wegen der bewussten Stufe-A/Stufe-B-Trennung)

## Was wurde gebaut

Plan 3 ist der Kern des Projekts: das System kann jetzt tatsächlich Szenen für das
Buch *Life Link* schreiben, mit einem klaren Weg zur lokalen, unzensierten
Generierung für heikle Inhalte.

**Der Schreib-Workflow ist vollständig end-to-end lauffähig.** Auf „Schreibe
Kapitel N, Szene M" (oder eine direkte Szenenbeschreibung) reagiert das System mit
einer kompletten Kette: Kontext laden → Beat und Figuren-Brief holen →
automatisch entscheiden, ob die Szene lokal oder in der Cloud geschrieben werden
soll → die Szene tatsächlich schreiben (Scene Agent) → sie gegen den bisherigen
Kanon auf Widersprüche prüfen (Kontinuitätsprüfung) → sie lektorieren (Editor-
Schleife) → sie erst dann final speichern. Findet die Kontinuitätsprüfung einen
schwerwiegenden Widerspruch, wird gar nicht erst geschrieben — die Szene landet als
Entwurf mit Konfliktliste, nicht im finalen Manuskript.

**Das lokale, unzensierte Modell ist als eigene Route angebunden**, aber bewusst
nur für den Scene Agent — jede andere Rolle des Systems wird das nie anfordern
können. Ein automatischer Content-Klassifikator entscheidet pro Szene, ob sie
lokal (explizite Sexualität als Verbreitungsvektor, Gewalt, Körperhorror, moralisch
kontroverse Manipulation) oder in der Cloud (Boardroom, Recherche, ELI5-
Erklärungen) geschrieben wird — mit Begründung und Konfidenzwert, und jederzeit
manuell übersteuerbar. Die zentrale Sicherheitsgarantie: ist die lokale
Infrastruktur (eine verschlüsselte VM mit SSH-Tunnel) nicht erreichbar, bricht das
System kontrolliert mit einer klaren Handlungsanweisung ab — es weicht niemals
unbemerkt auf ein Cloud-Modell aus, das eine unzensierte Szene ohnehin meist
verweigern oder abschwächen würde. Zusätzlich erkennt das System automatisch, wenn
ein Cloud-Modell eine Szene verweigert, als Signal zur Nachschärfung der
Klassifikationsregeln.

**Eine eigene Prüf-Suite für Szenenqualität** ergänzt die aus Plan 2 vorhandene
Eval-Infrastruktur: fünf Beispielszenen aus dem Buch-Exposé als wiederholbare
Testfälle, neue Kriterien (Emotion gezeigt statt benannt, plausible Wortzahl, die
richtige Figur kommt vor, die Nanobots/Naniten-Sprachregel wird eingehalten), sowie
ein Routing-Testset, das prüft, ob heikle vs. unkritische Szenen tatsächlich
korrekt lokal bzw. Cloud landen.

## Umgesetzte Tasks

| Task | Ergebnis |
|---|---|
| TASK-001 | Lokales LLM als Route `"local"` im Model-Router — ausschließlich für die Rolle `scene`, Health-Check, kein stiller Cloud-Fallback |
| TASK-002 | Scene Agent (Start Gemini) — schreibt Szenentext im korrekten Figuren-Sprachregister, ohne Meta-Kommentar/Platzhalter |
| TASK-003 | Szenen-Schritt in die Schreib-Pipeline eingehängt, Kontinuitätsprüfung + Konflikt-Gate, aktive Szene aus der User-Nachricht extrahiert |
| TASK-004 | Content-Classifier + dynamisches lokal/Cloud-Routing pro Turn, manueller Override, providerübergreifende Refusal-Erkennung (Entscheidung E9) |
| TASK-005 | Szenen-Eval-Suite (Dataset, Rubrik, vier neue deterministische/qualitative Metriken) + Routing-Eval-Dataset |

## Wichtige Design-Entscheidungen unterwegs

- **Dynamische Modellauflösung pro Turn statt bei Agent-Konstruktion:** ADK löst
  `Agent.model` nur einmal bei der Konstruktion auf, `state["route"]` steht aber
  erst nach dem Classifier-Schritt fest. Gelöst über einen `BaseAgent`-Wrapper
  (`_RoutedSceneStep`), der den Scene Agent pro Pipeline-Durchlauf frisch baut —
  dokumentiert im TASK-001-Walkthrough als architektonische Vorausschau, in TASK-004
  umgesetzt.
- **Kontinuitätsprüfung als Pipeline-Schritt statt `AgentTool`:** bewusste
  Abweichung von der ursprünglichen Task-Skizze, da die Prüfung ein zwingender
  deterministischer Schritt ist (kein Modell-Ermessen) und der bereits im State
  vorhandene Kontext ohne JSON-Roundtrip weiterverwendet werden kann.
- **`_ContinuityGate`-Komposition statt `escalate`:** ADKs `SequentialAgent`
  honoriert kein `escalate`-Signal (nur `LoopAgent` tut das) — ein früher Abbruch
  der Pipeline bei einem High-Severity-Konflikt wird stattdessen durch Komposition
  gelöst (der Editor-Loop wird als Sub-Agent nur bedingt aufgerufen).
- **`eval_case_id`-Präfix statt Dataset-Feld für die erwartete Route:** das
  `agents-cli eval`-Schema garantiert nur wenige Felder; die erwartete Route steht
  robust im Case-Namen selbst statt in einem möglicherweise nicht durchgereichten
  Custom-Feld.

## Wie mit dem defekten `agents-cli eval`-Pfad umgegangen wurde

Der in Plan 2 gefundene und inzwischen öffentlich gemeldete Bug
([google/agents-cli#82](https://github.com/google/agents-cli/issues/82)) macht
`agents-cli eval run/generate/grade` für dieses Projekt weiterhin unbenutzbar (jeder
Agent mit `before_agent_callback` ist betroffen, das gilt seit Plan 2 für den
Orchestrator). Alle eval-relevanten Akzeptanzkriterien wurden deshalb durchgehend
über direkte `InMemoryRunner`-Läufe gegen die echte Gemini-API plus direkte Aufrufe
der Judge-/Metrik-Funktionen verifiziert — funktional gleichwertig zum offiziellen
Pfad, nur ohne die CLI-Orchestrierung. Das ist in jedem betroffenen
Walkthrough (TASK-005 vor allem) explizit als „live verifiziert, `agents-cli eval
run` selbst blockiert" dokumentiert, nicht stillschweigend übersprungen.

## Wie die VM-Nichtverfügbarkeit die Verifikation beeinflusst hat

Die verschlüsselte Parallels-VM mit dem lokalen Modell lief während der gesamten
Session nicht (`curl http://localhost:8080/health` schlug zu Beginn und am Ende
fehl). Das ist der laut Plan **explizit vorgesehene, korrekte Zustand** (die VM wird
nicht dauerhaft betrieben) und wurde durchgehend als solcher behandelt:

- **Was live verifiziert werden konnte, ohne die VM zu brauchen:** der komplette
  Cloud-Pfad (Scene Agent, Pipeline, Classifier, Kontinuitätsprüfung, Editor-Loop),
  die Health-Check-Logik selbst (liefert korrekt `False`), der komplette
  Fehlerpfad bei angeforderter lokaler Route (`RuntimeError` mit
  Handlungsanweisung, durch die gesamte Turn-Kette bestätigt), und — besonders
  wichtig — die **Korrektheit der Klassifikationsentscheidung** für alle vier
  `uncensored-routing.json`-Cases (4/4 korrekt lokal/Cloud geroutet), da die
  Klassifikation selbst kein lokales Modell braucht.
- **Was ehrlich offen bleibt, weil es die laufende VM voraussetzt:** der volle
  Roundtrip einer tatsächlich lokal generierten Szene (Textqualität,
  tatsächliche Generierungsdauer gegen die dokumentierten 2–5 Minuten), und damit
  auch die deterministischen Szenen-Metriken (`scene_word_count_in_range`,
  `pov_character_present`, `terminology_leak`) auf echten lokalen Outputs. Diese
  Metriken selbst sind fertig und provider-agnostisch (arbeiten auf reinem
  Response-Text) — sie sind lauffähig, sobald jemand die VM startet
  (`docs/LOCAL_MODEL_VM_SETUP.md`) und einen Lauf mit `route="local"` bzw. `--model
  local` durchführt.

Keine dieser offenen Stellen wurde vorgetäuscht oder stillschweigend übersprungen
— jede ist im jeweiligen Task-Walkthrough konkret benannt.

## Endzustand

Alle 5 Tasks sind `✅ erledigt`. Der Branch `feature/plan03-szenen-und-lokales-llm`
enthält 5 Commits (einer pro Task, TASK-005 zusätzlich mit einem Stufe-B-Nachtrag-
Commit). `agents-cli lint` ist über den gesamten Branch grün, `uv run pytest
tests/unit` zählt 262 grüne Tests. Nicht gepusht, nicht gemergt — wie angewiesen.

Offene Punkte für Folge-Pläne:
- Plan 4/TASK-001 (QS lokaler Outputs) setzt eine laufende VM voraus, um die oben
  genannten offenen Verifikationen nachzuholen.
- Die Editor-Prüfung erkennt aktuell keine reinen Meta-/Rückfrage-Antworten des
  Scene Agent als "kein echter Szenentext" (beobachtet in TASK-003, wenn kein
  Plot-Beat vorliegt) — ein QS-Feinschliff-Thema für Plan 4.
- Offene Frage Plan 3 #1 (Kreativqualität von Gemini für Szenen) bleibt nach den
  bisherigen Stichproben unauffällig positiv — keine Veranlassung zur
  Claude-Umschaltung, aber weiterhin eine Entscheidung für den User bei Bedarf.
