#!/usr/bin/env python3
"""Audit non-causal KRK candidate-generator coverage using protected capacity frames."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CAPACITY_FRAMES = Path("reports/krk_protected_provider_coverage_frames_v0.json")
SEMANTICS_REVIEW = Path("reports/krk_protected_provider_capacity_frame_training_semantics_review_v0.json")
OUT_JSON = Path("reports/krk_candidate_generator_coverage_audit_v0.json")
OUT_MD = Path("reports/krk_candidate_generator_coverage_audit_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def build_audit() -> dict[str, Any]:
    frames = _load(CAPACITY_FRAMES)
    review = _load(SEMANTICS_REVIEW)
    if frames.get("causal_status") != "non_causal_capacity_frame_dataset":
        raise ValueError("capacity frames must remain non-causal")
    if review.get("causal_status") != "non_causal_semantics_review":
        raise ValueError("capacity-frame semantics review must remain non-causal")
    rows = list(frames.get("rows") or [])
    positives = [row for row in rows if row.get("capacity_label") == "positive_capacity"]
    negatives = [row for row in rows if row.get("capacity_label") == "negative_capacity"]
    recalled_positive = [row for row in positives if row.get("has_runtime_proposal_frame")]
    recalled_negative = [row for row in negatives if row.get("has_runtime_proposal_frame")]
    missing_positive = [row for row in positives if not row.get("has_runtime_proposal_frame")]

    by_stage_family: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        by_stage_family[str(row.get("source_stage"))][str(row.get("provider_family"))] += 1

    status = "candidate_generator_coverage_inconclusive"
    recommendation = "collect_more_candidate_generator_evidence"
    if positives and not recalled_positive:
        status = "candidate_generator_recall_gap_confirmed"
        recommendation = "design_non_causal_validated_provider_candidate_set_audit"
    elif positives and recalled_positive:
        status = "candidate_generator_positive_recall_present"
        recommendation = "review_candidate_generator_precision_before_runtime_work"

    payload = {
        "schema_version": "krk_candidate_generator_coverage_audit.v0",
        "causal_status": "non_causal_candidate_generator_audit",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(CAPACITY_FRAMES), str(SEMANTICS_REVIEW)],
        "summary": {
            "capacity_frame_count": len(rows),
            "positive_capacity_count": len(positives),
            "negative_capacity_count": len(negatives),
            "runtime_proposal_positive_recall_count": len(recalled_positive),
            "runtime_proposal_negative_recall_count": len(recalled_negative),
            "runtime_proposal_positive_recall_rate": _rate(len(recalled_positive), len(positives)),
            "runtime_proposal_negative_recall_rate": _rate(len(recalled_negative), len(negatives)),
            "missing_positive_capacity_count": len(missing_positive),
            "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
            "stage_family_counts": {stage: dict(counter) for stage, counter in by_stage_family.items()},
            "missing_positive_provider_family_counts": dict(Counter(str(row.get("provider_family")) for row in missing_positive)),
            "missing_positive_source_stage_counts": dict(Counter(str(row.get("source_stage")) for row in missing_positive)),
        },
        "interpretation": {
            "primary_finding": (
                "The current proposal-frame export has zero recall for protected providers that converted under forced-provider capacity labels."
            ),
            "architecture_implication": (
                "Selector work is premature unless the candidate/proposal set represents validated providers that can convert. "
                "This is a candidate-generation coverage gap, not a reason to patch Stage 7."
            ),
            "still_non_causal": True,
        },
        "missing_positive_examples": [
            {
                "state_id": row.get("state_id"),
                "source_stage": row.get("source_stage"),
                "provider_id": row.get("provider_id"),
                "provider_family": row.get("provider_family"),
                "forced_first_move": row.get("forced_first_move"),
                "forced_plies": row.get("forced_plies"),
                "existing_frame_providers": row.get("existing_frame_providers"),
            }
            for row in missing_positive
        ],
        "decision": {
            "status": status,
            "recommended_next_step": recommendation,
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_audit(payload)
    return payload


def validate_audit(payload: dict[str, Any]) -> None:
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
        raise ValueError("selector training must remain blocked")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Candidate Generator Coverage Audit v0",
        "",
        "This is a non-causal audit of whether current proposal frames include protected providers with forced-provider conversion evidence.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Interpretation", ""])
    for key, value in payload["interpretation"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Missing Positive Examples", ""])
    for item in payload["missing_positive_examples"]:
        lines.append(
            f"- state=`{item['state_id']}` stage=`{item['source_stage']}` provider=`{item['provider_id']}` "
            f"forced_move=`{item['forced_first_move']}` plies=`{item['forced_plies']}` "
            f"existing_frame_providers=`{item['existing_frame_providers']}`"
        )
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_audit()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
