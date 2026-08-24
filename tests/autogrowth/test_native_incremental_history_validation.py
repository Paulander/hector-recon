from __future__ import annotations

import copy
from dataclasses import replace
import hashlib
import hmac
import json

import chess
import pytest

from recon_lite import FrameContext, FrameKind
from recon_lite_hector.learning import (
    IntrinsicCreditConfig,
    IntrinsicCreditEngine,
)
from recon_lite_hector.nodes import StemCellState, StemCellTerminal
from recon_lite_chess.autogrowth.native_authority_handover import (
    FrozenCompetenceProvenance,
    NativeR0Organism,
)
from recon_lite_chess.autogrowth.native_competence_envelope import (
    AvailabilityState,
    CompetenceContextCell,
    CompetenceEnvelopeConfig,
    SpecializationMode,
)
from recon_lite_chess.autogrowth.native_intrinsic_curriculum import (
    R0_COMPETENCE_ID,
)
from recon_lite_chess.autogrowth import (
    native_deferred_specialization_fresh_discriminator as science,
    native_deferred_specialization_performance_reclosure as performance,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import (
    HISTORY_VALIDATION_INCREMENTAL,
    HISTORY_VALIDATION_LEGACY,
    NativeProspectiveAuthorityV2,
    ProspectiveV2IntegrityError,
    V2Mode,
)
from recon_lite_chess.autogrowth.native_single_graph_curriculum import (
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
)
from recon_lite_chess.autogrowth.native_trace_competence_authority import (
    TraceNativeCompetenceOrganism,
    TraceNativeLearningConfig,
)


MATE_ONE = "8/8/8/8/8/7K/5R2/7k w - - 0 {fullmove}"


def _canonical(value) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def _resign(authority, receipt):
    return replace(
        receipt,
        signature=hmac.new(
            authority._receipt_secret,
            _canonical(receipt.unsigned_manifest()),
            hashlib.sha256,
        ).hexdigest(),
    )


def _after(board: chess.Board, move: chess.Move) -> chess.Board:
    successor = board.copy(stack=False)
    successor.push(move)
    return successor


def _synthetic_r0() -> NativeR0Organism:
    board = chess.Board(MATE_ONE.format(fullmove=1))
    mate = next(
        move for move in board.legal_moves
        if _after(board, move).is_checkmate()
    )
    graph = NativeReConKRKGraph(config=NativeSingleGraphConfig(
        include_symmetries=False,
        max_ticks=80,
        indexed_scheduler=True,
        key_mode="canonical",
        shared_feature_atoms=True,
        shared_projection_atoms=True,
        include_grouped_cache_terminals=False,
        score_action_pattern_atoms=True,
        terminal_score_normalization="sqrt",
    ))
    graph.apply_intrinsic_td(
        board,
        mate,
        td_error=1.0,
        stage_diagnostic="incremental_history_synthetic_canary",
    )
    graph.mature_existing_graph()
    graph.freeze_existing_parameters(
        reason="incremental_history_synthetic_canary"
    )
    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(min_grounding_evidence=3)
    )
    credit.register(R0_COMPETENCE_ID, mature=True)
    state = credit.states[R0_COMPETENCE_ID]
    state.slow_value = state.fast_value = 0.8
    state.terminal_evidence = 3
    state.causal_confirmations = 1
    state.grounding_level = 0
    return NativeR0Organism(
        graph=graph,
        credit=credit,
        provenance=FrozenCompetenceProvenance.from_credit(
            credit, R0_COMPETENCE_ID
        ),
        frozen_triplet_ids=frozenset(graph.triplet_ids),
        source_manifest={
            "kind": "incremental_history_synthetic_canary",
        },
    )


def _synthetic_authority() -> NativeProspectiveAuthorityV2:
    envelope_config = CompetenceEnvelopeConfig(selection_seed=19073)
    source = TraceNativeCompetenceOrganism.empty(
        _synthetic_r0(),
        envelope_config=envelope_config,
        learning_config=TraceNativeLearningConfig(
            lifecycle_connected=False,
            specialization_mode=SpecializationMode.DISCONNECTED,
            genome_seed=envelope_config.selection_seed,
        ),
    )
    terminal = source.completion_terminal()
    evidence_ids = []
    common_signals: set[str] | None = None
    for index in range(1, 5):
        board = chess.Board(MATE_ONE.format(fullmove=index))
        frame = FrameContext(
            f"incremental-history-discovery:{index}",
            FrameKind.REAL,
            values={"board": board},
        )
        actuation, trace = source.r0.emit_action_with_trace(frame)
        assert actuation is not None and trace is not None
        receipt = terminal.mint(trace, board, _after(board, chess.Move.from_uci(
            actuation.move_uci
        )))
        record, inserted = source._accept_receipt(receipt)
        assert inserted and source.envelope.add_unique_evidence(record)
        evidence_ids.append(receipt.event_id)
        identities = set(trace.ordered_signal_identities)
        common_signals = (
            identities
            if common_signals is None
            else common_signals.intersection(identities)
        )
    assert common_signals is not None
    member = "internal:policy_response"
    assert member in common_signals
    stem = StemCellTerminal("incremental_history_parent")
    stem.state = StemCellState.MATURE
    stem.trial_node_id = "incremental_history_parent"
    stem.trial_parent_id = "competence_available_root"
    cell = CompetenceContextCell(
        cell_id="incremental_history_parent",
        members=(member,),
        born_round=0,
        born_request_ordinal=0,
        stem_cell=stem,
        polarity=AvailabilityState.AVAILABLE,
        evidence_keys=tuple(sorted(evidence_ids)),
        successes=len(evidence_ids),
        support=len(evidence_ids),
        success_lower_bound=0.568,
    )
    source.envelope.cells = {cell.cell_id: cell}
    source.envelope._member_specs = {cell.members}
    source.envelope.rebuild_graph()
    authority = NativeProspectiveAuthorityV2.from_organism(
        source, mode=V2Mode.PROSPECTIVE
    )
    authority.close_nomination()
    return authority


def _open_mint(
    authority: NativeProspectiveAuthorityV2,
    *,
    fullmove: int,
    frame_id: str,
):
    board = chess.Board(MATE_ONE.format(fullmove=fullmove))
    pending, trace = authority.open_real_event(FrameContext(
        frame_id, FrameKind.REAL, values={"board": board}
    ))
    successor = _after(
        board, chess.Move.from_uci(pending.actuation.move_uci)
    )
    receipt = authority.mint_environment_receipt(
        pending_token=pending.pending_token,
        trace=trace,
        predecessor=board,
        successor=successor,
    )
    return pending, trace, receipt


def _accept(
    authority: NativeProspectiveAuthorityV2,
    *,
    fullmove: int,
    frame_id: str,
):
    pending, trace, receipt = _open_mint(
        authority, fullmove=fullmove, frame_id=frame_id
    )
    return pending, trace, receipt, authority.consume(receipt)


def test_incremental_and_complete_replay_are_exact_after_every_event() -> None:
    initial = _synthetic_authority()
    incremental = copy.deepcopy(initial)
    complete_replay = copy.deepcopy(initial)
    incremental.set_history_validation_mode_for_development(
        HISTORY_VALIDATION_INCREMENTAL
    )
    complete_replay.set_history_validation_mode_for_development(
        HISTORY_VALIDATION_LEGACY
    )

    for position, fullmove in enumerate(range(20, 32)):
        frame_id = f"incremental-history-parity:{position}"
        incremental_open = _open_mint(
            incremental, fullmove=fullmove, frame_id=frame_id
        )
        replay_open = _open_mint(
            complete_replay, fullmove=fullmove, frame_id=frame_id
        )
        assert incremental_open == replay_open
        incremental_emission = incremental.consume(incremental_open[2])
        replay_emission = complete_replay.consume(replay_open[2])
        assert incremental_emission == replay_emission
        assert incremental.continuation_manifest() == (
            complete_replay.continuation_manifest()
        )
        incremental.verify_full_history_boundary(
            f"differential event {position}"
        )


def test_duplicate_order_physical_identity_and_disagreement_fail_closed() -> None:
    authority = _synthetic_authority()
    _pending, _trace, receipt, emission = _accept(
        authority, fullmove=40, frame_id="incremental-history:first"
    )
    history = authority.incremental_history_state
    assert history is not None
    assert authority.consume(receipt) == emission
    assert authority.incremental_history_state == history

    for label, ordinal_delta in (("reordered", 1), ("skipped", 3)):
        ordered = copy.deepcopy(authority)
        _pending, _trace, next_receipt = _open_mint(
            ordered,
            fullmove=41,
            frame_id=f"incremental-history:{label}",
        )
        out_of_order = _resign(
            ordered,
            replace(
                next_receipt,
                ordinal=next_receipt.ordinal + ordinal_delta,
            ),
        )
        before = ordered.continuation_digest()
        with pytest.raises(
            ProspectiveV2IntegrityError,
            match="out-of-order ordinal or ordinal gap",
        ):
            ordered.consume(out_of_order)
        assert ordered.continuation_digest() == before

    repeated = copy.deepcopy(authority)
    _pending, _trace, replay_receipt = _open_mint(
        repeated, fullmove=40, frame_id="incremental-history:remint"
    )
    before = repeated.continuation_digest()
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="reminted physical interaction",
    ):
        repeated.consume(replay_receipt)
    assert repeated.continuation_digest() == before

    bad_chain = copy.deepcopy(authority)
    assert bad_chain.incremental_history_state is not None
    bad_chain.incremental_history_state = replace(
        bad_chain.incremental_history_state,
        history_digest="0" * 64,
    )
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match=(
            "full history boundary injected chain failed: incremental history "
            "disagreement with complete reconstruction"
        ),
    ):
        bad_chain.verify_full_history_boundary("injected chain")

    bad_predecessor = copy.deepcopy(authority)
    bad_predecessor.event_transactions[receipt.pending_token][
        "predecessor_continuation_digest"
    ] = "0" * 64
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="incremental history predecessor disagreement at ordinal",
    ):
        bad_predecessor.verify_full_history_boundary(
            "injected predecessor"
        )


def test_midpoint_restoration_and_continued_learning_are_exact() -> None:
    uninterrupted = _synthetic_authority()
    restored_path = copy.deepcopy(uninterrupted)
    for position, fullmove in enumerate(range(60, 66)):
        frame_id = f"incremental-history-midpoint:{position}"
        _accept(
            uninterrupted, fullmove=fullmove, frame_id=frame_id
        )
        _accept(
            restored_path, fullmove=fullmove, frame_id=frame_id
        )

    restored_path = NativeProspectiveAuthorityV2.loads(
        restored_path.dumps()
    )
    assert restored_path.continuation_manifest() == (
        uninterrupted.continuation_manifest()
    )
    for position, fullmove in enumerate(range(66, 72), start=6):
        frame_id = f"incremental-history-midpoint:{position}"
        uninterrupted_row = _accept(
            uninterrupted, fullmove=fullmove, frame_id=frame_id
        )
        restored_row = _accept(
            restored_path, fullmove=fullmove, frame_id=frame_id
        )
        assert uninterrupted_row == restored_row
        assert restored_path.continuation_manifest() == (
            uninterrupted.continuation_manifest()
        )


def test_cached_runner_open_is_exact_with_incremental_predecessor() -> None:
    live = _synthetic_authority()
    cached = copy.deepcopy(live)
    row = science.StreamRow(
        region="synthetic_development_canary",
        region_ordinal=0,
        global_ordinal=0,
        row_id="incremental-history-cached-row",
        predecessor_fen=MATE_ONE.format(fullmove=90),
        d4_orbit_key="synthetic-development-canary",
        planned_physical_interaction_id="synthetic-development-canary",
    )
    record = performance.build_observation_cache(
        live.base,
        (row,),
        frame_namespace="incremental-history-cache",
    )[0]
    source_r0_digest, source_continuation_digest = (
        performance._source_bindings(live.base)
    )
    board = chess.Board(row.predecessor_fen)
    live_pending, live_trace = live.open_real_event(FrameContext(
        record.frame_id,
        FrameKind.REAL,
        values={"board": board},
    ))
    cached_pending, cached_trace = performance.open_cached_real_event(
        cached,
        row,
        record,
        source_r0_digest=source_r0_digest,
        source_continuation_digest=source_continuation_digest,
    )
    assert cached_trace == live_trace
    assert cached_pending == live_pending
    assert cached.continuation_manifest() == live.continuation_manifest()

    successor = _after(
        board, chess.Move.from_uci(live_pending.actuation.move_uci)
    )
    live_receipt = live.mint_environment_receipt(
        pending_token=live_pending.pending_token,
        trace=live_trace,
        predecessor=board,
        successor=successor,
    )
    cached_receipt = cached.mint_environment_receipt(
        pending_token=cached_pending.pending_token,
        trace=cached_trace,
        predecessor=board,
        successor=successor,
    )
    assert cached_receipt == live_receipt
    assert cached.consume(cached_receipt) == live.consume(live_receipt)
    assert cached.continuation_manifest() == live.continuation_manifest()
