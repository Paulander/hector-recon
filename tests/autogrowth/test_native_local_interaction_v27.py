"""Mechanism tests; fixture answers below are never supplied to a learner."""
from dataclasses import asdict, replace
import inspect
import pickle
from types import SimpleNamespace

import chess
import pytest

from recon_lite.choice_genome import finite_local_uncertainty
from recon_lite_chess.autogrowth import native_intrinsic_curriculum as curriculum
from recon_lite_chess.autogrowth.native_adaptive_boundary_development import development_config
from recon_lite_chess.autogrowth.mate_horizon_opponent import choose_mate_horizon_reply
from recon_lite_chess.autogrowth.foundation_curriculum import _mate_moves
from recon_lite_chess.autogrowth.native_single_graph_curriculum import (
    LOCAL_EXPLORATION_FINITE_UCB, LOCAL_EXPLORATION_BOUNDED,
    NativeReConKRKGraph, NativeSingleGraphConfig,
)

M1 = "k7/8/1K6/8/8/8/8/7R w - - 0 1"


@pytest.mark.parametrize("counts", [(-1, 0), (1, 0), (True, 1), (0, 1.0)])
def test_uncertainty_rejects_malformed_local_counts(counts):
    with pytest.raises(ValueError):
        finite_local_uncertainty(*counts)


def test_finite_uncertainty_can_lose_to_success_without_killing_exploration():
    assert finite_local_uncertainty(0, 0) == 0.0
    # One well-valued incumbent can win before any other contact. Eventually
    # repeated local use raises uncertainty enough to revisit a bad prior.
    decisions = []
    counts = [1, 0]
    for _ in range(64):
        values = [0.9, -0.9]
        chosen = max(range(2), key=lambda i: values[i] + finite_local_uncertainty(counts[i], sum(counts)))
        decisions.append(chosen)
        counts[chosen] += 1
    assert decisions[0] == 0
    assert 1 in decisions
    assert decisions.count(0) > decisions.count(1)


@pytest.mark.parametrize("mode", [LOCAL_EXPLORATION_FINITE_UCB, LOCAL_EXPLORATION_BOUNDED])
def test_native_incumbent_can_recur_before_all_first_contacts(monkeypatch, mode):
    graph = NativeReConKRKGraph(config=NativeSingleGraphConfig(
        max_ticks=80, key_mode="canonical", local_exploration_mode=mode,
    ))
    board = chess.Board(M1)
    incumbent = min(board.legal_moves, key=lambda move: move.uci())
    # Synthetic outcome-grounded update, not a chess competency claim.
    identity = graph.apply_intrinsic_td(board, incumbent, td_error=0.1,
        prediction_value=0.9, stage_diagnostic="synthetic")
    monkeypatch.setattr(graph, "_full_audit_candidates", lambda *_a, **_k: [
        (-9.0, move.uci(), identity) for move in board.legal_moves
    ])
    decision = graph.choose_local_training_action(board, "synthetic")
    assert decision.move == incumbent
    assert decision.action_option_exposure == 1
    assert decision.total_current_action_option_exposures == 1
    assert decision.action_option_count > 1
    assert decision.prediction == pytest.approx(0.91)
    assert decision.activation > decision.prediction
    # Choice has not fabricated another REAL contact.
    assert graph._local_action_option_exposure(identity, incumbent.uci()) == 1


@pytest.mark.parametrize("mode", [LOCAL_EXPLORATION_FINITE_UCB, LOCAL_EXPLORATION_BOUNDED])
def test_finite_local_choice_pickle_and_readonly_parity(mode):
    graph = NativeReConKRKGraph(config=NativeSingleGraphConfig(
        max_ticks=80, key_mode="canonical", local_exploration_mode=mode,
    ))
    board = chess.Board(M1)
    for _ in range(3):
        action = graph.choose_local_training_action(board, "parity")
        graph.apply_intrinsic_td(board, action.move, td_error=-0.2,
            prediction_value=action.prediction, stage_diagnostic="parity")
    restored = pickle.loads(pickle.dumps(graph))
    assert graph.choose_local_training_action(board, "parity").to_manifest() == restored.choose_local_training_action(board, "parity").to_manifest()
    before = graph.canonical_semantic_manifest()
    policy = graph.choose_local_policy_action(board)
    assert policy is not None and policy.exploration_bonus == 0.0
    assert graph.canonical_semantic_manifest() == before


@pytest.mark.parametrize("fen", curriculum.R1_RETIRED_DEVELOPMENT_FENS[:4])
def test_opponent_never_allows_mate_when_a_defence_exists(fen):
    board = chess.Board(fen)
    tested = 0
    for first in board.legal_moves:
        after_first = board.copy(stack=False)
        after_first.push(first)
        if after_first.is_game_over():
            continue
        before = after_first.fen()
        reply = choose_mate_horizon_reply(after_first)
        assert after_first.fen() == before
        assert reply in after_first.legal_moves
        selected = after_first.copy(stack=False)
        selected.push(reply)
        # Independent test-side all-reply specification. No answer set is
        # passed to a network, reward function, or candidate generator.
        unavoidable = True
        for alternative in after_first.legal_moves:
            successor = after_first.copy(stack=False)
            successor.push(alternative)
            unavoidable = unavoidable and bool(_mate_moves(successor))
        assert bool(_mate_moves(selected)) == unavoidable
        assert choose_mate_horizon_reply(after_first) == reply
        tested += 1
    assert tested > 0


def test_opponent_api_has_no_learner_or_solution_payload():
    assert tuple(inspect.signature(choose_mate_horizon_reply).parameters) == ("board",)
    with pytest.raises(ValueError):
        choose_mate_horizon_reply(chess.Board(M1))
    with pytest.raises(ValueError):
        choose_mate_horizon_reply(chess.Board())
    # A claim is not a board move, so fail closed rather than overclaim a
    # move-only opponent's handling of the fifty-move rule.
    with pytest.raises(ValueError, match="draw claims"):
        choose_mate_horizon_reply(chess.Board("8/8/1R6/8/8/1K6/8/1k6 b - - 100 1"))
    with pytest.raises(ValueError, match="terminal"):
        choose_mate_horizon_reply(chess.Board("k6R/8/1K6/8/8/8/8/8 b - - 0 1"))


def test_evaluation_attempts_unknown_finisher_without_certifying_it(monkeypatch):
    fen = curriculum.R1_RETIRED_DEVELOPMENT_FENS[0]
    first = curriculum._forced_mate_in_two_first_moves(chess.Board(fen))[0]
    monkeypatch.setattr(curriculum, "_supported_local_policy_action", lambda *_: first)
    queries = []

    def fixture_policy(_authority, board, **_kwargs):
        queries.append(board.fen())
        return False, {"selected_move": _mate_moves(board)[0].uci()}

    monkeypatch.setattr(curriculum, "_v2_r0_available", fixture_policy)
    authority = SimpleNamespace(certification_receipts=())
    kwargs = dict(max_samples=1, r0_child_authority=authority,
        action_selection_mode=curriculum.R1_ACTION_SELECTION_LOCAL_RECON)
    old = curriculum._evaluate_r1(None, (fen,), **kwargs)
    new = curriculum._evaluate_r1(None, (fen,), require_certified_finisher=False, **kwargs)
    assert old["conversion_count"] == 0
    assert new["conversion_count"] == 1
    assert new["reply_evaluation_mode"] == "exhaustive"
    assert new["uncertified_finisher_mate_count"] == new["reply_evaluation_count"]
    assert authority.certification_receipts == ()
    assert not new["finisher_action_requires_certification"]


def test_v27_configuration_changes_only_the_named_interaction_contract():
    old = development_config(continuous_hypothesis_evidence=True)
    new = development_config(continuous_hypothesis_evidence=True, local_interaction=True)
    assert {k for k, v in asdict(old).items() if asdict(new)[k] != v} == {
        "r1_local_exploration_mode", "r1_black_policy", "r1_require_certified_finisher_for_action",
    }
    assert new.r1_black_policy == curriculum.R1_BLACK_TASK_PERFECT
    assert new.r1_local_exploration_mode == LOCAL_EXPLORATION_BOUNDED
    with pytest.raises(ValueError):
        curriculum._effective_r1_reply_policy(new, None)
    with pytest.raises(ValueError):
        replace(new, r1_require_certified_finisher_for_action="false")


@pytest.mark.parametrize("mode", [LOCAL_EXPLORATION_FINITE_UCB, LOCAL_EXPLORATION_BOUNDED])
def test_maximal_experienced_return_is_not_beaten_by_imagined_upside(monkeypatch, mode):
    graph = NativeReConKRKGraph(config=NativeSingleGraphConfig(
        max_ticks=80, key_mode="canonical", local_exploration_mode=mode,
    ))
    board = chess.Board(M1)
    incumbent = min(board.legal_moves, key=lambda move: move.uci())
    identity = graph.apply_intrinsic_td(board, incumbent, td_error=0.0,
        prediction_value=1.0, stage_diagnostic="synthetic_maximal_return")
    monkeypatch.setattr(graph, "_full_audit_candidates", lambda *_a, **_k: [
        (19.0, move.uci(), identity) for move in board.legal_moves
    ])
    selected = graph.choose_local_training_action(board, "synthetic_maximal_return")
    if mode == LOCAL_EXPLORATION_FINITE_UCB:
        # Explicitly retain the counterexample to the first attempted fix.
        assert selected.move != incumbent
        assert selected.activation > 1.0
    else:
        assert selected.move == incumbent
        assert selected.activation == selected.prediction == 1.0
        assert selected.exploration_bonus == 0.0


def test_bounded_attention_releases_an_incumbent_after_bad_returns(monkeypatch):
    graph = NativeReConKRKGraph(config=NativeSingleGraphConfig(
        max_ticks=80, key_mode="canonical", local_exploration_mode=LOCAL_EXPLORATION_BOUNDED,
    ))
    board = chess.Board(M1)
    incumbent = min(board.legal_moves, key=lambda move: move.uci())
    identity = graph.apply_intrinsic_td(board, incumbent, td_error=0.0,
        prediction_value=1.0, stage_diagnostic="synthetic_contrast")
    monkeypatch.setattr(graph, "_full_audit_candidates", lambda *_a, **_k: [
        (19.0, move.uci(), identity) for move in board.legal_moves
    ])
    for _ in range(32):
        action = graph.choose_local_training_action(board, "synthetic_contrast")
        assert action.activation <= 1.0
        if action.move != incumbent:
            break
        graph.apply_intrinsic_td(board, action.move, td_error=-1.0-action.prediction,
            prediction_value=action.prediction, stage_diagnostic="synthetic_contrast")
    else:
        pytest.fail("contradicted incumbent retained attention indefinitely")


def test_bounded_attention_does_not_hide_negative_value_updates(monkeypatch):
    graph = NativeReConKRKGraph(config=NativeSingleGraphConfig(
        max_ticks=80, key_mode="canonical", local_exploration_mode=LOCAL_EXPLORATION_BOUNDED,
    ))
    board = chess.Board(M1)
    incumbent = min(board.legal_moves, key=lambda move: move.uci())
    identity = graph.apply_intrinsic_td(board, incumbent, td_error=0.0,
        prediction_value=1.0, stage_diagnostic="synthetic_contrast")
    graph.apply_intrinsic_td(board, incumbent, td_error=-1.0,
        prediction_value=1.0, stage_diagnostic="synthetic_contrast")
    monkeypatch.setattr(graph, "_full_audit_candidates", lambda *_a, **_k: [
        (19.0, move.uci(), identity) for move in board.legal_moves
    ])
    # Both optimistic activations reach1, but the contradicted value0.9
    # must not beat an alternative's0.95 merely through familiarity.
    selected = graph.choose_local_training_action(board, "synthetic_contrast")
    assert selected.move != incumbent
    assert selected.prediction == pytest.approx(0.95)
    assert selected.activation == 1.0
