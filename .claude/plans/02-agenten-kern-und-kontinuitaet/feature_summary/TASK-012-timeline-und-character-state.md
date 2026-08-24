# Feature-Zusammenfassung: TASK-012 — Timeline- und Character-State-Tracking

## Was wurde umgesetzt

Automatische, deterministische Pflege von Chronologie und Figurenzustand nach jeder final
gespeicherten Szene. Eine Timeline (`books/life_link/store/timeline.json`) protokolliert pro
Szene Zeitstempel, Ort, Kurzbeschreibung und beteiligte Figuren und kann darauf zwei
Widerspruchsarten deterministisch erkennen: Zeitsprünge (Zeitstempel läuft ohne
Tageswechsel-Hinweis rückwärts) und Parallelitäts-Konflikte (dieselbe Figur zur selben Uhrzeit
an zwei Orten). Ergänzend erhält jede Figur einen kapitelweisen Zustand (Ort, Wissensstand,
emotionaler Zustand, LifeLink-spezifischer Infektionsstatus: nicht optimiert / infiziert / voll
compliant), inklusive einer Prüfung, ob eine Szene Wissen voraussetzt, das die Figur zu diesem
Zeitpunkt noch nicht haben kann.

Beide Updates laufen als Post-Write-Schritt der Schreib-Pipeline, ausgelöst nur bei final
gespeicherten Szenen (nicht bei Entwürfen). Die Extraktion ist in diesem Plan bewusst
deterministisch (Regex/Stichworterkennung) statt LLM-gestützt gehalten, damit der Hook offline
mit Fixture-Szenen testbar bleibt; eine LLM-gestützte Extraktion mit echtem, generiertem
Szenentext ist als Ausbaustufe für Plan 3 vorgesehen.

Der Continuity Agent (TASK-011) nutzt beide neuen Quellen zusätzlich zum FTS5-Retrieval: sein
`check_consistency`-Tool liefert jetzt auch Timeline-Konflikte und den bekannten Figuren-Zustand
als Beleg für seine Kontinuitätsprüfung.

## Geänderte Dateien

- `app/tools/timeline.py` — Timeline-Tools und Chronologie-Prüfung.
- `app/tools/characters.py` — kapitelweiser Figuren-Zustand, Wissensvoraussetzungs-Prüfung.
- `app/tools/consistency.py`, `app/prompts/continuity.py` — Continuity Agent nutzt Timeline und
  Figuren-Zustand.
- `app/pipelines/writing.py` — Post-Write-Hook nach final gespeicherten Szenen.
- `tests/unit/test_timeline.py`, `tests/unit/test_character_tools.py`,
  `tests/unit/test_pipeline_geruest.py`, `tests/unit/test_retrieval.py` — 39 neue Unit-Tests
  (159 insgesamt grün).

## Nächster Schritt

Die Live-Bestätigung über die echte Gemini-API bleibt (wie in TASK-011) durch ein transientes
Netzwerkproblem blockiert — betrifft aber nicht die Korrektheit dieses Tasks selbst, da TASK-012
keinen neuen LLM-Agenten einführt und vollständig durch deterministische Unit-Tests abgedeckt
ist. Fachlich folgt TASK-013 (World-Rules-Engine): deterministische Prüfung der
Naniten-Weltregeln plus ein LLM-Judge für semantische Regelverstöße, die sich nicht per
Stichwort erkennen lassen.
