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

"""Pydantic-Schemas fuer strukturierte Agenten-Ausgaben (`output_schema`).

`output_schema` deaktiviert Tool-Calling und Delegation auf dem Agenten, der
es setzt (siehe ADK-Cheatsheet) -- deshalb laufen die Agenten, die diese
Schemas nutzen, immer zweistufig: ein Agent mit Tools sammelt Kontext
(`output_key="..._raw"`), ein nachgelagerter schemabewehrter Agent
formalisiert das Ergebnis.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SceneBeat(BaseModel):
    """Ein einzelner Szenen-Beat, wie ihn der Plot Agent liefert (TASK-004)."""

    chapter: int = Field(description="1-basierte Kapitelnummer.")
    scene: int = Field(description="1-basierte Szenennummer innerhalb des Kapitels.")
    pov_character: str = Field(description="Name der Point-of-View-Figur der Szene.")
    location: str = Field(description="Schauplatz der Szene.")
    beat: str = Field(description="Kurzbeschreibung, was in der Szene passiert.")
    turning_point: bool = Field(description="Ist dieser Beat ein Wendepunkt?")
    tension_level: int = Field(description="Spannungslevel 1 (niedrig) bis 10 (hoch).")
    characters_present: list[str] = Field(
        description="Namen aller in der Szene anwesenden Figuren."
    )


class SceneBeatList(BaseModel):
    """Wrapper, da `output_schema` ein einzelnes Pydantic-Modell erwartet,
    der Plot Agent aber eine Liste von Beats pro Phase liefert."""

    beats: list[SceneBeat] = Field(
        description="Alle Szenen-Beats der angefragten Phase."
    )


class ContinuityConflict(BaseModel):
    """Ein einzelner Kontinuitaets-Konflikt (TASK-011)."""

    type: str = Field(
        description=(
            "Art des Konflikts, z. B. 'Wissen zu frueh', 'Zeitsprung', "
            "'Parallelitaets-Konflikt', 'Regelverstoss'."
        )
    )
    evidence: str = Field(description="Die widerspruechliche Aussage im neuen Text.")
    reference: str = Field(
        description="Referenz auf die widersprechende Vorpassage, z. B. 'Kapitel 3, Szene 1'."
    )
    severity: Literal["low", "medium", "high"] = Field(
        description="Schweregrad des Konflikts."
    )


class ContinuityReport(BaseModel):
    """Strukturiertes Ergebnis des Continuity Agent (TASK-011)."""

    conflicts: list[ContinuityConflict] = Field(
        default_factory=list,
        description="Gefundene Kontinuitaets-Konflikte; leer, wenn keine gefunden wurden.",
    )


class EditorVerdict(BaseModel):
    """Strukturiertes Lektorats-Verdikt des Editor Agent (TASK-006)."""

    grade: Literal["pass", "needs_revision"] = Field(
        description="Gesamturteil: besteht der Text die Qualitaetspruefung?"
    )
    issues: list[str] = Field(
        default_factory=list,
        description="Konkrete, benannte Probleme (Register, Pacing, Show-dont-tell, ...).",
    )
    revised_text: str = Field(
        description="Die ueberarbeitete Fassung des Textes (Sprache/Stil, keine Plotaenderungen)."
    )
