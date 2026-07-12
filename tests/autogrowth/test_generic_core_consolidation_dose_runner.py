from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import runpy

import pytest


RUNNER = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "autogrowth"
    / "run_generic_core_consolidation_dose.py"
)
ARMS = ("scale_0_10", "scale_0_25", "scale_0_50", "scale_1_00")


def _budget() -> dict[str, object]:
    return {
        "training_episode_count": 8192,
        "evaluation_episode_count": 1024,
        "selection_count": {"left": 4079, "right": 4113},
        "rng_call_count": 24576,
    }


def _row() -> dict[str, object]:
    return {"arms": {arm: _budget() for arm in ARMS}}


@pytest.fixture(scope="module")
def identical_budget():
    return runpy.run_path(str(RUNNER))["_arms_have_identical_budget"]


def test_identical_budget_accepts_equal_dictionary_values(
    identical_budget,
) -> None:
    assert identical_budget(_row(), ARMS)


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("training_episode_count", 8191),
        ("evaluation_episode_count", 1023),
        ("selection_count", {"left": 4080, "right": 4112}),
        ("rng_call_count", 24575),
    ),
)
def test_identical_budget_rejects_each_unequal_field(
    identical_budget,
    field: str,
    replacement: object,
) -> None:
    changed = deepcopy(_row())
    changed["arms"]["scale_0_50"][field] = replacement
    assert not identical_budget(changed, ARMS)


def test_identical_budget_rejects_empty_arm_list(identical_budget) -> None:
    assert not identical_budget(_row(), ())
