#!/usr/bin/env python3
"""Review why abstention labels still fail after count threshold is met."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROBE = Path("reports/krk_abstention_training_probe_v1.json")
DATASET = Path("reports/krk_abstention_training_dataset_v1.json")
OUT_JSON = Path("reports/krk_abstention_feature_gap_review_v0.json")
OUT_MD = Path("reports/krk_abstention_feature_gap_review_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    probe = _load_json(PROBE)
    dataset = _load_json(DATASET)
    if probe.get("causal_status") != "non_causal_offline_probe":
        raise ValueError("probe must remain non-causal")
    if dataset.get("causal_status") != "non_causal_abstention_dataset":
        raise ValueError("dataset must remain non-causal")
    best = probe.get("best_result") or {}
    review = {
        "schema_version": "krk_abstention_feature_gap_review.v0",
        "causal_status": "non_causal_architecture_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(DATASET), str(PROBE)],
        "accepted_result": {
            "row_count": (dataset.get("summary") or {}).get("row_count"),
            "unsafe_owner_count": ((dataset.get("summary") or {}).get("label_counts") or {}).get("unsafe_owner"),
            "best_objective": best.get("objective"),
            "best_negative_suppression": best.get("negative_suppression"),
            "best_safe_preservation": best.get("safe_preservation"),
            "runtime_ready": False,
        },
        "diagnosis": [
            "Raw provider family/provenance is not enough to distinguish unsafe owners once selected-playout labels are included.",
            "The abstention gate now has enough examples by count, but it lacks state-local context features that explain why a normally useful provider is unsafe in a specific position.",
            "The next evidence object should join abstention labels to ControlPlaneEvidenceFrame terminal-space context, not collect more Stage7 repair traces.",
        ],
        "required_feature_groups": [
            "terminal_space_context: edge distance, box relevance, fence/cut state, rook safety, king support, mobility",
            "proposal_context: provider rank, normalized score, raw score gap, selected-vs-forced semantics",
            "monitor_context: local_provider_competition_failed, repair_needed_monitor, post_plan_stagnation where available",
            "label_semantics: selected_playout_success versus forced_provider_conversion separated at evaluation time",
        ],
        "recommended_next_step": {
            "status": "join_abstention_labels_with_control_plane_context",
            "artifacts": [
                "reports/krk_abstention_context_feature_dataset_v0.json",
                "reports/krk_abstention_context_feature_dataset_v0.md",
                "reports/krk_abstention_context_feature_probe_v0.json",
                "reports/krk_abstention_context_feature_probe_v0.md",
            ],
            "implementation_allowed": "non_causal_replay_free_only",
        },
        "blocked_next_steps": [
            "runtime_selector",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
            "m3_m4_arbitration_update",
        ],
    }
    validate(review)
    return review


def validate(review: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if review.get(key) is not False:
            raise ValueError(f"{key} must be false")


def render_markdown(review: dict[str, Any]) -> str:
    lines = [
        "# KRK Abstention Feature Gap Review v0",
        "",
        "This review explains why the abstention-first selector is still not runtime-ready after the v1 label-count threshold was met.",
        "",
        "## Accepted Result",
        "",
    ]
    for key, value in review["accepted_result"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Diagnosis", ""])
    for item in review["diagnosis"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Required Feature Groups", ""])
    for item in review["required_feature_groups"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Recommended Next Step",
            "",
            f"- Status: `{review['recommended_next_step']['status']}`",
            f"- Implementation allowed: `{review['recommended_next_step']['implementation_allowed']}`",
            f"- Artifacts: `{review['recommended_next_step']['artifacts']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    review = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(review), encoding="utf-8")
    print(json.dumps(review["recommended_next_step"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
