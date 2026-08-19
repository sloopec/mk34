# TASK-004: Content-Klassifikation und lokales Routing
Status: ⏳ ausstehend
Abhängig von: [TASK-001, TASK-003]
Abhängig von (plan-übergreifend): agenten-kern-und-kontinuitaet/TASK-012, agenten-kern-und-kontinuitaet/TASK-013
Parallel: nein
*(vormals TASK-018 im Gesamtplan)*

## Beschreibung
Kernstueck des Plans: automatische Entscheidung, ob eine Szene lokal (unzensiert) oder in der Cloud geschrieben wird.

**Classifier-Agent:**
- Input: Plot-Beat, beteiligte Figuren, erwarteter Inhalt
- Output: `{"route": "local" | "cloud", "reason": "...", "confidence": 0.0-1.0}`
- Modell: `model_for("classifier")` → Start `gemini-3.5-flash-lite` (E6, billig und haeufig); spaeter `anthropic/claude-haiku-4-5`
- `output_schema` fuer strukturierte Entscheidung
- Schreibt nach `state["route"]`, das `model_for("scene")` (TASK-001) konsumiert

**Routing-Kriterien** (aus dem Stoff abgeleitet): explizite Sexualitaet als Verbreitungsvektor, Gewalt, Koerperhorror, moralisch kontroverse Manipulationsszenen → lokal. Boardroom, Recherche, Dialogszenen, ELI5-Erklaerungen → Cloud.

**Manueller Override:** `--model local` / `--model cloud` bzw. im Prompt („schreibe das lokal"). Override schlaegt den Classifier immer.

**Kein stiller Fallback:** Ist die lokale VM nicht erreichbar, bricht der Lauf mit Handlungsanweisung ab (Verhalten aus TASK-001). Cloud-Fallback nur bei `MK34_ALLOW_CLOUD_FALLBACK=true` und mit expliziter Warnung.

**Refusal als Signal (provider-uebergreifend, Entscheidung E9):** Kommt trotz Cloud-Routing eine Verweigerung, wird der Fall in `uncensored-routing.json` aufgenommen und die Klassifikationsregel nachgeschaerft. Die Erkennung ist verbindlich fuer beide Signalformen zu bauen:
- **Gemini:** `finish_reason` `SAFETY`/`PROHIBITED_CONTENT` auf dem Kandidaten sowie leere Antwort mit `prompt_feedback.block_reason` (Prompt-seitiger Block) — beides zaehlt als Refusal.
- **Claude (spaeter):** `stop_reason: refusal`.
Die Erkennung lebt an einer Stelle (`is_refusal(response) -> bool` im Router-/Pipeline-Code), damit die Provider-Umschaltung (E6) sie nicht dupliziert.

**Performance lokale Route** (laut `docs/LOCAL_MODEL_VM_SETUP.md`: 5–15 tok/s, 2–5 Min pro Szene):
- Streaming-Output aktivieren
- `--ctx-size` und `--threads` gegen die reale Hardware tunen
- Kontext-Caching fuer die stabilen Kanon-Teile

## Akzeptanzkriterien
- [ ] Classifier liefert strukturierte Routing-Entscheidungen mit Begruendung
- [ ] `tests/eval/datasets/uncensored-routing.json` (mindestens Szene B und E aus `basics.md`) wird zu 100 % korrekt geroutet (Dataset entsteht in TASK-005)
- [ ] Manueller Override funktioniert und schlaegt den Classifier
- [ ] Lokaler Ausfall fuehrt zu klarer Fehlermeldung, nicht zu stillem Cloud-Fallback
- [ ] **E9:** `is_refusal(...)` erkennt beide Gemini-Signalformen (`finish_reason` `SAFETY`/`PROHIBITED_CONTENT` und `prompt_feedback.block_reason`) und ist fuer Claudes `stop_reason: refusal` vorbereitet (Unit-Test mit gestubbten Responses beider Provider); erkannte Faelle werden geloggt und als Nachschaerfungs-Fall in `uncensored-routing.json` abgelegt
- [ ] Streaming ist aktiv; eine 1000-Woerter-Szene bleibt im dokumentierten Zeitrahmen
- [ ] Der Preflight-Health-Check laeuft, bevor die Pipeline startet

## Betroffene Dateien
- `app/agents/classifier_agent.py`
- `app/models/router.py`
- `app/pipelines/writing.py`
- `docs/LOCAL_MODEL_VM_SETUP.md` (Tuning-Ergaenzungen)
