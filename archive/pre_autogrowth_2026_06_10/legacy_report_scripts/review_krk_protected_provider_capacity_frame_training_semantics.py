#!/usr/bin/env python3
"""Review whether protected capacity frames are safe selector-training labels."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COVERAGE_FRAMES = Path("reports/krk_protected_provider_coverage_frames_v0.json")
OUT_JSON = Path("reports/krk_protected_provider_capacity_frame_training_semantics_review_v0.json")
OUT_MD = Path("reports/krk_protected_provider_capacity_frame_training_semantics_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    frames = _load(COVERAGE_FRAMES)
    if frames.get("causal_status") != "non_causal_capacity_frame_dataset":
        raise ValueError("coverage frames must remain non-causal")
    rows = list(frames.get("rows") or [])
    positive = [row for row in rows if row.get("capacity_label") == "positive_capacity"]
    negative = [row for row in rows if row.get("capacity_label") == "negative_capacity"]
    payload = {
        "schema_version": "krk_protected_provider_capacity_frame_training_semantics_review.v0",
        "causal_status": "non_causal_semantics_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(COVERAGE_FRAMES)],
        "summary": {
            "row_count": len(rows),
            "positive_capacity_count": len(positive),
            "negative_capacity_count": len(negative),
            "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
            "training_row_count": sum(1 for row in rows if row.get("usable_for_training")),
            "runtime_proposal_row_count": sum(1 for row in rows if row.get("has_runtime_proposal_frame")),
            "provider_family_counts": dict(Counter(str(row.get("provider_family")) for row in rows)),
            "source_stage_counts": dict(Counter(str(row.get("source_stage")) for row in rows)),
        },
        "semantic_findings": [
            {
                "finding": "forced_provider_capacity_is_not_direct_selector_supervision",
                "evidence": "Rows were generated from forced-provider playouts for providers absent from runtime proposal frames.",
                "implication": "Positive capacity labels should not become selector positives without a separate proposal-generation or ownership review.",
            },
            {
                "finding": "candidate_generation_gap_precedes_selector_gap",
                "evidence": f"{len(positive)} converting protected labels were missing from proposal frames.",
                "implication": "The architecture needs non-causal proposal/candidate coverage evidence before selector training can be evaluated fairly.",
            },
            {
                "finding": "negative_capacity_labels_are_useful_hard_negatives_but_not_runtime_vetoes",
                "evidence": f"{len(negative)} protected forced-provider labels still max_plies at h40.",
                "implication": "They can test capacity limits, but must not suppress providers at runtime.",
            },
        ],
        "allowed_uses": [
            "proposal_coverage_audit",
            "candidate_generator_evaluation",
            "capacity_map_diagnostic",
            "state_provider_contrast_review",
        ],
        "blocked_uses": [
            "direct_selector_training_positive",
            "runtime_provider_boost",
            "runtime_provider_penalty",
            "runtime_candidate_generation",
            "topology_edge_creation",
            "stage7_repair_or_promotion",
            "stage8_training",
        ],
        "requirements_before_training_use": [
            "define a separate candidate-generator target or runtime-proposal target",
            "separate forced-provider capacity labels from selected-playout and runtime-proposal labels",
            "validate false positives with protected guardrails",
            "include negative-capacity labels and same-state alternatives",
            "keep Stage 7 held out unless explicitly reclassified",
            "run a non-causal review before any sandbox",
        ],
        "decision": {
            "status": "capacity_frames_diagnostic_not_selector_training_ready",
            "recommended_next_step": "design_non_causal_candidate_generator_coverage_audit",
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
    if payload["summary"]["training_row_count"] != 0:
        raise ValueError("capacity frame rows must not be training rows")
    if payload["decision"]["selector_training_allowed"] is not False:
        raise ValueError("selector training must remain blocked")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Protected Provider Capacity Frame Training Semantics Review v0",
        "",
        "This review decides whether protected capacity frames are safe to use as selector-training rows. They are not.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Findings", ""])
    for item in payload["semantic_findings"]:
        lines.append(f"- `{item['finding']}`: {item['implication']}")
    lines.extend(["", "## Allowed Uses", ""])
    for item in payload["allowed_uses"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Blocked Uses", ""])
    for item in payload["blocked_uses"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Requirements Before Training Use", ""])
    for item in payload["requirements_before_training_use"]:
        lines.append(f"- `{item}`")
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
