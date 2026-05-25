#!/usr/bin/env python3
"""Tests for KRK next-milestone decision artifacts."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location(
    "write_krk_curriculum_next_milestone_reviews_v0",
    ROOT / "scripts" / "write_krk_curriculum_next_milestone_reviews_v0.py",
)
assert _spec is not None
assert _spec.loader is not None
_reviews = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_reviews)

_adoption_spec = importlib.util.spec_from_file_location(
    "adopt_krk_retry1_protected_stack_v0",
    ROOT / "scripts" / "adopt_krk_retry1_protected_stack_v0.py",
)
assert _adoption_spec is not None
assert _adoption_spec.loader is not None
_adoption = importlib.util.module_from_spec(_adoption_spec)
_adoption_spec.loader.exec_module(_adoption)


def _load(path: str) -> dict:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_replacement_deferred_review_blocks_path_changes_without_approval():
    payload = _load("reports/krk_clean_stack_replacement_deferred_review_v0.json")

    assert payload["schema_version"] == "krk_clean_stack_replacement_deferred_review.v0"
    assert payload["status"] == "clean_stack_adoption_deferred_explicit_approval_required"
    assert payload["decision_state"] == "clean_stack_adoption_rejected_or_deferred"
    assert payload["replacement_review_ready"] is True
    assert payload["implementation_allowed_by_review_packet"] is False
    assert payload["explicit_approval_detected"] is False
    assert "Approve updating protected Stage 5/6 stack references" in payload["exact_approval_request"]
    assert payload["invariants"]["protected_stack_replacement_performed"] is False
    assert payload["invariants"]["runtime_defaults_changed"] is False
    assert payload["invariants"]["stage7_promotion"] is False
    assert payload["invariants"]["stage8_training"] is False


def test_stage4_caveat_decision_gate_keeps_runtime_blocked():
    matrix = _load("reports/krk_stage4_caveat_diagnostic_matrix_v0.json")
    gate = _load("reports/krk_stage4_caveat_decision_gate_v0.json")

    assert matrix["schema_version"] == "krk_stage4_caveat_diagnostic_matrix.v0"
    assert gate["schema_version"] == "krk_stage4_caveat_decision_gate.v0"
    assert gate["status"] == "stage4_candidate_generation_gap_with_known_residual_guardrail"
    assert "stage4_candidate_generation_gap" in gate["selected_decisions"]
    assert "stage4_known_residual_keep_as_guardrail" in gate["selected_decisions"]
    assert "stage4_runtime_sandbox_review_ready" in gate["rejected_decisions"]
    assert gate["runtime_or_training_authorized"] is False
    assert matrix["stage4_observed_caveat"]["max_plies"] == 32
    hypotheses = {item["hypothesis"]: item for item in matrix["hypotheses"]}
    assert hypotheses["candidate_generation_gap"]["confidence"] == "high"
    assert gate["invariants"]["runtime_behavior_changed"] is False
    assert gate["invariants"]["protected_stack_replacement_performed"] is False


def test_stage7_unlock_review_keeps_stage8_blocked():
    unlock = _load("reports/structural_candidates/stage7_heldout_unlock_review_v0.json")
    blocker = _load("reports/structural_candidates/stage7_to_stage8_blocker_review_v0.json")

    assert unlock["schema_version"] == "stage7_heldout_unlock_review.v0"
    assert unlock["status"] == "stage7_unlock_path_identified_broader_sequence_control_not_micro_repair"
    assert unlock["stage7_status"] == "local_valid_composition_quarantined"
    assert "stage7_sequence_policy_needed" in unlock["selected_unlock_paths"]
    assert "stage7_curriculum_boundary_confirmed" in unlock["selected_unlock_paths"]
    assert blocker["schema_version"] == "stage7_to_stage8_blocker_review.v0"
    assert blocker["status"] == "stage8_remains_blocked_with_review"
    assert blocker["stage7_promotion_allowed"] is False
    assert blocker["stage8_training_allowed"] is False
    assert blocker["invariants"]["stage7_promotion"] is False
    assert blocker["invariants"]["stage8_training"] is False


def test_curriculum_next_milestone_decision_is_review_only():
    payload = _load("reports/krk_curriculum_next_milestone_decision_v0.json")

    assert payload["schema_version"] == "krk_curriculum_next_milestone_decision.v0"
    assert payload["status"] == "krk_curriculum_next_milestone_review_ready"
    assert "clean_stack_adopted_and_validated" in payload["decision_states"]
    assert "stage4_caveat_reduction_path_identified" in payload["decision_states"]
    assert "stage7_unlock_path_identified" in payload["decision_states"]
    assert "stage8_remains_blocked_with_review" in payload["decision_states"]
    assert (
        payload["current_adopted_protected_stack_status"]
        == "retry1_protected_stage5_6_stack_adopted_manifest_only"
    )
    assert payload["invariants"]["active_stack_reference_updated"] is True
    assert payload["invariants"]["protected_stack_replacement_performed"] is False
    assert payload["invariants"]["runtime_behavior_changed"] is False
    assert payload["invariants"]["stage7_promotion"] is False
    assert payload["invariants"]["stage8_training"] is False
    assert "destructive snapshot replacement without rollback review" in payload["what_remains_forbidden"]


def test_retry1_active_stack_manifest_is_rollback_aware_and_non_destructive():
    payload = _load("reports/krk_active_protected_stack_v0.json")

    assert payload["schema_version"] == "krk_active_protected_stack.v0"
    assert payload["status"] == "retry1_protected_stage5_6_stack_adopted_manifest_only"
    assert payload["decision"]["clean_stack_adopted"] is True
    assert payload["decision"]["adoption_mechanism"] == "tracked_active_stack_manifest"
    assert payload["decision"]["filesystem_snapshots_replaced"] is False
    assert "stage5_fence" in payload["active_protected_stack"]
    assert "stage6_drive_overlay" in payload["active_protected_stack"]
    assert "stage5_fence" in payload["rollback_protected_stack"]
    assert "stage6_drive_overlay" in payload["rollback_protected_stack"]
    assert payload["adoption_scope"]["stage7"] == "unchanged_quarantined_held_out"
    assert payload["adoption_scope"]["stage8"] == "unchanged_blocked"
    assert payload["invariants"]["active_stack_reference_updated"] is True
    assert payload["invariants"]["files_copied_or_replaced"] is False
    assert payload["invariants"]["rollback_paths_preserved"] is True
    assert payload["invariants"]["runtime_defaults_changed"] is False
    assert payload["invariants"]["stage7_promotion"] is False
    assert payload["invariants"]["stage8_training"] is False


def test_retry1_post_replacement_validation_passes_without_runtime_changes():
    payload = _load("reports/krk_clean_stack_post_replacement_validation_v0.json")

    assert payload["schema_version"] == "krk_clean_stack_post_replacement_validation.v0"
    assert payload["status"] == "clean_stack_adopted_and_validated"
    assert payload["decision"]["clean_stack_adopted_and_validated"] is True
    assert payload["decision"]["stage7_status"] == "unchanged_quarantined_held_out"
    assert payload["decision"]["stage8_status"] == "unchanged_blocked"
    validation = payload["validation"]
    assert validation["stage5_conversion_preservation_guardrail"]["passed"] is True
    assert validation["stage5_conversion_preservation_guardrail"]["playouts"] == {"mate": 300}
    assert validation["stage6_drive_h40_historical_bonus"]["passed"] is True
    assert validation["stage6_drive_h40_historical_bonus"]["playouts"] == {"mate": 300}
    assert validation["stage4_caveat_control_no_regression"]["passed"] is True
    assert validation["m1_m4_preservation"]["passed"] is True
    assert validation["kpk_kqk_bridge_preservation"]["passed"] is True
    assert payload["invariants"]["runtime_behavior_changed"] is False
    assert payload["invariants"]["runtime_defaults_changed"] is False
    assert payload["invariants"]["files_copied_or_replaced"] is False
    assert payload["invariants"]["stage7_promotion"] is False
    assert payload["invariants"]["stage8_training"] is False
