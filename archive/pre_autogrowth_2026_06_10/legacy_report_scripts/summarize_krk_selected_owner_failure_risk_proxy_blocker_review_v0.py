#!/usr/bin/env python3
"""Summarize the failed selected-owner failure-risk proxy validation.

This is an architecture/reporting script only. It closes the v0 one-ply
move-shape proxy path after independent protected validation failed and points
the next evidence slice at visible competing-proposal and progress-window
signals.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DISCOVERY_REVIEW = Path("reports/krk_selected_owner_failure_risk_visible_proxy_review_v0.json")
INDEPENDENT_VALIDATION = Path("reports/krk_selected_owner_failure_risk_proxy_independent_validation_v0.json")
INDEPENDENT_LABELS = Path("reports/krk_selected_owner_failure_risk_proxy_independent_labels_v0.json")

OUT_JSON = Path("reports/krk_selected_owner_failure_risk_proxy_blocker_review_v0.json")
OUT_MD = Path("reports/krk_selected_owner_failure_risk_proxy_blocker_review_v0.md")

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
    "selector_training_allowed",
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _runtime_false_block() -> dict[str, bool]:
    return {key: False for key in RUNTIME_FALSE_KEYS}


def _validate_non_causal(payload: dict[str, Any]) -> None:
    for key in RUNTIME_FALSE_KEYS:
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if payload.get("implementation_allowed_by_this_review") is not False:
        raise ValueError("implementation_allowed_by_this_review must be false")
    if (payload.get("summary") or {}).get("stage7_row_count", 0) != 0:
        raise ValueError("Stage 7 rows must not be readiness rows")


def _examples(labels: list[dict[str, Any]], *, proxy_fires: bool, target: bool) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for row in labels:
        if bool(row.get("proxy_fires")) != proxy_fires:
            continue
        if bool(row.get("selected_owner_failure_risk_target")) != target:
            continue
        selected = row.get("selected_playout_success") or {}
        forced = row.get("forced_alternative_result") or {}
        examples.append(
            {
                "state_id": row.get("frame_id") or row.get("state_id"),
                "source_stage": (row.get("runtime_visible_candidate_features") or {}).get("source_stage"),
                "active_landmark_label": row.get("active_landmark_label"),
                "fen": row.get("fen"),
                "selected_owner": (row.get("runtime_visible_candidate_features") or {}).get("selected_owner_family"),
                "selected_move": row.get("selected_move"),
                "forced_alternative_provider": row.get("forced_alternative_provider"),
                "selected_result": selected.get("result"),
                "forced_result": forced.get("result"),
                "runtime_visible_candidate_features": row.get("runtime_visible_candidate_features") or {},
            }
        )
    return examples


def build_review(
    *,
    discovery_review: dict[str, Any] | None = None,
    independent_validation: dict[str, Any] | None = None,
    independent_labels: dict[str, Any] | None = None,
) -> dict[str, Any]:
    discovery_review = discovery_review if discovery_review is not None else _load(DISCOVERY_REVIEW)
    independent_validation = (
        independent_validation if independent_validation is not None else _load(INDEPENDENT_VALIDATION)
    )
    independent_labels = independent_labels if independent_labels is not None else _load(INDEPENDENT_LABELS)

    labels = list(independent_labels.get("labels") or [])
    metrics = independent_validation.get("metrics") or {}
    discovery_summary = discovery_review.get("summary") or {}
    independent_summary = independent_validation.get("summary") or {}
    false_positives = _examples(labels, proxy_fires=True, target=False)
    false_negatives = _examples(labels, proxy_fires=False, target=True)

    payload = {
        "schema_version": "krk_selected_owner_failure_risk_proxy_blocker_review.v0",
        "causal_status": "non_causal_architecture_review",
        **_runtime_false_block(),
        "implementation_allowed_by_this_review": False,
        "source_artifacts": [
            str(DISCOVERY_REVIEW),
            str(INDEPENDENT_VALIDATION),
            str(INDEPENDENT_LABELS),
        ],
        "summary": {
            "discovery_proxy_precision": discovery_summary.get("proxy_precision"),
            "discovery_proxy_recall": discovery_summary.get("proxy_recall"),
            "discovery_safe_preservation_recall": discovery_summary.get("safe_preservation_recall"),
            "independent_proxy_precision": metrics.get("precision"),
            "independent_proxy_recall": metrics.get("recall"),
            "independent_safe_preservation_recall": metrics.get("safe_preservation_recall"),
            "false_positive_count": metrics.get("false_positive"),
            "false_negative_count": metrics.get("false_negative"),
            "label_count": independent_summary.get("label_count"),
            "stage7_row_count": independent_summary.get("stage7_row_count"),
            "threshold_met": independent_summary.get("threshold_met"),
        },
        "classification": {
            "one_ply_move_shape_proxy": "rejected_overfit_to_discovery_dataset",
            "selected_owner_failure_risk_visibility": "missing_visible_competing_proposal_or_progress_window_evidence",
            "runtime_review_packet": "blocked",
        },
        "interpretation": [
            "The v0 proxy fit the discovery dataset but failed independent protected validation.",
            "The independent run produced false positives on safe-preservation cases and missed the only selected-owner failure-risk case.",
            "A one-ply selected move-shape proxy is insufficient as a runtime-review basis.",
            "The next evidence must expose visible competing-provider proposals or selected-owner progress-window failure, not forced-capacity labels alone.",
        ],
        "false_positive_examples": false_positives,
        "false_negative_examples": false_negatives,
        "next_evidence_tracks": [
            {
                "track": "visible_competing_proposal_evidence",
                "needed_terms": [
                    "alternative_provider_live_proposal",
                    "alternative_provider_role_licensed",
                    "alternative_provider_score_visible",
                    "same_state_provider_conflict_visible",
                    "provider_family_pair",
                ],
            },
            {
                "track": "progress_window_failure_evidence",
                "needed_terms": [
                    "selected_owner_trace_available",
                    "selected_owner_no_edge_progress",
                    "selected_owner_no_mate_progress",
                    "selected_owner_repeated_abstract_state",
                    "selected_owner_no_progress_plies",
                ],
            },
        ],
        "decision": {
            "status": "failed_proxy_closed_next_evidence_v1_required",
            "recommended_next_step": "build_selected_owner_failure_risk_evidence_v1",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
        },
    }
    _validate_non_causal(payload)
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    decision = payload["decision"]
    lines = [
        "# KRK Selected-Owner Failure-Risk Proxy Blocker Review v0",
        "",
        "## Decision",
        "",
        f"- status: `{decision['status']}`",
        f"- next step: `{decision['recommended_next_step']}`",
        "- runtime work allowed: `false`",
        "- selector training allowed: `false`",
        "",
        "## Metrics",
        "",
        f"- discovery precision / recall / safe-preservation: `{summary['discovery_proxy_precision']}` / `{summary['discovery_proxy_recall']}` / `{summary['discovery_safe_preservation_recall']}`",
        f"- independent precision / recall / safe-preservation: `{summary['independent_proxy_precision']}` / `{summary['independent_proxy_recall']}` / `{summary['independent_safe_preservation_recall']}`",
        f"- false positives / false negatives: `{summary['false_positive_count']}` / `{summary['false_negative_count']}`",
        f"- label count: `{summary['label_count']}`",
        f"- Stage 7 readiness rows: `{summary['stage7_row_count']}`",
        "",
        "## Interpretation",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["interpretation"])
    lines.extend(
        [
            "",
            "## Blocked Path",
            "",
            "- The v0 one-ply move-shape proxy is rejected as overfit to the discovery dataset.",
            "- No runtime-review packet is authorized from this evidence.",
            "- Future evidence must separate forced-capacity labels from visible ownership-failure risk.",
            "",
            "## Next Evidence Tracks",
            "",
        ]
    )
    for track in payload["next_evidence_tracks"]:
        lines.append(f"- `{track['track']}`: {', '.join(f'`{term}`' for term in track['needed_terms'])}")
    lines.extend(
        [
            "",
            "## Non-Causal Boundary",
            "",
            "- No runtime selector behavior.",
            "- No runtime terminals.",
            "- No selector training.",
            "- No Stage 7 promotion.",
            "- No Stage 8 training.",
            "- No runtime DTM/tablebase.",
            "- No gameplay-time topology mutation.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
