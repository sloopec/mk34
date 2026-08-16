# TASK-018: Content-Klassifikation und lokales Routing
Status: ⏳ ausstehend
Abhängig von: [TASK-016, TASK-017]
Parallel: nein

## Beschreibung
Kernstueck von Phase 4: automatische Entscheidung, ob eine Szene lokal (unzensiert) oder in der Cloud geschrieben wird.

**Classifier-Agent:**
- Input: Plot-Beat, beteiligte Figuren, erwarteter Inhalt
- Output: `{"route": "local" | "cloud", "reason": "...", "confidence": 0.0-1.0}`
- Modell: `model_for("classifier")` → `anthropic/claude-haiku-4-5` (billig, haeufig)
- `output_schema` fuer strukturierte Entscheidung
- Schreibt nach `state["route"]`, das der Scene Agent ueber `model_for("scene")` konsumiert

**Routing-Kriterien** (aus dem Stoff abgeleitet): explizite Sexualitaet als Verbreitungsvektor, Gewalt, Koerperhorror, moralisch kontroverse Manipulationsszenen → lokal. Boardroom, Recherche, Dialogszenen, ELI5-Erklaerungen → Cloud.

**Manueller Override:** `--model local` / `--model opus` bzw. im Prompt („schreibe das lokal"). Override schlaegt den Classifier immer.

**Kein stiller Fallback:** Ist die lokale VM nicht erreichbar, bricht der Lauf mit Handlungsanweisung ab. Cloud-Fallback nur bei `MK34_ALLOW_CLOUD_FALLBACK=true` und mit expliziter Warnung — sonst landet eine unzensierte Szene in einer Refusal oder in abgeschwaechtem Text.

**Refusal als Signal:** Kommt trotz Cloud-Routing ein `stop_reason: refusal`, wird der Fall in `uncensored-routing.json` aufgenommen und die Klassifikationsregel nachgeschaerft.

**Performance** (laut `docs/LOCAL_MODEL_VM_SETUP.md`: 5–15 tok/s, 2–5 Min pro Szene):
- Streaming-Output aktivieren
- `--ctx-size` und `--threads` gegen die reale Hardware tunen
- Kontext-Caching fuer die stabilen Kanon-Teile

## Akzeptanzkriterien
- [ ] Classifier liefert strukturierte Routing-Entscheidungen mit Begruendung
- [ ] `tests/eval/datasets/uncensored-routing.json` (Szene B und E aus `basics.md` u. a.) wird zu 100 % korrekt geroutet
- [ ] Manueller Override funktioniert und schlaegt den Classifier
- [ ] Lokaler Ausfall fuehrt zu klarer Fehlermeldung, nicht zu stillem Cloud-Fallback
- [ ] Streaming ist aktiv; eine 1000-Woerter-Szene bleibt im dokumentierten Zeitrahmen
- [ ] Der Preflight-Health-Check laeuft, bevor die Pipeline startet

## Betroffene Dateien
- `app/agents/classifier_agent.py`
- `app/models/router.py`
- `app/pipelines/writing.py`
- `tests/eval/datasets/uncensored-routing.json`
- `docs/LOCAL_MODEL_VM_SETUP.md` (Tuning-Ergaenzungen)
