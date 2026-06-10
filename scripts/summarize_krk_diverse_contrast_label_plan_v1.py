#!/usr/bin/env python3
"""Plan the next small diverse KRK state-local contrast label slice."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
READINESS_REVIEW = Path("reports/krk_runtime_selector_readiness_review_v1.json")
OUT_JSON = Path("reports/krk_diverse_contrast_label_plan_v1.json")
OUT_MD = Path("reports/krk_diverse_contrast_label_plan_v1.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_plan() -> dict[str, Any]:
    review = _load_json(READINESS_REVIEW)
    if review.get("decision", {}).get("status") != "runtime_selector_not_ready_collect_better_contrast_labels":
        raise ValueError("readiness review must request better contrast labels")

    plan = {
        "schema_version": "krk_diverse_contrast_label_plan.v1",
        "causal_status": "non_causal_label_plan",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifact": str(READINESS_REVIEW),
        "purpose": (
            "Collect a small, balanced, state-local provider contrast set that can test "
            "normalized selector objectives without relying on frame-level outcome labels."
        ),
        "label_budget": {
            "max_new_states": 8,
            "max_forced_provider_labels": 24,
            "horizon": 40,
            "trace_failures_only": True,
            "diagnostic_caches": True,
            "parallel_workers_if_available": True,
        },
        "strata": [
            {
                "stratum_id": "protected_stage4_wrong_tempo",
                "target_state_count": 2,
                "provider_families": ["stage0_basin", "edge_trap", "fence_established"],
                "purpose": "add non-stage5/6 contrast and negative controls",
            },
            {
                "stratum_id": "protected_stage5_fence",
                "target_state_count": 2,
                "provider_families": ["stage0_basin", "edge_trap", "fence_established", "drive_to_edge"],
                "purpose": "separate fence finish from edge-trap alternatives",
            },
            {
                "stratum_id": "protected_stage6_drive",
                "target_state_count": 2,
                "provider_families": ["stage0_basin", "drive_to_edge", "edge_trap", "fence_established"],
                "purpose": "separate drive ownership from stage0 and edge/fence fallbacks",
            },
            {
                "stratum_id": "stage7_challenge_eval_only",
                "target_state_count": 2,
                "provider_families": ["stage0_basin", "drive_to_edge", "edge_trap", "fence_established"],
                "purpose": "held-out evaluation only; never training",
                "training_allowed": False,
            },
        ],
        "required_fields": [
            "state_id",
            "fen",
            "source_stage",
            "active_landmark_label",
            "provider_id",
            "provider_family",
            "provider_maturity",
            "provider_local_rank",
            "normalized_score",
            "forced_result_h40",
            "forced_plies",
            "forced_first_move",
            "frame_outcome",
            "label_channel=forced_provider_state_local_contrast",
            "stage7_challenge_row",
            "causal_status=non_causal",
        ],
        "success_criteria": [
            "at least 40 non-Stage7 contrast rows",
            "at least 3 provider families with positive and negative examples where possible",
            "negative labels not dominated by one repeated state/provider family",
            "leave-state-out negative_suppression improves over 0.0",
            "Stage7 rows remain held-out evaluation only",
        ],
        "stop_conditions": [
            "projected runtime exceeds practical bounded h40 label budget",
            "labels require runtime DTM/tablebase",
            "labeling starts tuning Stage7",
            "protected Stage5/6 behavior is modified",
            "proposal would become a runtime selector",
        ],
        "decision": {
            "status": "diverse_contrast_label_plan_ready",
            "recommended_next_step": "run_bounded_diverse_contrast_label_slice_if_budget_allows",
            "runtime_test_allowed_next": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_plan(plan)
    return plan


def validate_plan(plan: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if plan.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if plan.get("decision", {}).get("runtime_test_allowed_next") is not False:
        raise ValueError("runtime tests remain blocked by this plan")


def render_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# KRK Diverse Contrast Label Plan v1",
        "",
        "This non-causal plan defines the next bounded contrast-label slice. It does not run labels or enable runtime behavior.",
        "",
        "## Purpose",
        "",
        plan["purpose"],
        "",
        "## Label Budget",
        "",
    ]
    for key, value in plan["label_budget"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Strata", ""])
    for item in plan["strata"]:
        lines.append(f"### `{item['stratum_id']}`")
        lines.append("")
        lines.append(f"- Target states: `{item['target_state_count']}`")
        lines.append(f"- Provider families: `{item['provider_families']}`")
        lines.append(f"- Purpose: {item['purpose']}")
        if item.get("training_allowed") is False:
            lines.append("- Training allowed: `False`")
        lines.append("")
    lines.extend(["## Required Fields", ""])
    for item in plan["required_fields"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Success Criteria", ""])
    for item in plan["success_criteria"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Stop Conditions", ""])
    for item in plan["stop_conditions"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Status: `{plan['decision']['status']}`",
            f"- Recommended next step: `{plan['decision']['recommended_next_step']}`",
            f"- Runtime test allowed next: `{plan['decision']['runtime_test_allowed_next']}`",
            f"- Stage 7 promotion allowed: `{plan['decision']['stage7_promotion_allowed']}`",
            f"- Stage 8 training allowed: `{plan['decision']['stage8_training_allowed']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    plan = build_plan()
    (ROOT / OUT_JSON).write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(plan), encoding="utf-8")
    print(json.dumps(plan["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
