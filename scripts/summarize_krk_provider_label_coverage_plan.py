#!/usr/bin/env python3
"""Plan bounded provider-label coverage for KRK control-plane frames.

This is a planning artifact only. It does not run labels or playouts.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


FILTERED_FRAMES = Path("reports/krk_control_plane_filtered_frames_v0.json")
STRATEGY_PROBE = Path("reports/krk_control_plane_strategy_arbitration_probe_v0.json")


def _load_json(root: Path, relative_path: Path) -> dict[str, Any]:
    payload = json.loads((root / relative_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {relative_path}")
    return payload


def _known_provider_result(proposal: dict[str, Any]) -> str:
    label = proposal.get("known_outcome_label") or {}
    result = label.get("result") or label.get("playout_result")
    return str(result) if result in {"mate", "max_plies", "draw", "stagnation"} else "unknown"


def build_plan(repo_root: Path) -> dict[str, Any]:
    filtered = _load_json(repo_root, FILTERED_FRAMES)
    probe = _load_json(repo_root, STRATEGY_PROBE)
    if filtered.get("causal_status") != "non_causal_filtered_frame_export":
        raise ValueError("filtered frames must remain non-causal")
    if probe.get("causal_status") != "non_causal_probe":
        raise ValueError("strategy probe must remain non-causal")

    benchmark_frames = [
        frame
        for frame in filtered.get("frames") or []
        if "strategy_arbitration_benchmark" in (frame.get("filter_metadata") or {}).get("benchmark_roles", [])
    ]
    total_by_stage: Counter[str] = Counter()
    known_by_stage: Counter[str] = Counter()
    unknown_by_stage: Counter[str] = Counter()
    unknown_examples = []
    for frame in benchmark_frames:
        stage = str(frame.get("source_stage") or "unknown")
        for proposal in frame.get("strategy_proposal_frames") or []:
            total_by_stage[stage] += 1
            if _known_provider_result(proposal) == "unknown":
                unknown_by_stage[stage] += 1
                if len(unknown_examples) < 12:
                    unknown_examples.append(
                        {
                            "frame_id": frame.get("frame_id"),
                            "source_stage": stage,
                            "provider_id": proposal.get("provider_id"),
                            "move_uci": proposal.get("move_uci"),
                        }
                    )
            else:
                known_by_stage[stage] += 1

    probe_status = str((probe.get("label_coverage") or {}).get("label_status") or "")
    unknown_count = sum(unknown_by_stage.values())
    recommended_next_slice = (
        "offline_strategy_arbitration_baseline_v1"
        if unknown_count == 0 and probe_status == "provider_labels_sufficient_for_small_probe"
        else "review_or_run_bounded_provider_label_p0"
    )
    coverage_status = (
        "sufficient_for_current_small_probe"
        if recommended_next_slice == "offline_strategy_arbitration_baseline_v1"
        else "bounded_provider_label_run_needed"
    )

    plan = {
        "schema_version": "krk_provider_label_coverage_plan.v0",
        "causal_status": "non_causal_label_plan",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "runtime_arbiter_added": False,
        "runtime_terminals_added": False,
        "labels_generated_in_this_slice": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(FILTERED_FRAMES), str(STRATEGY_PROBE)],
        "current_label_coverage": {
            "benchmark_frame_count": len(benchmark_frames),
            "proposal_count_by_stage": dict(total_by_stage),
            "known_provider_label_count_by_stage": dict(known_by_stage),
            "unknown_provider_label_count_by_stage": dict(unknown_by_stage),
            "provider_labeled_frame_count": (probe.get("label_coverage") or {}).get(
                "provider_labeled_frame_count"
            ),
            "frames_with_known_provider_mate": (probe.get("label_coverage") or {}).get(
                "frames_with_known_provider_mate"
            ),
            "unknown_examples": unknown_examples,
            "coverage_status": coverage_status,
        },
        "bounded_labeling_plan": [
            {
                "phase": "p0_protected_success_controls",
                "purpose": "Add provider-level h40 labels to protected Stage 5/6 success frames so arbitration has positive controls outside Stage 7.",
                "max_frames": 8,
                "max_provider_suggestions_per_frame": 2,
                "target_stages": ["stage5", "stage6"],
                "horizon": 40,
                "trace_mode": "failures_only",
                "diagnostic_caches_required": True,
                "new_runtime_behavior": False,
            },
            {
                "phase": "p1_stage4_caveat_controls",
                "purpose": "Label Stage 4 caveat provider suggestions to separate guardrail-definition debt from provider-selection failure.",
                "max_frames": 4,
                "max_provider_suggestions_per_frame": 2,
                "target_stages": ["stage4"],
                "horizon": 40,
                "trace_mode": "failures_only",
                "diagnostic_caches_required": True,
                "new_runtime_behavior": False,
            },
            {
                "phase": "p2_stage7_challenge_balance",
                "purpose": "Only after protected controls exist, add balanced labels for Stage 7 challenge frames without reopening Stage 7 repair.",
                "max_frames": 4,
                "max_provider_suggestions_per_frame": 2,
                "target_stages": ["stage7"],
                "horizon": 40,
                "trace_mode": "failures_only",
                "diagnostic_caches_required": True,
                "new_runtime_behavior": False,
            },
        ],
        "acceptance_for_future_label_run": [
            "no_runtime_behavior_change",
            "no_stage7_promotion",
            "no_stage8_training",
            "no_runtime_dtm_or_tablebase",
            "no_exhaustive_legal_first_sweeps",
            "provider_labels_are_written_as_non_causal_outcome_labels",
            "run_stops_if_projected_to_hours",
        ],
        "post_label_decision_gate": [
            "if protected-stage provider labels are sufficient, rerun offline strategy-arbitration probe",
            "if labels remain sparse, do not train arbiter; report evidence gap",
            "if Stage7 labels dominate, freeze as challenge set and collect broader controls first",
        ],
        "recommended_next_slice": recommended_next_slice,
        "blocked_next_steps": [
            "runtime_arbiter",
            "runtime_internal_terminal",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }
    validate_plan(plan)
    return plan


def validate_plan(plan: dict[str, Any]) -> None:
    if plan.get("causal_status") != "non_causal_label_plan":
        raise ValueError("provider label plan must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "runtime_arbiter_added",
        "runtime_terminals_added",
        "labels_generated_in_this_slice",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if plan.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if plan.get("recommended_next_slice") not in {
        "review_or_run_bounded_provider_label_p0",
        "offline_strategy_arbitration_baseline_v1",
    }:
        raise ValueError("unexpected recommended next slice")


def render_markdown(plan: dict[str, Any]) -> str:
    coverage = plan["current_label_coverage"]
    lines = [
        "# KRK Provider Label Coverage Plan v0",
        "",
        "This is a non-causal plan. It does not run provider labels, add playouts, "
        "change runtime behavior, train Stage 8, or promote Stage 7.",
        "",
        "## Current Coverage",
        "",
        f"- Benchmark frames: `{coverage['benchmark_frame_count']}`",
        f"- Proposal count by stage: `{coverage['proposal_count_by_stage']}`",
        f"- Known provider labels by stage: `{coverage['known_provider_label_count_by_stage']}`",
        f"- Unknown provider labels by stage: `{coverage['unknown_provider_label_count_by_stage']}`",
        f"- Provider-labeled frames: `{coverage['provider_labeled_frame_count']}`",
        f"- Frames with known provider mate: `{coverage['frames_with_known_provider_mate']}`",
        f"- Coverage status: `{coverage['coverage_status']}`",
        "",
        "## Bounded Labeling Plan",
        "",
    ]
    if coverage.get("coverage_status") == "sufficient_for_current_small_probe":
        lines.extend(
            [
                "The current filtered frames already contain provider-level labels for the "
                "small offline probe. The bounded labeling plan remains as a future fallback, "
                "but no p0 label run is needed before the next non-causal arbitration baseline.",
                "",
            ]
        )
    for phase in plan["bounded_labeling_plan"]:
        lines.extend(
            [
                f"### {phase['phase']}",
                "",
                f"- Purpose: {phase['purpose']}",
                f"- Max frames: `{phase['max_frames']}`",
                f"- Max provider suggestions per frame: `{phase['max_provider_suggestions_per_frame']}`",
                f"- Target stages: `{phase['target_stages']}`",
                f"- Horizon: `{phase['horizon']}`",
                f"- Trace mode: `{phase['trace_mode']}`",
                f"- New runtime behavior: `{phase['new_runtime_behavior']}`",
                "",
            ]
        )
    lines.extend(["## Acceptance For Future Label Run", ""])
    lines.extend(f"- `{item}`" for item in plan["acceptance_for_future_label_run"])
    lines.extend(["", "## Recommended Next Slice", "", f"`{plan['recommended_next_slice']}`", ""])
    return "\n".join(lines)


def write_outputs(plan: dict[str, Any], report_root: Path) -> None:
    report_root.mkdir(parents=True, exist_ok=True)
    (report_root / "krk_provider_label_coverage_plan_v0.json").write_text(
        json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (report_root / "krk_provider_label_coverage_plan_v0.md").write_text(
        render_markdown(plan), encoding="utf-8"
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
    plan = build_plan(repo_root)
    write_outputs(plan, report_root)
    print(json.dumps(plan["current_label_coverage"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
