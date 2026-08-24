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

"""Unit tests for the Plan 3/TASK-005 deterministic Szenen-Eval-Metriken
(`tests/eval/*_metric.py`) und die `show_dont_tell`-Rubrik.

Diese Module sind `custom_function_file`-Skripte fuer `agents-cli eval
grade` -- sie liegen unter `tests/eval/`, nicht `app/`, und sind bewusst
`app`-frei (siehe deren Docstrings). Import-Pfad-Setup analog zu
`tests/unit/test_judge.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

_EVAL_DIR = Path(__file__).resolve().parent.parent / "eval"
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

import pov_character_present_metric  # noqa: E402
import scene_word_count_in_range_metric  # noqa: E402
import terminology_leak_metric  # noqa: E402
from mk34_eval.judge import load_rubric  # noqa: E402


def _instance(prompt_text: str, response_text: str) -> dict:
    return {
        "prompt": {"role": "user", "parts": [{"text": prompt_text}]},
        "response": {"role": "model", "parts": [{"text": response_text}]},
    }


# --- pov_character_present ---------------------------------------------------


def test_pov_character_present_passes_when_prompt_character_appears() -> None:
    instance = _instance(
        "Schreibe eine Szene mit David und Dr. Sarah Lin.",
        "David sah Sarah an und schwieg.",
    )
    result = pov_character_present_metric.evaluate(instance)
    assert result["score"] == 1


def test_pov_character_present_fails_when_prompt_character_missing() -> None:
    instance = _instance(
        "Schreibe eine Szene mit David.",
        "Ronan sprach mit dem Vorstand ueber KPIs.",
    )
    result = pov_character_present_metric.evaluate(instance)
    assert result["score"] == 0
    assert "David" in result["explanation"]


def test_pov_character_present_passes_vacuously_without_named_character() -> None:
    instance = _instance(
        "Schreibe eine Szene ueber das Wetter.",
        "Es regnete den ganzen Tag.",
    )
    result = pov_character_present_metric.evaluate(instance)
    assert result["score"] == 1
    assert "nicht pruefbar" in result["explanation"]


def test_pov_character_present_matches_name_fragment() -> None:
    """ "Sarah" im Prompt (kurze Nennung) matcht "Dr. Sarah Lin" im Text und
    umgekehrt -- Namensbestandteil-Matching wie bei `characters_mentioned`."""
    instance = _instance(
        "Schreibe eine Szene mit Sarah.",
        "Dr. Sarah Lin betrat das Labor.",
    )
    result = pov_character_present_metric.evaluate(instance)
    assert result["score"] == 1


# --- terminology_leak ---------------------------------------------------------


def test_terminology_leak_flags_david_saying_naniten() -> None:
    instance = _instance(
        "Schreibe eine Szene mit David.",
        "David sagte: Ich habe von den Naniten gehoert.",
    )
    result = terminology_leak_metric.evaluate(instance)
    assert result["score"] == 0
    assert "Naniten" in result["explanation"]


def test_terminology_leak_flags_scientist_saying_nanobots() -> None:
    instance = _instance(
        "Schreibe eine Szene mit Sarah.",
        "Sarah erklaerte: Die Nanobots funktionieren einwandfrei.",
    )
    result = terminology_leak_metric.evaluate(instance)
    assert result["score"] == 0
    assert "Nanobots" in result["explanation"]


def test_terminology_leak_passes_on_correct_register() -> None:
    # Bewusst in getrennten Saetzen ohne Namensueberschneidung -- die
    # Metrik ist eine Satz-Naeherung (Figurenname + Begriff im selben Satz,
    # keine echte Sprecherzuordnung, siehe Modul-Docstring); ein Satz, der
    # sowohl "David" als auch "Naniten" enthaelt, waere auch bei korrekter
    # Sprecherzuordnung ein (falsch-positiver) Treffer dieser Naeherung.
    instance = _instance(
        "Schreibe eine Szene mit David und Sarah.",
        "David fragte nach den Nanobots. Sie erklaerte die Funktionsweise praezise.",
    )
    result = terminology_leak_metric.evaluate(instance)
    assert result["score"] == 1


# --- scene_word_count_in_range -------------------------------------------------


def test_scene_word_count_in_range_passes_within_corridor() -> None:
    text = " ".join(["Wort"] * 500)
    instance = _instance("Schreibe eine Szene.", text)
    result = scene_word_count_in_range_metric.evaluate(instance)
    assert result["score"] == 1


def test_scene_word_count_in_range_fails_when_too_short() -> None:
    instance = _instance("Schreibe eine Szene.", "Ein sehr kurzer Text.")
    result = scene_word_count_in_range_metric.evaluate(instance)
    assert result["score"] == 0


def test_scene_word_count_in_range_fails_when_too_long() -> None:
    text = " ".join(["Wort"] * 2500)
    instance = _instance("Schreibe eine Szene.", text)
    result = scene_word_count_in_range_metric.evaluate(instance)
    assert result["score"] == 0


# --- show_dont_tell rubric registration ---------------------------------------


def test_show_dont_tell_rubric_is_craft_tier() -> None:
    tier, body = load_rubric("show_dont_tell")
    assert tier == "craft"
    assert "Show" in body or "show" in body.lower()
