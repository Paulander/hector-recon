#!/usr/bin/env python3
"""Summarize the architecture decision after selected-path target probing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROBE = Path("reports/structural_candidates/stage7_selected_path_target_probe_v0.json")
AUDIT = Path("reports/structural_candidates/stage7_selected_failure_path_audit_v0.json")
OUT_JSON = Path("reports/structural_candidates/stage7_selected_path_architecture_review_v0.json")
OUT_MD = Path("reports/structural_candidates/stage7_selected_path_architecture_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    probe = _load(PROBE)
    audit = _load(AUDIT)
    return {
        "schema_version": "stage7_selected_path_architecture_review.v0",
        "causal_status": "non_causal_architecture_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(AUDIT), str(PROBE)],
        "current_findings": {
            "selected_failure_provider": audit["summary"]["selected_provider_counts"],
            "selected_failure_path_class_counts": audit["summary"]["selected_failure_path_class_counts"],
            "abstention_selected_penalized_count": audit["summary"]["abstention_stage7_selected_penalized_count"],
            "split_target_probe_status": probe["decision"]["status"],
            "source_bias_detected": probe["summary"]["source_bias_detected"],
        },
        "architecture_interpretation": [
            "The failed runtime abstention selector was aimed at unsafe proposals, but the actual selected Stage 7 failure path is stage0_basin ownership.",
            "The selected failure path is not one homogeneous target: half is ownership misselection with an existing converting provider, and half is sequence/continuation capacity or model-expression gap.",
            "The split-target framing is useful offline, but existing sequence success controls come from prior sandbox artifacts and are not clean enough to authorize runtime behavior.",
            "A single penalty, provider boost, or support adapter would conflate distinct failure modes and likely overfit the Stage 7 lab.",
        ],
        "recommended_next_work": {
            "status": "collect_clean_controls_or_review_before_runtime",
            "primary": "Collect or recover clean non-sandbox Stage 7/post-box sequence controls and additional ownership-gap examples before any runtime selector/arbiter work.",
            "secondary": "If clean controls cannot be collected cheaply, pause Stage 7 implementation and review whether box_shrink should be treated as local evidence/handoff trigger rather than an independent owner.",
            "minimum_clean_control_requirements": [
                "successful post-box h40 controls not produced by a candidate repair sandbox",
                "paired max_plies hard negatives for the same or nearby post-box families",
                "protected Stage 5/6 examples where stage0_basin or edge/fence ownership is safe",
                "held-out family split separating ownership-gap from sequence-gap cases",
            ],
        },
        "blocked_actions": [
            "scale two-stage abstention selector",
            "increase abstention penalty",
            "implement runtime arbiter",
            "make internal terminals causal",
            "add Stage 7 support adapter",
            "promote Stage 7",
            "train Stage 8",
            "use runtime DTM/tablebase",
        ],
        "decision": {
            "status": "runtime_no_go_architecture_review_required",
            "next_allowed_slice": "non_causal_clean_control_collection_plan",
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 Selected Path Architecture Review v0",
        "",
        f"Decision: `{payload['decision']['status']}`",
        "",
        "This review closes the selected-path runtime-test follow-up. It does not authorize runtime behavior.",
        "",
        "## Current Findings",
        "",
    ]
    for key, value in payload["current_findings"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Architecture Interpretation", ""])
    for item in payload["architecture_interpretation"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Recommended Next Work", ""])
    rec = payload["recommended_next_work"]
    lines.append(f"- Status: `{rec['status']}`")
    lines.append(f"- Primary: {rec['primary']}")
    lines.append(f"- Secondary: {rec['secondary']}")
    lines.extend(["", "Minimum clean-control requirements:", ""])
    for item in rec["minimum_clean_control_requirements"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Blocked Actions", ""])
    for item in payload["blocked_actions"]:
        lines.append(f"- `{item}`")
    lines.extend(["", f"Next allowed slice: `{payload['decision']['next_allowed_slice']}`", ""])
    return "\n".join(lines)


def main() -> None:
    payload = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
