#!/usr/bin/env python3
"""Summarize stratified gaps in the KRK control-plane evidence pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


MANIFEST = Path("reports/krk_control_plane_manifest_v0.json")


def _load_json(root: Path, relative_path: Path) -> dict[str, Any]:
    payload = json.loads((root / relative_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {relative_path}")
    return payload


def build_gap_report(repo_root: Path) -> dict[str, Any]:
    manifest = _load_json(repo_root, MANIFEST)
    if manifest.get("causal_status") != "non_causal_manifest":
        raise ValueError("manifest must remain non-causal")
    summary = manifest.get("summary") or {}
    coverage_by_field = {item["field"]: item for item in manifest.get("field_coverage") or []}
    strategy_summary = (coverage_by_field.get("strategy_proposal_frames") or {}).get("summary") or {}
    records_by_stage = strategy_summary.get("records_by_source_stage") or {}

    report = {
        "schema_version": "krk_control_plane_gap_report.v0",
        "causal_status": "non_causal_gap_report",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "hidden_python_controller": False,
        "gameplay_topology_mutation": False,
        "runtime_arbiter_added": False,
        "runtime_terminals_added": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(MANIFEST)],
        "coverage_snapshot": {
            "strategy_record_count": summary.get("strategy_record_count"),
            "strategy_proposal_count": summary.get("strategy_proposal_count"),
            "records_by_source_stage": records_by_stage,
            "monitor_record_count": summary.get("monitor_record_count"),
            "plan_window_count": summary.get("plan_window_count"),
            "sequence_seed_step_count": summary.get("sequence_seed_step_count"),
            "sequence_expanded_step_count": summary.get("sequence_expanded_step_count"),
            "new_playouts_added": summary.get("new_playouts_added"),
        },
        "stratified_gaps": [
            {
                "gap_id": "no_unified_control_plane_frames",
                "priority": "p0",
                "evidence": "Manifest coverage is field-level; downstream probes still need per-state ControlPlaneEvidenceFrame exports.",
                "affected_tracks": [
                    "strategy_arbitration",
                    "internal_monitors",
                    "sequence_policy",
                    "promotion_review",
                ],
                "minimum_next_step": "export_replay_free_control_plane_frames_v0",
                "causal_allowed": False,
            },
            {
                "gap_id": "sequence_labels_stage7_only",
                "priority": "p1",
                "evidence": (
                    f"Sequence labels have {summary.get('sequence_seed_step_count')} seed steps and "
                    f"{summary.get('sequence_expanded_step_count')} expanded steps, concentrated in Stage 7 residuals."
                ),
                "affected_tracks": ["sequence_policy", "curriculum_boundary_review"],
                "minimum_next_step": "design_stratified_sequence_data_plan_before_training",
                "causal_allowed": False,
            },
            {
                "gap_id": "plan_window_evidence_stage7_only",
                "priority": "p1",
                "evidence": f"Plan-window evidence currently has {summary.get('plan_window_count')} windows, primarily Stage 7.",
                "affected_tracks": ["plan_capsule_self_monitoring", "strategy_arbitration"],
                "minimum_next_step": "define_cross_stage_plan_window_export_requirements",
                "causal_allowed": False,
            },
            {
                "gap_id": "growth_governor_not_frame_level",
                "priority": "p1",
                "evidence": "GrowthGovernor status exists as plan/design evidence, not per-frame status.",
                "affected_tracks": ["structural_growth", "promotion_review"],
                "minimum_next_step": "non_causal_growth_governor_frame_status_design",
                "causal_allowed": False,
            },
            {
                "gap_id": "stage4_h40_caveat_not_explained",
                "priority": "p2",
                "evidence": "Stage 4 is clean in the 500-sample profile but has an h40 overlay/base-control caveat.",
                "affected_tracks": ["guardrail_definition", "arbitrary_krk_validation"],
                "minimum_next_step": "keep_as_guardrail_definition_caveat_until_control_frames_exist",
                "causal_allowed": False,
            },
            {
                "gap_id": "cross_domain_transfer_not_in_frame_contract_yet",
                "priority": "p2",
                "evidence": "KPK/KQK bridge sanity is referenced historically but not exported as control-plane frames.",
                "affected_tracks": ["kpk_kqk_transfer", "domain_generalization"],
                "minimum_next_step": "add_cross_domain_frame_requirements_after_krk_frame_export",
                "causal_allowed": False,
            },
        ],
        "recommended_next_slice": {
            "slice_id": "export_replay_free_control_plane_frames_v0",
            "reason": (
                "Before collecting new data or sandboxing any mechanism, existing evidence should be "
                "exported into unified per-state frames so strategy, monitor, sequence, and guardrail "
                "tracks can be compared without Stage 7-specific scripts."
            ),
            "allowed": True,
            "causal": False,
            "new_playouts_allowed": False,
        },
        "deferred_until_after_frame_export": [
            "new_sequence_training_data_collection",
            "runtime_strategy_arbiter_sandbox",
            "runtime_internal_terminal_sandbox",
            "stage8_training",
            "stage7_promotion",
        ],
        "blocked_next_steps": manifest.get("blocked_next_steps") or [],
    }
    validate_gap_report(report)
    return report


def validate_gap_report(report: dict[str, Any]) -> None:
    if report.get("causal_status") != "non_causal_gap_report":
        raise ValueError("gap report must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_score_changes",
        "runtime_direct_routing",
        "runtime_dtm_or_tablebase_lookup",
        "hidden_python_controller",
        "gameplay_topology_mutation",
        "runtime_arbiter_added",
        "runtime_terminals_added",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if report.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if report["recommended_next_slice"]["causal"]:
        raise ValueError("recommended next slice must remain non-causal")
    if report["recommended_next_slice"]["new_playouts_allowed"]:
        raise ValueError("recommended next slice must remain replay-free")


def render_markdown(report: dict[str, Any]) -> str:
    snapshot = report["coverage_snapshot"]
    recommendation = report["recommended_next_slice"]
    lines = [
        "# KRK Control-Plane Gap Report v0",
        "",
        "This is a non-causal gap report. It recommends replay-free evidence export, "
        "not runtime repair, Stage 7 promotion, Stage 8 training, or sandboxing.",
        "",
        "## Coverage Snapshot",
        "",
        f"- Strategy records: `{snapshot.get('strategy_record_count')}`",
        f"- Strategy proposals: `{snapshot.get('strategy_proposal_count')}`",
        f"- Records by source stage: `{snapshot.get('records_by_source_stage')}`",
        f"- Monitor records: `{snapshot.get('monitor_record_count')}`",
        f"- Plan windows: `{snapshot.get('plan_window_count')}`",
        f"- Sequence seed steps: `{snapshot.get('sequence_seed_step_count')}`",
        f"- Expanded sequence steps: `{snapshot.get('sequence_expanded_step_count')}`",
        f"- New playouts added: `{snapshot.get('new_playouts_added')}`",
        "",
        "## Stratified Gaps",
        "",
    ]
    for gap in report["stratified_gaps"]:
        lines.extend(
            [
                f"### {gap['gap_id']}",
                "",
                f"- Priority: `{gap['priority']}`",
                f"- Evidence: {gap['evidence']}",
                f"- Affected tracks: `{', '.join(gap['affected_tracks'])}`",
                f"- Minimum next step: `{gap['minimum_next_step']}`",
                f"- Causal allowed: `{gap['causal_allowed']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Recommended Next Slice",
            "",
            f"- Slice: `{recommendation['slice_id']}`",
            f"- Reason: {recommendation['reason']}",
            f"- Causal: `{recommendation['causal']}`",
            f"- New playouts allowed: `{recommendation['new_playouts_allowed']}`",
            "",
            "## Deferred",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in report["deferred_until_after_frame_export"])
    lines.extend(["", "## Blocked Next Steps", ""])
    lines.extend(f"- `{item}`" for item in report["blocked_next_steps"])
    lines.append("")
    return "\n".join(lines)


def write_outputs(report: dict[str, Any], report_root: Path) -> None:
    report_root.mkdir(parents=True, exist_ok=True)
    (report_root / "krk_control_plane_gap_report_v0.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (report_root / "krk_control_plane_gap_report_v0.md").write_text(
        render_markdown(report), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--report-root", type=Path, default=Path("reports"))
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    report_root = args.report_root
    if not report_root.is_absolute():
        report_root = repo_root / report_root
    report = build_gap_report(repo_root)
    write_outputs(report, report_root)
    print(json.dumps(report["recommended_next_slice"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
