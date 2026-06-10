#!/usr/bin/env python3
"""Summarize KRK strategy-arbiter out-of-sample architecture review."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROBE = Path("reports/krk_strategy_arbiter_out_of_sample_control_probe_v0.json")
READINESS = Path("reports/krk_strategy_arbiter_sandbox_readiness_criteria_v0.json")
BALANCED_REVIEW = Path("reports/krk_selector_balanced_architecture_review_v1.json")
OUT_JSON = Path("reports/krk_strategy_arbiter_out_of_sample_architecture_review_v0.json")
OUT_MD = Path("reports/krk_strategy_arbiter_out_of_sample_architecture_review_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    probe = _load_json(PROBE)
    readiness = _load_json(READINESS)
    balanced = _load_json(BALANCED_REVIEW)
    metrics = probe.get("metrics") or {}
    blockers = probe.get("decision", {}).get("sandbox_blockers") or []
    selector_sandbox_blocked = bool(blockers)
    return {
        "schema_version": "krk_strategy_arbiter_out_of_sample_architecture_review.v0",
        "causal_status": "non_causal_architecture_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(PROBE), str(READINESS), str(BALANCED_REVIEW)],
        "evidence_summary": {
            "readiness_status": readiness.get("decision", {}).get("status"),
            "balanced_review_status": balanced.get("decision", {}).get("status"),
            "out_of_sample_probe_status": probe.get("decision", {}).get("status"),
            "out_of_sample_label_count": metrics.get("label_count"),
            "out_of_sample_selected_result_counts": metrics.get("selected_result_counts"),
            "out_of_sample_forced_selected_result_counts": metrics.get(
                "forced_selected_provider_result_counts"
            ),
            "out_of_sample_selected_provider_counts": metrics.get("selected_provider_counts"),
            "out_of_sample_stage_result_counts": metrics.get("stage_result_counts"),
            "sandbox_blockers": blockers,
        },
        "interpretation": {
            "protected_stack_status": "mostly_converts_on_bounded_out_of_sample_controls",
            "selector_signal_status": (
                "not_ready_due_to_class_imbalance_and_provider_dominance"
                if selector_sandbox_blocked
                else "ready_for_default_off_design_review"
            ),
            "stage4_caveat": "one_stage4_wrong_tempo_control_max_plies_h40",
            "stage7_status": "local_valid_composition_quarantined_unchanged",
            "big_picture": (
                "The evidence supports protected-provider preservation and current KRK handoff "
                "conversion on most controls, but does not yet establish a general strategy "
                "arbiter because selected-provider labels are dominated by stage0_basin."
            ),
        },
        "decision": {
            "status": (
                "selector_sandbox_blocked_out_of_sample_controls_not_selector_diverse"
                if selector_sandbox_blocked
                else "selector_sandbox_design_review_allowed"
            ),
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "stage7_repair_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "recommended_next_step": (
                "design_selector_readiness_v2_or_strategy_owner_contrast_dataset"
                if selector_sandbox_blocked
                else "prepare_default_off_selector_sandbox_design_review"
            ),
        },
        "recommended_options": [
            {
                "option": "strategy_owner_contrast_dataset",
                "purpose": (
                    "Collect or derive labels where multiple providers are plausible and at least "
                    "one non-stage0 owner has conversion evidence."
                ),
                "causal_status": "non_causal_only",
            },
            {
                "option": "selector_readiness_v2",
                "purpose": (
                    "Revise readiness criteria to require provider diversity, balanced labels, "
                    "and explicit selected-vs-forced label semantics."
                ),
                "causal_status": "design_only",
            },
            {
                "option": "pause_runtime_arbiter",
                "purpose": (
                    "Keep strategy arbitration as an evidence pipeline until labels distinguish "
                    "strategy ownership rather than mostly confirming stage0 finishing."
                ),
                "causal_status": "no_runtime_change",
            },
        ],
        "blocked_next_steps": [
            "runtime_arbiter",
            "selector_sandbox",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }


def render_markdown(review: dict[str, Any]) -> str:
    evidence = review["evidence_summary"]
    decision = review["decision"]
    lines = [
        "# KRK Strategy Arbiter Out-of-Sample Architecture Review v0",
        "",
        "This review closes the current out-of-sample selector-readiness slice. It is "
        "non-causal and does not implement a runtime arbiter, selector sandbox, "
        "Stage 7 repair, Stage 7 promotion, or Stage 8 training.",
        "",
        "## Evidence",
        "",
        f"- Readiness status: `{evidence['readiness_status']}`",
        f"- Balanced review status: `{evidence['balanced_review_status']}`",
        f"- Out-of-sample probe status: `{evidence['out_of_sample_probe_status']}`",
        f"- Out-of-sample labels: `{evidence['out_of_sample_label_count']}`",
        f"- Selected results: `{evidence['out_of_sample_selected_result_counts']}`",
        f"- Forced selected-provider results: `{evidence['out_of_sample_forced_selected_result_counts']}`",
        f"- Selected providers: `{evidence['out_of_sample_selected_provider_counts']}`",
        f"- Stage results: `{evidence['out_of_sample_stage_result_counts']}`",
        f"- Sandbox blockers: `{evidence['sandbox_blockers']}`",
        "",
        "## Interpretation",
        "",
        f"- Protected stack: `{review['interpretation']['protected_stack_status']}`",
        f"- Selector signal: `{review['interpretation']['selector_signal_status']}`",
        f"- Stage 4 caveat: `{review['interpretation']['stage4_caveat']}`",
        f"- Stage 7 status: `{review['interpretation']['stage7_status']}`",
        f"- Big picture: {review['interpretation']['big_picture']}",
        "",
        "## Decision",
        "",
        f"- Status: `{decision['status']}`",
        f"- Recommended next step: `{decision['recommended_next_step']}`",
        "- Runtime arbiter remains blocked.",
        "- Selector sandbox remains blocked.",
        "- Stage 7 repair/promotion and Stage 8 training remain blocked.",
        "",
        "## Options",
        "",
    ]
    for option in review["recommended_options"]:
        lines.append(
            f"- `{option['option']}`: {option['purpose']} Status: `{option['causal_status']}`."
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    review = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(review), encoding="utf-8")
    print(json.dumps(review["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
