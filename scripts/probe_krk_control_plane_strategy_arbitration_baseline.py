#!/usr/bin/env python3
"""Run non-causal strategy-arbitration baselines over control-plane frames.

This script consumes existing filtered ControlPlaneEvidenceFrame artifacts. It
does not run playouts, change routing, train models, mutate topology, or use
DTM/tablebase values at runtime.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable

import chess

from recon_lite_chess.krk_baseline_nodes import _compute_krk_context_terms, _krk_geometry_metrics


FILTERED_FRAMES = Path("reports/krk_control_plane_filtered_frames_v0.json")

Selector = Callable[[dict[str, Any]], dict[str, Any] | None]


def _load_json(root: Path, relative_path: Path) -> dict[str, Any]:
    payload = json.loads((root / relative_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {relative_path}")
    return payload


def _known_provider_result(proposal: dict[str, Any]) -> str:
    label = proposal.get("known_outcome_label") or {}
    if not isinstance(label, dict):
        return "unknown"
    result = label.get("result") or label.get("playout_result")
    return str(result) if result in {"mate", "max_plies", "draw", "stagnation"} else "unknown"


def _score(value: Any, fallback: float = float("-inf")) -> float:
    return float(value) if isinstance(value, (int, float)) else fallback


def _box_area_relevance(metrics: dict[str, Any]) -> str:
    edge_value = metrics.get("enemy_edge_distance")
    box_value = metrics.get("box_area")
    edge = int(edge_value) if edge_value is not None else 99
    box = int(box_value) if box_value is not None else 0
    if edge <= 0:
        return "low"
    if edge == 1:
        return "medium" if box >= 8 else "low"
    return "high" if box >= 12 else "medium"


def _context_for_frame(frame: dict[str, Any]) -> dict[str, Any]:
    try:
        board = chess.Board(str(frame.get("fen") or ""))
    except Exception:
        return {"context_available": False}
    terms = _compute_krk_context_terms(board)
    metrics = _krk_geometry_metrics(board) or {}
    edge_distance = metrics.get("enemy_edge_distance")
    if edge_distance is None:
        edge_bucket = "unknown"
    elif int(edge_distance) <= 0:
        edge_bucket = "at_edge"
    elif int(edge_distance) == 1:
        edge_bucket = "near_edge"
    else:
        edge_bucket = "central"
    return {
        "context_available": True,
        "active_terminal_terms": sorted(key for key, value in terms.items() if value),
        "black_king_edge_distance": edge_distance,
        "black_king_edge_bucket": edge_bucket,
        "box_area": metrics.get("box_area"),
        "box_area_relevance": _box_area_relevance(metrics),
        "rook_safe": bool(terms.get("rook_safe", False)),
        "fence_exists": bool(terms.get("fence_exists", False)),
        "fence_stable": bool(terms.get("fence_stable", False)),
        "cut_stable": bool(terms.get("cut_stable", False)),
        "white_king_support_available": bool(terms.get("white_king_support_available", False)),
        "white_king_can_improve_support": bool(terms.get("king_support_can_improve", False)),
        "enemy_king_mobility": metrics.get("black_king_escape_count"),
        "mate_in_one_available": bool(terms.get("mate_in_one_available", False)),
        "edge_net_pressure_proxy": bool(
            terms.get("edge_trap_shape_available", False)
            or terms.get("corner_net_pressure_available", False)
            or terms.get("enemy_king_near_edge", False)
        ),
        "corner_net_pressure_proxy": bool(terms.get("corner_net_pressure_available", False)),
        "stalemate_or_draw_risk": bool(terms.get("stalemate_risk", False) or terms.get("draw_risk", False)),
    }


def _benchmark_frames(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        frame
        for frame in payload.get("frames") or []
        if "strategy_arbitration_benchmark" in (frame.get("filter_metadata") or {}).get("benchmark_roles", [])
    ]


def _top_by_key(frame: dict[str, Any], key: str) -> dict[str, Any] | None:
    proposals = [
        proposal
        for proposal in frame.get("strategy_proposal_frames") or []
        if isinstance(proposal.get(key), (int, float))
    ]
    if not proposals:
        return None
    return max(proposals, key=lambda proposal: _score(proposal.get(key)))


def _raw_score_selector(frame: dict[str, Any]) -> dict[str, Any] | None:
    return _top_by_key(frame, "raw_score")


def _normalized_score_selector(frame: dict[str, Any]) -> dict[str, Any] | None:
    return _top_by_key(frame, "normalized_score")


def _provider_rank_selector(frame: dict[str, Any]) -> dict[str, Any] | None:
    proposals = [
        proposal
        for proposal in frame.get("strategy_proposal_frames") or []
        if isinstance(proposal.get("provider_local_rank"), int)
    ]
    if not proposals:
        return None
    return min(
        proposals,
        key=lambda proposal: (
            int(proposal.get("provider_local_rank") or 999999),
            -_score(proposal.get("normalized_score"), 0.0),
            -_score(proposal.get("raw_score"), 0.0),
        ),
    )


def _provider_from_context(context: dict[str, Any]) -> str:
    active = set(context.get("active_terminal_terms") or [])
    if context.get("mate_in_one_available"):
        return "krk.stage0_basin"
    if context.get("fence_exists") and not context.get("fence_stable"):
        return "krk.fence_established"
    if context.get("black_king_edge_bucket") == "at_edge":
        if context.get("fence_exists") or "edge_trap_shape_available" in active:
            return "krk.edge_trap_close"
        return "krk.fence_established"
    if context.get("black_king_edge_bucket") == "near_edge":
        return "krk.drive_to_edge" if context.get("white_king_support_available") else "krk.fence_established"
    if context.get("box_area_relevance") == "high":
        return "krk.box_shrink"
    return "krk.stage0_basin"


def _proposal_for_provider(frame: dict[str, Any], provider_id: str) -> dict[str, Any] | None:
    proposals = [
        proposal
        for proposal in frame.get("strategy_proposal_frames") or []
        if proposal.get("provider_id") == provider_id
    ]
    if not proposals:
        return None
    return max(
        proposals,
        key=lambda proposal: (
            _score(proposal.get("normalized_score"), 0.0),
            _score(proposal.get("raw_score"), 0.0),
        ),
    )


def _visible_context_selector(frame: dict[str, Any]) -> dict[str, Any] | None:
    context = frame.get("computed_terminal_space_context") or {}
    return _proposal_for_provider(frame, _provider_from_context(context))


def _stage_prior_selector(frame: dict[str, Any]) -> dict[str, Any] | None:
    stage = str(frame.get("source_stage") or "")
    active = str(frame.get("active_landmark_label") or "")
    providers_by_stage = {
        "stage4": ["krk.stage0_basin", "krk.edge_trap_wrong_tempo"],
        "stage5": ["krk.edge_trap_close", "krk.fence_established", "krk.stage0_basin"],
        "stage6": ["krk.drive_to_edge", "krk.fence_established", "krk.stage0_basin"],
        "stage7": ["krk.box_shrink", "krk.post_box_shrink_continuation", "krk.drive_to_edge"],
    }
    if active == "box_shrink":
        providers = ["krk.post_box_shrink_continuation", "krk.box_shrink", "krk.drive_to_edge"]
    else:
        providers = providers_by_stage.get(stage, [])
    for provider_id in providers:
        proposal = _proposal_for_provider(frame, provider_id)
        if proposal is not None:
            return proposal
    return _normalized_score_selector(frame)


def _proposal_label_counts(frames: list[dict[str, Any]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    by_stage: Counter[str] = Counter()
    frames_with_mate = 0
    frames_with_only_max = 0
    for frame in frames:
        labels = [_known_provider_result(proposal) for proposal in frame.get("strategy_proposal_frames") or []]
        counts.update(labels)
        for label in labels:
            by_stage[f"{frame.get('source_stage')}:{label}"] += 1
        if "mate" in labels:
            frames_with_mate += 1
        elif labels and all(label == "max_plies" for label in labels):
            frames_with_only_max += 1
    return {
        "proposal_label_counts": dict(counts),
        "proposal_label_counts_by_stage": dict(by_stage),
        "frames_with_provider_mate": frames_with_mate,
        "frames_with_only_provider_max_plies": frames_with_only_max,
    }


def _evaluate_selector(
    frames: list[dict[str, Any]],
    *,
    selector_name: str,
    selector: Selector,
) -> dict[str, Any]:
    selected_count = 0
    selected_labels: Counter[str] = Counter()
    positive_available = 0
    hit_when_positive_available = 0
    miss_examples: list[dict[str, Any]] = []
    by_stage: Counter[str] = Counter()
    for frame in frames:
        labels = [_known_provider_result(proposal) for proposal in frame.get("strategy_proposal_frames") or []]
        has_positive = "mate" in labels
        if has_positive:
            positive_available += 1
        selected = selector(frame)
        if selected is None:
            selected_labels["no_selection"] += 1
            continue
        selected_count += 1
        result = _known_provider_result(selected)
        selected_labels[result] += 1
        by_stage[f"{frame.get('source_stage')}:{result}"] += 1
        if has_positive and result == "mate":
            hit_when_positive_available += 1
        elif has_positive and len(miss_examples) < 8:
            positive_providers = sorted(
                {
                    str(proposal.get("provider_id"))
                    for proposal in frame.get("strategy_proposal_frames") or []
                    if _known_provider_result(proposal) == "mate"
                }
            )
            miss_examples.append(
                {
                    "frame_id": frame.get("frame_id"),
                    "source_stage": frame.get("source_stage"),
                    "selected_provider": selected.get("provider_id"),
                    "selected_move": selected.get("move_uci"),
                    "selected_result": result,
                    "positive_providers": positive_providers,
                    "context": frame.get("computed_terminal_space_context"),
                }
            )
    return {
        "selector": selector_name,
        "selected_count": selected_count,
        "selected_label_counts": dict(selected_labels),
        "selected_label_counts_by_stage": dict(by_stage),
        "positive_available_frame_count": positive_available,
        "hit_when_positive_available_count": hit_when_positive_available,
        "hit_when_positive_available_rate": (
            hit_when_positive_available / positive_available if positive_available else None
        ),
        "selected_mate_rate": selected_labels["mate"] / selected_count if selected_count else None,
        "miss_examples": miss_examples,
    }


def _context_summary(frames: list[dict[str, Any]]) -> dict[str, Any]:
    edge_box: Counter[str] = Counter()
    stage_edge_box: Counter[str] = Counter()
    outcome_edge_box: Counter[str] = Counter()
    for frame in frames:
        context = frame.get("computed_terminal_space_context") or {}
        key = f"{context.get('black_king_edge_bucket')}|{context.get('box_area_relevance')}"
        edge_box[key] += 1
        stage_edge_box[f"{frame.get('source_stage')}|{key}"] += 1
        outcome_edge_box[f"{frame.get('outcome')}|{key}"] += 1
    return {
        "box_relevance_by_edge_bucket": dict(edge_box),
        "box_relevance_by_stage_edge_bucket": dict(stage_edge_box),
        "box_relevance_by_outcome_edge_bucket": dict(outcome_edge_box),
    }


def build_baseline(repo_root: Path) -> dict[str, Any]:
    payload = _load_json(repo_root, FILTERED_FRAMES)
    if payload.get("causal_status") != "non_causal_filtered_frame_export":
        raise ValueError("filtered frames must remain non-causal")
    frames = _benchmark_frames(payload)
    for frame in frames:
        frame["computed_terminal_space_context"] = _context_for_frame(frame)

    selector_results = [
        _evaluate_selector(frames, selector_name="raw_global_score", selector=_raw_score_selector),
        _evaluate_selector(frames, selector_name="normalized_score", selector=_normalized_score_selector),
        _evaluate_selector(frames, selector_name="provider_local_rank", selector=_provider_rank_selector),
        _evaluate_selector(frames, selector_name="visible_context_heuristic", selector=_visible_context_selector),
        _evaluate_selector(frames, selector_name="stage_prior_heuristic", selector=_stage_prior_selector),
    ]
    positive_available = _proposal_label_counts(frames)["frames_with_provider_mate"]
    best_hit_rate = max(
        (result["hit_when_positive_available_rate"] or 0.0 for result in selector_results),
        default=0.0,
    )
    if positive_available < 8:
        status = "inconclusive_need_more_stratified_data"
        recommended_next = "collect_more_stratified_arbitration_evidence"
    elif best_hit_rate >= 0.75:
        status = "strategy_arbitration_promising"
        recommended_next = "non_causal_strategy_arbiter_sandbox_design"
    else:
        status = "missing_feature_or_curriculum_boundary_still_likely"
        recommended_next = "review_feature_and_curriculum_boundary_evidence"

    baseline = {
        "schema_version": "krk_control_plane_strategy_arbitration_baseline.v1",
        "causal_status": "non_causal_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "hidden_python_controller": False,
        "gameplay_topology_mutation": False,
        "runtime_arbiter_added": False,
        "runtime_terminals_added": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(FILTERED_FRAMES)],
        "frame_summary": {
            "strategy_benchmark_frame_count": len(frames),
            "stage_counts": dict(Counter(str(frame.get("source_stage") or "unknown") for frame in frames)),
            **_proposal_label_counts(frames),
        },
        "context_summary": _context_summary(frames),
        "selector_results": selector_results,
        "decision": {
            "selected_status": status,
            "recommended_next_class": recommended_next,
            "interpretation": (
                "Existing provider labels are sufficient for a small offline baseline. "
                "At least one simple selector can recover many converting providers when one is present, "
                "but this remains non-causal and too small for runtime promotion."
            )
            if status == "strategy_arbitration_promising"
            else "The small baseline is not strong enough to justify sandbox design.",
            "causal_next_step_allowed": False,
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
    validate_baseline(baseline)
    return baseline


def validate_baseline(baseline: dict[str, Any]) -> None:
    if baseline.get("causal_status") != "non_causal_probe":
        raise ValueError("baseline must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_score_changes",
        "runtime_direct_routing",
        "runtime_dtm_or_tablebase_lookup",
        "hidden_python_controller",
        "gameplay_topology_mutation",
        "runtime_arbiter_added",
        "runtime_terminals_added",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if baseline.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if baseline["decision"]["causal_next_step_allowed"]:
        raise ValueError("baseline must not authorize causal next steps")


def render_markdown(baseline: dict[str, Any]) -> str:
    lines = [
        "# KRK Control-Plane Strategy Arbitration Baseline v1",
        "",
        "This is a non-causal offline selector baseline over existing filtered "
        "ControlPlaneEvidenceFrame records. It does not implement a runtime "
        "arbiter, add terminals, run playouts, train Stage 8, or promote Stage 7.",
        "",
        "## Frame Summary",
        "",
    ]
    summary = baseline["frame_summary"]
    for key in (
        "strategy_benchmark_frame_count",
        "stage_counts",
        "proposal_label_counts",
        "frames_with_provider_mate",
        "frames_with_only_provider_max_plies",
    ):
        lines.append(f"- `{key}`: `{summary.get(key)}`")
    lines.extend(["", "## Selector Results", ""])
    for result in baseline["selector_results"]:
        lines.extend(
            [
                f"### {result['selector']}",
                "",
                f"- Selected count: `{result['selected_count']}`",
                f"- Selected labels: `{result['selected_label_counts']}`",
                f"- Positive-available frames: `{result['positive_available_frame_count']}`",
                f"- Positive hit count: `{result['hit_when_positive_available_count']}`",
                f"- Positive hit rate: `{result['hit_when_positive_available_rate']}`",
                f"- Selected mate rate: `{result['selected_mate_rate']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Context Summary",
            "",
            f"- Box relevance by edge bucket: `{baseline['context_summary']['box_relevance_by_edge_bucket']}`",
            "",
            "## Decision",
            "",
            f"- Status: `{baseline['decision']['selected_status']}`",
            f"- Recommended next class: `{baseline['decision']['recommended_next_class']}`",
            f"- Interpretation: {baseline['decision']['interpretation']}",
            f"- Causal next step allowed: `{baseline['decision']['causal_next_step_allowed']}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(baseline: dict[str, Any], report_root: Path) -> None:
    report_root.mkdir(parents=True, exist_ok=True)
    (report_root / "krk_control_plane_strategy_arbitration_baseline_v1.json").write_text(
        json.dumps(baseline, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (report_root / "krk_control_plane_strategy_arbitration_baseline_v1.md").write_text(
        render_markdown(baseline), encoding="utf-8"
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
    baseline = build_baseline(repo_root)
    write_outputs(baseline, report_root)
    print(json.dumps(baseline["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
