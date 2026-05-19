#!/usr/bin/env python3
"""Run stratified non-causal KRK strategy-arbiter evaluation v2.

This probe separates selected-provider playout labels, forced-provider labels,
and same-move unselected-provider labels before evaluating simple selectors.
It does not implement a runtime arbiter or change gameplay behavior.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable


FILTERED_FRAMES = Path("reports/krk_control_plane_filtered_frames_v0.json")
RISK_REVIEW = Path("reports/krk_strategy_arbiter_evidence_risk_review_v0.json")
BASELINE = Path("reports/krk_control_plane_strategy_arbitration_baseline_v1.json")

Selector = Callable[[dict[str, Any], list[dict[str, Any]]], dict[str, Any] | None]


def _load_json(root: Path, relative_path: Path) -> dict[str, Any]:
    payload = json.loads((root / relative_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {relative_path}")
    return payload


def _result(proposal: dict[str, Any]) -> str:
    label = proposal.get("known_outcome_label") or {}
    if not isinstance(label, dict):
        return "unknown"
    value = label.get("result") or label.get("playout_result")
    return str(value) if value in {"mate", "max_plies", "draw", "stagnation"} else "unknown"


def _semantics(proposal: dict[str, Any]) -> str:
    label = proposal.get("known_outcome_label") or {}
    if not isinstance(label, dict):
        return "unknown"
    if label.get("source") == "forced_provider_result":
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


def _score(value: Any, fallback: float = float("-inf")) -> float:
    return float(value) if isinstance(value, (int, float)) else fallback


def _benchmark_frames(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        frame
        for frame in payload.get("frames") or []
        if "strategy_arbitration_benchmark" in (frame.get("filter_metadata") or {}).get("benchmark_roles", [])
    ]


def _top_by_key(proposals: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
    candidates = [proposal for proposal in proposals if isinstance(proposal.get(key), (int, float))]
    if not candidates:
        return None
    return max(candidates, key=lambda proposal: _score(proposal.get(key)))


def _raw_selector(frame: dict[str, Any], proposals: list[dict[str, Any]]) -> dict[str, Any] | None:
    return _top_by_key(proposals, "raw_score")


def _normalized_selector(frame: dict[str, Any], proposals: list[dict[str, Any]]) -> dict[str, Any] | None:
    return _top_by_key(proposals, "normalized_score")


def _rank_selector(frame: dict[str, Any], proposals: list[dict[str, Any]]) -> dict[str, Any] | None:
    ranked = [proposal for proposal in proposals if isinstance(proposal.get("provider_local_rank"), int)]
    if not ranked:
        return None
    return min(
        ranked,
        key=lambda proposal: (
            int(proposal.get("provider_local_rank") or 999999),
            -_score(proposal.get("normalized_score"), 0.0),
            -_score(proposal.get("raw_score"), 0.0),
        ),
    )


def _proposal_for_provider(proposals: list[dict[str, Any]], provider_id: str) -> dict[str, Any] | None:
    matches = [proposal for proposal in proposals if proposal.get("provider_id") == provider_id]
    if not matches:
        return None
    return max(
        matches,
        key=lambda proposal: (
            _score(proposal.get("normalized_score"), 0.0),
            _score(proposal.get("raw_score"), 0.0),
        ),
    )


def _stage_prior_selector(frame: dict[str, Any], proposals: list[dict[str, Any]]) -> dict[str, Any] | None:
    stage = str(frame.get("source_stage") or "")
    active = str(frame.get("active_landmark_label") or "")
    providers_by_stage = {
        "stage4": ["krk.stage0_basin", "krk.edge_trap_wrong_tempo"],
        "stage5": ["krk.edge_trap_close", "krk.fence_established", "krk.stage0_basin"],
        "stage6": ["krk.drive_to_edge", "krk.fence_established", "krk.stage0_basin"],
        "stage7": ["krk.box_shrink", "krk.post_box_shrink_continuation", "krk.drive_to_edge", "krk.fence_established"],
    }
    if active == "box_shrink":
        provider_order = ["krk.post_box_shrink_continuation", "krk.box_shrink", "krk.drive_to_edge", "krk.fence_established"]
    else:
        provider_order = providers_by_stage.get(stage, [])
    for provider_id in provider_order:
        proposal = _proposal_for_provider(proposals, provider_id)
        if proposal is not None:
            return proposal
    return _normalized_selector(frame, proposals)


SELECTORS: dict[str, Selector] = {
    "raw_global_score": _raw_selector,
    "normalized_score": _normalized_selector,
    "provider_local_rank": _rank_selector,
    "stage_prior_heuristic": _stage_prior_selector,
}


def _eligible_proposals(frame: dict[str, Any], semantic: str) -> list[dict[str, Any]]:
    return [
        proposal
        for proposal in frame.get("strategy_proposal_frames") or []
        if _semantics(proposal) == semantic
    ]


def _evaluate_stratum(
    frames: list[dict[str, Any]],
    *,
    semantic: str,
    selector_name: str,
    selector: Selector,
) -> dict[str, Any]:
    selected_count = 0
    selected_labels: Counter[str] = Counter()
    positive_available = 0
    positive_hit = 0
    no_selection = 0
    stage_counts: Counter[str] = Counter()
    misses = []
    for frame in frames:
        proposals = _eligible_proposals(frame, semantic)
        if not proposals:
            continue
        stage_counts[str(frame.get("source_stage") or "unknown")] += 1
        has_mate = any(_result(proposal) == "mate" for proposal in proposals)
        if has_mate:
            positive_available += 1
        selected = selector(frame, proposals)
        if selected is None:
            no_selection += 1
            continue
        selected_count += 1
        selected_result = _result(selected)
        selected_labels[selected_result] += 1
        if has_mate and selected_result == "mate":
            positive_hit += 1
        elif has_mate and len(misses) < 8:
            misses.append(
                {
                    "frame_id": frame.get("frame_id"),
                    "source_stage": frame.get("source_stage"),
                    "selector": selector_name,
                    "selected_provider": selected.get("provider_id"),
                    "selected_result": selected_result,
                    "mate_providers": sorted(
                        {
                            str(proposal.get("provider_id"))
                            for proposal in proposals
                            if _result(proposal) == "mate"
                        }
                    ),
                }
            )
    return {
        "label_semantics": semantic,
        "selector": selector_name,
        "eligible_frame_count": sum(1 for frame in frames if _eligible_proposals(frame, semantic)),
        "eligible_stage_counts": dict(stage_counts),
        "selected_count": selected_count,
        "no_selection_count": no_selection,
        "selected_label_counts": dict(selected_labels),
        "positive_available_frame_count": positive_available,
        "positive_hit_count": positive_hit,
        "positive_hit_rate": positive_hit / positive_available if positive_available else None,
        "selected_mate_rate": selected_labels["mate"] / selected_count if selected_count else None,
        "miss_examples": misses,
    }


def _max_only_summary(frames: list[dict[str, Any]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    examples = []
    for frame in frames:
        proposals = frame.get("strategy_proposal_frames") or []
        labels = [_result(proposal) for proposal in proposals]
        if not labels or "mate" in labels or "max_plies" not in labels:
            continue
        semantics = {_semantics(proposal) for proposal in proposals}
        if "forced_provider_outcome" in semantics:
            cls = "forced_existing_provider_capacity_or_horizon_gap"
        elif str(frame.get("source_stage") or "") in {"stage4", "stage5", "stage6"}:
            cls = "selected_playout_guardrail_or_horizon_caveat"
        else:
            cls = "selected_playout_max_only_unclassified"
        counts[cls] += 1
        if len(examples) < 8:
            examples.append(
                {
                    "frame_id": frame.get("frame_id"),
                    "source_stage": frame.get("source_stage"),
                    "classification": cls,
                    "providers": sorted({str(proposal.get("provider_id")) for proposal in proposals}),
                    "label_semantics": sorted(semantics),
                }
            )
    return {"classification_counts": dict(counts), "examples": examples}


def build_probe(repo_root: Path) -> dict[str, Any]:
    filtered = _load_json(repo_root, FILTERED_FRAMES)
    risk_review = _load_json(repo_root, RISK_REVIEW)
    baseline = _load_json(repo_root, BASELINE)
    for name, payload, expected in (
        ("filtered", filtered, "non_causal_filtered_frame_export"),
        ("risk_review", risk_review, "non_causal_review"),
        ("baseline", baseline, "non_causal_probe"),
    ):
        if payload.get("causal_status") != expected:
            raise ValueError(f"{name} artifact must remain {expected}")

    frames = _benchmark_frames(filtered)
    strata = [
        "selected_provider_playout",
        "forced_provider_outcome",
        "same_move_unselected_provider_playout",
    ]
    evaluations = [
        _evaluate_stratum(frames, semantic=semantic, selector_name=name, selector=selector)
        for semantic in strata
        for name, selector in SELECTORS.items()
    ]
    forced = [item for item in evaluations if item["label_semantics"] == "forced_provider_outcome"]
    selected = [item for item in evaluations if item["label_semantics"] == "selected_provider_playout"]
    best_forced = max((item["positive_hit_rate"] or 0.0 for item in forced), default=0.0)
    best_selected = max((item["positive_hit_rate"] or 0.0 for item in selected), default=0.0)
    max_only = _max_only_summary(frames)

    if best_forced >= 0.75 and best_selected >= 0.75:
        status = "stratified_strategy_arbitration_promising"
        next_step = "architecture_review_for_default_off_sandbox_skeleton"
    elif best_selected >= 0.75 and best_forced < 0.75:
        status = "selected_playout_controls_promising_forced_stage7_still_weak"
        next_step = "collect_or_review_forced_provider_controls_before_sandbox"
    else:
        status = "stratified_evidence_not_sandbox_ready"
        next_step = "do_not_implement_runtime_sandbox"

    probe = {
        "schema_version": "krk_strategy_arbiter_stratified_probe.v2",
        "causal_status": "non_causal_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(FILTERED_FRAMES), str(RISK_REVIEW), str(BASELINE)],
        "summary": {
            "benchmark_frame_count": len(frames),
            "best_forced_provider_positive_hit_rate": best_forced,
            "best_selected_provider_positive_hit_rate": best_selected,
            "max_only_summary": max_only,
        },
        "stratified_selector_results": evaluations,
        "decision": {
            "status": status,
            "runtime_sandbox_allowed": False,
            "recommended_next_step": next_step,
            "interpretation": (
                "Selected protected-control playout labels are easy for simple selectors, "
                "but forced-provider Stage7 labels remain the harder and smaller stratum."
            )
            if status == "selected_playout_controls_promising_forced_stage7_still_weak"
            else "Stratified evidence is summarized for architecture review only.",
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
    validate_probe(probe)
    return probe


def validate_probe(probe: dict[str, Any]) -> None:
    if probe.get("causal_status") != "non_causal_probe":
        raise ValueError("probe must remain non-causal")
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
        if probe.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if probe["decision"]["runtime_sandbox_allowed"]:
        raise ValueError("stratified probe must not authorize runtime sandboxing")


def render_markdown(probe: dict[str, Any]) -> str:
    summary = probe["summary"]
    decision = probe["decision"]
    lines = [
        "# KRK Strategy Arbiter Stratified Probe v2",
        "",
        "This is a non-causal, replay-free probe. It evaluates strategy-arbiter "
        "selectors separately for selected-provider playout labels, forced-provider "
        "labels, and same-move unselected-provider labels.",
        "",
        "## Summary",
        "",
        f"- Benchmark frames: `{summary['benchmark_frame_count']}`",
        f"- Best selected-provider positive hit rate: `{summary['best_selected_provider_positive_hit_rate']}`",
        f"- Best forced-provider positive hit rate: `{summary['best_forced_provider_positive_hit_rate']}`",
        f"- Max-only classification counts: `{summary['max_only_summary']['classification_counts']}`",
        "",
        "## Stratified Selector Results",
        "",
    ]
    for item in probe["stratified_selector_results"]:
        lines.extend(
            [
                f"### {item['label_semantics']} / {item['selector']}",
                "",
                f"- Eligible frames: `{item['eligible_frame_count']}`",
                f"- Eligible stage counts: `{item['eligible_stage_counts']}`",
                f"- Selected labels: `{item['selected_label_counts']}`",
                f"- Positive hit rate: `{item['positive_hit_rate']}`",
                f"- Selected mate rate: `{item['selected_mate_rate']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Decision",
            "",
            f"- Status: `{decision['status']}`",
            f"- Runtime sandbox allowed: `{decision['runtime_sandbox_allowed']}`",
            f"- Recommended next step: `{decision['recommended_next_step']}`",
            f"- Interpretation: {decision['interpretation']}",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(probe: dict[str, Any], report_root: Path) -> None:
    report_root.mkdir(parents=True, exist_ok=True)
    (report_root / "krk_strategy_arbiter_stratified_probe_v2.json").write_text(
        json.dumps(probe, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (report_root / "krk_strategy_arbiter_stratified_probe_v2.md").write_text(
        render_markdown(probe), encoding="utf-8"
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
    probe = build_probe(repo_root)
    write_outputs(probe, report_root)
    print(json.dumps(probe["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
