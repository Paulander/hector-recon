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
