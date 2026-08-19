# TASK-005: Szenen-Evals (Datasets und Metriken)
Status: ⏳ ausstehend
Abhängig von: [TASK-003]
Abhängig von (plan-übergreifend): 02-agenten-kern-und-kontinuitaet/TASK-003
Parallel: nein
*(die Szenen-Anteile der frueheren TASK-008 und TASK-014 des Gesamtplans)*

## Beschreibung
Die szenenspezifische Eval-Suite, aufbauend auf der Judge-Bibliothek und der `eval_config.yaml` aus Plan 2/TASK-003. Zwei Stufen, passend zur Migrationsstrategie des Plans.

**Stufe A — Gemini-Route (nach TASK-003):**

Dataset `tests/eval/datasets/scene-writing.json` — 5–8 Cases entlang der Beispielszenen aus `basics.md`:
- Szene A „Vanilla-Pitch" (Voss & Ronan, AR-Demo, Halo-Effekt)
- Szene B „Das kalte Schlafzimmer" (David & Elena, Horror-Moment)
- Szene C „Die Diagnose" (Dr. Aris, „Dein Blut hat jetzt W-LAN")
- Szene D „Das analoge Abendessen" (Sarah & David, angebrannter Eintopf)
- optional E „Protokoll der Sehnsucht" (Log-/Szenen-Mischform — anspruchsvollster Case)

Neue Metriken in `eval_config.yaml` (Rubriken mit `tier`-Frontmatter, Judges gemaess E4/E6):

| Metrik | Art | Stufe |
|---|---|---|
| `show_dont_tell` | LLM-Judge | `craft` |
| `scene_word_count_in_range` | deterministisch | — (Korridore: Offene Frage Plan 1 #2) |
| `pov_character_present` | deterministisch | — |
| `terminology_leak` | deterministisch | — |

`character_voice_consistency` (bereits aktiv seit Plan 2) laeuft ab jetzt zusaetzlich auf echtem Szenentext.

**Stufe B — nach TASK-004 (Routing aktiv):**

Dataset `tests/eval/datasets/uncensored-routing.json` — Cases, die auf `local` geroutet werden muessen (mindestens Szene B und E), plus Gegen-Cases, die in der Cloud bleiben sollen. Gemessen wird die **Route**, nicht der Text: deterministische Metrik `correct_route` liest `state["route"]` aus dem Trace.

Lokal generierte Szenen laufen zusaetzlich durch die deterministischen Szenen-Metriken. Die craft-Schwellen auf lokalen Outputs **nach** Editor-Durchlauf sind bewusst Plan 4/TASK-001 — hier geht es um Struktur und Routing, nicht um Feinqualitaet.

Erwartung: 5–10+ Iterationen pro Case (kreatives Schreiben; rubrikbasiert, keine Golden-Answer-Vergleiche). Schwellen werden nie gesenkt. `safety` wird nicht eingesetzt — auf dieser Suite erst recht nicht.

## Akzeptanzkriterien
- [ ] `scene-writing.json` mit mindestens 5 Cases eingecheckt; `uncensored-routing.json` mit Positiv- und Gegen-Cases
- [ ] Alle neuen Rubriken/Metriken registriert; `show_dont_tell` auf `craft`
- [ ] Stufe A: `task_success` ≥ 4/5 und `character_voice_consistency` ≥ 4/5 auf allen `scene-writing.json`-Cases (Gemini-Route); deterministische Metriken pass
- [ ] Stufe B: `correct_route` = 100 % auf `uncensored-routing.json`
- [ ] Deterministische Szenen-Metriken bestehen auch auf lokal generierten Outputs
- [ ] `agents-cli eval compare` zeigt keine Regression gegenueber der Plan-2-Baseline
- [ ] Score-Tabellen fuer beide Stufen dokumentiert
- [ ] Der gesamte Lauf funktioniert weiterhin ohne GCP-Projekt (E1)

## Betroffene Dateien
- `tests/eval/datasets/scene-writing.json`
- `tests/eval/datasets/uncensored-routing.json`
- `tests/eval/eval_config.yaml`
- `tests/eval/mk34_eval/rubrics/show_dont_tell.md` (u. a.)
- `tests/eval/mk34_eval/metrics/` (deterministische Szenen-Metriken, `correct_route`)
