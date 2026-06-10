#!/usr/bin/env python3
"""Design non-causal proposal coverage expansion for protected KRK states."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COVERAGE_REVIEW = Path("reports/krk_ranked_proposal_frame_protected_provider_coverage_review_v0.json")
OUT_JSON = Path("reports/krk_protected_proposal_coverage_expansion_plan_v0.json")
OUT_MD = Path("reports/krk_protected_proposal_coverage_expansion_plan_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_plan() -> dict[str, Any]:
    review = _load(COVERAGE_REVIEW)
    if review.get("causal_status") != "non_causal_coverage_review":
        raise ValueError("coverage review must remain non-causal")
    missing = list(review.get("records") or [])
    missing = [record for record in missing if not record.get("provider_present_in_frame")]
    payload = {
        "schema_version": "krk_protected_proposal_coverage_expansion_plan.v0",
        "causal_status": "non_causal_design_plan",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(COVERAGE_REVIEW)],
        "problem_statement": {
            "summary": "Protected forced-provider labels exist, but current StrategyProposalFrame rows omit those providers.",
            "why_it_matters": (
                "A selector benchmark cannot learn or evaluate a provider that is absent from the candidate frame. "
                "This is proposal-coverage evidence, not evidence that runtime selection should change."
            ),
        },
        "expansion_design": {
            "artifact_name": "krk_protected_provider_coverage_frames_v0",
            "candidate_record_kind": "non_causal_protected_provider_candidate_frame",
            "rows_to_create": len(missing),
            "row_sources": [
                "krk_protected_missing_provider_capacity_labels_v0",
                "krk_ranked_strategy_proposal_frames_v1 for shared state context",
            ],
            "required_row_fields": [
                "state_id",
                "frame_id",
                "source_stage",
                "active_landmark_label",
                "provider_id",
                "provider_family",
                "provider_version",
                "forced_result",
                "forced_plies",
                "forced_first_move",
                "label_semantics = forced_provider_capacity_label",
                "proposal_source = offline_forced_provider_label_not_runtime_proposal",
                "usable_for_training = false initially",
                "causal_status = non_causal",
            ],
            "must_not_include": [
                "runtime score override",
                "provider support bonus",
                "provider penalty",
                "topology edge",
                "runtime selector decision",
                "DTM/tablebase runtime label",
            ],
        },
        "label_semantics": {
            "forced_provider_capacity_label": (
                "Shows whether a provider can convert when forced for the first White move and then released. "
                "It is capacity/coverage evidence, not direct selector-positive evidence."
            ),
            "runtime_proposal_label": (
                "Shows a provider was actually proposed in a runtime trace. The current missing labels are not this."
            ),
            "selected_playout_success": "Shows the normally selected path converted; separate from provider capacity.",
        },
        "acceptance_for_next_slice": {
            "generate_rows_for_all_missing_protected_labels": len(missing),
            "stage7_rows_allowed": 0,
            "runtime_work_allowed": False,
            "training_allowed_initially": False,
            "requires_followup_review_before_training_use": True,
        },
        "decision": {
            "status": "protected_proposal_coverage_expansion_plan_ready",
            "recommended_next_step": "build_non_causal_protected_provider_coverage_frames_v0",
            "runtime_work_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_plan(payload)
    return payload


def validate_plan(payload: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if payload["acceptance_for_next_slice"]["stage7_rows_allowed"] != 0:
        raise ValueError("Stage 7 rows must remain excluded from this protected expansion")
    if payload["acceptance_for_next_slice"]["training_allowed_initially"] is not False:
        raise ValueError("coverage expansion rows must not be training rows initially")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Protected Proposal Coverage Expansion Plan v0",
        "",
        "This is a non-causal design plan. It does not implement a runtime selector or alter topology.",
        "",
        "## Problem",
        "",
        payload["problem_statement"]["summary"],
        "",
        payload["problem_statement"]["why_it_matters"],
        "",
        "## Expansion Design",
        "",
    ]
    design = payload["expansion_design"]
    lines.append(f"- Artifact: `{design['artifact_name']}`")
    lines.append(f"- Candidate record kind: `{design['candidate_record_kind']}`")
    lines.append(f"- Rows to create: `{design['rows_to_create']}`")
    lines.append(f"- Required fields: `{design['required_row_fields']}`")
    lines.append(f"- Must not include: `{design['must_not_include']}`")
    lines.extend(["", "## Label Semantics", ""])
    for key, value in payload["label_semantics"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Acceptance For Next Slice", ""])
    for key, value in payload["acceptance_for_next_slice"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_plan()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
