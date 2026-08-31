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

from recon_lite import LinkType
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
from recon_lite_chess.autogrowth.native_intrinsic_curriculum import (
    NativeIntrinsicCurriculumConfig,
    R1MechanisticArm,
    R0_BALANCED_STRATA,
    R0_COMPETENCE_ID,
    GATE_FEATURE_NAMES,
    R1_BALANCED_STRATA,
    R1_RETIRED_DEVELOPMENT_FENS,
    R1CheckpointInterrupt,
    V2_PROSPECTIVE_AVAILABILITY,
    _Pools,
    _apply_child_value_control,
    _attach_terminal_r1_regression_report,
    _balanced_r0_quotas,
    _balanced_r1_quotas,
    _build_r0_replay_memory,
    _choose_with_child_priority,
    _classify_r0_stratum,
    _classify_r1_stratum,
    _disable_nonmature_composites,
    _execute_white_and_observe,
    _evaluate_r1,
    _fit_r0_gate,
    _generate_balanced_r0_split,
    _generate_balanced_r1_split,
    _mechanistic_r1_arms,
    _namespace_development_fullmoves,
    _r0_available,
    _r0_available_with_dispatch_cache,
    _r1_orbit_key,
    _r1_snapshot_fingerprint,
    _replay_r0,
    run_native_intrinsic_curriculum,
    _restore_disabled_composites,
    _run_r1_arm,
    _v2_authoritative_predecessor_fens,
    _v2_r0_available,
    _v2_r0_observe_training_successor,
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

    def open_real_event(self, frame):
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


@pytest.mark.parametrize("v2_enabled", (False, True), ids=("legacy", "v2"))
def test_r1_interval_snapshot_resume_matches_uninterrupted(
    tmp_path, v2_enabled
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
        "no_bootstrap",
        uninterrupted_graph,
        uninterrupted_credit,
        gate,
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
    ) == 1

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
            gate,
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
        gate,
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
