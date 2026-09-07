"""Continuation tests; fixtures and historical records never teach the actor."""
import argparse
import copy
import inspect
import json
from pathlib import Path
import time

import chess
import pytest

from recon_lite.graph import LinkType
from recon_lite_chess.coach.pools import prepare
from recon_lite_chess.coach.terminal import ChessFeaturePort
from recon_lite_chess.experiments import ordinary_m1 as experiment


@pytest.fixture(scope="module")
def fixture(tmp_path_factory):
    root = tmp_path_factory.mktemp("ordinary-reference")
    pool = root / "pool"
    prepare(pool, seed=43, train=8, validation=4, test=4)
    request = argparse.Namespace(pool=pool, output=root / "prior", seeds=[1, 2], workers=1,
        conditions=4, candidates=8, discovery=4, after_episode=8, window=4, recovery=4,
        probability=0.5, min_support=1, wall_seconds=180)
    result = experiment.prior.run(request)
    reference = {"status": "complete", "manifest": experiment.read(request.output / "manifest.json"),
        "results": [{"seed": s["seed"], "roles": {name: pair | {"shadow_history_digest": pair["shadow"]["history_digest"]}
                    for name, pair in s["pairs"].items()}} for s in result["results"]]}
    path = root / "reference.json"
    experiment.atomic_json(path, reference)
    return pool, path


def request(fixture, root, **changes):
    pool, reference = fixture
    values = dict(pool=pool, reference=reference, output=root / "public", private=root / "private",
                  seeds=[1], workers=1, episodes=24, continuation_block=4, wall_seconds=180, resume=False)
    return argparse.Namespace(**(values | changes))


def clean(result):
    result = copy.deepcopy(result)
    result.pop("manifest_digest")
    for seed in result["results"]:
        seed.pop("wall_seconds")
    return result


def pause_at_anchor(monkeypatch, args, role_index=0):
    original = experiment.save_checkpoint
    def save(directory, state, manifest):
        result = original(directory, state, manifest)
        if state["role_index"] == role_index and str(manifest["anchor"]) in state["milestones"]:
            (args.output / "STOP").touch()
        return result
    monkeypatch.setattr(experiment, "save_checkpoint", save)
    return original


def test_actual_budget_closed_final_test_terminal_boundary_and_anchors(fixture, tmp_path, monkeypatch):
    pushes, original_push, original_read = [], chess.Board.push, Path.read_bytes
    original_measure = ChessFeaturePort.measure
    def push(board, move):
        pushes.append(move)
        return original_push(board, move)
    def read(path):
        assert path.name != "test.txt"
        return original_read(path)
    def measure(port, coordinate, binding):
        assert inspect.currentframe().f_back.f_code.co_name == "_reader"
        return original_measure(port, coordinate, binding)
    monkeypatch.setattr(chess.Board, "push", push)
    monkeypatch.setattr(Path, "read_bytes", read)
    monkeypatch.setattr(ChessFeaturePort, "measure", measure)
    args = request(fixture, tmp_path, seeds=[1, 2])
    result = experiment.run(args)
    assert result["status"] == "complete"
    assert len(pushes) == result["actual_moves_lower_bound"] == result["actual_moves_upper_bound"] == 224
    for seed in result["results"]:
        for role, data in seed["roles"].items():
            assert data["anchor_matches"] and set(data["milestones"]) == {"16", "24"}
            assert sum(b["training"]["real_moves"] for b in data["blocks"]) == 24
            assert data["milestones"]["24"]["lifecycle"]["completed"] == 24
            assert data["milestones"]["16"]["shadow_history_digest"] == data["milestones"]["24"]["shadow_history_digest"]
    with pytest.raises(FileExistsError):
        experiment.run(args)


def test_clean_resume_matches_uninterrupted_and_preserves_shared_weights(fixture, tmp_path, monkeypatch):
    baseline = experiment.run(request(fixture, tmp_path / "baseline"))
    args = request(fixture, tmp_path / "resumed")
    original = pause_at_anchor(monkeypatch, args, role_index=1)
    assert experiment.run(args)["status"] == "paused"
    assert not (args.output / "summary.json").exists()
    manifest = experiment.read(args.output / "manifest.json")
    state = experiment.load_checkpoint(args.private / "seed-1", manifest, 1)
    o = state["organism"]
    assert o.completed == 16 and not o.hold_topology
    assert o.trial_decision["status"] == "no_nomination"
    for c in o.conditions.values():
        for slot in range(o.slots):
            assert o.graph.edge_by_key[(f"gate:{slot}:{c.identity}", f"option:{slot}", LinkType.SUR)].w is c.weight
    monkeypatch.setattr(experiment, "save_checkpoint", original)
    (args.output / "STOP").unlink()
    args.resume = True
    resumed = experiment.run(args)
    assert clean(resumed) == clean(baseline)
    assert not resumed["interruptions"]


def test_interrupted_training_replays_from_checkpoint_and_reports_extra_moves(fixture, tmp_path, monkeypatch):
    baseline = experiment.run(request(fixture, tmp_path / "baseline"))
    args = request(fixture, tmp_path / "resumed")
    original, original_push = experiment.train, chess.Board.push
    pushes = []
    def push(board, move):
        pushes.append(move)
        return original_push(board, move)
    def interrupted(o, fens, order, **kw):
        if kw["start_event"] == 16:
            original(o, fens, order[:2], **kw)
            raise RuntimeError("injected interruption")
        return original(o, fens, order, **kw)
    monkeypatch.setattr(chess.Board, "push", push)
    monkeypatch.setattr(experiment, "train", interrupted)
    with pytest.raises(RuntimeError, match="injected"):
        experiment.run(args)
    assert (args.output / "seed-1-none-16.json").exists()
    assert not (args.output / "summary.json").exists()
    monkeypatch.setattr(experiment, "train", original)
    args.resume = True
    resumed = experiment.run(args)
    assert resumed["results"][0]["roles"] == baseline["results"][0]["roles"]
    assert resumed["actual_moves_lower_bound"] == 112
    assert len(pushes) == 114 < resumed["actual_moves_upper_bound"] == 116
    assert resumed["interruptions"][0]["already_committed"] is False


def test_committed_evaluation_recovers_public_record_without_replaying(fixture, tmp_path, monkeypatch):
    args = request(fixture, tmp_path)
    original, original_push = experiment.publish_milestone, chess.Board.push
    pushes = []
    def push(board, move):
        pushes.append(move)
        return original_push(board, move)
    def fail(*a, **kw):
        raise RuntimeError("public write interrupted")
    monkeypatch.setattr(chess.Board, "push", push)
    monkeypatch.setattr(experiment, "publish_milestone", fail)
    with pytest.raises(RuntimeError, match="public write"):
        experiment.run(args)
    monkeypatch.setattr(experiment, "publish_milestone", original)
    args.resume = True
    result = experiment.run(args)
    assert (args.output / "seed-1-none-16.json").exists()
    assert len(pushes) == result["actual_moves_lower_bound"] == result["actual_moves_upper_bound"] == 112
    assert result["interruptions"][0]["already_committed"]


def test_expired_cap_does_not_reset_on_resume(fixture, tmp_path, monkeypatch):
    args = request(fixture, tmp_path)
    original = pause_at_anchor(monkeypatch, args)
    assert experiment.run(args)["status"] == "paused"
    monkeypatch.setattr(experiment, "save_checkpoint", original)
    (args.output / "STOP").unlink()
    path = args.private / "seed-1/budget.json"
    budget = experiment.read(path)
    budget["deadline_utc"] = time.time() - 1
    experiment.atomic_json(path, budget)
    args.resume = True
    with pytest.raises(TimeoutError, match="original seed"):
        experiment.run(args)
    assert not (args.output / "summary.json").exists()


def test_serial_parallel_match(fixture, tmp_path):
    serial = experiment.run(request(fixture, tmp_path / "serial", seeds=[1, 2]))
    parallel = experiment.run(request(fixture, tmp_path / "parallel", seeds=[1, 2], workers=2))
    assert clean(serial) == clean(parallel)


def checkpoint_fixture(fixture, directory):
    directory.mkdir()
    reference = experiment.read(fixture[1])
    o = experiment.new_actor(1, "ranked", reference["manifest"]["plans"]["1"])
    state = {"seed": 1, "role_index": 0, "next_event": 0, "organism": o}
    manifest = {"source": experiment.sources()}
    experiment.save_checkpoint(directory, state, manifest)
    return state, manifest


def test_checkpoint_source_seed_and_transport_checked_before_unpickle(fixture, tmp_path, monkeypatch):
    directory = tmp_path / "checkpoint"
    state, manifest = checkpoint_fixture(fixture, directory)
    assert experiment.load_checkpoint(directory, manifest, 1)["next_event"] == 0
    def forbidden(*a, **kw):
        raise AssertionError("unpickle reached")
    monkeypatch.setattr(experiment.pickle, "load", forbidden)
    with pytest.raises(ValueError, match="experiment"):
        experiment.load_checkpoint(directory, manifest | {"changed": True}, 1)
    with pytest.raises(ValueError, match="seed"):
        experiment.load_checkpoint(directory, manifest, 2)
    original_sources = experiment.sources
    monkeypatch.setattr(experiment, "sources", lambda: manifest["source"] | {"runner_sha256": "changed"})
    with pytest.raises(ValueError, match="source"):
        experiment.load_checkpoint(directory, manifest, 1)
    monkeypatch.setattr(experiment, "sources", original_sources)
    pointer = experiment.read(directory / "latest.json")
    with (directory / pointer["file"]).open("ab") as stream:
        stream.write(b"corrupt")
    with pytest.raises(ValueError, match="transport"):
        experiment.load_checkpoint(directory, manifest, 1)


def test_partial_checkpoint_write_preserves_previous_pointer(fixture, tmp_path, monkeypatch):
    directory = tmp_path / "checkpoint"
    state, manifest = checkpoint_fixture(fixture, directory)
    before = (directory / "latest.json").read_bytes()
    def fail(obj, stream, **kw):
        stream.write(b"partial")
        raise RuntimeError("storage interrupted")
    monkeypatch.setattr(experiment.pickle, "dump", fail)
    with pytest.raises(RuntimeError, match="storage"):
        experiment.save_checkpoint(directory, state, manifest)
    assert (directory / "latest.json").read_bytes() == before
    assert experiment.load_checkpoint(directory, manifest, 1)["next_event"] == 0


def test_pending_feedback_cannot_be_checkpointed(fixture, tmp_path):
    directory = tmp_path / "checkpoint"
    state, manifest = checkpoint_fixture(fixture, directory)
    board = chess.Board("k7/8/1K6/8/8/8/8/7R w - - 0 1")
    state["organism"].act(ChessFeaturePort(board), event_id=0, learn=True)
    with pytest.raises(RuntimeError, match="feedback"):
        experiment.save_checkpoint(directory, state, manifest)


def test_opaque_coach_and_invalid_endpoint(fixture, tmp_path):
    assert experiment.train is experiment.prior.train
    with pytest.raises(ValueError, match="exceed"):
        experiment.run(request(fixture, tmp_path, episodes=16))
    assert not (tmp_path / "public").exists()


def test_completed_seed_can_republish_after_deadline_without_new_play(tmp_path, monkeypatch):
    directory, output = tmp_path / "private/seed-1", tmp_path / "public"
    directory.mkdir(parents=True)
    output.mkdir()
    manifest = {"source": experiment.sources(), "wall_seconds_per_seed": 10,
                "plans": {"1": {}}, "anchor": 16, "episodes": 24}
    state = {"seed": 1, "role_index": 3, "next_event": 0, "organism": None,
             "results": {}, "completed_utc": time.time()-2, "last_unit": None}
    experiment.save_checkpoint(directory, state, manifest)
    experiment.atomic_json(directory / "budget.json", {"deadline_utc": time.time()-1,
                           "manifest_digest": experiment.digest(manifest)})
    def forbidden(*a, **kw):
        raise AssertionError("completed seed replayed")
    monkeypatch.setattr(experiment, "train", forbidden)
    result = experiment.run_seed((1, manifest, (), (), {}, str(directory.parent), str(output)))
    assert result["status"] == "complete" and result["wall_seconds"] < 10
    assert (output / "seed-1.json").exists()


def test_materialized_trial_checkpoint_keeps_original_evidence_and_later_credit(tmp_path):
    from test_live_trial import step
    from recon_lite_hector.learning.terminal_development import DevelopmentConfig
    from recon_lite_hector.learning.live_trial import TrialConfig
    from recon_lite_hector.learning.residual_shadow import Definition, ShadowConfig
    o = experiment.prior.RecoveryTrial(recovery_after=8,
        config=DevelopmentConfig(max_conditions=1),
        shadow_config=ShadowConfig(candidates=2, discovery_episodes=4, min_support=1),
        trial_config=TrialConfig("ranked", 8),
        definitions=(Definition("and", ((0, True), (2, True))),
                     Definition("and", ((1, True), (2, True)))))
    for event in range(7):
        step(o, event)
    # Plant only the nomination in this mechanism fixture, never in chess runs.
    o.shadow.nomination = {"ranked": 0, "random": 1}
    step(o, 7)
    manifest = {"source": experiment.sources()}
    state = {"seed": 1, "role_index": 1, "next_event": 8, "organism": o}
    experiment.save_checkpoint(tmp_path, state, manifest)
    restored = experiment.load_checkpoint(tmp_path, manifest, 1)["organism"]
    c = restored.trial_condition
    assert c is not None and c.source_evidence is restored.shadow.evidence[c.source_index]
    for slot in range(restored.slots):
        assert restored.graph.edge_by_key[(f"gate:{slot}:{c.identity}", f"option:{slot}", LinkType.SUR)].w is c.weight
    for event in range(8, 20):
        assert step(o, event) == step(restored, event)
        assert experiment.actor_digest(o) == experiment.actor_digest(restored)
