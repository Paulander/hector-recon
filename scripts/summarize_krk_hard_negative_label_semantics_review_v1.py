#!/usr/bin/env python3
"""Review hard-negative capacity labels before selector use."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TARGETS = Path("reports/krk_hard_negative_selector_target_dataset_v2.json")
ABLATION = Path("reports/krk_hard_negative_selector_feature_ablation_v2.json")
EVIDENCE_REVIEW = Path("reports/krk_balanced_hard_negative_evidence_review_v0.json")
OUT_JSON = Path("reports/krk_hard_negative_label_semantics_review_v1.json")
OUT_MD = Path("reports/krk_hard_negative_label_semantics_review_v1.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _target_label(row: dict[str, Any]) -> str:
    if row.get("target_kind") == "hard_negative_capacity":
        return "capacity_negative"
    if row.get("target_kind") == "positive_capacity_context":
        return "capacity_positive"
    return "unknown"


def _state_outcome_profile(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("state_id"))].append(row)
    profiles = {}
    for state_id, state_rows in grouped.items():
        labels = Counter(_target_label(row) for row in state_rows)
        profiles[state_id] = {
            "row_count": len(state_rows),
            "capacity_positive": labels["capacity_positive"],
            "capacity_negative": labels["capacity_negative"],
            "has_state_local_contrast": labels["capacity_positive"] > 0 and labels["capacity_negative"] > 0,
            "providers": sorted({str(row.get("provider_id")) for row in state_rows}),
            "source_stages": sorted({str(row.get("source_stage")) for row in state_rows}),
        }
    return profiles


def build_review() -> dict[str, Any]:
    targets = _load(TARGETS)
    ablation = _load(ABLATION)
    evidence = _load(EVIDENCE_REVIEW)
    if targets.get("causal_status") != "non_causal_target_dataset":
        raise ValueError("targets must remain non-causal")
    if ablation.get("causal_status") != "non_causal_feature_ablation":
        raise ValueError("ablation must remain non-causal")
    if evidence.get("causal_status") != "non_causal_evidence_review":
        raise ValueError("evidence review must remain non-causal")
    rows = list(targets.get("rows") or [])
    profiles = _state_outcome_profile(rows)
    contrast_states = [state for state, profile in profiles.items() if profile["has_state_local_contrast"]]
    source_channels = Counter(str(row.get("source_artifact_channel")) for row in rows)
    label_by_channel: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        label_by_channel[str(row.get("source_artifact_channel"))][_target_label(row)] += 1
    semantics = [
        {
            "label_channel": "forced_provider_capacity_label",
            "allowed_use": "candidate_capacity_evidence_and_offline_feature_probe",
            "blocked_use": "direct_runtime_owner_selection_or_suppression",
            "reason": (
                "The labels force a provider for the first White move and then release. "
                "A mate result shows the provider can participate in conversion under that intervention; "
                "a max_plies result shows this forced path failed, not that the provider is always unsafe."
            ),
        },
        {
            "label_channel": "state_local_capacity_contrast",
            "allowed_use": "learn comparisons only within states or matched state families",
            "blocked_use": "global provider-family suppression",
            "reason": (
                "The same provider family can be positive in one protected state and negative in another. "
                "Global labels would over-suppress validated providers."
            ),
        },
        {
            "label_channel": "hard_negative_capacity",
            "allowed_use": "offline risk feature and hard-negative mining",
            "blocked_use": "selector training target until safe-owner preservation is separately validated",
            "reason": "The current hard-negative support is still sparse: nine rows across four states.",
        },
    ]
    payload = {
        "schema_version": "krk_hard_negative_label_semantics_review.v1",
        "causal_status": "non_causal_semantics_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(TARGETS), str(ABLATION), str(EVIDENCE_REVIEW)],
        "summary": {
            "row_count": len(rows),
            "state_count": len(profiles),
            "capacity_positive_count": sum(1 for row in rows if _target_label(row) == "capacity_positive"),
            "capacity_negative_count": sum(1 for row in rows if _target_label(row) == "capacity_negative"),
            "capacity_negative_state_count": sum(1 for profile in profiles.values() if profile["capacity_negative"] > 0),
            "state_local_contrast_state_count": len(contrast_states),
            "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
            "source_channel_counts": dict(source_channels),
            "label_by_source_channel": {key: dict(counter) for key, counter in sorted(label_by_channel.items())},
            "best_ablation_negative_suppression": (ablation.get("best_result") or {}).get("negative_suppression"),
            "best_ablation_positive_recall": (ablation.get("best_result") or {}).get("positive_recall"),
        },
        "state_profiles": profiles,
        "semantics": semantics,
        "recommended_objective_split": {
            "capacity_recall_objective": "which validated providers should be present in candidate set",
            "capacity_risk_objective": "which forced-provider paths are risky under current h40 continuation",
            "ownership_selection_objective": "which provider should own normal runtime decision; not supplied by this dataset alone",
            "safe_preservation_objective": "validated safe owners must be preserved before any suppression can be reviewed",
        },
        "decision": {
            "status": "capacity_labels_not_direct_selector_targets",
            "recommended_next_step": "run_stronger_capacity_risk_feature_review_non_causal",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_review(payload)
    return payload


def validate_review(payload: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_candidate_generator_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if payload["summary"]["stage7_row_count"] != 0:
        raise ValueError("Stage 7 rows must remain excluded")
    if payload["decision"]["selector_training_allowed"] is not False:
        raise ValueError("selector training remains blocked")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Hard-Negative Label Semantics Review v1",
        "",
        "This review separates forced-provider capacity evidence from runtime ownership evidence.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Semantics", ""])
    for item in payload["semantics"]:
        lines.append(
            f"- `{item['label_channel']}` allowed=`{item['allowed_use']}` blocked=`{item['blocked_use']}`. "
            f"{item['reason']}"
        )
    lines.extend(["", "## Objective Split", ""])
    for key, value in payload["recommended_objective_split"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
