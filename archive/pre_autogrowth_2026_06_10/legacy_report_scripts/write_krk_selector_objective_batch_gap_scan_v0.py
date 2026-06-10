#!/usr/bin/env python3
"""Write replay-free selector-objective evidence diversity gap scan."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SEED = Path("reports/strategy_arbitration/krk_selector_objective_seed_manifest_v2.json")
SEED_PROBE = Path("reports/strategy_arbitration/krk_selector_objective_seed_probe_v2.json")
FEATURE_PROBE = Path("reports/strategy_arbitration/krk_selector_objective_feature_probe_v2.json")
FRESH_COLLECTION = Path(
    "reports/strategy_arbitration/krk_selector_objective_fresh_diversity_collection_v0.json"
)
FRESH_REVIEW = Path(
    "reports/strategy_arbitration/krk_selector_objective_fresh_diversity_review_packet_v0.json"
)
SPENT_MANIFEST = Path(
    "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.json"
)
OUT_JSON = Path("reports/strategy_arbitration/krk_selector_objective_batch_gap_scan_v0.json")
OUT_MD = Path("reports/strategy_arbitration/krk_selector_objective_batch_gap_scan_v0.md")

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
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _stage_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get("source_stage") or "unknown") for row in rows).items()))


def _provider_counts(rows: list[dict[str, Any]], key: str = "selected_provider") -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key) or "unknown") for row in rows).items()))


def _fresh_seed_rows(seed: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in seed.get("seed_rows") or []
        if isinstance(row, dict)
        and row.get("source_collection")
        == "fresh_stage5_6_selector_objective_diversity_collection_v0"
    ]


def _spent_fens(spent: dict[str, Any]) -> set[str]:
    return {str(job.get("seed_fen")) for job in spent.get("jobs") or [] if job.get("seed_fen")}


def _fresh_rows(collection: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in collection.get("rows") or [] if isinstance(row, dict)]


def _path_row(
    *,
    rank: int,
    path_id: str,
    rows: list[dict[str, Any]],
    duplicate_count: int,
    duplicate_risk: str,
    label_semantics_risk: str,
    rationale: str,
) -> dict[str, Any]:
    owner_counts = Counter(str(row.get("selected_owner_label") or "unknown") for row in rows)
    channel_counts = Counter(str(row.get("objective_channel") or "unknown") for row in rows)
    return {
        "rank": rank,
        "path_id": path_id,
        "expected_rows": len(rows),
        "duplicate_count": duplicate_count,
        "duplicate_risk": duplicate_risk,
        "stage_counts": _stage_counts(rows),
        "provider_counts": _provider_counts(rows, key="selected_provider_label"),
        "owner_label_counts": dict(sorted(owner_counts.items())),
        "objective_channel_counts": dict(sorted(channel_counts.items())),
        "label_semantics_risk": label_semantics_risk,
        "capacity_labels_are_not_ownership_labels": True,
        "rationale": rationale,
    }


def build_payload(
    *,
    seed: dict[str, Any] | None = None,
    seed_probe: dict[str, Any] | None = None,
    feature_probe: dict[str, Any] | None = None,
    fresh_collection: dict[str, Any] | None = None,
    fresh_review: dict[str, Any] | None = None,
    spent_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load(SEED)
    seed_probe = seed_probe or _load(SEED_PROBE)
    feature_probe = feature_probe or _load(FEATURE_PROBE)
    fresh_collection = fresh_collection or _load(FRESH_COLLECTION)
    fresh_review = fresh_review or _load(FRESH_REVIEW)
    spent_manifest = spent_manifest or _load(SPENT_MANIFEST)

    seed_rows = [row for row in seed.get("seed_rows") or [] if isinstance(row, dict)]
    fresh_rows = _fresh_rows(fresh_collection)
    fresh_seed_rows = _fresh_seed_rows(seed)
    spent = _spent_fens(spent_manifest)
    duplicate_spent_count = sum(1 for row in fresh_rows if str(row.get("fen") or "") in spent)
    stage_excluded_count = sum(
        1 for row in fresh_rows if row.get("source_stage") in {"stage4", "stage7", "stage8"}
    )
    unsafe_runtime_delta_count = sum(
        int((fresh_collection.get("summary") or {}).get(key) or 0)
        for key in (
            "selected_move_delta_count",
            "selected_provider_delta_count",
            "selected_score_delta_count",
            "score_delta_count",
            "routing_delta_count",
            "invalid_frame_count",
        )
    )
    switch_rows = [
        row for row in fresh_rows if row.get("selected_owner_label") == "selected_owner_failed"
    ]
    preserve_rows = [
        row for row in fresh_rows if row.get("selected_owner_label") == "selected_owner_converted"
    ]
    non_stage0_rows = [
        row
        for row in fresh_rows
        if str(row.get("selected_provider_label") or "") != "krk.stage0_basin"
    ]
    progress_rows = [
        row
        for row in fresh_rows
        if row.get("objective_channel") == "progress_window_failure_contrast_candidate"
    ]
    ranked_paths = [
        _path_row(
            rank=1,
            path_id="more_selected_owner_failed_switch_contrast_rows",
            rows=switch_rows,
            duplicate_count=duplicate_spent_count,
            duplicate_risk="low_against_spent_manifest; overlaps prior seed for some states but refresh counts improve",
            label_semantics_risk="low: selected-owner labels remain offline outcomes, capacity frames are evidence only",
            rationale="Adds four Stage 5/6 selected-owner failures with visible positive alternatives.",
        ),
        _path_row(
            rank=2,
            path_id="more_safe_preservation_controls",
            rows=preserve_rows,
            duplicate_count=duplicate_spent_count,
            duplicate_risk="low_against_spent_manifest; includes new protected plan-window states",
            label_semantics_risk="low: safe-preservation labels are selected-owner outcomes, not capacity labels",
            rationale="Balances switch rows with four preservation controls.",
        ),
        _path_row(
            rank=3,
            path_id="more_non_stage0_selected_owner_rows",
            rows=non_stage0_rows,
            duplicate_count=duplicate_spent_count,
            duplicate_risk="low_against_spent_manifest; limited row count remains the main risk",
            label_semantics_risk="low: provider family is provenance, not ownership",
            rationale="Adds edge-trap and fence provider families beyond stage0.",
        ),
        _path_row(
            rank=4,
            path_id="better_stage5_6_balance",
            rows=fresh_rows,
            duplicate_count=duplicate_spent_count,
            duplicate_risk="low_against_spent_manifest",
            label_semantics_risk="low",
            rationale="Fresh evidence is exactly balanced at four Stage 5 and four Stage 6 rows.",
        ),
        _path_row(
            rank=5,
            path_id="provider_family_diversity",
            rows=fresh_rows,
            duplicate_count=duplicate_spent_count,
            duplicate_risk="medium: stage0 remains dominant despite new families",
            label_semantics_risk="low: provider family is used only as a visible/provenance feature",
            rationale="Improves but does not fully solve provider-family concentration.",
        ),
        _path_row(
            rank=6,
            path_id="progress_window_failure_contrasts",
            rows=progress_rows,
            duplicate_count=duplicate_spent_count,
            duplicate_risk="low_against_spent_manifest; only two rows available",
            label_semantics_risk="low: h40 selected-successor outcome labels stay offline",
            rationale="Adds two progress-window rows but remains sparse.",
        ),
    ]
    replay_free_recovery_possible = (
        (fresh_collection.get("decision") or {}).get("collection_valid") is True
        and stage_excluded_count == 0
        and duplicate_spent_count == 0
        and unsafe_runtime_delta_count == 0
        and (seed.get("summary") or {}).get("fresh_collection_added_seed_row_count", 0) >= 3
        and (seed.get("summary") or {}).get("selector_training_row_count") == 0
        and (seed.get("summary") or {}).get("stage7_training_row_count") == 0
    )
    decision_status = (
        "selector_objective_diversity_improved_replay_free"
        if replay_free_recovery_possible
        else "selector_objective_collection_candidates_review_ready"
        if fresh_review.get("candidate_rows")
        else "selector_objective_diversity_still_blocked_no_good_rows"
    )
    return {
        "schema_version": "krk_selector_objective_batch_gap_scan.v0",
        "causal_status": "non_causal_replay_free_gap_scan",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            str(SEED),
            str(SEED_PROBE),
            str(FEATURE_PROBE),
            str(FRESH_COLLECTION),
            str(FRESH_REVIEW),
            str(SPENT_MANIFEST),
        ],
        "summary": {
            "seed_row_count": len(seed_rows),
            "fresh_collection_seed_row_count": len(fresh_seed_rows),
            "fresh_collection_joined_row_count": (fresh_collection.get("summary") or {}).get(
                "joined_row_count"
            ),
            "fresh_collection_stage_counts": (fresh_collection.get("summary") or {}).get(
                "stage_counts"
            ),
            "fresh_collection_provider_counts": (fresh_collection.get("summary") or {}).get(
                "selected_provider_counts"
            ),
            "fresh_collection_selected_owner_counts": (
                fresh_collection.get("summary") or {}
            ).get("selected_owner_counts"),
            "fresh_collection_generated_frame_count": (
                fresh_collection.get("summary") or {}
            ).get("generated_frame_count"),
            "duplicate_spent_manifest_count": duplicate_spent_count,
            "stage4_7_8_fresh_row_count": stage_excluded_count,
            "unsafe_runtime_delta_count": unsafe_runtime_delta_count,
            "selector_training_row_count": (seed.get("summary") or {}).get(
                "selector_training_row_count"
            ),
            "stage7_training_row_count": (seed.get("summary") or {}).get(
                "stage7_training_row_count"
            ),
            "runtime_authorization_row_count": (seed.get("summary") or {}).get(
                "runtime_authorization_row_count"
            ),
            "seed_probe_status": (seed_probe.get("decision") or {}).get("status"),
            "feature_probe_status": (feature_probe.get("decision") or {}).get("status"),
            "replay_free_recovery_possible": replay_free_recovery_possible,
        },
        "ranked_evidence_paths": ranked_paths,
        "decision": {
            "status": decision_status,
            "collection_run_allowed": False,
            "label_run_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "recommended_next_step": (
                "stop_at_feature_probe_review_boundary"
                if decision_status == "selector_objective_diversity_improved_replay_free"
                else "review_ranked_collection_packet_before_any_collection"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Selector Objective Batch Gap Scan v0",
        "",
        "This scan ranks replay-free evidence-expansion paths. It does not execute collection, train a selector, or authorize runtime behavior.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- collection_run_allowed: `{payload['decision']['collection_run_allowed']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- runtime_changes_allowed: `{payload['decision']['runtime_changes_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Ranked Evidence Paths", ""])
    for row in payload["ranked_evidence_paths"]:
        lines.append(
            "- "
            f"rank={row['rank']} "
            f"path=`{row['path_id']}` "
            f"expected_rows={row['expected_rows']} "
            f"duplicate_risk=`{row['duplicate_risk']}` "
            f"label_semantics_risk=`{row['label_semantics_risk']}` "
            f"stage_counts={row['stage_counts']} "
            f"provider_counts={row['provider_counts']}"
        )
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
