#!/usr/bin/env python3
"""Non-causal sandbox protocol for the Stage 7 post-box Plan Capsule.

This script does not compile or run a causal capsule. It checks whether the
existing offline DTM/reference trajectories support the proposed bounded
entry/progress/exit/abort semantics, so a later runtime sandbox has concrete
terms to implement instead of becoming a hidden controller.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_CANDIDATE = Path(
    "reports/structural_candidates/stage7_post_box_continuation_capsule_candidate.json"
)
DEFAULT_TRAJECTORY = Path(
    "reports/structural_candidates/stage7_post_box_dtm_trajectory_seed_h40.json"
)
DEFAULT_OUTPUT = Path(
    "reports/structural_candidates/stage7_post_box_plan_capsule_sandbox_protocol.json"
)
DEFAULT_MD_OUTPUT = Path(
    "reports/structural_candidates/stage7_post_box_plan_capsule_sandbox_protocol.md"
)


PROGRESS_TERM_SUPPORT = {
    "box_area_decreases_or_does_not_expand": {
        "box_area_decreases_after_move",
        "box_area_not_increased_after_move",
    },
    "cut_or_fence_preserved_or_restored": {
        "fence_exists_after_move",
        "fence_stable_after_move",
        "cut_preserved_after_move",
        "cut_replaced_after_move",
    },
    "white_king_support_improves": {
        "white_king_distance_to_rook_decreases",
        "white_king_distance_to_enemy_decreases",
    },
    "enemy_king_mobility_decreases": {
        "black_king_escape_count_decreases_after_move",
        "black_king_escape_count_not_increased_after_move",
    },
    "corner_net_pressure_increases": {
        "enemy_corner_distance_not_increased_after_move",
    },
    "mate_basin_proximity_improves": {
        "enemy_edge_distance_not_increased_after_move",
        "enemy_corner_distance_not_increased_after_move",
    },
    "safe_check_or_cut_created": {
        "safe_check_created_after_move",
        "checking_line_created_after_move",
        "fence_exists_after_move",
        "fence_stable_after_move",
        "rook_to_checking_line",
    },
    "stagnation_avoided": set(),
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _step_terms(step: dict[str, Any]) -> set[str]:
    return set(step.get("move_shape_terms") or []) | set(step.get("post_move_terms") or [])


def _matched_progress_terms(step: dict[str, Any], *, previous_dtm: int | None) -> list[str]:
    terms = _step_terms(step)
    matched: list[str] = []
    for progress_term, supporting_terms in PROGRESS_TERM_SUPPORT.items():
        if progress_term == "stagnation_avoided":
            child_dtm = step.get("child_dtm")
            if previous_dtm is not None and child_dtm is not None and int(child_dtm) < int(previous_dtm):
                matched.append(progress_term)
            continue
        if terms & supporting_terms:
            matched.append(progress_term)
    return matched


def _abort_terms(step: dict[str, Any], *, previous_dtm: int | None) -> list[str]:
    terms = _step_terms(step)
    aborts: list[str] = []
    if "rook_safe_after_move" not in terms:
        aborts.append("rook_unsafe")
    if "box_area_not_increased_after_move" not in terms and "box_area_decreases_after_move" not in terms:
        aborts.append("box_expands_or_unverified")
    child_dtm = step.get("child_dtm")
    if previous_dtm is not None and child_dtm is not None and int(child_dtm) >= int(previous_dtm):
        aborts.append("no_dtm_progress_after_owned_move")
    return aborts


def evaluate_capsule_protocol(
    *,
    candidate: dict[str, Any],
    trajectory_seed: dict[str, Any],
    ttl_white_moves: int | None = None,
) -> dict[str, Any]:
    capsule = candidate.get("plan_capsule") or {}
    ttl = int(ttl_white_moves or capsule.get("ttl_white_moves") or 3)
    trajectories = trajectory_seed.get("trajectories") or []
    per_trajectory: list[dict[str, Any]] = []
    pass_count = 0
    abort_count = 0

    for trajectory in trajectories:
        if not isinstance(trajectory, dict):
            continue
        steps = [s for s in trajectory.get("white_training_steps") or [] if isinstance(s, dict)]
        previous_dtm = trajectory.get("start_dtm")
        owned_steps = []
        trajectory_aborts: list[str] = []
        matched_progress_union: set[str] = set()
        for step in steps[:ttl]:
            matched_progress = _matched_progress_terms(step, previous_dtm=previous_dtm)
            aborts = _abort_terms(step, previous_dtm=previous_dtm)
            matched_progress_union.update(matched_progress)
            trajectory_aborts.extend(aborts)
            owned_steps.append(
                {
                    "ply_index": step.get("ply_index"),
                    "move": step.get("move"),
                    "previous_dtm": previous_dtm,
                    "child_dtm": step.get("child_dtm"),
                    "matched_progress_terms": matched_progress,
                    "abort_terms": aborts,
                    "move_shape_terms": step.get("move_shape_terms") or [],
                    "post_move_terms": step.get("post_move_terms") or [],
                }
            )
            previous_dtm = step.get("child_dtm", previous_dtm)

        progress_ok = bool(owned_steps) and all(step["matched_progress_terms"] for step in owned_steps)
        abort_free = not trajectory_aborts
        dtm_progress = (
            trajectory.get("start_dtm") is not None
            and previous_dtm is not None
            and int(previous_dtm) < int(trajectory.get("start_dtm"))
        )
        protocol_supported = progress_ok and abort_free and dtm_progress
        pass_count += int(protocol_supported)
        abort_count += int(not abort_free)
        per_trajectory.append(
            {
                "start_fen": trajectory.get("start_fen"),
                "start_dtm": trajectory.get("start_dtm"),
                "dtm_after_owned_steps": previous_dtm,
                "ttl_white_moves": ttl,
                "owned_step_count": len(owned_steps),
                "progress_ok": progress_ok,
                "abort_free": abort_free,
                "dtm_progress": dtm_progress,
                "protocol_supported_by_reference": protocol_supported,
                "matched_progress_terms": sorted(matched_progress_union),
                "abort_terms": sorted(set(trajectory_aborts)),
                "owned_steps": owned_steps,
                "exit_status": (
                    "ttl_expired_with_dtm_progress"
                    if protocol_supported
                    else "ttl_or_abort_requires_refinement"
                ),
            }
        )

    return {
        "schema_version": "stage7_post_box_plan_capsule_sandbox_protocol.v1",
        "causal_status": "non_causal",
        "runtime_behavior_changed": False,
        "candidate_id": candidate.get("candidate_id"),
        "capsule_id": capsule.get("capsule_id"),
        "ttl_white_moves": ttl,
        "trajectory_count": len(per_trajectory),
        "reference_supported_count": pass_count,
        "reference_abort_count": abort_count,
        "support_rate": (pass_count / len(per_trajectory)) if per_trajectory else 0.0,
        "interpretation": (
            "reference trajectories support a bounded commitment protocol"
            if per_trajectory and pass_count == len(per_trajectory)
            else "reference trajectories expose abort/progress gaps before causal sandboxing"
        ),
        "next_action": (
            "compile_default_off_visible_capsule_sandbox"
            if per_trajectory and pass_count == len(per_trajectory)
            else "refine_capsule_terms_before_runtime_sandbox"
        ),
        "per_trajectory": per_trajectory,
        "hard_blocks": [
            "do_not_train_stage8",
            "do_not_promote_stage7",
            "do_not_enable_runtime_capsule_by_default",
            "do_not_mutate_topology_during_gameplay",
        ],
    }


def _write_md(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Stage 7 Post-Box Plan Capsule Sandbox Protocol",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"Runtime behavior changed: `{payload['runtime_behavior_changed']}`",
        f"Capsule: `{payload.get('capsule_id')}`",
        f"TTL white moves: `{payload['ttl_white_moves']}`",
        f"Reference support: `{payload['reference_supported_count']}/{payload['trajectory_count']}`",
        "",
        "This is a non-causal protocol check. It does not compile a runtime plan owner.",
        "",
        "## Interpretation",
        "",
        payload["interpretation"],
        "",
        f"Next action: `{payload['next_action']}`",
        "",
        "## Trajectories",
        "",
    ]
    for item in payload.get("per_trajectory") or []:
        lines.append(f"- `{item.get('start_fen')}`")
        lines.append(f"  start DTM `{item.get('start_dtm')}` -> after TTL `{item.get('dtm_after_owned_steps')}`")
        lines.append(f"  supported: `{item.get('protocol_supported_by_reference')}`")
        if item.get("abort_terms"):
            lines.append(f"  abort terms: `{', '.join(item['abort_terms'])}`")
        lines.append(f"  progress terms: `{', '.join(item.get('matched_progress_terms') or [])}`")
    lines.extend(["", "## Hard Blocks", ""])
    for block in payload.get("hard_blocks") or []:
        lines.append(f"- `{block}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate non-causal Stage 7 Plan Capsule sandbox protocol")
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--trajectory-seed", type=Path, default=DEFAULT_TRAJECTORY)
    parser.add_argument("--ttl-white-moves", type=int, default=None)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MD_OUTPUT)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = evaluate_capsule_protocol(
        candidate=_load_json(args.candidate),
        trajectory_seed=_load_json(args.trajectory_seed),
        ttl_white_moves=args.ttl_white_moves,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_md(payload, args.markdown_output)
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
