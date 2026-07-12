from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import runpy

import pytest


RUNNER = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "autogrowth"
    / "run_generic_core_adaptive_consolidation.py"
)
ARMS = ("fixed_full", "fixed_low", "adaptive")


def _arm(left: int, right: int) -> dict[str, object]:
    return {
        "training_episode_count": 8192,
        "evaluation_episode_count": 1024,
        "selection_count": {"left": left, "right": right},
        "rng_call_count": 49152,
    }


def _row() -> dict[str, object]:
    return {
        "arms": {
            "fixed_full": _arm(8000, 8384),
            "fixed_low": _arm(8100, 8284),
            "adaptive": _arm(8200, 8184),
        }
    }


@pytest.fixture(scope="module")
def identical_total_budget():
    return runpy.run_path(str(RUNNER))[
        "_arms_have_identical_total_budget"
    ]


def test_total_budget_allows_different_action_distributions(
    identical_total_budget,
) -> None:
    assert identical_total_budget(_row(), ARMS)


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("training_episode_count", 8191),
        ("evaluation_episode_count", 1023),
        ("selection_count", {"left": 8201, "right": 8184}),
        ("rng_call_count", 49151),
    ),
)
def test_total_budget_rejects_each_unequal_total(
    identical_total_budget,
    field: str,
    replacement: object,
) -> None:
    changed = deepcopy(_row())
    changed["arms"]["adaptive"][field] = replacement
    assert not identical_total_budget(changed, ARMS)


def test_total_budget_rejects_empty_arm_list(
    identical_total_budget,
) -> None:
    assert not identical_total_budget(_row(), ())
