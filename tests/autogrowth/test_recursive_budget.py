"""Intervention identity, schedule, retention and independent process limits."""
from collections import Counter
from pathlib import Path
import pickle
import sys
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/autogrowth"))
import run_recursive_budget as budget
from guard_recursive_budget import guard


def test_only_split_budget_changes_including_after_saved_graph_restore(tmp_path):
    actor = budget.lab.RecursiveDevelopment(seed=2)
    actor, _, _ = budget.lab.train_block(actor, list(range(16)), tmp_path / "block", "start")
    for cap in budget.CAPS:
        child = budget.fork(actor, cap)
        assert budget.lab.evaluate(child) == budget.lab.evaluate(actor)
        child.bias.fast += .1
        with pytest.raises(AssertionError, match="fork changed"):
            budget.verify_fork(actor, child, cap)


def test_fixed_continuation_has_two_shifts_and_new_seeded_order():
    for seed in (4, 5, 6, 7, 8, 9):
        rows = budget.schedule(seed)
        assert len(rows) == 768 and rows != budget.lab.schedule(seed)[1]
        for block in range(6):
            counts = Counter(rows[block * 128:(block + 1) * 128])
            assert len(counts) == 16
            for row, count in counts.items():
                assert count == (14 if bool(budget.lab.ROWS[row][2]) == (block < 3) else 2)


def test_restored_fork_compares_set_values_but_rejects_changed_graph_metadata(tmp_path):
    from recon_lite_hector.learning.recursive_context import Expression
    actor = budget.lab.RecursiveDevelopment()
    expressions = [Expression("read", atom=(i, True)) for i in range(50)]
    actor.seen = set(expressions)
    child = budget.fork(actor, 12)
    child.seen = set(reversed(expressions))
    budget.lab.save_actor(actor, tmp_path / "parent.pkl.gz")
    budget.lab.save_actor(child, tmp_path / "child.pkl.gz")
    parent = budget.lab.load_actor(tmp_path / "parent.pkl.gz")
    child = budget.lab.load_actor(tmp_path / "child.pkl.gz")
    budget.verify_fork(parent, child, 12)
    child.graph.nodes["catalog"].meta["changed"] = True
    with pytest.raises(AssertionError, match="fork changed actor state: graph"):
        budget.verify_fork(parent, child, 12)


def test_retention_counts_changed_row_identities_even_when_scores_tie():
    def evaluation(episode, correct):
        return {"episode": episode, "correct": len(correct), "context_correct": [1, 1],
                "rows": [{"row": i, "reward": 1 if i in correct else -1} for i in range(16)]}
    series = [evaluation(0, {0, 1}), evaluation(1, {1, 2}), evaluation(2, {1, 2}),
              evaluation(3, {1, 2}), evaluation(4, {0, 1})]
    result = budget.transitions(series)
    assert result["milestones"][0]["lost_from_previous"] == [0]
    assert result["initial_successes_never_lost_at_measurements"] == 1
    assert result["new_b_at_middle"] == [2]
    assert result["new_b_retained_at_end"] == []


def test_independent_guard_stops_a_non_cooperating_child_and_preserves_exit_code():
    started = time.monotonic()
    assert guard([sys.executable, "-c", "import time; time.sleep(30)"], 1) == 124
    assert time.monotonic() - started < 8
    assert guard([sys.executable, "-c", "raise SystemExit(7)"], 5) == 7
