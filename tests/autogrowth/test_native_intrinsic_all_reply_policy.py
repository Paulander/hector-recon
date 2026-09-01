from __future__ import annotations

from types import SimpleNamespace

import chess
import pytest

from recon_lite_chess.autogrowth.foundation_curriculum import (
    _forced_mate_in_two_first_moves,
)
from recon_lite_chess.autogrowth.native_intrinsic_curriculum import (
    R0_COMPETENCE_ID,
    R1_RETIRED_DEVELOPMENT_FENS,
    R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE,
    R1_REPLY_POLICY_SAMPLED_ROUND_ROBIN,
    NativeIntrinsicCurriculumConfig,
    _effective_r1_reply_policy,
    _grounded_all_reply_successor_signal,
    _prospective_counterexample_episode,
    _prospective_counterexample_reply_probe,
    _r1_reply_counter_defaults,
    _r1_reply_authority_from_classification,
    _r1_reply_authority_from_local_provider,
    _r1_terminal_reply_terminal_kind,
)
from recon_lite_chess.autogrowth.native_all_reply_envelope import (
    AvailabilityState,
    ReplyAuthority,
    evaluate_all_reply_envelope,
)
from recon_lite_hector.learning import (
    IntrinsicCreditConfig,
    IntrinsicCreditEngine,
    Responsibility,
)


class _Authority:
    """Small V2-shaped test double; no learner labels enter the policy."""

    def __init__(self, *, state: str = "AVAILABLE", false_ids: tuple[str, ...] = ()):
        self.state = state
        self.false_ids = false_ids
        self.next_expected_ordinal = 0
        self.pending_event = None
        self.base = SimpleNamespace(
            receipts={},
            r0=SimpleNamespace(
                provenance=SimpleNamespace(
                    grounded=True,
                    mature=True,
                    can_emit=True,
                    consolidated_value=0.73,
                    grounding_source="test_grounded_real_history",
                )
            ),
        )
        self.consumed_receipts = {}
        self.accepted_real_references = {}
        self.structural_epoch_schedule = ()
        self.current_generation = 0
        self.generation_phase = SimpleNamespace(value="prospective")
        self.states = {}
        self.deferred_requests = {}
        self.deferred_child_births = {}

    def _move(self, board: chess.Board) -> chess.Move:
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            after = board.copy(stack=False)
            after.push(move)
            if after.is_checkmate():
                return move
        return min(board.legal_moves, key=lambda item: item.uci())

    def _classification(self) -> SimpleNamespace:
        probability = {
            "AVAILABLE": 1.0,
            "UNKNOWN": 0.5,
            "REFUTED": 0.0,
        }[self.state]
        return SimpleNamespace(
            state=self.state,
            to_manifest=lambda: {
                "state": self.state,
                "probability": probability,
                "uncertainty": 0.0 if self.state == "AVAILABLE" else 1.0,
                "available_cell_ids": [],
                "refuted_cell_ids": [],
                "formal_available": self.state == "AVAILABLE",
                "formal_refuted": self.state == "REFUTED",
                "policy_response": True,
            },
        )

    def open_virtual(self, frame, **_kwargs):
        move = self._move(frame.values["board"])
        return {
            "query": SimpleNamespace(
                actuation=SimpleNamespace(
                    move_uci=move.uci(), option_identity="test-r0"
                ),
                response=SimpleNamespace(
                    available=self.state == "AVAILABLE",
                    grounded=True,
                    grounding_source="test_grounded_real_history",
                ),
                availability_provenance={
                    "authority": "NativeProspectiveAuthorityV2_graph_emission",
                    "certification_evidence_added": 0,
                },
            ),
            "classification": self._classification(),
        }

    def open_real_event(self, frame, **_kwargs):
        move = self._move(frame.values["board"])
        pending = SimpleNamespace(
            pending_token=f"pending:{self.next_expected_ordinal}",
            pre_outcome_classification=self._classification(),
        )
        self.pending_event = pending
        return pending, SimpleNamespace(
            actuation=SimpleNamespace(
                move_uci=move.uci(), option_identity="test-r0"
            )
        )

    def mint_environment_receipt(self, *, predecessor, **_kwargs):
        return SimpleNamespace(
            event_id=f"event:{self.next_expected_ordinal}",
            predecessor_fen=predecessor.fen(),
        )

    def consume(self, receipt, **_kwargs):
        self.consumed_receipts[receipt.event_id] = receipt
        self.accepted_real_references[receipt.event_id] = SimpleNamespace(
            receipt_id=receipt.event_id,
            stable_physical_interaction_id=f"physical:{receipt.event_id}",
        )
        self.next_expected_ordinal += 1
        self.pending_event = None
        return SimpleNamespace(
            manifest=lambda: {
                "prequential_false_authority_ids": list(self.false_ids)
            }
        )

    def continuation_digest(self) -> str:
        return str(self.next_expected_ordinal)


class _PerSuccessorAuthority(_Authority):
    """Test-only V2-shaped authority with scripted values per successor FEN.

    The mapping isolates envelope selection and credit plumbing.  Its formal
    AVAILABLE rows are not claims about chess competence and never enter a
    learner or development experiment.
    """

    def __init__(self, classification_by_successor_fen: dict[str, float]):
        super().__init__(state="AVAILABLE")
        self.classification_by_successor_fen = dict(
            classification_by_successor_fen
        )

    def _classification_for_board(self, board: chess.Board) -> SimpleNamespace:
        value = self.classification_by_successor_fen[board.fen()]
        return SimpleNamespace(
            state=AvailabilityState.AVAILABLE.value,
            to_manifest=lambda: {
                "state": AvailabilityState.AVAILABLE.value,
                "probability": value,
                "uncertainty": 1.0 - value,
                "available_cell_ids": [],
                "refuted_cell_ids": [],
                "formal_available": True,
                "formal_refuted": False,
                "policy_response": True,
            },
        )

    def open_virtual(self, frame, **_kwargs):
        move = self._move(frame.values["board"])
        return {
            "query": SimpleNamespace(
                actuation=SimpleNamespace(
                    move_uci=move.uci(), option_identity="test-r0"
                ),
                response=SimpleNamespace(
                    available=True,
                    grounded=True,
                    grounding_source="test_grounded_real_history",
                ),
                availability_provenance={
                    "authority": "NativeProspectiveAuthorityV2_graph_emission",
                    "certification_evidence_added": 0,
                },
            ),
            "classification": self._classification_for_board(
                frame.values["board"]
            ),
        }

    def open_real_event(self, frame, **_kwargs):
        board = frame.values["board"]
        move = self._move(board)
        pending = SimpleNamespace(
            pending_token=f"pending:{self.next_expected_ordinal}",
            pre_outcome_classification=self._classification_for_board(board),
        )
        self.pending_event = pending
        return pending, SimpleNamespace(
            actuation=SimpleNamespace(
                move_uci=move.uci(), option_identity="test-r0"
            )
        )


class _LocalProviderAuthority(_Authority):
    """UNKNOWN shell around one exact, locally grounded native provider."""

    def __init__(self):
        super().__init__(state="UNKNOWN")
        credit = IntrinsicCreditEngine(
            IntrinsicCreditConfig(min_grounding_evidence=1)
        )
        credit.register("test-r0")
        credit.begin_episode()
        credit.transition("test-r0", terminal_kind="mate")
        audit = credit.consolidate_direct_outcome_providers(("test-r0",))
        assert audit["provider_ids"] == ["test-r0"]
        self.credit = credit
        self.base.r0.credit = credit
        self.base.r0.direct_provider_ids = frozenset(("test-r0",))
        self.base.r0.provenance = SimpleNamespace(
            grounded=False,
            mature=False,
            can_emit=False,
            consolidated_value=0.0,
            grounding_source="unused_global_test_provenance",
        )

    def open_virtual(self, frame, **_kwargs):
        opened = super().open_virtual(frame, **_kwargs)
        provider = self.credit.direct_outcome_provider_response("test-r0")
        assert provider is not None
        opened["query"].response = SimpleNamespace(
            available=True,
            grounded=True,
            grounding_source=provider["grounding_source"],
        )
        opened["query"].availability_provenance[
            "base_availability_provenance"
        ] = {"local_provider": provider}
        return opened


class _CoreGraph:
    """Small graph-shaped frozen-core double for envelope routing tests."""

    triplet_ids = frozenset(("core:test",))

    @staticmethod
    def _move(board: chess.Board) -> chess.Move:
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            after = board.copy(stack=False)
            after.push(move)
            if after.is_checkmate():
                return move
        return min(board.legal_moves, key=lambda item: item.uci())

    def audit_choice(self, board, masked_triplets=None):
        del masked_triplets
        move = self._move(board)
        return {
            "selected_move": move.uci(),
            "selected_triplet": "core:test",
            "selected_score": 0.8,
            "confirmed_candidate_count": 1,
            "candidate_triplet_count": 1,
            "confirmed_candidates": [
                {"move": move.uci(), "triplet_id": "core:test", "score": 0.8}
            ],
        }


class _CoreGate:
    mature = True

    def __init__(self, confirms: bool, probability: float = 0.81):
        self._confirms = bool(confirms)
        self._probability = float(probability)

    def confirms(self, _features):
        return self._confirms

    def probability(self, _features):
        return self._probability


def _fixture(*, state: str = "AVAILABLE", false_ids: tuple[str, ...] = ()):
    fen = R1_RETIRED_DEVELOPMENT_FENS[0]
    board = chess.Board(fen)
    first = _forced_mate_in_two_first_moves(board)[0]
    after_first = board.copy(stack=False)
    after_first.push(first)
    counters = {
        **_r1_reply_counter_defaults(),
        "availability_queries": 0,
        "availability_positives": 0,
        "virtual_frame_queries": 0,
        "v2_duplicate_virtual_queries": 0,
        "v2_real_observations": 0,
        "v2_structural_transitions": 0,
        "child_handoffs": 0,
    }
    return (
        _Authority(state=state, false_ids=false_ids),
        fen,
        first,
        after_first,
        counters,
    )


def _episode(
    authority,
    fen,
    first,
    after_first,
    counters,
    exposures=None,
    seen=None,
    core_graph=None,
    core_gate=None,
    credit=None,
):
    return _prospective_counterexample_episode(
        authority,
        after_first,
        credit=credit,
        fen=fen,
        white_move_uci=first.uci(),
        arm_name="test",
        epoch=0,
        position_index=0,
        exposure_counts={} if exposures is None else exposures,
        seen_predecessor_fens=set() if seen is None else seen,
        frame_session=None,
        generic_seed=17,
        arm_bootstrap_enabled=True,
        counters=counters,
        r0_core_graph=core_graph,
        r0_core_gate=core_gate,
        r0_core_triplet_ids=(
            None if core_graph is None else frozenset(core_graph.triplet_ids)
        ),
    )


def test_unknown_shell_cannot_veto_exact_local_all_reply_providers() -> None:
    authority = _LocalProviderAuthority()
    fen = R1_RETIRED_DEVELOPMENT_FENS[0]
    board = chess.Board(fen)
    first = _forced_mate_in_two_first_moves(board)[0]
    after_first = board.copy(stack=False)
    after_first.push(first)
    counters = {
        **_r1_reply_counter_defaults(),
        "availability_queries": 0,
        "availability_positives": 0,
        "virtual_frame_queries": 0,
        "v2_duplicate_virtual_queries": 0,
        "v2_real_observations": 0,
        "v2_structural_transitions": 0,
        "child_handoffs": 0,
    }

    probe = _prospective_counterexample_reply_probe(
        authority,
        after_first,
        fen=fen,
        white_move_uci=first.uci(),
        exposure_counts={},
        frame_prefix="test:local-provider-probe",
        frame_session=None,
        generic_seed=17,
    )
    assert probe["envelope"].state is AvailabilityState.AVAILABLE
    assert probe["provider_ids"] == ("test-r0",)
    assert all(
        row["classification"]["state"] == "UNKNOWN"
        for row in probe["contexts"]
    )

    terminal_kind, successor_ids, episode = _episode(
        authority,
        fen,
        first,
        after_first,
        counters,
        credit=authority.credit,
    )
    assert terminal_kind is None
    assert successor_ids == ("test-r0",)
    assert episode["successor_signal"].provider_ids == ("test-r0",)
    assert episode["successor_signal"].value > 0.0


@pytest.mark.parametrize(
    "override",
    (
        {"expected_value": float("nan")},
        {"confidence": float("inf")},
        {"uncertainty": -0.1},
        {"direct_positive_evidence": 0},
        {"direct_contrast_evidence": 1},
    ),
)
def test_malformed_local_provider_abstains(override) -> None:
    provider = {
        "cell_id": "local:test",
        "expected_value": 0.8,
        "confidence": 0.75,
        "uncertainty": 0.25,
        "direct_positive_evidence": 3,
        "direct_contrast_evidence": 0,
    }
    provider.update(override)
    row = _r1_reply_authority_from_local_provider(
        "reply:test",
        provider,
        exposure_count=0,
    )
    assert row.state is AvailabilityState.UNKNOWN
    assert row.grounded is False
    assert row.value == 0.0


def test_new_reply_policy_is_gated_by_authority_and_defaults_to_legacy() -> None:
    config = NativeIntrinsicCurriculumConfig()
    assert config.r1_reply_policy == R1_REPLY_POLICY_SAMPLED_ROUND_ROBIN
    assert _effective_r1_reply_policy(config, None) == R1_REPLY_POLICY_SAMPLED_ROUND_ROBIN
    opt_in = NativeIntrinsicCurriculumConfig(
        r1_reply_policy=R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE
    )
    assert _effective_r1_reply_policy(opt_in, None) == R1_REPLY_POLICY_SAMPLED_ROUND_ROBIN
    assert _effective_r1_reply_policy(opt_in, object()) == R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE


def test_virtual_probe_does_not_advance_played_reply_exposures() -> None:
    authority, fen, first, after_first, _counters = _fixture()
    exposures = {}
    probe = _prospective_counterexample_reply_probe(
        authority,
        after_first,
        fen=fen,
        white_move_uci=first.uci(),
        exposure_counts=exposures,
        frame_prefix="test:probe",
        frame_session=None,
        generic_seed=17,
    )
    assert probe["virtual_query_count"] > 0
    assert exposures == {}


def test_child_mate_is_handoff_not_second_r1_terminal_and_exposure_is_selected_only() -> None:
    authority, fen, first, after_first, counters = _fixture()
    exposures = {}
    terminal_kind, successor_ids, audit = _episode(
        authority, fen, first, after_first, counters, exposures
    )
    assert terminal_kind is None
    assert successor_ids == (R0_COMPETENCE_ID,)
    assert len(exposures) == 1
    assert tuple(exposures.values()) == (1,)
    assert counters["reply_counterexample_mate_count"] == 1
    assert audit["successor_signal"].value == 1.0
    assert audit["manifest"]["effective_source"] == "v2_grounded_descendant"
    assert audit["manifest"]["successor_signal"]["aggregation"] == (
        "minimum_over_all_grounded_available_replies"
    )


def test_frozen_core_all_reply_rows_feed_grounded_min_td_value() -> None:
    authority, fen, first, after_first, counters = _fixture()
    terminal_kind, successor_ids, audit = _episode(
        authority,
        fen,
        first,
        after_first,
        counters,
        core_graph=_CoreGraph(),
        core_gate=_CoreGate(True),
    )

    assert terminal_kind is None
    assert successor_ids == (R0_COMPETENCE_ID,)
    signal = audit["successor_signal"]
    assert signal is not None
    # Value is the explicit child provenance value; gate probability is only
    # the per-reply confidence used by the exact all-reply minimum.
    assert signal.value == 0.73
    assert signal.confidence == 0.81
    assert audit["manifest"]["effective_core_available"] is True
    assert audit["manifest"]["core_overrode_v2_false_authority"] is False


def test_core_abstention_delegates_to_grounded_v2_descendant() -> None:
    authority, fen, first, after_first, counters = _fixture()
    terminal_kind, successor_ids, audit = _episode(
        authority,
        fen,
        first,
        after_first,
        counters,
        core_graph=_CoreGraph(),
        core_gate=_CoreGate(False),
    )

    assert terminal_kind is None
    assert successor_ids == (R0_COMPETENCE_ID,)
    assert audit["successor_signal"] is not None
    assert audit["manifest"]["effective_core_available"] is False
    assert audit["manifest"]["effective_reply_available"] is True


def test_core_abstention_and_unknown_v2_produce_no_successor_value() -> None:
    authority, fen, first, after_first, counters = _fixture(state="UNKNOWN")
    terminal_kind, successor_ids, audit = _episode(
        authority,
        fen,
        first,
        after_first,
        counters,
        core_graph=_CoreGraph(),
        core_gate=_CoreGate(False),
    )

    assert terminal_kind is None
    assert successor_ids == ()
    assert audit["successor_signal"] is None
    assert audit["manifest"]["envelope"]["state"] == "unknown"


def test_grounded_core_handoff_is_not_vetoed_by_raw_v2_false_ids() -> None:
    authority, fen, first, after_first, counters = _fixture(
        false_ids=("descendant:contradiction",)
    )
    terminal_kind, successor_ids, audit = _episode(
        authority,
        fen,
        first,
        after_first,
        counters,
        core_graph=_CoreGraph(),
        core_gate=_CoreGate(True),
    )

    assert terminal_kind is None
    assert successor_ids == (R0_COMPETENCE_ID,)
    assert audit["successor_signal"] is not None
    assert audit["manifest"]["core_overrode_v2_false_authority"] is True


def test_core_v2_action_parity_is_required_for_grounded_handoff() -> None:
    class _MismatchingCoreGraph(_CoreGraph):
        @staticmethod
        def _move(board: chess.Board) -> chess.Move:
            legal = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
            # The fixture's authority chooses a mate when one exists.  Choose
            # a different legal action to exercise the fail-closed parity
            # boundary without supplying any move label to the learner.
            for move in legal:
                after = board.copy(stack=False)
                after.push(move)
                if not after.is_checkmate():
                    return move
            return legal[-1]

    authority, fen, first, after_first, counters = _fixture()
    with pytest.raises(RuntimeError, match="core action differs"):
        _episode(
            authority,
            fen,
            first,
            after_first,
            counters,
            core_graph=_MismatchingCoreGraph(),
            core_gate=_CoreGate(True),
        )


def test_false_authority_suppresses_same_event_handoff() -> None:
    authority, fen, first, after_first, counters = _fixture(false_ids=("cell:x",))
    terminal_kind, successor_ids, audit = _episode(
        authority, fen, first, after_first, counters
    )
    assert terminal_kind is None
    assert successor_ids == ()
    assert audit["successor_signal"] is None
    assert audit["manifest"]["prequential_false_authority_ids"] == ["cell:x"]
    assert counters["reply_counterexample_false_authority_count"] == 1


def test_later_duplicate_certified_virtual_can_handoff() -> None:
    authority, fen, first, after_first, counters = _fixture()
    initial = _prospective_counterexample_reply_probe(
        authority,
        after_first,
        fen=fen,
        white_move_uci=first.uci(),
        exposure_counts={},
        frame_prefix="test:target",
        frame_session=None,
        generic_seed=17,
    )
    target = initial["selected"]["exposure_key"]
    exposures = {
        context["exposure_key"]: (0 if context["exposure_key"] == target else 10)
        for context in initial["contexts"]
    }
    seen = set()
    first_result = _episode(
        authority, fen, first, after_first, counters, exposures, seen
    )
    assert first_result[1] == (R0_COMPETENCE_ID,)
    assert len(authority.consumed_receipts) == 1
    duplicate_result = _episode(
        authority, fen, first, after_first, counters, exposures, seen
    )
    assert duplicate_result[0] is None
    assert duplicate_result[1] == (R0_COMPETENCE_ID,)
    assert duplicate_result[2]["successor_signal"] is not None
    assert duplicate_result[2]["manifest"]["successor_signal"]["evidence"] == (
        "reused_prior_real_evidence"
    )
    assert counters["reply_counterexample_duplicate_virtual_count"] == 1
    assert len(authority.consumed_receipts) == 1


def test_terminal_black_reply_credit_mapping_is_fail_closed() -> None:
    assert _r1_terminal_reply_terminal_kind("stalemate") == "horizon"
    assert _r1_terminal_reply_terminal_kind("rook_loss") == "rook_loss"
    assert _r1_terminal_reply_terminal_kind("mate") == "failure"


def test_terminal_selected_reply_produces_complete_fail_closed_manifest() -> None:
    # This first move exposes a legal black rook capture.  The all-reply
    # selector therefore chooses a terminal REFUTED row before the REAL branch
    # runs; effective-routing fields must still be initialized and reported.
    authority = _Authority(state="UNKNOWN")
    fen = R1_RETIRED_DEVELOPMENT_FENS[1]
    board = chess.Board(fen)
    first = chess.Move.from_uci("a8a2")
    after_first = board.copy(stack=False)
    after_first.push(first)
    counters = {
        **_r1_reply_counter_defaults(),
        "availability_queries": 0,
        "availability_positives": 0,
        "virtual_frame_queries": 0,
        "v2_duplicate_virtual_queries": 0,
        "v2_real_observations": 0,
        "v2_structural_transitions": 0,
        "child_handoffs": 0,
    }

    terminal_kind, successor_ids, audit = _episode(
        authority,
        fen,
        first,
        after_first,
        counters,
    )

    assert terminal_kind == "rook_loss"
    assert successor_ids == ()
    assert audit["manifest"]["effective_source"] == "terminal_refuted"
    assert audit["manifest"]["effective_core_available"] is False
    assert audit["manifest"]["effective_reply_available"] is False
    selected_context = next(
        row
        for row in audit["manifest"]["reply_context"]
        if row["reply_id"] == audit["manifest"]["selected_reply_id"]
    )
    assert selected_context["effective_source"] == "terminal_refuted"


@pytest.mark.parametrize(
    ("raw_grounded", "expected_grounded"),
    (
        (True, True),
        (False, False),
        (None, False),
        ("false", False),
        (0, False),
        (1, False),
    ),
)
def test_reply_authority_grounding_accepts_only_exact_bool(
    raw_grounded, expected_grounded
) -> None:
    row = _r1_reply_authority_from_classification(
        "reply:grounding",
        {
            "state": AvailabilityState.AVAILABLE.value,
            "probability": 1.0,
            "uncertainty": 0.0,
        },
        exposure_count=0,
        grounded=raw_grounded,
    )

    assert row.grounded is expected_grounded


def test_numeric_handoff_uses_exact_minimum_and_never_partial_unknown() -> None:
    available = evaluate_all_reply_envelope(
        (
            ReplyAuthority(
                "reply:a", AvailabilityState.AVAILABLE, 0.91, 0.72,
                grounded=True,
            ),
            ReplyAuthority(
                "reply:b", AvailabilityState.AVAILABLE, 0.83, 0.31,
                grounded=True,
            ),
        ),
        envelope_id="test:minimum",
    )
    signal = _grounded_all_reply_successor_signal(
        available,
        bootstrap_enabled=True,
        actual_mate=True,
        clean_preoutcome_evidence=True,
    )
    assert signal is not None
    assert signal.value == 0.31
    assert signal.confidence == 0.83
    assert signal.provider_ids == (R0_COMPETENCE_ID,)
    for disabled in (
        {"bootstrap_enabled": False, "actual_mate": True,
         "clean_preoutcome_evidence": True},
        {"bootstrap_enabled": True, "actual_mate": False,
         "clean_preoutcome_evidence": True},
        {"bootstrap_enabled": True, "actual_mate": True,
         "clean_preoutcome_evidence": False},
    ):
        assert _grounded_all_reply_successor_signal(
            available, **disabled
        ) is None

    unknown = evaluate_all_reply_envelope(
        (
            ReplyAuthority(
                "reply:a", AvailabilityState.AVAILABLE, 0.91, 0.72,
                grounded=True,
            ),
            ReplyAuthority(
                "reply:b", AvailabilityState.UNKNOWN, 0.5, 0.0,
                grounded=True,
            ),
        ),
        envelope_id="test:unknown",
    )
    assert unknown.partial_value == 0.72
    assert unknown.value == 0.0
    assert _grounded_all_reply_successor_signal(
        unknown,
        bootstrap_enabled=True,
        actual_mate=True,
        clean_preoutcome_evidence=True,
    ) is None


def test_all_reply_minimum_value_reaches_real_td_credit() -> None:
    # A code-defined synthetic position with five legal black replies.  The
    # lowest positive authority value is assigned to d7e8; that successor has
    # the local Qe7 mate selected by the test authority, so the policy can
    # exercise the complete virtual-probe -> one REAL event -> TD path.  The
    # extra white rook keeps the chess curriculum's native non-rook-loss
    # terminal convention intact.  The per-reply AVAILABLE values below are a
    # deliberately scripted plumbing fixture, not learned chess assertions.
    fen = "8/3k4/8/6K1/8/Q7/R7/8 w - - 0 1"
    board = chess.Board(fen)
    first = chess.Move.from_uci("g5f6")
    after_first = board.copy(stack=False)
    after_first.push(first)
    reply_values = {
        "d7c6": 0.72,
        "d7c7": 0.64,
        "d7c8": 0.83,
        "d7d8": 0.91,
        "d7e8": 0.31,
    }
    classification_by_successor_fen = {}
    for reply in sorted(after_first.legal_moves, key=lambda item: item.uci()):
        successor = after_first.copy(stack=False)
        successor.push(reply)
        classification_by_successor_fen[successor.fen()] = reply_values[reply.uci()]
    authority = _PerSuccessorAuthority(classification_by_successor_fen)
    counters = {
        **_r1_reply_counter_defaults(),
        "availability_queries": 0,
        "availability_positives": 0,
        "virtual_frame_queries": 0,
        "v2_duplicate_virtual_queries": 0,
        "v2_real_observations": 0,
        "v2_structural_transitions": 0,
        "child_handoffs": 0,
    }
    exposures = {}
    terminal_kind, successor_ids, audit = _episode(
        authority,
        fen,
        first,
        after_first,
        counters,
        exposures,
    )

    manifest = audit["manifest"]
    contexts = manifest["reply_context"]
    legal_replies = {
        reply.uci() for reply in sorted(after_first.legal_moves, key=lambda item: item.uci())
    }
    assert terminal_kind is None
    assert successor_ids == (R0_COMPETENCE_ID,)
    assert len(manifest["reply_ids"]) == len(legal_replies)
    assert {row["black_move"] for row in contexts} == legal_replies
    assert {row["reply_id"] for row in contexts} == set(manifest["reply_ids"])

    values_by_move = {
        row["black_move"]: row["authority_row"]["value"] for row in contexts
    }
    assert len(values_by_move) == len(legal_replies)
    assert all(value > 0.0 for value in values_by_move.values())
    assert len(set(values_by_move.values())) == len(values_by_move)
    assert values_by_move["d7e8"] == pytest.approx(0.31)
    reply_rows = manifest["envelope"]["reply_rows"]
    selected_row = min(reply_rows, key=lambda row: row["value"])
    assert manifest["selected_reply_id"] == selected_row["reply_id"]
    assert manifest["selected_black_move"] == min(
        values_by_move, key=values_by_move.__getitem__
    )
    assert manifest["selected_black_move"] == "d7e8"

    assert manifest["real_event"] is True
    assert manifest["duplicate_virtual_query"] is False
    assert manifest["actual_r0_action_mated"] is True
    assert manifest["positive_handoff"] is True
    assert manifest["envelope"]["state"] == AvailabilityState.AVAILABLE.value
    assert manifest["envelope"]["positive_gate"] is True
    assert manifest["envelope"]["value"] == pytest.approx(
        min(values_by_move.values())
    )
    assert manifest["successor_signal"]["aggregation"] == (
        "minimum_over_all_grounded_available_replies"
    )
    assert audit["successor_signal"].value == pytest.approx(
        min(values_by_move.values())
    )
    assert audit["successor_signal"].provider_ids == (R0_COMPETENCE_ID,)
    assert audit["successor_signal"].grounding_ancestors == (
        R0_COMPETENCE_ID,
    )
    assert exposures == {audit["selected_exposure_key"]: 1}
    assert len(authority.consumed_receipts) == 1
    assert len(authority.accepted_real_references) == 1
    assert counters["reply_counterexample_real_event_count"] == 1
    assert counters["reply_counterexample_duplicate_virtual_count"] == 0

    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(min_grounding_evidence=3)
    )
    provider = credit.register(R0_COMPETENCE_ID, mature=True)
    provider.fast_value = 0.8
    provider.slow_value = 0.8
    provider.grounding_level = 0
    provider.terminal_evidence = 3
    provider.causal_confirmations = 1
    credit.register("r1:test")
    credit.begin_episode()
    event = credit.transition(
        "r1:test",
        responsibilities=(Responsibility("r1:test"),),
        explicit_successor_signal=audit["successor_signal"],
    )
    assert event.successor_value == pytest.approx(
        manifest["envelope"]["value"]
    )
    assert event.provider_ids == (R0_COMPETENCE_ID,)
    assert event.terminal_kind is None
    assert event.real_step is True
    assert "r1:test" in event.updated_values
    assert event.td_error == pytest.approx(
        event.immediate_reward
        + credit.config.gamma * event.successor_value
        - event.predicted_value
    )
