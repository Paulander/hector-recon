"""Boundary and behavior tests. Test-side answers never enter learner training."""

import argparse
from dataclasses import FrozenInstanceError
import json
import math

import chess
import pytest

from recon_lite import NodeType
from recon_lite_chess.coach.exercise import play_mate_one
from recon_lite_chess.coach.interface import BoardSensor, Feedback, PositionReading
from recon_lite_chess.coach.native import NativeConfig, NativeOrganism
from recon_lite_chess.coach.pools import load_split, orbit_key, prepare
from recon_lite_chess.coach.runner import (
    RunState, evaluate, load_checkpoint, save_checkpoint, source_identity, train,
)


M1 = "k7/8/1K6/8/8/8/8/7R w - - 0 1"


class OpaquePlayer:
    def __init__(self, action):
        self.action = action
        self.feedback = []
        self.sensor = None

    @property
    def graph(self):
        raise AssertionError("the coach must not inspect the learner")

    def act(self, sensor, *, event_id, learn):
        self.sensor = sensor
        return self.action

    def observe(self, feedback):
        self.feedback.append(feedback)


@pytest.mark.parametrize("move,reason,reward,real_moves", [
    ("h1h8", "checkmate", 1, 1),
    ("h1h2", "exercise_timeout", -1, 1),
    ("h1a2", "illegal_action", -1, 0),
    (None, "no_action", -1, 0),
])
def test_coach_grades_only_the_actual_action(monkeypatch, move, reason, reward, real_moves):
    pushes = []
    original = chess.Board.push

    def counted(board, action):
        pushes.append(action.uci())
        return original(board, action)

    monkeypatch.setattr(chess.Board, "push", counted)
    organism = OpaquePlayer(move)
    attempt = play_mate_one(organism, M1, event_id=9, learn=True)
    assert (attempt.reason, attempt.reward, attempt.real_moves) == (reason, reward, real_moves)
    assert pushes == ([move] if real_moves else [])
    assert organism.feedback == [Feedback(9, move, reward, reason)]
    if reason == "exercise_timeout":
        assert not chess.Board(attempt.after_fen).is_game_over()
    assert not hasattr(organism.sensor, "board")
    with pytest.raises(FrozenInstanceError):
        organism.sensor.reading.white_to_move = False


def test_evaluation_never_sends_feedback():
    organism = OpaquePlayer("h1h8")
    assert play_mate_one(organism, M1, event_id=0, learn=False).reward == 1
    assert not organism.feedback


def test_stalemate_is_an_observed_failure():
    organism = OpaquePlayer("h7b7")
    attempt = play_mate_one(organism, "k7/7R/1K6/8/8/8/8/8 w - - 0 1",
                           event_id=0, learn=True)
    assert attempt.reason == "stalemate" and attempt.reward == -1
    assert attempt.real_moves == 1 and chess.Board(attempt.after_fen).is_stalemate()


def _reading(fen=M1):
    board = chess.Board(fen)
    return BoardSensor(PositionReading(
        tuple(sorted((sq, p.piece_type, p.color) for sq, p in board.piece_map().items())),
        board.turn, board.halfmove_clock, board.fullmove_number,
    ))


def test_empty_start_and_no_runtime_teacher(monkeypatch):
    from recon_lite_chess.autogrowth import native_single_graph_curriculum as native

    def forbidden(*_a, **_kw):
        raise AssertionError("teacher/reward table is forbidden in learner interaction")

    for name in ("_mate_moves", "_forced_mate_in_two_first_moves", "_move_reward"):
        monkeypatch.setattr(native, name, forbidden)
    monkeypatch.setattr(native.NativeReConKRKGraph, "train_action_rewards", forbidden)
    organism = NativeOrganism()
    assert not organism._graph.triplet_ids
    assert len(organism._graph.graph.nodes) == 1
    assert not organism._graph.graph.edges
    assert not organism._credit.states
    attempt = play_mate_one(organism, M1, event_id=0, learn=True)
    assert attempt.real_moves == 1
    assert len(organism._graph.triplet_ids) == 1
    assert organism._observations == 1
    assert sum(s.terminal_evidence for s in organism._credit.states.values()) == 1
    for node in organism._graph.graph.nodes.values():
        if node.ntype == NodeType.TERMINAL:
            assert organism._graph.graph.children(node.nid) == []


def test_feedback_binding_rejects_duplicates_and_partial_checkpoints(tmp_path):
    organism = NativeOrganism()
    action = organism.act(_reading(), event_id=4, learn=True)
    with pytest.raises(ValueError, match="match"):
        organism.observe(Feedback(3, action, -1, "exercise_timeout"))
    with pytest.raises(ValueError, match="reward"):
        organism.observe(Feedback(4, action, math.nan, "exercise_timeout"))
    with pytest.raises(RuntimeError, match="between action"):
        save_checkpoint(RunState(organism, "test", 0, source_identity()), tmp_path)
    organism.observe(Feedback(4, action, -1, "synthetic_test_outcome"))
    with pytest.raises(RuntimeError, match="no pending"):
        organism.observe(Feedback(4, action, -1, "synthetic_test_outcome"))
    with pytest.raises(ValueError, match="increasing"):
        organism.act(_reading(), event_id=4, learn=True)
    assert organism._observations == 1


def test_value_and_slow_memory_have_the_same_meaning():
    organism = NativeOrganism(NativeConfig(consolidation_every=1))
    for i in range(100):
        action = organism.act(_reading(), event_id=i, learn=True)
        _, _, decision = organism._pending
        before = decision.prediction
        # Synthetic positive outcome tests numerical semantics, not chess skill.
        organism.observe(Feedback(i, action, 1.0, "synthetic_test_outcome"))
        q = organism._graph._local_action_option_value(decision.triplet_id, action)
        state = organism._credit.states[decision.triplet_id + ":" + action]
        expected = min(1.0, before + organism._graph.config.eta_m3 * min(1.0, 1.0 - before))
        assert q == pytest.approx(expected)
        assert state.fast_value == pytest.approx(q)
        if any(s.slow_value > 0 for s in organism._credit.states.values()):
            break
    # Direct clean evidence, not a validation score, admits slow local memory.
    assert any(s.slow_value > 0 for s in organism._credit.states.values())
    assert not organism._graph.frozen_policy_triplet_ids


def test_resume_reproduces_future_moves_values_and_topology(tmp_path):
    organism = NativeOrganism(NativeConfig(consolidation_every=3))
    for i in range(4):
        play_mate_one(organism, M1, event_id=i, learn=True)
    state = RunState(organism, "test", 2, source_identity(), next_event=4)
    save_checkpoint(state, tmp_path)
    restored = load_checkpoint(tmp_path).organism
    for i in range(4, 10):
        a = play_mate_one(organism, M1, event_id=i, learn=True)
        b = play_mate_one(restored, M1, event_id=i, learn=True)
        assert a == b
    assert organism._graph.canonical_semantic_manifest() == restored._graph.canonical_semantic_manifest()
    assert organism._credit.states == restored._credit.states
    before = restored._graph.canonical_semantic_manifest()
    play_mate_one(restored, M1, event_id=0, learn=False)
    assert before == restored._graph.canonical_semantic_manifest()


@pytest.fixture(scope="module")
def pool(tmp_path_factory):
    directory = tmp_path_factory.mktemp("coach") / "pool"
    prepare(directory, seed=43, train=8, validation=4, test=4)
    return directory


def test_pool_contains_only_valid_exercises_and_disjoint_orbits(pool):
    orbits = {}
    for split in ("train", "validation", "test"):
        fens, _ = load_split(pool, split)
        orbits[split] = set()
        for fen in fens:
            board = chess.Board(fen)
            assert board.is_valid() and board.turn == chess.WHITE
            found = False
            for move in list(board.legal_moves):
                board.push(move)
                found |= board.is_checkmate()
                board.pop()
            assert found
            orbits[split].add(orbit_key(board))
    assert not orbits["train"] & (orbits["validation"] | orbits["test"])
    assert not orbits["validation"] & orbits["test"]
    manifest = json.loads((pool / "manifest.json").read_text())
    assert "moves" not in manifest and "answers" not in manifest


def _args(pool, run, episodes, *, resume=False):
    return argparse.Namespace(pool=pool, run=run, seed=2, episodes=episodes,
                              checkpoint_every=4, progress_every=4, wall_seconds=60, resume=resume)


def test_runner_resume_order_and_separate_evaluation(pool, tmp_path):
    run = tmp_path / "run"
    initial = train(_args(pool, run, 0))
    assert initial["attempts"] == initial["real_white_moves"] == 0
    baseline = evaluate(argparse.Namespace(pool=pool, run=run, split="validation"))
    assert baseline["checkmates"] == 0 and baseline["abstentions"] == 4
    first = train(_args(pool, run, 4, resume=True))
    assert first["attempts"] == first["real_white_moves"] == 4
    with (run / "moves.jsonl").open("a") as stream:
        stream.write('{"event_id":4,"uncommitted":true}\n')
    resumed = train(_args(pool, run, 8, resume=True))
    assert resumed["attempts"] == 8
    events = [json.loads(line) for line in (run / "moves.jsonl").read_text().splitlines()]
    assert [e["event_id"] for e in events] == list(range(8))
    assert all("uncommitted" not in e for e in events)
    control = tmp_path / "control"
    train(_args(pool, control, 8))
    assert (run / "moves.jsonl").read_text() == (control / "moves.jsonl").read_text()
    before = (run / "latest.json").read_bytes()
    result = evaluate(argparse.Namespace(pool=pool, run=run, split="validation"))
    assert result["count"] == 4 and result["learning"] is False
    assert (run / "latest.json").read_bytes() == before
    (run / "run.lock").mkdir()
    with pytest.raises(RuntimeError, match="stop the active"):
        evaluate(argparse.Namespace(pool=pool, run=run, split="test"))
    assert not (run / "final_test_opened.json").exists()
    (run / "run.lock").rmdir()
    evaluate(argparse.Namespace(pool=pool, run=run, split="test"))
    with pytest.raises(RuntimeError, match="final test"):
        train(_args(pool, run, 12, resume=True))


def test_checkpoint_rejects_corrupted_transport(tmp_path):
    state = RunState(NativeOrganism(), "test", 2, source_identity())
    path = save_checkpoint(state, tmp_path)
    with path.open("ab") as stream:
        stream.write(b"corrupt")
    with pytest.raises(ValueError, match="transport"):
        load_checkpoint(tmp_path)
