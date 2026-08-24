# Durchführungsbericht: TASK-005 — Szenen-Evals (Datasets und Metriken)
Abgeschlossen (Stufe A): 2026-08-24T00:00:00Z · Stufe B: siehe Nachtrag unten

## Was wurde umgesetzt (Stufe A)

- `tests/eval/mk34_eval/rubrics/show_dont_tell.md` — neue `craft`-Rubrik (Emotion
  gezeigt statt benannt, mit expliziter Ausnahme für die bewusst klinisch-benennende
  KI-Analyse-Ebene aus Szene E).
- `tests/eval/show_dont_tell_metric.py` — Judge-Anbindung, identisches Muster wie
  `character_voice_consistency_metric.py`.
- Drei neue deterministische Metriken (kein LLM-Aufruf), alle bewusst
  **self-contained ohne `import app`** (siehe unten):
  - `tests/eval/scene_word_count_in_range_metric.py` — Wortzahl-Korridor
    **250–1800 Wörter** als bewusst weiter, provisorischer Fragment-/Runaway-Schutz.
    Die engeren, szenenspezifischen Korridore sind weiterhin die noch offene
    Autoren-Entscheidung aus `01-fundament-und-kontext/plan.md` → Offene Frage #1 —
    dieser Task löst sie nicht, sondern dokumentiert den Platzhalter explizit im
    Metrik-Docstring.
  - `tests/eval/pov_character_present_metric.py` — mindestens eine im Prompt
    namentlich genannte Kanon-Figur muss auch im Szenentext vorkommen (vacuously
    pass, wenn der Prompt keine Kanon-Figur nennt).
  - `tests/eval/terminology_leak_metric.py` — David/Ronan/Vorstand nie "Naniten",
    Sarah/Voss/Aris nie "Nanobots"; Satz-Näherung analog zu
    `app/tools/consistency.py::_check_terminology` (keine echte
    Sprecherzuordnung, bewusste, dokumentierte Vereinfachung).
- `tests/eval/eval_config.yaml` — alle vier neuen Metriken registriert
  (`metrics_to_run` + `custom_metrics`).
- `tests/eval/datasets/scene-writing.json` — 5 Cases entlang der Beispielszenen
  A–E aus `basics.md`, als direkte Schreib-Prompts mit eingebettetem Setting/
  Aktion/Dialog-Kern/Sprachregister-Vorgabe formuliert (siehe Design-Entscheidung
  unten).
- `tests/unit/test_scene_eval_metrics.py` — 11 Unit-Tests für die drei
  deterministischen Metriken (Pass-/Fail-Fälle, vacuous-pass ohne Figur, bekannte
  Näherungs-Falle bei `terminology_leak` dokumentiert) plus ein
  Rubrik-Registrierungstest für `show_dont_tell`.

## Design-Entscheidung: self-contained Metrik-Module ohne `import app`

Wie bereits bei allen bestehenden `custom_function_file`-Metriken (siehe
`mk34_eval/judge.py`-Docstring) laufen diese Skripte in `agents-cli eval grade`s
eigener Python-Umgebung ohne `google-adk` — ein `import app` würde über
`app/__init__.py` → `app.agent` → `google.adk` scheitern. Die drei neuen
deterministischen Metriken duplizieren deshalb die für sie nötigen Kanon-Daten
(Figurennamen, Register-Zuordnung) lokal, statt `app.tools.manuscript`/
`app.tools.consistency` zu importieren — konsistent mit der bereits etablierten
Konvention, Figurennamen direkt in Rubriken zu hardcoden (siehe
`character_voice_consistency.md`).

## Design-Entscheidung: `scene-writing.json`-Prompts mit eingebettetem Kontext

`plot_outline.json` enthält für dieses Buchprojekt noch keine `scene_beats`-Einträge
(der Plot Agent wurde für keines der Beispiel-Kapitel je ausgeführt) — ein Prompt der
Form "Schreibe Kapitel 1, Szene 1" würde deshalb (wie im TASK-003-Walkthrough
dokumentiert) auf `beat: None` treffen und eine Rückfrage statt Prosa erzeugen, egal
welche Beispielszene eigentlich gemeint ist. Die Cases sind deshalb als direkte
Schreib-Anweisungen mit vollständig eingebettetem Setting/Aktion/Dialog-Kern/
Sprachregister-Vorgabe formuliert (analog zum bereits etablierten
`editorial_revision`-Case in `multi-agent.json`, der ebenfalls Text direkt im Prompt
liefert statt sich auf State zu verlassen) — die Orchestrator-Routing-Regel aus
TASK-003 ("konkrete Szene schreiben" → `writing_pipeline`) greift bei diesen Prompts
zuverlässig, wie die Live-Stichprobe unten zeigt.

## Live-Stichprobe (Stufe A) — echte Gemini-API, voller Orchestrator

Da `agents-cli eval run/generate` wegen des bekannten Bugs
(`docs/known-issues/agents-cli-eval-generate-missing-content.md`,
[google/agents-cli#82](https://github.com/google/agents-cli/issues/82)) für jeden
Agenten mit `before_agent_callback` weiterhin nicht nutzbar ist — der Orchestrator hat
seit Plan 2 `before_agent_callback=initialize_state` — wurde eine repräsentative
Stichprobe (`scene_b_kaltes_schlafzimmer`) manuell end-to-end durchgespielt:

1. `InMemoryRunner` gegen den vollen `app.agent.root_agent` mit dem exakten
   `scene-writing.json`-Prompt.
2. Die vier neuen deterministischen Metriken sowie `show_dont_tell`,
   `character_voice_consistency` und `task_success` direkt über
   `mk34_eval.judge.judge(...)` gegen die echte finale Antwort aufgerufen (derselbe
   Code, den `agents-cli eval grade` intern für `custom_function_file`-Metriken
   ausführen würde -- nur ohne den defekten CLI-Zwischenschritt).

Ergebnis:

| Metrik | Ergebnis |
|---|---|
| `pov_character_present` | 1 (David, Elena im Text) |
| `scene_word_count_in_range` | 1 (669 Wörter) |
| `terminology_leak` | 1 (kein Registerbruch) |
| `show_dont_tell` | **5/5** — Craft-Judge |
| `character_voice_consistency` | **5/5** |
| `task_success` | **5/5** |

Damit liegt die Stichprobe deutlich über den Stufe-A-Gates aus `plan.md`
(`task_success ≥ 4/5`, `character_voice_consistency ≥ 4/5`, deterministische
Metriken pass). Die vollständige 5-Case-Matrix ist NICHT live durchgelaufen (Kosten/
Zeit einer manuellen Alternative zum defekten CLI-Pfad für alle Cases), aber die
Struktur (Dataset, Metriken, Rubrik) ist vollständig eingecheckt und bereit für einen
echten `agents-cli eval run`, sobald der Upstream-Bug behoben ist.

**Beobachtung (kein neuer Bug, aber notiert):** Die im Trace sichtbare finale
Antwort des `writing_pipeline`-Turns ist der rohe, strukturierte
`EditorVerdict`-JSON-Text (`{"grade": ..., "issues": [...], "revised_text": ...}`),
nicht nur `revised_text` isoliert -- das ist die inhärente Konsequenz von
`output_schema` auf dem Editor Agent (Plan 2/TASK-006) und betrifft jede Auswertung
dieser Pipeline über den finalen Turn-Text, nicht nur diesen Task. Die Judges/Metriken
extrahieren den eingebetteten Szenentext trotzdem zuverlässig (siehe Scores oben) --
für eine sauberere Trennung wäre ein eigener `output_key` für den reinen Fließtext
denkbar, das ist aber ein Pipeline-/Schema-Thema außerhalb des TASK-005-Scopes.

**Manuskript-Artefakte des Testlaufs bewusst verworfen:** der Prompt enthält keine
"Kapitel N, Szene M"-Angabe, daher liefen `active_chapter`/`active_scene` auf die
Defaults (1/1) — der Testlauf hätte `chapter_01.md`/`characters.json`/`timeline.json`
mit dem Szene-B-Text überschrieben. Alle drei Dateien wurden nach der Verifikation
per `git checkout` auf den zuletzt committeten Stand (TASK-002/003) zurückgesetzt.

## Geänderte Dateien

- `tests/eval/mk34_eval/rubrics/show_dont_tell.md` (neu)
- `tests/eval/show_dont_tell_metric.py` (neu)
- `tests/eval/scene_word_count_in_range_metric.py` (neu)
- `tests/eval/pov_character_present_metric.py` (neu)
- `tests/eval/terminology_leak_metric.py` (neu)
- `tests/eval/eval_config.yaml`
- `tests/eval/datasets/scene-writing.json` (neu)
- `tests/unit/test_scene_eval_metrics.py` (neu)
- `pyproject.toml` — codespell-Ignore-Liste erweitert

## Verifikationsschritte

1. `uv run pytest tests/unit -q` — 218 Tests grün (inkl. 11 neuer Metrik-Tests).
2. `agents-cli lint` — grün (ruff check/format, codespell, `ty check`).
3. Live-Stichprobe (siehe oben) — ein vollständiger `scene-writing.json`-Case
   end-to-end durch `InMemoryRunner` + direkte Judge-/Metrik-Aufrufe, alle sechs
   Metriken deutlich über den Stufe-A-Gates.
4. **Blockiert (bekannter externer Bug, nicht Teil dieses Tasks):** die offizielle
   `agents-cli eval run`-Ausführung über alle 5 Cases mit Score-Tabelle und
   `agents-cli eval compare` gegen die Plan-2-Baseline bleibt so lange nicht
   durchführbar, wie [google/agents-cli#82](https://github.com/google/agents-cli/issues/82)
   offen ist.

---

## Nachtrag: Stufe B (nach TASK-004)

Siehe separater Abschnitt/Commit -- wird ergänzt, sobald TASK-004 (Content-
Klassifikation und lokales Routing) abgeschlossen ist.
