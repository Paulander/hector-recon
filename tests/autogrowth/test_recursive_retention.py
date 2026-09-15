"""Checks for trajectory preservation and fail-closed experimental evidence."""
from collections import Counter
import json
from pathlib import Path
import pickle
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/autogrowth"
sys.path.insert(0, str(SCRIPTS))
import run_recursive_retention as lab


def state(actor):
    return {"conditions": actor.conditions, "bias": actor.bias,
            "history": actor.history, "splits": actor.splits, "evidence": actor.evidence,
            "completed": actor.completed, "expressions": actor.expressions,
            "rngs": [getattr(actor, name).getstate() for name in ("rng", "proposal_rng", "exploration_rng")],
            "edges": [(e.src, e.dst, e.ltype, float(e.w)) for e in actor.graph.edges]}


def test_declared_schedule_contains_both_directions_and_no_reward_rule_switch():
    for seed in lab.SEEDS:
        prefix, continuation = lab.schedule(seed)
        assert len(prefix) == 256 and len(continuation) == 768
        assert set(Counter(prefix).values()) == {32}
        assert all(not lab.ROWS[row][2] for row in prefix)
        for block in range(6):
            counts = Counter(continuation[block * 128:(block + 1) * 128])
            assert len(counts) == 16
            for row, count in counts.items():
                dominant = lab.ROWS[row][2] if block < 3 else not lab.ROWS[row][2]
                assert count == (14 if dominant else 2)


def test_recording_restore_and_disposable_evaluation_preserve_learning(tmp_path):
    config = lab.RecursiveConfig(prefix=8, grow_every=8, min_support=1)
    actor = lab.RecursiveDevelopment(seed=2, recursive_config=config,
                                    config=lab.DevelopmentConfig(max_conditions=16))
    control = pickle.loads(pickle.dumps(actor))
    order = list(range(16)) * 2
    restored, previous, result = lab.train_block(actor, order, tmp_path / "block", "start")
    for row in order:
        env = lab.BooleanEnvironment(lab.ROWS[row])
        event = control.completed
        action = control.act(env, event_id=event, learn=True)
        control.observe(lab.Feedback(event, action, env.outcome()))
    assert state(restored) == state(control)
    before = pickle.dumps(restored, protocol=5)
    assert lab.evaluate(restored) == result
    assert pickle.dumps(restored, protocol=5) == before
    assert previous == lab.digest((tmp_path / "block/checkpoint.pkl.gz").read_bytes())
    assert lab.verify_block(tmp_path / "block", order, 0, "start")["training_records"] == 32


def test_existing_journals_cannot_be_overwritten_and_missing_record_is_rejected(tmp_path):
    actor = lab.RecursiveDevelopment(seed=1)
    lab.train_block(actor, [0, 1, 2, 3], tmp_path / "block", "start", do_evaluate=False)
    path = tmp_path / "block/training.jsonl"
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        lab.write_once(path, b"replacement")
    assert path.read_bytes() == original
    path.write_bytes(b"".join(original.splitlines(keepends=True)[:-1]))
    with pytest.raises(AssertionError, match="hash mismatch"):
        lab.verify_block(tmp_path / "block", [0, 1, 2, 3], 0, "start")


def test_interrupted_block_retains_partial_records_without_claiming_completion(tmp_path, monkeypatch):
    actor = lab.RecursiveDevelopment(seed=1)
    outcome = lab.BooleanEnvironment.outcome
    calls = []
    def fail(environment):
        calls.append(1)
        if len(calls) == 4:
            raise InterruptedError("injected interruption")
        return outcome(environment)
    monkeypatch.setattr(lab.BooleanEnvironment, "outcome", fail)
    with pytest.raises(InterruptedError):
        lab.train_block(actor, list(range(8)), tmp_path / "block", "start")
    assert (tmp_path / "block/intent.json").exists()
    records = (tmp_path / "block/progress.jsonl").read_text().splitlines()
    assert [json.loads(line)["event"] for line in records] == [0, 1, 2]
    assert not (tmp_path / "block/complete.json").exists()
    assert not (tmp_path / "block/training.jsonl").exists()


def test_wrong_schedule_or_checkpoint_ancestry_is_rejected(tmp_path):
    actor = lab.RecursiveDevelopment(seed=1)
    lab.train_block(actor, [0, 1], tmp_path / "block", "start", do_evaluate=False)
    with pytest.raises(AssertionError):
        lab.verify_block(tmp_path / "block", [1, 0], 0, "start")
    with pytest.raises(AssertionError):
        lab.verify_block(tmp_path / "block", [0, 1], 0, "unrelated")


def test_paired_fork_rejects_an_unmatched_weight():
    parent = lab.RecursiveDevelopment()
    child = pickle.loads(pickle.dumps(parent))
    child.config = lab.replace(child.config, max_conditions=24)
    child.recursive_config = lab.replace(child.recursive_config, role="random")
    lab.verify_fork(parent, child, "random")
    child.bias.fast += .1
    with pytest.raises(AssertionError, match="bias"):
        lab.verify_fork(parent, child, "random")


def test_empty_start_restores_before_action_options_exist(tmp_path):
    actor = lab.RecursiveDevelopment()
    lab.save_actor(actor, tmp_path / "start.pkl.gz")
    restored = lab.load_actor(tmp_path / "start.pkl.gz")
    assert restored.schema is None and restored.completed == 0


def test_completed_evidence_is_independent_of_a_stale_progress_prefix(tmp_path):
    actor = lab.RecursiveDevelopment()
    lab.train_block(actor, [0, 1, 2], tmp_path / "block", "start", do_evaluate=False)
    progress = tmp_path / "block/progress.jsonl"
    progress.write_bytes(progress.read_bytes().splitlines(keepends=True)[0])
    assert lab.verify_block(tmp_path / "block", [0, 1, 2], 0, "start")["training_records"] == 3
    progress.write_bytes(b"unrelated content\n")
    with pytest.raises(AssertionError, match="contradictory progress"):
        lab.verify_block(tmp_path / "block", [0, 1, 2], 0, "start")
