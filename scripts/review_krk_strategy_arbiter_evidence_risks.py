#!/usr/bin/env python3
"""Review KRK strategy-arbiter evidence risks before any sandbox work.

This is replay-free and non-causal. It separates provider-label semantics and
classifies max-only frames so strategy-arbitration evidence is not overstated.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


FILTERED_FRAMES = Path("reports/krk_control_plane_filtered_frames_v0.json")
BASELINE = Path("reports/krk_control_plane_strategy_arbitration_baseline_v1.json")
DESIGN = Path("reports/krk_strategy_arbiter_sandbox_design_v0.json")


def _load_json(root: Path, relative_path: Path) -> dict[str, Any]:
    payload = json.loads((root / relative_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {relative_path}")
    return payload


def _result(label: dict[str, Any]) -> str:
    value = label.get("result") or label.get("playout_result")
    return str(value) if value in {"mate", "max_plies", "draw", "stagnation"} else "unknown"


def _label_semantics(label: dict[str, Any]) -> str:
    source = str(label.get("source") or "")
    if source == "forced_provider_result":
        return "forced_provider_outcome"
    if "playout_result" in label:
        if label.get("selected") is True:
            return "selected_provider_playout"
        if label.get("selected") is False:
            return "same_move_unselected_provider_playout"
        return "playout_without_selection_flag"
    if "result" in label:
        return "result_without_source"
    return "unknown"


def _benchmark_frames(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        frame
        for frame in payload.get("frames") or []
        if "strategy_arbitration_benchmark" in (frame.get("filter_metadata") or {}).get("benchmark_roles", [])
    ]


def _frame_label_summary(frame: dict[str, Any]) -> dict[str, Any]:
    results: Counter[str] = Counter()
    semantics: Counter[str] = Counter()
    providers_by_result: dict[str, list[str]] = defaultdict(list)
    for proposal in frame.get("strategy_proposal_frames") or []:
        label = proposal.get("known_outcome_label") or {}
        if not isinstance(label, dict):
            label = {}
        result = _result(label)
        semantic = _label_semantics(label)
        results[result] += 1
        semantics[semantic] += 1
        providers_by_result[result].append(str(proposal.get("provider_id") or "unknown"))
    return {
        "result_counts": dict(results),
        "semantic_counts": dict(semantics),
        "providers_by_result": {key: sorted(set(value)) for key, value in providers_by_result.items()},
        "has_provider_mate": results["mate"] > 0,
        "max_only": bool(results) and results["mate"] == 0 and results["max_plies"] > 0,
    }


def _max_only_classification(frame: dict[str, Any], summary: dict[str, Any]) -> str:
    semantics = set(summary["semantic_counts"])
    stage = str(frame.get("source_stage") or "")
    if "forced_provider_outcome" in semantics:
        return "forced_existing_provider_capacity_or_horizon_gap"
    if stage in {"stage4", "stage5", "stage6"}:
        return "selected_playout_guardrail_or_horizon_caveat"
    return "selected_playout_max_only_unclassified"


def build_review(repo_root: Path) -> dict[str, Any]:
    filtered = _load_json(repo_root, FILTERED_FRAMES)
    baseline = _load_json(repo_root, BASELINE)
    design = _load_json(repo_root, DESIGN)
    for name, payload, expected in (
        ("filtered", filtered, "non_causal_filtered_frame_export"),
        ("baseline", baseline, "non_causal_probe"),
        ("design", design, "non_causal_design"),
    ):
        if payload.get("causal_status") != expected:
            raise ValueError(f"{name} artifact must remain {expected}")

    frames = _benchmark_frames(filtered)
    semantic_counts: Counter[str] = Counter()
    semantic_result_counts: Counter[str] = Counter()
    semantic_stage_counts: Counter[str] = Counter()
    max_only_frames = []
    provider_mate_frames = []
    frame_records = []
    for frame in frames:
        summary = _frame_label_summary(frame)
        for semantic, count in summary["semantic_counts"].items():
            semantic_counts[semantic] += count
            semantic_stage_counts[f"{frame.get('source_stage')}:{semantic}"] += count
        for proposal in frame.get("strategy_proposal_frames") or []:
            label = proposal.get("known_outcome_label") or {}
            if not isinstance(label, dict):
                label = {}
            semantic_result_counts[f"{_label_semantics(label)}:{_result(label)}"] += 1
        record = {
            "frame_id": frame.get("frame_id"),
            "state_id": frame.get("state_id"),
            "source_stage": frame.get("source_stage"),
            "active_landmark_label": frame.get("active_landmark_label"),
            "outcome": frame.get("outcome"),
            **summary,
        }
        if summary["max_only"]:
            record["max_only_classification"] = _max_only_classification(frame, summary)
            max_only_frames.append(record)
        if summary["has_provider_mate"]:
            provider_mate_frames.append(record)
        frame_records.append(record)

    forced_positive_count = sum(
        1
        for record in provider_mate_frames
        if "forced_provider_outcome" in set(record["semantic_counts"])
    )
    selected_positive_count = sum(
        1
        for record in provider_mate_frames
        if "selected_provider_playout" in set(record["semantic_counts"])
    )
    same_move_positive_count = sum(
        1
        for record in provider_mate_frames
        if "same_move_unselected_provider_playout" in set(record["semantic_counts"])
    )
    max_class_counts = Counter(str(record["max_only_classification"]) for record in max_only_frames)
    risk_status = (
        "runtime_sandbox_blocked_pending_semantics_review"
        if forced_positive_count and (selected_positive_count or same_move_positive_count)
        else "label_semantics_sufficient_for_design_review"
    )
    review = {
        "schema_version": "krk_strategy_arbiter_evidence_risk_review.v0",
        "causal_status": "non_causal_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(FILTERED_FRAMES), str(BASELINE), str(DESIGN)],
        "summary": {
            "benchmark_frame_count": len(frames),
            "provider_mate_frame_count": len(provider_mate_frames),
            "max_only_frame_count": len(max_only_frames),
            "label_semantic_counts": dict(semantic_counts),
            "label_semantic_result_counts": dict(semantic_result_counts),
            "label_semantic_stage_counts": dict(semantic_stage_counts),
            "provider_mate_frames_by_semantic": {
                "forced_provider_outcome": forced_positive_count,
                "selected_provider_playout": selected_positive_count,
                "same_move_unselected_provider_playout": same_move_positive_count,
            },
            "max_only_classification_counts": dict(max_class_counts),
        },
        "max_only_frames": max_only_frames,
        "provider_mate_frame_examples": provider_mate_frames[:12],
        "decision": {
            "status": risk_status,
            "runtime_sandbox_allowed": False,
            "interpretation": (
                "Provider labels are useful for offline design, but selected-playout, "
                "same-move unselected-provider, and forced-provider semantics are mixed. "
                "A runtime sandbox should not be implemented until the arbiter evaluation "
                "separates those semantics."
            )
            if risk_status == "runtime_sandbox_blocked_pending_semantics_review"
            else "Label semantics are sufficiently uniform for a design review.",
            "recommended_next_step": "stratified_non_causal_arbiter_evaluation_v2",
        },
        "blocked_next_steps": [
            "runtime_arbiter",
            "runtime_internal_terminal",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }
    validate_review(review)
    return review


def validate_review(review: dict[str, Any]) -> None:
    if review.get("causal_status") != "non_causal_review":
        raise ValueError("review must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_arbiter_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if review.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if review["decision"]["runtime_sandbox_allowed"]:
        raise ValueError("risk review must not authorize runtime sandboxing")


def render_markdown(review: dict[str, Any]) -> str:
    summary = review["summary"]
    decision = review["decision"]
    lines = [
        "# KRK Strategy Arbiter Evidence Risk Review v0",
        "",
        "This is a replay-free, non-causal review of the two pre-sandbox risks: "
        "mixed provider-label semantics and max-only frame classification.",
        "",
        "## Summary",
        "",
    ]
    for key in (
        "benchmark_frame_count",
        "provider_mate_frame_count",
        "max_only_frame_count",
        "label_semantic_counts",
        "provider_mate_frames_by_semantic",
        "max_only_classification_counts",
    ):
        lines.append(f"- `{key}`: `{summary.get(key)}`")
    lines.extend(["", "## Max-Only Frames", ""])
    for record in review["max_only_frames"][:12]:
        lines.append(
            f"- `{record['frame_id']}` stage=`{record['source_stage']}` "
            f"class=`{record['max_only_classification']}` semantics=`{record['semantic_counts']}`"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Status: `{decision['status']}`",
            f"- Runtime sandbox allowed: `{decision['runtime_sandbox_allowed']}`",
            f"- Interpretation: {decision['interpretation']}",
            f"- Recommended next step: `{decision['recommended_next_step']}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(review: dict[str, Any], report_root: Path) -> None:
    report_root.mkdir(parents=True, exist_ok=True)
    (report_root / "krk_strategy_arbiter_evidence_risk_review_v0.json").write_text(
        json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (report_root / "krk_strategy_arbiter_evidence_risk_review_v0.md").write_text(
        render_markdown(review), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--report-root", type=Path, default=Path("reports"))
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    report_root = args.report_root
    if not report_root.is_absolute():
        report_root = repo_root / report_root
    review = build_review(repo_root)
    write_outputs(review, report_root)
    print(json.dumps(review["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
