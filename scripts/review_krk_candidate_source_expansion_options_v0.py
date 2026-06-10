#!/usr/bin/env python3
"""Review non-causal candidate source expansion options from the gap manifest."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("reports/strategy_arbitration/krk_candidate_source_gap_manifest_v0.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_candidate_source_expansion_options_v0.json")
OUT_MD = Path("reports/strategy_arbitration/krk_candidate_source_expansion_options_v0.md")


def _load(path: Path = MANIFEST) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_payload(manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = manifest or _load()
    summary = manifest.get("summary") or {}
    exact_missing = int(summary.get("exact_missing_positive_capacity_count", 0) or 0)
    policy_cell_covered = int(summary.get("policy_cell_covered_exact_missing_count", 0) or 0)
    policy_cell_missing = int(summary.get("policy_cell_missing_count", 0) or 0)
    gap_by_stage = dict(summary.get("gap_count_by_stage") or {})
    gap_by_family = dict(summary.get("gap_count_by_family") or {})
    options = [
        {
            "option_id": "exact_trace_enrichment_within_existing_policy_cells",
            "scope": "stage5_stage6_current_refresh_policy_cells",
            "supported_by_gap_count": policy_cell_covered,
            "purpose": (
                "Improve exact move/provider trace coverage where the reviewed policy "
                "cell is already visible but the exact capacity candidate is absent."
            ),
            "runtime_implementation_requires_review_packet": True,
            "selector_allowed": False,
            "risk": "candidate_volume_growth_without_selection_value",
        },
        {
            "option_id": "protected_stage4_scope_review",
            "scope": "stage4_review_only",
            "supported_by_gap_count": int(gap_by_stage.get("stage4", 0) or 0),
            "purpose": "Decide whether Stage 4 should be eligible for observation-only candidate generation.",
            "runtime_implementation_requires_review_packet": True,
            "selector_allowed": False,
            "risk": "stage4_wrong_tempo_debt_scope_needs_separate_guardrails",
        },
        {
            "option_id": "plan_sequence_candidate_trace_review",
            "scope": "plan_capsule_sequence_candidates",
            "supported_by_gap_count": 0,
            "purpose": "Define separate observation frames for sequence/PlanCapsule candidates when provider-pack frames are insufficient.",
            "runtime_implementation_requires_review_packet": True,
            "selector_allowed": False,
            "risk": "sequence_candidates_are_not_one_ply_provider_capacity_labels",
        },
        {
            "option_id": "selector_training",
            "scope": "not_allowed",
            "supported_by_gap_count": 0,
            "purpose": "Out of scope because capacity/source gaps are not ownership labels.",
            "runtime_implementation_requires_review_packet": True,
            "selector_allowed": False,
            "risk": "would_mix_candidate_generation_capacity_with_runtime_ownership",
        },
    ]
    preferred = (
        "exact_trace_enrichment_within_existing_policy_cells"
        if policy_cell_covered >= policy_cell_missing
        else "protected_stage4_scope_review"
    )
    return {
        "schema_version": "krk_candidate_source_expansion_options.v1",
        "causal_status": "non_causal_expansion_options_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(MANIFEST)],
        "summary": {
            "exact_missing_positive_capacity_count": exact_missing,
            "policy_cell_covered_exact_missing_count": policy_cell_covered,
            "policy_cell_missing_count": policy_cell_missing,
            "gap_count_by_stage": gap_by_stage,
            "gap_count_by_family": gap_by_family,
        },
        "options": options,
        "preferred_next_review": preferred,
        "required_before_runtime": [
            "new_review_packet",
            "default_off_scope",
            "candidate_count_bound",
            "default_off_equivalence",
            "no_score_delta",
            "no_selected_move_or_provider_delta",
            "no_stage7_training_rows",
            "no_selector_or_routing",
        ],
        "decision": {
            "status": "candidate_source_expansion_options_review_complete_runtime_packet_required",
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": (
                "draft_exact_trace_enrichment_runtime_review_packet"
                if preferred == "exact_trace_enrichment_within_existing_policy_cells"
                else "draft_stage4_candidate_generation_scope_review"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Candidate Source Expansion Options v0",
        "",
        "This review turns the source-gap manifest into non-causal next-step options. It does not authorize runtime behavior.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- runtime_changes_allowed: `{payload['decision']['runtime_changes_allowed']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        f"- preferred_next_review: `{payload['preferred_next_review']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Options", ""])
    for option in payload["options"]:
        lines.append(
            "- "
            f"`{option['option_id']}` scope=`{option['scope']}` "
            f"supported_by_gap_count=`{option['supported_by_gap_count']}` "
            f"selector_allowed=`{option['selector_allowed']}` "
            f"requires_review_packet=`{option['runtime_implementation_requires_review_packet']}`"
        )
        lines.append(f"  {option['purpose']}")
    lines.extend(["", "## Required Before Runtime", ""])
    lines.extend(f"- `{item}`" for item in payload["required_before_runtime"])
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
