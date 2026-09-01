from __future__ import annotations

from types import SimpleNamespace

import chess
from recon_lite import FrameKind
from recon_lite_hector.learning import IntrinsicCreditConfig, IntrinsicCreditEngine

from recon_lite_chess.autogrowth import native_intrinsic_v2_development as intrinsic
from recon_lite_chess.autogrowth.native_intrinsic_curriculum import (
    NativeIntrinsicCurriculumConfig,
    R0_COMPETENCE_ID,
    V2_PROSPECTIVE_AVAILABILITY,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import (
    StructuralMode,
)
from recon_lite_chess.autogrowth.native_single_graph_curriculum import (
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
)


def _source_rows(count: int) -> tuple[str, ...]:
    board = chess.Board("7k/8/8/8/8/8/1K6/7R w - - 0 1")
    rows = []
    for fullmove in range(1, count + 1):
        board.fullmove_number = fullmove
        rows.append(board.fen())
    return tuple(rows)


def test_certification_tape_is_exact_disjoint_content_partition() -> None:
    source = _source_rows(64)
    discovery = intrinsic._neutral_discovery_tape(tuple(reversed(source)))
    certification = intrinsic._neutral_certification_tape(
        source,
        discovery,
    )

    assert len(discovery) == 32
    assert len(certification) == 32
    assert len(set(discovery)) == len(discovery)
    assert len(set(certification)) == len(certification)
    assert set(discovery).isdisjoint(certification)
    assert set(discovery).union(certification) == set(source)
    assert all(fen == chess.Board(fen).fen() for fen in certification)


def test_certification_tape_is_partition_and_order_invariant() -> None:
    source = _source_rows(64)
    discovery = intrinsic._neutral_discovery_tape(source)

    forward = intrinsic._neutral_certification_tape(source, discovery)
    reversed_source = intrinsic._neutral_certification_tape(
        tuple(reversed(source)),
        tuple(reversed(discovery)),
    )

    assert forward == reversed_source


def test_certification_tape_selects_up_to_32_remaining_rows() -> None:
    source = _source_rows(40)
    discovery = intrinsic._neutral_discovery_tape(source)
    certification = intrinsic._neutral_certification_tape(source, discovery)

    assert len(discovery) == 32
    assert len(certification) == 8
    assert set(certification).isdisjoint(discovery)


def test_event_driven_contradiction_settles_before_next_real_admission() -> None:
    class _FrameSession:
        def close(self) -> None:
            return None

    class _Authority:
        structural_mode = StructuralMode.EVENT_DRIVEN

        def __init__(self) -> None:
            self.events: list[str] = []
            self.pending_request = False
            self.materialized_requests = 0
            self.ordinal = 0

        def frame_session(self):
            return _FrameSession()

        def open_real_event(self, frame, *, frame_session):
            assert frame.kind is FrameKind.REAL
            assert not self.pending_request
            self.events.append(f"open:{frame.frame_id}")
            pending = SimpleNamespace(pending_token=f"token:{self.ordinal}")
            trace = SimpleNamespace(
                actuation=SimpleNamespace(move_uci="h1h2")
            )
            return pending, trace

        def mint_environment_receipt(
            self, *, pending_token, trace, predecessor, successor
        ):
            self.events.append(f"mint:{pending_token}")
            return SimpleNamespace(receipt_id=pending_token)

        def consume(self, receipt, *, frame_session):
            self.events.append(f"consume:{receipt.receipt_id}")
            # Simulate a contradiction-driven structural request.  The
            # authority safe point must materialize/refine it before another
            # REAL frame is admitted.
            self.pending_request = True
            self.ordinal += 1
            return SimpleNamespace()

        def settle_pending_structural_requests(self):
            assert self.pending_request
            self.events.append("settle-and-materialize")
            self.pending_request = False
            self.materialized_requests += 1

    authority = _Authority()
    fens = _source_rows(2)
    receipts, emissions = intrinsic._certify_real_rows(authority, fens)

    assert len(receipts) == len(emissions) == 2
    assert authority.materialized_requests == 2
    assert authority.events == [
        "open:native-intrinsic-v2-certification:0000",
        "mint:token:0",
        "consume:token:0",
        "settle-and-materialize",
        "open:native-intrinsic-v2-certification:0001",
        "mint:token:1",
        "consume:token:1",
        "settle-and-materialize",
    ]


def test_empty_event_driven_factory_reads_no_pool_and_seeds_no_authority() -> None:
    graph = NativeReConKRKGraph(
        config=NativeSingleGraphConfig(include_symmetries=False)
    )
    board = chess.Board("k7/8/1K6/8/8/8/8/7R w - - 0 1")
    graph.ensure_triplet(
        board,
        min(board.legal_moves, key=lambda item: item.uci()),
        stage="empty_authority_test_r0",
    )
    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(min_grounding_evidence=1)
    )
    credit.register(R0_COMPETENCE_ID, mature=True)
    state = credit.states[R0_COMPETENCE_ID]
    state.fast_value = state.slow_value = 0.75
    state.terminal_evidence = 1
    state.causal_confirmations = 1
    state.grounding_level = 0

    class ForbiddenPools:
        def __getattribute__(self, name):
            raise AssertionError(f"empty boundary factory read pool field {name}")

    graph_before = graph.canonical_semantic_manifest()
    credit_before = credit.snapshot()
    authority, audit = intrinsic.build_empty_event_driven_v2_r0_authority(
        graph,
        credit,
        ForbiddenPools(),
        NativeIntrinsicCurriculumConfig(
            run_r1=True,
            r0_availability_mode=V2_PROSPECTIVE_AVAILABILITY,
            r0_boundary_ecology_enabled=True,
        ),
    )

    assert authority.structural_mode is StructuralMode.EVENT_DRIVEN
    assert authority.structural_epoch_schedule == ()
    assert authority.states == {}
    assert authority.accepted_real_references == {}
    assert authority.boundary_promotion_requests == {}
    assert authority._pending_request_ids() == ()
    assert authority.base.receipts == {}
    assert authority.base.envelope.cells == {}
    assert audit["boundary_initialization"] == (
        "empty_event_driven_positive_shell"
    )
    assert audit["pool_rows_read_for_boundary_initialization"] == 0
    assert audit["negative_authority_roots_initialized"] == 0
    assert audit["serialization_roundtrip_exact"] is True
    assert graph.canonical_semantic_manifest() == graph_before
    assert credit.snapshot() == credit_before
