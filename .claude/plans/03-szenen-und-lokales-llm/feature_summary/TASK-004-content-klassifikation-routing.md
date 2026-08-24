# Feature-Zusammenfassung: TASK-004 — Content-Klassifikation und lokales Routing

## Was wurde umgesetzt

Das System entscheidet jetzt automatisch, ob eine Szene lokal (auf dem unzensierten,
selbstgehosteten Modell) oder in der Cloud (Gemini) geschrieben werden soll — und
erklärt seine Entscheidung nachvollziehbar. Ein neuer Klassifikations-Schritt prüft
vor jedem Szenenschreiben Inhalt und Kontext gegen klare Kriterien (explizite
Sexualität, Gewalt, Körperhorror oder moralisch kontroverse Manipulation → lokal;
Boardroom-, Recherche- und Erklärszenen → Cloud) und liefert Begründung sowie
Konfidenz mit. Wer möchte, kann diese automatische Entscheidung jederzeit manuell
übersteuern ("--model local" oder "schreibe das lokal").

Wichtiger als die Klassifikation selbst ist die Sicherheitsgarantie: ist eine Szene
als "lokal" eingestuft, aber die lokale Infrastruktur (die VM mit dem unzensierten
Modell) gerade nicht erreichbar, bricht das System kontrolliert mit einer klaren
Handlungsanweisung ab, statt die Szene unbemerkt auf ein Cloud-Modell auszuweichen —
eine unzensierte Szene auf einem Cloud-Modell würde ohnehin meist verweigert oder
abgeschwächt. Das wurde in einem echten Testlauf bestätigt: der manuelle
"--model local"-Override wurde korrekt erkannt, und da die VM aktuell nicht läuft,
stoppte das System sauber mit exakt dieser Anweisung — kein Absturz, kein stiller
Fallback.

Zusätzlich erkennt das System jetzt automatisch, wenn ein Cloud-Modell eine Szene
verweigert (Safety-Block) — ein Signal dafür, dass die Klassifikationsregel für
diesen Fall nachgeschärft werden sollte.

## Geänderte Dateien

- `mk34-book-agent/app/schemas.py`
- `mk34-book-agent/app/prompts/classifier.py`
- `mk34-book-agent/app/agents/classifier_agent.py`
- `mk34-book-agent/app/models/router.py`
- `mk34-book-agent/app/agents/scene_agent.py`
- `mk34-book-agent/app/pipelines/writing.py`
- `docs/LOCAL_MODEL_VM_SETUP.md`
- `mk34-book-agent/tests/unit/test_classifier_agent.py`
- `mk34-book-agent/tests/unit/test_is_refusal.py`
- `mk34-book-agent/tests/unit/test_pipeline_geruest.py`
- `mk34-book-agent/tests/unit/test_scene_agent.py`
- `mk34-book-agent/pyproject.toml`

## Nächster Schritt

TASK-005 (Stufe B) kann jetzt das Routing-Dataset (`uncensored-routing.json`)
anlegen und gegen die tatsächliche Klassifikations-/Routing-Logik prüfen. Die
vollständige Verifikation der lokalen Route (Zeitrahmen, tatsächliche
Szenenqualität) bleibt offen, bis die VM einmal gestartet wird.
