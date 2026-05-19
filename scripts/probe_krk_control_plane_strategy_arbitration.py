#!/usr/bin/env python3
"""Probe offline KRK strategy arbitration on filtered control-plane frames."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable


FILTERED_FRAMES = Path("reports/krk_control_plane_filtered_frames_v0.json")


Selector = Callable[[list[dict[str, Any]]], dict[str, Any] | None]


def _load_json(root: Path, relative_path: Path) -> dict[str, Any]:
    payload = json.loads((root / relative_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {relative_path}")
    return payload


def _known_provider_result(proposal: dict[str, Any]) -> str:
    label = proposal.get("known_outcome_label") or {}
    if isinstance(label, dict):
        result = label.get("result") or label.get("playout_result")
        if result in {"mate", "max_plies", "draw", "stagnation"}:
            return str(result)
    return "unknown"


def _select_raw_score(proposals: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [p for p in proposals if isinstance(p.get("raw_score"), (int, float))]
    if not candidates:
        return None
    return max(candidates, key=lambda proposal: float(proposal["raw_score"]))


def _select_normalized_score(proposals: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [p for p in proposals if isinstance(p.get("normalized_score"), (int, float))]
    if not candidates:
        return None
    return max(candidates, key=lambda proposal: float(proposal["normalized_score"]))


def _select_provider_rank(proposals: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [p for p in proposals if isinstance(p.get("provider_local_rank"), int)]
    if not candidates:
        return None
    return min(candidates, key=lambda proposal: int(proposal["provider_local_rank"]))


def _evaluate_selector(frames: list[dict[str, Any]], name: str, selector: Selector) -> dict[str, Any]:
    selected = []
    unknown = 0
    mate = 0
    max_plies = 0
    for frame in frames:
        proposal = selector(frame.get("strategy_proposal_frames") or [])
        if proposal is None:
            continue
        result = _known_provider_result(proposal)
        selected.append(
            {
                "frame_id": frame.get("frame_id"),
                "provider_id": proposal.get("provider_id"),
                "move_uci": proposal.get("move_uci"),
                "known_provider_result": result,
            }
        )
        if result == "mate":
            mate += 1
        elif result == "max_plies":
            max_plies += 1
        else:
            unknown += 1
    known = mate + max_plies
    return {
        "selector": name,
        "selected_count": len(selected),
        "known_selected_count": known,
        "selected_mate_count": mate,
        "selected_max_plies_count": max_plies,
        "selected_unknown_count": unknown,
        "known_selected_mate_rate": mate / known if known else None,
        "selected_examples": selected[:8],
    }


def build_probe(repo_root: Path) -> dict[str, Any]:
    filtered = _load_json(repo_root, FILTERED_FRAMES)
    if filtered.get("causal_status") != "non_causal_filtered_frame_export":
        raise ValueError("filtered frame export must remain non-causal")
    frames = [
        frame
        for frame in filtered.get("frames") or []
        if "strategy_arbitration_benchmark" in (frame.get("filter_metadata") or {}).get("benchmark_roles", [])
    ]
    provider_labeled_frames = [
        frame
        for frame in frames
        if any(
            _known_provider_result(proposal) in {"mate", "max_plies"}
            for proposal in frame.get("strategy_proposal_frames") or []
        )
    ]
    frames_with_known_mate = [
        frame
        for frame in provider_labeled_frames
        if any(_known_provider_result(proposal) == "mate" for proposal in frame.get("strategy_proposal_frames") or [])
    ]
    frames_with_raw = [
        frame
        for frame in frames
        if any(isinstance(proposal.get("raw_score"), (int, float)) for proposal in frame.get("strategy_proposal_frames") or [])
    ]
    frames_with_normalized = [
        frame
        for frame in frames
        if any(
            isinstance(proposal.get("normalized_score"), (int, float))
            for proposal in frame.get("strategy_proposal_frames") or []
        )
    ]
    selector_results = [
        _evaluate_selector(provider_labeled_frames, "raw_global_score", _select_raw_score),
        _evaluate_selector(provider_labeled_frames, "normalized_score", _select_normalized_score),
        _evaluate_selector(provider_labeled_frames, "provider_local_rank", _select_provider_rank),
    ]
    label_status = (
        "provider_labels_underpowered"
        if len(frames_with_known_mate) < 5
        else "provider_labels_sufficient_for_small_probe"
    )
    probe = {
        "schema_version": "krk_control_plane_strategy_arbitration_probe.v0",
        "causal_status": "non_causal_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "runtime_arbiter_added": False,
        "runtime_terminals_added": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(FILTERED_FRAMES)],
        "label_coverage": {
            "strategy_benchmark_frame_count": len(frames),
            "provider_labeled_frame_count": len(provider_labeled_frames),
            "frames_with_known_provider_mate": len(frames_with_known_mate),
            "frames_with_raw_scores": len(frames_with_raw),
            "frames_with_normalized_scores": len(frames_with_normalized),
            "label_status": label_status,
        },
        "oracle_ceilings": {
            "known_provider_mate_available_count": len(frames_with_known_mate),
            "known_provider_mate_available_rate": (
                len(frames_with_known_mate) / len(provider_labeled_frames)
                if provider_labeled_frames
                else None
            ),
        },
        "selector_results": selector_results,
        "decision": {
            "selected_status": label_status,
            "interpretation": (
                "The filtered control-plane frames are useful as a common evidence substrate, "
                "but provider-level conversion labels are too sparse for a reliable learned "
                "strategy-arbitration benchmark."
            )
            if label_status == "provider_labels_underpowered"
            else "Provider labels are sufficient for a small non-causal arbitration benchmark.",
            "recommended_next_slice": "provider_label_coverage_plan_v0"
            if label_status == "provider_labels_underpowered"
            else "offline_strategy_arbitration_baseline_v1",
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
    validate_probe(probe)
    return probe


def validate_probe(probe: dict[str, Any]) -> None:
    if probe.get("causal_status") != "non_causal_probe":
        raise ValueError("probe must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "runtime_arbiter_added",
        "runtime_terminals_added",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if probe.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if probe["decision"]["causal_next_step_allowed"]:
        raise ValueError("probe must not authorize causal next steps")


def render_markdown(probe: dict[str, Any]) -> str:
    coverage = probe["label_coverage"]
    decision = probe["decision"]
    lines = [
        "# KRK Control-Plane Strategy Arbitration Probe v0",
        "",
        "This is a non-causal offline probe over filtered control-plane frames. It "
        "does not implement a runtime arbiter or authorize a sandbox.",
        "",
        "## Label Coverage",
        "",
    ]
    lines.extend(f"- `{key}`: `{value}`" for key, value in coverage.items())
    lines.extend(["", "## Selector Results", ""])
    for result in probe["selector_results"]:
        lines.extend(
            [
                f"### {result['selector']}",
                "",
                f"- Selected count: `{result['selected_count']}`",
                f"- Known selected count: `{result['known_selected_count']}`",
                f"- Mate / max_plies / unknown: `{result['selected_mate_count']}` / `{result['selected_max_plies_count']}` / `{result['selected_unknown_count']}`",
                f"- Known selected mate rate: `{result['known_selected_mate_rate']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Decision",
            "",
            f"- Status: `{decision['selected_status']}`",
            f"- Interpretation: {decision['interpretation']}",
            f"- Recommended next slice: `{decision['recommended_next_slice']}`",
            f"- Causal next step allowed: `{decision['causal_next_step_allowed']}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(probe: dict[str, Any], report_root: Path) -> None:
    report_root.mkdir(parents=True, exist_ok=True)
    (report_root / "krk_control_plane_strategy_arbitration_probe_v0.json").write_text(
        json.dumps(probe, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (report_root / "krk_control_plane_strategy_arbitration_probe_v0.md").write_text(
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
