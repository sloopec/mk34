# Durchführungsbericht: TASK-010 — Eval für Multi-Agent-Trajektorie
Abgeschlossen: 2026-08-24T17:30:00Z

## Was wurde umgesetzt

- **`tests/eval/datasets/multi-agent.json`** — vier Multi-Turn-Cases (als Single-Turn-Prompts
  gegen den Orchestrator, siehe Design-Entscheidungen): `beat_development`, `character_brief`,
  `editorial_revision`, `beat_brief_editorial_combination`.
- **Drei neue Rubriken** (alle `tier: fast`) in `tests/eval/mk34_eval/rubrics/`:
  `tool_use_quality.md`, `trajectory_quality.md`, `eli5_quality.md` — rubrikbasiert statt starre
  Sequenz-Matches, wie von der Task-Datei gefordert.
  gefordert.
- **Drei neue Metrik-Wrapper** (`tests/eval/tool_use_quality_metric.py`,
  `trajectory_quality_metric.py`, `eli5_quality_metric.py`), die alle über `mk34_eval.judge`
  laufen — derselbe Call-Site wie `task_success`/`character_voice_consistency` aus TASK-003.
- **`eval_config.yaml`** um die drei neuen Metriken in `metrics_to_run` und `custom_metrics`
  erweitert.

## Bekannter Blocker — ein ZWEITER, unabhängiger `agents-cli`-Bug gefunden

Zusätzlich zum in TASK-003 dokumentierten `eval grade`-Bug wurde hier ein **zweiter, unabhängiger
Bug in `agents-cli eval generate`** gefunden, der jeden Eval-Lauf gegen den seit TASK-007
bestehenden Orchestrator betrifft — nicht nur `multi-agent.json`, sondern **auch das bereits in
TASK-003 funktionierende `basic-dataset.json`**:

```
[generate] case[0] FAILED: Malformed agent event: missing content.
```

**Root-Cause-Analyse** (direkt im installierten `agents-cli`-Quellcode nachvollzogen,
`google/agents/cli/eval/cmd_generate.py::_parse_sse_event`):

```python
missing = [field for field in ("author", "content") if not event.get(field)]
if missing:
    raise ValueError(f"Malformed agent event: missing {' and '.join(missing)}.")
```

`eval generate` verlangt zwingend ein `content`-Feld auf **jedem** SSE-Event der `/run_sse`-Route.
Der Orchestrator (seit TASK-007 mit `sub_agents=[plot_agent, editor_agent]`) emittiert am Ende
jedes Turns jedoch ein reines Buchhaltungs-Event ohne `content` (nur `actions.endOfAgent: true`) —
genau dieses Event-Muster wurde bereits im `-v`-Output des TASK-007-Live-Tests beobachtet
(`{"actions": {..., "endOfAgent": true}, ...}` ohne `content`-Schlüssel). `agents-cli run`
toleriert das (druckt einfach jedes Event-JSON), `eval generate`s SSE-Parser bricht dagegen hart
ab.

**Verifikation, dass dies unabhängig vom Dataset-Inhalt ist:** `agents-cli eval generate` wurde
zusätzlich erneut gegen das unveränderte `basic-dataset.json` ausgeführt (das in TASK-003 nach dem
API-Key-Wechsel noch erfolgreich lief) — **identischer Fehler**, obwohl an diesem Dataset nichts
geändert wurde. Das bestätigt: der Bruch liegt am Orchestrator-Event-Muster (seit TASK-007), nicht
an `multi-agent.json`.

**Ausgeschlossene Ursache:** testweise wurden `events_compaction_config`/`resumability_config`
(TASK-008) aus `App(...)` entfernt und derselbe Lauf wiederholt — **derselbe Fehler**, also nicht
die Ursache. Der Code wurde danach unmittelbar auf den committeten Stand zurückgesetzt
(`git diff --stat app/agent.py` zeigt keine Abweichung).

**Einordnung:** Damit ist **die gesamte `agents-cli eval`-Befehlskette** (`eval generate` UND
`eval grade`) für dieses Projekt aktuell nicht lauffähig — zwei unabhängige, im
Drittanbieter-Code verifizierte Bugs, keiner davon im mk34-Projektcode behebbar, ohne den
installierten `agents-cli`-Quellcode selbst zu patchen (ausdrücklich außerhalb des Scopes). Die
Judge-Bibliothek selbst (`mk34_eval.judge`) ist vollständig funktionsfähig und unit-getestet.

**Auswirkung auf den Plan:** Jeder weitere Task mit einem `agents-cli eval run/generate/grade`-
Gate (TASK-011: `continuity.json`, 0 False Negatives) ist auf dieselbe Weise blockiert. Dieser
Befund wird dem User als eigener Blocker-Punkt gemeldet (siehe Chat-Antwort nach diesem Task).

## Geänderte Dateien

- `tests/eval/datasets/multi-agent.json` (neu)
- `tests/eval/mk34_eval/rubrics/tool_use_quality.md`, `trajectory_quality.md`, `eli5_quality.md`
  (neu)
- `tests/eval/tool_use_quality_metric.py`, `trajectory_quality_metric.py`,
  `eli5_quality_metric.py` (neu)
- `tests/eval/eval_config.yaml` (erweitert)
- `pyproject.toml` (codespell-Ausnahmeliste erweitert)

## Design-Entscheidungen

**`multi-agent.json` als vier Single-Turn-Prompts, nicht als echte Mehrturn-Sessions.** Die
Task-Datei beschreibt die Cases konzeptionell als Multi-Turn ("Beat → Brief → Lektorat ... in
einer Session"). Das offizielle Multi-Turn/`agent_data`-Format (siehe
`google-agents-cli-eval`-Skill → `dataset_schema.md`) ist jedoch für **Grading-Input**
(bereits vorhandener, fertig generierter Trace) vorgesehen — nicht für **Inference-Input**, das
`eval generate` als Startpunkt für einen frischen, mehrschrittigen Lauf verwenden könnte. Reale
Mehrturn-Generierung aus einem handgeschriebenen Dataset heraus ist mit dem dokumentierten Schema
nicht vorgesehen. Die vier Cases wurden daher als plausible Single-Turn-Prompts an den
Orchestrator formuliert, wobei der vierte Case (`beat_brief_editorial_combination`) bewusst alle
drei Teilaufgaben in einer zusammengesetzten Anfrage stellt, um zu prüfen, wie der Orchestrator
mit einer mehrteiligen Anfrage umgeht — das ist die praktikabelste Annäherung an die
Aufgabenstellung innerhalb der tatsächlichen CLI-Fähigkeiten.

**Kein Workaround für den `agents-cli`-Bug versucht** (z. B. Monkeypatching des installierten
CLI-Codes, Downgrade auf 1.3.1 nur um in eine andere, ebenfalls bereits dokumentierte
Fehlerklasse zurückzufallen). Das würde den Scope dieses Tasks verlassen und eine Entscheidung
treffen (Umgang mit fremdem, außerhalb des Repos liegendem Tool-Code), die dem User vorbehalten
bleiben sollte.

## Verifikationsschritte

1. `uv run pytest tests/unit -q` → 108 passed (keine neuen Unit-Tests nötig — die drei neuen
   Metrik-Dateien sind duenne Wrapper um das bereits in TASK-003 vollstaendig unit-getestete
   `mk34_eval.judge`, konsistent mit `task_success_metric.py`/`character_voice_consistency_metric.py`,
   die ebenfalls nicht separat getestet werden).
2. `agents-cli lint` → `ruff check`, `ruff format --check`, `codespell`, `ty check` alle grün.
3. `agents-cli eval generate --dataset tests/eval/datasets/multi-agent.json` → **fehlgeschlagen**,
   `Malformed agent event: missing content` fuer alle 4 Cases (siehe Blocker-Abschnitt).
4. Kontrolllauf `agents-cli eval generate --dataset tests/eval/datasets/basic-dataset.json` →
   **ebenfalls fehlgeschlagen**, identischer Fehler — bestaetigt, dass der Bug unabhaengig vom
   Dataset-Inhalt ist und am Orchestrator-Event-Muster liegt.
5. Root-Cause direkt im installierten `agents-cli`-Quellcode verifiziert
   (`cmd_generate.py::_parse_sse_event`), inkl. Ausschluss von
   `EventsCompactionConfig`/`ResumabilityConfig` als Ursache (testweise entfernt, derselbe Fehler,
   Code danach unveraendert zurueckgesetzt).
6. `git -C .. status --short books/` nach jedem Lauf geprueft; ein versehentlicher
   Store-Schreibzugriff (`plot_outline.json`, vermutlich aus einem teilweise ausgefuehrten
   `plot_agent`-Lauf vor dem SSE-Parser-Fehler) wurde per `git checkout` zurueckgesetzt.
