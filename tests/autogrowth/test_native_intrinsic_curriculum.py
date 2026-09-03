from __future__ import annotations

from collections import Counter
import copy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import pickle
import subprocess
import sys
import textwrap
from types import SimpleNamespace

import chess
import pytest

from recon_lite import FrameContext, FrameKind, LinkType
from recon_lite_chess.autogrowth import (
    native_intrinsic_curriculum as curriculum_module,
)

from recon_lite_hector.learning import (
    CompetenceGateExample,
    IntrinsicCreditConfig,
    IntrinsicCreditEngine,
    OutcomeCalibratedPrototypeGate,
    Responsibility,
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
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import (
    NativeProspectiveAuthorityV2,
    StructuralMode,
    V2Mode,
)
from recon_lite_chess.autogrowth.native_prospective_boundary_candidate_ecology import (
    ProspectiveBoundaryCandidateEcology,
)
from recon_lite_chess.autogrowth.native_trace_competence_authority import (
    TraceNativeCompetenceOrganism,
    TraceNativeLearningConfig,
)
from recon_lite_chess.autogrowth.native_intrinsic_curriculum import (
    NativeIntrinsicCurriculumConfig,
    R1MechanisticArm,
    R0_BALANCED_STRATA,
    R0_COMPETENCE_ID,
    R0DevelopmentCeilingReached,
    GATE_FEATURE_NAMES,
    R1_BALANCED_STRATA,
    R1_RETIRED_DEVELOPMENT_FENS,
    R1CheckpointInterrupt,
    R1_ACTION_SELECTION_LOCAL_RECON,
    R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE,
    V2_PROSPECTIVE_AVAILABILITY,
    _Pools,
    _apply_child_value_control,
    _attach_terminal_r1_regression_report,
    _balanced_r0_quotas,
    _balanced_r1_quotas,
    _boundary_ecology_step,
    _build_r0_replay_memory,
    _choose_with_child_priority,
    _classify_r0_stratum,
    _classify_r1_stratum,
    _disable_nonmature_composites,
    _execute_white_and_observe,
    _evaluate_r0,
    _evaluate_r1,
    _fit_r0_gate,
    _generate_balanced_r0_split,
    _generate_balanced_r1_split,
    _mechanistic_r1_arms,
    _native_v2_r0_admission_audit,
    _native_v2_authority_ready_for_r1,
    _native_v2_runtime_integrity_ready,
    _new_boundary_ecology_from_authority_history,
    _namespace_development_fullmoves,
    _r0_available,
    _r0_available_with_dispatch_cache,
    _r1_orbit_key,
    _r1_snapshot_fingerprint,
    _select_r1_training_action,
    _train_r0,
    _replay_r0,
    run_native_intrinsic_curriculum,
    _restore_disabled_composites,
    _run_r1_arm,
    _v2_authoritative_predecessor_fens,
    _v2_r0_available,
    _v2_r0_observe_training_successor,
    _verify_boundary_ecology_alignment,
    _write_live_r1_progress,
)
from recon_lite_chess.autogrowth.foundation_curriculum import (
    _forced_mate_in_two_first_moves,
    _mate_moves,
)
from recon_lite_chess.autogrowth.native_single_graph_curriculum import (
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
)


MATE_ONE_FEN = "k7/8/1K6/8/8/8/8/7R w - - 0 1"


def test_r1_exhaustive_evaluation_never_opens_correct_move_labels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fen = R1_RETIRED_DEVELOPMENT_FENS[0]
    board = chess.Board(fen)
    first = _forced_mate_in_two_first_moves(board)[0]
    policy = {board.fen(): first}
    after_first = board.copy(stack=False)
    after_first.push(first)
    for reply in tuple(after_first.legal_moves):
        successor = after_first.copy(stack=False)
        successor.push(reply)
        mate_moves = _mate_moves(successor)
        assert mate_moves
        policy[successor.fen()] = mate_moves[0]

    class ScriptedPolicy:
        def choose(self, position, **_kwargs):
            return policy.get(position.fen())

    def forbidden_label_read(_board):
        raise AssertionError("R1 evaluation opened a correct-move label")

    monkeypatch.setattr(
        curriculum_module,
        "_forced_mate_in_two_first_moves",
        forbidden_label_read,
    )
    result = _evaluate_r1(
        ScriptedPolicy(),
        (fen,),
        max_samples=1,
    )

    assert result["conversion_count"] == 1
    assert result["conversion_rate"] == 1.0
    assert result["reply_evaluation_mode"] == "exhaustive"
    assert result["samples"][0]["all_replies_mated"] is True
    assert "parent_first_move_correct_count" not in result


class _FakeV2Authority:
    """Minimal serialized authority double for curriculum-boundary tests."""

    def __init__(self, *, certify_after: int = 1, grounded: bool = True) -> None:
        self.certify_after = int(certify_after)
        self.grounded = bool(grounded)
        self.receipts = {}
        self.base = SimpleNamespace(
            receipts=self.receipts,
            r0=SimpleNamespace(
                provenance=SimpleNamespace(
                    grounded=self.grounded,
                    grounding_source=(
                        "test_grounded_real_history"
                        if self.grounded
                        else None
                    ),
                )
            ),
        )
        self.accepted_real_references = {}
        self.consumed_receipts = {}
        self.pending_event = None
        self.next_expected_ordinal = 0
        self.structural_epoch_schedule = ()
        self.current_generation = 0
        self.generation_phase = SimpleNamespace(value="prospective")
        self.states = {}
        self.deferred_requests = {}
        self.deferred_child_births = {}

    @property
    def certified(self) -> bool:
        return self.next_expected_ordinal >= self.certify_after

    def _classification(self):
        state = "AVAILABLE" if self.certified else "UNKNOWN"
        return SimpleNamespace(
            state=state,
            to_manifest=lambda: {"state": state},
        )

    @staticmethod
    def _actuation(board: chess.Board):
        move = min(board.legal_moves, key=lambda item: item.uci())
        return SimpleNamespace(
            move_uci=move.uci(),
            option_identity="fake-v2-r0-option",
        )

    def open_virtual(self, frame) -> dict[str, object]:
        actuation = self._actuation(frame.values["board"])
        response = SimpleNamespace(
            available=self.certified,
            grounded=self.grounded,
            grounding_source=(
                "test_grounded_real_history" if self.grounded else None
            ),
        )
        query = SimpleNamespace(
            actuation=actuation,
            response=response,
            availability_provenance={
                "authority": "NativeProspectiveAuthorityV2_graph_emission",
                "certification_evidence_added": 0,
            },
        )
        return {"query": query, "classification": self._classification()}

    def open_real_event(self, frame, **_kwargs):
        if self.pending_event is not None:
            raise RuntimeError("fake V2 authority already has a pending event")
        actuation = self._actuation(frame.values["board"])
        pending = SimpleNamespace(
            pending_token=f"pending-{self.next_expected_ordinal}",
            pre_outcome_classification=self._classification(),
        )
        self.pending_event = pending
        return pending, SimpleNamespace(actuation=actuation)

    def mint_environment_receipt(
        self, *, pending_token, trace, predecessor, successor
    ):
        del trace, successor
        if self.pending_event is None or pending_token != self.pending_event.pending_token:
            raise RuntimeError("fake V2 receipt is not paired with its pending event")
        return SimpleNamespace(
            event_id=f"event-{self.next_expected_ordinal}",
            predecessor_fen=predecessor.fen(),
        )

    def consume(self, receipt):
        if self.pending_event is None:
            raise RuntimeError("fake V2 consume has no pending event")
        self.accepted_real_references[receipt.event_id] = SimpleNamespace(
            receipt_id=receipt.event_id,
            stable_physical_interaction_id=f"physical:{receipt.event_id}",
        )
        self.consumed_receipts[receipt.event_id] = receipt
        self.next_expected_ordinal += 1
        self.pending_event = None
        return SimpleNamespace(
            manifest=lambda: {"event_id": receipt.event_id}
        )

    def continuation_manifest(self) -> dict[str, object]:
        return {
            "certify_after": self.certify_after,
            "next_expected_ordinal": self.next_expected_ordinal,
            "accepted_real_references": tuple(
                (key, reference.stable_physical_interaction_id)
                for key, reference in sorted(
                    self.accepted_real_references.items()
                )
            ),
            "consumed_receipts": tuple(
                (key, receipt.predecessor_fen)
                for key, receipt in sorted(self.consumed_receipts.items())
            ),
        }

    def continuation_digest(self) -> str:
        return hashlib.sha256(
            repr(self.continuation_manifest()).encode("utf-8")
        ).hexdigest()

    def dumps(self) -> bytes:
        return pickle.dumps(self, protocol=5)

    @classmethod
    def loads(cls, payload: bytes) -> "_FakeV2Authority":
        restored = pickle.loads(payload)
        if not isinstance(restored, cls):
            raise TypeError("unexpected fake V2 authority payload")
        return restored

    def verify_full_history_boundary(self, boundary: str) -> None:
        assert boundary


def test_development_fullmove_namespace_is_exact_and_non_geometric() -> None:
    groups = _namespace_development_fullmoves(
        ((MATE_ONE_FEN,), ()),
        base=900_000,
    )
    board = chess.Board(groups[0][0])
    original = chess.Board(MATE_ONE_FEN)
    assert board.fullmove_number == 900_000
    assert board.board_fen() == original.board_fen()
    assert board.turn == original.turn
    assert groups[1] == ()


def _graph() -> NativeReConKRKGraph:
    return NativeReConKRKGraph(
        config=NativeSingleGraphConfig(
            include_symmetries=False,
            eta_m3=0.1,
            max_ticks=80,
            key_mode="canonical",
            shared_feature_atoms=True,
            shared_projection_atoms=True,
            include_grouped_cache_terminals=False,
            score_action_pattern_atoms=True,
            score_hierarchy_edge_weights=True,
        )
    )


def test_native_intrinsic_graph_starts_with_empty_learned_state() -> None:
    graph = _graph()
    audit = graph.learned_state_audit()

    assert audit == {
        "node_count": 1,
        "edge_count": 0,
        "triplet_count": 0,
        "trainable_edge_count": 0,
        "nonzero_trainable_edge_count": 0,
        "nonzero_local_weight_node_count": 0,
        "m3_update_count": 0,
        "m4_event_count": 0,
    }


def test_strict_r0_uses_local_choice_and_validation_cannot_stop_budget() -> None:
    graph = _graph()
    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(min_grounding_evidence=1)
    )
    credit.register(R0_COMPETENCE_ID)
    config = NativeIntrinsicCurriculumConfig(
        r0_epochs=2,
        r0_validation_interval=1,
        r0_mastery_threshold=0.0,
        r0_action_selection_mode=R1_ACTION_SELECTION_LOCAL_RECON,
        validation_controls_stage_transitions=False,
        max_samples=0,
    )

    training = _train_r0(
        graph,
        credit,
        (MATE_ONE_FEN,),
        (MATE_ONE_FEN,),
        (),
        config=config,
    )

    assert training["stopped_epoch"] == 2
    assert training["episodes"] == 2
    assert training["native_local_action_count"] == 2
    assert training["scheduled_action_count"] == 0
    assert training["validation_controls_stage_transitions"] is False
    assert all(
        checkpoint["validation_mastery"] is True
        for checkpoint in training["validation_checkpoints"]
    )
    assert {
        checkpoint["validation_action_selection_mode"]
        for checkpoint in training["validation_checkpoints"]
    } == {R1_ACTION_SELECTION_LOCAL_RECON}
    assert credit.states[R0_COMPETENCE_ID].terminal_evidence == 0
    assert credit.states[R0_COMPETENCE_ID].mature is False

    disabled = _evaluate_r0(
        graph,
        (MATE_ONE_FEN,),
        masked_triplets=set(graph.triplet_ids),
        max_samples=1,
        action_selection_mode=R1_ACTION_SELECTION_LOCAL_RECON,
    )
    assert disabled["accuracy"] == 0.0
    assert disabled["null_selection_count"] == 1
    assert disabled["effective_action_selection_mode"] == (
        "native_local_all_sources_masked_abstention"
    )


def test_r0_development_ceiling_interrupts_only_after_complete_epoch() -> None:
    graph = _graph()
    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(min_grounding_evidence=1)
    )
    credit.register(R0_COMPETENCE_ID)
    config = NativeIntrinsicCurriculumConfig(
        r0_epochs=3,
        r0_validation_interval=99,
        r0_action_selection_mode=R1_ACTION_SELECTION_LOCAL_RECON,
        validation_controls_stage_transitions=False,
        development_wall_ceiling_seconds=0.0,
        max_samples=0,
    )

    with pytest.raises(R0DevelopmentCeilingReached) as interrupted:
        _train_r0(
            graph,
            credit,
            (MATE_ONE_FEN, MATE_ONE_FEN),
            (MATE_ONE_FEN,),
            (),
            config=config,
        )

    assert interrupted.value.epoch == 1
    assert "wall_seconds" in interrupted.value.reason
    # Both positions in the first epoch completed their observed transition;
    # no mid-epoch ceiling check may discard the second action/TD update.
    assert graph.graph.nodes["tg26o_root"].meta["request_exposures"] == 2
    assert graph.m3_update_count > 0


def test_r0_gate_selection_ignores_regression_until_final_report(monkeypatch) -> None:
    """Gate maturity must be determined by train/validation only."""

    def fake_example(_graph, label: str) -> CompetenceGateExample:
        positive = label.startswith("positive")
        value = 1.0 if positive else 0.0
        return CompetenceGateExample(
            features=(value,) * len(GATE_FEATURE_NAMES),
            success=positive,
        )

    class RegressionBomb:
        def __iter__(self):
            raise AssertionError("gate fitting read the withheld regression split")

        def __len__(self):
            raise AssertionError("gate fitting inspected withheld regression size")

    monkeypatch.setattr(
        "recon_lite_chess.autogrowth.native_intrinsic_curriculum._gate_example",
        fake_example,
    )
    gate, selection = _fit_r0_gate(
        object(),
        train_positive=("positive-train",),
        train_negative=("negative-train",),
        validation_positive=("positive-validation",),
        validation_negative=("negative-validation",),
        regression_positive=RegressionBomb(),
        regression_negative=RegressionBomb(),
    )

    assert gate.mature is True
    assert selection["selection_split"] == "gate_validation"
    assert selection["regression_metrics"] is None
    assert selection["regression_withheld_until_final"] is True


def test_top_level_r0_stage_entry_uses_validation_and_reports_regression_last(
    tmp_path, monkeypatch
) -> None:
    """A bad held-out R0 split cannot block validation-selected stage entry."""

    regression_fen = R1_RETIRED_DEVELOPMENT_FENS[0]
    pools = _Pools(
        r0_train=(MATE_ONE_FEN,),
        r0_validation=(MATE_ONE_FEN,),
        r0_regression=(regression_fen,),
        gate_train_decoys=(R1_RETIRED_DEVELOPMENT_FENS[1],),
        gate_validation_decoys=(R1_RETIRED_DEVELOPMENT_FENS[2],),
        gate_regression_decoys=(R1_RETIRED_DEVELOPMENT_FENS[3],),
        r1_train=(),
        r1_validation=(),
        r1_regression=(),
        r0_train_strata=("test",),
        r0_validation_strata=("test",),
        r0_regression_strata=("test",),
        r0_excluded_fens=(),
        r0_pool_mode="test",
        r1_train_strata=(),
        r1_validation_strata=(),
        r1_regression_strata=(),
        r1_pool_mode="test",
    )

    class Gate:
        mature = True

        def to_dict(self):
            return {"mature": True}

        def evaluate(self, examples):
            return {
                "count": len(examples),
                "true_positive": 0,
                "false_positive": 0,
                "true_negative": len(examples),
                "false_negative": 0,
                "precision": 0.0,
                "recall": 0.0,
            }

    calls: list[tuple[str, ...]] = []

    def fake_evaluate(_graph, fens, **_kwargs):
        values = tuple(fens)
        calls.append(values)
        is_validation = values == pools.r0_validation
        return {
            "position_count": len(values),
            "correct_count": len(values) if is_validation else 0,
            "accuracy": 1.0 if is_validation else 0.0,
            "null_selection_count": 0,
            "illegal_move_count": 0,
            "stalemate_count": 0,
            "rook_loss_count": 0,
            "samples": [],
        }

    def fake_train(*_args, **_kwargs):
        return {
            "episodes": 1,
            "observed_mate_count": 1,
            "observed_nonterminal_count": 0,
            "observed_failure_count": 0,
            "formal_confirmation_failure_count": 0,
            "stopped_epoch": 1,
            "validation_checkpoints": [],
            "teacher_positive_move_sets_consumed": 0,
            "forced_first_move_labels_consumed": 0,
            "graph_after_training": {},
            "duration_seconds": 0.0,
        }

    monkeypatch.setattr(
        "recon_lite_chess.autogrowth.native_intrinsic_curriculum._build_pools",
        lambda _cfg: pools,
    )
    monkeypatch.setattr(
        "recon_lite_chess.autogrowth.native_intrinsic_curriculum._train_r0",
        fake_train,
    )
    monkeypatch.setattr(
        "recon_lite_chess.autogrowth.native_intrinsic_curriculum._evaluate_r0",
        fake_evaluate,
    )
    monkeypatch.setattr(
        "recon_lite_chess.autogrowth.native_intrinsic_curriculum._fit_r0_gate",
        lambda *_args, **_kwargs: (Gate(), {"selection_split": "gate_validation"}),
    )

    result = run_native_intrinsic_curriculum(
        config=NativeIntrinsicCurriculumConfig(
            seed=123,
            run_r1=False,
            output_path=str(tmp_path / "result.json"),
            progress_path=str(tmp_path / "progress.json"),
        )
    )

    # Initial validation, validation-only intervention probe, and exactly one
    # final report query on the withheld R0 regression pool.
    assert calls == [pools.r0_validation, pools.r0_validation, pools.r0_regression]
    assert result.payload["r0"]["pass"] is True
    assert result.payload["r0"]["regression"]["accuracy"] == 0.0
    assert result.payload["r0"]["regression_pass_report_only"] is False
    progress = json.loads(Path(result.config.progress_path).read_text())
    assert "regression_accuracy" not in progress["r0"]
    assert progress["r0"]["regression_withheld_until_final"] is True


def test_strict_stage_entry_reads_local_providers_not_aggregate_accuracy(
    tmp_path, monkeypatch
) -> None:
    pools = _Pools(
        r0_train=(MATE_ONE_FEN,),
        r0_validation=(MATE_ONE_FEN,),
        r0_regression=(MATE_ONE_FEN,),
        gate_train_decoys=(R1_RETIRED_DEVELOPMENT_FENS[1],),
        gate_validation_decoys=(R1_RETIRED_DEVELOPMENT_FENS[2],),
        gate_regression_decoys=(R1_RETIRED_DEVELOPMENT_FENS[3],),
        r1_train=(),
        r1_validation=(),
        r1_regression=(),
        r0_train_strata=("test",),
        r0_validation_strata=("test",),
        r0_regression_strata=("test",),
        r0_excluded_fens=(),
        r0_pool_mode="test",
        r1_train_strata=(),
        r1_validation_strata=(),
        r1_regression_strata=(),
        r1_pool_mode="test",
    )

    class Gate:
        mature = False

        @staticmethod
        def to_dict():
            return {"mature": False}

        @staticmethod
        def evaluate(examples):
            return {
                "count": len(examples),
                "true_positive": 0,
                "false_positive": 0,
                "true_negative": len(examples),
                "false_negative": 0,
                "precision": 0.0,
                "recall": 0.0,
            }

    def seed_one_local_provider(graph, credit, *_args, **_kwargs):
        board = chess.Board(MATE_ONE_FEN)
        move = next(
            item
            for item in board.legal_moves
            if _execute_white_and_observe(board, item) == "mate"
        )
        triplet_id = graph.apply_intrinsic_td(
            board,
            move,
            td_error=1.0,
            stage_diagnostic="strict_local_provider_test",
        )
        credit.register(triplet_id)
        for _ in range(3):
            credit.begin_episode()
            credit.transition(triplet_id, terminal_kind="mate")
        return {
            "episodes": 3,
            "observed_mate_count": 3,
            "observed_nonterminal_count": 0,
            "observed_failure_count": 0,
            "formal_confirmation_failure_count": 0,
            "stopped_epoch": 3,
            "validation_checkpoints": [],
            "teacher_positive_move_sets_consumed": 0,
            "forced_first_move_labels_consumed": 0,
            "graph_after_training": graph.learned_state_audit(),
            "duration_seconds": 0.0,
        }

    def submastery_report(_graph, fens, **_kwargs):
        count = len(tuple(fens))
        return {
            "position_count": count,
            "correct_count": max(0, count - 1),
            "accuracy": 0.9791666666666666,
            "null_selection_count": 0,
            "illegal_move_count": 0,
            "stalemate_count": 0,
            "rook_loss_count": 0,
            "samples": [],
        }

    monkeypatch.setattr(curriculum_module, "_build_pools", lambda _cfg: pools)
    monkeypatch.setattr(curriculum_module, "_train_r0", seed_one_local_provider)
    monkeypatch.setattr(curriculum_module, "_evaluate_r0", submastery_report)
    monkeypatch.setattr(
        curriculum_module,
        "_fit_r0_gate",
        lambda *_args, **_kwargs: (Gate(), {"selection_split": "report_only"}),
    )

    result = run_native_intrinsic_curriculum(
        config=NativeIntrinsicCurriculumConfig(
            seed=456,
            run_r1=False,
            r0_action_selection_mode=R1_ACTION_SELECTION_LOCAL_RECON,
            r0_boundary_ecology_enabled=True,
            validation_controls_stage_transitions=False,
            output_path=str(tmp_path / "result.json"),
            progress_path=str(tmp_path / "progress.json"),
        )
    )

    assert result.payload["r0"]["pass"] is True
    assert result.payload["r0"]["pass_semantics"] == (
        "nonempty_local_direct_outcome_provider_set"
    )
    assert result.payload["r0"]["training_mastery_report"] is False
    assert result.payload["r0"]["endogenous_readiness_pass"] is True
    assert result.payload["r0"]["final_report_pass"] is False
    assert result.payload["r0"]["final_report_pass_semantics"] == (
        "aggregate_training_and_regression_performance_report_only"
    )
    assert result.payload["r0"]["local_provider_audit"]["provider_count"] == 1
    assert result.payload["r0"]["consolidation"][
        "global_r0_maturity_mutated"
    ] is False
    global_state = result.payload["final_credit"]["states"][R0_COMPETENCE_ID]
    assert global_state["terminal_evidence"] == 0
    assert global_state["mature"] is False


def test_v2_runtime_integrity_failure_cannot_rescue_r1_with_legacy_gate(
    monkeypatch, tmp_path
) -> None:
    """V2 admission must fail closed even when the old gate is mature."""

    pools = _Pools(
        r0_train=(MATE_ONE_FEN,),
        r0_validation=(MATE_ONE_FEN,),
        r0_regression=(MATE_ONE_FEN,),
        gate_train_decoys=(R1_RETIRED_DEVELOPMENT_FENS[1],),
        gate_validation_decoys=(R1_RETIRED_DEVELOPMENT_FENS[2],),
        gate_regression_decoys=(R1_RETIRED_DEVELOPMENT_FENS[3],),
        r1_train=(R1_RETIRED_DEVELOPMENT_FENS[4],),
        r1_validation=(R1_RETIRED_DEVELOPMENT_FENS[5],),
        r1_regression=(R1_RETIRED_DEVELOPMENT_FENS[6],),
        r0_train_strata=("test",),
        r0_validation_strata=("test",),
        r0_regression_strata=("test",),
        r0_excluded_fens=(),
        r0_pool_mode="test",
        r1_train_strata=("test",),
        r1_validation_strata=("test",),
        r1_regression_strata=("test",),
        r1_pool_mode="test",
    )
    graph = _graph()

    class Gate:
        mature = True

        @staticmethod
        def to_dict() -> dict[str, object]:
            return {"mature": True}

    class Authority:
        base = SimpleNamespace(
            r0=SimpleNamespace(graph=graph, frozen_triplet_ids=frozenset())
        )

        @staticmethod
        def open_virtual(*_args, **_kwargs):
            raise AssertionError("failed V2 authority should not be queried")

        @staticmethod
        def continuation_digest() -> str:
            return "failed-v2-integrity"

    monkeypatch.setattr(
        curriculum_module,
        "_build_pools",
        lambda _cfg: pools,
    )
    monkeypatch.setattr(
        curriculum_module,
        "_train_r0",
        lambda *_args, **_kwargs: {
            "episodes": 1,
            "observed_mate_count": 1,
            "observed_nonterminal_count": 0,
            "observed_failure_count": 0,
            "formal_confirmation_failure_count": 0,
            "stopped_epoch": 1,
            "validation_checkpoints": [],
            "teacher_positive_move_sets_consumed": 0,
            "forced_first_move_labels_consumed": 0,
            "graph_after_training": {},
            "duration_seconds": 0.0,
        },
    )

    def evaluate(_graph, fens, **_kwargs):
        return {
            "position_count": len(tuple(fens)),
            "correct_count": len(tuple(fens)),
            "accuracy": 1.0,
            "null_selection_count": 0,
            "illegal_move_count": 0,
            "stalemate_count": 0,
            "rook_loss_count": 0,
            "samples": [],
        }

    monkeypatch.setattr(curriculum_module, "_evaluate_r0", evaluate)
    monkeypatch.setattr(
        curriculum_module,
        "_fit_r0_gate",
        lambda *_args, **_kwargs: (Gate(), {"selection_split": "gate_validation"}),
    )
    monkeypatch.setattr(
        curriculum_module,
        "_evaluate_r0_gate_regression",
        lambda *_args, **_kwargs: {
            "true_positive": 1,
            "false_positive": 0,
        },
    )
    monkeypatch.setattr(
        curriculum_module,
        "_clone_parity",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        curriculum_module,
        "_build_r0_replay_memory",
        lambda *_args, **_kwargs: ((), {}),
    )
    monkeypatch.setattr(
        curriculum_module,
        "_native_v2_r0_admission_audit",
        lambda *_args, **_kwargs: {
            "runtime_integrity_pass": False,
            "pass": False,
        },
    )

    def forbidden_arm(*_args, **_kwargs):
        raise AssertionError("legacy gate rescued failed V2 integrity")

    monkeypatch.setattr(curriculum_module, "_run_r1_arm", forbidden_arm)

    result = run_native_intrinsic_curriculum(
        config=NativeIntrinsicCurriculumConfig(
            seed=999,
            run_r1=True,
            r0_availability_mode=V2_PROSPECTIVE_AVAILABILITY,
            r0_boundary_ecology_enabled=True,
            output_path=str(tmp_path / "result.json"),
            progress_path=str(tmp_path / "progress.json"),
        ),
        r0_child_authority_factory=lambda *_args: (
            Authority(),
            {"factory_audit": True},
        ),
    )

    assert result.payload["r0_child_authority"]["native_r0_admission"][
        "runtime_integrity_pass"
    ] is False
    assert result.payload["r1_arms"] == {}
    assert result.payload["decision"]["r1_executed"] is False


def test_live_progress_removes_stale_regression_from_reused_file(tmp_path) -> None:
    progress_path = tmp_path / "progress.json"
    progress_path.write_text(
        json.dumps({"r0": {"regression_accuracy": 0.25}}),
        encoding="utf-8",
    )
    config = NativeIntrinsicCurriculumConfig(progress_path=str(progress_path))
    _write_live_r1_progress(
        config,
        arm_name="full_intrinsic",
        epoch=2,
        checkpoint={
            "validation_conversion_rate": 0.5,
            "r0_retention_accuracy": 1.0,
            "r0_validation_retention_accuracy": 1.0,
        },
        snapshot_path=tmp_path / "snapshot.pkl",
        resumed=False,
    )
    payload = json.loads(progress_path.read_text(encoding="utf-8"))
    assert "regression_accuracy" not in payload["r0"]
    assert "regression" not in payload["active_r1_arm"]
    assert payload["active_r1_arm"]["regression_withheld_until_final"] is True


def test_terminal_r1_regression_is_attached_once_per_arm_after_training(
    monkeypatch,
) -> None:
    """Terminal reports are queried only after the arm set is complete."""

    pools = SimpleNamespace(
        r1_regression=("r1-regression",),
        r1_regression_strata=("test",),
        r0_regression=("r0-regression",),
    )
    config = NativeIntrinsicCurriculumConfig(max_samples=0)
    events: list[tuple[str, str]] = []
    training_done: list[str] = []

    monkeypatch.setattr(
        "recon_lite_chess.autogrowth.native_intrinsic_curriculum._disable_nonmature_composites",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "recon_lite_chess.autogrowth.native_intrinsic_curriculum._restore_disabled_composites",
        lambda *_args, **_kwargs: None,
    )

    def fake_r1(_graph, fens, **_kwargs):
        events.append(("r1_regression", fens[0]))
        return {"conversion_rate": 0.0}

    def fake_r0(_graph, fens, **_kwargs):
        events.append(("r0_regression", fens[0]))
        return {"accuracy": 0.0}

    monkeypatch.setattr(
        "recon_lite_chess.autogrowth.native_intrinsic_curriculum._evaluate_r1",
        fake_r1,
    )
    monkeypatch.setattr(
        "recon_lite_chess.autogrowth.native_intrinsic_curriculum._evaluate_r0",
        fake_r0,
    )

    def deferred_arm(name: str) -> dict[str, object]:
        graph = object()
        return {
            "regression": None,
            "r0_regression_retention": None,
            "routing_ablation": {
                "child_priority_off": {
                    "validation": {},
                    "regression": None,
                }
            },
            "_terminal_regression_context": {
                "graph": graph,
                "r0_child_triplet_ids": None,
                "child_dispatch_cache": None,
                "r0_child_authority": None,
                "current_routing_name": "child_priority_off",
            },
            "name": name,
        }

    arms = {"full_intrinsic": deferred_arm("full_intrinsic")}
    training_done.append("full_intrinsic")
    # No report query is made while the control arm is still absent.
    assert events == []
    arms["no_bootstrap"] = deferred_arm("no_bootstrap")
    training_done.append("no_bootstrap")

    for arm in arms.values():
        _attach_terminal_r1_regression_report(arm, pools, config)

    assert training_done == ["full_intrinsic", "no_bootstrap"]
    assert events == [
        ("r1_regression", "r1-regression"),
        ("r0_regression", "r0-regression"),
        ("r1_regression", "r1-regression"),
        ("r0_regression", "r0-regression"),
    ]
    for arm in arms.values():
        assert arm["terminal_regression_evaluation"] == {
            "evaluated_after_all_r1_arms": True,
            "r1_regression_query_count": 1,
            "r0_regression_retention_query_count": 1,
            "selection_influenced": False,
        }
        assert "_terminal_regression_context" not in arm


def test_r1_maturity_and_intervention_are_validation_only(monkeypatch, tmp_path) -> None:
    """A validation win is actionable even when final regression is poor."""

    pools = _Pools(
        r0_train=(MATE_ONE_FEN,),
        r0_validation=(MATE_ONE_FEN,),
        r0_regression=(R1_RETIRED_DEVELOPMENT_FENS[0],),
        gate_train_decoys=(R1_RETIRED_DEVELOPMENT_FENS[1],),
        gate_validation_decoys=(R1_RETIRED_DEVELOPMENT_FENS[2],),
        gate_regression_decoys=(R1_RETIRED_DEVELOPMENT_FENS[3],),
        r1_train=(R1_RETIRED_DEVELOPMENT_FENS[4],),
        r1_validation=(R1_RETIRED_DEVELOPMENT_FENS[5],),
        r1_regression=(R1_RETIRED_DEVELOPMENT_FENS[6],),
        r0_train_strata=("test",),
        r0_validation_strata=("test",),
        r0_regression_strata=("test",),
        r0_excluded_fens=(),
        r0_pool_mode="test",
        r1_train_strata=("test",),
        r1_validation_strata=("test",),
        r1_regression_strata=("test",),
        r1_pool_mode="test",
    )

    class Gate:
        mature = True

        def to_dict(self):
            return {"mature": True}

        def evaluate(self, examples):
            return {
                "count": len(examples),
                "true_positive": 0,
                "false_positive": 0,
                "true_negative": len(examples),
                "false_negative": 0,
                "precision": 0.0,
                "recall": 0.0,
            }

    events: list[str] = []

    def fake_r0_eval(_graph, fens, **_kwargs):
        values = tuple(fens)
        is_validation = values == pools.r0_validation
        if values == pools.r0_regression:
            events.append("r0_regression")
        return {
            "position_count": len(values),
            "correct_count": len(values) if is_validation else 0,
            "accuracy": 1.0 if is_validation else 0.0,
            "null_selection_count": 0,
            "illegal_move_count": 0,
            "stalemate_count": 0,
            "rook_loss_count": 0,
            "samples": [],
        }

    def fake_r0_train(*_args, **_kwargs):
        return {
            "episodes": 1,
            "observed_mate_count": 1,
            "observed_nonterminal_count": 0,
            "observed_failure_count": 0,
            "formal_confirmation_failure_count": 0,
            "stopped_epoch": 1,
            "validation_checkpoints": [],
            "teacher_positive_move_sets_consumed": 0,
            "forced_first_move_labels_consumed": 0,
            "graph_after_training": {},
            "duration_seconds": 0.0,
        }

    def fake_arm(_name, _graph, credit, *_args, **_kwargs):
        events.append(f"train:{_name}")
        credit.register("native_intrinsic_r1_mate_in_2", mature=False, hierarchy_depth=0)
        is_full = _name == "full_intrinsic"
        validation_rate = 1.0 if is_full else 0.0

        # The primary arm is mutated only after both training arms return.
        # Wrap the selected objects so the order assertion below covers every
        # validation-selected mutation, not just the training calls.
        original_set_mature = credit.set_mature
        original_intervention = credit.record_paired_intervention
        original_consolidate = credit.consolidate
        original_graph_mature = _graph.mature_existing_graph
        original_graph_freeze = _graph.freeze_existing_parameters

        def set_mature(*args, **kwargs):
            events.append("mutation:set_mature")
            return original_set_mature(*args, **kwargs)

        def record_intervention(*args, **kwargs):
            events.append("mutation:paired_intervention")
            return original_intervention(*args, **kwargs)

        def consolidate(*args, **kwargs):
            events.append("mutation:credit_consolidate")
            return original_consolidate(*args, **kwargs)

        def mature_graph(*args, **kwargs):
            events.append("mutation:graph_mature")
            return original_graph_mature(*args, **kwargs)

        def freeze_graph(*args, **kwargs):
            events.append("mutation:graph_freeze")
            return original_graph_freeze(*args, **kwargs)

        credit.set_mature = set_mature
        credit.record_paired_intervention = record_intervention
        credit.consolidate = consolidate
        _graph.mature_existing_graph = mature_graph
        _graph.freeze_existing_parameters = freeze_graph
        return {
            "training": {
                "episodes": 1,
                "stopped_epoch": 1,
                "joint_mastery": False,
                "child_handoff_count": 0,
                "r0_replay_episode_count": 0,
            },
            "validation": {"conversion_rate": validation_rate},
            "r0_validation_retention": {"accuracy": 1.0},
            "regression": None,
            "r0_regression_retention": None,
            "r0_retention": None,
            "routing_ablation": {
                "child_priority_off": {
                    "validation": {"conversion_rate": validation_rate},
                    "regression": None,
                }
            },
            "_terminal_regression_context": {
                "graph": _graph,
                "r0_child_triplet_ids": None,
                "child_dispatch_cache": None,
                "r0_child_authority": None,
                "current_routing_name": "child_priority_off",
            },
        }

    def fake_r1_eval(_graph, fens, **_kwargs):
        assert tuple(fens) == pools.r1_regression
        events.append("r1_regression")
        return {"conversion_rate": 0.0}

    monkeypatch.setattr(
        "recon_lite_chess.autogrowth.native_intrinsic_curriculum._build_pools",
        lambda _cfg: pools,
    )
    monkeypatch.setattr(
        "recon_lite_chess.autogrowth.native_intrinsic_curriculum._train_r0",
        fake_r0_train,
    )
    monkeypatch.setattr(
        "recon_lite_chess.autogrowth.native_intrinsic_curriculum._evaluate_r0",
        fake_r0_eval,
    )
    monkeypatch.setattr(
        "recon_lite_chess.autogrowth.native_intrinsic_curriculum._fit_r0_gate",
        lambda *_args, **_kwargs: (Gate(), {"selection_split": "gate_validation"}),
    )
    monkeypatch.setattr(
        "recon_lite_chess.autogrowth.native_intrinsic_curriculum._run_r1_arm",
        fake_arm,
    )
    monkeypatch.setattr(
        "recon_lite_chess.autogrowth.native_intrinsic_curriculum._evaluate_r1",
        fake_r1_eval,
    )

    result = run_native_intrinsic_curriculum(
        config=NativeIntrinsicCurriculumConfig(
            seed=456,
            r0_epochs=1,
            r1_epochs=1,
            run_r1=True,
            output_path=str(tmp_path / "result.json"),
            progress_path=str(tmp_path / "progress.json"),
        )
    )

    assert result.payload["decision"]["r1_validation_pass"] is True
    assert result.payload["decision"]["r1_pass"] is False
    assert result.payload["decision"]["r1_final_report_pass"] is False
    assert result.payload["r1_arms"]["full_intrinsic"]["consolidation"][
        "paired_intervention"
    ]["enabled_return"] == pytest.approx(1.0)
    assert result.payload["r1_arms"]["full_intrinsic"]["consolidation"][
        "paired_intervention"
    ]["disabled_return"] == pytest.approx(0.0)
    assert result.payload["r1_arms"]["full_intrinsic"]["regression"][
        "conversion_rate"
    ] == 0.0
    assert result.payload["r1_arms"]["full_intrinsic"]["credit"]["states"][
        "native_intrinsic_r1_mate_in_2"
    ]["mature"] is True
    arm_graph = result.payload["r1_arms"]["full_intrinsic"]["graph"]
    final_graph = result.payload["final_graph"]
    assert {
        key: arm_graph[key]
        for key in ("node_count", "edge_count", "triplet_count", "m3_update_count")
    } == {
        key: final_graph[key]
        for key in ("node_count", "edge_count", "triplet_count", "m3_update_count")
    }
    assert events == [
        "train:full_intrinsic",
        "train:no_bootstrap",
        "mutation:set_mature",
        "mutation:paired_intervention",
        "mutation:graph_mature",
        "mutation:graph_freeze",
        "mutation:credit_consolidate",
        "r1_regression",
        "r0_regression",
        "r1_regression",
        "r0_regression",
        "r0_regression",
    ]


def test_mechanistic_factorial_names_every_causal_factor_and_disables_growth() -> None:
    arms = _mechanistic_r1_arms(NativeIntrinsicCurriculumConfig())
    by_name = {arm.name: arm for arm in arms}

    assert set(by_name) == {
        "no_bootstrap",
        "learned_gate_learned_value",
        "learned_gate_zero_value",
        "shuffled_gate_learned_value",
        "exact_verify_learned_value",
        "exact_verify_zero_value",
        "exact_verify_constant_value",
        "exact_verify_learned_value_no_hierarchy_score",
    }
    assert all(not arm.composition_enabled for arm in arms)
    assert all(arm.mature_child_priority for arm in arms)
    assert by_name["no_bootstrap"].bootstrap_enabled is False
    assert by_name["exact_verify_zero_value"].child_value_mode == "zero"
    assert (
        by_name["exact_verify_learned_value_no_hierarchy_score"].hierarchy_edge_scoring
        is False
    )


def test_child_value_controls_change_only_emitted_slow_value() -> None:
    config = NativeIntrinsicCurriculumConfig(r1_placebo_child_value=0.375)
    base = IntrinsicCreditEngine(IntrinsicCreditConfig())
    base.register(
        R0_COMPETENCE_ID,
        mature=True,
        initial_fast_value=0.61,
        initial_slow_value=0.73,
    )

    observed = {}
    for mode in ("learned", "zero", "constant"):
        credit = copy.deepcopy(base)
        audit = _apply_child_value_control(
            credit,
            R1MechanisticArm(
                name=f"test_{mode}",
                bootstrap_enabled=True,
                availability_mode="prototype_gate",
                child_value_mode=mode,
            ),
            config,
        )
        state = credit.states[R0_COMPETENCE_ID]
        observed[mode] = state.slow_value
        assert state.fast_value == pytest.approx(0.61)
        assert audit["learned_value_before_control"] == pytest.approx(0.73)

    assert observed == pytest.approx(
        {"learned": 0.73, "zero": 0.0, "constant": 0.375}
    )


def test_native_graph_pickle_roundtrip_restores_runtime_predicates() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        graph.ensure_triplet(board, move, stage="snapshot_test")

    restored = pickle.loads(pickle.dumps(graph, protocol=5))

    assert restored.learned_state_audit() == graph.learned_state_audit()
    assert restored.audit_choice(board) == graph.audit_choice(board)
    assert all(
        node.predicate is not None
        for node in restored.graph.nodes.values()
        if node.ntype.name == "TERMINAL"
    )
    assert all(
        edge is restored.graph.edge_by_key[
            (edge.src, edge.dst, edge.ltype)
        ]
        for edges in restored.triplet_trainable_edges.values()
        for edge in edges
    )
    triplet_id = min(restored.triplet_trainable_edges)
    indexed_edge = restored.triplet_trainable_edges[triplet_id][0]
    canonical_edge = restored.graph.edge_by_key[
        (indexed_edge.src, indexed_edge.dst, indexed_edge.ltype)
    ]
    before_weight = float(canonical_edge.w)
    restored._apply_m3(triplet_id, reward=1.0)
    assert indexed_edge is canonical_edge
    assert float(canonical_edge.w) != before_weight


def test_native_graph_restores_legacy_detached_trainable_edge_index() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    graph.ensure_triplet(
        board,
        min(board.legal_moves, key=lambda item: item.uci()),
        stage="legacy_snapshot_alias_test",
    )
    legacy_state = dict(graph.__dict__)
    legacy_state["graph"] = copy.deepcopy(graph.graph)
    legacy_state["snapshot_schema_version"] = "native_recon_krk_graph.v1"
    assert any(
        edge is not legacy_state["graph"].edge_by_key[
            (edge.src, edge.dst, edge.ltype)
        ]
        for edges in legacy_state["triplet_trainable_edges"].values()
        for edge in edges
    )

    restored = object.__new__(NativeReConKRKGraph)
    restored.__setstate__(legacy_state)

    assert all(
        edge is restored.graph.edge_by_key[
            (edge.src, edge.dst, edge.ltype)
        ]
        for edges in restored.triplet_trainable_edges.values()
        for edge in edges
    )


def test_native_graph_semantic_manifest_excludes_only_runtime_diagnostics() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    graph.ensure_triplet(
        board,
        min(board.legal_moves, key=lambda item: item.uci()),
        stage="semantic_manifest_test",
    )
    before = graph.canonical_semantic_manifest()
    node = next(iter(graph.graph.nodes.values()))
    node.meta["activation_count"] = 999
    node.meta["choice_selected"] = True
    graph.runtime_choice_count = 999
    graph.scheduler_stats["choose_calls"] = 999
    assert graph.canonical_semantic_manifest() == before

    node.meta["action_uci"] = "a1a2"
    assert graph.canonical_semantic_manifest() != before


def test_frozen_policy_token_cache_matches_live_formal_confirmation() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    for _ in range(4):
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            terminal = _execute_white_and_observe(board, move)
            graph.apply_intrinsic_td(
                board,
                move,
                td_error=1.0 if terminal == "mate" else -1.0,
                stage_diagnostic="cache_token_test",
            )
    graph.mature_existing_graph()
    graph.freeze_existing_parameters(reason="cache_token_test")
    allowed = frozenset(graph.triplet_ids)

    token_cache: dict[str, dict] = {}
    miss = _r0_available_with_dispatch_cache(
        graph,
        None,
        board,
        mode="virtual_frame_verified",
        allowed_triplets=allowed,
        cache=token_cache,
        enabled=True,
        cache_validation_mode="frozen_policy_token",
    )
    token_hit = _r0_available_with_dispatch_cache(
        graph,
        None,
        board,
        mode="virtual_frame_verified",
        allowed_triplets=allowed,
        cache=token_cache,
        enabled=True,
        cache_validation_mode="frozen_policy_token",
    )
    live_hit = _r0_available_with_dispatch_cache(
        graph,
        None,
        board,
        mode="virtual_frame_verified",
        allowed_triplets=allowed,
        cache=token_cache,
        enabled=True,
        cache_validation_mode="live_formal",
    )

    assert miss[0] is True and miss[2] is False
    assert token_hit[0] == live_hit[0] == miss[0]
    assert token_hit[1]["selected_move"] == live_hit[1]["selected_move"]
    assert token_hit[1]["selected_triplet"] == live_hit[1]["selected_triplet"]
    assert token_hit[1]["cache_validation_mode"] == "frozen_policy_token"
    assert live_hit[1]["cache_validation_mode"] == "live_formal"
    assert token_hit[2] is True and live_hit[2] is True
    assert token_hit[3] is False and live_hit[3] is False
    assert graph.frozen_child_policy_token(allowed) == token_cache[board.fen()][
        "frozen_policy_token"
    ]
    assert graph.frozen_child_policy_token(frozenset()) is None


def test_frozen_policy_token_full_arm_matches_live_formal_with_cache_hits(
    tmp_path,
) -> None:
    base_graph = _graph()
    r1_fen = R1_RETIRED_DEVELOPMENT_FENS[0]
    r1_board = chess.Board(r1_fen)
    forced_first = tuple(_forced_mate_in_two_first_moves(r1_board))
    assert forced_first

    # Build a small, real Mate-in-1 child from every successor of one forced
    # Mate-in-2 move. This is test setup only; R1 training still receives no
    # forced-move labels and selects actions through the native graph.
    after_first = r1_board.copy(stack=False)
    after_first.push(forced_first[0])
    for reply in tuple(after_first.legal_moves):
        successor = after_first.copy(stack=False)
        successor.push(reply)
        for _ in range(4):
            for move in sorted(successor.legal_moves, key=lambda item: item.uci()):
                terminal = _execute_white_and_observe(successor, move)
                base_graph.apply_intrinsic_td(
                    successor,
                    move,
                    td_error=1.0 if terminal == "mate" else -1.0,
                    stage_diagnostic="cache_arm_test_r0",
                )
    base_graph.mature_existing_graph()
    base_graph.freeze_existing_parameters(reason="cache_arm_test")
    child_triplets = frozenset(base_graph.triplet_ids)

    base_credit = IntrinsicCreditEngine(IntrinsicCreditConfig())
    base_credit.register(R0_COMPETENCE_ID, mature=True)
    gate = OutcomeCalibratedPrototypeGate(
        feature_names=("probe",),
        offsets=(0.0,),
        scales=(1.0,),
        prototypes=((0.0,), (1.0,)),
        outcomes=(False, True),
        neighbors=1,
        threshold=0.5,
        train_metrics={},
        validation_metrics={},
        mature=True,
    )
    pools = _Pools(
        r0_train=(MATE_ONE_FEN,),
        r0_validation=(MATE_ONE_FEN,),
        r0_regression=(MATE_ONE_FEN,),
        gate_train_decoys=(),
        gate_validation_decoys=(),
        gate_regression_decoys=(),
        r1_train=(r1_fen,),
        r1_validation=(r1_fen,),
        r1_regression=(r1_fen,),
        r0_train_strata=("test",),
        r0_validation_strata=("test",),
        r0_regression_strata=("test",),
        r0_excluded_fens=(),
        r0_pool_mode="test",
        r1_train_strata=("test",),
        r1_validation_strata=("test",),
        r1_regression_strata=("test",),
        r1_pool_mode="test",
    )

    def run_arm(mode: str):
        graph = copy.deepcopy(base_graph)
        credit = copy.deepcopy(base_credit)
        config = NativeIntrinsicCurriculumConfig(
            r0_replay_per_r1_epoch=0,
            r1_validation_interval=30,
            r1_snapshot_interval=30,
            r1_mastery_threshold=2.0,
            max_samples=0,
            progress_path=str(tmp_path / f"{mode}_progress.json"),
            r1_snapshot_dir=str(tmp_path / mode),
            resume_r1_snapshots=False,
            r0_child_cache_validation_mode=mode,
        )
        result = _run_r1_arm(
            "full_intrinsic",
            graph,
            credit,
            gate,
            pools,
            r0_replay_memory=(),
            r0_child_triplet_ids=child_triplets,
            max_epochs=30,
            config=config,
        )
        return graph, credit, result

    live_graph, live_credit, live = run_arm("live_formal")
    token_graph, token_credit, token = run_arm("frozen_policy_token")

    assert live["training"]["r0_child_dispatch_cache_hit_count"] > 0
    assert token["training"]["r0_child_dispatch_cache_certified_hit_count"] == live[
        "training"
    ]["r0_child_dispatch_cache_hit_count"]
    assert token["training"]["child_handoff_count"] == live["training"][
        "child_handoff_count"
    ]
    assert token["validation"] == live["validation"]
    assert token["regression"] == live["regression"]
    assert token["r0_retention"] == live["r0_retention"]
    assert token_graph.learned_state_audit() == live_graph.learned_state_audit()
    assert token_credit.snapshot() == live_credit.snapshot()


def test_native_stem_composite_uses_graph_and_separates_correlation_from_causation() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    rows = []
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        triplet_id = graph.ensure_triplet(board, move, stage="composite_test")
        atoms = {
            node_id
            for node_id in graph.triplet_nodes[triplet_id]
            if graph.graph.nodes[node_id].meta.get("shared_feature_atom")
        }
        rows.append((move, triplet_id, atoms))

    selected = None
    for first_move, first_triplet, first_atoms in rows:
        for second_move, _second_triplet, second_atoms in rows:
            common = sorted(first_atoms & second_atoms)
            first_only = sorted(first_atoms - second_atoms)
            if first_move != second_move and common and first_only:
                selected = (
                    first_move,
                    first_triplet,
                    second_move,
                    (common[0], first_only[0]),
                )
                break
        if selected is not None:
            break
    assert selected is not None
    first_move, first_triplet, contrast_move, members = selected

    composite_id = graph.materialize_shared_composite(
        members,
        (first_triplet,),
        stage="composite_test",
    )
    cell = graph.composite_cells[composite_id]
    composite_node_id = graph.composite_node_by_triplet[(composite_id, first_triplet)]
    assert cell.state.name == "TRIAL"
    assert cell.is_composition is True
    assert tuple(cell.children) == tuple(sorted(members))
    assert graph.graph.nodes[composite_node_id].meta["confirm_policy"] == "k_of_n"
    assert graph.graph.nodes[composite_node_id].meta["confirm_k"] == 2

    graph.confirm_candidate(
        board,
        triplet_id=first_triplet,
        move_uci=first_move.uci(),
    )
    assert graph.graph.nodes[composite_node_id].state.name in {"TRUE", "CONFIRMED"}
    graph.apply_intrinsic_td(
        board,
        first_move,
        td_error=1.0,
        stage_diagnostic="composite_test",
    )
    assert cell.candidate_stats.relevance_stats.activation_count == 1
    assert cell.candidate_stats.credit_stats.positive_correlation == 1
    assert cell.candidate_stats.credit_stats.total_interventions == 0
    assert cell.candidate_stats.decision(xp=cell.xp) == "trial"

    graph.confirm_candidate(
        board,
        triplet_id=first_triplet,
        move_uci=contrast_move.uci(),
    )
    assert graph.graph.nodes[composite_node_id].state.name == "FAILED"

    graph.confirm_candidate(
        board,
        triplet_id=first_triplet,
        move_uci=first_move.uci(),
    )
    enabled_score = graph.confirm_candidate(
        board,
        triplet_id=first_triplet,
        move_uci=first_move.uci(),
    )["selected_score"]
    assert graph.graph.nodes[composite_node_id].state.name in {"TRUE", "CONFIRMED"}
    assert graph._confirmed_composite_score(first_triplet)[0] > 0.0
    heldout_state = _disable_nonmature_composites(graph, enabled=True)
    masked_trial_score = graph.confirm_candidate(
        board,
        triplet_id=first_triplet,
        move_uci=first_move.uci(),
    )["selected_score"]
    _restore_disabled_composites(graph, heldout_state)
    assert masked_trial_score is not None and masked_trial_score < enabled_score
    graph.set_composite_enabled(composite_id, enabled=False)
    disabled_score = graph.confirm_candidate(
        board,
        triplet_id=first_triplet,
        move_uci=first_move.uci(),
    )["selected_score"]
    assert enabled_score is not None and disabled_score is not None
    assert enabled_score > disabled_score

    for cycle in range(5):
        assert graph.record_composite_intervention(
            composite_id,
            enabled_return=1.0,
            disabled_return=0.0,
            cycle=cycle,
        ) == "positive"
    assert cell.candidate_stats.credit_stats.positive_intervention == 5
    assert cell.candidate_stats.decision(xp=cell.xp) == "mature"
    consolidation = graph.consolidate_composite_candidate(composite_id)
    assert consolidation["decision"] == "mature"
    assert consolidation["state"] == "MATURE"
    assert composite_id not in graph.disabled_composite_ids
    assert graph.graph.nodes[composite_node_id].meta["tier"] == "mature"

    restored = pickle.loads(pickle.dumps(graph, protocol=5))
    assert composite_id in restored.composite_cells
    assert restored.composite_member_ids[composite_id] == tuple(sorted(members))
    assert restored.to_dict()["composite_candidate_count"] == 1


def test_native_composite_proposals_are_selective_bounded_and_deterministic() -> None:
    graph = _graph()
    observed_triplets = set()
    for fen_index, fen in enumerate(R1_RETIRED_DEVELOPMENT_FENS[:4]):
        board = chess.Board(fen)
        for move_index, move in enumerate(
            sorted(board.legal_moves, key=lambda item: item.uci())
        ):
            triplet_id = graph.apply_intrinsic_td(
                board,
                move,
                td_error=1.0 if (fen_index + move_index) % 4 == 0 else -1.0,
                stage_diagnostic="proposal_test",
            )
            observed_triplets.add(triplet_id)

    first = graph.rank_shared_composite_candidates(
        observed_triplets,
        max_candidates=5,
        max_atoms_per_triplet=256,
        min_support=2,
    )
    second = graph.rank_shared_composite_candidates(
        reversed(sorted(observed_triplets)),
        max_candidates=5,
        max_atoms_per_triplet=256,
        min_support=2,
    )

    assert first
    assert first == second
    assert len(first) <= 5
    assert len({row["activation_signature_sha256"] for row in first}) == len(first)
    assert len({tuple(row["parent_triplet_ids"]) for row in first}) == len(first)
    assert {row["proposal_valence"] for row in first} == {"positive", "negative"}
    assert all(
        row["support"] < min(row["member_supports"])
        and row["candidate_generation_used_outcome_label"] is False
        and row["candidate_generation_signal"] == "native_root_edge_weight"
        for row in first
    )
    controls = graph.matched_random_shared_composite_candidates(
        observed_triplets,
        first,
        seed=20260721,
        max_atoms_per_triplet=256,
        min_support=2,
    )
    repeated_controls = graph.matched_random_shared_composite_candidates(
        reversed(sorted(observed_triplets)),
        first,
        seed=20260721,
        max_atoms_per_triplet=256,
        min_support=2,
    )
    assert controls == repeated_controls
    assert len(controls) == len(first)
    assert {row["candidate_id"] for row in controls}.isdisjoint(
        row["candidate_id"] for row in first
    )
    assert all(
        row["control_selection_used_outcome_signal"] is False
        and row["control_tie_break"] == "seeded_candidate_identity_sha256"
        for row in controls
    )
    selected = first[0]
    composite_id = graph.materialize_shared_composite(
        selected["member_atom_ids"],
        selected["parent_triplet_ids"],
        stage="proposal_test",
    )
    assert composite_id == selected["candidate_id"]
    assert graph.composite_triplets[composite_id] == set(
        selected["parent_triplet_ids"]
    )


def test_r1_structural_epoch_materializes_trial_candidates_without_causal_maturity(
    tmp_path,
    monkeypatch,
) -> None:
    def fake_rank(self, triplet_ids, **_kwargs):
        triplet_id = sorted(triplet_ids)[0]
        members = sorted(
            node_id
            for node_id in self.triplet_nodes[triplet_id]
            if self.graph.nodes[node_id].meta.get("shared_feature_atom")
        )[:2]
        assert len(members) == 2
        return (
            {
                "candidate_id": "structural_hook_test_candidate",
                "member_atom_ids": members,
                "parent_triplet_ids": [triplet_id],
                "candidate_generation_used_outcome_label": False,
                "candidate_generation_signal": "native_root_edge_weight",
            },
        )

    monkeypatch.setattr(
        NativeReConKRKGraph,
        "rank_shared_composite_candidates",
        fake_rank,
    )
    graph = _graph()
    credit = IntrinsicCreditEngine(IntrinsicCreditConfig())
    credit.register(R0_COMPETENCE_ID, mature=True)
    gate = OutcomeCalibratedPrototypeGate(
        feature_names=("probe",),
        offsets=(0.0,),
        scales=(1.0,),
        prototypes=((0.0,), (1.0,)),
        outcomes=(False, True),
        neighbors=1,
        threshold=0.5,
        train_metrics={},
        validation_metrics={},
        mature=True,
    )
    r1_fen = R1_RETIRED_DEVELOPMENT_FENS[0]
    pools = _Pools(
        r0_train=(MATE_ONE_FEN,),
        r0_validation=(MATE_ONE_FEN,),
        r0_regression=(MATE_ONE_FEN,),
        gate_train_decoys=(),
        gate_validation_decoys=(),
        gate_regression_decoys=(),
        r1_train=(r1_fen,),
        r1_validation=(r1_fen,),
        r1_regression=(r1_fen,),
        r0_train_strata=("test",),
        r0_validation_strata=("test",),
        r0_regression_strata=("test",),
        r0_excluded_fens=(),
        r0_pool_mode="test",
        r1_train_strata=("test",),
        r1_validation_strata=("test",),
        r1_regression_strata=("test",),
        r1_pool_mode="test",
    )
    config = NativeIntrinsicCurriculumConfig(
        r0_replay_per_r1_epoch=0,
        r1_validation_interval=1,
        r1_snapshot_interval=1,
        r1_mastery_threshold=2.0,
        max_samples=0,
        progress_path=str(tmp_path / "progress.json"),
        r1_snapshot_dir=str(tmp_path / "snapshots"),
        resume_r1_snapshots=False,
        r1_composite_proposal_epochs=(1,),
        r1_composite_consolidation_epochs=(1,),
        r1_composite_max_candidates=1,
    )

    result = _run_r1_arm(
        "full_intrinsic",
        graph,
        credit,
        gate,
        pools,
        r0_replay_memory=(),
        r0_child_triplet_ids=frozenset(),
        max_epochs=1,
        config=config,
    )

    assert result["training"]["composite_candidate_count"] == 1
    assert result["training"]["composite_mature_count"] == 0
    assert result["training"]["composite_causal_intervention_count"] == 1
    assert result["training"]["composition_events"][0]["new_candidate_count"] == 1
    consolidation = result["training"]["composition_consolidation_events"][0]
    assert consolidation["pool_role"] == "training_only_paired_intervention"
    assert consolidation["candidate_results"][0]["paired_neutral_count"] == 1
    assert consolidation["candidate_results"][0]["consolidation"]["decision"] == "trial"
    cell = next(iter(graph.composite_cells.values()))
    assert cell.state.name == "TRIAL"
    assert cell.candidate_stats.credit_stats.total_interventions == 1


def test_v2_training_observation_cannot_bootstrap_itself_and_duplicate_is_virtual() -> None:
    authority = _FakeV2Authority(certify_after=1)
    board = chess.Board(MATE_ONE_FEN)
    seen_predecessor_fens: set[str] = set()

    before_real = authority.continuation_digest()
    available, response, duplicate, structural = _v2_r0_observe_training_successor(
        authority,
        board,
        seen_predecessor_fens=seen_predecessor_fens,
        frame_id="v2-curriculum:first-real",
    )

    assert available is False
    assert response["classification"] == {"state": "UNKNOWN"}
    assert duplicate is False
    assert structural is None
    assert authority.next_expected_ordinal == 1
    assert authority.continuation_digest() != before_real

    after_real = authority.continuation_digest()
    now_available, virtual_response = _v2_r0_available(
        authority,
        board,
        frame_id="v2-curriculum:post-outcome-virtual",
    )
    assert now_available is True
    assert virtual_response["classification"] == {"state": "AVAILABLE"}
    assert authority.continuation_digest() == after_real

    duplicate_available, _, is_duplicate, duplicate_structural = (
        _v2_r0_observe_training_successor(
            authority,
            board,
            seen_predecessor_fens=seen_predecessor_fens,
            frame_id="v2-curriculum:duplicate",
        )
    )
    assert duplicate_available is True
    assert is_duplicate is True
    assert duplicate_structural is None
    assert authority.next_expected_ordinal == 1
    assert authority.continuation_digest() == after_real


def test_v2_virtual_availability_fails_closed_when_response_is_ungrounded() -> None:
    authority = _FakeV2Authority(certify_after=0, grounded=False)

    available, response = _v2_r0_available(
        authority,
        chess.Board(MATE_ONE_FEN),
        frame_id="v2-curriculum:ungrounded",
    )

    assert available is False
    assert response["grounded"] is False
    assert response["grounding_source"] is None

    real_available, real_response, duplicate, _structural = (
        _v2_r0_observe_training_successor(
            _FakeV2Authority(certify_after=0, grounded=False),
            chess.Board(MATE_ONE_FEN),
            seen_predecessor_fens=set(),
            frame_id="v2-curriculum:ungrounded-real",
        )
    )
    assert real_available is False
    assert duplicate is False
    assert real_response["grounded"] is False


@pytest.mark.parametrize("raw_grounded", (None, "false", 0, 1))
def test_v2_grounding_adapter_preserves_malformed_raw_value_and_fails_closed(
    raw_grounded,
) -> None:
    authority = _FakeV2Authority(certify_after=0, grounded=True)
    authority.grounded = raw_grounded
    authority.base.r0.provenance.grounded = raw_grounded

    available, response = _v2_r0_available(
        authority,
        chess.Board(MATE_ONE_FEN),
        frame_id="v2-curriculum:malformed-grounding",
    )

    assert available is False
    assert response["grounded"] is raw_grounded

    real_authority = _FakeV2Authority(certify_after=0, grounded=True)
    real_authority.base.r0.provenance.grounded = raw_grounded
    real_available, real_response, duplicate, _structural = (
        _v2_r0_observe_training_successor(
            real_authority,
            chess.Board(MATE_ONE_FEN),
            seen_predecessor_fens=set(),
            frame_id="v2-curriculum:malformed-grounding-real",
        )
    )
    assert real_available is False
    assert duplicate is False
    assert real_response["grounded"] is raw_grounded


def test_v2_duplicate_index_reads_only_fen_bearing_receipt_ledgers() -> None:
    discovery_fen = MATE_ONE_FEN
    prospective_fen = R1_RETIRED_DEVELOPMENT_FENS[0]
    authority = SimpleNamespace(
        base=SimpleNamespace(
            receipts={
                "discovery": SimpleNamespace(predecessor_fen=discovery_fen),
            }
        ),
        consumed_receipts={
            "prospective": SimpleNamespace(predecessor_fen=prospective_fen),
            "repeated": SimpleNamespace(predecessor_fen=discovery_fen),
        },
        accepted_real_references={
            key: SimpleNamespace(receipt_id=key)
            for key in ("discovery", "prospective", "repeated")
        },
    )

    assert all(
        not hasattr(reference, "predecessor_fen")
        for reference in authority.accepted_real_references.values()
    )
    assert _v2_authoritative_predecessor_fens(authority) == frozenset(
        (discovery_fen, prospective_fen)
    )


def test_new_boundary_ecology_mirrors_only_existing_prospective_history() -> None:
    def reference(
        receipt_id: str,
        ordinal: int,
        *,
        observed: bool,
        signal_id: str | None = None,
    ) -> SimpleNamespace:
        resolved_signal_id = signal_id or f"atom:{receipt_id}"
        return SimpleNamespace(
            receipt_id=receipt_id,
            ordinal=ordinal,
            stable_physical_interaction_id=f"physical:{receipt_id}",
            ordered_signal_identities=(resolved_signal_id,),
            typed_signal_roles=((resolved_signal_id, "BASE_TERMINAL"),),
            observed_outcome=observed,
        )

    discovery = reference("discovery", 3, observed=True)
    shared_signal = "atom:shared"
    first = reference(
        "prospective:first", 7, observed=False, signal_id=shared_signal
    )
    second = reference(
        "prospective:second", 5, observed=True, signal_id=shared_signal
    )
    authority = SimpleNamespace(
        base=SimpleNamespace(receipts={discovery.receipt_id: object()}),
        # Deliberately reverse chronology: initialization must canonicalize it.
        consumed_receipts={
            first.receipt_id: object(),
            second.receipt_id: object(),
        },
        accepted_real_references={
            discovery.receipt_id: discovery,
            first.receipt_id: first,
            second.receipt_id: second,
        },
        states={},
        current_generation=0,
    )

    ecology = _new_boundary_ecology_from_authority_history(
        authority,
        genome_seed=23,
    )

    assert isinstance(ecology, ProspectiveBoundaryCandidateEcology)
    assert tuple(ecology.observations) == (
        second.receipt_id,
        first.receipt_id,
    )
    assert discovery.receipt_id not in ecology.observations
    assert ecology.active_sketch_count == 0
    assert ecology.lifetime_birth_count == 0
    assert not ecology.sketches
    assert not ecology.tombstones
    assert ecology.manifest()["demands"] == []
    assert ecology.frontier_ordinal == first.ordinal
    _verify_boundary_ecology_alignment(authority, ecology, roundtrip=True)

    # The first later R1 receipt extends the exact same ledger rather than
    # opening a second history after the mirrored prefix.  Earlier receipts
    # may rank proposals, but cannot become support for the newborn sketch.
    third = reference(
        "r1:first", 8, observed=True, signal_id=shared_signal
    )
    authority.consumed_receipts[third.receipt_id] = object()
    authority.accepted_real_references[third.receipt_id] = third
    promotions, event = _boundary_ecology_step(
        authority,
        ecology,
        receipt_id=third.receipt_id,
        pre_outcome_state=AvailabilityState.UNKNOWN,
    )
    assert not promotions
    assert event["observation_receipt_id"] == third.receipt_id
    assert event["surprise_success"] is True
    assert event["born_candidate_ids"]
    prefix_ids = {first.receipt_id, second.receipt_id}
    for candidate_id in event["born_candidate_ids"]:
        candidate = ecology.sketches[candidate_id]
        assert candidate.birth_ordinal == third.ordinal
        assert candidate.triggering_receipt_id == third.receipt_id
        assert candidate.positive_receipt_ids == (third.receipt_id,)
        assert candidate.read_receipt_ids == (third.receipt_id,)
        assert candidate.lifetime_match_count == 1
        assert candidate.lifetime_support_count == 1
        assert candidate.lifetime_contradiction_count == 0
        assert prefix_ids.isdisjoint(candidate.positive_receipt_ids)
        assert prefix_ids.isdisjoint(candidate.read_receipt_ids)
    assert set(ecology.observations) == set(authority.consumed_receipts)
    _verify_boundary_ecology_alignment(authority, ecology, roundtrip=True)

    # Three later matching successes can promote the bud, but the matching
    # prefix still cannot enter its full post-birth promotion audit.
    promotions = ()
    for ordinal in range(9, 12):
        later = reference(
            f"r1:support:{ordinal}",
            ordinal,
            observed=True,
            signal_id=shared_signal,
        )
        authority.consumed_receipts[later.receipt_id] = object()
        authority.accepted_real_references[later.receipt_id] = later
        promotions, _event = _boundary_ecology_step(
            authority,
            ecology,
            receipt_id=later.receipt_id,
            pre_outcome_state=AvailabilityState.AVAILABLE,
        )
    assert len(promotions) == 1
    request = promotions[0]
    assert prefix_ids.isdisjoint(request.supporting_receipt_ids)
    assert prefix_ids.isdisjoint(request.inspected_receipt_ids)
    assert request.supporting_receipt_commitment is not None
    assert request.inspected_receipt_commitment is not None
    assert request.supporting_receipt_commitment.count == 4
    assert request.inspected_receipt_commitment.count == 4
    _verify_boundary_ecology_alignment(authority, ecology, roundtrip=True)

    missing_reference = SimpleNamespace(
        base=SimpleNamespace(receipts={}),
        consumed_receipts={"missing": object()},
        accepted_real_references={},
    )
    for continuous_evidence in (False, True):
        with pytest.raises(
            RuntimeError,
            match="lacks an accepted REAL reference",
        ):
            _new_boundary_ecology_from_authority_history(
                missing_reference,
                genome_seed=23,
                continuous_evidence=continuous_evidence,
            )
    missing_base_reference = SimpleNamespace(
        base=SimpleNamespace(receipts={"missing-base": object()}),
        consumed_receipts={},
        accepted_real_references={},
    )
    with pytest.raises(RuntimeError, match="lacks an accepted REAL reference"):
        _new_boundary_ecology_from_authority_history(
            missing_base_reference,
            genome_seed=23,
            continuous_evidence=True,
        )

    malformed = reference("malformed", 12, observed=True)
    malformed.ordinal = True
    malformed_authority = SimpleNamespace(
        base=SimpleNamespace(receipts={}),
        consumed_receipts={malformed.receipt_id: object()},
        accepted_real_references={malformed.receipt_id: malformed},
    )
    with pytest.raises(ValueError, match="non-negative integer"):
        _new_boundary_ecology_from_authority_history(
            malformed_authority,
            genome_seed=23,
        )


def test_local_action_lifetime_evidence_is_exact_and_resume_safe() -> None:
    counters: dict[str, int | float] = {}
    positive_options: set[tuple[str, str]] = set()

    def record(move, *, exposure, source, td=0.0, terminal=None, value=0.0):
        return curriculum_module._record_r1_local_action_evidence(
            {
                "pattern_id": "shared-pattern",
                "move_uci": move,
                "action_option_exposure": exposure,
                "prediction_source": source,
            },
            td_error=td,
            terminal_kind=terminal,
            successor_value=value,
            counters=counters,
            positive_credit_options=positive_options,
        )

    # A success is evidence for a later revisit, never its own revisit.
    assert not record(
        "a1a2", exposure=0, source="bounded_generalized_prior",
        td=0.5, terminal="mate",
    )
    # A sibling actuator sharing the pattern is not the credited option.
    assert not record(
        "a1a3", exposure=1, source="learned_exact_action_value",
    )
    # More than a presentation-ring length of unrelated events cannot erase
    # the positive option's report-only evidence.
    for index in range(20):
        assert not record(
            f"unrelated-{index}", exposure=0,
            source="bounded_generalized_prior", td=0.1,
        )
    counters, positive_options = pickle.loads(pickle.dumps((
        counters, positive_options,
    )))
    assert record(
        "a1a2", exposure=1, source="learned_exact_action_value",
    )
    assert positive_options == {("shared-pattern", "a1a2")}
    assert counters == {
        "local_action_first_contact_selections": 21,
        "local_action_post_contact_selections": 2,
        "local_action_exact_q_selections": 2,
        "local_action_positive_credit_revisits": 1,
    }


@pytest.mark.parametrize(
    ("v2_enabled", "selection_mode", "v27"),
    (
        (False, "scheduled", False),
        (True, "scheduled", False),
        (True, R1_ACTION_SELECTION_LOCAL_RECON, False),
        (True, R1_ACTION_SELECTION_LOCAL_RECON, True),
    ),
    ids=("legacy", "v2-scheduled", "v2-native-local", "v27-environment-local"),
)
def test_r1_interval_snapshot_resume_matches_uninterrupted(
    tmp_path, monkeypatch, v2_enabled, selection_mode, v27
) -> None:
    base_graph = _graph()
    base_credit = IntrinsicCreditEngine(IntrinsicCreditConfig())
    base_credit.register(R0_COMPETENCE_ID, mature=True)
    gate = OutcomeCalibratedPrototypeGate(
        feature_names=("probe",),
        offsets=(0.0,),
        scales=(1.0,),
        prototypes=((0.0,), (1.0,)),
        outcomes=(False, True),
        neighbors=1,
        threshold=0.5,
        train_metrics={},
        validation_metrics={},
        mature=True,
    )
    pools = _Pools(
        r0_train=(MATE_ONE_FEN,),
        r0_validation=(MATE_ONE_FEN,),
        r0_regression=(MATE_ONE_FEN,),
        gate_train_decoys=(),
        gate_validation_decoys=(),
        gate_regression_decoys=(),
        r1_train=(R1_RETIRED_DEVELOPMENT_FENS[0],),
        r1_validation=(R1_RETIRED_DEVELOPMENT_FENS[1],),
        r1_regression=(R1_RETIRED_DEVELOPMENT_FENS[2],),
        r0_train_strata=("test",),
        r0_validation_strata=("test",),
        r0_regression_strata=("test",),
        r0_excluded_fens=(),
        r0_pool_mode="test",
        r1_train_strata=("test",),
        r1_validation_strata=("test",),
        r1_regression_strata=("test",),
        r1_pool_mode="test",
    )
    common = dict(
        r0_availability_mode=(
            V2_PROSPECTIVE_AVAILABILITY
            if v2_enabled
            else "virtual_frame_verified"
        ),
        r0_replay_per_r1_epoch=0,
        r1_validation_interval=1,
        r1_snapshot_interval=1,
        r1_mastery_threshold=2.0,
        mature_child_priority=False,
        r1_action_selection_mode=selection_mode,
        r1_local_exploration_mode=("finite_local_ucb_v1" if v27 else "first_contact_then_ucb_v1"),
        r1_black_policy=("exact_mate_horizon_v1" if v27 else "learner_counterexample"),
        r1_reply_policy=("prospective_counterexample" if v27 else "sampled_round_robin"),
        r1_require_certified_finisher_for_action=not v27,
        max_samples=0,
    )
    if selection_mode == R1_ACTION_SELECTION_LOCAL_RECON:
        def forbidden_legacy_path(*_args, **_kwargs):
            raise AssertionError("retired host routing reached in native-local arm")

        for name in (
            "_scheduled_confirmed_action",
            "_choose_with_child_priority",
            "_r0_available",
            "_r0_available_with_dispatch_cache",
        ):
            monkeypatch.setattr(
                curriculum_module,
                name,
                forbidden_legacy_path,
            )
        monkeypatch.setattr(
            OutcomeCalibratedPrototypeGate,
            "confirms",
            forbidden_legacy_path,
        )
        monkeypatch.setattr(
            OutcomeCalibratedPrototypeGate,
            "probability",
            forbidden_legacy_path,
        )
    arm_gate = (
        None
        if v2_enabled and selection_mode == R1_ACTION_SELECTION_LOCAL_RECON
        else gate
    )
    uninterrupted_config = NativeIntrinsicCurriculumConfig(
        progress_path=str(tmp_path / "uninterrupted_progress.json"),
        r1_snapshot_dir=str(tmp_path / "uninterrupted"),
        resume_r1_snapshots=False,
        **common,
    )
    uninterrupted_graph = copy.deepcopy(base_graph)
    uninterrupted_credit = copy.deepcopy(base_credit)
    uninterrupted = _run_r1_arm(
        "no_bootstrap",
        uninterrupted_graph,
        uninterrupted_credit,
        arm_gate,
        pools,
        r0_replay_memory=(),
        r0_child_triplet_ids=frozenset(),
        r0_child_authority=(
            _FakeV2Authority(certify_after=1) if v2_enabled else None
        ),
        max_epochs=4,
        config=uninterrupted_config,
    )
    assert all(
        checkpoint.get("regression_withheld_from_selection") is True
        and checkpoint["r0_retention_accuracy"]
        == checkpoint["r0_validation_retention_accuracy"]
        and not any(
            key.startswith("regression_")
            and key != "regression_withheld_from_selection"
            for key in checkpoint
        )
        for checkpoint in uninterrupted["training"]["validation_checkpoints"]
    )
    assert sum(
        row["regression"] is None
        for row in uninterrupted["routing_ablation"].values()
    ) == (
        0
        if selection_mode == R1_ACTION_SELECTION_LOCAL_RECON
        else 1
    )

    resume_config = NativeIntrinsicCurriculumConfig(
        progress_path=str(tmp_path / "resume_progress.json"),
        r1_snapshot_dir=str(tmp_path / "resume"),
        resume_r1_snapshots=True,
        **common,
    )
    with pytest.raises(R1CheckpointInterrupt) as interrupted:
        _run_r1_arm(
            "no_bootstrap",
            copy.deepcopy(base_graph),
            copy.deepcopy(base_credit),
            arm_gate,
            pools,
            r0_replay_memory=(),
            r0_child_triplet_ids=frozenset(),
            r0_child_authority=(
                _FakeV2Authority(certify_after=1) if v2_enabled else None
            ),
            max_epochs=4,
            config=resume_config,
            stop_after_epoch=2,
        )
    assert interrupted.value.epoch == 2
    assert interrupted.value.snapshot_path.exists()

    resumed_graph = copy.deepcopy(base_graph)
    resumed_credit = copy.deepcopy(base_credit)
    resumed = _run_r1_arm(
        "no_bootstrap",
        resumed_graph,
        resumed_credit,
        arm_gate,
        pools,
        r0_replay_memory=(),
        r0_child_triplet_ids=frozenset(),
        r0_child_authority=(
            _FakeV2Authority(certify_after=1) if v2_enabled else None
        ),
        max_epochs=4,
        config=replace(
            resume_config,
            development_wall_ceiling_seconds=10_000.0,
            development_peak_rss_ceiling_mib=4_096.0,
        ),
    )
    assert all(
        checkpoint.get("regression_withheld_from_selection") is True
        and checkpoint["r0_retention_accuracy"]
        == checkpoint["r0_validation_retention_accuracy"]
        and not any(
            key.startswith("regression_")
            and key != "regression_withheld_from_selection"
            for key in checkpoint
        )
        for checkpoint in resumed["training"]["validation_checkpoints"]
    )

    ignored_training_keys = {
        "duration_seconds",
        "resumed_from_snapshot",
        "snapshot_path",
        "snapshot_write_count",
        "history_snapshot_paths",
    }
    assert {
        key: value
        for key, value in resumed["training"].items()
        if key not in ignored_training_keys
    } == {
        key: value
        for key, value in uninterrupted["training"].items()
        if key not in ignored_training_keys
    }
    assert resumed["validation"] == uninterrupted["validation"]
    assert resumed["regression"] == uninterrupted["regression"]
    assert resumed["r0_retention"] == uninterrupted["r0_retention"]
    assert resumed_graph.learned_state_audit() == uninterrupted_graph.learned_state_audit()
    assert resumed_graph.canonical_semantic_manifest() == (
        uninterrupted_graph.canonical_semantic_manifest()
    )
    assert resumed_credit.snapshot() == uninterrupted_credit.snapshot()
    assert resumed["training"]["resumed_from_snapshot"] is True
    if selection_mode == R1_ACTION_SELECTION_LOCAL_RECON:
        assert resumed["training"]["local_action_event_digest"] == (
            uninterrupted["training"]["local_action_event_digest"]
        )
        assert resumed["training"]["local_action_recent_events"] == (
            uninterrupted["training"]["local_action_recent_events"]
        )
        assert resumed["training"]["local_action_event_count"] > 0
        assert (
            resumed["training"]["local_action_first_contact_selection_count"]
            + resumed["training"]["local_action_post_contact_selection_count"]
        ) == resumed["training"]["local_action_event_count"]
        assert resumed["training"][
            "local_action_lifetime_evidence_is_report_only"
        ] is True
        assert all(
            event["triplet_id"] == event["credited_triplet_id"]
            for event in resumed["training"]["local_action_recent_events"]
        )
    if v2_enabled:
        assert resumed["v2_child_authority"] == uninterrupted[
            "v2_child_authority"
        ]
        assert resumed["training"]["v2_real_observation_count"] > 0
        assert resumed["training"]["availability_query_count"] > 0
        assert resumed["training"]["child_handoff_count"] == 0
    assert len(resumed["training"]["history_snapshot_paths"]) == 4
    assert all(
        Path(path).exists()
        for path in resumed["training"]["history_snapshot_paths"]
    )


_REAL_ECOLOGY_R1_FEN = (
    "8/3R4/8/8/8/2K5/8/k7 w - - 0 1"
)
_REAL_ECOLOGY_NEGATIVE_FEN = (
    "k7/8/1K6/8/8/8/8/7R w - - 0 1"
)


class _AlwaysAbstainCoreGate:
    """Synthetic local gate that leaves the V2 descendant in jurisdiction."""

    mature = True

    def confirms(self, _features) -> bool:
        return False

    def to_dict(self) -> dict[str, object]:
        return {"kind": "always_abstain_core_gate"}


def _real_ecology_authority(
    *, seed_discovery: bool = True
) -> tuple[
    NativeProspectiveAuthorityV2, frozenset[str]
]:
    """Build a tiny actual V2 authority from code-defined chess positions.

    ``seed_discovery`` retains the original historical-negative fixture for
    tests of discovery exclusion.  The no-discovery variant starts with an
    empty native envelope so the first four post-nomination REAL receipts are
    ordinals 0..3; it is used where a zero-based birth frontier is itself the
    invariant under test.
    """

    r1_board = chess.Board(_REAL_ECOLOGY_R1_FEN)
    target_rows: list[tuple[chess.Board, chess.Move, float]] = []
    # Deterministically script enough test-only actions into this synthetic
    # source graph for every selected REAL challenge to have a native graph
    # actuation.  ``_mate_moves`` is used only to construct this code-defined
    # integration fixture; it is not learner input or experimental evidence.
    for white_move in sorted(r1_board.legal_moves, key=lambda item: item.uci())[:2]:
        after_first = r1_board.copy(stack=False)
        after_first.push(white_move)
        for black_move in sorted(after_first.legal_moves, key=lambda item: item.uci()):
            successor = after_first.copy(stack=False)
            successor.push(black_move)
            mating_moves = tuple(_mate_moves(successor))
            action = (
                mating_moves[0]
                if mating_moves
                else min(successor.legal_moves, key=lambda item: item.uci())
            )
            target_rows.append((
                successor,
                action,
                1.0 if mating_moves else -1.0,
            ))

    negative_board = chess.Board(_REAL_ECOLOGY_NEGATIVE_FEN)
    negative_action = next(
        move
        for move in negative_board.legal_moves
        if _execute_white_and_observe(negative_board, move) != "mate"
    )
    graph = NativeReConKRKGraph(
        config=NativeSingleGraphConfig(
            include_symmetries=False,
            max_ticks=80,
            indexed_scheduler=True,
            key_mode="canonical",
            shared_feature_atoms=True,
            shared_projection_atoms=True,
            include_grouped_cache_terminals=False,
            score_action_pattern_atoms=True,
            terminal_score_normalization="sqrt",
        )
    )
    graph_rows = (
        (*target_rows, (negative_board, negative_action, -1.0))
        if seed_discovery
        else tuple(target_rows)
    )
    for board, action, observed_td in graph_rows:
        for _ in range(5):
            graph.apply_intrinsic_td(
                board,
                action,
                td_error=observed_td,
                stage_diagnostic="real_v2_ecology_parity",
            )
    graph.mature_existing_graph()
    graph.freeze_existing_parameters(reason="real_v2_ecology_parity")

    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(min_grounding_evidence=3)
    )
    credit.register(R0_COMPETENCE_ID, mature=True)
    state = credit.states[R0_COMPETENCE_ID]
    state.fast_value = state.slow_value = 0.8
    state.terminal_evidence = 3
    state.causal_confirmations = 1
    state.grounding_level = 0
    source_r0 = NativeR0Organism(
        graph=graph,
        credit=credit,
        provenance=FrozenCompetenceProvenance.from_credit(
            credit, R0_COMPETENCE_ID
        ),
        frozen_triplet_ids=frozenset(graph.triplet_ids),
        source_manifest={"kind": "real_v2_ecology_parity"},
    )
    source = TraceNativeCompetenceOrganism.empty(
        source_r0,
        envelope_config=CompetenceEnvelopeConfig(selection_seed=123),
        learning_config=TraceNativeLearningConfig(
            lifecycle_connected=True,
            specialization_mode=SpecializationMode.LOCAL_CONTRAST,
            genome_seed=123,
        ),
    )

    if seed_discovery:
        # A mature REFUTED parent gives the real authority a native negative
        # boundary hypothesis.  It is deliberately not prospectively
        # certified: the parity run must birth ecology candidates from later
        # observed success, never from discovery or a preloaded certification.
        frame = FrameContext(
            "real-v2-ecology:discovery",
            FrameKind.REAL,
            values={"board": negative_board},
        )
        actuation, trace = source.r0.emit_action_with_trace(frame)
        assert actuation is not None and trace is not None
        negative_successor = negative_board.copy(stack=False)
        negative_successor.push(chess.Move.from_uci(actuation.move_uci))
        assert not negative_successor.is_checkmate()
        receipt = source.completion_terminal().mint(
            trace, negative_board, negative_successor
        )
        record, inserted = source._accept_receipt(receipt)
        assert inserted
        assert source.envelope.add_unique_evidence(record)

        stem = StemCellTerminal("real_v2_ecology_refuted_parent")
        stem.state = StemCellState.MATURE
        stem.trial_node_id = stem.cell_id
        stem.trial_parent_id = "competence_available_root"
        parent = CompetenceContextCell(
            cell_id=stem.cell_id,
            members=("internal:policy_response",),
            born_round=0,
            born_request_ordinal=0,
            stem_cell=stem,
            polarity=AvailabilityState.REFUTED,
            evidence_keys=(receipt.event_id,),
            failures=1,
            support=1,
            prune_reason="real_v2_ecology_parity_negative_seed",
        )
        source.envelope.cells = {parent.cell_id: parent}
        source.envelope._member_specs = {parent.members}
        source.envelope.rebuild_graph()
    authority = NativeProspectiveAuthorityV2.from_organism(
        source,
        mode=V2Mode.PROSPECTIVE,
        specialization_mode=SpecializationMode.LOCAL_CONTRAST,
        structural_mode=StructuralMode.EVENT_DRIVEN,
        structural_epoch_schedule=(),
    )
    authority.close_nomination()
    return authority, frozenset(graph.triplet_ids)


def _real_ecology_pools() -> _Pools:
    return _Pools(
        r0_train=(_REAL_ECOLOGY_R1_FEN,),
        r0_validation=(_REAL_ECOLOGY_R1_FEN,),
        r0_regression=(_REAL_ECOLOGY_R1_FEN,),
        gate_train_decoys=(),
        gate_validation_decoys=(),
        gate_regression_decoys=(),
        r1_train=(_REAL_ECOLOGY_R1_FEN,),
        r1_validation=(_REAL_ECOLOGY_R1_FEN,),
        r1_regression=(_REAL_ECOLOGY_R1_FEN,),
        r0_train_strata=("synthetic",),
        r0_validation_strata=("synthetic",),
        r0_regression_strata=("synthetic",),
        r0_excluded_fens=(),
        r0_pool_mode="test",
        r1_train_strata=("synthetic",),
        r1_validation_strata=("synthetic",),
        r1_regression_strata=("synthetic",),
        r1_pool_mode="test",
    )


def _real_ecology_config(
    tmp_path: Path, *, resume: bool, continuous_evidence: bool = False
) -> NativeIntrinsicCurriculumConfig:
    return NativeIntrinsicCurriculumConfig(
        progress_path=str(tmp_path / "progress.json"),
        r1_snapshot_dir=str(tmp_path / "snapshots"),
        resume_r1_snapshots=resume,
        r0_replay_per_r1_epoch=0,
        r1_validation_interval=1,
        r1_snapshot_interval=1,
        r0_mastery_threshold=0.0,
        r1_mastery_threshold=2.0,
        max_samples=0,
        r0_availability_mode=V2_PROSPECTIVE_AVAILABILITY,
        r1_reply_policy=R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE,
        r0_boundary_ecology_enabled=True,
        r0_boundary_continuous_evidence=continuous_evidence,
    )


def _real_ecology_run(
    *,
    authority: NativeProspectiveAuthorityV2,
    child_triplet_ids: frozenset[str],
    pools: _Pools,
    config: NativeIntrinsicCurriculumConfig,
    gate: _AlwaysAbstainCoreGate,
    stop_after_epoch: int | None = None,
    max_epochs: int = 2,
) -> dict[str, object]:
    arm = R1MechanisticArm(
        name="test_v2_ecology",
        bootstrap_enabled=True,
        availability_mode=V2_PROSPECTIVE_AVAILABILITY,
        mature_child_priority=False,
    )
    credit = IntrinsicCreditEngine(IntrinsicCreditConfig())
    credit.register(R0_COMPETENCE_ID, mature=True)
    return _run_r1_arm(
        arm.name,
        _graph(),
        credit,
        gate,
        pools,
        r0_replay_memory=(),
        r0_child_triplet_ids=child_triplet_ids,
        max_epochs=max_epochs,
        config=config,
        arm_spec=arm,
        r0_child_authority=authority,
        r0_core_graph=authority.base.r0.graph,
        r0_core_gate=gate,
        r0_core_triplet_ids=child_triplet_ids,
        stop_after_epoch=stop_after_epoch,
    )


@pytest.mark.parametrize("continuous_evidence", [False, True])
def test_real_v2_boundary_ecology_snapshot_resume_matches_uninterrupted(
    tmp_path, continuous_evidence,
) -> None:
    """Exercise the actual event-driven V2/ecology state across a resume."""

    authority, child_triplet_ids = _real_ecology_authority()
    pools = _real_ecology_pools()
    gate = _AlwaysAbstainCoreGate()
    uninterrupted = _real_ecology_run(
        authority=authority,
        child_triplet_ids=child_triplet_ids,
        pools=pools,
        config=_real_ecology_config(
            tmp_path / "uninterrupted", resume=False,
            continuous_evidence=continuous_evidence,
        ),
        gate=gate,
    )
    with pytest.raises(R1CheckpointInterrupt) as interrupted:
        _real_ecology_run(
            authority=authority,
            child_triplet_ids=child_triplet_ids,
            pools=pools,
            config=_real_ecology_config(
                tmp_path / "resumed", resume=True,
                continuous_evidence=continuous_evidence,
            ),
            gate=gate,
            stop_after_epoch=1,
        )
    snapshot_path = interrupted.value.snapshot_path
    assert interrupted.value.epoch == 1
    assert snapshot_path.exists()
    with snapshot_path.open("rb") as handle:
        snapshot = pickle.load(handle)
    assert isinstance(snapshot["r0_child_authority_payload"], bytes)
    assert isinstance(snapshot["boundary_ecology_manifest"], dict)
    assert snapshot["boundary_ecology_manifest"]["observations"]

    resumed = _real_ecology_run(
        authority=authority,
        child_triplet_ids=child_triplet_ids,
        pools=pools,
        config=_real_ecology_config(
            tmp_path / "resumed", resume=True,
            continuous_evidence=continuous_evidence,
        ),
        gate=gate,
    )
    ignored_training_keys = {
        "duration_seconds",
        "resumed_from_snapshot",
        "snapshot_path",
        "snapshot_write_count",
        "history_snapshot_paths",
    }
    assert {
        key: value
        for key, value in resumed["training"].items()
        if key not in ignored_training_keys
    } == {
        key: value
        for key, value in uninterrupted["training"].items()
        if key not in ignored_training_keys
    }
    assert resumed["validation"] == uninterrupted["validation"]
    assert resumed["regression"] == uninterrupted["regression"]
    assert resumed["r0_retention"] == uninterrupted["r0_retention"]
    # The semantic V2 audit is exact.  Pickle byte length/hash are deliberately
    # representation-level diagnostics: a load/rebuild can change object
    # memoization without changing the signed continuation manifest.
    serialized_diagnostic_keys = {"serialized_bytes", "serialized_sha256"}
    assert {
        key: value
        for key, value in resumed["v2_child_authority"].items()
        if key not in serialized_diagnostic_keys
    } == {
        key: value
        for key, value in uninterrupted["v2_child_authority"].items()
        if key not in serialized_diagnostic_keys
    }
    uninterrupted_snapshot = pickle.loads(
        Path(uninterrupted["training"]["snapshot_path"]).read_bytes()
    )
    resumed_snapshot = pickle.loads(
        Path(resumed["training"]["snapshot_path"]).read_bytes()
    )
    assert (
        resumed_snapshot["graph"].learned_state_audit()
        == uninterrupted_snapshot["graph"].learned_state_audit()
    )
    assert (
        resumed_snapshot["graph"].canonical_semantic_manifest()
        == uninterrupted_snapshot["graph"].canonical_semantic_manifest()
    )
    assert (
        resumed_snapshot["credit"].snapshot()
        == uninterrupted_snapshot["credit"].snapshot()
    )
    assert (
        resumed_snapshot["v2_seen_predecessor_fens"]
        == uninterrupted_snapshot["v2_seen_predecessor_fens"]
    )
    uninterrupted_authority = NativeProspectiveAuthorityV2.loads(
        uninterrupted_snapshot["r0_child_authority_payload"]
    )
    resumed_authority = NativeProspectiveAuthorityV2.loads(
        resumed_snapshot["r0_child_authority_payload"]
    )
    assert (
        resumed_authority.continuation_manifest()
        == uninterrupted_authority.continuation_manifest()
    )
    assert (
        resumed_snapshot["boundary_ecology_manifest"]
        == uninterrupted_snapshot["boundary_ecology_manifest"]
    )
    assert resumed["training"]["boundary_ecology"] == uninterrupted[
        "training"
    ]["boundary_ecology"]
    assert resumed["training"]["boundary_ecology"]["observation_count"] > 0
    assert resumed["training"]["boundary_ecology"]["lifetime_birth_count"] > 0
    assert resumed["training"]["all_reply_envelope_count"] > 0
    assert resumed["training"]["all_reply_counterexample_mate_count"] > 0
    assert resumed["training"]["v2_real_observation_count"] > 0
    assert resumed["v2_child_authority"]["serialization_roundtrip_exact"] is True
    assert resumed["v2_child_authority"]["full_history_boundary_exact"] is True
    assert resumed["v2_child_authority"]["certification_discovery_leak_count"] == 0
    assert resumed["training"]["resumed_from_snapshot"] is True


@pytest.mark.parametrize("continuous_evidence", [False, True])
@pytest.mark.parametrize(
    "evaluation_function",
    ["_evaluate_r1", "_evaluate_r0", "_evaluate_frozen_native_r0_policy"],
)
def test_pending_evaluation_snapshot_resume_does_not_retrain_or_skip_verdict(
    tmp_path, monkeypatch, continuous_evidence, evaluation_function,
) -> None:
    """An unscheduled epoch-one evaluation cannot strand the settled organism."""
    authority, child_triplet_ids = _real_ecology_authority()
    pools = _real_ecology_pools()
    gate = _AlwaysAbstainCoreGate()

    def config_for(directory, *, resume):
        return replace(
            _real_ecology_config(
                directory, resume=resume, continuous_evidence=continuous_evidence,
            ),
            r1_validation_interval=4,
            r1_snapshot_interval=4,
        )

    def run(config):
        return _real_ecology_run(
            authority=authority,
            child_triplet_ids=child_triplet_ids,
            pools=pools,
            config=config,
            gate=gate,
        )

    uninterrupted = run(config_for(tmp_path / "uninterrupted", resume=False))
    interrupted_config = config_for(tmp_path / "resumed", resume=True)
    restored_composites = []
    original_restore = curriculum_module._restore_disabled_composites

    def record_restore(graph, disabled_state):
        original_restore(graph, disabled_state)
        restored_composites.append(True)

    def interrupt_evaluation(*_args, **_kwargs):
        progress = json.loads(Path(interrupted_config.progress_path).read_text())
        active = progress["active_r1_arm"]
        assert active["epoch"] == 1
        assert active["evaluation_pending"] is True
        assert active["validation_conversion_rate"] is None
        assert Path(active["snapshot_path"]).is_file()
        raise KeyboardInterrupt("synthetic interruption inside evaluation")

    with monkeypatch.context() as patch:
        patch.setattr(curriculum_module, evaluation_function, interrupt_evaluation)
        patch.setattr(curriculum_module, "_restore_disabled_composites", record_restore)
        with pytest.raises(KeyboardInterrupt, match="synthetic interruption"):
            run(interrupted_config)
    assert restored_composites == [True]

    progress = json.loads(Path(interrupted_config.progress_path).read_text())
    snapshot_path = Path(progress["active_r1_arm"]["snapshot_path"])
    pending = pickle.loads(snapshot_path.read_bytes())
    assert pending["next_epoch"] == pending["pending_evaluation_epoch"] == 1
    assert pending["counters"]["episodes"] == 1
    assert pending["checkpoints"] == []
    assert pending["history_snapshot_paths"] == []
    assert pending["joint_mastery"] is False
    assert pending["boundary_ecology_manifest"]["observations"]
    assert NativeProspectiveAuthorityV2.loads(
        pending["r0_child_authority_payload"]
    ).pending_event is None

    trained_epochs = []
    resumed_evaluations = []
    original_select = curriculum_module._select_r1_training_action
    original_evaluate = getattr(curriculum_module, evaluation_function)

    def select_once(*args, **kwargs):
        # Epochs here are zero-based. The completed first epoch must not rerun.
        assert kwargs["epoch"] == 1
        trained_epochs.append(kwargs["epoch"])
        return original_select(*args, **kwargs)

    def record_evaluation(*args, **kwargs):
        resumed_evaluations.append(len(trained_epochs))
        return original_evaluate(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(curriculum_module, "_select_r1_training_action", select_once)
        patch.setattr(curriculum_module, evaluation_function, record_evaluation)
        resumed = run(interrupted_config)
    assert trained_epochs == [1]
    assert resumed_evaluations[0] == 0  # Pending verdict precedes new experience.

    baseline_state = pickle.loads(
        Path(uninterrupted["training"]["snapshot_path"]).read_bytes()
    )
    resumed_state = pickle.loads(snapshot_path.read_bytes())
    assert resumed_state["pending_evaluation_epoch"] is None
    assert resumed_state["next_epoch"] == baseline_state["next_epoch"] == 2
    assert resumed_state["graph"].canonical_semantic_manifest() == (
        baseline_state["graph"].canonical_semantic_manifest()
    )
    assert resumed_state["credit"].snapshot() == baseline_state["credit"].snapshot()
    for key in (
        "checkpoints", "v2_seen_predecessor_fens", "boundary_ecology_manifest",
        "reply_policy_event_digest", "local_action_event_digest",
    ):
        assert resumed_state[key] == baseline_state[key]
    assert NativeProspectiveAuthorityV2.loads(
        resumed_state["r0_child_authority_payload"]
    ).continuation_manifest() == NativeProspectiveAuthorityV2.loads(
        baseline_state["r0_child_authority_payload"]
    ).continuation_manifest()
    ignored_training_keys = {
        "duration_seconds", "resumed_from_snapshot", "snapshot_path",
        "snapshot_write_count", "history_snapshot_paths",
    }
    assert {
        key: value for key, value in resumed["training"].items()
        if key not in ignored_training_keys
    } == {
        key: value for key, value in uninterrupted["training"].items()
        if key not in ignored_training_keys
    }
    for key in ("validation", "regression", "r0_retention"):
        assert resumed[key] == uninterrupted[key]
    assert len(resumed_state["history_snapshot_paths"]) == 2
    assert all(Path(path).is_file() for path in resumed_state["history_snapshot_paths"])
    final_progress = json.loads(Path(interrupted_config.progress_path).read_text())
    assert final_progress["active_r1_arm"]["evaluation_pending"] is False


def test_off_cadence_pending_evaluation_is_not_skipped_on_resume(tmp_path, monkeypatch):
    authority, child_triplet_ids = _real_ecology_authority()
    config = replace(
        _real_ecology_config(tmp_path, resume=True, continuous_evidence=True),
        r1_validation_interval=4,
        r1_snapshot_interval=4,
    )

    def run(*, stop_after_epoch=None):
        return _real_ecology_run(
            authority=authority, child_triplet_ids=child_triplet_ids,
            pools=_real_ecology_pools(), config=config,
            gate=_AlwaysAbstainCoreGate(), max_epochs=3,
            stop_after_epoch=stop_after_epoch,
        )

    original_evaluate = curriculum_module._evaluate_r1

    def interrupt_second_epoch(*args, **kwargs):
        active = json.loads(Path(config.progress_path).read_text())["active_r1_arm"]
        if active["epoch"] == 2:
            raise KeyboardInterrupt("off-cadence pending evaluation")
        return original_evaluate(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(curriculum_module, "_evaluate_r1", interrupt_second_epoch)
        with pytest.raises(KeyboardInterrupt, match="off-cadence"):
            run(stop_after_epoch=2)
    progress = json.loads(Path(config.progress_path).read_text())
    snapshot_path = Path(progress["active_r1_arm"]["snapshot_path"])
    pending = pickle.loads(snapshot_path.read_bytes())
    assert pending["next_epoch"] == pending["pending_evaluation_epoch"] == 2
    assert [row["epoch"] for row in pending["checkpoints"]] == [1]

    trained_epochs = []
    evaluation_order = []
    original_select = curriculum_module._select_r1_training_action

    def record_select(*args, **kwargs):
        trained_epochs.append(kwargs["epoch"])
        return original_select(*args, **kwargs)

    def record_evaluate(*args, **kwargs):
        active = json.loads(Path(config.progress_path).read_text())["active_r1_arm"]
        evaluation_order.append((active["epoch"], len(trained_epochs)))
        return original_evaluate(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(curriculum_module, "_select_r1_training_action", record_select)
        patch.setattr(curriculum_module, "_evaluate_r1", record_evaluate)
        resumed = run()  # No longer requesting the diagnostic epoch-two stop.
    assert evaluation_order[0] == (2, 0)
    assert trained_epochs == [2]
    assert resumed["training"]["episodes"] == 3
    assert [
        row["epoch"] for row in resumed["training"]["validation_checkpoints"]
    ] == [1, 2, 3]


def test_atomic_epoch_snapshot_failure_preserves_prior_checkpoint(tmp_path, monkeypatch):
    path = tmp_path / "organism.pkl"
    previous = {"next_epoch": 1, "pending_evaluation_epoch": None}
    curriculum_module._atomic_pickle(path, previous)
    previous_bytes = path.read_bytes()

    def failed_dump(_payload, handle, **_kwargs):
        handle.write(b"partial pickle")
        raise OSError("synthetic disk write failure")

    monkeypatch.setattr(curriculum_module.pickle, "dump", failed_dump)
    with pytest.raises(OSError, match="synthetic disk write failure"):
        curriculum_module._atomic_pickle(path, {"next_epoch": 2})
    assert path.read_bytes() == previous_bytes
    assert pickle.loads(path.read_bytes()) == previous


def test_r1_production_uses_event_local_structural_settlement(
    tmp_path, monkeypatch
) -> None:
    """Production R1 never queues boundary promotions until an epoch end."""

    authority, child_triplet_ids = _real_ecology_authority(
        seed_discovery=False
    )
    calls: list[object] = []
    frame_events: list[object | None] = []
    real_events: list[bool] = []
    settlement_events: list[tuple[object, object | None]] = []
    original = curriculum_module._v2_r0_observe_training_successor
    original_settle = curriculum_module._settle_event_local_v2_boundary

    def observe(*args, **kwargs):
        # A fresh per-decision set is the deferred production mode.  In
        # particular, a per-epoch set must not be reused across interactions.
        calls.append(kwargs.get("pending_boundary_candidate_ids"))
        result = original(*args, **kwargs)
        frame_events.append(kwargs.get("frame_session"))
        real_events.append(not result[2])
        return result

    def settle(authority_arg, ecology_arg, pending_arg):
        result = original_settle(authority_arg, ecology_arg, pending_arg)
        settlement_events.append((pending_arg, result))
        return result

    monkeypatch.setattr(
        curriculum_module,
        "_v2_r0_observe_training_successor",
        observe,
    )

    # Hold the environment-facing action fixed so this mechanism test feeds
    # the same positive, code-defined shell on every first move.  The
    # production selector remains untouched; only the structural settlement
    # ordering is under test here.
    def select_positive_action(graph, board, **_kwargs):
        return (*curriculum_module._scheduled_confirmed_action(
            graph,
            board,
            schedule_index=0,
            stage_diagnostic="R1_mate_in_2",
            action_order=(
                curriculum_module.R1_ACTION_ORDER_LEGACY_LEXICOGRAPHIC
            ),
        ), None)

    monkeypatch.setattr(
        curriculum_module,
        "_select_r1_training_action",
        select_positive_action,
    )
    monkeypatch.setattr(
        curriculum_module,
        "_settle_event_local_v2_boundary",
        settle,
    )

    def forbidden_settlement(_ecology):
        raise AssertionError(
            "production R1 must not call epoch/event settle_refinements"
        )

    monkeypatch.setattr(
        ProspectiveBoundaryCandidateEcology,
        "settle_refinements",
        forbidden_settlement,
    )
    base = chess.Board(_REAL_ECOLOGY_R1_FEN)
    stream_fens = []
    for index in range(8):
        board = base.copy(stack=False)
        board.fullmove_number = 400 + index
        stream_fens.append(board.fen())
    result = _real_ecology_run(
        authority=authority,
        child_triplet_ids=child_triplet_ids,
        pools=replace(
            _real_ecology_pools(),
            r1_train=tuple(stream_fens),
            r1_train_strata=tuple("synthetic" for _ in stream_fens),
        ),
        config=_real_ecology_config(tmp_path, resume=False),
        gate=_AlwaysAbstainCoreGate(),
    )

    assert calls
    assert all(isinstance(value, set) for value in calls)
    assert len({id(value) for value in calls}) == len(calls)
    real_indices = [index for index, is_real in enumerate(real_events) if is_real]
    assert settlement_events
    assert len(settlement_events) == len(real_indices)
    assert all(
        pending is calls[real_indices[index]]
        for index, (pending, _structural) in enumerate(settlement_events)
    )
    transition_index = next(
        index
        for index, (_pending, structural) in enumerate(settlement_events)
        if structural is not None
    )
    # The first four events share one frozen-R0 frame session.  The event-local
    # structural commit then closes it; the next event must execute in a fresh
    # session.  This is the only permitted refresh trigger within the epoch.
    assert transition_index >= 1
    assert all(
        frame_events[real_indices[index]] is frame_events[real_indices[0]]
        for index in range(transition_index + 1)
    )
    assert frame_events[real_indices[transition_index + 1]] is not frame_events[
        real_indices[transition_index]
    ]
    assert result["training"]["v2_structural_transition_count"] >= 1


def test_strict_reply_frame_identity_ignores_epoch_and_position_labels():
    """Chunking/presentation labels cannot change a strict REAL stream."""

    def run(label_offset: int):
        authority, _child_triplet_ids = _real_ecology_authority()
        ecology = ProspectiveBoundaryCandidateEcology()
        seen: set[str] = set()
        exposures: dict[tuple[str, str, str], int] = {}
        counters = {
            **curriculum_module._r1_reply_counter_defaults(),
            "episodes": 0,
            "child_handoffs": 0,
            "availability_queries": 0,
            "availability_positives": 0,
            "virtual_frame_queries": 0,
            "v2_duplicate_virtual_queries": 0,
            "v2_real_observations": 0,
            "v2_structural_transitions": 0,
        }
        stream = []
        base = chess.Board(_REAL_ECOLOGY_R1_FEN)
        for index in range(4):
            board = base.copy(stack=False)
            board.fullmove_number = 200 + index
            move = min(board.legal_moves, key=lambda item: item.uci())
            after_first = board.copy(stack=False)
            after_first.push(move)
            terminal_kind, successor_ids, audit = (
                curriculum_module._prospective_counterexample_episode(
                    authority,
                    after_first,
                    fen=board.fen(),
                    white_move_uci=move.uci(),
                    arm_name="strict-frame-identity",
                    epoch=label_offset + index * 7,
                    position_index=label_offset + index * 11,
                    exposure_counts=exposures,
                    seen_predecessor_fens=seen,
                    frame_session=None,
                    generic_seed=17,
                    arm_bootstrap_enabled=True,
                    counters=counters,
                    strict_adaptive=True,
                    boundary_ecology=ecology,
                )
            )
            stream.append((
                terminal_kind,
                successor_ids,
                authority.continuation_manifest(),
                ecology.manifest(),
            ))
            counters["episodes"] += 1
        return tuple(stream)

    first = run(0)
    relabeled = run(1000)
    assert first == relabeled
    assert first[-1][2]["accepted_real_references"]
    assert first[-1][3]["observations"]


@pytest.mark.parametrize("continuous_evidence", [False, True])
def test_production_real_stream_promotes_before_postbirth_certification(
    continuous_evidence,
):
    """Physical promotion must preserve exactly the opted-in evidence clock.

    This is a code-defined mechanism fixture, not evidence of generalization:
    it repeats a tiny geometry with distinct physical interaction identities.
    """

    authority, _child_triplet_ids = _real_ecology_authority(
        seed_discovery=False
    )
    ecology = curriculum_module._new_boundary_ecology_from_authority_history(
        authority,
        genome_seed=curriculum_module.BoundaryEcologyConfig().genome_seed,
        continuous_evidence=continuous_evidence,
    )
    seen: set[str] = set()
    exposures: dict[tuple[str, str, str], int] = {}
    counters = {
        **curriculum_module._r1_reply_counter_defaults(),
        "episodes": 0,
        "child_handoffs": 0,
        "availability_queries": 0,
        "availability_positives": 0,
        "virtual_frame_queries": 0,
        "v2_duplicate_virtual_queries": 0,
        "v2_real_observations": 0,
        "v2_structural_transitions": 0,
    }
    base = chess.Board(_REAL_ECOLOGY_R1_FEN)
    child_id: str | None = None
    birth_exclusion_ids: tuple[str, ...] = ()
    birth_exclusion_digest: str | None = None
    birth_exclusion_frontier: int | None = None
    certification_event_count = 5 if continuous_evidence else 8
    semantic_birth = 0 if continuous_evidence else 3
    for index in range(certification_event_count):
        board = base.copy(stack=False)
        board.fullmove_number = 300 + index
        move = min(board.legal_moves, key=lambda item: item.uci())
        after_first = board.copy(stack=False)
        after_first.push(move)
        terminal_kind, successor_ids, audit = (
            curriculum_module._prospective_counterexample_episode(
                authority,
                after_first,
                fen=board.fen(),
                white_move_uci=move.uci(),
                arm_name="production-stream-gate",
                # All eight interactions belong to one logical epoch.
                epoch=0,
                position_index=index,
                exposure_counts=exposures,
                seen_predecessor_fens=seen,
                frame_session=None,
                generic_seed=17,
                arm_bootstrap_enabled=True,
                counters=counters,
                strict_adaptive=True,
                boundary_ecology=ecology,
            )
        )
        assert terminal_kind == "mate"
        assert successor_ids == ()
        assert audit["successor_signal"] is None
        structural = audit["structural"]
        if continuous_evidence:
            if index < 4:
                assert structural is None
            else:
                assert structural is not None
                assert len(structural["child_ids"]) == 1
                child_id = structural["child_ids"][0]
                child = authority.states[child_id]
                assert child.hypothesis.birth_frontier == 0
                assert child.hypothesis.materialization_frontier == 4
                assert child.support == 4
                assert child.prospectively_certified is True
                exclusion = child.hypothesis.discovery_exclusion_commitment
                assert exclusion is not None
                assert exclusion.count == 1
                assert exclusion.exclusive_frontier == 1
                birth_exclusion_ids = exclusion.witness_ids
                birth_exclusion_digest = exclusion.digest
                birth_exclusion_frontier = exclusion.exclusive_frontier
                assert len(child.certification_receipt_ids) == 4
                assert all(
                    authority.accepted_real_references[item].ordinal > 0
                    for item in child.certification_receipt_ids
                )
        elif index < 3:
            assert structural is None
        elif index == 3:
            assert structural is not None
            assert len(structural["promotion_candidate_ids"]) == 1
            assert len(structural["child_ids"]) == 1
            child_id = structural["child_ids"][0]
            child = authority.states[child_id]
            assert child.hypothesis.birth_frontier == 3
            birth_exclusion_ids = tuple(
                sorted(authority.accepted_real_references)
            )
            assert len(birth_exclusion_ids) == 4
            assert all(
                authority.accepted_real_references[item].ordinal <= 3
                for item in birth_exclusion_ids
            )
            exclusion = child.hypothesis.discovery_exclusion_commitment
            assert exclusion is not None
            birth_exclusion_digest = exclusion.digest
            birth_exclusion_frontier = exclusion.exclusive_frontier
            assert exclusion.count == 4
            assert exclusion.exclusive_frontier == 4
            assert set(exclusion.witness_ids) == set(birth_exclusion_ids)
            assert set(child.hypothesis.discovery_exclusion_receipt_ids) == set(
                birth_exclusion_ids
            )
            assert child.support == 0
            assert child.prospectively_certified is False
            assert child.certification_receipt_ids == ()
        else:
            assert child_id is not None
            child = authority.states[child_id]
            assert child.support == index - 3
            assert child.prospectively_certified is (index == 7)
            if index < 7:
                # Receipt IDs are retained as the child's prospective
                # evidence ledger before the threshold is reached; the
                # certification bit, not an empty ledger, is the gate.
                assert len(child.certification_receipt_ids) == index - 3

        counters["episodes"] += 1

    assert child_id is not None
    child = authority.states[child_id]
    assert child.support == 4
    assert child.prospectively_certified is True
    # The event that supplied the fourth post-birth receipt could not use its
    # own newly certified child as a pre-outcome successor.
    certification_ids = tuple(child.certification_receipt_ids)
    assert certification_ids
    assert set(certification_ids).isdisjoint(birth_exclusion_ids)
    assert all(
        authority.accepted_real_references[item].ordinal > semantic_birth
        for item in certification_ids
    )
    assert birth_exclusion_digest is not None
    assert birth_exclusion_frontier == semantic_birth + 1
    # This verifies both chronological replay paths, including the distinct
    # semantic-birth and graph-materialization frontiers in continuous mode.
    authority.verify_full_history_boundary("continuous_evidence_chess_canary")
    restored_authority = NativeProspectiveAuthorityV2.loads(authority.dumps())
    assert restored_authority.continuation_manifest() == authority.continuation_manifest()
    curriculum_module._verify_boundary_ecology_alignment(
        authority, ecology, roundtrip=True
    )
    lineage = curriculum_module._adaptive_positive_lineage_audit(authority, ecology)
    assert lineage["certification_leak_count"] == 0
    assert lineage["certified_node_count"] == 1

    # The ninth unique REAL interaction is the first one allowed to expose
    # the now-certified shell.  It is deliberately outside the four-event
    # discovery prefix and carries a fresh persisted interaction ordinal.
    credit = IntrinsicCreditEngine(IntrinsicCreditConfig())
    decision_id = "r1:ninth-postbirth-decision"
    credit.register(decision_id, hierarchy_depth=1)
    board = base.copy(stack=False)
    board.fullmove_number = 300 + certification_event_count
    move = min(board.legal_moves, key=lambda item: item.uci())
    after_first = board.copy(stack=False)
    after_first.push(move)
    _terminal_kind, successor_ids, ninth_audit = (
        curriculum_module._prospective_counterexample_episode(
            authority,
            after_first,
            credit=credit,
            decision_id=decision_id,
            fen=board.fen(),
            white_move_uci=move.uci(),
            arm_name="production-stream-gate",
            epoch=999,
            position_index=999,
            exposure_counts=exposures,
            seen_predecessor_fens=seen,
            frame_session=None,
            generic_seed=17,
            arm_bootstrap_enabled=True,
            counters=counters,
            strict_adaptive=True,
            boundary_ecology=ecology,
        )
    )
    assert counters["episodes"] == certification_event_count
    assert ninth_audit["manifest"]["real_event"] is True
    assert authority.next_expected_ordinal == certification_event_count + 1

    # This fixture has one legal opponent reply.  Its already-certified shell
    # must close the actual strict envelope and carry value to the first move;
    # a raw AVAILABLE classification without a valid provider is not enough.
    signal = ninth_audit["successor_signal"]
    assert signal is not None
    assert signal.provider_ids == successor_ids
    assert child_id in signal.provider_ids
    assert signal.value > 0.0
    assert counters["child_handoffs"] == 1
    assert ninth_audit["manifest"]["positive_handoff"] is True
    assert len(ninth_audit["manifest"]["reply_ids"]) == 1
    credit.begin_episode()
    credited = credit.transition(
        decision_id,
        explicit_successor_signal=signal,
        external_provider_records=ninth_audit["external_provider_records"],
        external_provider_resolver=authority.native_provider_response,
        prediction_override=0.0,
    )
    assert credited.successor_value == pytest.approx(signal.value)
    assert credited.td_error > 0.0

    # A later VIRTUAL query may expose the same capability but cannot add
    # certification evidence.  The preceding assertions used only the
    # provider captured before the ninth REAL observation, not this query.
    selected_black = chess.Move.from_uci(
        ninth_audit["manifest"]["selected_black_move"]
    )
    ninth_successor = after_first.copy(stack=False)
    ninth_successor.push(selected_black)
    available, availability_response = curriculum_module._v2_r0_available(
        authority,
        ninth_successor,
        frame_id="production-stream-gate:ninth:virtual-capability",
    )
    assert available is True
    assert availability_response["classification"]["state"] == "available"
    provenance = availability_response["availability_provenance"]
    assert child_id in provenance["matching_certified_cell_ids"]
    assert (
        provenance["certification_provenance"][child_id][
            "prospectively_certified"
        ]
        is True
    )
    assert provenance["certification_evidence_added"] == 0
    assert all(
        authority.accepted_real_references[item].ordinal > semantic_birth
        for item in certification_ids
    )


def test_mastered_snapshot_resume_is_report_only_and_does_not_retrain(
    tmp_path, monkeypatch
) -> None:
    """A committed mastery snapshot resumes without an extra epoch.

    The validation interval intentionally does not divide the epoch budget;
    the first epoch is still a valid observation because the runner always
    observes epoch zero.  On resume, no current-checkpoint variable or epoch
    body may be required.
    """

    base_graph = _graph()
    base_credit = IntrinsicCreditEngine(IntrinsicCreditConfig())
    base_credit.register(R0_COMPETENCE_ID, mature=True)
    gate = OutcomeCalibratedPrototypeGate(
        feature_names=("probe",),
        offsets=(0.0,),
        scales=(1.0,),
        prototypes=((0.0,), (1.0,)),
        outcomes=(False, True),
        neighbors=1,
        threshold=0.5,
        train_metrics={},
        validation_metrics={},
        mature=True,
    )
    r1_fen = R1_RETIRED_DEVELOPMENT_FENS[0]
    pools = _Pools(
        r0_train=(MATE_ONE_FEN,),
        r0_validation=(MATE_ONE_FEN,),
        r0_regression=(MATE_ONE_FEN,),
        gate_train_decoys=(),
        gate_validation_decoys=(),
        gate_regression_decoys=(),
        r1_train=(r1_fen,),
        r1_validation=(r1_fen,),
        r1_regression=(r1_fen,),
        r0_train_strata=("test",),
        r0_validation_strata=("test",),
        r0_regression_strata=("test",),
        r0_excluded_fens=(),
        r0_pool_mode="test",
        r1_train_strata=("test",),
        r1_validation_strata=("test",),
        r1_regression_strata=("test",),
        r1_pool_mode="test",
    )
    common = dict(
        r0_replay_per_r1_epoch=0,
        r1_validation_interval=3,
        r1_snapshot_interval=1,
        r1_mastery_threshold=0.0,
        r0_mastery_threshold=0.0,
        mature_child_priority=False,
        max_samples=0,
    )
    uninterrupted_config = NativeIntrinsicCurriculumConfig(
        progress_path=str(tmp_path / "uninterrupted_progress.json"),
        r1_snapshot_dir=str(tmp_path / "uninterrupted"),
        resume_r1_snapshots=False,
        **common,
    )
    uninterrupted_graph = copy.deepcopy(base_graph)
    uninterrupted_credit = copy.deepcopy(base_credit)
    uninterrupted = _run_r1_arm(
        "full_intrinsic",
        uninterrupted_graph,
        uninterrupted_credit,
        gate,
        pools,
        r0_replay_memory=(),
        r0_child_triplet_ids=frozenset(),
        max_epochs=4,
        config=uninterrupted_config,
    )
    assert uninterrupted["training"]["joint_mastery"] is True
    assert uninterrupted["training"]["stopped_epoch"] == 1
    assert len(uninterrupted["training"]["validation_checkpoints"]) == 1

    resume_config = NativeIntrinsicCurriculumConfig(
        progress_path=str(tmp_path / "resume_progress.json"),
        r1_snapshot_dir=str(tmp_path / "resume"),
        resume_r1_snapshots=True,
        **common,
    )
    with pytest.raises(R1CheckpointInterrupt) as interrupted:
        _run_r1_arm(
            "full_intrinsic",
            copy.deepcopy(base_graph),
            copy.deepcopy(base_credit),
            gate,
            pools,
            r0_replay_memory=(),
            r0_child_triplet_ids=frozenset(),
            max_epochs=4,
            config=resume_config,
            stop_after_epoch=1,
        )
    assert interrupted.value.epoch == 1

    def no_extra_training(*_args, **_kwargs):
        raise AssertionError("mastered snapshot resumed an extra training epoch")

    monkeypatch.setattr(
        "recon_lite_chess.autogrowth.native_intrinsic_curriculum._scheduled_confirmed_action",
        no_extra_training,
    )
    resumed_graph = copy.deepcopy(base_graph)
    resumed_credit = copy.deepcopy(base_credit)
    resumed = _run_r1_arm(
        "full_intrinsic",
        resumed_graph,
        resumed_credit,
        gate,
        pools,
        r0_replay_memory=(),
        r0_child_triplet_ids=frozenset(),
        max_epochs=4,
        config=resume_config,
    )

    assert resumed["training"]["resumed_from_snapshot"] is True
    assert resumed["training"]["resumed_from_mastered_snapshot"] is True
    assert resumed["training"]["episodes"] == uninterrupted["training"]["episodes"]
    for key in (
        "child_handoff_count",
        "availability_query_count",
        "availability_positive_count",
        "successor_value_sum",
        "r0_replay_episode_count",
        "formal_confirmation_failure_count",
    ):
        assert resumed["training"][key] == uninterrupted["training"][key]
    assert resumed["training"]["validation_checkpoints"] == uninterrupted[
        "training"
    ]["validation_checkpoints"]
    assert resumed["validation"] == uninterrupted["validation"]
    assert resumed["regression"] == uninterrupted["regression"]
    assert resumed["r0_validation_retention"] == uninterrupted[
        "r0_validation_retention"
    ]
    assert resumed["r0_regression_retention"] == uninterrupted[
        "r0_regression_retention"
    ]
    assert resumed_graph.learned_state_audit() == uninterrupted_graph.learned_state_audit()
    assert resumed_graph.canonical_semantic_manifest() == (
        uninterrupted_graph.canonical_semantic_manifest()
    )
    assert resumed_credit.snapshot() == uninterrupted_credit.snapshot()


def test_r1_snapshot_fingerprint_ignores_only_operational_controls(tmp_path) -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    graph.ensure_triplet(
        board,
        min(board.legal_moves, key=lambda item: item.uci()),
        stage="fingerprint_test",
    )
    r0_triplets = frozenset(graph.triplet_ids)
    graph.freeze_existing_parameters(reason="fingerprint_test")
    credit = IntrinsicCreditEngine(IntrinsicCreditConfig())
    credit.register(R0_COMPETENCE_ID, mature=True)
    gate = OutcomeCalibratedPrototypeGate(
        feature_names=("probe",),
        offsets=(0.0,),
        scales=(1.0,),
        prototypes=((0.0,), (1.0,)),
        outcomes=(False, True),
        neighbors=1,
        threshold=0.5,
        train_metrics={},
        validation_metrics={},
        mature=True,
    )
    pools = _Pools(
        r0_train=(MATE_ONE_FEN,),
        r0_validation=(MATE_ONE_FEN,),
        r0_regression=(MATE_ONE_FEN,),
        gate_train_decoys=(),
        gate_validation_decoys=(),
        gate_regression_decoys=(),
        r1_train=(R1_RETIRED_DEVELOPMENT_FENS[0],),
        r1_validation=(R1_RETIRED_DEVELOPMENT_FENS[1],),
        r1_regression=(R1_RETIRED_DEVELOPMENT_FENS[2],),
        r0_train_strata=("test",),
        r0_validation_strata=("test",),
        r0_regression_strata=("test",),
        r0_excluded_fens=(),
        r0_pool_mode="test",
        r1_train_strata=("test",),
        r1_validation_strata=("test",),
        r1_regression_strata=("test",),
        r1_pool_mode="test",
    )
    arm = R1MechanisticArm(name="no_bootstrap", bootstrap_enabled=False)
    config = NativeIntrinsicCurriculumConfig(
        output_path=str(tmp_path / "one" / "result.json"),
        progress_path=str(tmp_path / "one" / "progress.json"),
        r1_snapshot_dir=str(tmp_path / "one" / "snapshots"),
        resume_r1_snapshots=False,
        r1_keep_checkpoint_history=True,
        max_samples=1,
        development_wall_ceiling_seconds=1.0,
        development_peak_rss_ceiling_mib=512.0,
    )

    def fingerprint(candidate: NativeIntrinsicCurriculumConfig) -> str:
        return _r1_snapshot_fingerprint(
            graph,
            credit,
            gate,
            pools,
            arm_name=arm.name,
            arm_spec=arm,
            r0_child_triplet_ids=r0_triplets,
            r0_child_authority_digest="authority-digest",
            config=candidate,
        )

    operationally_changed = replace(
        config,
        output_path=str(tmp_path / "two" / "result.json"),
        progress_path=str(tmp_path / "two" / "progress.json"),
        r1_snapshot_dir=str(tmp_path / "two" / "snapshots"),
        resume_r1_snapshots=True,
        r1_keep_checkpoint_history=False,
        max_samples=0,
        development_wall_ceiling_seconds=7_200.0,
        development_peak_rss_ceiling_mib=8_192.0,
    )
    assert fingerprint(operationally_changed) == fingerprint(config)
    strict_no_gate = _r1_snapshot_fingerprint(
        graph,
        credit,
        None,
        pools,
        arm_name=arm.name,
        arm_spec=arm,
        r0_child_triplet_ids=r0_triplets,
        r0_child_authority_digest="authority-digest",
        config=replace(
            config,
            r0_action_selection_mode=R1_ACTION_SELECTION_LOCAL_RECON,
            r1_action_selection_mode=R1_ACTION_SELECTION_LOCAL_RECON,
            validation_controls_stage_transitions=False,
        ),
    )
    assert isinstance(strict_no_gate, str) and len(strict_no_gate) == 64
    assert strict_no_gate != fingerprint(config)
    assert fingerprint(replace(config, eta_m3=config.eta_m3 / 2.0)) != fingerprint(
        config
    )
    before_metadata_change = fingerprint(config)
    action_node = next(
        node for node in graph.graph.nodes.values()
        if "action_uci" in node.meta
    )
    original_action = str(action_node.meta["action_uci"])
    action_node.meta["action_uci"] = (
        "a1a2" if original_action != "a1a2" else "a1a3"
    )
    after_metadata_change = fingerprint(config)
    assert after_metadata_change != before_metadata_change
    triplet_id = min(graph.triplet_ids)
    graph.triplet_pattern_key_cache[triplet_id] = {
        "resume-cache-sensitivity"
    }
    after_cache_change = fingerprint(config)
    assert after_cache_change != after_metadata_change
    credit.event_index += 1
    assert fingerprint(config) != after_cache_change


def test_r1_base_state_identity_is_hash_seed_stable() -> None:
    script = textwrap.dedent(
        """
        import hashlib
        import json
        import chess

        from recon_lite_hector.learning import IntrinsicCreditConfig, IntrinsicCreditEngine
        from recon_lite_chess.autogrowth.native_intrinsic_curriculum import (
            R0_COMPETENCE_ID,
            _r1_base_state_identity,
        )
        from recon_lite_chess.autogrowth.native_single_graph_curriculum import (
            NativeReConKRKGraph,
            NativeSingleGraphConfig,
        )

        graph = NativeReConKRKGraph(config=NativeSingleGraphConfig(
            include_symmetries=False,
            key_mode="canonical",
            shared_feature_atoms=True,
            shared_projection_atoms=True,
            include_grouped_cache_terminals=False,
        ))
        board = chess.Board("k7/8/1K6/8/8/8/8/7R w - - 0 1")
        for move in sorted(board.legal_moves, key=lambda item: item.uci())[:4]:
            graph.ensure_triplet(board, move, stage="hash_seed_test")
        triplets = frozenset(graph.triplet_ids)
        graph.freeze_existing_parameters(reason="hash_seed_test")
        credit = IntrinsicCreditEngine(IntrinsicCreditConfig())
        credit.register(R0_COMPETENCE_ID, mature=True)
        credit.states[R0_COMPETENCE_ID].grounding_ancestors = {
            "ancestor-a", "ancestor-b", "ancestor-c", "ancestor-d"
        }
        manifest = _r1_base_state_identity(graph, credit, triplets)
        encoded = json.dumps(
            manifest, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
        print(hashlib.sha256(encoded).hexdigest())
        """
    )
    pythonpath = os.pathsep.join(
        filter(
            None,
            (
                str(Path.cwd() / "src"),
                str(Path.cwd() / "libs" / "recon-lite" / "src"),
                os.environ.get("PYTHONPATH"),
            ),
        )
    )
    digests = []
    for seed in ("1", "2"):
        environment = dict(os.environ)
        environment.update(PYTHONHASHSEED=seed, PYTHONPATH=pythonpath)
        result = subprocess.run(
            (sys.executable, "-c", script),
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        )
        digests.append(result.stdout.strip())

    assert len(set(digests)) == 1


def test_balanced_r1_quotas_cover_all_setup_and_orientation_strata() -> None:
    quotas = _balanced_r1_quotas(16)

    assert tuple(quotas) == R1_BALANCED_STRATA
    assert sum(quotas.values()) == 16
    assert all(
        quotas[f"rook_barrier:{side}"] == 2
        for side in ("left", "right", "bottom", "top")
    )
    assert all(
        quotas[f"king_edge:{side}"] == 1
        for side in ("left", "right", "bottom", "top")
    )
    assert all(
        quotas[f"king_corner:{corner}"] == 1
        for corner in ("a1", "a8", "h1", "h8")
    )
    with pytest.raises(ValueError):
        _balanced_r1_quotas(12)


def test_balanced_r0_splits_cover_all_locations_and_are_orbit_disjoint() -> None:
    used_fens: set[str] = set()
    used_orbits: set[str] = set()
    train, train_labels = _generate_balanced_r0_split(
        count=16,
        seed=20260719,
        used_fens=used_fens,
        used_orbits=used_orbits,
        max_attempts=300_000,
    )
    heldout, heldout_labels = _generate_balanced_r0_split(
        count=8,
        seed=20260720,
        used_fens=used_fens,
        used_orbits=used_orbits,
        max_attempts=300_000,
    )

    assert tuple(_balanced_r0_quotas(8)) == R0_BALANCED_STRATA
    assert Counter(train_labels) == Counter(_balanced_r0_quotas(16))
    assert Counter(heldout_labels) == Counter(_balanced_r0_quotas(8))
    generated_orbits = [_r1_orbit_key(fen) for fen in (*train, *heldout)]
    assert len(generated_orbits) == len(set(generated_orbits))
    for fen, label in zip(
        (*train, *heldout), (*train_labels, *heldout_labels), strict=True
    ):
        board = chess.Board(fen)
        assert _mate_moves(board)
        assert _classify_r0_stratum(board) == label
    with pytest.raises(ValueError):
        _balanced_r0_quotas(12)


def test_balanced_r1_splits_are_stratified_and_orbit_disjoint() -> None:
    used_fens: set[str] = set()
    retired_orbits = {_r1_orbit_key(fen) for fen in R1_RETIRED_DEVELOPMENT_FENS}
    used_orbits = set(retired_orbits)

    train, train_labels = _generate_balanced_r1_split(
        count=16,
        seed=20260718,
        used_fens=used_fens,
        used_orbits=used_orbits,
        max_attempts=300_000,
    )
    heldout, heldout_labels = _generate_balanced_r1_split(
        count=16,
        seed=20260719,
        used_fens=used_fens,
        used_orbits=used_orbits,
        max_attempts=300_000,
    )

    assert Counter(train_labels) == Counter(_balanced_r1_quotas(16))
    assert Counter(heldout_labels) == Counter(_balanced_r1_quotas(16))
    assert set(train).isdisjoint(heldout)
    generated_orbits = [_r1_orbit_key(fen) for fen in (*train, *heldout)]
    assert len(generated_orbits) == len(set(generated_orbits))
    assert not retired_orbits.intersection(generated_orbits)

    for fen, label in zip((*train, *heldout), (*train_labels, *heldout_labels), strict=True):
        board = chess.Board(fen)
        forced = tuple(_forced_mate_in_two_first_moves(board))
        assert forced
        assert _classify_r1_stratum(board, forced) == label


def test_observed_action_td_updates_only_executed_native_branch() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    mating_move = next(
        move
        for move in board.legal_moves
        if _execute_white_and_observe(board, move) == "mate"
    )
    triplet_id = graph.ensure_triplet(board, mating_move, stage="R0_test")
    confirmation = graph.confirm_candidate(
        board,
        triplet_id=triplet_id,
        move_uci=mating_move.uci(),
    )
    assert confirmation["selected_move"] == mating_move.uci()

    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(
            eta_fast=0.5,
            eta_slow=1.0,
            min_grounding_evidence=1,
        )
    )
    credit.register(R0_COMPETENCE_ID)
    credit.register(triplet_id, hierarchy_depth=1)
    credit.begin_episode()
    event = credit.transition(
        triplet_id,
        responsibilities=(
            Responsibility(triplet_id),
            Responsibility(R0_COMPETENCE_ID, parent_distance=1),
        ),
        terminal_kind="mate",
    )
    graph.apply_intrinsic_td(
        board,
        mating_move,
        td_error=event.td_error,
        stage_diagnostic="R0_test",
    )

    audit = graph.learned_state_audit()
    assert audit["triplet_count"] == 1
    assert audit["m3_update_count"] > 0
    assert audit["nonzero_trainable_edge_count"] > 0
    assert credit.states[R0_COMPETENCE_ID].terminal_evidence == 1


def test_nonmating_action_receives_only_metabolic_td_not_teacher_failure() -> None:
    board = chess.Board(MATE_ONE_FEN)
    nonmating = next(
        move
        for move in board.legal_moves
        if _execute_white_and_observe(board, move) is None
    )
    assert _execute_white_and_observe(board, nonmating) is None

    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(real_move_cost=0.02, eta_fast=0.5)
    )
    credit.register("observed_action")
    event = credit.transition("observed_action", terminal_kind=None)

    assert event.immediate_reward == -0.02
    assert event.successor_value == 0.0
    assert event.terminal_kind is None
    assert credit.states["observed_action"].terminal_evidence == 0


def test_shared_triplet_is_evaluated_for_each_overlapping_current_move() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    mating_move = next(
        move
        for move in board.legal_moves
        if _execute_white_and_observe(board, move) == "mate"
    )
    triplet_id = graph.apply_intrinsic_td(
        board,
        mating_move,
        td_error=1.0,
        stage_diagnostic="R0_pair_mapping_test",
    )

    audit = graph.audit_choice(board)
    rows = [
        row
        for row in audit["confirmed_candidates"]
        if row["triplet_id"] == triplet_id
    ]

    assert audit["candidate_triplet_count"] > audit["unique_candidate_triplet_count"]
    assert len({row["move"] for row in rows}) > 1
    assert any(
        row["move"] != mating_move.uci() and row["score"] > 0.0
        for row in rows
    )


def test_hierarchy_score_uses_current_triplet_edge_for_shared_atom() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    first_move, second_move = list(board.legal_moves)[:2]
    first_id = graph.ensure_triplet(board, first_move, stage="shared_parent_test")
    second_id = graph.ensure_triplet(board, second_move, stage="shared_parent_test")
    roles = {
        "before_feature",
        "delta_feature",
        "after_feature",
        "projection_feature",
    }
    shared_ids = [
        node_id
        for node_id in graph.triplet_nodes[first_id] & graph.triplet_nodes[second_id]
        if graph.graph.nodes[node_id].meta.get("role") in roles
    ]
    assert shared_ids

    def parent_id(triplet_id: str, role: str) -> str:
        suffix = {
            "before_feature": "before_script",
            "delta_feature": "action_script",
            "projection_feature": "action_script",
            "after_feature": "after_script",
        }[role]
        return f"{triplet_id}_{suffix}"

    for node_id in graph.triplet_nodes[second_id]:
        node = graph.graph.nodes[node_id]
        role = str(node.meta.get("role", ""))
        node.meta["local_weight"] = 0.0
        if role in roles:
            edge = graph.graph.get_edge(parent_id(second_id, role), node_id, LinkType.SUB)
            assert edge is not None
            edge.w = 0.0
    shared_id = shared_ids[0]
    role = str(graph.graph.nodes[shared_id].meta["role"])
    first_edge = graph.graph.get_edge(parent_id(first_id, role), shared_id, LinkType.SUB)
    second_edge = graph.graph.get_edge(parent_id(second_id, role), shared_id, LinkType.SUB)
    assert first_edge is not None and second_edge is not None
    first_edge.w = 1.0
    second_edge.w = -1.0

    confirmation = graph.confirm_candidate(
        board, triplet_id=second_id, move_uci=second_move.uci()
    )
    assert confirmation["selected_move"] == second_move.uci()
    score, _ = graph._confirmed_terminal_score(second_id)
    assert score == pytest.approx(-1.0)


def test_virtual_frame_availability_uses_child_move_without_grounding() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    mating_move = next(
        move
        for move in board.legal_moves
        if _execute_white_and_observe(board, move) == "mate"
    )
    graph.apply_intrinsic_td(
        board,
        mating_move,
        td_error=1.0,
        stage_diagnostic="R0_virtual_frame_test",
    )

    available, response = _r0_available(
        graph,
        None,
        board,
        mode="virtual_frame_verified",
    )

    assert available is True
    assert response["selected_move"] == mating_move.uci()
    assert response["availability_source"] == "mature_child_selected_virtual_frame"
    assert response["virtual_frame_terminal_grounding_granted"] is False

    graph.freeze_existing_parameters(reason="R0_test_consolidation")
    cache: dict[str, dict[str, object]] = {}
    first_available, _first_response, first_hit, first_mismatch = (
        _r0_available_with_dispatch_cache(
            graph,
            None,
            board,
            mode="virtual_frame_verified",
            allowed_triplets=frozenset(graph.triplet_ids),
            cache=cache,
            enabled=True,
        )
    )
    second_available, second_response, second_hit, second_mismatch = (
        _r0_available_with_dispatch_cache(
            graph,
            None,
            board,
            mode="virtual_frame_verified",
            allowed_triplets=frozenset(graph.triplet_ids),
            cache=cache,
            enabled=True,
        )
    )
    assert (first_available, first_hit, first_mismatch) == (True, False, False)
    assert (second_available, second_hit, second_mismatch) == (True, True, False)
    assert second_response["availability_source"] == "live_confirmed_frozen_child_dispatch_memory"
    hierarchical = _choose_with_child_priority(
        graph,
        board,
        r0_child_triplet_ids=frozenset(graph.triplet_ids),
    )
    assert hierarchical == mating_move


def _trained_r0_core_for_routing_tests() -> tuple[
    NativeReConKRKGraph, chess.Board, chess.Move
]:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    mating_move = next(
        move
        for move in board.legal_moves
        if _execute_white_and_observe(board, move) == "mate"
    )
    graph.apply_intrinsic_td(
        board,
        mating_move,
        td_error=1.0,
        stage_diagnostic="R0_protected_core_routing_test",
    )
    graph.mature_existing_graph()
    graph.freeze_existing_parameters(reason="R0_protected_core_routing_test")
    return graph, board, mating_move


class _FixedLocalCoreGate:
    def __init__(self, confirms: bool) -> None:
        self.mature = True
        self._confirms = bool(confirms)

    def confirms(self, _features) -> bool:
        return self._confirms

    def to_dict(self) -> dict[str, object]:
        return {"gate": "fixed_local_test", "confirms": self._confirms}


def test_protected_core_survives_grown_shared_topology_interference() -> None:
    trained, board, mating_move = _trained_r0_core_for_routing_tests()
    frozen_core = copy.deepcopy(trained)
    grown = copy.deepcopy(trained)
    for edge in grown.graph.edges:
        edge.w = -100.0

    assert grown.choose(board) != mating_move
    selected = _choose_with_child_priority(
        grown,
        board,
        r0_child_triplet_ids=frozenset(),
        r0_core_graph=frozen_core,
        r0_core_gate=_FixedLocalCoreGate(True),
        r0_core_triplet_ids=frozenset(frozen_core.triplet_ids),
    )
    assert selected == mating_move


def test_protected_core_abstention_leaves_r1_exploration_to_grown_graph() -> None:
    trained, board, _mating_move = _trained_r0_core_for_routing_tests()
    frozen_core = copy.deepcopy(trained)
    grown = copy.deepcopy(trained)
    for edge in grown.graph.edges:
        edge.w = -100.0
    grown_choice = grown.choose(board)

    selected = _choose_with_child_priority(
        grown,
        board,
        r0_child_triplet_ids=frozenset(),
        r0_core_graph=frozen_core,
        r0_core_gate=_FixedLocalCoreGate(False),
        r0_core_triplet_ids=frozenset(frozen_core.triplet_ids),
    )
    assert selected == grown_choice


def test_core_abstention_does_not_fall_into_mutable_virtual_child_fallback() -> None:
    trained, board, _mating_move = _trained_r0_core_for_routing_tests()
    frozen_core = copy.deepcopy(trained)
    grown = copy.deepcopy(trained)
    for edge in grown.graph.edges:
        edge.w = -100.0
    grown_choice = grown.choose(board)
    authority = _FakeV2Authority(certify_after=100)

    selected = _choose_with_child_priority(
        grown,
        board,
        # Deliberately retain a nonempty legacy id set.  With a protected core,
        # an UNKNOWN V2 result must not invoke virtual_frame_verified on the
        # mutable grown graph and manufacture a core preemption.
        r0_child_triplet_ids=frozenset(frozen_core.triplet_ids),
        r0_child_authority=authority,
        r0_core_graph=frozen_core,
        r0_core_gate=_FixedLocalCoreGate(False),
        r0_core_triplet_ids=frozenset(frozen_core.triplet_ids),
    )
    assert selected == grown_choice


def test_available_protected_core_precedes_v2_descendant() -> None:
    trained, board, mating_move = _trained_r0_core_for_routing_tests()
    frozen_core = copy.deepcopy(trained)
    grown = copy.deepcopy(trained)
    for edge in grown.graph.edges:
        edge.w = -100.0
    authority = _FakeV2Authority(certify_after=0)

    selected = _choose_with_child_priority(
        grown,
        board,
        r0_child_triplet_ids=frozenset(),
        r0_child_authority=authority,
        r0_core_graph=frozen_core,
        r0_core_gate=_FixedLocalCoreGate(True),
        r0_core_triplet_ids=frozenset(frozen_core.triplet_ids),
    )
    assert selected == mating_move


def test_continuous_evidence_requires_ecology_and_changes_resume_identity() -> None:
    with pytest.raises(ValueError, match="requires boundary ecology"):
        NativeIntrinsicCurriculumConfig(r0_boundary_continuous_evidence=True)
    with pytest.raises(ValueError, match="must be boolean"):
        NativeIntrinsicCurriculumConfig(r0_boundary_continuous_evidence=1)
    config = NativeIntrinsicCurriculumConfig(r0_boundary_ecology_enabled=True)
    credit = IntrinsicCreditEngine(IntrinsicCreditConfig())
    graph = _graph()
    arm = R1MechanisticArm(name="test", bootstrap_enabled=True)

    def fingerprint(cfg):
        return _r1_snapshot_fingerprint(
            graph, credit, None, _real_ecology_pools(),
            arm_name=arm.name, arm_spec=arm,
            r0_child_triplet_ids=frozenset(),
            r0_child_authority_digest=None, config=cfg,
        )

    assert fingerprint(config) != fingerprint(replace(
        config, r0_boundary_continuous_evidence=True
    ))


def test_protected_core_identity_is_bound_into_r1_resume_fingerprint() -> None:
    trained, _board, _mating_move = _trained_r0_core_for_routing_tests()
    frozen_core = copy.deepcopy(trained)
    gate = _FixedLocalCoreGate(True)
    credit = IntrinsicCreditEngine(IntrinsicCreditConfig())
    credit.register(R0_COMPETENCE_ID, mature=True)
    pools = _Pools(
        r0_train=(MATE_ONE_FEN,),
        r0_validation=(MATE_ONE_FEN,),
        r0_regression=(MATE_ONE_FEN,),
        gate_train_decoys=(),
        gate_validation_decoys=(),
        gate_regression_decoys=(),
        r1_train=(R1_RETIRED_DEVELOPMENT_FENS[0],),
        r1_validation=(R1_RETIRED_DEVELOPMENT_FENS[1],),
        r1_regression=(R1_RETIRED_DEVELOPMENT_FENS[2],),
        r0_train_strata=("test",),
        r0_validation_strata=("test",),
        r0_regression_strata=("test",),
        r0_excluded_fens=(),
        r0_pool_mode="test",
        r1_train_strata=("test",),
        r1_validation_strata=("test",),
        r1_regression_strata=("test",),
        r1_pool_mode="test",
    )
    config = NativeIntrinsicCurriculumConfig(max_samples=0)
    arm = R1MechanisticArm(name="full_intrinsic", bootstrap_enabled=True)
    first = _r1_snapshot_fingerprint(
        trained,
        credit,
        gate,
        pools,
        arm_name=arm.name,
        arm_spec=arm,
        r0_child_triplet_ids=frozenset(trained.triplet_ids),
        r0_child_authority_digest=None,
        config=config,
        r0_core_graph=frozen_core,
        r0_core_triplet_ids=frozenset(frozen_core.triplet_ids),
    )
    frozen_core.graph.edges[0].w += 0.25
    second = _r1_snapshot_fingerprint(
        trained,
        credit,
        gate,
        pools,
        arm_name=arm.name,
        arm_spec=arm,
        r0_child_triplet_ids=frozenset(trained.triplet_ids),
        r0_child_authority_digest=None,
        config=config,
        r0_core_graph=frozen_core,
        r0_core_triplet_ids=frozenset(frozen_core.triplet_ids),
    )
    assert second != first


def test_r0_replay_uses_graph_selected_action_and_real_outcome() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    mating_move = next(
        move
        for move in board.legal_moves
        if _execute_white_and_observe(board, move) == "mate"
    )
    graph.apply_intrinsic_td(
        board,
        mating_move,
        td_error=1.0,
        stage_diagnostic="R0_replay_setup",
    )
    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(
            eta_fast=0.5,
            min_grounding_evidence=1,
        )
    )
    credit.register(R0_COMPETENCE_ID)
    before_updates = graph.m3_update_count

    replay = _replay_r0(
        graph,
        credit,
        (MATE_ONE_FEN,),
        epoch=0,
        count=1,
    )

    assert replay["episodes"] == 1
    assert replay["observed_mates"] == 1
    assert replay["observed_nonmates"] == 0
    assert replay["formal_confirmation_failures"] == 0
    assert replay["cached_outcome_mismatches"] == 0
    assert graph.m3_update_count > before_updates
    assert credit.states[R0_COMPETENCE_ID].terminal_evidence == 1


def test_native_v2_r0_admission_is_read_only_and_requires_clean_jurisdiction(
    monkeypatch,
) -> None:
    positive = "k7/8/1K6/8/8/8/8/7R w - - 0 1"
    decoy = "8/8/8/8/8/2K5/7R/k7 w - - 0 1"

    class _R0:
        @staticmethod
        def inference_guard_identity() -> str:
            return "immutable-r0"

    class _Session:
        def close(self) -> None:
            pass

    class _Authority:
        base = SimpleNamespace(r0=_R0())

        @staticmethod
        def continuation_digest() -> str:
            return "immutable-authority"

        @staticmethod
        def frame_session() -> _Session:
            return _Session()

    def available(_authority, board, *, frame_id, frame_session=None):
        assert frame_id.startswith("native-r0-admission:")
        assert frame_session is not None
        if board.fen() == chess.Board(positive).fen():
            mating = next(
                move for move in board.legal_moves
                if _execute_white_and_observe(board, move) == "mate"
            )
            return True, {
                "selected_move": mating.uci(),
                "classification": {"state": "available"},
            }
        return False, {
            "selected_move": None,
            "classification": {"state": "unknown"},
        }

    monkeypatch.setattr(curriculum_module, "_v2_r0_available", available)
    audit = _native_v2_r0_admission_audit(
        _Authority(),
        positive_fens=(positive,),
        negative_fens=(decoy,),
        max_samples=2,
    )

    assert audit["pass"] is True
    assert audit["runtime_integrity_pass"] is True
    assert audit["coverage_specificity_controls_r1_stage_entry"] is False
    assert audit["runtime_integrity_controls_r1_stage_entry"] is True
    assert audit["runtime_integrity_checks_all_emitted_actuations"] is True
    assert audit["positive_authorized_mate_count"] == 1
    assert audit["negative_available_count"] == 0
    assert audit["continuation_immutable"] is True
    assert audit["frozen_r0_immutable"] is True
    assert audit["validation_outcomes_consumed_by_learner"] is False


def test_partial_native_r0_coverage_is_report_only_not_an_r1_entry_gate(
    monkeypatch,
) -> None:
    positive = "k7/8/1K6/8/8/8/8/7R w - - 0 1"
    decoy = "8/8/8/8/8/2K5/7R/k7 w - - 0 1"

    class _R0:
        @staticmethod
        def inference_guard_identity() -> str:
            return "immutable-r0"

    class _Session:
        def close(self) -> None:
            pass

    class _Authority:
        base = SimpleNamespace(r0=_R0())

        @staticmethod
        def continuation_digest() -> str:
            return "immutable-authority"

        @staticmethod
        def frame_session() -> _Session:
            return _Session()

    def abstaining(_authority, board, *, frame_id, frame_session=None):
        assert frame_id.startswith("native-r0-admission:")
        assert frame_session is not None
        selected = next(iter(board.legal_moves), None)
        return False, {
            "selected_move": None if selected is None else selected.uci(),
            "classification": {"state": "unknown"},
        }

    monkeypatch.setattr(curriculum_module, "_v2_r0_available", abstaining)
    audit = _native_v2_r0_admission_audit(
        _Authority(),
        positive_fens=(positive,),
        negative_fens=(decoy,),
        max_samples=2,
    )

    assert audit["pass"] is False
    assert audit["positive_authorized_count"] == 0
    assert audit["negative_available_count"] == 0
    assert audit["runtime_integrity_pass"] is True
    assert _native_v2_runtime_integrity_ready(audit) is True
    assert _native_v2_authority_ready_for_r1(
        availability_mode=V2_PROSPECTIVE_AVAILABILITY,
        authority_present=True,
        boundary_ecology_enabled=True,
        admission_audit=audit,
    ) is True
    assert audit["coverage_specificity_controls_r1_stage_entry"] is False


def test_native_r0_available_illegal_actuation_blocks_runtime_integrity(
    monkeypatch,
) -> None:
    positive = "k7/8/1K6/8/8/8/8/7R w - - 0 1"

    class _R0:
        @staticmethod
        def inference_guard_identity() -> str:
            return "immutable-r0"

    class _Authority:
        base = SimpleNamespace(r0=_R0())

        @staticmethod
        def continuation_digest() -> str:
            return "immutable-authority"

    monkeypatch.setattr(
        curriculum_module,
        "_v2_r0_available",
        lambda *_args, **_kwargs: (
            True,
            {
                "selected_move": "a1a8",
                "classification": {"state": "available"},
            },
        ),
    )
    audit = _native_v2_r0_admission_audit(
        _Authority(),
        positive_fens=(positive,),
        negative_fens=(),
        max_samples=1,
    )

    assert audit["runtime_integrity_pass"] is False
    assert audit["available_invalid_actuation_count"] == 1
    assert _native_v2_runtime_integrity_ready(audit) is False
    assert _native_v2_authority_ready_for_r1(
        availability_mode=V2_PROSPECTIVE_AVAILABILITY,
        authority_present=True,
        boundary_ecology_enabled=True,
        admission_audit=audit,
    ) is False


def test_native_r0_unknown_illegal_emission_blocks_runtime_integrity(
    monkeypatch,
) -> None:
    positive = "k7/8/1K6/8/8/8/8/7R w - - 0 1"

    class _R0:
        @staticmethod
        def inference_guard_identity() -> str:
            return "immutable-r0"

    class _Authority:
        base = SimpleNamespace(r0=_R0())

        @staticmethod
        def continuation_digest() -> str:
            return "immutable-authority"

    monkeypatch.setattr(
        curriculum_module,
        "_v2_r0_available",
        lambda *_args, **_kwargs: (
            False,
            {
                "selected_move": "a1a8",
                "classification": {"state": "unknown"},
            },
        ),
    )
    audit = _native_v2_r0_admission_audit(
        _Authority(),
        positive_fens=(positive,),
        negative_fens=(),
        max_samples=1,
    )

    assert audit["pass"] is False
    assert audit["runtime_integrity_pass"] is False
    assert audit["available_invalid_actuation_count"] == 0
    assert audit["illegal_selection_count"] == 1
    assert _native_v2_runtime_integrity_ready(audit) is False


def test_cached_r0_replay_is_graph_memory_live_confirmed_and_reexecuted() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    mating_move = next(
        move
        for move in board.legal_moves
        if _execute_white_and_observe(board, move) == "mate"
    )
    for _ in range(8):
        graph.apply_intrinsic_td(
            board,
            mating_move,
            td_error=1.0,
            stage_diagnostic="R0_cached_replay_setup",
        )
    memory, audit = _build_r0_replay_memory(graph, (MATE_ONE_FEN,))
    assert audit["teacher_solution_labels_consumed"] == 0
    assert audit["experience_count"] == 1
    assert memory[0].move_uci == mating_move.uci()
    assert memory[0].observed_terminal == "mate"

    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(eta_fast=0.5, min_grounding_evidence=1)
    )
    credit.register(R0_COMPETENCE_ID)
    replay = _replay_r0(
        graph,
        credit,
        (MATE_ONE_FEN,),
        epoch=0,
        count=1,
        memory=memory,
    )

    assert replay["episodes"] == 1
    assert replay["observed_mates"] == 1
    assert replay["formal_confirmation_failures"] == 0
    assert replay["cached_outcome_mismatches"] == 0


def test_local_r1_action_selection_never_reaches_host_schedule(monkeypatch) -> None:
    board = chess.Board(MATE_ONE_FEN)
    emitted = next(iter(board.legal_moves))
    triplet_id = "native-emitted-triplet"
    calls: list[tuple[str, str]] = []

    class _Decision:
        move_uci = emitted.uci()
        confirmed = True
        prediction = 0.25

        def __init__(self) -> None:
            self.triplet_id = triplet_id

        def to_manifest(self) -> dict[str, object]:
            return {
                "move_uci": self.move_uci,
                "triplet_id": self.triplet_id,
                "selection_authority": "native_anonymous_choice",
            }

    class _Graph:
        @staticmethod
        def choose_local_training_action(
            received: chess.Board,
            stage_diagnostic: str,
        ) -> _Decision:
            calls.append((received.fen(), stage_diagnostic))
            return _Decision()

    def forbidden_schedule(*_args, **_kwargs):
        raise AssertionError("host action schedule reached in native-local mode")

    monkeypatch.setattr(
        curriculum_module,
        "_scheduled_confirmed_action",
        forbidden_schedule,
    )
    monkeypatch.setattr(
        curriculum_module,
        "_r1_legal_action_order",
        forbidden_schedule,
    )
    monkeypatch.setattr(
        curriculum_module,
        "_stable_hash_action_permutation",
        forbidden_schedule,
    )
    monkeypatch.setattr(
        curriculum_module,
        "_opaque_r1_position_identity",
        forbidden_schedule,
    )
    config = replace(
        NativeIntrinsicCurriculumConfig(),
        r1_action_selection_mode=R1_ACTION_SELECTION_LOCAL_RECON,
    )

    move, credited, confirmed, prediction, manifest = (
        _select_r1_training_action(
            _Graph(),
            board,
            epoch=99,
            position_index=7,
            fen=board.fen(),
            config=config,
        )
    )

    assert move == emitted
    assert credited == triplet_id
    assert confirmed is True
    assert prediction == pytest.approx(0.25)
    assert manifest["selection_authority"] == "native_anonymous_choice"
    assert calls == [(board.fen(), "R1_mate_in_2")]


def test_local_r1_training_fails_before_execution_when_exact_branch_is_unconfirmed() -> None:
    board = chess.Board(MATE_ONE_FEN)
    emitted = next(iter(board.legal_moves))

    class _Decision:
        move_uci = emitted.uci()
        triplet_id = "unconfirmed-native-branch"
        confirmed = False
        prediction = 0.0

        @staticmethod
        def to_manifest() -> dict[str, object]:
            return {}

    class _Graph:
        @staticmethod
        def choose_local_training_action(
            _received: chess.Board,
            stage_diagnostic: str,
        ) -> _Decision:
            assert stage_diagnostic == "R1_mate_in_2"
            return _Decision()

    config = replace(
        NativeIntrinsicCurriculumConfig(),
        r1_action_selection_mode=R1_ACTION_SELECTION_LOCAL_RECON,
    )
    with pytest.raises(RuntimeError, match="could not formally confirm"):
        _select_r1_training_action(
            _Graph(),
            board,
            epoch=0,
            position_index=0,
            fen=board.fen(),
            config=config,
        )


def test_local_r1_evaluation_uses_native_policy_and_direct_successor_authority(
    monkeypatch,
) -> None:
    fen = R1_RETIRED_DEVELOPMENT_FENS[0]
    board = chess.Board(fen)
    first_moves = tuple(sorted(
        _forced_mate_in_two_first_moves(board),
        key=lambda move: move.uci(),
    ))
    assert first_moves
    first = first_moves[0]
    native_policy_calls: list[str] = []
    successor_queries: list[str] = []

    class _Graph:
        @staticmethod
        def choose_local_policy_action(received: chess.Board):
            native_policy_calls.append(received.fen())
            return SimpleNamespace(move=first, policy_supported=True)

        @staticmethod
        def choose(*_args, **_kwargs):
            raise AssertionError("legacy weighted graph chooser reached")

        @staticmethod
        def audit_choice(*_args, **_kwargs):
            raise AssertionError("legacy graph audit chooser reached")

    def forbidden_priority(*_args, **_kwargs):
        raise AssertionError("host child-priority cascade reached")

    def native_successor(_authority, successor, *, frame_id, **_kwargs):
        successor_queries.append(frame_id)
        mating = next(
            move
            for move in successor.legal_moves
            if _execute_white_and_observe(successor, move) == "mate"
        )
        return True, {
            "selected_move": mating.uci(),
            "classification": {"state": "available"},
        }

    monkeypatch.setattr(
        curriculum_module,
        "_choose_with_child_priority",
        forbidden_priority,
    )
    monkeypatch.setattr(
        curriculum_module,
        "_v2_r0_available",
        native_successor,
    )

    result = _evaluate_r1(
        _Graph(),
        (fen,),
        max_samples=1,
        r0_child_authority=object(),
        action_selection_mode=R1_ACTION_SELECTION_LOCAL_RECON,
    )

    after_first = board.copy(stack=False)
    after_first.push(first)
    assert result["conversion_count"] == 1
    assert result["adaptive_host_priority_cascade_used"] is False
    assert result["certified_successor_authority_enabled"] is True
    assert native_policy_calls == [board.fen()]
    assert len(successor_queries) == len(tuple(after_first.legal_moves))


def test_local_r1_evaluation_abstains_on_an_empty_native_graph(monkeypatch) -> None:
    fen = R1_RETIRED_DEVELOPMENT_FENS[0]
    graph = NativeReConKRKGraph(
        config=NativeSingleGraphConfig(
            include_symmetries=False,
            train_repetitions=1,
            max_ticks=80,
        )
    )

    def forbidden_successor(*_args, **_kwargs):
        raise AssertionError("successor authority queried after unsupported first move")

    monkeypatch.setattr(
        curriculum_module,
        "_v2_r0_available",
        forbidden_successor,
    )

    result = _evaluate_r1(
        graph,
        (fen,),
        max_samples=1,
        r0_child_authority=object(),
        action_selection_mode=R1_ACTION_SELECTION_LOCAL_RECON,
    )

    assert result["conversion_count"] == 0
    assert result["null_selection_count"] == 1
    assert result["reply_evaluation_count"] == 0
    assert result["samples"][0]["selected_first"] is None


def test_local_r0_retention_fails_closed_on_native_authority_abstention(
    monkeypatch,
) -> None:
    def forbidden_priority(*_args, **_kwargs):
        raise AssertionError("host fallback reached after native abstention")

    monkeypatch.setattr(
        curriculum_module,
        "_choose_with_child_priority",
        forbidden_priority,
    )
    monkeypatch.setattr(
        curriculum_module,
        "_v2_r0_available",
        lambda *_args, **_kwargs: (
            False,
            {"selected_move": None, "classification": {"state": "unknown"}},
        ),
    )

    result = curriculum_module._evaluate_r0(
        SimpleNamespace(),
        (MATE_ONE_FEN,),
        max_samples=1,
        r0_child_authority=object(),
        action_selection_mode=R1_ACTION_SELECTION_LOCAL_RECON,
    )

    assert result["accuracy"] == 0.0
    assert result["null_selection_count"] == 1
    assert result["native_authority_fail_closed"] is True
