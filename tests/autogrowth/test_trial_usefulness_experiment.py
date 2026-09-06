import argparse
from dataclasses import asdict
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


def args(pool, output, workers=1):
    return argparse.Namespace(pool=pool, output=output, seeds=[1, 2], workers=workers,
        conditions=4, candidates=8, discovery=4, after_episode=8, suffix=4,
        window=4, probability=0.5, min_support=1, wall_seconds=120)


def test_exact_actual_budget_and_closed_final_test(pool, tmp_path, monkeypatch):
    original_read = Path.read_bytes
    def read(p):
        assert p.name != "test.txt"
        return original_read(p)
    monkeypatch.setattr(Path, "read_bytes", read)
    pushes, original = [], chess.Board.push
    def push(board, move):
        pushes.append(move.uci())
        return original(board, move)
    monkeypatch.setattr(chess.Board, "push", push)
    r = experiment.run(args(pool, tmp_path / "run"))
    assert r["status"] == "complete" and len(pushes) == 2 * (5 * 12 + 9 * 4)
    for seed in r["results"]:
        assert seed["prefix_behavior_and_history_identical"]
        for name, arm in seed["arms"].items():
            assert arm["evaluation"]["learned_state_unchanged"]
            if name.startswith("probe_"):
                assert arm["usefulness"]["groups"]["disabled"]["participations"] == 0
                assert arm["usefulness"]["assigned_episodes"] == (4 if arm["decision"]["status"] == "attached" else 0)
    with pytest.raises(FileExistsError):
        experiment.run(args(pool, tmp_path / "run"))


def test_serial_parallel_match_and_old_controls_are_unchanged(pool, tmp_path):
    a = experiment.run(args(pool, tmp_path / "serial"))
    b = experiment.run(args(pool, tmp_path / "parallel", 2))
    old = experiment.prior.run(args(pool, tmp_path / "old"))
    for r in (a, b, old):
        r.pop("manifest_digest")
        for seed in r["results"]:
            for arm in seed["arms"].values():
                arm.pop("seconds")
    assert a == b
    for new, previous in zip(a["results"], old["results"]):
        for role in ("none", "ranked", "random"):
            assert new["arms"][role] == previous["arms"][role]


def test_failure_keeps_protocol_and_no_partial_summary(pool, tmp_path, monkeypatch):
    def fail(*a, **kw):
        raise TimeoutError("budget")
    monkeypatch.setattr(experiment, "train", fail)
    with pytest.raises(TimeoutError):
        experiment.run(args(pool, tmp_path / "run"))
    assert (tmp_path / "run" / "manifest.json").exists()
    assert (tmp_path / "run" / "failure.json").exists()
    assert not (tmp_path / "run" / "summary.json").exists()


def test_opaque_coach_uses_no_probe_information(monkeypatch):
    class Opaque:
        @property
        def use_outcomes(self):
            raise AssertionError("coach inspected use history")
        @property
        def graph(self):
            raise AssertionError("coach inspected graph")
        def act(self, port, *, event_id, learn):
            return "h1h8"
        def observe(self, feedback):
            assert set(asdict(feedback)) == {"event_id", "action", "reward"}
    result = experiment.train(Opaque(), ("k7/8/1K6/8/8/8/8/7R w - - 0 1",), (0, 0),
                              start_event=8, deadline=float("inf"))
    assert result["mates"] == result["real_moves"] == 2


def test_invalid_probability_and_overlap_rejected(pool, tmp_path, monkeypatch):
    request = args(pool, tmp_path / "bad")
    request.probability = 1
    with pytest.raises(ValueError):
        experiment.run(request)
    request.probability = 0.5
    monkeypatch.setattr(experiment, "load_split", lambda *a: (("k7/8/1K6/8/8/8/8/7R w - - 0 1",), "same"))
    with pytest.raises(ValueError, match="orbits overlap"):
        experiment.run(request)
    assert not request.output.exists()
