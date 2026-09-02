"""Data-free causal-order regressions for event-local structural settlement.

The bounded authority double models retirement of the exact shell provider
used by the current all-reply signal.  Provider validation, credit transition,
and graph TD are real.  The selected action/outcome are synthetic test inputs,
not chess-performance evidence; execution stops before any evaluation or file
write.  Real retirement/replacement and persistence have separate exact tests.
"""

from types import SimpleNamespace

import chess
import pytest

from recon_lite_chess.autogrowth import native_intrinsic_curriculum as curriculum
from recon_lite_chess.autogrowth.native_all_reply_envelope import (
    AvailabilityState,
    ReplyAuthority,
)
from recon_lite_chess.autogrowth.native_prospective_boundary_candidate_ecology import (
    ProspectiveBoundaryCandidateEcology,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import (
    StructuralMode,
)
from recon_lite_chess.autogrowth.native_single_graph_curriculum import (
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
)
from recon_lite_hector.learning import IntrinsicCreditConfig, IntrinsicCreditEngine
from tests.autogrowth.test_native_shell_provider import _provider


class _NextDecision(Exception):
    """Stop before the second decision, without evaluating or snapshotting."""


class _CreditFailure(Exception):
    pass


class _ProviderAuthority:
    """Only the bounded surfaces needed before the second decision stop."""

    structural_mode = StructuralMode.EVENT_DRIVEN
    pending_event = None

    def __init__(self, events):
        self.events = events
        record = _provider()
        self.provider_id = str(record["cell_id"])
        self.live_providers = {self.provider_id: record}
        self.boundary_promotion_requests = {}
        self.base = SimpleNamespace(receipts={}, r0=SimpleNamespace())
        self.consumed_receipts = {}
        self.accepted_real_references = {}

    def dumps(self):
        # This stand-in deliberately makes no serialization claim.  The
        # production arm's clone seam returns this same bounded test object.
        return self

    @classmethod
    def loads(cls, value):
        assert isinstance(value, cls)
        return value

    def continuation_digest(self):
        return "event-local-order-test"

    def native_provider_response(self, provider_id):
        return self.live_providers.get(provider_id)

    def frame_session(self):
        self.events.append("frame_open")
        return SimpleNamespace(close=lambda: self.events.append("frame_close"))


def _exercise_event(tmp_path, monkeypatch, *, duplicate=False, fail_at=None):
    events = []
    authority = _ProviderAuthority(events)
    graph = NativeReConKRKGraph(config=NativeSingleGraphConfig(
        include_symmetries=False,
        max_ticks=40,
        indexed_scheduler=True,
        key_mode="canonical",
    ))
    credit = IntrinsicCreditEngine(IntrinsicCreditConfig())
    credit.register(curriculum.R0_COMPETENCE_ID, mature=True)
    # A legal code-defined board is merely the native graph's action input.
    # No move solver, fixture corpus, environment rollout, or oracle is used.
    fen = "8/8/8/8/8/5K2/R7/7k w - - 0 1"
    pools = curriculum._Pools(
        r0_train=(), r0_validation=(), r0_regression=(),
        gate_train_decoys=(), gate_validation_decoys=(),
        gate_regression_decoys=(),
        r1_train=(fen, fen), r1_validation=(), r1_regression=(),
        r0_train_strata=(), r0_validation_strata=(), r0_regression_strata=(),
        r0_excluded_fens=(), r0_pool_mode="synthetic_order_test",
        r1_train_strata=("synthetic", "synthetic"),
        r1_validation_strata=(), r1_regression_strata=(),
        r1_pool_mode="synthetic_order_test",
    )
    config = curriculum.NativeIntrinsicCurriculumConfig(
        progress_path=str(tmp_path / "unused-progress.json"),
        r1_snapshot_dir=str(tmp_path / "unused-snapshots"),
        resume_r1_snapshots=False,
        r0_boundary_ecology_enabled=True,
        r0_action_selection_mode=curriculum.R0_ACTION_SELECTION_LOCAL_RECON,
        r1_action_selection_mode=curriculum.R1_ACTION_SELECTION_LOCAL_RECON,
        validation_controls_stage_transitions=False,
        r1_reply_policy=curriculum.R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE,
        r0_replay_per_r1_epoch=0,
    )
    arm = curriculum.R1MechanisticArm(
        name="event-local-order",
        bootstrap_enabled=True,
        availability_mode=curriculum.V2_PROSPECTIVE_AVAILABILITY,
        mature_child_priority=False,
    )
    selected = []
    nominated_sets = []
    credited_events = []

    def select(local_graph, board, **_kwargs):
        if selected:
            events.append("next_decision")
            raise _NextDecision
        events.append("select")
        move = chess.Move.from_uci("a2a3")
        assert move in board.legal_moves
        triplet_id = local_graph.ensure_triplet(board, move, stage="order-test")
        selected.append(triplet_id)
        return move, triplet_id, True, 0.0, None

    def episode(current_authority, _after_first, **kwargs):
        assert current_authority is authority
        assert kwargs["strict_adaptive"] is True
        pending_ids = kwargs["pending_boundary_candidate_ids"]
        assert isinstance(pending_ids, set) and not pending_ids
        nominated_sets.append(pending_ids)
        events.append("duplicate_virtual" if duplicate else "real")
        if not duplicate:
            pending_ids.add("eligible-existing-bud")
        record = authority.native_provider_response(authority.provider_id)
        envelope = SimpleNamespace(
            state=AvailabilityState.AVAILABLE,
            positive_gate=True,
            replies=(ReplyAuthority(
                reply_id="synthetic-reply",
                state=AvailabilityState.AVAILABLE,
                confidence=0.6, value=0.6, exposure_count=0, grounded=True,
            ),),
            value=0.6,
        )
        records = {authority.provider_id: record}
        signal = curriculum._grounded_all_reply_successor_signal(
            envelope,
            bootstrap_enabled=True, actual_mate=True,
            clean_preoutcome_evidence=True,
            credit=credit,
            provider_ids=(authority.provider_id,),
            provider_records=records,
            external_provider_resolver=authority.native_provider_response,
            strict_adaptive=True,
        )
        assert signal is not None
        credit.preflight_explicit_successor_signal(
            signal,
            recipient_id=kwargs["decision_id"],
            external_provider_records=records,
            external_provider_resolver=authority.native_provider_response,
        )
        return None, (authority.provider_id,), {
            "reply_orbits": (),
            "successor_signal": signal,
            "external_provider_records": records,
            "manifest": {"real_event": not duplicate},
            "structural": None,
            "response": {},
        }

    original_transition = credit.transition

    def transition(*args, **kwargs):
        events.append("credit")
        assert authority.native_provider_response(authority.provider_id) is not None
        if fail_at == "credit":
            raise _CreditFailure("credit rejected")
        event = original_transition(*args, **kwargs)
        assert event.successor_value == pytest.approx(0.6)
        credited_events.append(event)
        return event

    original_graph_td = graph.apply_intrinsic_td

    def graph_td(*args, **kwargs):
        events.append("graph_td")
        assert authority.native_provider_response(authority.provider_id) is not None
        if fail_at == "graph_td":
            raise _CreditFailure("graph TD rejected")
        return original_graph_td(*args, **kwargs)

    def promotion_request(current_authority, _ecology, candidate_id):
        assert current_authority is authority
        assert candidate_id == "eligible-existing-bud"
        return SimpleNamespace(candidate_id=candidate_id)

    def settle(current_authority, *, promotions=()):
        assert current_authority is authority
        assert events[-1] == "graph_td"
        assert len(promotions) == 1
        assert promotions[0].candidate_id == "eligible-existing-bud"
        events.append("settle")
        authority.live_providers.pop(authority.provider_id)
        authority.boundary_promotion_requests[promotions[0].candidate_id] = promotions[0]
        return {"retired_cell_ids": [authority.provider_id], "child_ids": ["new-bud"]}

    def mark_promoted(_ecology, candidate_id):
        assert candidate_id in authority.boundary_promotion_requests
        events.append("mark_promoted")

    monkeypatch.setattr(curriculum, "_select_r1_training_action", select)
    monkeypatch.setattr(curriculum, "_prospective_counterexample_episode", episode)
    monkeypatch.setattr(curriculum, "_boundary_promotion_request_from_candidate", promotion_request)
    monkeypatch.setattr(curriculum, "_advance_v2_structural_frontier", settle)
    monkeypatch.setattr(ProspectiveBoundaryCandidateEcology, "mark_promoted", mark_promoted)
    monkeypatch.setattr(credit, "transition", transition)
    monkeypatch.setattr(graph, "apply_intrinsic_td", graph_td)
    expected_error = _CreditFailure if fail_at else _NextDecision
    with pytest.raises(expected_error):
        curriculum._run_r1_arm(
            arm.name, graph, credit, None, pools,
            r0_replay_memory=(), r0_child_triplet_ids=frozenset(),
            max_epochs=1, config=config, arm_spec=arm,
            r0_child_authority=authority,
        )
    assert not list(tmp_path.iterdir())
    assert len(nominated_sets) == 1
    return events, authority, credited_events


def test_current_envelope_provider_survives_td_then_retires_before_next_decision(
    tmp_path, monkeypatch,
):
    events, authority, credited = _exercise_event(tmp_path, monkeypatch)
    assert events == [
        "frame_open", "select", "real", "credit", "graph_td", "settle",
        "mark_promoted", "frame_close", "frame_open", "next_decision", "frame_close",
    ]
    assert len(credited) == 1
    assert authority.native_provider_response(authority.provider_id) is None


@pytest.mark.parametrize("fail_at", ("credit", "graph_td"))
def test_failed_current_credit_never_commits_structural_growth(
    tmp_path, monkeypatch, fail_at,
):
    events, authority, _credited = _exercise_event(
        tmp_path, monkeypatch, fail_at=fail_at,
    )
    assert "settle" not in events
    assert "mark_promoted" not in events
    assert "next_decision" not in events
    assert events.count("frame_open") == 1
    assert authority.native_provider_response(authority.provider_id) is not None
    # Only the structural operation is proved absent: this deliberately does
    # not assert rollback of already consumed REAL/ecology or credit state.


def test_duplicate_virtual_handoff_does_not_settle_or_refresh_structure(
    tmp_path, monkeypatch,
):
    events, authority, credited = _exercise_event(
        tmp_path, monkeypatch, duplicate=True,
    )
    assert events == [
        "frame_open", "select", "duplicate_virtual", "credit", "graph_td",
        "next_decision", "frame_close",
    ]
    assert len(credited) == 1
    assert authority.native_provider_response(authority.provider_id) is not None
