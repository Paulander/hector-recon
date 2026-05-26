#!/usr/bin/env python3
"""Tests for the Stage 5 guardrail control-debt review."""

import importlib.util
import json
from pathlib import Path


_spec = importlib.util.spec_from_file_location(
    "review_krk_stage5_guardrail_control_debt_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_stage5_guardrail_control_debt_v0.py",
)
assert _spec is not None
assert _spec.loader is not None
_review = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_review)

_split_spec = importlib.util.spec_from_file_location(
    "write_krk_stage5_guardrail_semantics_split_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_stage5_guardrail_semantics_split_v0.py",
)
assert _split_spec is not None
assert _split_spec.loader is not None
_split = importlib.util.module_from_spec(_split_spec)
_split_spec.loader.exec_module(_split)

_debt_audit_spec = importlib.util.spec_from_file_location(
    "audit_krk_stage5_local_reward_contract_debt_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "audit_krk_stage5_local_reward_contract_debt_v0.py",
)
assert _debt_audit_spec is not None
assert _debt_audit_spec.loader is not None
_debt_audit = importlib.util.module_from_spec(_debt_audit_spec)
_debt_audit_spec.loader.exec_module(_debt_audit)

_replacement_review_spec = importlib.util.spec_from_file_location(
    "write_krk_clean_retrain_retry1_replacement_readiness_review_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_clean_retrain_retry1_replacement_readiness_review_v0.py",
)
assert _replacement_review_spec is not None
assert _replacement_review_spec.loader is not None
_replacement_review = importlib.util.module_from_spec(_replacement_review_spec)
_replacement_review_spec.loader.exec_module(_replacement_review)

_stage4_review_spec = importlib.util.spec_from_file_location(
    "review_krk_retry1_stage4_caveat_control_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_retry1_stage4_caveat_control_v0.py",
)
assert _stage4_review_spec is not None
assert _stage4_review_spec.loader is not None
_stage4_review = importlib.util.module_from_spec(_stage4_review_spec)
_stage4_review_spec.loader.exec_module(_stage4_review)

_preservation_checks_spec = importlib.util.spec_from_file_location(
    "write_krk_retry1_preservation_checks_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_retry1_preservation_checks_v0.py",
)
assert _preservation_checks_spec is not None
assert _preservation_checks_spec.loader is not None
_preservation_checks = importlib.util.module_from_spec(_preservation_checks_spec)
_preservation_checks_spec.loader.exec_module(_preservation_checks)

_snapshot_manifest_spec = importlib.util.spec_from_file_location(
    "write_krk_retry1_protected_stack_snapshot_manifest_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_retry1_protected_stack_snapshot_manifest_v0.py",
)
assert _snapshot_manifest_spec is not None
assert _snapshot_manifest_spec.loader is not None
_snapshot_manifest = importlib.util.module_from_spec(_snapshot_manifest_spec)
_snapshot_manifest_spec.loader.exec_module(_snapshot_manifest)

_replacement_packet_spec = importlib.util.spec_from_file_location(
    "write_krk_retry1_clean_stack_replacement_review_packet_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_retry1_clean_stack_replacement_review_packet_v0.py",
)
assert _replacement_packet_spec is not None
assert _replacement_packet_spec.loader is not None
_replacement_packet = importlib.util.module_from_spec(_replacement_packet_spec)
_replacement_packet_spec.loader.exec_module(_replacement_packet)


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _stage5_payload() -> dict:
    return {
        "total": 4,
        "no_move": 0,
        "improved": 2,
        "worsened": 2,
        "optimal": 2,
        "playouts": {"mate": 4},
        "one_ply_status": "failed",
        "conversion_status": "passed",
        "shadow_candidate_count": 0,
        "label": "fence_established",
        "stagnation_breaker_king_support_bonus": 2.0,
        "early_stop_stable_suggestions": 2,
        "handoff_packet_counts_by_phase": {
            "post_own_move": {"failed": 2, "confirmed": 2},
            "playout_summary": {"confirmed": 4},
        },
        "handoff_packets": [
            {
                "phase": "post_own_move",
                "status": "failed",
                "achieved": ["visible_fence_contract_confirmed"],
                "failed": ["reward_confirmed.fence_established"],
                "evidence_terms": {
                    "fen": "7k/8/8/8/R7/8/5K2/8 w - - 0 1",
                    "move": "f2g3",
                    "chosen_reward": -0.75,
                    "oracle_reward": 0.149,
                    "reward_confirmed": False,
                    "visible_fence_contract_confirmed": True,
                    "fence_exists_after_own_move": True,
                    "fence_stable_after_own_move": False,
                    "cut_axis_after_own_move": "edge",
                    "rook_safe_after_own_move": True,
                    "box_area_after_own_move": 28,
                },
            },
            {
                "phase": "post_own_move",
                "status": "confirmed",
                "achieved": [
                    "reward_confirmed.fence_established",
                    "visible_fence_contract_confirmed",
                ],
                "failed": [],
                "evidence_terms": {
                    "fen": "4k3/R7/K7/8/8/8/8/8 w - - 0 1",
                    "move": "a7h7",
                    "chosen_reward": 0.074,
                    "oracle_reward": 0.074,
                    "reward_confirmed": True,
                    "visible_fence_contract_confirmed": True,
                    "fence_exists_after_own_move": True,
                    "fence_stable_after_own_move": False,
                    "cut_axis_after_own_move": "edge",
                    "rook_safe_after_own_move": True,
                    "box_area_after_own_move": 7,
                },
            },
        ],
    }


def test_stage5_control_debt_review_splits_conversion_from_one_ply_debt(tmp_path: Path):
    overlay = _write_json(tmp_path / "overlay.json", _stage5_payload())
    control = _write_json(tmp_path / "control.json", _stage5_payload())
    promotion = _write_json(
        tmp_path / "promotion.json",
        {
            "promotion_status": "overlay_only",
            "failures": [],
            "guardrail_control_debt": [{"kind": "guardrail_control_debt"}],
            "guardrail_deltas_vs_control": [{"regressed_vs_control": False}],
        },
    )
    inspection = _write_json(
        tmp_path / "inspection.json",
        {"status": "stage6_gap_explained_by_validation_profile_mismatch"},
    )

    review = _review.build_review(
        overlay_artifact=overlay,
        base_control_artifact=control,
        promotion_eval_artifact=promotion,
        inspection_artifact=inspection,
    )

    assert review["status"] == "stage5_one_ply_guardrail_control_debt_confirmed"
    assert review["decision"]["stage5_conversion_preserved"] is True
    assert review["decision"]["stage5_one_ply_debt_reproduces_in_base_control"] is True
    assert review["decision"]["stage5_overlay_regressed_vs_base_control"] is False
    assert review["decision"]["should_quarantine_stage6_overlay_for_stage5_one_ply_debt"] is False
    assert review["decision"]["should_replace_protected_stack_now"] is False
    assert review["guardrail_definition_recommendation"]["split_required"] is True
    assert review["invariants"]["runtime_defaults_changed"] is False
    assert review["invariants"]["stage7_promotion"] is False
    assert review["invariants"]["stage8_training"] is False


def test_generated_stage5_control_debt_review_artifact_preserves_decision():
    path = Path("reports/krk_stage5_guardrail_control_debt_review_v0.json")
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_stage5_guardrail_control_debt_review.v0"
    assert payload["decision"]["stage5_overlay_regressed_vs_base_control"] is False
    assert payload["decision"]["stage5_conversion_preserved"] is True
    assert payload["decision"]["stage5_one_ply_debt_reproduces_in_base_control"] is True
    assert payload["decision"]["should_replace_protected_stack_now"] is False
    assert payload["guardrail_definition_recommendation"]["split_required"] is True
    assert payload["stage5_overlay"]["mate_rate"] == 1.0
    assert payload["stage5_base_control"]["mate_rate"] == 1.0


def test_stage5_guardrail_semantics_split_artifact_blocks_clean_replacement():
    payload = json.loads(
        Path("reports/krk_stage5_guardrail_semantics_split_v0.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["schema_version"] == "krk_stage5_guardrail_semantics_split.v0"
    assert payload["status"] == "stage5_guardrail_semantics_split_defined"
    assert payload["decision"]["clean_stack_replacement_allowed"] is False
    assert payload["decision"]["stage6_overlay_use_allowed_as_overlay_only"] is True
    tracks = {track["track_id"]: track for track in payload["guardrail_tracks"]}
    assert "stage5.conversion_preservation_guardrail" in tracks
    assert "stage5.local_reward_contract_guardrail" in tracks
    assert (
        payload["clean_retrain_promotion_policy"][
            "stage5_local_reward_debt_reproduces_in_base_control"
        ]
        == "overlay_only_control_debt"
    )


def test_stage5_local_reward_contract_debt_audit_classifies_semantics_debt():
    payload = json.loads(
        Path("reports/krk_stage5_local_reward_contract_debt_audit_v0.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["schema_version"] == "krk_stage5_local_reward_contract_debt_audit.v0"
    assert payload["status"] == "stage5_local_reward_contract_debt_is_guardrail_semantics_debt"
    assert payload["decision"]["overlay_matches_base_control_patterns"] is True
    assert payload["decision"]["local_reward_debt_is_stage6_regression"] is False
    assert payload["decision"]["clean_stack_replacement_allowed"] is False
    assert (
        payload["pattern_summary"]["semantic_alignment_counts"][
            "visible_contract_and_conversion_without_local_reward"
        ]
        == 156
    )
    assert payload["invariants"]["runtime_defaults_changed"] is False
    assert payload["invariants"]["stage7_promotion"] is False


def test_retry1_replacement_readiness_review_allows_only_remaining_checks():
    payload = json.loads(
        Path("reports/krk_clean_retrain_retry1_replacement_readiness_review_v0.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["schema_version"] == "krk_clean_retrain_retry1_replacement_readiness_review.v0"
    assert payload["status"] == "retry1_ready_for_remaining_preservation_checks_not_replacement"
    assert payload["decision"]["stage6_target_passed_corrected_profile"] is True
    assert payload["decision"]["stage5_conversion_preservation_passed"] is True
    assert (
        payload["decision"][
            "stage5_local_reward_debt_accepted_as_known_base_control_debt_for_overlay_review"
        ]
        is True
    )
    assert payload["decision"]["clean_stack_replacement_allowed"] is False
    assert payload["replacement_policy"]["allowed_now"] is False
    required_checks = {item["check_id"] for item in payload["remaining_required_checks"]}
    assert "stage4_overlay_caveat_control_review" in required_checks
    assert "m1_m4_preservation_suite" in required_checks
    assert "kpk_kqk_bridge_preservation" in required_checks
    assert payload["invariants"]["runtime_defaults_changed"] is False
    assert payload["invariants"]["stage8_training"] is False


def test_retry1_stage4_caveat_control_review_artifact_blocks_replacement():
    payload = json.loads(
        Path("reports/krk_clean_retrain_retry1_stage4_caveat_control_review_v0.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["schema_version"] == "krk_clean_retrain_retry1_stage4_caveat_control_review.v0"
    assert payload["status"] == "stage4_caveat_reproduces_in_base_control_no_overlay_regression"
    assert payload["decision"]["stage4_overlay_regressed_vs_base_control"] is False
    assert payload["decision"]["stage4_caveat_reproduces_in_base_control"] is True
    assert payload["decision"]["clean_stack_replacement_allowed"] is False
    assert payload["delta_overlay_vs_base_control"]["mate_delta"] == 0
    assert payload["delta_overlay_vs_base_control"]["max_plies_delta"] == 0
    assert payload["delta_overlay_vs_base_control"]["shadow_candidate_delta"] == 0
    assert payload["stage4_overlay"]["mate"] == 268
    assert payload["stage4_base_control"]["mate"] == 268
    assert payload["invariants"]["runtime_defaults_changed"] is False
    assert payload["invariants"]["stage7_promotion"] is False
    assert payload["invariants"]["stage8_training"] is False


def test_retry1_preservation_checks_artifact_passes_but_does_not_replace():
    payload = json.loads(
        Path("reports/krk_clean_retrain_retry1_preservation_checks_v0.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["schema_version"] == "krk_clean_retrain_retry1_preservation_checks.v0"
    assert payload["status"] == "retry1_m1_m4_and_bridge_preservation_checks_passed"
    assert payload["decision"]["stage4_caveat_control_review_passed"] is True
    assert payload["decision"]["m1_m4_preservation_passed"] is True
    assert payload["decision"]["kpk_kqk_bridge_preservation_passed"] is True
    assert payload["decision"]["clean_stack_replacement_allowed"] is False
    assert payload["test_run"]["result"] == "passed"
    assert payload["test_run"]["passed_count"] == 78
    assert "protected_stack_snapshot_manifest" in payload["remaining_required_checks"]
    assert payload["runtime_behavior_changed"] is False
    assert payload["invariants"]["runtime_defaults_changed"] is False
    assert payload["hidden_python_controller"] is False
    assert payload["invariants"]["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False


def test_retry1_snapshot_manifest_records_paths_without_replacement():
    payload = json.loads(
        Path(
            "reports/krk_clean_retrain_retry1_protected_stack_snapshot_manifest_v0.json"
        ).read_text(encoding="utf-8")
    )

    assert (
        payload["schema_version"]
        == "krk_clean_retrain_retry1_protected_stack_snapshot_manifest.v0"
    )
    assert payload["status"] == "retry1_protected_stack_snapshot_manifest_ready_no_replacement"
    assert payload["decision"]["manifest_records_current_protected_stack"] is True
    assert payload["decision"]["manifest_records_retry1_candidate_stack"] is True
    assert payload["decision"]["all_referenced_paths_exist"] is True
    assert payload["decision"]["clean_stack_replacement_allowed_by_manifest"] is False
    assert payload["path_existence"]["missing_paths"] == []
    assert "stage5_fence" in payload["current_protected_stack"]
    assert "stage6_drive_overlay" in payload["current_protected_stack"]
    assert "stage5_fence" in payload["retry1_candidate_stack"]
    assert "stage6_drive_overlay" in payload["retry1_candidate_stack"]
    assert payload["invariants"]["files_copied_or_replaced"] is False
    assert payload["invariants"]["runtime_defaults_changed"] is False
    assert payload["invariants"]["stage7_promotion"] is False
    assert payload["invariants"]["stage8_training"] is False


def test_retry1_clean_stack_replacement_packet_requires_explicit_approval():
    payload = json.loads(
        Path(
            "reports/krk_clean_retrain_retry1_clean_stack_replacement_review_packet_v0.json"
        ).read_text(encoding="utf-8")
    )

    assert (
        payload["schema_version"]
        == "krk_clean_retrain_retry1_clean_stack_replacement_review_packet.v0"
    )
    assert (
        payload["status"]
        == "retry1_clean_stack_replacement_review_ready_explicit_approval_required"
    )
    assert payload["decision"]["replacement_review_ready"] is True
    assert payload["decision"]["implementation_allowed_by_this_packet"] is False
    assert payload["decision"]["clean_stack_replacement_performed"] is False
    assert (
        payload["decision"]["explicit_human_approval_required_before_any_file_change"]
        is True
    )
    assert all(payload["prerequisites"].values())
    assert payload["invariants"]["files_copied_or_replaced"] is False
    assert payload["invariants"]["runtime_defaults_changed"] is False
    assert payload["invariants"]["gameplay_topology_mutation"] is False
    assert payload["invariants"]["stage7_promotion"] is False
    assert payload["invariants"]["stage8_training"] is False
    forbidden = set(payload["required_approval_scope_if_approved_later"]["forbidden"])
    assert "promote Stage 7" in forbidden
    assert "train Stage 8" in forbidden
    assert "delete or overwrite rollback sources" in forbidden
