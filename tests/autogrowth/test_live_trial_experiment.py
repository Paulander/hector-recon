import argparse
from dataclasses import asdict
import json
from pathlib import Path

import chess
import pytest

from recon_lite_chess.coach.pools import prepare
from recon_lite_chess.experiments import live_trial as experiment


@pytest.fixture
def pool(tmp_path):
    directory = tmp_path / "pool"
    prepare(directory, seed=43, train=8, validation=4, test=4)
    return directory


def args(pool, output, workers=1):
    return argparse.Namespace(pool=pool, output=output, seeds=[1, 2], workers=workers,
                              conditions=4, candidates=8, discovery=4, after_episode=8,
                              suffix=4, min_support=1, wall_seconds=90)


def test_actual_move_budget_closed_test_and_readonly_ablation(pool, tmp_path, monkeypatch):
    original_read = Path.read_bytes
    def read(path):
        assert path.name != "test.txt"
        return original_read(path)
    monkeypatch.setattr(Path, "read_bytes", read)
    pushes, original_push = [], chess.Board.push
    def push(board, move):
        pushes.append(move.uci())
        return original_push(board, move)
    monkeypatch.setattr(chess.Board, "push", push)
    result = experiment.run(args(pool, tmp_path / "run"))
    assert len(pushes) == 2 * (3 * 12 + 5 * 4)
    assert result["status"] == "complete"
    for seed in result["results"]:
        assert seed["prefix_behavior_and_history_identical"]
        for role, arm in seed["arms"].items():
            assert arm["live_counts"]["episodes"] == 4
            assert arm["evaluation"]["learned_state_unchanged"]
            if role != "none":
                assert arm["ablation"]["evaluation"]["learned_state_unchanged"]
    manifest = json.loads((tmp_path / "run" / "manifest.json").read_text())
    assert not manifest["final_test_opened"] and manifest["validation_is_development"]
    assert manifest["training_moves"] + manifest["validation_moves_including_ablations"] == len(pushes)
    # Public output contains no learned weight fields or raw board/move rows.
    public = json.dumps(result)
    assert '"weight"' not in public and '"after_fen"' not in public and '"action"' not in public
    with pytest.raises(FileExistsError):
        experiment.run(args(pool, tmp_path / "run"))


def test_serial_parallel_parity(pool, tmp_path):
    a = experiment.run(args(pool, tmp_path / "serial"))
    b = experiment.run(args(pool, tmp_path / "parallel", 2))
    for result in (a, b):
        result.pop("manifest_digest")
        for seed in result["results"]:
            for arm in seed["arms"].values():
                arm.pop("seconds")
    assert a == b


def test_coach_remains_opaque_and_event_ids_continue(monkeypatch):
    class Opaque:
        @property
        def graph(self):
            raise AssertionError("coach inspected graph")

        @property
        def trial_decision(self):
            raise AssertionError("coach inspected trial")

        def act(self, port, *, event_id, learn):
            assert event_id in (8, 9) and learn
            return "h1h8"

        def observe(self, feedback):
            assert set(asdict(feedback)) == {"event_id", "action", "reward"}
    def forbidden(*args):
        raise AssertionError("training called offline inspection")
    monkeypatch.setattr(experiment, "learned_digest", forbidden)
    result = experiment.train(Opaque(), ("k7/8/1K6/8/8/8/8/7R w - - 0 1",), (0, 0),
                              start_event=8, deadline=float("inf"))
    assert result["mates"] == result["real_moves"] == 2


def test_failure_keeps_protocol_without_partial_summary(pool, tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise TimeoutError("budget")
    monkeypatch.setattr(experiment, "train", fail)
    with pytest.raises(TimeoutError):
        experiment.run(args(pool, tmp_path / "run"))
    assert (tmp_path / "run" / "manifest.json").exists()
    assert (tmp_path / "run" / "failure.json").exists()
    assert not (tmp_path / "run" / "summary.json").exists()


def test_overlap_and_invalid_budgets_rejected_before_play(pool, tmp_path, monkeypatch):
    request = args(pool, tmp_path / "bad")
    request.seeds = [1, 1]
    with pytest.raises(ValueError, match="unique seeds"):
        experiment.run(request)
    request.seeds = [1]
    request.after_episode = 4
    with pytest.raises(ValueError, match="prospective interval"):
        experiment.run(request)
    request.after_episode = 8
    monkeypatch.setattr(experiment, "load_split", lambda *a: (("k7/8/1K6/8/8/8/8/7R w - - 0 1",), "same"))
    with pytest.raises(ValueError, match="orbits overlap"):
        experiment.run(request)
    assert not request.output.exists()
