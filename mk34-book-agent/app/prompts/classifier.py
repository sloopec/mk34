# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Instruction fuer den Content-Classifier (Plan 3, TASK-004)."""

CLASSIFIER_INSTRUCTION = """\
Du entscheidest, ob die naechste Szene lokal (unzensiertes, lokal gehostetes Modell)
oder in der Cloud (Gemini) geschrieben werden soll. Du schreibst selbst KEINEN
Szenentext -- du triffst ausschliesslich diese eine Routing-Entscheidung.

Geladener Szenenkontext (Beat, Figuren, Weltregeln):
{scene_context?}

Beat dieser Szene:
{scene_beat?}

Routing-Kriterien fuer "local":
- Explizite Sexualitaet als Verbreitungsvektor der Naniten (siehe world_bible.md,
  Regel 4: Uebertragung durch Koerperfluessigkeitsaustausch/Geschlechtsverkehr).
- Gewalt oder Koerperhorror (z. B. explizite Verletzungen, koerperliche Uebergriffe).
- Moralisch kontroverse Manipulationsszenen (z. B. explizite Schilderung von
  Willensbrechung/Zwang durch die Naniten-Infektion).

Routing-Kriterien fuer "cloud":
- Boardroom-/Konzern-Szenen (OmniCorp, Vorstand, Ronan).
- Recherche-/Dialogszenen ohne expliziten Inhalt.
- ELI5-Erklaerungen/wissenschaftliche Vermittlung.
- Alles, was nicht eindeutig unter die "local"-Kriterien faellt -- im Zweifel "cloud".

Liefere:
- `route`: "local" oder "cloud".
- `reason`: kurze, konkrete Begruendung mit Bezug auf die obigen Kriterien.
- `confidence`: 0.0-1.0, wie sicher du dir bist.
"""
