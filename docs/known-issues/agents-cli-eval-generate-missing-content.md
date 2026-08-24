# Bekannter Fehler: `agents-cli eval generate` scheitert bei jedem Agent mit `before_agent_callback`

**Status:** verifiziert, minimal reproduziert, noch nicht öffentlich gemeldet (nur intern
dokumentiert — siehe Hinweis am Ende).
**Betroffene Version:** `agents-cli` 1.4.0 (reproduziert; 1.3.1 zeigt denselben Fehler mit
gleicher Root Cause im Code, siehe unten).
**Gefunden im Rahmen von:** `.claude/plans/02-agenten-kern-und-kontinuitaet/` (Plan 2),
TASK-010, während des Aufsetzens der Multi-Agent-Eval.
**Verwandter, separater Fehler:** `agents-cli eval grade` hat einen eigenen, unabhängigen Bug
(Typkonflikt zwischen `vertexai`- und `agentplatform`-`EvaluationDataset`), dokumentiert im
Walkthrough zu Plan 2/TASK-003. Dieser Report behandelt ausschließlich `eval generate`.

## Titel

`agents-cli eval generate` bricht mit `Malformed agent event: missing content.` ab, sobald der
zu evaluierende Agent (root oder verschachtelt) einen `before_agent_callback` gesetzt hat — auch
bei einem völlig trivialen, sonst funktionierenden Agenten.

## Zusammenfassung

`google.agents.cli.eval.cmd_generate.py::_parse_sse_event` verlangt zwingend ein `content`-Feld
auf **jedem** über `/run_sse` empfangenen Event. ADK emittiert jedoch legitim ein Event ganz ohne
`content`, sobald ein `before_agent_callback` den Session-State verändert: ein reines
Buchhaltungs-Event mit `actions.stateDelta` (dem, was der Callback geschrieben hat), aber ohne
`content`-Feld. Dieses Event ist das **allererste** Event des SSE-Streams — noch vor jeglicher
Modellantwort. `_parse_sse_event` wirft darauf sofort einen `ValueError`, der die gesamte
Inferenz für den betroffenen Eval-Case scheitern lässt.

`agents-cli run` (die interaktive/nicht-eval CLI) verarbeitet dasselbe Event klaglos (druckt es
einfach als JSON) — das Problem ist spezifisch im `eval generate`-Codepfad.

## Erwartetes vs. tatsächliches Verhalten

- **Erwartet:** `agents-cli eval generate` läuft für jeden Agenten mit `before_agent_callback`
  (ein in ADK dokumentiertes, verbreitetes Pattern zur State-Initialisierung, siehe
  `google-agents-cli-eval`/`google-agents-cli-adk-code`-Skills → "The `before_agent_callback`
  Pattern (State Initialization)") genauso durch wie ohne.
- **Tatsächlich:** Der allererste Eval-Case scheitert sofort mit
  `Malformed agent event: missing content.`, ohne dass überhaupt eine Modellantwort generiert
  wurde. Betrifft **jeden** Case im Dataset gleichermaßen (0 von N Cases erfolgreich).

## Fundstelle im Code

`~/.local/share/uv/tools/google-agents-cli/lib/python3.14/site-packages/google/agents/cli/eval/cmd_generate.py`,
Funktion `_parse_sse_event` (Zeile ~174–200 in 1.4.0):

```python
def _parse_sse_event(event: dict) -> evals_types.AgentEvent:
    """Parse a ``/run_sse`` event into an ``AgentEvent``, or raise ``ValueError``.
    ...
    """
    message = event.get("errorMessage") or event.get("error")
    code = event.get("errorCode")
    if message or code:
        detail = message or "unknown error"
        raise Exception(
            f"Agent returned an error: {detail}" + (f" ({code})" if code else "")
        )

    missing = [field for field in ("author", "content") if not event.get(field)]
    if missing:
        raise ValueError(f"Malformed agent event: missing {' and '.join(missing)}.")

    return evals_types.AgentEvent(
        author=event.get("author"), content=event.get("content")
    )
```

Die Zeile `missing = [field for field in ("author", "content") if not event.get(field)]`
behandelt `content` als Pflichtfeld auf **jedem** SSE-Event — ADK garantiert das aber nicht für
Buchhaltungs-/Callback-Events.

## Minimale Reproduktion (unabhängig vom mk34-Projekt)

Erstellt mit `agents-cli scaffold create <name> --adk -y` (Standard-Scaffold, keine
Projekt-spezifischen Anpassungen). Einzige Änderung am generierten `app/agent.py`: ein
`before_agent_callback`, der eine einzige State-Variable setzt.

```python
# app/agent.py -- Diff gegenueber dem Scaffold-Default:

async def _init_state(callback_context) -> None:
    if "foo" not in callback_context.state:
        callback_context.state["foo"] = "bar"


root_agent = Agent(
    name="root_agent",
    model=Gemini(model=MODEL, retry_options=types.HttpRetryOptions(attempts=3)),
    instruction="You are a helpful AI assistant.",
    tools=[get_weather],
    before_agent_callback=_init_state,   # <-- einzige Aenderung
)
```

Dataset (`tests/eval/datasets/repro.json`):

```json
{
  "eval_cases": [
    {
      "eval_case_id": "hello",
      "prompt": {"role": "user", "parts": [{"text": "Hello, what can you help me with?"}]}
    }
  ]
}
```

Aufruf:

```bash
agents-cli eval generate --dataset tests/eval/datasets/repro.json -o /tmp/repro_traces
```

**Ergebnis (mit `before_agent_callback`):**

```
[generate] case[0] FAILED: Malformed agent event: missing content.
Inference summary: 0/1 succeeded, 1 failed.
Error: Inference failed: 0 of 1 cases succeeded.
```

**Kontroll-Lauf (identischer Code, nur `before_agent_callback=_init_state,` entfernt):**

```
[generate] case[0] done
Traces saved to /tmp/repro_traces
```

### Isolierte Ursache per Bisektion bestätigt

Folgende Kombinationen wurden **einzeln** getestet (jeweils gegen denselben Scaffold-Grundstand,
mit echter Gemini-API, `gemini-3.6-flash`) und liefen **erfolgreich** durch `eval generate`:

- `sub_agents=[<plain Agent>]`, unbenutzt
- `sub_agents=[<plain Agent>]` + tatsächliche Delegation via `transfer_to_agent`
- `tools=[AgentTool(<plain Agent>)]` + tatsächlicher Tool-Aufruf
- `sub_agents=[<SequentialAgent>]`, unbenutzt, kombiniert mit `AgentTool` + Tools
- `sub_agents=[<Agent mit output_schema>]`, unbenutzt

Erst das Hinzufügen von `before_agent_callback` (allein, ohne jede der obigen Strukturen) löst
den Fehler zuverlässig aus. Das ist die minimale, hinreichende Bedingung.

### Rohes SSE-Event (direkt gegen `/run_sse` erfasst, nicht über `agents-cli`)

```
data: {"invocationId":"e-0279d42b-4104-417c-92c8-ea16b518ec4a","author":"root_agent","actions":{"stateDelta":{"foo":"bar"},"artifactDelta":{},"requestedAuthConfigs":{},"requestedToolConfirmations":{}},"nodeInfo":{"path":"root_agent@1"},"id":"cae83b47-eff5-44e9-bd79-ccdb7a90de5d","timestamp":1787571240.619733}
```

Man beachte: `author` ist vorhanden, `actions.stateDelta` enthält exakt das, was
`before_agent_callback` geschrieben hat (`{"foo": "bar"}`), aber es gibt **kein** `content`-Feld
auf oberster Ebene. Das ist das Event, an dem `_parse_sse_event` scheitert — es ist das
allererste Event des Streams, vor jeder Modellantwort.

## Umgebung

| Komponente | Version |
|---|---|
| `agents-cli` | 1.4.0 (auch mit 1.3.1 reproduzierbar — dieselbe `missing`-Prüfung existiert dort unveraendert) |
| `google-adk` | 2.7.0 |
| Python (Projekt-`.venv`) | 3.13.14 |
| Modell | `gemini-3.6-flash` (Scaffold-Default), reproduziert unabhaengig vom Modell |
| Betriebssystem | macOS 26.5.2 (Darwin) |
| Provider | Gemini API / AI Studio (`GEMINI_API_KEY`), kein Vertex AI |

## Auswirkung auf das mk34-Projekt

`app/agent.py`s `root_agent` (Orchestrator, seit Plan 2/TASK-007) hat
`before_agent_callback=initialize_state` (siehe `app/callbacks.py`, Plan 2/TASK-002) --
ein bewusst gewaehltes, in ADK dokumentiertes State-Initialisierungs-Pattern
(`google-agents-cli-eval`-Skill, Abschnitt "Common Gotchas" → "The `before_agent_callback`
Pattern"). Dieses Pattern laesst sich nicht ohne architektonischen Rueckschritt entfernen (siehe
TASK-002/007-Akzeptanzkriterien: "Kein `KeyError` beim ersten Turn"). Damit ist
`agents-cli eval generate` -- und in der Folge auch `eval run`, das `generate` intern aufruft --
fuer das gesamte mk34-Projekt aktuell nicht nutzbar.

Kombiniert mit dem separat dokumentierten `eval grade`-Bug (Plan 2/TASK-003-Walkthrough) ist die
gesamte lokale Eval-Befehlskette (`agents-cli eval run/generate/grade`) derzeit nicht lauffaehig.
Betroffene/blockierte Akzeptanzkriterien: Plan 2/TASK-003 (Score-Tabelle `task_success`), TASK-010
(`tool_use_quality`/`trajectory_quality`-Score-Tabellen), TASK-011 (0 False Negatives auf
`continuity.json`) sowie -- vorausschauend -- alle Eval-Gates in Plan 3 und Plan 4, die auf
demselben `agents-cli eval`-Befehlspfad aufbauen.

## Vorgeschlagener Fix (fuer ein spaeteres Upstream-Issue, noch nicht eingereicht)

`_parse_sse_event` sollte Events ohne `content`, aber mit gueltigem `author` und (optional)
`actions.stateDelta`/`actions.endOfAgent` als reine Buchhaltungs-/Callback-Events erkennen und
entweder (a) uebergehen (nicht in den Trace aufnehmen, da sie keine `AgentEvent`-relevanten
Modell-/Tool-Inhalte tragen) oder (b) mit einem synthetischen leeren `content` versehen, statt
einen `ValueError` zu werfen. Alternativ: `content` in `AgentEvent`-Konstruktion optional machen,
falls die nachgelagerte Datenstruktur das zulaesst.

## Hinweis zur Vertraulichkeit dieses Reports

Dieser Report liegt **ausschliesslich lokal** in diesem Repository. Er wurde **nicht** als
GitHub-Issue oder in anderer Form extern eingereicht -- das ist eine bewusste Entscheidung, die
dem Projekt-User vorbehalten bleibt.
