"""Recovery is extra ordinary experience, with no new learner policy."""
import argparse
import json
from pathlib import Path

import chess
import pytest

from recon_lite_chess.coach.pools import prepare
from recon_lite_chess.experiments import trial_usefulness as experiment


@pytest.fixture
def pool(tmp_path):
    p = tmp_path / "pool"
    prepare(p, seed=43, train=8, validation=4, test=4)
    return p


def request(pool, output, **changes):
    values = dict(pool=pool, output=output, seeds=[1, 2], workers=1,
                  conditions=4, candidates=8, discovery=4, after_episode=8,
                  suffix=4, window=4, recovery=4, probability=0.5,
                  min_support=1, wall_seconds=120)
    return argparse.Namespace(**(values | changes))


def test_recovery_exact_moves_closed_test_and_frozen_probe(pool, tmp_path, monkeypatch):
    original_read, original_push = Path.read_bytes, chess.Board.push
    pushes = []
    def read(p):
        assert p.name != "test.txt"
        return original_read(p)
    def push(board, move):
        pushes.append(move.uci())
        return original_push(board, move)
    monkeypatch.setattr(Path, "read_bytes", read)
    monkeypatch.setattr(chess.Board, "push", push)
    r = experiment.run(request(pool, tmp_path / "run"))
    assert len(pushes) == 2 * (5 * 16 + 9 * 4)
    manifest = json.loads((tmp_path / "run/manifest.json").read_text())
    assert manifest["phase_episodes"] == dict(prefix=8, probe_or_matched_control=4,
                                             normal_access_recovery=4)
    for seed in r["results"]:
        for name, arm in seed["arms"].items():
            assert arm["suffix_training"]["real_moves"] == 4
            assert arm["recovery_training"]["real_moves"] == 4
            assert arm["before_recovery"]["lifecycle"]["completed"] == 12
            assert arm["after_recovery"]["completed"] == 16
            assert arm["probe_history_unchanged"]
            assert arm["before_recovery"]["learned_digest"] != arm["learned_digest"]
            if name.startswith("probe_"):
                assert arm["before_recovery"]["use_history_digest"] == arm["usefulness"]["history_digest"]
                assert arm["usefulness"]["groups"]["disabled"]["participations"] == 0


def test_phase_split_preserves_uninterrupted_learning_and_prefix(pool, tmp_path):
    recovery = experiment.run(request(pool, tmp_path / "recovery"))
    uninterrupted = experiment.run(request(pool, tmp_path / "uninterrupted", suffix=8, recovery=0))
    short = experiment.run(request(pool, tmp_path / "short", recovery=0))
    for new, continuous, previous in zip(recovery["results"], uninterrupted["results"], short["results"]):
        for name, arm in new["arms"].items():
            before, end = previous["arms"][name], continuous["arms"][name]
            for key in ("prefix_training", "suffix_training"):
                assert arm[key] == before[key]
            assert arm["before_recovery"]["learned_digest"] == before["learned_digest"]
            for key in ("learned_digest", "evaluation", "structure", "live_counts",
                        "decision", "shadow", "trial_state", "ablation", "usefulness"):
                assert arm.get(key) == end.get(key)


def test_recovery_serial_parallel_match(pool, tmp_path):
    serial = experiment.run(request(pool, tmp_path / "serial"))
    parallel = experiment.run(request(pool, tmp_path / "parallel", workers=2))
    for r in (serial, parallel):
        r.pop("manifest_digest")
        for seed in r["results"]:
            for arm in seed["arms"].values():
                arm.pop("seconds")
    assert serial == parallel


def test_recovery_does_not_accept_incomplete_probe_or_negative_budget(pool, tmp_path):
    for changes in ({"suffix": 3}, {"suffix": 5}, {"recovery": -1}):
        with pytest.raises(ValueError, match="recovery"):
            experiment.run(request(pool, tmp_path / "bad", **changes))
    assert not (tmp_path / "bad").exists()


def test_recovery_failure_is_incomplete(pool, tmp_path, monkeypatch):
    original = experiment.train
    def train(*args, **kwargs):
        if kwargs["start_event"] == 12:
            raise TimeoutError("recovery budget")
        return original(*args, **kwargs)
    monkeypatch.setattr(experiment, "train", train)
    with pytest.raises(TimeoutError, match="recovery budget"):
        experiment.run(request(pool, tmp_path / "run"))
    assert (tmp_path / "run/manifest.json").exists()
    assert (tmp_path / "run/failure.json").exists()
    assert not (tmp_path / "run/summary.json").exists()


def test_later_failure_preserves_finished_arm_evidence(pool, tmp_path, monkeypatch):
    original, prefixes = experiment.train, []
    def train(*args, **kwargs):
        if kwargs["start_event"] == 0:
            prefixes.append(True)
            if len(prefixes) == 2:
                raise TimeoutError("next arm interrupted")
        return original(*args, **kwargs)
    monkeypatch.setattr(experiment, "train", train)
    with pytest.raises(TimeoutError, match="next arm interrupted"):
        experiment.run(request(pool, tmp_path / "run"))
    saved = json.loads((tmp_path / "run/seed-1-none.json").read_text())
    assert saved["arm"] == "none" and saved["seed"] == 1
    assert saved["result"]["after_recovery"]["completed"] == 16
    assert saved["result"]["evaluation"]["count"] == 4
    assert (tmp_path / "run/failure.json").exists()
    assert not (tmp_path / "run/summary.json").exists()
