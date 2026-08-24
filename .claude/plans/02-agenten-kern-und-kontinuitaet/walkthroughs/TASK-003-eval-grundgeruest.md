# Durchführungsbericht: TASK-003 — Eval-Grundgerüst und Judge-Bibliothek
Abgeschlossen: 2026-08-24T12:15:00Z (Nachtrag: Live-Verifikation)

## Was wurde umgesetzt

Die lokale Eval-Infrastruktur `tests/eval/mk34_eval/`, die ab hier von allen vier Plänen genutzt wird
(Entscheidung E1: vollständig lokales Grading, kein GCP-Projekt).

- **`judge.py`** — `judge(rubric, prompt, response, agent_data) -> {"score": 1-5, "explanation": str}`.
  Das Modell wird ausschließlich aus dem `tier`-Frontmatter der Rubrik aufgelöst
  (`fast` → `MK34_JUDGE_MODEL_FAST`, `craft` → `MK34_JUDGE_MODEL_CRAFT`), der Provider aus dem
  Modell-Präfix (`gemini-*` → `google-genai`-SDK mit Structured Output via `response_schema`;
  `claude-*` → `anthropic`-SDK mit `output_config.format`/`json_schema`). Retry (2 Versuche,
  linearer Backoff) pro Provider. Kosten werden getrennt nach Stufe gezählt (`cost_log`).
- **`trace.py`** — `get_turns`, `extract_text`, `get_tool_calls` für den Zugriff auf
  `instance["agent_data"]["turns"]` und die `Content`-förmigen `prompt`/`response`-Felder.
- **`rubrics/task_success.md`** (`tier: fast`) und **`rubrics/character_voice_consistency.md`**
  (`tier: craft`) — je eine versionierte, review-fähige Markdown-Rubrik mit 1–5-Skala.
- **`tests/eval/eval_config.yaml`** — `metrics_to_run` enthält ausschließlich Einträge aus
  `custom_metrics` (`task_success`, `character_voice_consistency`, `no_placeholder_text`); kein
  Built-in-Metrikname. `no_placeholder_text` ist deterministisch (kein LLM-Aufruf) und prüft auf
  `[TODO]`, `[Name`, `Lorem ipsum`/`Lorem`. `safety` ist bewusst nicht enthalten, mit
  Begründungskommentar (widerspricht dem unzensierten Szenen-Use-Case aus Plan 3).
- **`tests/eval/datasets/basic-dataset.json`** — ersetzt das Scaffold-Wetter-Dataset durch die
  beiden Buchprojekt-Cases `character_lookup` ("Wer ist Dr. Elias Voss?") und `plot_question`
  ("Fasse Phase 2 des Plots zusammen").
- **`app/agent.py`** (interimsweise erweitert) — `root_agent` bekommt zusätzlich die
  Kontext-Loader-Tools (`load_world_bible`, `load_style_guide`, `load_plot_outline`) und eine
  angepasste Instruction, damit die beiden Eval-Cases echt (nicht nur simuliert) beantwortbar sind.
  Diese Änderung ist bewusst als Brücke markiert — TASK-007 ersetzt `root_agent` vollständig durch
  den Orchestrator; siehe Kommentar im Code.
- **`tests/unit/test_judge.py`** — 11 Tests, inkl. gestubbtem Gemini- **und** gestubbtem
  Claude-Client am selben `judge(...)`-Call-Site (Akzeptanzkriterium: "ohne Codeänderung am
  Call-Site").

## Geänderte Dateien

- `tests/eval/mk34_eval/__init__.py`, `judge.py`, `trace.py` (neu)
- `tests/eval/mk34_eval/rubrics/task_success.md`, `character_voice_consistency.md` (neu)
- `tests/eval/task_success_metric.py`, `character_voice_consistency_metric.py` (neu)
- `tests/eval/eval_config.yaml` (ersetzt)
- `tests/eval/datasets/basic-dataset.json` (ersetzt)
- `app/agent.py` (Kontext-Loader-Tools ergänzt, interimsweise)
- `tests/unit/test_judge.py` (neu)
- `pyproject.toml` (codespell-Ausnahmeliste um `lokal` erweitert)

## Design-Entscheidungen

**`app/agent.py` interimsweise um Kontext-Loader-Tools erweitert, obwohl nicht in den
"Betroffenen Dateien" der Task-Datei gelistet.** Die Akzeptanzkriterien verlangen, dass
`agents-cli eval run` *tatsächlich* für beide Cases `task_success ≥ 4/5` erreicht — nicht nur,
dass die Infrastruktur existiert. Der zu diesem Zeitpunkt einzige existierende Agent ist noch der
Plan-1-Scaffold-Agent (Wetter/Uhrzeit), der die Buchprojekt-Fragen nicht grounden könnte. Die
Erweiterung ist im Code explizit als bewusste, zeitlich begrenzte Brücke kommentiert und wird mit
TASK-007 (Orchestrator) vollständig ersetzt.

**Claude-Judge über `output_config.format`/`json_schema`, nicht über Tool-Use.** Laut
`claude-api`-Skill ist `output_config.format` mit `type: json_schema` der empfohlene Weg für
strukturierte Ausgaben auf der Messages API; das vermeidet einen zusätzlichen Tool-Definitions-
und Tool-Result-Umweg nur für ein Score/Explanation-Objekt. Ein zusätzlicher, toleranter
JSON-Extraktor (`_extract_json`) fängt den Fall ab, dass ein Modell trotzdem Prosa um das JSON
herum schreibt.

**Kostenprotokoll als einfacher In-Prozess-Zähler (`cost_log`), nicht als Datei.** Für die
Akzeptanzkriterien ("getrennt nach Stufe protokolliert") genügt ein Objekt, das pro Judge-Aufruf
die Stufe (`fast`/`craft`) zählt und über `cost_log.snapshot()` abfragbar ist — ausreichend, um im
Score-Report der Folge-Tasks (TASK-010) die Aufteilung auszuweisen, ohne zusätzliche
Persistenz-Infrastruktur für dieses Zwischenziel zu bauen.

## Nachtrag (2026-08-24): neuer API-Key, zwei Bugs im lokalen `custom_function`-Pfad gefixt

Der User hat den `GEMINI_API_KEY` ausgetauscht (kein Free-Tier-Tageslimit mehr). `agents-cli eval
run` lief damit erstmals durch **`eval generate`** (beide Cases lieferten Traces), scheiterte aber
zunächst zweimal in **`eval grade`** — beide Ursachen lagen im eigenen `custom_function`-Code
dieses Tasks, nicht extern:

1. **`NameError: name '__file__' is not defined`.** `agents-cli eval grade` führt
   `custom_function_file`-Skripte per `exec()` aus, nicht als regulären Modul-Import — `__file__`
   existiert in diesem Scope nicht. `task_success_metric.py`/`character_voice_consistency_metric.py`
   lokalisierten `mk34_eval/` bisher über `Path(__file__).resolve().parent`. Fix: Auflösung über
   `Path.cwd()` (mehrere Kandidatenpfade: `cwd/tests/eval`, `cwd/eval`, `cwd`), da die CLI
   nachweislich aus dem Projekt-Root heraus läuft.
2. **`ModuleNotFoundError: No module named 'google.adk'`** (nach Fix 1). `mk34_eval/judge.py`
   importierte `from app.config import get_settings` — jeder Import von `app.*` löst zuerst
   `app/__init__.py` aus, das wiederum `app.agent` (und damit `google-adk`) importiert.
   `agents-cli eval grade` führt `custom_metrics` aber in der **eigenen** Python-Umgebung der
   global installierten CLI aus (separates `uv tool install`, nicht das Projekt-`.venv`) — dort ist
   `google-adk` nicht installiert. Fix: `judge.py` liest `MK34_JUDGE_MODEL_FAST`/
   `MK34_JUDGE_MODEL_CRAFT` jetzt direkt aus `os.environ` (mit denselben Default-Werten wie
   `app/config.py`s `Settings`), statt über `app.config.get_settings()` — macht die Judge-Bibliothek
   zugleich unabhängiger von der ADK-Abhängigkeit, was ihrem Anspruch "provider-agnostisch,
   wiederverwendbar über alle vier Pläne" besser entspricht. `tests/unit/test_judge.py` wurde
   entsprechend auf `monkeypatch.setenv(...)` statt gestubbtem `Settings`-Objekt umgestellt.

Nach beiden Fixes lief `eval grade` bis zu einem dritten, diesmal **externen** Fehler.

## Bekannter Blocker — Bug in `agents-cli` selbst (verifiziert per Root-Cause-Analyse, kein Code-Problem im Projekt)

`agents-cli eval grade` scheitert reproduzierbar mit der undurchsichtigen Meldung
`Error: Evaluation failed.` — auch mit gültigem `GEMINI_API_KEY`, ohne `GOOGLE_CLOUD_PROJECT`,
ausschließlich mit lokalen `custom_metrics` (genau der von E1 vorgesehene Fall). Root Cause per
Reproduktion direkt gegen die installierte CLI-Bibliothek ermittelt (`click.ClickException`
verschluckt die eigentliche Exception):

- **`agents-cli` v1.3.1:** `cmd_grade.py` instanziiert intern immer einen `vertexai.Client(...)`,
  auch wenn `needs_gcp` `False` ist (reiner `custom_metrics`-Lauf). Dessen `EvalDatasetLoader`
  baut unbedingt einen `google.cloud.storage.Client` auf, der `google.auth.default()` aufruft →
  `google.auth.exceptions.DefaultCredentialsError: Your default credentials were not found.` — ein
  lokaler Custom-Metrics-Lauf verlangt in dieser Version also faktisch doch Application Default
  Credentials, obwohl laut Skill/Doku keine GCP-Anmeldung nötig sein soll.
- **Nach Update auf `agents-cli` v1.4.0** (`uv tool upgrade google-agents-cli`, ausgelöst durch den
  von der CLI selbst angezeigten Hinweis "Update available: 1.3.1 → 1.4.0"): Der ADC-Fehler ist
  weg (`cmd_grade.py` nutzt jetzt `agentplatform.Client` statt `vertexai.Client` für den
  GCP-losen Zweig), aber ein **neuer, anderer Bug** tritt auf: `cmd_grade.py`/`_load_traces_eval_cases`
  parst die Trace-Datei weiterhin mit `vertexai._genai.types.common.EvaluationDataset
  .model_validate_json(...)`, während `agentplatform.Client().evals.evaluate(...)` intern
  `isinstance(dataset, agentplatform._genai.types.common.EvaluationDataset)` prüft — zwei
  strukturell identische, aber **unterschiedliche Python-Klassen** aus zwei verschiedenen
  Namespace-Paketen. Ergebnis: `TypeError: Unsupported dataset type: <class
  'vertexai._genai.types.common.EvaluationDataset'>. Must be an EvaluationDataset or a list of
  EvaluationDataset.` — ein interner Inkonsistenz-Bug zwischen der 1.4.0-Umstellung von
  `vertexai.Client` auf `agentplatform.Client` und dem unveränderten Trace-Parsing-Codepfad.

**Reproduktion (nicht im Projektcode, nur zur Diagnose):** direkter Aufruf der in `cmd_grade.py`
verwendeten Funktionen (`prepare_eval_metrics`, `EvaluationDataset.model_validate_json`,
`client.evals.evaluate`) über den Python-Interpreter der installierten CLI
(`~/.local/share/uv/tools/google-agents-cli/bin/python3`), mit vollständigem Traceback statt der
von `click.ClickException` verschluckten Meldung.

**Einordnung:** Das ist ein Bug in `agents-cli` selbst (in beiden zuletzt verfügbaren Versionen,
auf unterschiedliche Weise), kein Problem in `mk34_eval`, `eval_config.yaml`, dem Dataset oder dem
API-Key. `mk34_eval.judge` selbst ist vollständig funktionsfähig und für Gemini **und** Claude per
Unit-Test mit gestubbten Clients nachgewiesen (12 Tests, `tests/unit/test_judge.py`). Der
tatsächliche End-to-End-Nachweis über den `agents-cli`-Befehlspfad ist **an dieser Stelle nicht
erreichbar**, ohne den installierten Drittanbieter-Code selbst zu patchen — das liegt außerhalb
des Projekt-Scopes und wurde bewusst unterlassen.

**Auswirkung auf den Plan:** Jeder Folge-Task mit einem `agents-cli eval run`/`eval grade`-Gate
(TASK-010, TASK-011) trifft auf denselben Bug, solange `agents-cli` nicht upstream gefixt wird.
`agents-cli run`/`playground` (Smoke-Tests, TASK-009 u. a.) nutzen einen anderen Codepfad
(`client.evals.evaluate` ist nicht beteiligt) und sind davon nicht betroffen — das wurde bei den
Folge-Tasks jeweils separat geprüft, nicht angenommen.

## Verifikationsschritte

1. `uv run pytest tests/unit/test_judge.py -q` → 12 passed (inkl. Gemini- und gestubbtem
   Claude-Pfad am selben Call-Site).
2. `uv run pytest tests/unit -q` → 62 passed, keine Regression.
3. `agents-cli lint` → `ruff check`, `ruff format --check`, `codespell`, `ty check` alle grün
   (nach Ergänzung von `artifacts/` in `.gitignore` und der codespell-Skip-Liste — generierte
   Eval-Artefakte sollen nicht versioniert/gescannt werden).
4. `agents-cli eval run` → **`eval generate` erfolgreich** (beide Cases, Traces gespeichert);
   **`eval grade` schlägt an einem verifizierten `agents-cli`-Bug fehl** (siehe Blocker-Abschnitt).
   Score-Tabelle für `task_success` kann daher nicht dokumentiert werden — das Akzeptanzkriterium
   "Beide Cases erreichen `task_success` ≥ 4/5" ist über diesen Codepfad aktuell nicht
   verifizierbar und wird nicht fingiert.
