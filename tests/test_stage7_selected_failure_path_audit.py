import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_stage7_selected_failure_path_audit_is_non_causal_and_split() -> None:
    subprocess.run(
        [sys.executable, "scripts/summarize_stage7_selected_failure_path_audit.py"],
        cwd=ROOT,
        check=True,
    )
    payload = json.loads(
        (ROOT / "reports/structural_candidates/stage7_selected_failure_path_audit_v0.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["decision"]["status"] == "mixed_selected_path_gap_no_runtime_patch"
    assert payload["summary"]["selected_provider_counts"] == {"krk.stage0_basin": 4}
    assert payload["summary"]["selected_failure_path_class_counts"] == {
        "continuation_capacity_or_sequence_policy_gap": 2,
        "strategy_ownership_gap_existing_provider_can_convert": 2,
    }
    assert payload["summary"]["abstention_stage7_selected_penalized_count"] == 0


def test_stage7_selected_path_target_spec_keeps_targets_split() -> None:
    subprocess.run(
        [sys.executable, "scripts/summarize_stage7_selected_failure_path_audit.py"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, "scripts/summarize_stage7_selected_path_target_spec.py"],
        cwd=ROOT,
        check=True,
    )
    payload = json.loads(
        (ROOT / "reports/structural_candidates/stage7_selected_path_target_spec_v0.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["hidden_python_controller"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["status"] == "split_targets_required"
    target_by_id = {target["target_id"]: target for target in payload["target_specs"]}
    assert target_by_id["stage7.selected_path.strategy_ownership_gap.v0"]["state_count"] == 2
    assert target_by_id["stage7.selected_path.sequence_continuation_gap.v0"]["state_count"] == 2
    assert payload["decision_gate"]["status"] == "non_causal_targets_defined_no_runtime_work"


def test_stage7_selected_path_target_dataset_blocks_underpowered_sequence_target() -> None:
    subprocess.run(
        [sys.executable, "scripts/summarize_stage7_selected_failure_path_audit.py"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, "scripts/summarize_stage7_selected_path_target_spec.py"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, "scripts/build_stage7_selected_path_target_dataset.py"],
        cwd=ROOT,
        check=True,
    )
    payload = json.loads(
        (ROOT / "reports/structural_candidates/stage7_selected_path_target_dataset_v0.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["hidden_python_controller"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["ownership_target_minimally_trainable"] is True
    assert payload["summary"]["sequence_target_minimally_trainable"] is False
    assert payload["summary"]["benchmark_underpowered"] is True
    assert payload["decision"]["status"] == "ownership_target_minimal_sequence_target_underpowered"


def test_stage7_sequence_control_recovery_marks_controls_offline_only() -> None:
    subprocess.run(
        [sys.executable, "scripts/summarize_stage7_selected_failure_path_audit.py"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, "scripts/summarize_stage7_selected_path_target_spec.py"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, "scripts/build_stage7_selected_path_target_dataset.py"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, "scripts/recover_stage7_post_box_sequence_controls.py"],
        cwd=ROOT,
        check=True,
    )
    recovery = json.loads(
        (ROOT / "reports/structural_candidates/stage7_post_box_sequence_control_recovery_v0.json").read_text(
            encoding="utf-8"
        )
    )
    dataset = json.loads(
        (ROOT / "reports/structural_candidates/stage7_selected_path_target_dataset_v1.json").read_text(
            encoding="utf-8"
        )
    )

    assert recovery["runtime_behavior_changed"] is False
    assert recovery["runtime_score_changes"] is False
    assert recovery["runtime_direct_routing"] is False
    assert recovery["hidden_python_controller"] is False
    assert recovery["summary"]["usable_for_offline_benchmark"] is True
    assert recovery["summary"]["usable_for_runtime_authorization"] is False
    assert dataset["runtime_selector_implemented"] is False
    assert dataset["summary"]["sequence_target_minimally_trainable"] is True
    assert dataset["summary"]["sequence_control_caveat"] == "sandbox_sourced_controls_offline_only"
    assert dataset["decision"]["status"] == "split_target_dataset_ready_for_offline_probe_with_sandbox_sourced_sequence_controls"


def test_stage7_selected_path_probe_blocks_runtime_when_source_biased() -> None:
    for script in (
        "scripts/summarize_stage7_selected_failure_path_audit.py",
        "scripts/summarize_stage7_selected_path_target_spec.py",
        "scripts/build_stage7_selected_path_target_dataset.py",
        "scripts/recover_stage7_post_box_sequence_controls.py",
        "scripts/probe_stage7_selected_path_targets.py",
    ):
        subprocess.run([sys.executable, script], cwd=ROOT, check=True)

    payload = json.loads(
        (ROOT / "reports/structural_candidates/stage7_selected_path_target_probe_v0.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["source_bias_detected"] is True
    assert payload["decision"]["status"] == "split_targets_separable_but_source_biased_no_runtime"


def test_stage7_selected_path_architecture_review_blocks_runtime() -> None:
    for script in (
        "scripts/summarize_stage7_selected_failure_path_audit.py",
        "scripts/summarize_stage7_selected_path_target_spec.py",
        "scripts/build_stage7_selected_path_target_dataset.py",
        "scripts/recover_stage7_post_box_sequence_controls.py",
        "scripts/probe_stage7_selected_path_targets.py",
        "scripts/summarize_stage7_selected_path_architecture_review.py",
    ):
        subprocess.run([sys.executable, script], cwd=ROOT, check=True)

    payload = json.loads(
        (ROOT / "reports/structural_candidates/stage7_selected_path_architecture_review_v0.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["decision"]["status"] == "runtime_no_go_architecture_review_required"
    assert payload["decision"]["next_allowed_slice"] == "non_causal_clean_control_collection_plan"


def test_stage7_clean_artifact_manifest_finds_replay_free_clean_candidates() -> None:
    subprocess.run(
        [sys.executable, "scripts/build_stage7_clean_artifact_manifest.py"],
        cwd=ROOT,
        check=True,
    )
    payload = json.loads(
        (ROOT / "reports/structural_candidates/stage7_clean_artifact_manifest_v0.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["clean_candidate_count"] > 0
    assert payload["decision"]["status"] == "clean_artifact_manifest_ready"
    assert payload["decision"]["recommended_next_step"] == "recover_clean_sequence_controls_from_manifest_candidates"
    assert payload["decision"]["runtime_work_allowed"] is False

    rows_by_artifact = {row["artifact"]: row for row in payload["rows"]}
    baseline = rows_by_artifact["reports/krk_two_stage_abstention_stage7_baseline_3_seed11_h40.json"]
    enabled = rows_by_artifact["reports/krk_two_stage_abstention_stage7_enabled_3_seed11_h40.json"]
    assert baseline["candidate_for_clean_control_recovery"] is True
    assert enabled["candidate_for_clean_control_recovery"] is False
    assert enabled["classification"] == "repair_sandbox_sourced"


def test_stage7_clean_sequence_control_recovery_uses_manifest_clean_candidates_only() -> None:
    subprocess.run(
        [sys.executable, "scripts/build_stage7_clean_artifact_manifest.py"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, "scripts/recover_stage7_clean_sequence_controls.py"],
        cwd=ROOT,
        check=True,
    )
    payload = json.loads(
        (ROOT / "reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["usable_for_runtime_authorization"] is False
    assert payload["summary"]["control_count"] > 0
    assert payload["summary"]["role_counts"]["clean_sequence_hard_negative"] >= 5
    assert payload["acceptance"]["clean_sequence_success_controls_met"] is True
    assert payload["decision"]["status"] == "clean_sequence_controls_recovered_for_offline_source_bias_audit"

    for control in payload["controls"]:
        assert control["source_classification"] != "repair_sandbox_sourced"
        assert control["source_enabled_flags"] == []
        assert control["source_runtime_activity_fields"] == []
        if control["result"] != "mate":
            assert control["max_plies"] == 40


def test_stage7_clean_h40_label_manifest_is_bounded_and_non_causal() -> None:
    for script in (
        "scripts/build_stage7_clean_artifact_manifest.py",
        "scripts/recover_stage7_clean_sequence_controls.py",
        "scripts/summarize_stage7_clean_h40_label_manifest.py",
    ):
        subprocess.run([sys.executable, script], cwd=ROOT, check=True)
    payload = json.loads(
        (ROOT / "reports/structural_candidates/stage7_clean_h40_label_manifest_v0.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["max_total_samples"] <= 10
    assert payload["summary"]["max_horizon"] == 40
    assert payload["decision"]["status"] == "no_label_run_needed_or_topology_missing"
    assert payload["decision"]["runtime_work_allowed"] is False

    job = payload["jobs"][0]
    command = " ".join(job["command"])
    assert "--enable-stage7-king-tempo" not in command
    assert "--enable-krk-strategy-arbiter-sandbox" not in command
    assert "--enable-krk-two-stage-abstention-selector" not in command


def test_stage7_clean_h40_label_run_review_blocks_runtime_work() -> None:
    for script in (
        "scripts/build_stage7_clean_artifact_manifest.py",
        "scripts/recover_stage7_clean_sequence_controls.py",
        "scripts/summarize_stage7_clean_h40_label_manifest.py",
        "scripts/summarize_stage7_clean_h40_label_run_review.py",
    ):
        subprocess.run([sys.executable, script], cwd=ROOT, check=True)
    payload = json.loads(
        (ROOT / "reports/structural_candidates/stage7_clean_h40_label_run_review_v0.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["no_runtime_repair_flags_detected"] is True
    assert payload["decision"]["runtime_work_allowed"] is False
    assert payload["decision"]["status"] in {
        "bounded_label_run_no_novel_clean_success_controls",
        "bounded_label_run_closed_clean_success_gap",
        "bounded_label_run_clean_gap_still_open",
    }


def test_stage7_clean_control_sampling_review_blocks_unreviewed_more_labels() -> None:
    for script in (
        "scripts/build_stage7_clean_artifact_manifest.py",
        "scripts/recover_stage7_clean_sequence_controls.py",
        "scripts/summarize_stage7_clean_h40_label_manifest.py",
        "scripts/summarize_stage7_clean_h40_label_run_review.py",
        "scripts/summarize_stage7_clean_control_sampling_review.py",
    ):
        subprocess.run([sys.executable, script], cwd=ROOT, check=True)
    payload = json.loads(
        (ROOT / "reports/structural_candidates/stage7_clean_control_sampling_review_v0.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["decision"]["runtime_work_allowed"] is False
    assert "unreviewed additional Stage 7 label runs" in payload["blocked_next_steps"]
    assert payload["decision"]["recommended_next_step"] in {
        "architecture_review_before_more_stage7_clean_labels",
        "build_clean_selected_path_dataset_and_source_bias_audit",
    }


def test_stage7_clean_control_architecture_review_pauses_stage7_collection() -> None:
    for script in (
        "scripts/build_stage7_clean_artifact_manifest.py",
        "scripts/recover_stage7_clean_sequence_controls.py",
        "scripts/summarize_stage7_clean_h40_label_manifest.py",
        "scripts/summarize_stage7_clean_h40_label_run_review.py",
        "scripts/summarize_stage7_clean_control_sampling_review.py",
        "scripts/summarize_stage7_clean_control_architecture_review.py",
    ):
        subprocess.run([sys.executable, script], cwd=ROOT, check=True)
    payload = json.loads(
        (ROOT / "reports/structural_candidates/stage7_clean_control_architecture_review_v0.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["decision"]["runtime_work_allowed"] is False
    assert payload["decision"]["status"] == "stage7_clean_control_collection_closed_heldout_only"
    assert (
        payload["decision"]["recommended_next_step"]
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )
    assert payload["evidence"]["protected_failure_contrast_collection_command_available"] is True
    assert payload["evidence"]["protected_failure_contrast_approval_receipt_present"] is False
    assert payload["evidence"]["protected_failure_contrast_approval_receipt_valid"] is False
    assert payload["evidence"]["protected_failure_contrast_runner_collection_run_allowed"] is False
    assert payload["evidence"]["protected_failure_contrast_runner_execution_requested"] is False
    assert payload["evidence"]["protected_failure_contrast_runner_processed_job_count"] == 0
    assert payload["evidence"]["protected_failure_contrast_runner_executed_job_count"] == 0
    assert any("now meet" in item for item in payload["conclusions"])
    assert "unreviewed additional Stage 7 h40 labels" in payload["blocked_next_steps"]
    preferred = [path for path in payload["recommended_paths"] if path["preferred"] is True]
    assert preferred[0]["path_id"] == "broader_krk_strategy_sequence_architecture_review"


def test_krk_strategy_sequence_architecture_review_keeps_stage7_held_out() -> None:
    subprocess.run(
        [sys.executable, "scripts/summarize_krk_strategy_sequence_architecture_review.py"],
        cwd=ROOT,
        check=True,
    )
    payload = json.loads(
        (ROOT / "reports/krk_strategy_sequence_architecture_review_v0.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["decision"]["runtime_work_allowed"] is False
    assert payload["decision"]["recommended_next_step"] == "define_krk_strategy_sequence_evidence_plan_v0"
    assert "another Stage 7 local repair" in payload["forbidden_shortcuts"]
    objectives = {item["objective_id"] for item in payload["next_architecture_objectives"]}
    assert {"strategy_ownership_evidence", "sequence_policy_evidence", "curriculum_boundary_evidence"} <= objectives


def test_krk_strategy_sequence_evidence_plan_is_non_causal_and_split() -> None:
    subprocess.run(
        [sys.executable, "scripts/summarize_krk_strategy_sequence_architecture_review.py"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, "scripts/summarize_krk_strategy_sequence_evidence_plan.py"],
        cwd=ROOT,
        check=True,
    )
    payload = json.loads(
        (ROOT / "reports/krk_strategy_sequence_evidence_plan_v0.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["decision"]["runtime_work_allowed"] is False
    assert payload["decision"]["recommended_next_step"] == "run_replay_free_strategy_sequence_inventory"
    tracks = {track["track_id"]: track for track in payload["tracks"]}
    assert set(tracks) == {"strategy_ownership", "sequence_policy", "curriculum_boundary"}
    assert tracks["strategy_ownership"]["stage7_usage"] == "held_out_challenge_only"
    assert tracks["sequence_policy"]["stage7_usage"] == "evaluation_only_no_training_rows"
    assert "runtime selector implementation" in payload["blocked_actions"]


def test_krk_strategy_sequence_inventory_blocks_runtime_on_sequence_gap() -> None:
    for script in (
        "scripts/summarize_krk_strategy_sequence_architecture_review.py",
        "scripts/summarize_krk_strategy_sequence_evidence_plan.py",
        "scripts/summarize_krk_strategy_sequence_inventory.py",
    ):
        subprocess.run([sys.executable, script], cwd=ROOT, check=True)
    payload = json.loads(
        (ROOT / "reports/krk_strategy_sequence_inventory_v0.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["decision"]["runtime_work_allowed"] is False
    assert (
        payload["decision"]["status"]
        == "replay_free_inventory_state_holdout_gap_blocks_runtime"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "review_state_holdout_signal_before_runtime_or_continue_protected_failure_contrast_gate"
    )
    assert payload["gap_summary"]["sequence_policy_has_clean_success_gap"] is False
    assert payload["gap_summary"]["sequence_policy_clean_gate_closed"] is True
    assert payload["gap_summary"]["state_holdout_gap_blocks_runtime"] is True
    assert payload["sequence_policy_inventory"]["ready_for_runtime_review"] is False


def test_stage7_curriculum_boundary_decision_reclassifies_box_shrink() -> None:
    subprocess.run(
        [sys.executable, "scripts/summarize_stage7_curriculum_boundary_decision.py"],
        cwd=ROOT,
        check=True,
    )
    payload = json.loads(
        (ROOT / "reports/structural_candidates/stage7_curriculum_boundary_decision_v0.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["decision"]["status"] == "box_shrink_reclassified_as_local_evidence_handoff_trigger"
    assert (
        payload["decision"]["recommended_next_step"]
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )
    assert payload["decision"]["stage7_standalone_repair_target"] is False
    assert payload["decision"]["box_shrink_promotable_independent_stage"] is False
    assert payload["current_evidence_state"]["stage7_clean_success_controls_met"] is True
    assert payload["current_evidence_state"]["stage7_clean_hard_negatives_met"] is True
    assert (
        payload["current_evidence_state"]["stage7_clean_review_next_step"]
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )
    assert payload["new_role_for_stage7"]["stage7_residuals_role"] == "heldout_challenge_set"
    assert "more Stage 7 local move-shape tuning" in payload["explicitly_rejected_next_steps"]
