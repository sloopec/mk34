# TASK-007: Lokaler Smoke-Test und Lint
Status: ⏳ pending
Depends-on: [TASK-006]
Parallel: no

## Description
Verifizieren, dass das Grundgeruest laeuft — bevor Eval aufgesetzt wird.

```bash
uv sync
agents-cli lint
agents-cli run "Schreibe Kapitel 1, Szene 1"
agents-cli run "Wer ist Dr. Elias Voss und was ist seine Rolle?" -v
agents-cli playground        # interaktive Durchsicht
```

`-v` gibt die vollstaendigen Event-JSONs aus — damit pruefen, ob die Tools tatsaechlich aufgerufen werden und mit welchen Argumenten (haeufigster Frueh-Fehler: das Modell erfindet Kontext statt `load_scene_context` aufzurufen).

Zusaetzlich einen Lauf **ohne** laufende lokale VM machen und pruefen, dass der Router sauber meldet statt still auf Cloud auszuweichen.

Dies ist ein Smoke-Test, **kein** Verhaltenstest. Keine pytest-Assertions auf LLM-Textinhalte.

## Acceptance Criteria
- [ ] `agents-cli lint` ist gruen
- [ ] `uv run pytest` (Unit-Tests aus TASK-002/004/005) ist gruen
- [ ] Beide `agents-cli run`-Prompts liefern plausible Antworten
- [ ] Im `-v`-Output sind die erwarteten Tool-Calls mit korrekten Argumenten sichtbar
- [ ] `agents-cli playground` startet und der Agent ist bedienbar
- [ ] Lauf ohne lokale VM erzeugt eine klare Fehlermeldung, keinen stillen Cloud-Fallback

## Affected Files
- keine Codeaenderung erwartet; ggf. Fixes an `app/prompts/scene.py`, `app/tools/*`
