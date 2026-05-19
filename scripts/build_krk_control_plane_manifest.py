#!/usr/bin/env python3
"""Map existing KRK artifacts into the control-plane evidence contract.

This manifest is replay-free. It inventories available evidence and gaps without
running playouts, adding runtime consumers, or changing topology.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CONTRACT = Path("reports/krk_control_plane_evidence_contract_v0.json")
PROTECTED_STATUS = Path("reports/krk_protected_stage_status.json")
STAGE6_MANIFEST = Path("reports/stage6_overlay_validation_manifest.md")
STRATEGY_DATASET = Path("reports/strategy_arbitration/krk_strategy_arbitration_dataset_v0.json")
MONITOR_RECORDS = Path("reports/strategy_arbitration/krk_strategy_monitor_records_v0.json")
INTERNAL_TERMINAL_EVIDENCE = Path("reports/strategy_arbitration/krk_internal_terminal_evidence_v1.json")
PLAN_WINDOW = Path("reports/structural_candidates/stage7_plan_capsule_owned_window_25_h40.json")
PLAN_AUDIT = Path("reports/structural_candidates/stage7_post_box_plan_capsule_audit.json")
DTM_TRAJECTORY_SEED = Path("reports/structural_candidates/stage7_post_box_dtm_trajectory_seed_h40.json")
DTM_TRAJECTORY_SEED_JSONL = Path("reports/structural_candidates/stage7_post_box_dtm_trajectory_seed_h40.jsonl")
DTM_TRAJECTORY_EXPANDED = Path("reports/structural_candidates/stage7_post_box_dtm_trajectory_seed_expanded_h40.json")
DTM_TRAJECTORY_EXPANDED_JSONL = Path(
    "reports/structural_candidates/stage7_post_box_dtm_trajectory_seed_expanded_h40.jsonl"
)
TRAINING_OBJECTIVE_BENCHMARK = Path(
    "reports/structural_candidates/stage7_training_objective_benchmark.json"
)
TRAINING_OBJECTIVE_GATE = Path(
    "reports/structural_candidates/stage7_training_objective_decision_gate.json"
)
GROWTH_GOVERNOR_PLAN = Path("reports/structural_candidates/stage7_box_shrink_growth_governor_plan.json")
STAGE6_PROMOTION = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/"
    "promotion_eval_stage6_overlay.json"
)
STAGE7_CLOSURE = Path("reports/structural_candidates/stage7_post_decision_closure.json")


def _load_json(root: Path, relative_path: Path) -> dict[str, Any]:
    payload = json.loads((root / relative_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {relative_path}")
    return payload


def _load_optional_json(root: Path, relative_path: Path) -> dict[str, Any]:
    path = root / relative_path
    if not path.exists():
        return {}
    return _load_json(root, relative_path)


def _line_count(root: Path, relative_path: Path) -> int:
    path = root / relative_path
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _artifact_status(root: Path, relative_path: Path) -> dict[str, Any]:
    path = root / relative_path
    return {
        "path": str(relative_path),
        "exists": path.exists(),
        "kind": "json" if path.suffix == ".json" else "jsonl" if path.suffix == ".jsonl" else "text",
    }


def _required_contract_fields(contract: dict[str, Any]) -> list[str]:
    return list(((contract.get("primary_frame") or {}).get("required_fields") or []))


def _coverage_item(field: str, status: str, sources: list[Path], summary: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "field": field,
        "coverage_status": status,
        "source_artifacts": [str(source) for source in sources],
        "summary": summary or {},
    }


def build_manifest(repo_root: Path) -> dict[str, Any]:
    contract = _load_json(repo_root, CONTRACT)
    if contract.get("causal_status") != "non_causal_schema_contract":
        raise ValueError("control-plane contract must be non-causal")

    protected = _load_json(repo_root, PROTECTED_STATUS)
    strategy = _load_json(repo_root, STRATEGY_DATASET)
    monitor = _load_json(repo_root, MONITOR_RECORDS)
    terminal = _load_json(repo_root, INTERNAL_TERMINAL_EVIDENCE)
    plan_window = _load_optional_json(repo_root, PLAN_WINDOW)
    plan_audit = _load_optional_json(repo_root, PLAN_AUDIT)
    seed = _load_optional_json(repo_root, DTM_TRAJECTORY_SEED)
    expanded = _load_optional_json(repo_root, DTM_TRAJECTORY_EXPANDED)
    benchmark = _load_optional_json(repo_root, TRAINING_OBJECTIVE_BENCHMARK)
    training_gate = _load_optional_json(repo_root, TRAINING_OBJECTIVE_GATE)
    growth_plan = _load_optional_json(repo_root, GROWTH_GOVERNOR_PLAN)
    stage6_promotion = _load_optional_json(repo_root, STAGE6_PROMOTION)
    stage7_closure = _load_optional_json(repo_root, STAGE7_CLOSURE)

    seed_steps = _line_count(repo_root, DTM_TRAJECTORY_SEED_JSONL)
    expanded_steps = _line_count(repo_root, DTM_TRAJECTORY_EXPANDED_JSONL)
    protected_summary = protected.get("summary") or {}
    strategy_summary = strategy.get("summary") or {}
    monitor_summary = monitor.get("summary") or {}
    terminal_summary = terminal.get("summary") or {}
    plan_windows = plan_window.get("windows") or []
    required_fields = _required_contract_fields(contract)

    field_coverage = [
        _coverage_item(
            "protected_provider_provenance",
            "covered_summary_level",
            [PROTECTED_STATUS, STAGE6_MANIFEST],
            {
                "protected_or_promoted_stages": protected_summary.get("yes_protected_or_promoted") or [],
                "cleanest_solved_components": protected_summary.get("cleanest_solved_components") or [],
                "solved_with_caveat": protected_summary.get("solved_with_caveat") or [],
            },
        ),
        _coverage_item(
            "strategy_proposal_frames",
            "covered_record_level",
            [STRATEGY_DATASET],
            {
                "record_count": strategy_summary.get("record_count"),
                "proposal_count": strategy_summary.get("proposal_count"),
                "records_by_source_stage": strategy_summary.get("records_by_source_stage") or {},
            },
        ),
        _coverage_item(
            "internal_monitor_records",
            "covered_record_level",
            [MONITOR_RECORDS, INTERNAL_TERMINAL_EVIDENCE],
            {
                "monitor_record_count": monitor_summary.get("monitor_record_count"),
                "internal_terminal_count": terminal_summary.get("terminal_count"),
                "causal_ready_terminals": terminal_summary.get("causal_ready_terminals") or [],
                "strongest_candidates": terminal_summary.get("strongest_internal_terminal_candidates") or [],
            },
        ),
        _coverage_item(
            "plan_capsule_window_records",
            "covered_stage7_only",
            [PLAN_WINDOW, PLAN_AUDIT],
            {
                "window_count": len(plan_windows),
                "plan_audit_schema": plan_audit.get("schema_version"),
            },
        ),
        _coverage_item(
            "sequence_training_examples",
            "covered_stage7_only_offline",
            [
                DTM_TRAJECTORY_SEED,
                DTM_TRAJECTORY_SEED_JSONL,
                DTM_TRAJECTORY_EXPANDED,
                DTM_TRAJECTORY_EXPANDED_JSONL,
                TRAINING_OBJECTIVE_BENCHMARK,
            ],
            {
                "seed_trajectory_count": len(seed.get("trajectories") or []),
                "seed_step_count": seed_steps,
                "expanded_trajectory_count": len(expanded.get("trajectories") or []),
                "expanded_step_count": expanded_steps,
                "benchmark_status": benchmark.get("final_decision")
                or benchmark.get("benchmark_decision")
                or benchmark.get("status"),
            },
        ),
        _coverage_item(
            "guardrail_result_summaries",
            "covered_summary_level",
            [PROTECTED_STATUS, STAGE6_PROMOTION],
            {
                "stage6_promotion_status": stage6_promotion.get("promotion_status"),
                "stage7_status": protected.get("stage7_status"),
                "protected_or_promoted_stages": protected_summary.get("yes_protected_or_promoted") or [],
            },
        ),
        _coverage_item(
            "growth_governor_status",
            "partial_design_only",
            [GROWTH_GOVERNOR_PLAN],
            {
                "source_schema": growth_plan.get("schema_version"),
                "gap": "No unified per-frame GrowthGovernorStatus export exists yet.",
            },
        ),
        _coverage_item(
            "promotion_gate_status",
            "covered_summary_level",
            [STAGE6_PROMOTION, TRAINING_OBJECTIVE_GATE, STAGE7_CLOSURE],
            {
                "stage6_promotion_status": stage6_promotion.get("promotion_status"),
                "stage7_training_gate": training_gate.get("selected_outcome"),
                "stage7_closure_status": stage7_closure.get("decision")
                or stage7_closure.get("selected_outcome")
                or stage7_closure.get("status"),
            },
        ),
    ]

    covered_fields = {item["field"] for item in field_coverage}
    missing_required_fields = sorted(set(required_fields) - covered_fields - {
        "frame_id",
        "domain",
        "state_id",
        "fen",
        "source_stage",
        "active_landmark_label",
        "outcome_labels",
        "source_artifacts",
        "causal_status",
    })

    manifest = {
        "schema_version": "krk_control_plane_manifest.v0",
        "causal_status": "non_causal_manifest",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "runtime_arbiter_added": False,
        "runtime_terminals_added": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "contract_artifact": str(CONTRACT),
        "source_artifacts": [
            str(PROTECTED_STATUS),
            str(STAGE6_MANIFEST),
            str(STRATEGY_DATASET),
            str(MONITOR_RECORDS),
            str(INTERNAL_TERMINAL_EVIDENCE),
            str(PLAN_WINDOW),
            str(PLAN_AUDIT),
            str(DTM_TRAJECTORY_SEED),
            str(DTM_TRAJECTORY_EXPANDED),
            str(TRAINING_OBJECTIVE_BENCHMARK),
            str(TRAINING_OBJECTIVE_GATE),
            str(GROWTH_GOVERNOR_PLAN),
            str(STAGE6_PROMOTION),
            str(STAGE7_CLOSURE),
        ],
        "artifact_inventory": [
            _artifact_status(repo_root, path)
            for path in [
                PROTECTED_STATUS,
                STAGE6_MANIFEST,
                STRATEGY_DATASET,
                MONITOR_RECORDS,
                INTERNAL_TERMINAL_EVIDENCE,
                PLAN_WINDOW,
                PLAN_AUDIT,
                DTM_TRAJECTORY_SEED,
                DTM_TRAJECTORY_SEED_JSONL,
                DTM_TRAJECTORY_EXPANDED,
                DTM_TRAJECTORY_EXPANDED_JSONL,
                TRAINING_OBJECTIVE_BENCHMARK,
                TRAINING_OBJECTIVE_GATE,
                GROWTH_GOVERNOR_PLAN,
                STAGE6_PROMOTION,
                STAGE7_CLOSURE,
            ]
        ],
        "field_coverage": field_coverage,
        "summary": {
            "required_field_count": len(required_fields),
            "covered_contract_fields": sorted(covered_fields),
            "missing_required_fields_after_manifest": missing_required_fields,
            "strategy_record_count": strategy_summary.get("record_count"),
            "strategy_proposal_count": strategy_summary.get("proposal_count"),
            "monitor_record_count": monitor_summary.get("monitor_record_count"),
            "plan_window_count": len(plan_windows),
            "sequence_seed_step_count": seed_steps,
            "sequence_expanded_step_count": expanded_steps,
            "new_playouts_added": 0,
            "records_from_existing_artifacts_only": True,
            "recommended_next_slice": "stratified_control_plane_gap_report_v0",
        },
        "gaps": [
            {
                "gap_id": "unified_frame_export_missing",
                "description": "Artifacts map to contract fields, but no per-state ControlPlaneEvidenceFrame export exists yet.",
                "next_step_class": "frame_exporter_design_or_replay_free_export",
            },
            {
                "gap_id": "growth_governor_status_not_frame_level",
                "description": "GrowthGovernor evidence is available as design/status artifacts, not per-frame status.",
                "next_step_class": "non_causal_status_export",
            },
            {
                "gap_id": "sequence_examples_stage7_only",
                "description": "Offline DTM/trajectory sequence labels are concentrated in Stage 7 residuals.",
                "next_step_class": "stratified_data_collection_plan",
            },
            {
                "gap_id": "plan_windows_stage7_only",
                "description": "Plan-capsule window evidence is mostly Stage 7-specific.",
                "next_step_class": "cross_stage_window_evidence_design",
            },
        ],
        "blocked_next_steps": contract.get("blocked_next_steps") or [],
    }
    validate_manifest(manifest)
    return manifest


def validate_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("causal_status") != "non_causal_manifest":
        raise ValueError("manifest must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "runtime_arbiter_added",
        "runtime_terminals_added",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if manifest.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if manifest["summary"]["new_playouts_added"] != 0:
        raise ValueError("manifest must remain replay-free")
    if "strategy_proposal_frames" not in manifest["summary"]["covered_contract_fields"]:
        raise ValueError("strategy proposal frame coverage missing")
    if "internal_monitor_records" not in manifest["summary"]["covered_contract_fields"]:
        raise ValueError("internal monitor coverage missing")


def render_markdown(manifest: dict[str, Any]) -> str:
    summary = manifest["summary"]
    lines = [
        "# KRK Control-Plane Manifest v0",
        "",
        "This replay-free manifest maps existing KRK artifacts into the non-causal "
        "control-plane evidence contract. It adds no labels, playouts, runtime "
        "consumers, terminals, arbiters, promotions, or topology changes.",
        "",
        "## Summary",
        "",
        f"- Strategy records: `{summary.get('strategy_record_count')}`",
        f"- Strategy proposal frames: `{summary.get('strategy_proposal_count')}`",
        f"- Monitor records: `{summary.get('monitor_record_count')}`",
        f"- Plan windows: `{summary.get('plan_window_count')}`",
        f"- Sequence seed steps: `{summary.get('sequence_seed_step_count')}`",
        f"- Expanded sequence steps: `{summary.get('sequence_expanded_step_count')}`",
        f"- New playouts added: `{summary.get('new_playouts_added')}`",
        f"- Recommended next slice: `{summary.get('recommended_next_slice')}`",
        "",
        "## Field Coverage",
        "",
    ]
    for item in manifest["field_coverage"]:
        lines.extend(
            [
                f"### {item['field']}",
                "",
                f"- Coverage: `{item['coverage_status']}`",
                "- Sources: " + ", ".join(f"`{source}`" for source in item["source_artifacts"]),
                "- Summary: "
                + ", ".join(f"`{key}={value}`" for key, value in item["summary"].items()),
                "",
            ]
        )
    lines.extend(["## Gaps", ""])
    for gap in manifest["gaps"]:
        lines.append(f"- `{gap['gap_id']}`: {gap['description']} Next: `{gap['next_step_class']}`")
    lines.extend(["", "## Blocked Next Steps", ""])
    lines.extend(f"- `{item}`" for item in manifest["blocked_next_steps"])
    lines.append("")
    return "\n".join(lines)


def write_outputs(manifest: dict[str, Any], report_root: Path) -> None:
    report_root.mkdir(parents=True, exist_ok=True)
    (report_root / "krk_control_plane_manifest_v0.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (report_root / "krk_control_plane_manifest_v0.md").write_text(
        render_markdown(manifest), encoding="utf-8"
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
    manifest = build_manifest(repo_root)
    write_outputs(manifest, report_root)
    print(json.dumps(manifest["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
