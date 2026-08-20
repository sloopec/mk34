# Durchführungsbericht: TASK-003 — Eval-Grundgerüst und Judge-Bibliothek
Abgeschlossen: 2026-08-20T00:30:00Z

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

## Bekannter Blocker — externe Ressourcengrenze, nicht code-bedingt

**`agents-cli eval run` konnte heute nicht bis zum Ende durchlaufen werden.** Nach drei
Versuchen (mit Wartezeiten dazwischen) liefert die Gemini-API durchgehend
`429 RESOURCE_EXHAUSTED` mit `quotaId: GenerateRequestsPerDayPerProjectPerModel-FreeTier`,
`quotaValue: 20` für `gemini-3.7-flash` — das **Tageskontingent** des kostenlosen
`GEMINI_API_KEY`-Tiers ist vollständig ausgeschöpft (u. a. durch die Versuche selbst sowie
vorangegangene Retries). Das ist keine Fehlkonfiguration im Code: `model_for("orchestrator")`
löst korrekt auf, `GEMINI_API_KEY` wird korrekt geladen (bestätigt durch die erfolgreichen
Requests, bevor das Kontingent griff, sowie durch `uv run --env-file .env pytest
tests/integration -q`, die denselben Pfad nutzen und zuvor grün liefen).

**Auswirkung:** Das Akzeptanzkriterium "Beide Cases erreichen `task_success` ≥ 4/5;
Score-Tabelle im PR/Commit dokumentiert" ist **heute nicht verifizierbar** und wird hiermit nicht
fingiert. Alle anderen Akzeptanzkriterien (Dataset/Config eingecheckt, ausschließlich
`custom_metrics`, Judge-Modellauflösung über `tier`, Kostenprotokoll getrennt nach Stufe, `safety`
mit Begründung ausgeschlossen, Unit-Tests inkl. gestubbtem Claude-Pfad) sind erfüllt und durch
`uv run pytest`/`agents-cli lint` verifiziert.

**Auswirkung auf den weiteren Plan:** Jeder Folge-Task mit einem Live-Eval- oder
`agents-cli run`/`playground`-Gate (TASK-009, TASK-010, TASK-011 u. a.) trifft auf dieselbe
Tageskontingent-Grenze, solange sie nicht zurückgesetzt ist. Dieser Blocker wird dem User separat
gemeldet (siehe Chat-Antwort) — es wird nicht eigenmächtig auf ein anderes Modell/Provider
umgeschaltet.

## Verifikationsschritte

1. `uv run pytest tests/unit/test_judge.py -q` → 11 passed.
2. `uv run --env-file .env pytest tests/unit tests/integration -q` → 66 passed (bestätigt
   `GEMINI_API_KEY` funktioniert grundsätzlich, vor Erreichen des Tageskontingents).
3. `agents-cli lint` → `ruff check`, `ruff format --check`, `codespell`, `ty check` alle grün.
4. `agents-cli eval run` → **nicht abgeschlossen**, siehe Blocker-Abschnitt oben. Score-Tabelle
   kann daher an dieser Stelle nicht dokumentiert werden; wird nachgeholt, sobald das Kontingent
   zurückgesetzt ist oder der User eine Alternative vorgibt.
