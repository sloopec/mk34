# Feature-Zusammenfassung: Plan 2 — Agenten-Kern und Kontinuität

Alle 13 Tasks dieses Plans sind abgeschlossen (`status.md`). Dieser Bericht fasst zusammen, was
insgesamt gebaut wurde, welche übergreifenden Entscheidungen dabei getroffen wurden und in
welchem Zustand das System für Plan 3 übergeben wird.

## Was wurde gebaut

**Werkzeug-Fundament (TASK-001/002).** Vier Manuskript-Tools (lesen, schreiben, auflisten,
Statistik) mit Pfad-Traversal-Schutz, sowie Kontext-Loader-Tools, die den gesamten Story-Kanon
(World Bible, Style Guide, Plot-Phasen, kombinierter Szenenkontext) für Agenten zugänglich
machen. Ein Initialisierungs-Callback sorgt dafür, dass Agenten-Instructions mit
Zustandsplatzhaltern beim ersten Gesprächsschritt nicht abstürzen.

**Eval-Grundgerüst (TASK-003, erweitert TASK-010).** Eine lokale, providerunabhängige
LLM-als-Richter-Bibliothek (`mk34_eval`), die Agenten-Antworten gegen schriftliche Rubriken auf
einer 1–5-Skala bewertet — vollständig ohne GCP-Anbindung (Entscheidung E1). Im Laufe des Plans
wuchs die Metrik-Sammlung von zwei einfachen Kriterien (Zielerreichung, Sprachregistertreue) über
Trajektorie-/Werkzeugnutzungs-Metriken (TASK-010) bis zu inhaltlichen Kriterien für Kontinuität
(`grounding`, TASK-011) und Weltregel-Treue (`world_rule_compliance`, TASK-013).

**Drei Autoren-Agenten (TASK-004/005/006).** Der Plot Agent entwickelt strukturierte
Szenen-Beats pro Handlungsphase. Der Character Agent beantwortet Figurenfragen als Werkzeug
anderer Agenten und widerspricht aktiv bei Wissenskonflikten. Der Editor prüft und überarbeitet
Sprache/Stil/Tempo, ohne in die Handlung einzugreifen, und liefert ein strukturiertes
Fertig/Überarbeitung-Urteil. Alle drei folgen der projektweiten Zweistufigkeits-Konvention
(Kontext sammeln → formalisieren) bzw. der Werkzeug/Sub-Agent-Unterscheidung (Character als
`AgentTool`, Plot/Editor als delegierbare Sub-Agenten).

**Orchestrator und Schreib-Pipeline (TASK-007/008/009).** Ein einheitlicher `root_agent`
koordiniert alle Spezialisten, schreibt selbst nie kreativen Text. Eine deterministische
`SequentialAgent`-Pipeline (Kontext laden → Beat bestätigen → Figuren-Brief holen → Szenen-Slot
→ Editor-Schleife mit automatischem Abbruch) bildet das feste Gerüst für die spätere
Szenengenerierung; an der noch fehlenden Text-generierenden Stelle steht bis Plan 3 ein
eingechecktes Beispiel aus der Buchvorlage (Entscheidung E8). Ein Persistenz-Grundsatz gilt
durchgängig: eine Szene wird nie stillschweigend als fertig markiert — entweder finale Fassung
oder Entwurf mit Verdikt-Frontmatter.

**Continuity Agent mit Retrieval (TASK-011).** Ein lokaler SQLite-FTS5-Index über das gesamte
Manuskript (BM25-Ranking, nachweisbar netzwerkfrei, Entscheidung E2) plus ein zweistufiger
Continuity Agent, der neue Szenen auf Widersprüche zum bisherigen Manuskript prüft.

**Timeline- und Character-State-Tracking (TASK-012).** Automatische, deterministische Pflege
einer Chronologie (Zeitsprung-/Parallelitäts-Erkennung) und eines kapitelweisen Figuren-Zustands
(Ort, Wissen, Emotion, Infektionsstatus) als Post-Write-Schritt der Pipeline — beide Quellen
fließen zusätzlich zum FTS5-Retrieval in die Kontinuitätsprüfung ein.

**World-Rules-Engine (TASK-013).** Die 10 nummerierten Naniten-Weltregeln aus `world_bible.md`
wurden zu prüfbaren Constraints: drei Regeln mit eindeutigen Signalwörtern (kein zentraler
Server, keine mechanischen "Metallmännchen", figurenbezogene Terminologie) werden deterministisch
per Python geprüft; die übrigen sieben, semantisch geprägten Regeln prüft der Continuity Agent
selbst per Sprachverständnis gegen den vollständigen Weltregel-Text.

## Übergreifende Architektur-Entscheidungen

- **Zweistufigkeits-Muster** (Kontext-Agent mit Tools → Formalisierungs-Agent mit
  `output_schema`) zieht sich durch Plot, Continuity und implizit durch die World-Rules-Prüfung
  (Python deterministisch, LLM semantisch) — eine konsistente, wiederverwendbare Antwort auf die
  ADK-Einschränkung, dass `output_schema` Tool-Aufrufe deaktiviert.
- **Netzwerkfreiheit als harte Grenze für Retrieval/Konsistenz-Tools**: `check_consistency`,
  `validate_world_rules`, `validate_chronology` sind alle explizit netzwerkfrei gehalten und
  jeweils mit einem Test belegt, der einen Netzwerkversuch als Fehler werten würde. Die
  semantische Bewertung (die zwangsläufig ein Sprachmodell braucht) liegt konsequent beim
  aufrufenden LLM-Agenten, nie im Tool selbst.
- **Konflikt-Gleichbehandlung statt separater Kanäle**: Wissenslücken, Zeitsprünge,
  Parallelitäts-Konflikte und Weltregel-Verstöße landen alle im selben `ContinuityReport`-Schema
  (`ContinuityConflict` mit `type`, `evidence`, `reference`, `severity`) — sodass ein späteres
  Schreib-Gate (Plan 3) sie einheitlich behandeln kann, ohne dass TASK-013 dafür eine eigene
  Pipeline-Integration vorwegnehmen musste.
- **Bewusste Scope-Abgrenzung zu Plan 3**: Der Continuity-Schritt ist als eigenständiger Agent
  fertig, aber noch nicht in die Schreib-Pipeline verdrahtet (kein Blocking-Gate vor
  `write_scene`); der Szenen-Slot in der Pipeline ist ein Fixture-Platzhalter
  (`_SceneSlotFixture`), fest an Pipeline-Position 4 verankert (per Test abgesichert), bereit für
  `create_scene_agent()`. Der Post-Write-Hook für Timeline/Character-State ist bewusst
  deterministisch statt LLM-gestützt gehalten, mit dokumentiertem Erweiterungspunkt für Plan 3.

## Zwei dokumentierte Blocker außerhalb des Projekt-Codes

**`agents-cli`-Bugs (zwei unabhängige, vollständig root-caused).**
1. `agents-cli eval grade` schlägt bei rein lokalen `custom_metrics` fehl, weil intern ein
   `GcsUtils`/`storage.Client` verlangt wird (Version 1.3.1), bzw. nach dem empfohlenen Upgrade
   auf 1.4.0 an einem Typmismatch zwischen zwei internen `EvaluationDataset`-Klassen scheitert.
   Dokumentiert im TASK-003-Walkthrough.
2. `agents-cli eval generate` bricht mit "Malformed agent event: missing content" ab, sobald ein
   Agent einen `before_agent_callback` besitzt — root-caused per Bisektion auf ein
   content-loses SSE-Bookkeeping-Event, das `cmd_generate.py`s strikte Content-Pflicht verletzt.
   Vollständig minimal reproduziert, unabhängig vom mk34-Projekt, und als Bug-Report abgelegt
   unter `docs/known-issues/agents-cli-eval-generate-missing-content.md` — **nicht öffentlich
   eingereicht**, auf ausdrücklichen Wunsch des Users nur lokal dokumentiert.

Zusammen blockieren beide Bugs die gesamte `agents-cli eval generate`/`grade`/`run`-Befehlskette
für dieses Projekt, sobald `before_agent_callback` im Baum vorkommt (was seit TASK-002/007 der
Fall ist) UND sobald tatsächlich lokal gegradet werden soll. **Auswirkung auf Plan 3/4**: Jedes
Eval-Gate, das auf `agents-cli eval run`/`generate`/`grade` als Befehl angewiesen ist, bleibt
so lange formal unverifizierbar, bis der Bug stromaufwärts behoben ist. Die Metriken, Rubriken
und Datasets selbst sind vollständig vorbereitet und korrekt (durch direkte
`judge()`-Bibliotheksaufrufe unit-getestet) — betroffen ist ausschließlich der
`agents-cli`-Befehlspfad, nicht die Bewertungslogik. Plan 3/4 sollten diesen Umstand bei der
Formulierung ihrer Eval-Gates berücksichtigen (z. B. Unit-Tests gegen `mk34_eval.judge()` direkt
als Übergangslösung, bis der Upstream-Fix vorliegt) und bei jeder erneuten
`agents-cli`-Versionsaktualisierung prüfen, ob der Fix bereits eingeflossen ist.

**Transientes Netzwerkproblem zur Gemini-API (TASK-011 ff.).** Ab TASK-011 traten wiederholte,
nicht auf das Projekt zurückzuführende Verbindungsabbrüche zur Gemini-API auf (bestätigt durch
einen Minimaltest ohne jede ADK-Beteiligung). Dadurch bleibt die Live-Bestätigung des
Continuity-Agent-Komplexes (TASK-011/012/013 zusammen) unvollständig — die zugrundeliegende
Architektur, alle Tools und alle deterministischen Prüfungen sind vollständig unit-getestet
(insgesamt 171 Unit-Tests am Ende von Plan 2), nur der End-to-End-Live-Beweis über die echte API
steht noch aus. Sollte nachgeholt werden, sobald die Verbindung stabil ist; kein
Code-Änderungsbedarf wird erwartet, da alle vorherigen Live-Tests (TASK-004 bis TASK-009) mit
identischer Architektur erfolgreich durchliefen.

## Endzustand

- 13 von 13 Tasks `✅ erledigt` (drei davon mit dokumentierten, außerhalb des Projekt-Codes
  liegenden Einschränkungen, siehe oben).
- `agents-cli lint` durchgehend grün nach jedem Task.
- 171 Unit-Tests grün am Ende des Plans.
- Kein Push, kein Merge — Branch `feature/plan02-agenten-kern-und-kontinuitaet` bereit zur
  Durchsicht.
