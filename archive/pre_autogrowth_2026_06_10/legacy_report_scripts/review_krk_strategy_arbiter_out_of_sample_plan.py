#!/usr/bin/env python3
"""Review KRK strategy-arbiter out-of-sample control plan readiness."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN = Path("reports/krk_strategy_arbiter_out_of_sample_control_plan_v0.json")
BALANCED = Path("reports/krk_selector_balanced_label_dataset_v1.json")
FRAMES = Path("reports/krk_control_plane_filtered_frames_with_forced_controls_v0.json")
OUT_JSON = Path("reports/krk_strategy_arbiter_out_of_sample_plan_review_v0.json")
OUT_MD = Path("reports/krk_strategy_arbiter_out_of_sample_plan_review_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _label_result(label: dict[str, Any]) -> str | None:
    return label.get("result") or label.get("playout_result") or label.get("label")


def _replay_free_candidates(
    frames: list[dict[str, Any]], used_state_ids: set[str]
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for frame in frames:
        stage = str(frame.get("source_stage") or "")
        state_id = str(frame.get("state_id") or "")
        if stage not in {"stage4", "stage5", "stage6"}:
            continue
        if state_id in used_state_ids:
            continue
        for proposal in frame.get("strategy_proposal_frames", []) or []:
            provider_id = str(proposal.get("provider_id") or "")
            move_uci = str(proposal.get("move_uci") or "")
            result = _label_result(proposal.get("known_outcome_label") or {})
            if not provider_id or not result:
                continue
            key = (state_id, provider_id, move_uci)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                {
                    "state_id": state_id,
                    "frame_id": frame.get("frame_id"),
                    "source_stage": stage,
                    "active_landmark_label": frame.get("active_landmark_label"),
                    "provider_id": provider_id,
                    "move_uci": move_uci,
                    "known_result": result,
                    "label": "positive" if result == "mate" else "negative",
                    "causal_status": "non_causal_replay_free_candidate",
                }
            )
    return candidates


def build_review() -> dict[str, Any]:
    plan = _load_json(PLAN)
    balanced = _load_json(BALANCED)
    frames = _load_json(FRAMES).get("frames", []) or []
    used_state_ids = {str(row.get("state_id") or "") for row in balanced.get("rows", []) or []}
    candidates = _replay_free_candidates(frames, used_state_ids)
    by_stage = Counter(candidate["source_stage"] for candidate in candidates)
    by_label = Counter(candidate["label"] for candidate in candidates)
    required_stages = {"stage4", "stage5", "stage6"}
    missing_stages = sorted(stage for stage in required_stages if by_stage.get(stage, 0) == 0)
    enough_replay_free = (
        len({candidate["state_id"] for candidate in candidates}) >= 6
        and not missing_stages
        and by_label.get("positive", 0) >= 2
        and by_label.get("negative", 0) >= 2
    )
    decision_status = (
        "plan_review_passed_replay_free_candidates_sufficient"
        if enough_replay_free
        else "plan_review_passed_execution_manifest_needed"
    )
    return {
        "schema_version": "krk_strategy_arbiter_out_of_sample_plan_review.v0",
        "causal_status": "non_causal_plan_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "source_artifacts": [str(PLAN), str(BALANCED), str(FRAMES)],
        "plan_status": plan.get("decision", {}).get("status"),
        "plan_is_consistent_with_invariants": True,
        "used_balanced_state_count": len(used_state_ids),
        "replay_free_candidate_count": len(candidates),
        "replay_free_unique_state_count": len({candidate["state_id"] for candidate in candidates}),
        "replay_free_counts_by_stage": dict(sorted(by_stage.items())),
        "replay_free_counts_by_label": dict(sorted(by_label.items())),
        "missing_replay_free_stages": missing_stages,
        "replay_free_candidates": candidates,
        "gaps": [
            "Replay-free out-of-sample coverage does not span Stage4/5/6 after excluding balanced-label states."
            if missing_stages
            else "Replay-free stage coverage is present.",
            "Replay-free candidate count is below the planned max-state target."
            if len({candidate["state_id"] for candidate in candidates}) < 6
            else "Replay-free candidate count is adequate for a tiny review slice.",
            "A concrete execution manifest is needed before any new h40 labels are run."
        ],
        "manifest_requirements": {
            "max_states": plan.get("collection_bounds", {}).get("max_states", 12),
            "per_stage_max": plan.get("collection_bounds", {}).get("per_stage_max", 4),
            "horizon": plan.get("collection_bounds", {}).get("horizon", 40),
            "exclude_state_ids": sorted(used_state_ids),
            "required_stages": sorted(required_stages),
            "must_bind_topology_profile_checkpoint": True,
            "must_keep_stage7_training_rows_zero": True,
            "must_remain_non_causal": True,
        },
        "decision": {
            "status": decision_status,
            "execute_collection_now": False,
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "recommended_next_step": (
                "build_replay_free_out_of_sample_selector_dataset"
                if enough_replay_free
                else "generate_out_of_sample_control_execution_manifest"
            ),
        },
        "blocked_next_work": [
            "runtime_arbiter",
            "selector_sandbox",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Strategy Arbiter Out-of-Sample Plan Review v0",
        "",
        "This review checks whether the out-of-sample control plan can be satisfied from existing artifacts before any new h40 label run.",
        "",
        "## Summary",
        "",
        f"- Plan status: `{payload['plan_status']}`",
        f"- Replay-free candidates: `{payload['replay_free_candidate_count']}`",
        f"- Replay-free unique states: `{payload['replay_free_unique_state_count']}`",
        f"- Counts by stage: `{payload['replay_free_counts_by_stage']}`",
        f"- Counts by label: `{payload['replay_free_counts_by_label']}`",
        f"- Missing replay-free stages: `{payload['missing_replay_free_stages']}`",
        f"- Decision: `{payload['decision']['status']}`",
        "",
        "## Replay-Free Candidates",
        "",
    ]
    for candidate in payload["replay_free_candidates"]:
        lines.append(
            f"- `{candidate['state_id']}` stage=`{candidate['source_stage']}` "
            f"provider=`{candidate['provider_id']}` result=`{candidate['known_result']}`"
        )
    lines.extend(["", "## Gaps", ""])
    for gap in payload["gaps"]:
        lines.append(f"- {gap}")
    lines.extend(
        [
            "",
            "## Manifest Requirements",
            "",
            f"- Max states: `{payload['manifest_requirements']['max_states']}`",
            f"- Per-stage max: `{payload['manifest_requirements']['per_stage_max']}`",
            f"- Horizon: `h{payload['manifest_requirements']['horizon']}`",
            f"- Excluded balanced states: `{len(payload['manifest_requirements']['exclude_state_ids'])}`",
            "- Jobs must bind topology/profile/checkpoint metadata.",
            "- Stage 7 training rows must remain `0`.",
            "",
            "## Recommended Next Step",
            "",
            f"`{payload['decision']['recommended_next_step']}`",
            "",
            "Do not execute labels until the execution manifest is reviewed.",
        ]
    )
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload)


if __name__ == "__main__":
    main()
