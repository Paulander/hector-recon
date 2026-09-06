import argparse
from dataclasses import asdict
import json
from pathlib import Path

import chess
import pytest

from recon_lite_chess.coach.pools import prepare
from recon_lite_chess.experiments import residual_shadow as experiment


@pytest.fixture
def pool(tmp_path):
    directory = tmp_path / "pool"
    prepare(directory, seed=43, train=8, validation=4, test=4)
    return directory


def args(pool, output, workers=1):
    return argparse.Namespace(pool=pool, output=output, seeds=[1, 2], workers=workers,
                              conditions=4, candidates=8, discovery=4, prospective=4,
                              min_support=1, wall_seconds=90)


def test_only_actual_actions_and_no_evaluation_pool_reads(pool, tmp_path, monkeypatch):
    original_read = Path.read_bytes
    def read(path):
        assert path.name not in ("test.txt", "validation.txt")
        return original_read(path)
    monkeypatch.setattr(Path, "read_bytes", read)
    pushes, original_push = [], chess.Board.push
    def push(board, move):
        pushes.append(move.uci())
        return original_push(board, move)
    monkeypatch.setattr(chess.Board, "push", push)
    result = experiment.run(args(pool, tmp_path / "run"))
    assert len(pushes) == 2 * 2 * 8
    assert result["status"] == "complete"
    for seed in result["results"]:
        assert seed["behavior_and_actor_unchanged"]
        assert seed["arms"]["control"]["training"] == seed["arms"]["shadow"]["training"]
        assert seed["arms"]["control"]["actor_digest"] == seed["arms"]["shadow"]["actor_digest"]
    manifest = json.loads((tmp_path / "run" / "manifest.json").read_text())
    assert not manifest["validation_opened"] and not manifest["final_test_opened"]
    with pytest.raises(FileExistsError):
        experiment.run(args(pool, tmp_path / "run"))


def test_serial_and_parallel_have_identical_results(pool, tmp_path):
    a = experiment.run(args(pool, tmp_path / "serial"))
    b = experiment.run(args(pool, tmp_path / "parallel", 2))
    for result in (a, b):
        result.pop("manifest_digest")  # Protocol records worker count.
        for seed in result["results"]:
            for arm in seed["arms"].values():
                arm.pop("seconds")
    assert a == b


def test_coach_does_not_read_graph_or_nomination(monkeypatch):
    class Opaque:
        @property
        def graph(self):
            raise AssertionError("coach inspected graph")

        @property
        def shadow(self):
            raise AssertionError("coach inspected shadow")

        def act(self, port, *, event_id, learn):
            return "h1h8"

        def observe(self, feedback):
            assert set(asdict(feedback)) == {"event_id", "action", "reward"}
    def forbidden(*args):
        raise AssertionError("offline report called during training")
    monkeypatch.setattr(experiment, "actor_digest", forbidden)
    monkeypatch.setattr(experiment, "public_shadow_report", forbidden)
    result = experiment.train(Opaque(), ("k7/8/1K6/8/8/8/8/7R w - - 0 1",), (0, 0), deadline=float("inf"))
    assert result["mates"] == result["real_moves"] == 2


def test_failure_preserves_protocol_without_partial_summary(pool, tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise TimeoutError("budget")
    monkeypatch.setattr(experiment, "train", fail)
    with pytest.raises(TimeoutError):
        experiment.run(args(pool, tmp_path / "run"))
    assert (tmp_path / "run" / "manifest.json").exists()
    assert (tmp_path / "run" / "failure.json").exists()
    assert not (tmp_path / "run" / "summary.json").exists()


def test_invalid_budgets_rejected_before_play(pool, tmp_path, monkeypatch):
    request = args(pool, tmp_path / "bad")
    request.seeds = [1, 1]
    with pytest.raises(ValueError, match="unique seeds"):
        experiment.run(request)
    request.seeds = [1]
    request.discovery = 1
    with pytest.raises(ValueError, match="active and inactive"):
        experiment.run(request)
    request.discovery = 4
    monkeypatch.setattr(experiment, "load_split", lambda *a: ((), "empty"))
    with pytest.raises(ValueError, match="nonempty"):
        experiment.run(request)
    assert not request.output.exists()
