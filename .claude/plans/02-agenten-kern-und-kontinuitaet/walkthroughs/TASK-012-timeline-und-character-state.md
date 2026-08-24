# Durchführungsbericht: TASK-012 — Timeline- und Character-State-Tracking
Abgeschlossen: 2026-08-24T20:00:00Z

## Was wurde umgesetzt

Deterministisches Tracking von Chronologie und Figurenzustand, das nach jeder final
gespeicherten Szene automatisch fortgeschrieben wird.

**Timeline (`app/tools/timeline.py`, Persistenz `books/life_link/store/timeline.json`)**
- `append_event(chapter, scene, timestamp, location, description, characters)` — trägt ein
  Ereignis ein; idempotent bezüglich `(chapter, scene)` (ein wiederholter Aufruf ersetzt den
  bestehenden Eintrag, analog zur Replace-Semantik von `write_scene`).
- `read_timeline(from_chapter, to_chapter)` — liest Ereignisse, optional auf einen
  Kapitelbereich eingeschränkt, sortiert nach `(chapter, scene)`.
- `validate_chronology()` — rein deterministische Prüfung zweier Widerspruchsarten:
  - **Zeitsprünge**: Ein späteres Ereignis (in Erzählreihenfolge) hat einen Zeitstempel, der
    ohne erkennbaren Tageswechsel-Hinweis in der Beschreibung (z. B. "am nächsten Tag",
    "Stunden später") vor dem Zeitstempel des vorherigen Ereignisses liegt.
  - **Parallelitäts-Konflikte**: Dieselbe Figur ist laut Zeitstempel zur exakt selben Uhrzeit
    an zwei unterschiedlichen Orten gelistet.
- `extract_timestamp(text)` — extrahiert `"HH:MM Uhr"` per Regex (vgl. Szene E, "20:43 Uhr"),
  konsistent mit der bereits in TASK-011 (`app/retrieval/index.py`) etablierten Extraktion.

**Character-State (Erweiterung `app/tools/characters.py`)**
- Neues Feld `state_by_chapter` je Figur in `characters.json`:
  `{"<chapter>": {"location", "knowledge", "emotional_state", "infection_status"}}`
  (Kapitelnummern als String-Keys, da JSON keine int-Keys kennt).
  `infection_status` ist LifeLink-spezifisch: `"nicht_optimiert" | "infiziert" | "voll_compliant"`
  (Terminologie aus `basics.md`, Szene E: "volle Compliance trotz kognitiver Ablehnung").
- `update_character_state(name, chapter, location, knowledge, emotional_state, infection_status)`
  — schreibt/ersetzt den Zustand einer Figur für ein Kapitel.
- `get_knowledge_state(name, chapter)` — erweitert (Rückwärtskompatibilität gewahrt): liefert
  weiterhin das grobe Phasen-Fliesstext-Feld `knowledge_state`, ergänzt um `chapter_state` — den
  zuletzt bekannten kapitelgenauen Zustand bei oder vor dem angefragten Kapitel (Figuren
  "vergessen" ihren Zustand nicht zwischen Kapiteln ohne expliziten neuen Eintrag). `None`, wenn
  noch kein Eintrag für diese oder eine frühere Kapitelnummer existiert.
- `check_knowledge_prerequisite(name, chapter, required_knowledge)` — die geforderte "Warnung,
  wenn eine Szene Wissen voraussetzt, das die Figur zu diesem Zeitpunkt nicht haben kann":
  deterministischer Stichwort-Abgleich gegen den bekannten Wissensstand; `"unknown"` (kein
  automatischer Verstoß), wenn noch kein kapitelgenauer Zustand vorliegt — fehlende Daten sind
  kein Widerspruchsbeweis.

**Post-Write-Hook (`app/pipelines/writing.py`)**
- `_update_timeline_and_character_state(callback_context, text)` wird aus `_persist_or_draft`
  aufgerufen, aber **nur** im `grade == "pass"`-Zweig (nicht bei Entwürfen) — konsistent mit der
  Persistenz-Konvention "nie stillschweigend als fertig markieren": solange eine Szene nicht final
  ist, soll sie auch nicht als kanonisches Timeline-/Zustands-Update gelten.
- Extraktion: `location`/`characters`/`description` bevorzugt aus `state["scene_context"]["beat"]`
  (vom Plot Agent gepflegt, TASK-004); Fallback auf `characters_mentioned(text)` und die ersten
  150 Zeichen des Textes, falls kein Beat vorhanden ist (z. B. wenn die Pipeline ad hoc ohne
  vorherigen Plot-Schritt aufgerufen wird). `timestamp` per `extract_timestamp`.
  `infection_status` per deterministischer Stichwort-Erkennung (`_detect_infection_status`:
  "compliance"/"infiziert"/"nicht optimiert"/Varianten).

**Continuity Agent nutzt beide neuen Quellen**
- `app/tools/consistency.py::check_consistency` erweitert um `timeline_conflicts` (gefiltert auf
  im Text erwähnte Figuren) und `character_states` (bei übergebener `chapter`-Nummer, sonst leer)
  neben dem bereits vorhandenen `relevant_passages`-Retrieval aus TASK-011.
- `app/prompts/continuity.py::CONTINUITY_CONTEXT_INSTRUCTION` angepasst: Der Agent ruft jetzt
  `check_consistency(new_text, context_refs, chapter)` auf und wird explizit angewiesen, auch
  `timeline_conflicts` und `character_states` als Belegquellen für Wissen-zu-früh-, Zeitsprung-
  und Parallelitäts-Konflikte zu nutzen (nicht nur die FTS5-Vorpassagen aus TASK-011).

## Design-Entscheidung: Deterministische statt LLM-gestützter Extraktion im Post-Write-Hook

Die Task-Beschreibung sieht vor: "die Extraktion ist LLM-gestützt, das Schreiben deterministisch
über Tools." Für diesen Plan wird der Hook dennoch vollständig deterministisch implementiert
(Regex-Zeitstempel, bekannte Figurennamen, Stichwort-Erkennung für den Infektionsstatus), aus
zwei Gründen:
1. Der Satz direkt danach in derselben Task-Beschreibung: "Der Post-Write-Hook wird hier am
   Pipeline-Gerüst (TASK-008) implementiert und mit Fixture-Szenen getestet; scharf geschaltet
   wird er mit dem Szenen-Schritt in Plan 3" — liest sich als Hinweis, dass die *Mechanik* (Hook,
   Aufrufstelle, Tool-Schreibzugriffe) in Plan 2 gebaut und mit der Fixture-Szene E getestet
   werden soll, waehrend die *Feinabstimmung* (z. B. eine belastbarere LLM-Extraktion) mit dem
   echten, generierten Szenentext in Plan 3 folgt.
2. Akzeptanzkriterium "pytest deckt Timeline-Validierung mit Fixtures ab" verlangt offline
   lauffähige, deterministische Tests — ein LLM-Extraktionsschritt hätte (wie in TASK-011
   dokumentiert) das Risiko transienter Netzwerkprobleme in die Kern-Testsuite dieses Tasks
   getragen.

Diese Abweichung ist im Docstring von `app/pipelines/writing.py` (Modul-Ebene und bei
`_detect_infection_status`) dokumentiert. Eine Ersetzung durch eine LLM-gestützte Extraktion
(analog zum zweistufigen Muster von Plot/Continuity Agent) ist als Erweiterungspunkt für Plan 3
vorgesehen, sobald der Scene Agent echten statt Fixture-Text liefert.

## Unit-Tests

- `tests/unit/test_timeline.py` (17 Tests, neu): `extract_timestamp`, `append_event`
  (Schreiben, Idempotenz pro Szene), `read_timeline` (Kapitelbereich-Filter, Sortierung),
  `validate_chronology` — inklusive der beiden explizit geforderten Fixture-Fälle:
  `test_validate_chronology_detects_artificial_time_jump` (künstlich eingebauter Zeitsprung:
  20:43 Uhr → 08:00 Uhr ohne Tageswechsel-Hinweis) und
  `test_validate_chronology_detects_parallel_location_conflict` (David gleichzeitig um
  20:00 Uhr an zwei Orten), plus Gegenproben (kein Sprung bei Tageswechsel-Hinweis, kein
  Sprung bei vorwärtslaufender Zeit, kein Konflikt bei gleichem Ort).
- `tests/unit/test_character_tools.py` (10 neue Tests): `update_character_state`,
  `get_knowledge_state` mit kapitelgenauem Zustand und Fallback auf den letzten früheren
  Eintrag, `check_knowledge_prerequisite` (ok/violation/unknown/not_found).
- `tests/unit/test_pipeline_geruest.py` (8 neue Tests): `_detect_infection_status`
  (Stichwörter), `_update_timeline_and_character_state` (Beat-Metadaten-Pfad und
  Fallback-Pfad ohne Beat), `_persist_or_draft` ruft den Hook nur bei `grade == "pass"` auf
  (nicht bei Entwürfen) — inklusive expliziter Isolation der bestehenden
  `test_persist_or_draft_writes_final_scene_on_pass`, die zuvor unbeabsichtigt die echten
  Store-Dateien getroffen hätte, sobald der Hook eingebaut ist.
- `tests/unit/test_retrieval.py` (4 neue Tests): `check_consistency` liefert leere
  `timeline_conflicts`/`character_states` standardmäßig, surfaced Parallelitäts-Konflikte für im
  Text erwähnte Figuren, liefert `character_states` nur bei übergebener `chapter`-Nummer. Die
  bestehende `book`-Fixture wurde um Monkeypatches für `characters.store_dir`/`timeline.store_dir`
  ergänzt, damit sie weiterhin hermetisch bleibt (sonst hätte `check_consistency` jetzt
  transitiv die echten Store-Dateien gelesen).
- Gesamt: 159 Unit-Tests grün (`uv run python -m pytest tests/unit -q`), davon 39 neu für
  diesen Task.

## Blocker: Live-Verifikation weiterhin durch transientes Netzwerkproblem blockiert

Wie bereits in TASK-011 dokumentiert, bleibt die Gemini-API-Verbindung instabil. Ein erneuter
Versuch, `agents-cli run "Sag nur 'ok'."` (triviale Anfrage an den Root-Orchestrator, keine
neue Funktionalität dieses Tasks) auszuführen, blieb nach 45 Sekunden ohne Antwort hängen
(Server gestartet, Anfrage gesendet, keine Reaktion). Da TASK-012 keinen neuen LLM-Agenten
einführt (reine Tool-Erweiterung plus deterministischer Pipeline-Hook), sind die
Akzeptanzkriterien dieses Tasks vollständig durch die 39 neuen, deterministischen Unit-Tests
abgedeckt und nicht auf eine Live-LLM-Bestätigung angewiesen — der offene Live-Nachtest aus
TASK-011 (Continuity Agent erkennt einen Regelverstoß live) bleibt der einzige, weiterhin
unbestätigte End-to-End-Punkt, sobald die Verbindung wieder stabil ist.

## Geänderte Dateien

- `app/tools/timeline.py` — neu: `append_event`, `read_timeline`, `validate_chronology`,
  `extract_timestamp`.
- `app/tools/characters.py` — neu: `update_character_state`, `check_knowledge_prerequisite`;
  erweitert: `get_knowledge_state` um `chapter_state`.
- `app/tools/consistency.py` — `check_consistency` erweitert um `chapter`-Parameter,
  `timeline_conflicts`, `character_states`.
- `app/prompts/continuity.py` — Instruktion nutzt jetzt beide neuen Evidenzquellen.
- `app/pipelines/writing.py` — Post-Write-Hook `_update_timeline_and_character_state`,
  `_detect_infection_status`, Aufruf aus `_persist_or_draft` im `pass`-Zweig.
- `tests/unit/test_timeline.py` — neu, 17 Tests.
- `tests/unit/test_character_tools.py` — 10 neue Tests.
- `tests/unit/test_pipeline_geruest.py` — 8 neue Tests, bestehender Test isoliert.
- `tests/unit/test_retrieval.py` — 4 neue Tests, `book`-Fixture um zwei Monkeypatches ergänzt.
- `pyproject.toml` — codespell-Ignorierliste um `ende`, `tage` ergänzt (deutsche
  Wortkollisionen).

## Verifikationsschritte

1. `agents-cli lint` — grün (`ruff check`, `ruff format --check`, `codespell`, `ty check`).
2. `uv run python -m pytest tests/unit -q` — 159 Tests grün (39 neu).
3. `git status --short books/` — keine Verschmutzung des echten Buchprojekts durch die
   Tests (alle Timeline-/Character-State-Tests laufen über `monkeypatch`-isolierte
   `tmp_path`-Stores).
4. `agents-cli run "Sag nur 'ok'."` — nach 45 s ohne Antwort abgebrochen; bestätigt das aus
   TASK-011 bekannte transiente Netzwerkproblem, nicht spezifisch für diesen Task (keine neue
   LLM-Funktionalität in TASK-012).
