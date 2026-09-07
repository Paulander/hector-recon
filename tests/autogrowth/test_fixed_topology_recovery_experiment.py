"""Matched lab controls retain an opaque coach and count only actual moves."""
import argparse
import json
from pathlib import Path

import chess
import pytest

from recon_lite_chess.coach.pools import prepare
from recon_lite_chess.experiments import fixed_topology_recovery as experiment


@pytest.fixture
def pool(tmp_path):
    p = tmp_path / "pool"
    prepare(p, seed=43, train=8, validation=4, test=4)
    return p


def request(pool, output, **changes):
    values = dict(pool=pool, output=output, seeds=[1, 2], workers=1,
                  conditions=4, candidates=8, discovery=4, after_episode=8,
                  window=4, recovery=4, probability=0.5, min_support=1, wall_seconds=120)
    return argparse.Namespace(**(values | changes))


def test_exact_moves_closed_final_test_and_fixed_history(pool, tmp_path, monkeypatch):
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
    manifest = json.loads((tmp_path / "run/manifest.json").read_text())
    assert len(pushes) == 344 == manifest["training_moves"] + manifest["validation_moves_including_ablations"]
    assert manifest["experience_per_final_actor"] == 16
    for seed in r["results"]:
        for pair in seed["pairs"].values():
            assert pair["exploration_streams_match"]
            assert pair["before_recovery"]["lifecycle"]["completed"] == 12
            assert pair["arms"]["fixed"]["representation_unchanged"]
            for arm in pair["arms"].values():
                assert arm["after_recovery"]["completed"] == 16
                assert arm["recovery_training"]["real_moves"] == 4
                assert arm["probe_history_unchanged"] and arm["evaluation"]["learned_state_unchanged"]
                if "usefulness" in arm:
                    assert arm["usefulness"]["history_digest"] == pair["before_recovery"]["use_history_digest"]
    with pytest.raises(FileExistsError):
        experiment.run(request(pool, tmp_path / "run"))


def test_previous_prefix_and_serial_parallel_match(pool, tmp_path):
    serial = experiment.run(request(pool, tmp_path / "serial"))
    parallel = experiment.run(request(pool, tmp_path / "parallel", workers=2))
    old = experiment.prior.run(request(pool, tmp_path / "old", suffix=4, recovery=0))
    for r in (serial, parallel):
        r.pop("manifest_digest")
        for seed in r["results"]:
            seed.pop("seconds")
            for pair in seed["pairs"].values():
                for arm in pair["arms"].values():
                    arm.pop("seconds")
    assert serial == parallel
    for new, previous in zip(serial["results"], old["results"]):
        for name, pair in new["pairs"].items():
            reference = previous["arms"][name]
            for key in ("prefix_training", "suffix_training", "decision", "shadow"):
                assert pair[key] == reference[key]
            assert pair["before_recovery"]["learned_digest"] == reference["learned_digest"]
            if name.startswith("probe_"):
                assert pair["before_recovery"]["use_history_digest"] == reference["usefulness"]["history_digest"]


def test_later_failure_preserves_finished_mode(pool, tmp_path, monkeypatch):
    original, calls = experiment.train, []
    def train(o, *args, **kwargs):
        calls.append(o.hold_topology)
        if o.hold_topology:
            raise TimeoutError("fixed mode interrupted")
        return original(o, *args, **kwargs)
    monkeypatch.setattr(experiment, "train", train)
    with pytest.raises(TimeoutError, match="fixed mode"):
        experiment.run(request(pool, tmp_path / "run"))
    saved = json.loads((tmp_path / "run/seed-1-none-normal.json").read_text())
    assert saved["result"]["evaluation"]["count"] == 4
    assert saved["shared_history"]["before_recovery"]["lifecycle"]["completed"] == 12
    assert (tmp_path / "run/failure.json").exists()
    assert not (tmp_path / "run/summary.json").exists()


def test_opaque_coach_has_no_recovery_or_graph_information():
    assert experiment.train is experiment.prior.train
    class Opaque:
        @property
        def hold_topology(self):
            raise AssertionError("coach inspected control")
        @property
        def graph(self):
            raise AssertionError("coach inspected graph")
        def act(self, port, *, event_id, learn):
            return "h1h8"
        def observe(self, feedback):
            assert set(vars(feedback)) == {"event_id", "action", "reward"}
    r = experiment.train(Opaque(), ("k7/8/1K6/8/8/8/8/7R w - - 0 1",), (0,),
                         start_event=12, deadline=float("inf"))
    assert r["mates"] == r["real_moves"] == 1


def test_invalid_budget_and_orbit_overlap_rejected(pool, tmp_path, monkeypatch):
    for changes in ({"recovery": 0}, {"seeds": [1, 1]}, {"wall_seconds": 0}):
        with pytest.raises(ValueError, match="budgets"):
            experiment.run(request(pool, tmp_path / "bad", **changes))
    monkeypatch.setattr(experiment, "load_split", lambda *a: (("k7/8/1K6/8/8/8/8/7R w - - 0 1",), "same"))
    with pytest.raises(ValueError, match="orbits overlap"):
        experiment.run(request(pool, tmp_path / "bad"))
    assert not (tmp_path / "bad").exists()
