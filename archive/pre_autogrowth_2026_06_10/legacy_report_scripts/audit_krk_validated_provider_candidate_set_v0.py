#!/usr/bin/env python3
"""Audit a non-causal validated-provider candidate-set expansion."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_COVERAGE = Path("reports/krk_candidate_generator_coverage_audit_v0.json")
CAPACITY_FRAMES = Path("reports/krk_protected_provider_coverage_frames_v0.json")
OUT_JSON = Path("reports/krk_validated_provider_candidate_set_audit_v0.json")
OUT_MD = Path("reports/krk_validated_provider_candidate_set_audit_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def build_audit() -> dict[str, Any]:
    coverage = _load(CANDIDATE_COVERAGE)
    frames = _load(CAPACITY_FRAMES)
    if coverage.get("causal_status") != "non_causal_candidate_generator_audit":
        raise ValueError("candidate-generator coverage audit must remain non-causal")
    if frames.get("causal_status") != "non_causal_capacity_frame_dataset":
        raise ValueError("capacity frames must remain non-causal")
    rows = list(frames.get("rows") or [])
    positives = [row for row in rows if row.get("capacity_label") == "positive_capacity"]
    negatives = [row for row in rows if row.get("capacity_label") == "negative_capacity"]
    by_state: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_state[str(row.get("state_id"))].append(row)

    state_summaries = []
    for state_id, state_rows in sorted(by_state.items()):
        existing = sorted({provider for row in state_rows for provider in row.get("existing_frame_providers", [])})
        added = sorted({str(row.get("provider_id")) for row in state_rows})
        state_summaries.append({
            "state_id": state_id,
            "source_stage": state_rows[0].get("source_stage"),
            "existing_frame_providers": existing,
            "added_validated_providers": added,
            "added_positive_capacity_count": sum(1 for row in state_rows if row.get("capacity_label") == "positive_capacity"),
            "added_negative_capacity_count": sum(1 for row in state_rows if row.get("capacity_label") == "negative_capacity"),
        })

    payload = {
        "schema_version": "krk_validated_provider_candidate_set_audit.v0",
        "causal_status": "non_causal_candidate_set_audit",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(CANDIDATE_COVERAGE), str(CAPACITY_FRAMES)],
        "candidate_set_policy": {
            "name": "validated_provider_pack_candidates_for_protected_contexts",
            "description": (
                "Offline audit policy that adds validated/frozen provider candidates for protected states "
                "when current proposal frames omit them."
            ),
            "causal_status": "non_causal_policy_audit_only",
            "runtime_default": "not_implemented",
        },
        "summary": {
            "state_count": len(by_state),
            "added_candidate_count": len(rows),
            "added_positive_capacity_count": len(positives),
            "added_negative_capacity_count": len(negatives),
            "positive_capacity_recall_if_included": _rate(len(positives), len(positives)),
            "negative_capacity_inclusion_rate": _rate(len(negatives), len(rows)),
            "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
            "source_stage_counts": dict(Counter(str(row.get("source_stage")) for row in rows)),
            "provider_family_counts": dict(Counter(str(row.get("provider_family")) for row in rows)),
        },
        "state_summaries": state_summaries,
        "interpretation": {
            "benefit": "A validated-provider candidate-set expansion would recover the currently missing protected positive-capacity providers.",
            "risk": "The same expansion also introduces negative-capacity providers; candidate generation cannot replace selection/scoring.",
            "architecture_split": "Treat candidate generation and strategy selection as separate non-causal evidence tracks before runtime work.",
        },
        "decision": {
            "status": "validated_provider_candidate_set_recall_promising_requires_selector_semantics",
            "recommended_next_step": "design_two_stage_candidate_generation_and_selection_review",
            "runtime_work_allowed": False,
            "candidate_generator_runtime_allowed": False,
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
    if payload["decision"]["candidate_generator_runtime_allowed"] is not False:
        raise ValueError("runtime candidate generation remains blocked")
    if payload["decision"]["selector_training_allowed"] is not False:
        raise ValueError("selector training remains blocked")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Validated Provider Candidate Set Audit v0",
        "",
        "This is a non-causal audit of a possible validated-provider candidate-set expansion. It does not implement runtime candidate generation.",
        "",
        "## Policy",
        "",
        f"- Name: `{payload['candidate_set_policy']['name']}`",
        f"- Runtime default: `{payload['candidate_set_policy']['runtime_default']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Interpretation", ""])
    for key, value in payload["interpretation"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## State Summaries", ""])
    for item in payload["state_summaries"]:
        lines.append(
            f"- state=`{item['state_id']}` stage=`{item['source_stage']}` "
            f"added=`{item['added_validated_providers']}` "
            f"positive=`{item['added_positive_capacity_count']}` negative=`{item['added_negative_capacity_count']}`"
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
