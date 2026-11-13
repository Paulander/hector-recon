from dataclasses import asdict, replace
import json
import pickle

import chess
import pytest

from recon_lite_chess.autogrowth.mate_horizon_opponent import choose_mate_horizon_reply
from recon_lite_chess.coach.interface import Feedback
from recon_lite_chess.coach.m2_schema import M2ChessFeaturePort
from recon_lite_chess.coach.selective import create_actor
from recon_lite_chess.coach.setup_practice import (
    SetupPracticeActor, SetupPracticeError, create_setup_actor, play_setup_practice,
)
from recon_lite_hector.learning.recursive_context import Expression, combine
from recon_lite_hector.learning.route_action_bud import RouteActionEvidence
from recon_lite_hector.learning.terminal_development import Condition, PlasticWeight


TWO_MOVE = "1K6/8/k7/3R4/8/8/8/8 w - - 0 1"
ONE_MOVE = "k7/8/1K6/8/8/8/8/7R w - - 0 1"


def _prefer_move(actor, fen, move, port_type, *, weight=1.0):
    """Plant one native reader per distinguishing coordinate in a test graph."""
    port = port_type(chess.Board(fen))
    bindings = port.bindings()
    coordinates = [i for i in range(len(port.schema))
                   if len({port.measure(i, name) for name in bindings}) > 1]
    leaf = actor.leaves[0]
    contributors = list(leaf.contributions)
    for i in coordinates:
        atom = (i, port.measure(i, move))
        cid = actor.next_condition
        actor.next_condition += 1
        actor.conditions[cid] = Condition(cid, (atom,), "and", actor.completed,
                                         weight=PlasticWeight(fast=weight))
        actor.base_expressions[cid] = Expression("read", atom=atom)
        actor.birth_visits[cid] = actor.owner_visits[0]
        actor.owner_seen[0].add(actor.base_expressions[cid])
        contributors.append(cid)
    actor.leaves[0] = replace(leaf, contributions=tuple(contributors))
    actor._rebuild(actor.slots)
    actor.validate_ownership()


@pytest.fixture
def winning_pair():
    from recon_lite_chess.coach.terminal import ChessFeaturePort

    setup = create_setup_actor(seed=0)
    finisher = create_actor(seed=2)
    _prefer_move(setup, TWO_MOVE, "b8c7", M2ChessFeaturePort)
    board = chess.Board(TWO_MOVE)
    board.push_uci("b8c7")
    board.push_uci("a6a7")
    _prefer_move(finisher, board.fen(), "d5a5", ChessFeaturePort)
    return setup, finisher


def test_actual_setup_reply_and_frozen_finish_then_one_owned_credit(winning_pair):
    setup, finisher = winning_pair
    master = pickle.dumps(finisher)
    finisher_calls = []
    original_act = type(finisher).act

    def act(actor, port, *, event_id, learn):
        assert actor is not finisher and not learn
        assert actor.exploration_rng.getstate() == finisher.exploration_rng.getstate()
        assert setup.completed == 0 and setup.pending[0][:2] == (9, "b8c7")
        finisher_calls.append(port.bindings())
        return original_act(actor, port, event_id=event_id, learn=learn)

    def reply(board):
        assert [move.uci() for move in board.move_stack] == ["b8c7"]
        assert setup.completed == 0 and setup.owner_visits == {0: 0}
        return choose_mate_horizon_reply(board)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(type(finisher), "act", act)
        episode = play_setup_practice(setup, finisher, TWO_MOVE, event_id=9, learn=True,
                                      opponent=reply)
    assert len(finisher_calls) == 1
    assert [(m.role, m.action) for m in episode.moves] == [
        ("setup", "b8c7"), ("black", "a6a7"), ("m1", "d5a5"),
    ]
    assert all(a.after_fen == b.before_fen for a, b in zip(episode.moves, episode.moves[1:]))
    assert chess.Board(episode.moves[-1].after_fen).is_checkmate()
    assert (episode.outcome, episode.reward) == ("checkmate", 1.0)
    assert episode.credit.feedback == Feedback(9, "b8c7", 1.0)
    assert episode.menu.score_spread > 0.0
    assert episode.frame.active == tuple(cid for cid, _, _ in episode.credit.weights_before)
    assert len(episode.frame.active) > 1
    assert setup.completed == 1 and setup.owner_visits == {0: 1} and not setup.pending
    assert pickle.dumps(finisher) == master
    assert json.loads(json.dumps(asdict(episode)))["moves"][2]["role"] == "m1"


def test_credit_decays_weights_but_evidence_keeps_raw_residual(winning_pair):
    setup, finisher = winning_pair
    episode = play_setup_practice(setup, finisher, TWO_MOVE, event_id=0, learn=True)
    credit = episode.credit
    assert credit.multiplier == 0.8
    assert credit.residual == 1.0 - episode.frame.prediction
    assert credit.residual != 0.0
    delta = 0.3 * 0.8 * credit.residual / len(episode.frame.active)
    assert credit.weights_after == tuple(
        (cid, fast + delta, slow) for cid, fast, slow in credit.weights_before
    )
    assert all(evidence.n0 + evidence.n1 == 1
               and evidence.sum0 + evidence.sum1 == credit.residual
               for evidence in setup.birth_evidence[0])
    assert all(evidence.sum0 + evidence.sum1 == credit.residual
               for evidence in setup.owner_evidence[0].values())


@pytest.mark.parametrize("fen,move,expected,roles,reward", [
    (ONE_MOVE, "h1h8", "checkmate", ["setup"], 1.0),
    ("k7/7R/1K6/8/8/8/8/8 w - - 0 1", "h7b7", "stalemate", ["setup"], -1.0),
    (ONE_MOVE.replace("0 1", "98 1"), "h1d1", "draw", ["setup"], -1.0),
    (TWO_MOVE, "d5b5", "rook_captured", ["setup", "black"], -1.0),
])
def test_early_outcome_closes_one_setup_frame_without_decay(fen, move, expected, roles, reward):
    setup = create_setup_actor(seed=0)
    finisher = create_actor(seed=2)
    _prefer_move(setup, fen, move, M2ChessFeaturePort)
    replies = []

    def reply(board):
        replies.append(board.peek().uci())
        return choose_mate_horizon_reply(board)

    episode = play_setup_practice(setup, finisher, fen, event_id=0, learn=True, opponent=reply)
    assert [m.role for m in episode.moves] == roles
    assert replies == ([move] if "black" in roles else [])
    assert (episode.outcome, episode.reward) == (expected, reward)
    assert episode.credit.multiplier == 1.0
    assert episode.credit.feedback == Feedback(0, move, reward)


def test_greedy_evaluation_uses_disposable_actors_and_returns_no_credit(winning_pair):
    setup, finisher = winning_pair
    before = pickle.dumps(setup), pickle.dumps(finisher)
    episode = play_setup_practice(setup, finisher, TWO_MOVE, event_id=0, learn=False)
    assert episode.outcome == "checkmate"
    assert episode.frame is None and episode.credit is None and not episode.development
    assert episode.completed_before == episode.completed_after == 0
    assert episode.menu.score_spread > 0.0
    assert (pickle.dumps(setup), pickle.dumps(finisher)) == before


@pytest.mark.parametrize("bad_reply", [chess.Move.null(), "a6a7"])
def test_invalid_reply_is_technical_and_leaves_the_frame_uncredited(winning_pair, bad_reply):
    setup, finisher = winning_pair
    weights = setup._weights(setup.conditions)
    with pytest.raises(SetupPracticeError, match="legal Black move") as failed:
        play_setup_practice(setup, finisher, TWO_MOVE, event_id=0, learn=True,
                            opponent=lambda _: bad_reply)
    assert failed.value.stage == "black" and isinstance(failed.value.__cause__, ValueError)
    assert [move.role for move in failed.value.moves] == ["setup"]
    assert failed.value.last_fen == failed.value.moves[-1].after_fen
    assert setup.pending[0][:2] == (0, "b8c7")
    assert setup.completed == 0 and setup.owner_visits == {0: 0}
    assert setup._weights(setup.conditions) == weights and not setup.development_history
    with pytest.raises(RuntimeError, match="completed"):
        pickle.dumps(setup)
    with pytest.raises(RuntimeError, match="completed"):
        play_setup_practice(setup, finisher, TWO_MOVE, event_id=1, learn=True)


def test_finisher_failure_is_not_a_training_label(winning_pair, monkeypatch):
    setup, finisher = winning_pair
    weights = setup._weights(setup.conditions)

    def fail(*args, **kwargs):
        raise RuntimeError("synthetic finisher failure")

    monkeypatch.setattr(type(finisher), "act", fail)
    with pytest.raises(SetupPracticeError, match="synthetic finisher failure") as failed:
        play_setup_practice(setup, finisher, TWO_MOVE, event_id=0, learn=True)
    assert failed.value.stage == "m1" and isinstance(failed.value.__cause__, RuntimeError)
    assert [move.role for move in failed.value.moves] == ["setup", "black"]
    assert setup.pending[0][:2] == (0, "b8c7")
    assert setup.completed == 0 and setup._weights(setup.conditions) == weights


def test_malformed_and_stale_feedback_leave_pending_and_weights_intact(winning_pair):
    setup, _ = winning_pair
    port = M2ChessFeaturePort(chess.Board(TWO_MOVE))
    action = setup.act(port, event_id=3, learn=True)
    pending, weights = setup.pending[:], setup._weights(setup.conditions)
    malformed = (Feedback(2, action, 1.0), Feedback(3, "wrong", 1.0),
                 Feedback(3, action, float("nan")), Feedback(3, action, float("inf")),
                 Feedback(3, action, True), Feedback(3, action, 0.0),
                 Feedback(True, action, 1.0))
    for feedback in malformed:
        with pytest.raises(ValueError, match="requires a bound|does not bind"):
            setup._credit_practice(feedback, finisher_committed=True)
        assert setup.pending == pending and setup._weights(setup.conditions) == weights
        assert setup.completed == 0 and setup.owner_visits == {0: 0}
    good = Feedback(3, action, 1.0)
    setup._credit_practice(good, finisher_committed=True)
    with pytest.raises(ValueError, match="does not bind"):
        setup._credit_practice(good, finisher_committed=True)
    assert setup.completed == 1


def test_growth_runs_at_the_owner_boundary_after_the_pending_frame_closes(winning_pair, monkeypatch):
    setup, finisher = winning_pair
    setup.owner_visits[0] = setup.completed = 63
    original = SetupPracticeActor._run_development
    seen = []

    def run_development(actor, owner):
        assert not actor.pending
        assert all(getattr(actor, name) is None for name in (
            "owner_pending", "candidate_pending", "action_bud_pending", "birth_search_pending",
            "deferred_development",
        ))
        assert actor.owner_visits[owner] == actor.completed == 64
        seen.append(owner)
        original(actor, owner)

    monkeypatch.setattr(SetupPracticeActor, "_run_development", run_development)
    episode = play_setup_practice(setup, finisher, TWO_MOVE, event_id=63, learn=True)
    assert seen == [0]
    assert len(episode.development) == 1
    assert (episode.development[0].owner, episode.development[0].visit) == (0, 64)
    assert "_practice_capture" not in vars(setup)
    pickle.dumps(setup)


def test_episode_records_native_action_bud_identity(winning_pair):
    setup, finisher = winning_pair
    setup.owner_visits[0] = setup.completed = 63
    evidence = RouteActionEvidence()
    # Plant prior evidence. The ordinary development code still chooses and
    # installs the real bud after this fixture's selected action closes.
    for route in (False, True):
        for reader in (False, True):
            for _ in range(setup.development_config.min_support):
                evidence.add(route, reader, True, 10.0 if route and reader else 0.0)
    setup.action_bud_evidence[0][(0, 0)] = evidence
    expected = combine("and", (setup.owner_candidates[0], setup.action_readers[0]))
    before = set(setup.conditions)

    episode = play_setup_practice(setup, finisher, TWO_MOVE, event_id=63, learn=True)

    record, = episode.development
    admitted, = set(setup.conditions) - before
    assert type(record.bud) is int and record.bud == admitted
    assert record.born is None
    assert admitted == setup.action_bud_history[-1]["condition"]
    assert setup.base_expressions[admitted] == expected
    assert admitted in setup.leaves[0].contributions
    assert float(setup.conditions[admitted].weight) == 0.0


def test_resume_reproduces_native_moves_credit_and_state(winning_pair):
    setup, finisher = winning_pair
    play_setup_practice(setup, finisher, TWO_MOVE, event_id=0, learn=True)
    restored_setup, restored_finisher = pickle.loads(pickle.dumps((setup, finisher)))
    a = play_setup_practice(setup, finisher, TWO_MOVE, event_id=1, learn=True)
    b = play_setup_practice(restored_setup, restored_finisher, TWO_MOVE, event_id=1, learn=True)
    assert a == b
    assert setup._weights(setup.conditions) == restored_setup._weights(restored_setup.conditions)
    assert setup.birth_evidence == restored_setup.birth_evidence
    assert setup.exploration_rng.getstate() == restored_setup.exploration_rng.getstate()
    weights = setup._weights(setup.conditions)
    with pytest.raises(ValueError, match="event must increase"):
        play_setup_practice(setup, finisher, TWO_MOVE, event_id=1, learn=True)
    assert setup.completed == 2 and setup._weights(setup.conditions) == weights


def test_ordinary_two_move_timeout_uses_negative_delayed_setup_credit():
    setup = create_setup_actor(seed=0)
    finisher = create_actor(seed=2)
    episode = play_setup_practice(setup, finisher, TWO_MOVE, event_id=0, learn=True)
    assert [move.role for move in episode.moves] == ["setup", "black", "m1"]
    assert (episode.outcome, episode.reward) == ("exercise_timeout", -1.0)
    assert episode.credit.multiplier == 0.8
    assert episode.credit.feedback == Feedback(0, episode.moves[0].action, -1.0)
    assert episode.menu.score_spread == 0.0
