#!/usr/bin/env python3
"""Build non-causal KRK candidate-generation / strategy-sequence review artifacts.

This script is replay-free. It merges existing proposal-frame, forced-capacity,
strategy-sequence inventory, and post-activation runtime-test audit artifacts to
answer which alternatives should be visible before any future strategy arbiter
or sequence policy is allowed to act.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

CAPACITY_FRAMES = Path("reports/krk_protected_provider_coverage_frames_v0.json")
RANKED_FRAMES = Path("reports/krk_ranked_strategy_proposal_frames_v1.json")
VALIDATED_SET_AUDIT = Path("reports/krk_validated_provider_candidate_set_audit_v0.json")
STRATEGY_SEQUENCE_INVENTORY = Path("reports/krk_strategy_sequence_inventory_v0.json")
POST_ACTIVATION_AUDIT = Path(
    "reports/krk_progress_window_reconsideration_post_activation_audit_v0.json"
)

OUT_COVERAGE_JSON = Path("reports/strategy_arbitration/krk_candidate_proposal_coverage_v0.json")
OUT_COVERAGE_MD = Path("reports/strategy_arbitration/krk_candidate_proposal_coverage_v0.md")
OUT_REVIEW_JSON = Path(
    "reports/strategy_arbitration/krk_candidate_generation_strategy_review_v0.json"
)
OUT_REVIEW_MD = Path("reports/strategy_arbitration/krk_candidate_generation_strategy_review_v0.md")
OUT_FRAME_SCHEMA_JSON = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_candidate_frame_v1.json"
)
OUT_FRAME_SCHEMA_MD = Path("reports/strategy_arbitration/krk_strategy_sequence_candidate_frame_v1.md")


RUNTIME_FALSE_KEYS = (
    "runtime_behavior_changed",
    "runtime_defaults_changed",
    "runtime_selector_implemented",
    "runtime_candidate_generator_implemented",
    "runtime_terminals_added",
    "runtime_dtm_or_tablebase_lookup",
    "gameplay_topology_mutation",
    "stage7_promotion_allowed",
    "stage8_training_allowed",
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _runtime_false_block() -> dict[str, bool]:
    return {key: False for key in RUNTIME_FALSE_KEYS}


def _provider_family(provider_id: str | None) -> str:
    text = str(provider_id or "")
    if text == "krk.stage0_basin":
        return "stage0_basin"
    if text == "krk.drive_to_edge":
        return "drive_to_edge"
    if text == "krk.fence_established":
        return "fence_established"
    if text.startswith("krk.edge_trap"):
        return "edge_trap"
    if text == "krk.box_shrink":
        return "box_shrink"
    if "post_box" in text or "plan_capsule" in text:
        return "plan_or_sequence"
    return "other"


def _proposal_index(ranked_rows: list[dict[str, Any]]) -> dict[str, set[str]]:
    by_state: dict[str, set[str]] = defaultdict(set)
    for row in ranked_rows:
        state_id = str(row.get("state_id") or "")
        provider = str(row.get("provider_id") or "")
        if state_id and provider:
            by_state[state_id].add(provider)
    return by_state


def _coverage_rows(
    capacity_rows: list[dict[str, Any]],
    ranked_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    proposals_by_state = _proposal_index(ranked_rows)
    rows = []
    for row in capacity_rows:
        state_id = str(row.get("state_id") or "")
        provider = str(row.get("provider_id") or "")
        current = sorted(proposals_by_state.get(state_id) or row.get("existing_frame_providers") or [])
        provider_visible = provider in set(current)
        capacity_label = str(row.get("capacity_label") or "unknown")
        rows.append(
            {
                "schema_version": "krk_candidate_proposal_coverage_row.v0",
                "state_id": state_id,
                "frame_id": row.get("frame_id"),
                "fen": row.get("fen"),
                "source_stage": row.get("source_stage"),
                "active_landmark_label": row.get("active_landmark_label"),
                "provider_id": provider,
                "provider_family": row.get("provider_family") or _provider_family(provider),
                "capacity_label": capacity_label,
                "forced_result": row.get("forced_result"),
                "forced_first_move": row.get("forced_first_move"),
                "forced_plies": row.get("forced_plies"),
                "current_visible_providers": current,
                "provider_visible_in_current_proposals": provider_visible,
                "candidate_generation_channel": (
                    "existing_visible_provider_proposal"
                    if provider_visible
                    else "missing_validated_provider_capacity_candidate"
                ),
                "label_semantics": row.get("label_semantics")
                or "forced_provider_capacity_label",
                "usable_for_selector_training": False,
                "stage7_challenge_row": bool(row.get("stage7_challenge_row", False)),
                "causal_status": "non_causal_capacity_coverage_evidence",
            }
        )
    return rows


def _post_activation_summary(payload: dict[str, Any]) -> dict[str, Any]:
    records = list(payload.get("activation_records") or [])
    selected_provider_counts = Counter(
        str((record.get("reconsideration_selected") or {}).get("provider_id") or "unknown")
        for record in records
    )
    supported_provider_counts: Counter[str] = Counter()
    supported_move_count = 0
    supported_mate_count = 0
    unsupported_visible_mate_count = 0
    for record in records:
        for candidate in record.get("all_supported_candidates", []) or []:
            supported_move_count += 1
            provider = str(candidate.get("provider_id") or "unknown")
            supported_provider_counts[provider] += 1
        supported_mate_count += int(record.get("supported_candidate_mate_count", 0) or 0)
        unsupported_visible_mate_count += int(
            record.get("unsupported_visible_candidate_mate_count", 0) or 0
        )
    return {
        "target_frame_id": payload.get("target_frame_id"),
        "classification": payload.get("classification", {}),
        "activation_count": len(records),
        "selected_supported_provider_counts": dict(sorted(selected_provider_counts.items())),
        "supported_provider_counts": dict(sorted(supported_provider_counts.items())),
        "supported_candidate_count": supported_move_count,
        "supported_candidate_mate_count": supported_mate_count,
        "unsupported_visible_candidate_mate_count": unsupported_visible_mate_count,
        "interpretation": (
            "Progress-window reconsideration activated, but selected/supported/sampled visible "
            "candidates did not convert under bounded h40 continuation."
        ),
    }


def _summarize_coverage(rows: list[dict[str, Any]]) -> dict[str, Any]:
    positive = [row for row in rows if row.get("capacity_label") == "positive_capacity"]
    negative = [row for row in rows if row.get("capacity_label") == "negative_capacity"]
    visible_positive = [row for row in positive if row.get("provider_visible_in_current_proposals")]
    visible_negative = [row for row in negative if row.get("provider_visible_in_current_proposals")]
    missing_positive = [row for row in positive if not row.get("provider_visible_in_current_proposals")]
    return {
        "row_count": len(rows),
        "state_count": len({row.get("state_id") for row in rows}),
        "positive_capacity_count": len(positive),
        "negative_capacity_count": len(negative),
        "positive_capacity_visible_count": len(visible_positive),
        "negative_capacity_visible_count": len(visible_negative),
        "positive_capacity_recall": (
            len(visible_positive) / len(positive) if positive else None
        ),
        "negative_capacity_visibility_rate": (
            len(visible_negative) / len(negative) if negative else None
        ),
        "missing_positive_capacity_count": len(missing_positive),
        "stage7_row_count": sum(1 for row in rows if row.get("stage7_challenge_row")),
        "missing_positive_provider_family_counts": dict(
            sorted(Counter(row.get("provider_family") for row in missing_positive).items())
        ),
        "missing_positive_source_stage_counts": dict(
            sorted(Counter(row.get("source_stage") for row in missing_positive).items())
        ),
        "all_provider_family_counts": dict(
            sorted(Counter(row.get("provider_family") for row in rows).items())
        ),
    }


def build_coverage_payload() -> dict[str, Any]:
    capacity = _load(CAPACITY_FRAMES)
    ranked = _load(RANKED_FRAMES)
    validated = _load(VALIDATED_SET_AUDIT)
    post_activation = _load(POST_ACTIVATION_AUDIT)
    rows = _coverage_rows(list(capacity.get("rows") or []), list(ranked.get("rows") or []))
    summary = _summarize_coverage(rows)
    payload = {
        "schema_version": "krk_candidate_proposal_coverage.v0",
        "causal_status": "non_causal_candidate_generation_coverage_benchmark",
        **_runtime_false_block(),
        "source_artifacts": [
            str(CAPACITY_FRAMES),
            str(RANKED_FRAMES),
            str(VALIDATED_SET_AUDIT),
            str(POST_ACTIVATION_AUDIT),
        ],
        "summary": summary,
        "validated_provider_candidate_set_counterfactual": {
            "status": (validated.get("decision") or {}).get("status"),
            "positive_capacity_recall_if_included": (
                validated.get("summary") or {}
            ).get("positive_capacity_recall_if_included"),
            "negative_capacity_inclusion_rate": (
                validated.get("summary") or {}
            ).get("negative_capacity_inclusion_rate"),
            "interpretation": validated.get("interpretation", {}),
        },
        "progress_window_post_activation": _post_activation_summary(post_activation),
        "rows": rows,
        "decision": {
            "status": "candidate_generation_gap_confirmed",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "recommended_next_step": "design_strategy_sequence_candidate_frame_schema_v1",
        },
    }
    return payload


def build_review_payload(coverage: dict[str, Any]) -> dict[str, Any]:
    inventory = _load(STRATEGY_SEQUENCE_INVENTORY)
    summary = coverage["summary"]
    post_activation = coverage["progress_window_post_activation"]
    sequence_inventory = inventory.get("sequence_policy_inventory", {})
    strategy_inventory = inventory.get("strategy_ownership_inventory", {})
    missing_positive = [
        row for row in coverage["rows"]
        if row.get("capacity_label") == "positive_capacity"
        and not row.get("provider_visible_in_current_proposals")
    ]
    review = {
        "schema_version": "krk_candidate_generation_strategy_review.v0",
        "causal_status": "non_causal_strategy_sequence_review",
        **_runtime_false_block(),
        "source_artifacts": [
            str(OUT_COVERAGE_JSON),
            str(STRATEGY_SEQUENCE_INVENTORY),
            str(POST_ACTIVATION_AUDIT),
        ],
        "question_answers": {
            "what_alternatives_should_be_visible": [
                "validated provider candidates with protected positive-capacity evidence",
                "candidate moves from CandidateMoveFrame when provider proposals omit legal progress moves",
                "plan/capsule sequence candidates when one-ply provider moves do not convert",
                "broader KRK strategy proposals when local stage labels are boundary signals",
            ],
            "which_alternatives_are_missing_from_current_frames": {
                "protected_positive_capacity_missing_count": summary["missing_positive_capacity_count"],
                "missing_provider_family_counts": summary["missing_positive_provider_family_counts"],
                "missing_source_stage_counts": summary["missing_positive_source_stage_counts"],
            },
            "which_can_be_generated_by_existing_validated_providers": sorted(
                {
                    row["provider_id"]
                    for row in missing_positive
                    if row.get("provider_family")
                    in {"stage0_basin", "fence_established", "edge_trap", "drive_to_edge"}
                }
            ),
            "which_require_candidate_move_frame_enumeration": [
                "states where provider proposals omit legal progress moves",
                "states where support terms are broad but no provider candidate converts",
            ],
            "which_require_plan_capsule_sequence_candidates": [
                "progress-window activation states whose selected/supported one-ply candidates all max out",
                "Stage 7 held-out residuals with sequence-policy or post-box continuation gaps",
            ],
            "which_require_new_broader_krk_strategy_proposals": [
                "phase-boundary states where local stage ownership is not stable",
                "positions needing edge-net / king-support continuation beyond current providers",
            ],
            "capacity_evidence_only": [
                "forced-provider h40 mate labels",
                "forced-provider h40 max_plies labels",
                "validated-provider candidate-set counterfactual rows",
            ],
            "what_remains_non_causal": [
                "coverage rows",
                "capacity labels",
                "candidate-generation benchmark",
                "strategy/sequence review",
                "InternalTerminalSpec and PlanCapsuleSpec evidence",
            ],
        },
        "benchmark_findings": {
            "protected_positive_capacity_recall_current": summary["positive_capacity_recall"],
            "protected_positive_capacity_missing_count": summary["missing_positive_capacity_count"],
            "validated_provider_pack_positive_recall_if_included": (
                coverage["validated_provider_candidate_set_counterfactual"]
                .get("positive_capacity_recall_if_included")
            ),
            "validated_provider_pack_negative_capacity_inclusion_rate": (
                coverage["validated_provider_candidate_set_counterfactual"]
                .get("negative_capacity_inclusion_rate")
            ),
            "progress_window_supported_candidate_mate_count": post_activation[
                "supported_candidate_mate_count"
            ],
            "progress_window_unsupported_visible_candidate_mate_count": post_activation[
                "unsupported_visible_candidate_mate_count"
            ],
            "sequence_policy_success_controls_met": sequence_inventory.get("success_controls_met"),
            "sequence_policy_ready_for_runtime_review": sequence_inventory.get(
                "ready_for_runtime_review"
            ),
            "strategy_ownership_ready_for_runtime_review": strategy_inventory.get(
                "ready_for_runtime_review"
            ),
        },
        "candidate_channels": [
            {
                "channel": "validated_provider_pack",
                "role": "candidate_generation",
                "status": "recall_promising_but_selection_risk",
                "causal_status": "non_causal",
                "reason": "Would recover protected positive-capacity providers, but also includes negative-capacity providers.",
            },
            {
                "channel": "candidate_move_frame",
                "role": "legal_move_hypothesis_generation",
                "status": "needed_for_provider_omission_cases",
                "causal_status": "non_causal_design_needed",
                "reason": "Provider proposals can omit legal alternatives; candidate moves must remain visible hypotheses, not hidden selectors.",
            },
            {
                "channel": "plan_capsule_sequence_candidate",
                "role": "multi_step_candidate_generation",
                "status": "needed_for_progress_window_and_stage7_sequence_gaps",
                "causal_status": "non_causal_design_needed",
                "reason": "One-ply safe/progress moves may not convert without sequence policy.",
            },
            {
                "channel": "broader_krk_strategy_proposal",
                "role": "phase_boundary_strategy_generation",
                "status": "needed_for_stage7_boundary_cases",
                "causal_status": "non_causal_design_needed",
                "reason": "Stage 7 is local evidence / handoff trigger, not a stable owner.",
            },
        ],
        "decision": {
            "status": "strategy_sequence_control_plane_v1_needed",
            "runtime_sandbox_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "recommended_next_step": "define_non_causal_strategy_sequence_candidate_frame_v1",
            "future_runtime_sandbox_requires": [
                "candidate-generation candidate set exists",
                "selection semantics separate capacity from ownership",
                "sequence-policy candidates have clean success and hard-negative controls",
                "default-off review packet",
                "target smoke improvement before guardrails",
            ],
        },
    }
    return review


def build_frame_schema_payload(review: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "krk_strategy_sequence_candidate_frame_spec.v1",
        "causal_status": "non_causal_schema_design",
        **_runtime_false_block(),
        "source_artifacts": [
            str(OUT_COVERAGE_JSON),
            str(OUT_REVIEW_JSON),
            str(STRATEGY_SEQUENCE_INVENTORY),
        ],
        "purpose": (
            "Represent visible candidate-generation hypotheses for KRK strategy/sequence "
            "control without treating capacity evidence as selector labels."
        ),
        "frame_types": [
            {
                "frame_type": "validated_provider_candidate",
                "source_channel": "protected_forced_provider_capacity",
                "meaning": "Existing provider has offline capacity evidence in this state/context.",
                "label_semantics": "capacity_evidence_not_ownership_label",
                "causal_status": "non_causal",
                "future_consumer": "candidate_generator_dataset",
            },
            {
                "frame_type": "candidate_move_hypothesis",
                "source_channel": "CandidateMoveFrame",
                "meaning": "Legal move has visible move-shape/post-move terms worth evaluating.",
                "label_semantics": "move_hypothesis_not_selector_decision",
                "causal_status": "non_causal",
                "future_consumer": "proposal_coverage_and_move_ranking_benchmark",
            },
            {
                "frame_type": "plan_capsule_sequence_candidate",
                "source_channel": "PlanCapsuleSpec_or_sequence_window",
                "meaning": "A bounded multi-step continuation may be needed.",
                "label_semantics": "sequence_candidate_not_runtime_commitment",
                "causal_status": "non_causal",
                "future_consumer": "sequence_policy_benchmark",
            },
            {
                "frame_type": "broader_krk_strategy_candidate",
                "source_channel": "phase_boundary_or_internal_monitor",
                "meaning": "Current local stage may need handoff to a broader strategy family.",
                "label_semantics": "strategy_candidate_not_provider_route",
                "causal_status": "non_causal",
                "future_consumer": "strategy_arbitration_dataset",
            },
        ],
        "required_fields": [
            "schema_version",
            "frame_id",
            "state_id",
            "fen",
            "source_stage",
            "active_landmark_label",
            "frame_type",
            "candidate_id",
            "candidate_provider_id",
            "candidate_move_uci",
            "candidate_plan_id",
            "candidate_strategy_family",
            "source_terms",
            "move_shape_terms",
            "post_move_terms",
            "safety_terms",
            "internal_monitor_terms",
            "capacity_evidence",
            "ownership_evidence",
            "sequence_evidence",
            "label_semantics",
            "stage7_challenge_row",
            "usable_for_selector_training",
            "usable_for_candidate_generation_training",
            "causal_status"
        ],
        "label_semantics": {
            "capacity_evidence": "Provider or candidate can convert when forced/offline; not direct ownership.",
            "ownership_evidence": "Normal routing selected/failed/succeeded; still requires safe-preservation split.",
            "sequence_evidence": "Multi-step continuation outcome or plan-window label.",
            "stage7_challenge_row": "Held-out evaluation/challenge only, not training/readiness row."
        },
        "forbidden_causal_uses": [
            "direct_provider_request",
            "direct_move_selection",
            "runtime_dtm_or_tablebase_lookup",
            "gameplay_topology_mutation",
            "stage7_promotion",
            "stage8_training_from_stage7",
            "default_policy_change"
        ],
        "future_runtime_sandbox_requirements": review["decision"]["future_runtime_sandbox_requires"],
        "decision": {
            "status": "strategy_sequence_candidate_frame_schema_defined",
            "runtime_sandbox_allowed": False,
            "recommended_next_step": "populate_strategy_sequence_candidate_frames_replay_free_v1",
        },
    }


def write_coverage_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Candidate Proposal Coverage v0",
        "",
        "Replay-free, non-causal benchmark of whether current proposal frames expose protected validated-provider capacity alternatives.",
        "",
        "## Summary",
        "",
    ]
    for key in (
        "row_count",
        "state_count",
        "positive_capacity_count",
        "positive_capacity_visible_count",
        "positive_capacity_recall",
        "missing_positive_capacity_count",
        "negative_capacity_count",
        "negative_capacity_visibility_rate",
        "stage7_row_count",
    ):
        lines.append(f"- `{key}`: `{summary.get(key)}`")
    lines.extend(
        [
            f"- `missing_positive_provider_family_counts`: `{summary.get('missing_positive_provider_family_counts')}`",
            f"- `missing_positive_source_stage_counts`: `{summary.get('missing_positive_source_stage_counts')}`",
            "",
            "## Progress-Window Post-Activation Link",
            "",
            f"- classification: `{payload['progress_window_post_activation']['classification']}`",
            f"- supported_candidate_mate_count: `{payload['progress_window_post_activation']['supported_candidate_mate_count']}`",
            f"- unsupported_visible_candidate_mate_count: `{payload['progress_window_post_activation']['unsupported_visible_candidate_mate_count']}`",
            "",
            "## Decision",
            "",
            f"- status: `{payload['decision']['status']}`",
            f"- next: `{payload['decision']['recommended_next_step']}`",
            f"- runtime_work_allowed: `{payload['decision']['runtime_work_allowed']}`",
            "",
        ]
    )
    (ROOT / OUT_COVERAGE_MD).write_text("\n".join(lines), encoding="utf-8")


def write_review_markdown(payload: dict[str, Any]) -> None:
    findings = payload["benchmark_findings"]
    lines = [
        "# KRK Candidate Generation Strategy Review v0",
        "",
        "Non-causal strategy/sequence review after the quarantined progress-window reconsideration sandbox.",
        "",
        "## Findings",
        "",
    ]
    for key, value in findings.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Candidate Channels", ""])
    for row in payload["candidate_channels"]:
        lines.append(
            f"- `{row['channel']}`: `{row['status']}`; role=`{row['role']}`; causal=`{row['causal_status']}`"
        )
    lines.extend(
        [
            "",
            "## Answers",
            "",
            f"- alternatives_should_be_visible: `{payload['question_answers']['what_alternatives_should_be_visible']}`",
            f"- missing_from_current_frames: `{payload['question_answers']['which_alternatives_are_missing_from_current_frames']}`",
            f"- existing_validated_provider_candidates: `{payload['question_answers']['which_can_be_generated_by_existing_validated_providers']}`",
            f"- capacity_evidence_only: `{payload['question_answers']['capacity_evidence_only']}`",
            "",
            "## Decision",
            "",
            f"- status: `{payload['decision']['status']}`",
            f"- next: `{payload['decision']['recommended_next_step']}`",
            f"- runtime_sandbox_allowed: `{payload['decision']['runtime_sandbox_allowed']}`",
            "",
        ]
    )
    (ROOT / OUT_REVIEW_MD).write_text("\n".join(lines), encoding="utf-8")


def write_frame_schema_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Strategy/Sequence Candidate Frame v1",
        "",
        "Non-causal schema design for candidate-generation hypotheses. This is not a runtime generator, selector, or arbiter.",
        "",
        "## Purpose",
        "",
        payload["purpose"],
        "",
        "## Frame Types",
        "",
    ]
    for row in payload["frame_types"]:
        lines.append(
            f"- `{row['frame_type']}` from `{row['source_channel']}`: "
            f"{row['meaning']} semantics=`{row['label_semantics']}`"
        )
    lines.extend(
        [
            "",
            "## Required Fields",
            "",
            f"`{payload['required_fields']}`",
            "",
            "## Forbidden Causal Uses",
            "",
            f"`{payload['forbidden_causal_uses']}`",
            "",
            "## Decision",
            "",
            f"- status: `{payload['decision']['status']}`",
            f"- next: `{payload['decision']['recommended_next_step']}`",
            f"- runtime_sandbox_allowed: `{payload['decision']['runtime_sandbox_allowed']}`",
            "",
        ]
    )
    (ROOT / OUT_FRAME_SCHEMA_MD).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    coverage = build_coverage_payload()
    review = build_review_payload(coverage)
    frame_schema = build_frame_schema_payload(review)
    (ROOT / OUT_COVERAGE_JSON).write_text(
        json.dumps(coverage, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ROOT / OUT_REVIEW_JSON).write_text(
        json.dumps(review, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ROOT / OUT_FRAME_SCHEMA_JSON).write_text(
        json.dumps(frame_schema, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_coverage_markdown(coverage)
    write_review_markdown(review)
    write_frame_schema_markdown(frame_schema)
    print(json.dumps(review["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
