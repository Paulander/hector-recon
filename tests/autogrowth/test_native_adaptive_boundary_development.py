from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import chess
import pytest

from recon_lite_chess.autogrowth import (
    native_adaptive_boundary_development as adaptive,
    native_intrinsic_v2_development as intrinsic,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import (
    StructuralMode,
)
from recon_lite_chess.autogrowth.native_intrinsic_curriculum import (
    R0_ACTION_SELECTION_LOCAL_RECON,
    R1_ACTION_SELECTION_LOCAL_RECON,
)


def test_discovery_receipts_accept_role_mismatch_and_use_observed_outcome() -> None:
    """Discovery learning follows the real successor, not pool membership."""

    class _R0:
        @staticmethod
        def emit_action_with_trace(frame):
            board = frame.values["board"]
            for move in board.legal_moves:
                successor = board.copy(stack=False)
                successor.push(move)
                if not successor.is_checkmate():
                    return SimpleNamespace(move_uci=move.uci()), object()
            raise AssertionError("test board unexpectedly has only mating moves")

    class _Terminal:
        @staticmethod
        def mint(_trace, predecessor, successor):
            return SimpleNamespace(
                predecessor_fen=predecessor.fen(),
                observed_terminal_result=successor.is_checkmate(),
            )

    source = SimpleNamespace(r0=_R0(), completion_terminal=lambda: _Terminal())
    # This is a positive-pool mate-in-one row, but the frozen test network
    # deliberately emits a non-mating legal successor for it.
    positive_pool_fen = "k7/8/1K6/8/8/8/8/7R w - - 0 1"

    receipts = intrinsic._mint_discovery_receipts(source, (positive_pool_fen,))

    assert len(receipts) == 1
    assert receipts[0].predecessor_fen == positive_pool_fen
    assert receipts[0].observed_terminal_result is False
    assert tuple(inspect.signature(
        intrinsic._mint_discovery_receipts
    ).parameters) == ("source", "fens")


def test_neutral_discovery_tape_is_partition_invariant() -> None:
    """The same training multiset yields one content-defined 32-row tape."""

    source_fens = tuple(f"source-fen-{index:02d}" for index in range(40))
    r0_partition_a = source_fens[:24]
    decoy_partition_a = source_fens[24:]
    r0_partition_b = source_fens[8:32]
    decoy_partition_b = source_fens[:8] + source_fens[32:]

    tape_a = intrinsic._neutral_discovery_tape(
        r0_partition_a + decoy_partition_a
    )
    tape_b = intrinsic._neutral_discovery_tape(
        tuple(reversed(r0_partition_b + decoy_partition_b))
    )

    assert len(tape_a) == len(tape_b) == 32
    assert tape_a == tape_b
    assert len(set(tape_a)) == 32
    assert set(tape_a).issubset(set(source_fens))


def test_neutral_tape_order_is_the_receipt_sequence() -> None:
    """Content order, rather than a source role, determines receipt ordinals."""

    class _R0:
        @staticmethod
        def emit_action_with_trace(frame):
            board = frame.values["board"]
            for move in board.legal_moves:
                successor = board.copy(stack=False)
                successor.push(move)
                if not successor.is_checkmate():
                    return SimpleNamespace(move_uci=move.uci()), object()
            raise AssertionError("test board unexpectedly has only mating moves")

    class _Terminal:
        def __init__(self) -> None:
            self.event_ordinals: list[int] = []

        def mint(self, _trace, predecessor, successor):
            ordinal = len(self.event_ordinals)
            self.event_ordinals.append(ordinal)
            return SimpleNamespace(
                event_id=f"event:{ordinal:02d}",
                predecessor_fen=predecessor.fen(),
                observed_terminal_result=successor.is_checkmate(),
            )

    source_fens = tuple(
        f"k7/8/1K6/8/8/8/8/7R w - - 0 {index}"
        for index in range(1, 41)
    )
    tape = intrinsic._neutral_discovery_tape(source_fens)
    terminal = _Terminal()
    source = SimpleNamespace(
        r0=_R0(), completion_terminal=lambda: terminal
    )

    receipts = intrinsic._mint_discovery_receipts(source, tape)

    assert len(receipts) == 32
    assert tuple(receipt.event_id for receipt in receipts) == tuple(
        f"event:{index:02d}" for index in range(32)
    )
    assert tuple(receipt.predecessor_fen for receipt in receipts) == tuple(
        chess.Board(fen).fen() for fen in tape
    )


def test_profiles_preserve_frozen_r0_and_only_change_r1_work(tmp_path: Path) -> None:
    canary = adaptive.development_config(
        "canary", output_dir=tmp_path / "canary", seed=17,
        max_wall_seconds=11.0, max_peak_rss_mib=22.0,
    )
    gate = adaptive.development_config(
        "gate", output_dir=tmp_path / "gate", seed=17,
        max_wall_seconds=11.0, max_peak_rss_mib=22.0,
    )
    frozen = intrinsic.development_config(
        output_dir=tmp_path / "reference",
        max_wall_seconds=11.0,
        max_peak_rss_mib=22.0,
    )

    assert canary.r1_reply_policy == gate.r1_reply_policy == (
        "prospective_counterexample"
    )
    # The adaptive selector never consults the legacy action-order field.
    assert canary.r1_action_order == gate.r1_action_order == frozen.r1_action_order
    assert canary.r1_action_selection_mode == gate.r1_action_selection_mode == (
        R1_ACTION_SELECTION_LOCAL_RECON
    )
    assert canary.r0_boundary_ecology_enabled is True
    assert gate.r0_boundary_ecology_enabled is True
    assert canary.r0_action_selection_mode == gate.r0_action_selection_mode == (
        R0_ACTION_SELECTION_LOCAL_RECON
    )
    assert canary.validation_controls_stage_transitions is False
    assert gate.validation_controls_stage_transitions is False
    assert frozen.validation_controls_stage_transitions is True
    assert canary.seed == gate.seed == 17
    assert canary.development_fen_fullmove_base == (
        adaptive.DEVELOPMENT_FEN_FULLMOVE_BASE
    )
    assert canary.development_fen_fullmove_base != (
        intrinsic.DEVELOPMENT_FEN_FULLMOVE_BASE
    )
    assert canary.output_path.endswith("canary/result.json")
    assert gate.output_path.endswith("gate/result.json")
    assert canary.progress_path != gate.progress_path
    assert {
        field: getattr(canary, field)
        for field in adaptive._PROFILE_WORK["canary"]
    } == adaptive._PROFILE_WORK["canary"]
    assert {
        field: getattr(gate, field)
        for field in adaptive._PROFILE_WORK["gate"]
    } == adaptive._PROFILE_WORK["gate"]
    assert canary.development_wall_ceiling_seconds == 11.0
    assert canary.development_peak_rss_ceiling_mib == 22.0

    r0_fields = (
        "r0_train_count", "r0_validation_count", "r0_regression_count",
        "r0_gate_train_decoy_count", "r0_gate_validation_decoy_count",
        "r0_gate_regression_decoy_count", "r0_pool_mode", "r0_epochs",
        "r0_replay_per_r1_epoch", "r0_validation_interval",
        "r0_availability_mode", "freeze_r0_parameters_for_r1",
        "eta_m3", "eta_fast", "eta_slow", "real_move_cost",
    )
    for field in r0_fields:
        assert getattr(canary, field) == getattr(frozen, field)
        assert getattr(gate, field) == getattr(frozen, field)

    assert canary.r1_validation_interval == 1
    assert canary.r1_snapshot_interval == 1
    assert canary.r1_pool_mode == "random"
    assert gate.r1_pool_mode == "balanced_setup"
    assert gate.r1_validation_interval <= 4
    assert gate.r1_snapshot_interval <= 4
    assert gate.r1_train_count > canary.r1_train_count
    assert gate.r1_epochs > canary.r1_epochs
    with pytest.raises(
        ValueError,
        match="profile must be one of canary, follow-through, gate",
    ):
        adaptive.development_config("scientific")


@pytest.mark.parametrize(
    "override",
    (
        {"r0_action_selection_mode": "scheduled"},
        {"r1_action_selection_mode": "scheduled"},
        {"validation_controls_stage_transitions": True},
        {"r0_replay_per_r1_epoch": 1},
        {"r0_boundary_ecology_enabled": False},
    ),
)
def test_adaptive_config_fails_closed_on_retired_host_controls(
    tmp_path: Path,
    override: dict[str, object],
) -> None:
    config = replace(
        adaptive.development_config(output_dir=tmp_path),
        **override,
    )
    with pytest.raises(ValueError, match="retired host control"):
        adaptive._validate_adaptive_mechanism_config(config)


def test_follow_through_is_an_eight_epoch_canary_extension(tmp_path: Path) -> None:
    canary = adaptive.development_config(
        "canary", output_dir=tmp_path, seed=17,
        max_wall_seconds=11.0, max_peak_rss_mib=22.0,
    )
    follow_through = adaptive.development_config(
        " FOLLOW_THROUGH ", output_dir=tmp_path, seed=17,
        max_wall_seconds=11.0, max_peak_rss_mib=22.0,
    )

    canary_payload = asdict(canary)
    follow_payload = asdict(follow_through)
    changed = {
        field
        for field in canary_payload
        if canary_payload[field] != follow_payload[field]
    }
    assert changed == {"r1_epochs"}
    assert follow_through.r1_pool_mode == "random"
    assert (
        follow_through.r1_train_count,
        follow_through.r1_validation_count,
        follow_through.r1_regression_count,
    ) == (8, 4, 4)
    assert follow_through.r1_epochs == 8
    assert follow_through.r1_validation_interval == 1
    assert follow_through.r1_snapshot_interval == 1
    assert adaptive._normalize_profile("follow_through") == (
        adaptive.FOLLOW_THROUGH_PROFILE
    )
    assert adaptive._profile_for_config(follow_through) == (
        adaptive.FOLLOW_THROUGH_PROFILE
    )


class _FakeAuthority:
    def __init__(self) -> None:
        self.structural_mode = StructuralMode.SCHEDULED
        self.structural_epoch_schedule = (64,)
        self.boundaries: list[str] = []

    def verify_full_history_boundary(self, boundary: str) -> None:
        self.boundaries.append(boundary)

    def continuation_manifest(self) -> dict[str, object]:
        return {
            "structural_mode": self.structural_mode.value,
            "structural_epoch_schedule": list(self.structural_epoch_schedule),
        }

    def dumps(self) -> bytes:
        return b"fake-authority"

    @classmethod
    def loads(cls, _payload: bytes) -> "_FakeAuthority":
        restored = cls()
        restored.structural_mode = StructuralMode.EVENT_DRIVEN
        restored.structural_epoch_schedule = ()
        return restored


def test_factory_preserves_authority_constructed_in_event_mode(monkeypatch) -> None:
    authority = _FakeAuthority()
    authority.structural_mode = StructuralMode.EVENT_DRIVEN
    authority.structural_epoch_schedule = ()
    audit = {
        "structural_schedule": {
            "absolute_event_frontiers": [],
            "prospective_events_before_structure": None,
        },
        "candidate_count": 1,
    }
    calls: list[tuple[object, ...]] = []

    def base_factory(*args):
        calls.append(args)
        return authority, audit

    monkeypatch.setattr(
        adaptive._intrinsic,
        "build_empty_event_driven_v2_r0_authority",
        base_factory,
    )
    observed, corrected = adaptive.build_empty_event_driven_v2_r0_authority(
        object(), object(), object(), object()
    )

    assert observed is authority
    assert len(calls) == 1
    assert authority.structural_mode is StructuralMode.EVENT_DRIVEN
    assert authority.structural_epoch_schedule == ()
    assert authority.boundaries == [
        "native-adaptive-boundary-development",
    ]
    assert corrected["structural_mode"] == "event_driven"
    assert corrected["structural_epoch_schedule"] == []
    schedule = corrected["structural_schedule"]
    assert schedule["absolute_event_frontiers"] == []
    assert schedule["scheduled_frontiers"] == []
    assert schedule["no_scheduled_frontiers"] is True
    assert schedule["prospective_events_before_structure"] is None


def test_factory_rejects_post_construction_mode_rewrite(monkeypatch) -> None:
    authority = _FakeAuthority()
    monkeypatch.setattr(
        adaptive._intrinsic,
        "build_empty_event_driven_v2_r0_authority",
        lambda *_args: (authority, {}),
    )
    with pytest.raises(RuntimeError, match="not constructed in event-driven"):
        adaptive.build_empty_event_driven_v2_r0_authority(
            object(), object(), object(), object()
        )
    assert authority.structural_mode is StructuralMode.SCHEDULED
    assert authority.structural_epoch_schedule == (64,)


@dataclass
class _FakeResult:
    r0_pass: bool = True

    def to_dict(self) -> dict[str, object]:
        return {"synthetic": True, "r0": {"pass": self.r0_pass}}


@dataclass
class _FakeGateResult:
    r0_pass: bool = True
    r1_executed: bool = False
    r1_pass: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "synthetic": True,
            "r0": {"pass": self.r0_pass},
            "decision": {
                "r0_pass": self.r0_pass,
                "r1_executed": self.r1_executed,
                "r1_pass": self.r1_pass,
            },
        }


class _PayloadResult:
    def __init__(self) -> None:
        self.payload: dict[str, object] = {}


def test_complete_per_run_mechanism_evidence_never_claims_scientific_gate() -> None:
    payload = {
        "scientific_contract": {
            "validation_outcome_mastery_is_report_only_for_stage_transitions": True,
        },
        "decision": {
            "r0_pass": True,
            "r1_executed": True,
            "r1_pass": True,
        },
        "r0": {
            "training": {
                "r0_action_selection_mode": R0_ACTION_SELECTION_LOCAL_RECON,
                "native_local_action_count": 48,
                "scheduled_action_count": 0,
            }
        },
        "r0_child_authority": {
            "boundary_initialization": "empty_event_driven_positive_shell",
            "no_scheduled_frontiers": True,
            "initial_state": {
                "base_receipt_count": 0,
                "base_cell_count": 0,
                "nominated_candidate_count": 0,
                "authority_state_count": 0,
            },
        },
        "r1_arms": {
            "full_intrinsic": {
                "training": {
                    "r1_action_selection_mode": R1_ACTION_SELECTION_LOCAL_RECON,
                    "local_action_recent_events": [
                        {
                            "position_index": 0,
                            "pattern_id": "pattern:revisited",
                            "pattern_exposure": 0,
                            "move_uci": "a1a2",
                            "raw_value": 0.0,
                            "triplet_id": "t0",
                            "credited_triplet_id": "t0",
                        },
                        {
                            "position_index": 0,
                            "pattern_id": "pattern:revisited",
                            "pattern_exposure": 1,
                            "move_uci": "a1a2",
                            "raw_value": 0.25,
                            "triplet_id": "t1",
                            "credited_triplet_id": "t1",
                        },
                    ],
                    "local_candidate_cap_bound": False,
                    "resumed_from_snapshot": True,
                    "boundary_ecology": {
                        "tombstone_count": 1,
                        "active_candidate_count": 2,
                        "active_candidate_cap": 32,
                    },
                    "all_reply_envelope_available_count": 1,
                    "child_handoff_count": 1,
                    "successor_value_sum": 0.25,
                },
                "validation": {"conversion_count": 1},
                "r0_validation_retention": {"accuracy": 1.0},
                "v2_child_authority": {
                    "serialization_roundtrip_exact": True,
                    "full_history_boundary_exact": True,
                    "structural_events": [
                        {"retired_cell_ids": ["old"], "child_ids": ["new"]}
                    ],
                    "adaptive_positive_lineages": {
                        "lineage_count": 1,
                        "certified_node_count": 1,
                        "postbirth_certification_receipt_count": 1,
                        "all_certification_disjoint": True,
                        "all_certification_postbirth": True,
                        "certification_leak_count": 0,
                    },
                },
            }
        },
    }

    gates = adaptive._result_gate_fields(payload)

    assert gates["curriculum_gate_passed"] is True
    assert gates["mechanism_checks"]["r0_native_local_action_policy"] is True
    assert gates["mechanism_checks"]["empty_event_driven_positive_shell"] is True
    assert gates["mechanism_checks"][
        "validation_outcome_mastery_report_only"
    ] is True
    assert gates["per_run_mechanism_gate_passed"] is True
    assert gates["scientific_gate_passed"] is False
    assert adaptive._completion_status(gates) == (
        "PER_RUN_MECHANISM_GATE_PASSED_DEVELOPMENT_ONLY"
    )


def test_fresh_pattern_turnover_is_not_reported_as_policy_revisit() -> None:
    """Repeated positions with fresh local patterns are not a revisit."""

    payload = {
        "decision": {
            "r0_pass": True,
            "r1_executed": True,
            "r1_pass": True,
        },
        "r1_arms": {
            "full_intrinsic": {
                "training": {
                    "r1_action_selection_mode": R1_ACTION_SELECTION_LOCAL_RECON,
                    "local_action_recent_events": [
                        {
                            "position_index": 0,
                            "pattern_id": "pattern:fresh-a",
                            "pattern_exposure": 0,
                            "move_uci": "a1a2",
                            "raw_value": 0.0,
                            "triplet_id": "t0",
                            "credited_triplet_id": "t0",
                        },
                        {
                            "position_index": 0,
                            "pattern_id": "pattern:fresh-b",
                            "pattern_exposure": 0,
                            "move_uci": "a1a3",
                            "raw_value": 0.25,
                            "triplet_id": "t1",
                            "credited_triplet_id": "t1",
                        },
                    ],
                    "local_candidate_cap_bound": False,
                    "resumed_from_snapshot": True,
                    "boundary_ecology": {
                        "tombstone_count": 1,
                        "active_candidate_count": 2,
                        "active_candidate_cap": 32,
                    },
                    "all_reply_envelope_available_count": 1,
                    "child_handoff_count": 1,
                    "successor_value_sum": 0.25,
                },
                "validation": {"conversion_count": 1},
                "r0_frozen_native_policy_retention": {"accuracy": 1.0},
                "r0_validation_retention": {
                    "accuracy": 0.375,
                    "metric_name": "r0_v2_shell_coverage",
                    "metric_semantics": (
                        "native_v2_shell_available_mate_coverage;"
                        "not_frozen_graph_retention"
                    ),
                },
                "r0_v2_shell_coverage": {"accuracy": 0.375},
                "v2_child_authority": {
                    "serialization_roundtrip_exact": True,
                    "full_history_boundary_exact": True,
                    "structural_events": [
                        {"retired_cell_ids": ["old"], "child_ids": ["new"]}
                    ],
                    "adaptive_positive_lineages": {
                        "lineage_count": 1,
                        "certified_node_count": 1,
                        "postbirth_certification_receipt_count": 1,
                        "all_certification_disjoint": True,
                        "all_certification_postbirth": True,
                        "certification_leak_count": 0,
                    },
                },
            }
        },
    }

    gates = adaptive._result_gate_fields(payload)

    assert gates["r0_validation_retention_semantics"].startswith(
        "native_v2_shell_available"
    )
    assert gates["r0_frozen_native_policy_retention"]["accuracy"] == 1.0
    assert gates["r0_v2_shell_coverage"]["accuracy"] == 0.375
    assert gates["mechanism_checks"][
        "revisited_local_score_or_action_changed"
    ] is False
    assert gates["per_run_mechanism_gate_passed"] is False


def test_run_marks_result_payload_without_running_curriculum(
    tmp_path: Path, monkeypatch
) -> None:
    result = _PayloadResult()
    monkeypatch.setattr(
        adaptive, "run_native_intrinsic_curriculum", lambda **_kwargs: result
    )
    cfg = adaptive.development_config(output_dir=tmp_path, seed=29)
    observed = adaptive.run_development(cfg)
    assert observed is result
    assert result.payload["label"] == adaptive.DEVELOPMENT_LABEL
    assert result.payload["scientific_use_permitted"] is False
    protocol = result.payload["development_protocol"]
    assert protocol["profile"] == "canary"
    assert protocol["r1_reply_policy"] == "prospective_counterexample"
    assert protocol["no_learner_oracle"] is True
    assert protocol["harness_exhaustive_evaluation_used"] is True
    assert protocol["harness_evaluation_influences_learning"] is False
    assert protocol["stage_gates_are_harness_stop_go_only"] is False
    assert protocol["stage_gates_are_harness_controlled"] is True
    assert protocol["r0_stage_entry_controller"] == (
        "training_outcome_policy_mastery_harness"
    )
    assert protocol[
        "training_outcome_controls_maturity_consolidation_freeze_and_stage_entry"
    ] is True
    assert protocol["whole_curriculum_endogenous_claimed"] is False
    assert protocol[
        "validation_controls_maturity_consolidation_freeze_and_stage_entry"
    ] is False
    assert protocol[
        "validation_outcome_mastery_is_report_only_for_stage_transitions"
    ] is True
    assert protocol["validation_is_report_only_for_stage_transitions"] is False
    assert protocol[
        "validation_runtime_integrity_safety_veto_may_block_stage_entry"
    ] is True
    assert protocol["validation_does_not_select_runtime_actions"] is True


def test_cli_writes_independent_schema_and_source_identity(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(adaptive, "run_development", lambda _cfg: _FakeResult())
    assert adaptive.main([
        "--profile", "canary", "--output-dir", str(tmp_path), "--seed", "23",
        "--max-wall-seconds", "3", "--max-peak-rss-mib", "4",
    ]) == 0

    result = json.loads((tmp_path / "result.json").read_text())
    attempt = json.loads((tmp_path / "attempt.json").read_text())
    assert result == {"synthetic": True, "r0": {"pass": True}}
    assert attempt["schema_version"] == adaptive.SCHEMA_VERSION
    assert attempt["label"] == adaptive.DEVELOPMENT_LABEL
    assert attempt["scientific_use_permitted"] is False
    assert attempt["protected_outcomes_accessed"] is False
    assert attempt["learner_oracle_used"] is False
    assert attempt["harness_exhaustive_evaluation_used"] is True
    assert attempt["learner_parameter_tuning_performed"] is False
    assert attempt["profile"] == "canary"
    assert attempt["config"]["seed"] == 23
    assert attempt["config"]["output_path"] == str(tmp_path / "result.json")
    identity = attempt["source_identity"]
    assert identity["development_runner_module"] == adaptive.__name__
    assert identity["development_runner_sha256"] == hashlib.sha256(
        Path(adaptive.__file__).read_bytes()
    ).hexdigest()
    assert attempt["status"] == "COMPLETED_R0_ONLY_NO_R1_GATE"
    assert attempt["r0_pass"] is True
    assert attempt["r1_executed"] is False
    assert attempt["r1_pass"] is False
    assert attempt["work_completed"] is True
    assert attempt["scientific_gate_passed"] is False


def test_cli_normalizes_follow_through_and_reports_failed_scientific_gate(
    tmp_path: Path, monkeypatch
) -> None:
    result = _FakeGateResult(r0_pass=True, r1_executed=True, r1_pass=False)
    observed_configs = []

    def fake_run(config):
        observed_configs.append(config)
        return result

    monkeypatch.setattr(adaptive, "run_development", fake_run)
    assert adaptive.main([
        "--profile", " FOLLOW_THROUGH ", "--output-dir", str(tmp_path),
    ]) == 0

    attempt = json.loads((tmp_path / "attempt.json").read_text())
    assert len(observed_configs) == 1
    assert attempt["profile"] == adaptive.FOLLOW_THROUGH_PROFILE
    assert attempt["config"]["r1_pool_mode"] == "random"
    assert attempt["config"]["r1_train_count"] == 8
    assert attempt["config"]["r1_validation_count"] == 4
    assert attempt["config"]["r1_regression_count"] == 4
    assert attempt["config"]["r1_epochs"] == 8
    assert attempt["config"]["r1_validation_interval"] == 1
    assert attempt["config"]["r1_snapshot_interval"] == 1
    assert attempt["status"] == "COMPLETED_R1_GATE_FAILED"
    assert attempt["r1_executed"] is True
    assert attempt["r1_pass"] is False
    assert attempt["scientific_gate_passed"] is False


@pytest.mark.parametrize(
    ("result", "expected_status", "expected_gate"),
    [
        (
            _FakeGateResult(r0_pass=True, r1_executed=True, r1_pass=False),
            "COMPLETED_R1_GATE_FAILED",
            False,
        ),
        (
            _FakeGateResult(r0_pass=True, r1_executed=True, r1_pass=True),
            "COMPLETED_R1_MECHANISM_GATE_FAILED",
            True,
        ),
    ],
)
def test_cli_distinguishes_r1_gate_failure_from_success(
    tmp_path: Path, monkeypatch, result, expected_status: str, expected_gate: bool
) -> None:
    monkeypatch.setattr(adaptive, "run_development", lambda _cfg: result)
    assert adaptive.main(["--output-dir", str(tmp_path)]) == 0
    attempt = json.loads((tmp_path / "attempt.json").read_text())
    assert attempt["status"] == expected_status
    assert attempt["r0_pass"] is True
    assert attempt["r1_executed"] is True
    assert attempt["r1_pass"] is expected_gate
    assert attempt["work_completed"] is True
    assert attempt["curriculum_gate_passed"] is expected_gate
    assert attempt["per_run_mechanism_gate_passed"] is False
    assert attempt["scientific_gate_passed"] is False
    if not expected_gate:
        assert "PASSED" not in attempt["status"]


def test_ceiling_keeps_attempt_contract_and_returns_exit_two(
    tmp_path: Path, monkeypatch
) -> None:
    snapshot = tmp_path / "snapshots" / "epoch.pkl"

    def stopped(_cfg):
        raise adaptive.R1DevelopmentCeilingReached(
            epoch=1, snapshot_path=snapshot, reason="test ceiling"
        )

    monkeypatch.setattr(adaptive, "run_development", stopped)
    assert adaptive.main(["--output-dir", str(tmp_path)]) == 2
    attempt = json.loads((tmp_path / "attempt.json").read_text())
    assert attempt["status"] == "CEILING_REACHED_AT_EXACT_EPOCH_SNAPSHOT"
    assert attempt["snapshot_path"] == str(snapshot)
    assert attempt["r0_pass"] is None
    assert attempt["r1_executed"] is None
    assert attempt["r1_pass"] is None
    assert attempt["work_completed"] is False
    assert attempt["scientific_gate_passed"] is False


def test_r0_ceiling_is_non_resumable_and_keeps_gates_unknown(
    tmp_path: Path, monkeypatch
) -> None:
    def stopped(_cfg):
        raise adaptive.R0DevelopmentCeilingReached(
            epoch=1,
            reason="wall_seconds=0.001>=0.000",
        )

    monkeypatch.setattr(adaptive, "run_development", stopped)
    assert adaptive.main(["--output-dir", str(tmp_path)]) == 2
    attempt = json.loads((tmp_path / "attempt.json").read_text())
    assert attempt["status"] == (
        "R0_CEILING_REACHED_AT_COMPLETE_EPOCH_NON_RESUMABLE"
    )
    assert attempt["epoch"] == 1
    assert attempt["reason"] == "wall_seconds=0.001>=0.000"
    assert attempt["resumable"] is False
    assert "snapshot_path" not in attempt
    assert attempt["r0_pass"] is None
    assert attempt["r1_executed"] is None
    assert attempt["r1_pass"] is None
    assert attempt["work_completed"] is False
    assert attempt["curriculum_gate_passed"] is False
    assert attempt["scientific_gate_passed"] is False


def test_cli_reports_r0_gate_block_without_claiming_mechanism_pass(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        adaptive,
        "run_development",
        lambda _cfg: _FakeResult(r0_pass=False),
    )
    assert adaptive.main(["--output-dir", str(tmp_path)]) == 3
    attempt = json.loads((tmp_path / "attempt.json").read_text())
    assert attempt["status"] == "BLOCKED_AT_R0_MASTERY_GATE"
    assert attempt["r0_pass"] is False
    assert attempt["r1_executed"] is False
    assert attempt["r1_pass"] is False
    assert attempt["work_completed"] is True
    assert attempt["scientific_gate_passed"] is False
