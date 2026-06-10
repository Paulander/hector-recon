#!/usr/bin/env python3
"""Probe non-causal KRK candidate proposal quality axes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/strategy_arbitration/krk_candidate_proposal_quality_dataset_v1.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_candidate_proposal_quality_probe_v1.json")
OUT_MD = Path("reports/strategy_arbitration/krk_candidate_proposal_quality_probe_v1.md")


def _load(path: Path = DATASET) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _known_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in payload.get("rows") or []:
        if not isinstance(row, dict):
            continue
        if row.get("stage7_challenge_row"):
            continue
        if row.get("capacity_evidence_kind") in {"positive_capacity", "negative_capacity"}:
            rows.append(row)
    return rows


def _metrics(rows: list[dict[str, Any]], predicate: Callable[[dict[str, Any]], bool]) -> dict[str, Any]:
    positives = [row for row in rows if row.get("capacity_evidence_kind") == "positive_capacity"]
    negatives = [row for row in rows if row.get("capacity_evidence_kind") == "negative_capacity"]
    predicted_positive = [row for row in rows if predicate(row)]
    tp = sum(1 for row in predicted_positive if row.get("capacity_evidence_kind") == "positive_capacity")
    fp = sum(1 for row in predicted_positive if row.get("capacity_evidence_kind") == "negative_capacity")
    fn = len(positives) - tp
    tn = len(negatives) - fp
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / len(positives) if positives else 0.0
    negative_suppression = tn / len(negatives) if negatives else 0.0
    return {
        "known_row_count": len(rows),
        "positive_count": len(positives),
        "negative_count": len(negatives),
        "predicted_positive_count": len(predicted_positive),
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "positive_precision": precision,
        "positive_recall": recall,
        "negative_suppression": negative_suppression,
        "balanced_score": (recall + negative_suppression) / 2,
    }


def _thresholds(rows: list[dict[str, Any]]) -> dict[str, int]:
    densities = sorted(int(row.get("visible_term_density") or 0) for row in rows)
    if not densities:
        return {"median_density": 0, "upper_quartile_density": 0}
    return {
        "median_density": densities[len(densities) // 2],
        "upper_quartile_density": densities[(len(densities) * 3) // 4],
    }


def build_payload(dataset: dict[str, Any] | None = None) -> dict[str, Any]:
    dataset = dataset or _load()
    rows = _known_rows(dataset)
    thresholds = _thresholds(rows)
    probes = {
        "candidate_move_frame_source": lambda row: row.get("candidate_source") == "candidate_move_frame",
        "validated_provider_pack_source": lambda row: row.get("candidate_source")
        == "validated_provider_pack",
        "has_post_or_safety_terms": lambda row: int(row.get("post_move_term_count") or 0)
        + int(row.get("safety_term_count") or 0)
        > 0,
        "visible_density_at_or_above_median": lambda row: int(row.get("visible_term_density") or 0)
        >= thresholds["median_density"],
        "visible_density_at_or_above_upper_quartile": lambda row: int(
            row.get("visible_term_density") or 0
        )
        >= thresholds["upper_quartile_density"],
        "distinct_from_selected_move": lambda row: row.get("selected_move_relation")
        == "distinct_from_selected",
        "same_selected_provider": lambda row: row.get("provider_relation")
        == "same_as_selected_provider",
        "simple_quality_axis": lambda row: (
            int(row.get("post_move_term_count") or 0) > 0
            or int(row.get("safety_term_count") or 0) > 0
            or row.get("candidate_source") == "validated_provider_pack"
        ),
    }
    results = {name: _metrics(rows, predicate) for name, predicate in probes.items()}
    best_name, best = max(
        results.items(),
        key=lambda item: (item[1]["balanced_score"], item[1]["positive_recall"]),
        default=("none", _metrics([], lambda _row: False)),
    )
    stage7_rows = sum(1 for row in dataset.get("rows") or [] if row.get("stage7_challenge_row"))
    status = (
        "proposal_quality_axes_promising_but_selector_blocked"
        if best["positive_recall"] >= 0.7 and best["negative_suppression"] >= 0.7
        else "proposal_quality_axes_insufficient_for_selector_review"
    )
    return {
        "schema_version": "krk_candidate_proposal_quality_probe.v1",
        "causal_status": "non_causal_quality_axis_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifact": str(DATASET),
        "summary": {
            "known_capacity_row_count": len(rows),
            "stage7_challenge_row_count": stage7_rows,
            "stage7_readiness_training_row_count": 0,
            "thresholds": thresholds,
            "best_probe": best_name,
            "best_probe_metrics": best,
        },
        "probe_results": results,
        "interpretation": {
            "quality_axes_have_some_signal": best["balanced_score"] > 0.5,
            "quality_axes_ready_for_selector_review": status
            == "proposal_quality_axes_promising_but_selector_blocked",
            "capacity_labels_are_not_ownership_labels": True,
            "stage7_excluded_from_probe_readiness": True,
        },
        "decision": {
            "status": status,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": "candidate_proposal_quality_decision_gate",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Candidate Proposal Quality Probe v1",
        "",
        "This probe evaluates simple non-causal quality axes over known protected capacity rows. It is not selector training.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
        f"- known_capacity_row_count: {summary['known_capacity_row_count']}",
        f"- stage7_challenge_row_count: {summary['stage7_challenge_row_count']}",
        f"- best_probe: `{summary['best_probe']}`",
        f"- best_probe_metrics: `{summary['best_probe_metrics']}`",
        "",
        "## Probe Results",
        "",
    ]
    for name, metrics in payload["probe_results"].items():
        lines.append(
            f"- `{name}`: precision=`{metrics['positive_precision']:.3f}` "
            f"recall=`{metrics['positive_recall']:.3f}` "
            f"negative_suppression=`{metrics['negative_suppression']:.3f}` "
            f"balanced=`{metrics['balanced_score']:.3f}`"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "These probe results do not authorize a selector, scoring changes, guardrails, Stage 7 promotion, or Stage 8 training.",
        ]
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
