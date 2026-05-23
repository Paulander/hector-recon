#!/usr/bin/env python3
"""Write decision gate for KRK candidate proposal quality v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/strategy_arbitration/krk_candidate_proposal_quality_dataset_v1.json")
PROBE = Path("reports/strategy_arbitration/krk_candidate_proposal_quality_probe_v1.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_candidate_proposal_quality_decision_v1.json")
OUT_MD = Path("reports/strategy_arbitration/krk_candidate_proposal_quality_decision_v1.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_payload(
    dataset: dict[str, Any] | None = None,
    probe: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dataset = dataset or _load(DATASET)
    probe = probe or _load(PROBE)
    dataset_summary = dataset.get("summary") or {}
    probe_summary = probe.get("summary") or {}
    best = probe_summary.get("best_probe_metrics") or {}
    recall = float(best.get("positive_recall") or 0.0)
    negative_suppression = float(best.get("negative_suppression") or 0.0)
    ready = recall >= 0.7 and negative_suppression >= 0.7
    return {
        "schema_version": "krk_candidate_proposal_quality_decision.v1",
        "causal_status": "non_causal_decision_gate",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(DATASET), str(PROBE)],
        "evidence": {
            "dataset_row_count": dataset_summary.get("row_count"),
            "quality_probe_row_count": dataset_summary.get("quality_probe_row_count"),
            "stage7_challenge_row_count": dataset_summary.get("stage7_challenge_row_count"),
            "stage7_readiness_training_row_count": dataset_summary.get(
                "stage7_readiness_training_row_count"
            ),
            "best_probe": probe_summary.get("best_probe"),
            "best_positive_precision": best.get("positive_precision"),
            "best_positive_recall": recall,
            "best_negative_suppression": negative_suppression,
            "best_balanced_score": best.get("balanced_score"),
        },
        "decision": {
            "status": "candidate_proposal_quality_not_selector_ready"
            if not ready
            else "candidate_proposal_quality_review_ready",
            "selector_allowed": False,
            "guardrails_allowed": False,
            "runtime_changes_allowed": False,
            "more_blind_label_farming_allowed": False,
            "recommended_next_step": "design_broader_strategy_sequence_candidate_sources"
            if not ready
            else "selector_review_packet_design",
        },
        "rationale": [
            "observation-only candidate generation is safe and visible",
            "candidate proposal quality axes have some signal but do not jointly pass recall and negative-suppression thresholds",
            "more blind candidate-move capacity labels are inefficient because candidate coverage is broad and sparse",
            "PlanCapsule sequence and broader strategy candidates are still absent from runtime observation frames",
            "candidate generation remains separate from selection",
        ],
        "blocked_next_steps": [
            "runtime_selector",
            "score_changes",
            "provider_routing",
            "guardrail_campaign",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
        ],
    }


def write_markdown(payload: dict[str, Any]) -> None:
    evidence = payload["evidence"]
    lines = [
        "# KRK Candidate Proposal Quality Decision v1",
        "",
        "This decision gate closes the current observation-candidate quality slice.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Evidence",
        "",
        f"- dataset_row_count: {evidence['dataset_row_count']}",
        f"- quality_probe_row_count: {evidence['quality_probe_row_count']}",
        f"- stage7_challenge_row_count: {evidence['stage7_challenge_row_count']}",
        f"- best_probe: `{evidence['best_probe']}`",
        f"- best_positive_precision: `{float(evidence['best_positive_precision'] or 0.0):.3f}`",
        f"- best_positive_recall: `{float(evidence['best_positive_recall'] or 0.0):.3f}`",
        f"- best_negative_suppression: `{float(evidence['best_negative_suppression'] or 0.0):.3f}`",
        f"- best_balanced_score: `{float(evidence['best_balanced_score'] or 0.0):.3f}`",
        "",
        "## Rationale",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["rationale"])
    lines.extend(["", "## Blocked Next Steps", ""])
    lines.extend(f"- `{step}`" for step in payload["blocked_next_steps"])
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
