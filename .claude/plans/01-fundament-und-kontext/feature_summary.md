# Feature-Zusammenfassung: Plan 1 — Fundament und Kontext

Status: ✅ alle drei Tasks abgeschlossen (TASK-001 Scaffold, TASK-002 Model-Router,
TASK-003 Kontext-Store).

## Was wurde gebaut

Plan 1 legt das technische und inhaltliche Fundament fuer das mk34-Book-Writing-System (Google
ADK, Buchprojekt *Life Link*).

**TASK-001 — Projekt-Scaffold.** Das ADK-Projekt `mk34-book-agent/` wurde ueber
`agents-cli scaffold create` im Prototype-Modus erzeugt (kein Deployment, kein CI/CD, kein
GCP-Projekt — Entscheidung E1). Sessions sind von Anfang an persistent: statt der
Scaffold-Default-Option (`InMemorySessionService`) laeuft eine `DatabaseSessionService`-Instanz
gegen eine lokale SQLite-Datei (Entscheidung E3), sodass Unterhaltungen einen Server-Neustart
ueberstehen. Das Buch-Datenverzeichnis (`books/`) liegt bewusst ausserhalb des Agent-Projekts, im
Repo-Root (Entscheidung E5).

**TASK-002 — Model-Router.** Eine zentrale Funktion (`model_for(role)`) entscheidet fuer jede
Agentenrolle, welches Modell verwendet wird — kein Agent-Modul haelt jemals einen eigenen
Modell-Namen. Gestartet wird ausschliesslich mit Gemini (Entscheidung E6): schnell/guenstig fuer
Routing-Aufgaben (Orchestrator, Continuity, Research), staerker fuer kreative/analytische
Aufgaben (Plot, Character, Editor, Style, Szenen). Der Router ist so gebaut, dass eine spaetere
Umschaltung auf Claude oder ein lokales Modell (nur fuer das Szenenschreiben, kommt in einem
spaeteren Plan) eine reine Konfigurationsaenderung waere. Fehlt der noetige API-Schluessel, bricht
der Start mit einer klaren Fehlermeldung ab statt still auf ein anderes Modell auszuweichen. Im
Zuge dieses Tasks wurde zusaetzlich ein Problem im generierten Projekt-Scaffold behoben, das den
lokalen Testbetrieb ohne Google-Cloud-Projekt komplett blockiert hatte (der Server versuchte sich
immer gegen Google Cloud zu authentifizieren, unabhaengig davon, ob das ueberhaupt gebraucht
wird) — danach war der laengst faellige End-to-End-Test moeglich: Der Agent antwortet
nachweislich ueber Gemini, sowohl im interaktiven Playground als auch per Kommandozeile, und eine
Unterhaltung bleibt ueber einen kompletten Server-Neustart hinweg erhalten.

**TASK-003 — Kontext-Store.** Die freien Buchgrundlagen (`books/life_link/idea/basics.md`, ein
Fliesstext mit Praemisse, Technologie, Figuren, sechs Handlungsphasen und Beispielszenen) wurden
in einen strukturierten, git-versionierten Store ueberfuehrt: alle neun Figuren mit Sprachregister,
Motivation und Entwicklungsbogen; alle sechs Handlungsphasen mit ihren Szenen-Beats; die harten,
ueberpruefbaren Regeln, wie sich die Naniten-Schwarmintelligenz verhalten darf (kein zentraler
Server, Uebertragung nur bei koerperlicher Naehe, keine mechanischen "Roboter" usw.); und ein
Stilregelwerk (wer spricht wie, welcher Ton, Wissenschaft nur ueber Dialog statt
Erzaehler-Erklaerung). Ab jetzt ist dieser Store die massgebliche Referenz fuer alle kommenden
Agenten — nicht mehr der freie Text.

## Wesentliche Entscheidungen

- **Gemini-first statt Claude-first** (E6, im Verlauf von Plan 1 getroffen): Der urspruengliche
  Plan sah Claude als ersten Provider vor; das wurde umgestellt, weil der Nutzer zunaechst
  ausschliesslich mit Gemini testen wollte. Claude und ein lokales Modell bleiben als
  vorbereitete, aber nicht angebundene Alternativen im Router-Design.
- **`gemini-3.1-pro-preview` fuer alle anspruchsvollen Rollen freigegeben** (E7), trotz
  Preview-Status, mit der Option, bei Instabilitaet per Konfigurationsaenderung auf ein stabiles
  Modell zurueckzuwechseln.
- **Scaffold-Fix fuer GCP-freien Lokalbetrieb**: Notwendige, minimal-invasive Korrektur ausserhalb
  der urspruenglich geplanten Aenderungsliste von TASK-002, da der generierte Code sonst in jeder
  Umgebung ohne Google-Cloud-Setup grundsaetzlich nicht lauffaehig war.

## Endzustand

- `mk34-book-agent/` ist ein lauffaehiges ADK-Projekt mit persistenten Sessions, zentralem
  Model-Router und gruenem `agents-cli lint`.
- `books/life_link/store/` enthaelt den vollstaendigen strukturierten Kontext fuer das Buchprojekt
  *Life Link*.
- Beide Nachfolgeplaene (`02-agenten-kern-und-kontinuitaet/`, `03-szenen-und-lokales-llm/`) koennen
  auf dem Router (`model_for`) und dem Kontext-Store aufbauen, wie in `.claude/plans/README.md`
  vorgesehen.
