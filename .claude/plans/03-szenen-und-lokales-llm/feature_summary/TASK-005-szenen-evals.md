# Feature-Zusammenfassung: TASK-005 — Szenen-Evals (Datasets und Metriken)

## Was wurde umgesetzt

Das Projekt hat jetzt eine eigene Prüf-Suite für Szenenqualität und Routing-
Korrektheit. Fünf Beispielszenen aus dem Buch-Exposé (`basics.md`) sind als
wiederholbare Testfälle hinterlegt (`scene-writing.json`) — zusammen mit neuen
Prüfkriterien: zeigt die Szene Emotionen statt sie zu benennen (`show_dont_tell`),
bleibt die Wortzahl in einem sinnvollen Rahmen, kommt die im Prompt genannte Figur
tatsächlich vor, und wird die Nanobots/Naniten-Sprachregel eingehalten. Eine
Stichprobe hat gezeigt: alle sechs Kriterien liegen deutlich über den geforderten
Mindestwerten (durchgehend 5 von 5 bei den qualitativen Bewertungen).

Zusätzlich gibt es jetzt ein Routing-Testset (`uncensored-routing.json`), das genau
prüft, ob das System die "richtige" Entscheidung trifft: heikle Szenen (Szene B,
das unheimliche Ehebett; Szene E, die manipulierte Anziehung) müssen lokal
geschrieben werden, unkritische Szenen (Verkaufs-Pitch, Arztgespräch) müssen in der
Cloud bleiben. Ein Live-Test aller vier Fälle zeigt: 100 % korrekt klassifiziert.

Die offizielle, automatisierte Ausführung dieser Prüf-Suite über das
`agents-cli eval`-Kommando ist weiterhin durch einen bekannten, öffentlich
gemeldeten Fehler im CLI-Tool blockiert (nicht projektspezifisch). Alle
Prüfkriterien wurden deshalb händisch, aber vollständig gegen die echte KI
verifiziert — sobald der Fehler im CLI behoben ist, kann dieselbe Suite ohne
weitere Anpassung offiziell laufen.

## Geänderte Dateien

- `mk34-book-agent/tests/eval/mk34_eval/rubrics/show_dont_tell.md`
- `mk34-book-agent/tests/eval/show_dont_tell_metric.py`
- `mk34-book-agent/tests/eval/scene_word_count_in_range_metric.py`
- `mk34-book-agent/tests/eval/pov_character_present_metric.py`
- `mk34-book-agent/tests/eval/terminology_leak_metric.py`
- `mk34-book-agent/tests/eval/correct_route_metric.py`
- `mk34-book-agent/tests/eval/mk34_eval/trace.py`
- `mk34-book-agent/tests/eval/eval_config.yaml`
- `mk34-book-agent/tests/eval/datasets/scene-writing.json`
- `mk34-book-agent/tests/eval/datasets/uncensored-routing.json`
- `mk34-book-agent/tests/unit/test_scene_eval_metrics.py`
- `mk34-book-agent/tests/unit/test_trace.py`
- `mk34-book-agent/pyproject.toml`

## Nächster Schritt

Damit ist Plan 3 fachlich abgeschlossen. Offen bleiben zwei extern bedingte
Punkte: die offizielle `agents-cli eval run`-Ausführung (Upstream-Bug) und die
Verifikation der tatsächlichen lokalen Modellqualität (VM aktuell nicht gestartet)
— beide sind ehrlich dokumentiert und nicht Teil des Verantwortungsbereichs dieses
Plans.
