#!/usr/bin/env python3
"""Write a fresh Stage 5/6-only selector-objective diversity review packet.

This is a review-only artifact for a possible future observation collection.
It does not execute collection, train a selector, change runtime behavior,
promote Stage 7, or train Stage 8.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTEXT_DATASET = ROOT / "reports/krk_ownership_selection_context_dataset_v3.json"
PROTECTED_WINDOWS = (
    ROOT / "reports/strategy_arbitration/krk_protected_plan_window_frames_v0.json"
)
SPENT_MANIFEST = (
    ROOT
    / "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.json"
)
SEED_V2 = (
    ROOT / "reports/strategy_arbitration/krk_selector_objective_seed_manifest_v2.json"
)
OLD_REVIEW_PACKET = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_selector_objective_diverse_collection_review_packet_v0.json"
)
DIVERSITY_GAP_REVIEW = (
    ROOT / "reports/strategy_arbitration/krk_selector_objective_diversity_gap_review_v0.json"
)
ADDITIONAL_COLLECTION_DECISION = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_failure_contrast_additional_collection_decision_v1.json"
)

OUT_MANIFEST_JSON = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_selector_objective_fresh_diversity_manifest_v0.json"
)
OUT_MANIFEST_MD = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_selector_objective_fresh_diversity_manifest_v0.md"
)
OUT_REVIEW_JSON = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_selector_objective_fresh_diversity_review_packet_v0.json"
)
OUT_REVIEW_MD = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_selector_objective_fresh_diversity_review_packet_v0.md"
)

PROTECTED_STAGES = {"stage5", "stage6"}
EXCLUDED_STAGES = {"stage4", "stage7", "stage8"}
CONTEXT_STATE_IDS = [
    "state.0b1f2153179b",
    "state.3dca34326fca",
    "state.02feb8593cc6",
    "state.67a88e3b1dd2",
    "state.699f0003a511",
    "state.d1f052d2cab2",
]
PLAN_WINDOW_FRAME_IDS = [
    "planwin.227342c93b11",
    "planwin.5fa48b6e0286",
]

COMMON_FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "runtime_selector_implemented": False,
    "runtime_score_changes": False,
    "runtime_direct_routing": False,
    "runtime_provider_suppression": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "hidden_python_controller": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return payload


def _provider_family(provider: Any) -> str:
    text = str(provider or "")
    if text.startswith("krk."):
        text = text[4:]
    if text.startswith("edge_trap"):
        return text
    return text or "unknown"


def _objective_channel(selected_owner_label: str, source_type: str) -> str:
    if selected_owner_label == "selected_owner_failed":
        return "candidate_switch_contrast_seed"
    if source_type == "protected_plan_window_frame":
        return "progress_window_failure_contrast_candidate"
    return "safe_preservation_contrast_seed"


def _why(row: dict[str, Any]) -> str:
    if row["selected_owner_label"] == "selected_owner_failed":
        return (
            "adds a Stage 5/6 selected-owner failure switch-contrast row without "
            "using capacity labels as ownership labels"
        )
    if row["source_type"] == "protected_plan_window_frame":
        return (
            "adds an unused protected plan-window state for future failure-contrast "
            "observation while avoiding the spent v0 manifest"
        )
    return "adds Stage 5/6 safe-preservation balance for the switch-vs-preserve objective"


def _row_from_context(
    row: dict[str, Any],
    *,
    index: int,
    seed_state_ids: set[str],
    old_review_state_ids: set[str],
    spent_fens: set[str],
) -> dict[str, Any]:
    stage = str(row.get("source_stage") or "")
    label = str(row.get("target_label") or "")
    provider = str(row.get("provider_id") or "")
    fen = str(row.get("fen") or "")
    state_id = str(row.get("state_id") or "")
    source_type = "ownership_context_replay_free"
    out = {
        "schema_version": "krk_selector_objective_fresh_diversity_row.v0",
        "causal_status": "non_causal_collection_candidate_review_row",
        "row_id": f"selector_objective_fresh_diversity.{index:02d}",
        "source_type": source_type,
        "state_id": state_id,
        "frame_id": row.get("frame_id"),
        "fen": fen,
        "source_stage": stage,
        "active_landmark_label": row.get("active_landmark_label"),
        "selected_provider": provider,
        "selected_provider_family": _provider_family(provider),
        "selected_owner_label": label,
        "objective_channel": _objective_channel(label, source_type),
        "target_collection_goal": (
            "switch_contrast_observation"
            if label == "selected_owner_failed"
            else "safe_preservation_observation"
        ),
        "label_source": "ownership_context_selected_playout_outcome",
        "capacity_label_used_as_ownership_label": False,
        "why_adds_new_evidence": "",
        "duplicate_risk": {
            "spent_failure_contrast_manifest_duplicate": fen in spent_fens,
            "existing_seed_manifest_v2_state_overlap": state_id in seed_state_ids,
            "prior_diverse_review_packet_state_overlap": state_id in old_review_state_ids,
        },
        "requires_explicit_collection_approval": True,
        "collection_run_allowed_by_manifest": False,
        "runtime_behavior_changed": False,
        "usable_for_selector_training": False,
        "usable_for_runtime_authorization": False,
        "stage7_training_row": False,
    }
    out["why_adds_new_evidence"] = _why(out)
    return out


def _row_from_plan_window(
    frame: dict[str, Any],
    *,
    index: int,
    spent_frame_ids: set[str],
    spent_fens: set[str],
) -> dict[str, Any]:
    provider = str(frame.get("selected_successor") or "")
    label = (
        "selected_owner_converted"
        if frame.get("h40_outcome_label") == "conversion_positive"
        else "selected_owner_failed"
    )
    fen = str(frame.get("fen") or "")
    source_type = "protected_plan_window_frame"
    out = {
        "schema_version": "krk_selector_objective_fresh_diversity_row.v0",
        "causal_status": "non_causal_collection_candidate_review_row",
        "row_id": f"selector_objective_fresh_diversity.{index:02d}",
        "source_type": source_type,
        "state_id": f"protected.{frame.get('frame_id')}",
        "frame_id": frame.get("frame_id"),
        "fen": fen,
        "source_stage": frame.get("source_stage"),
        "source_family": frame.get("source_family"),
        "active_landmark_label": frame.get("active_landmark_label"),
        "selected_provider": provider,
        "selected_provider_family": _provider_family(provider),
        "selected_owner_label": label,
        "objective_channel": _objective_channel(label, source_type),
        "target_collection_goal": "progress_window_failure_contrast_observation",
        "label_source": "protected_plan_window_selected_successor_h40_outcome",
        "capacity_label_used_as_ownership_label": False,
        "why_adds_new_evidence": "",
        "duplicate_risk": {
            "spent_failure_contrast_manifest_duplicate": (
                frame.get("frame_id") in spent_frame_ids or fen in spent_fens
            ),
            "existing_seed_manifest_v2_state_overlap": False,
            "prior_diverse_review_packet_state_overlap": False,
        },
        "requires_explicit_collection_approval": True,
        "collection_run_allowed_by_manifest": False,
        "runtime_behavior_changed": False,
        "usable_for_selector_training": False,
        "usable_for_runtime_authorization": False,
        "stage7_training_row": False,
    }
    out["why_adds_new_evidence"] = _why(out)
    return out


def build_manifest() -> dict[str, Any]:
    context = _load(CONTEXT_DATASET)
    windows = _load(PROTECTED_WINDOWS)
    spent = _load(SPENT_MANIFEST)
    seed_v2 = _load(SEED_V2)
    old_review = _load(OLD_REVIEW_PACKET)

    seed_state_ids = {
        str(row.get("state_id")) for row in seed_v2.get("seed_rows") or [] if row.get("state_id")
    }
    old_review_state_ids = {
        str(row.get("state_id"))
        for row in old_review.get("review_rows") or []
        if row.get("state_id")
    }
    spent_frame_ids = {
        str(job.get("seed_frame_id"))
        for job in spent.get("jobs") or []
        if job.get("seed_frame_id")
    }
    spent_fens = {
        str(job.get("seed_fen")) for job in spent.get("jobs") or [] if job.get("seed_fen")
    }

    context_by_id = {
        str(row.get("state_id")): row
        for row in context.get("rows") or []
        if row.get("state_id")
    }
    frame_by_id = {
        str(frame.get("frame_id")): frame
        for frame in windows.get("frames") or []
        if frame.get("frame_id")
    }

    rows: list[dict[str, Any]] = []
    for state_id in CONTEXT_STATE_IDS:
        rows.append(
            _row_from_context(
                context_by_id[state_id],
                index=len(rows) + 1,
                seed_state_ids=seed_state_ids,
                old_review_state_ids=old_review_state_ids,
                spent_fens=spent_fens,
            )
        )
    for frame_id in PLAN_WINDOW_FRAME_IDS:
        rows.append(
            _row_from_plan_window(
                frame_by_id[frame_id],
                index=len(rows) + 1,
                spent_frame_ids=spent_frame_ids,
                spent_fens=spent_fens,
            )
        )

    stage_counts = Counter(row["source_stage"] for row in rows)
    owner_counts = Counter(row["selected_owner_label"] for row in rows)
    provider_counts = Counter(row["selected_provider"] for row in rows)
    provider_family_counts = Counter(row["selected_provider_family"] for row in rows)
    channel_counts = Counter(row["objective_channel"] for row in rows)
    duplicate_spent_count = sum(
        1 for row in rows if row["duplicate_risk"]["spent_failure_contrast_manifest_duplicate"]
    )
    duplicate_candidate_fen_count = len(rows) - len({row["fen"] for row in rows})
    seed_overlap_count = sum(
        1 for row in rows if row["duplicate_risk"]["existing_seed_manifest_v2_state_overlap"]
    )
    old_review_overlap_count = sum(
        1 for row in rows if row["duplicate_risk"]["prior_diverse_review_packet_state_overlap"]
    )
    valid_scope = (
        len(rows) == 8
        and set(stage_counts) == PROTECTED_STAGES
        and not (set(stage_counts) & EXCLUDED_STAGES)
        and stage_counts["stage5"] == stage_counts["stage6"] == 4
        and owner_counts["selected_owner_failed"] >= 4
        and channel_counts["candidate_switch_contrast_seed"] >= 4
        and channel_counts["progress_window_failure_contrast_candidate"] >= 2
        and duplicate_spent_count == 0
        and duplicate_candidate_fen_count == 0
        and all(row["capacity_label_used_as_ownership_label"] is False for row in rows)
        and all(row["usable_for_selector_training"] is False for row in rows)
        and all(row["stage7_training_row"] is False for row in rows)
    )
    return {
        "schema_version": "krk_selector_objective_fresh_diversity_manifest.v0",
        "causal_status": "non_causal_collection_manifest",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            str(CONTEXT_DATASET.relative_to(ROOT)),
            str(PROTECTED_WINDOWS.relative_to(ROOT)),
            str(SPENT_MANIFEST.relative_to(ROOT)),
            str(SEED_V2.relative_to(ROOT)),
            str(OLD_REVIEW_PACKET.relative_to(ROOT)),
            str(DIVERSITY_GAP_REVIEW.relative_to(ROOT)),
            str(ADDITIONAL_COLLECTION_DECISION.relative_to(ROOT)),
        ],
        "collection_constraints": {
            "review_packet_only": True,
            "collection_run_allowed": False,
            "requires_future_explicit_approval": True,
            "max_rows": 8,
            "included_stages": sorted(PROTECTED_STAGES),
            "excluded_stages": sorted(EXCLUDED_STAGES),
            "observation_only": True,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "runtime_dtm_or_tablebase_allowed": False,
            "gameplay_topology_mutation_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "summary": {
            "candidate_row_count": len(rows),
            "stage_counts": dict(sorted(stage_counts.items())),
            "selected_provider_counts": dict(sorted(provider_counts.items())),
            "selected_provider_family_counts": dict(sorted(provider_family_counts.items())),
            "selected_owner_failed_count": owner_counts["selected_owner_failed"],
            "selected_owner_converted_count": owner_counts["selected_owner_converted"],
            "switch_contrast_count": channel_counts["candidate_switch_contrast_seed"],
            "safe_preservation_count": owner_counts["selected_owner_converted"],
            "progress_window_failure_contrast_count": channel_counts[
                "progress_window_failure_contrast_candidate"
            ],
            "non_stage0_selected_owner_count": sum(
                1 for row in rows if row["selected_provider_family"] != "stage0_basin"
            ),
            "spent_manifest_duplicate_count": duplicate_spent_count,
            "duplicate_candidate_fen_count": duplicate_candidate_fen_count,
            "existing_seed_manifest_v2_state_overlap_count": seed_overlap_count,
            "prior_diverse_review_packet_state_overlap_count": old_review_overlap_count,
            "duplicate_risk_assessment": (
                "fresh_against_spent_failure_contrast_manifest_with_known_seed_overlap"
            ),
            "replay_free_recovery_enough": False,
            "selector_training_row_count": 0,
            "stage7_training_row_count": 0,
            "runtime_authorization_row_count": 0,
            "valid_scope": valid_scope,
        },
        "candidate_rows": rows,
        "decision": {
            "status": (
                "fresh_stage5_stage6_diversity_collection_review_ready"
                if valid_scope
                else "selector_objective_diversity_still_blocked_no_good_rows"
            ),
            "recommended_next_step": (
                "review_packet_only_wait_for_future_explicit_collection_approval"
                if valid_scope
                else "architecture_review_required_before_more_selector_objective_collection"
            ),
            "collection_run_allowed": False,
            "label_run_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def build_review(manifest: dict[str, Any]) -> dict[str, Any]:
    summary = manifest["summary"]
    decision_status = manifest["decision"]["status"]
    ready = decision_status == "fresh_stage5_stage6_diversity_collection_review_ready"
    return {
        "schema_version": "krk_selector_objective_fresh_diversity_review_packet.v0",
        "causal_status": "non_causal_review_packet",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_selector_objective_fresh_diversity_manifest_v0.json",
            *manifest["source_artifacts"],
        ],
        "candidate_rows": manifest["candidate_rows"],
        "review": {
            "replay_free_recovery_attempted": True,
            "replay_free_recovery_enough": False,
            "why_seed_probe_not_rewritten": (
                "Stage 5/6 replay-free evidence still has sparse switch/failure "
                "diversity; existing v2 seed/probe depends on Stage 4 rows."
            ),
            "duplicate_risk_assessment": summary["duplicate_risk_assessment"],
            "capacity_labels_are_not_ownership_labels": True,
            "review_packet_only": True,
            "future_collection_requires_explicit_approval": True,
        },
        "summary": {
            "candidate_row_count": summary["candidate_row_count"],
            "stage_counts": summary["stage_counts"],
            "provider_counts": summary["selected_provider_counts"],
            "provider_family_counts": summary["selected_provider_family_counts"],
            "selected_owner_failed_count": summary["selected_owner_failed_count"],
            "selected_owner_converted_count": summary["selected_owner_converted_count"],
            "switch_contrast_count": summary["switch_contrast_count"],
            "safe_preservation_count": summary["safe_preservation_count"],
            "progress_window_failure_contrast_count": summary[
                "progress_window_failure_contrast_count"
            ],
            "non_stage0_selected_owner_count": summary["non_stage0_selected_owner_count"],
            "spent_manifest_duplicate_count": summary["spent_manifest_duplicate_count"],
            "duplicate_candidate_fen_count": summary["duplicate_candidate_fen_count"],
            "existing_seed_manifest_v2_state_overlap_count": summary[
                "existing_seed_manifest_v2_state_overlap_count"
            ],
            "prior_diverse_review_packet_state_overlap_count": summary[
                "prior_diverse_review_packet_state_overlap_count"
            ],
            "selector_training_row_count": 0,
            "stage7_training_row_count": 0,
            "runtime_authorization_row_count": 0,
        },
        "decision": {
            "status": (
                "fresh_stage5_stage6_diversity_collection_review_ready"
                if ready
                else "selector_objective_diversity_still_blocked_no_good_rows"
            ),
            "recommended_next_step": (
                "stop_until_future_explicit_approval_to_execute_reviewed_collection"
                if ready
                else "architecture_review_required_before_more_selector_objective_collection"
            ),
            "collection_run_allowed": False,
            "label_run_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "runtime_ready": False,
            "selector_ready": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def _write_markdown(path: Path, title: str, payload: dict[str, Any]) -> None:
    lines = [
        f"# {title}",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        "This artifact is review-only. It does not execute collection, train a selector, change runtime behavior, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Candidate Rows", ""])
    for row in payload["candidate_rows"]:
        lines.append(
            "- "
            f"`{row['row_id']}` "
            f"stage=`{row['source_stage']}` "
            f"provider=`{row['selected_provider']}` "
            f"label=`{row['selected_owner_label']}` "
            f"channel=`{row['objective_channel']}` "
            f"why={row['why_adds_new_evidence']}"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
            "- collection_run_allowed: `false`",
            "- selector_training_allowed: `false`",
            "- runtime_changes_allowed: `false`",
            "- Stage 7 promotion and Stage 8 training remain blocked.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    manifest = build_manifest()
    review = build_review(manifest)
    OUT_MANIFEST_JSON.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_markdown(
        OUT_MANIFEST_MD,
        "KRK Selector Objective Fresh Diversity Manifest v0",
        manifest,
    )
    OUT_REVIEW_JSON.write_text(
        json.dumps(review, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_markdown(
        OUT_REVIEW_MD,
        "KRK Selector Objective Fresh Diversity Review Packet v0",
        review,
    )
    print(json.dumps(review["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
