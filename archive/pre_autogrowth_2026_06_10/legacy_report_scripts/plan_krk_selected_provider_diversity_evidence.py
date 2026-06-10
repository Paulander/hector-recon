#!/usr/bin/env python3
"""Plan non-causal selected-provider diversity evidence for KRK selector readiness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
READINESS_REVIEW = Path("reports/krk_selector_readiness_after_contrast_probe_review_v0.json")
OUT_JSON = Path("reports/krk_selected_provider_diversity_evidence_plan_v0.json")
OUT_MD = Path("reports/krk_selected_provider_diversity_evidence_plan_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_plan() -> dict[str, Any]:
    review = _load_json(READINESS_REVIEW)
    if review.get("causal_status") != "non_causal_architecture_review":
        raise ValueError("readiness review must remain non-causal")
    plan = {
        "schema_version": "krk_selected_provider_diversity_evidence_plan.v0",
        "causal_status": "non_causal_design_plan",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "labels_generated_in_this_slice": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(READINESS_REVIEW)],
        "purpose": (
            "Fill the remaining selector-readiness gap by finding protected Stage4/5/6 states "
            "where normal arbitration selects diverse validated providers, without using Stage7 training rows."
        ),
        "evidence_gap": {
            "gap_id": "selected_provider_family_diversity_missing",
            "current_selected_training_provider_families": (
                (review.get("evidence") or {}).get("selected_training_provider_families") or []
            ),
            "required_selected_provider_families": 3,
            "stage7_training_rows_allowed": 0,
        },
        "allowed_collection_phases": [
            {
                "phase": "replay_free_scan",
                "status": "allowed",
                "description": "Search existing Stage4/5/6 artifacts for selected provider families beyond stage0_basin/edge_trap.",
            },
            {
                "phase": "bounded_protected_sampling_manifest",
                "status": "design_only_until_reviewed",
                "description": "If replay-free scan fails, propose small h40 protected-only sampling jobs with no Stage7 rows.",
            },
            {
                "phase": "label_execution",
                "status": "blocked_until_manifest_review",
                "description": "Run labels only after an explicit manifest and review, with diagnostic caches and failure traces only.",
            },
        ],
        "target_provider_families": [
            "stage0_basin",
            "edge_trap",
            "fence_established",
            "drive_to_edge",
        ],
        "minimum_future_evidence": {
            "protected_stages": ["stage4", "stage5", "stage6"],
            "distinct_selected_provider_families": 3,
            "max_selected_provider_family_dominance": 0.7,
            "stage7_training_rows": 0,
            "horizon": 40,
        },
        "decision": {
            "status": "selected_provider_diversity_evidence_plan_defined",
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "recommended_next_step": "run_replay_free_selected_provider_diversity_scan",
        },
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
    validate_plan(plan)
    return plan


def validate_plan(plan: dict[str, Any]) -> None:
    if plan.get("causal_status") != "non_causal_design_plan":
        raise ValueError("plan must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_arbiter_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "labels_generated_in_this_slice",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if plan.get(key) is not False:
            raise ValueError(f"{key} must be false")


def render_markdown(plan: dict[str, Any]) -> str:
    gap = plan["evidence_gap"]
    lines = [
        "# KRK Selected Provider Diversity Evidence Plan v0",
        "",
        "This is a non-causal design plan. It does not sample, label, implement a selector, "
        "promote Stage 7, or train Stage 8.",
        "",
        "## Purpose",
        "",
        plan["purpose"],
        "",
        "## Evidence Gap",
        "",
        f"- Gap: `{gap['gap_id']}`",
        f"- Current selected provider families: `{gap['current_selected_training_provider_families']}`",
        f"- Required selected provider families: `{gap['required_selected_provider_families']}`",
        f"- Stage 7 training rows allowed: `{gap['stage7_training_rows_allowed']}`",
        "",
        "## Allowed Collection Phases",
        "",
    ]
    for phase in plan["allowed_collection_phases"]:
        lines.append(f"- `{phase['phase']}` status=`{phase['status']}`: {phase['description']}")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Status: `{plan['decision']['status']}`",
            f"- Recommended next step: `{plan['decision']['recommended_next_step']}`",
            "- Runtime arbiter and selector sandbox remain blocked.",
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
