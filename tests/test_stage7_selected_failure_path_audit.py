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
