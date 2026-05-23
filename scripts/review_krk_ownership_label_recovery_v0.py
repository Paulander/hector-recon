#!/usr/bin/env python3
"""Review ownership-label recovery after KRK strategy-sequence dataset v5."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v5.json")
OWNERSHIP = Path("reports/krk_ownership_selection_label_dataset_v5.json")
PAIRED_REVIEW = Path("reports/krk_state_local_paired_ownership_review_v1.json")
PROGRESS_AUDIT = Path("reports/krk_progress_window_reconsideration_post_activation_audit_v0.json")
BOUNDARY = Path("reports/strategy_arbitration/krk_candidate_generation_v5_next_boundary_review_v0.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_ownership_label_recovery_review_v0.json")
OUT_MD = Path("reports/strategy_arbitration/krk_ownership_label_recovery_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _provider_trace_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("evidence_channel") == "runtime_observation_trace_feature"
        and not row.get("stage7_challenge_row")
        and row.get("candidate_provider_id")
    ]


def _ownership_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in payload.get("rows") or []
        if isinstance(row, dict) and row.get("source_stage") != "stage7"
    ]


def build_payload(
    *,
    dataset: dict[str, Any] | None = None,
    ownership: dict[str, Any] | None = None,
    paired_review: dict[str, Any] | None = None,
    progress_audit: dict[str, Any] | None = None,
    boundary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dataset = dataset or _load(DATASET)
    ownership = ownership or _load(OWNERSHIP)
    paired_review = paired_review or _load(PAIRED_REVIEW)
    progress_audit = progress_audit or _load(PROGRESS_AUDIT)
    boundary = boundary or _load(BOUNDARY)

    dataset_rows = [row for row in dataset.get("rows") or [] if isinstance(row, dict)]
    trace_rows = _provider_trace_rows(dataset_rows)
    own_rows = _ownership_rows(ownership)
    trace_by_state: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in trace_rows:
        trace_by_state[str(row.get("state_id"))].append(row)

    joined_records = []
    for own in own_rows:
        state_id = str(own.get("state_id") or "")
        state_trace = trace_by_state.get(state_id, [])
        positive_candidates = [
            row
            for row in state_trace
            if str(row.get("capacity_label") or "").startswith("positive_capacity")
        ]
        if not state_trace:
            continue
        converted = own.get("target_label") == "selected_owner_converted"
        if converted and positive_candidates:
            recovery_class = "safe_preservation_with_visible_positive_alternative"
        elif not converted and positive_candidates:
            recovery_class = "selected_failure_with_visible_positive_alternative"
        elif converted:
            recovery_class = "safe_owner_with_trace_context_only"
        else:
            recovery_class = "selected_failure_with_trace_context_only"
        joined_records.append(
            {
                "state_id": state_id,
                "source_stage": own.get("source_stage"),
                "selected_provider": own.get("provider_id"),
                "selected_provider_family": own.get("provider_family"),
                "target_label": own.get("target_label"),
                "trace_provider_candidate_count": len(state_trace),
                "positive_trace_provider_candidate_count": len(positive_candidates),
                "trace_sources": sorted(
                    {str(row.get("trace_feature_source") or "unknown") for row in state_trace}
                ),
                "recovery_class": recovery_class,
                "usable_for_selector_training": False,
            }
        )

    class_counts = Counter(record["recovery_class"] for record in joined_records)
    source_stage_counts = Counter(str(row.get("source_stage") or "unknown") for row in own_rows)
    provider_family_counts = Counter(str(row.get("provider_family") or "unknown") for row in own_rows)
    label_counts = Counter(str(row.get("target_label") or "unknown") for row in own_rows)
    selector_rows = int((ownership.get("summary") or {}).get("selector_training_row_count", 0) or 0)
    stage7_rows = int((ownership.get("summary") or {}).get("stage7_row_count", 0) or 0)
    paired_summary = paired_review.get("summary") or {}
    progress_classification = progress_audit.get("classification") or {}
    candidate_context_ready = (
        (boundary.get("decision") or {}).get("status")
        == "candidate_generation_v5_next_boundary_context_improved_selector_blocked"
    )
    seed_manifest_ready = (
        class_counts["selected_failure_with_visible_positive_alternative"] > 0
        and class_counts["safe_preservation_with_visible_positive_alternative"] > 0
        and selector_rows == 0
        and stage7_rows == 0
    )

    return {
        "schema_version": "krk_ownership_label_recovery_review.v0",
        "causal_status": "non_causal_label_recovery_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            str(DATASET),
            str(OWNERSHIP),
            str(PAIRED_REVIEW),
            str(PROGRESS_AUDIT),
            str(BOUNDARY),
        ],
        "summary": {
            "ownership_row_count": len(own_rows),
            "ownership_target_label_counts": dict(sorted(label_counts.items())),
            "ownership_source_stage_counts": dict(sorted(source_stage_counts.items())),
            "ownership_provider_family_counts": dict(sorted(provider_family_counts.items())),
            "selector_training_row_count": selector_rows,
            "stage7_row_count": stage7_rows,
            "runtime_trace_provider_candidate_row_count": len(trace_rows),
            "joined_state_count": len(joined_records),
            "joined_recovery_class_counts": dict(sorted(class_counts.items())),
            "selected_failure_with_visible_positive_alternative_count": class_counts[
                "selected_failure_with_visible_positive_alternative"
            ],
            "safe_preservation_with_visible_positive_alternative_count": class_counts[
                "safe_preservation_with_visible_positive_alternative"
            ],
            "paired_threshold_passing_model_count": paired_summary.get(
                "threshold_passing_model_count"
            ),
            "paired_runtime_feature_passing_model_count": paired_summary.get(
                "runtime_feature_passing_model_count"
            ),
            "progress_sandbox_primary_failure_class": progress_classification.get("primary"),
            "candidate_context_ready": candidate_context_ready,
        },
        "joined_records": joined_records,
        "label_recovery_gaps": [
            "ownership labels are still offline evidence and not selector-training rows",
            "provider-family diversity remains narrow, especially stage0_basin-heavy",
            "paired objective semantics pass only with offline outcome/channel labels",
            "runtime feature translation remains unresolved for a general selector",
            "progress-window sandbox failure showed candidate-set coverage can still be missing",
        ],
        "forbidden_uses": [
            "selector_training",
            "score_changes",
            "provider_routing",
            "capacity_labels_as_ownership_labels",
            "stage7_training_or_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
        "decision": {
            "status": (
                "ownership_label_recovery_seed_manifest_ready_selector_blocked"
                if seed_manifest_ready
                else "ownership_label_recovery_underpowered_selector_blocked"
            ),
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": (
                "build_non_causal_selector_objective_seed_manifest"
                if seed_manifest_ready
                else "collect_more_normal_routing_ownership_labels_non_causal"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Ownership Label Recovery Review v0",
        "",
        "This review joins dataset v5 candidate-generation trace context with existing ownership labels. It is a non-causal label-recovery review, not selector training.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- runtime_changes_allowed: `{payload['decision']['runtime_changes_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Label Recovery Gaps", ""])
    lines.extend(f"- `{item}`" for item in payload["label_recovery_gaps"])
    lines.extend(["", "## Forbidden Uses", ""])
    lines.extend(f"- `{item}`" for item in payload["forbidden_uses"])
    lines.extend(["", "## Joined Records", ""])
    for record in payload["joined_records"]:
        lines.append(
            "- "
            f"`{record['state_id']}` "
            f"{record['target_label']} "
            f"{record['selected_provider']} "
            f"trace_candidates={record['trace_provider_candidate_count']} "
            f"positive_trace_candidates={record['positive_trace_provider_candidate_count']} "
            f"class=`{record['recovery_class']}`"
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
