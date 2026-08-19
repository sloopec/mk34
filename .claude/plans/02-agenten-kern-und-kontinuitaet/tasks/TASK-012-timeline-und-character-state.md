# TASK-012: Timeline- und Character-State-Tracking
Status: ⏳ ausstehend
Abhängig von: [TASK-011]
Parallel: ja
*(vormals TASK-016 im Gesamtplan)*

## Beschreibung
Automatische Pflege von Chronologie und Figurenzustand nach jeder geschriebenen Szene.

**Timeline** (`app/tools/timeline.py`, Persistenz `books/life_link/store/timeline.json`):
- `append_event(chapter, scene, timestamp, location, description, characters)`
- `read_timeline(from_chapter, to_chapter)`
- `validate_chronology()` — erkennt Zeitspruenge und Parallelitaets-Konflikte (Figur an zwei Orten gleichzeitig)
- Zeitangaben werden aus dem Szenentext extrahiert (vgl. `20:43 Uhr` in Szene E)

**Character-State** (Erweiterung `app/tools/characters.py`):
Pro Kapitel je Figur: Ort, Wissensstand, emotionaler Zustand, Infektionsstatus (LifeLink-spezifisch: nicht optimiert / infiziert / voll compliant).
- Automatisches Update nach jeder geschriebenen Szene
- Warnung, wenn eine Szene Wissen voraussetzt, das die Figur zu diesem Zeitpunkt nicht haben kann

Beide Updates laufen als Post-Write-Schritt der Pipeline, nicht als freie LLM-Entscheidung — die Extraktion ist LLM-gestuetzt, das Schreiben deterministisch ueber Tools. Der Post-Write-Hook wird hier am Pipeline-Geruest (TASK-008) implementiert und mit Fixture-Szenen getestet; scharf geschaltet wird er mit dem Szenen-Schritt in Plan 3.

## Akzeptanzkriterien
- [ ] `timeline.json` wird nach jedem `write_scene` automatisch fortgeschrieben
- [ ] `validate_chronology()` erkennt einen kuenstlich eingebauten Zeitsprung und einen Parallelitaets-Konflikt
- [ ] `knowledge_state` pro Figur und Kapitel wird gepflegt
- [ ] Der Continuity Agent nutzt beide Quellen in `check_consistency`
- [ ] pytest deckt Timeline-Validierung mit Fixtures ab

## Betroffene Dateien
- `app/tools/timeline.py`
- `app/tools/characters.py`
- `books/life_link/store/timeline.json`
- `app/pipelines/writing.py` (Post-Write-Schritt)
- `tests/unit/test_timeline.py`
