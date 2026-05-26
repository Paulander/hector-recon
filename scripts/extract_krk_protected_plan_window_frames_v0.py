#!/usr/bin/env python3
"""Extract replay-free protected KRK plan-window frames from Stage 4/5/6 traces.

These frames are not PlanCapsule runtime behavior. They are non-causal
cross-stage evidence records built from existing handoff packets so sequence
policy work can compare entry/progress/exit/handoff-like fields outside Stage 7.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "reports/strategy_arbitration/krk_cross_stage_plan_capsule_evidence_requirements_v0.json"
OUTPUT_JSON = ROOT / "reports/strategy_arbitration/krk_protected_plan_window_frames_v0.json"
OUTPUT_MD = ROOT / "reports/strategy_arbitration/krk_protected_plan_window_frames_v0.md"

SCHEMA_VERSION = "krk_protected_plan_window_frames.v0"

STAGE_ARTIFACTS = {
    "stage4": {
        "label": "edge_trap_wrong_tempo",
        "path": (
            "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/"
            "stage6_overlay_composed/stage4_wrong_tempo_overlay_300_seed7_h40_profile_bonus.json"
        ),
        "frame_family": "wrong_tempo_plan_window",
    },
    "stage5": {
        "label": "fence_established",
        "path": (
            "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/"
            "stage6_overlay_composed/stage5_fence_overlay_300_seed7_h40_profile_bonus.json"
        ),
        "frame_family": "fence_handoff_plan_window",
    },
    "stage6": {
        "label": "drive_to_edge",
        "path": (
            "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/"
            "stage6_overlay_composed/stage6_drive_overlay_300_seed7_h40_profile_bonus.json"
        ),
        "frame_family": "drive_to_edge_plan_window",
    },
}

COMMON_FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "runtime_candidate_generator_changes_implemented": False,
    "runtime_selector_implemented": False,
    "runtime_score_changes": False,
    "runtime_direct_routing": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
}


def _load(path: str | Path) -> dict[str, Any]:
    full = ROOT / path if isinstance(path, str) else path
    return json.loads(full.read_text(encoding="utf-8"))


def _frame_id(*parts: Any) -> str:
    digest = hashlib.sha1("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:12]
    return f"planwin.{digest}"


def _key(terms: dict[str, Any]) -> tuple[str, str] | None:
    fen = terms.get("fen")
    move = terms.get("move")
    if not fen or not move:
        return None
    return str(fen), str(move)


def _packets_by_phase(payload: dict[str, Any]) -> dict[tuple[str, str], dict[str, dict[str, Any]]]:
    grouped: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for packet in payload.get("handoff_packets") or []:
        if not isinstance(packet, dict):
            continue
        terms = packet.get("evidence_terms") or {}
        if not isinstance(terms, dict):
            continue
        key = _key(terms)
        phase = packet.get("phase")
        if key is None or not phase:
            continue
        grouped[key][str(phase)] = packet
    return grouped


def _terms(packet: dict[str, Any] | None) -> dict[str, Any]:
    if not packet:
        return {}
    terms = packet.get("evidence_terms") or {}
    return terms if isinstance(terms, dict) else {}


def _frame_from_group(
    *,
    source_stage: str,
    label: str,
    frame_family: str,
    source_artifact: str,
    key: tuple[str, str],
    packets: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    own = _terms(packets.get("post_own_move"))
    reply = _terms(packets.get("post_opponent_reply"))
    summary = _terms(packets.get("playout_summary"))
    result = summary.get("playout_result") or summary.get("observed_outcome")
    status = "success" if result == "mate" else "failure" if result in {"max_plies", "draw"} else "unknown"
    entry_terms = [
        term
        for term, value in {
            "visible_fence_contract_confirmed": own.get("visible_fence_contract_confirmed"),
            "reward_confirmed": own.get("reward_confirmed"),
            "rook_safe_after_own_move": own.get("rook_safe_after_own_move"),
            "enemy_king_boxed_after_own_move": own.get("enemy_king_boxed_after_own_move"),
        }.items()
        if value is True
    ]
    progress_terms = [
        term
        for term, value in {
            "fence_survived_reply": reply.get("fence_survived_reply"),
            "enemy_king_boxed_after_reply": reply.get("enemy_king_boxed_after_reply"),
            "successor_affordance": "successor_affordance" in (packets.get("post_opponent_reply") or {}).get("achieved", []),
            "handoff_gap_absent": reply.get("handoff_gap") is False,
        }.items()
        if value is True
    ]
    abort_terms = [
        term
        for term, value in {
            "reward_contract_mismatch": own.get("reward_contract_mismatch") or reply.get("reward_contract_mismatch"),
            "fence_broken_by_reply": reply.get("fence_broken_by_reply"),
            "provider_selected_without_role_license": reply.get("provider_selected_without_role_license"),
            "max_plies": result == "max_plies",
        }.items()
        if value is True
    ]
    handoff_targets = sorted((reply.get("continuation_exports") or {}).keys())
    if not handoff_targets:
        handoff_targets = sorted((packets.get("post_opponent_reply") or {}).get("continuation_exports", {}).keys())
    return {
        "schema_version": "krk_protected_plan_window_frame.v0",
        "frame_id": _frame_id(source_stage, key[0], key[1], result),
        "source_stage": source_stage,
        "source_family": frame_family,
        "source_artifact": source_artifact,
        "fen": key[0],
        "move_uci": key[1],
        "active_landmark_label": label,
        "result": result,
        "outcome_bucket": status,
        "plies": summary.get("plies"),
        "entry_terms_confirmed": entry_terms,
        "progress_terms_after_first_reply": progress_terms,
        "abort_terms": abort_terms,
        "handoff_targets": handoff_targets,
        "selected_successor": reply.get("successor_selected_skill"),
        "selected_successor_contract_met": reply.get("selected_successor_contract_met"),
        "semantic_alignment_status": summary.get("semantic_alignment_status") or own.get("semantic_alignment_status"),
        "h40_outcome_label": "conversion_positive" if result == "mate" else "conversion_failure",
        "stage7_heldout_challenge": False,
        "usable_for_selector_training": False,
        "usable_for_runtime_authorization": False,
        "causal_status": "non_causal_replay_free_protected_plan_window",
    }


def _select_balanced(frames: list[dict[str, Any]], *, per_stage_success: int = 6, per_stage_failure: int = 6) -> list[dict[str, Any]]:
    selected = []
    by_stage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for frame in frames:
        by_stage[frame["source_stage"]].append(frame)
    for stage in sorted(by_stage):
        stage_frames = by_stage[stage]
        stage_successes = [frame for frame in stage_frames if frame["outcome_bucket"] == "success"]
        failures = [frame for frame in stage_frames if frame["outcome_bucket"] == "failure"][:per_stage_failure]
        # Stage 5/6 may have no failures in protected traces; include extra
        # successes so cross-stage coverage is still useful. Only draw from
        # success rows here; stage_frames can contain failures and would
        # otherwise duplicate a sparse failure row in the selected evidence.
        successes = stage_successes[:per_stage_success]
        if len(failures) < per_stage_failure:
            successes = stage_successes[: per_stage_success + (per_stage_failure - len(failures))]
        selected.extend(successes + failures)
    deduped = []
    seen_frame_ids: set[str] = set()
    for frame in selected:
        frame_id = str(frame.get("frame_id"))
        if frame_id in seen_frame_ids:
            continue
        seen_frame_ids.add(frame_id)
        deduped.append(frame)
    return deduped


def build_payload(requirements: dict[str, Any] | None = None) -> dict[str, Any]:
    requirements = requirements or _load(REQUIREMENTS)
    all_frames = []
    source_counts = {}
    for stage, spec in STAGE_ARTIFACTS.items():
        payload = _load(spec["path"])
        grouped = _packets_by_phase(payload)
        source_counts[stage] = len(grouped)
        for key, packets in grouped.items():
            if "playout_summary" not in packets:
                continue
            all_frames.append(
                _frame_from_group(
                    source_stage=stage,
                    label=spec["label"],
                    frame_family=spec["frame_family"],
                    source_artifact=spec["path"],
                    key=key,
                    packets=packets,
                )
            )
    frames = _select_balanced(all_frames)
    stage_counts = Counter(frame["source_stage"] for frame in frames)
    outcome_counts = Counter(frame["outcome_bucket"] for frame in frames)
    protected_min = int(
        requirements.get("acceptance_before_sequence_policy_benchmark", {}).get(
            "protected_stage4_5_6_frame_count_min",
            20,
        )
    )
    protected_met = len(frames) >= protected_min and all(stage_counts.get(stage, 0) > 0 for stage in STAGE_ARTIFACTS)
    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_replay_free_protected_window_extraction",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_cross_stage_plan_capsule_evidence_requirements_v0.json",
            *[spec["path"] for spec in STAGE_ARTIFACTS.values()],
        ],
        "source_group_counts": source_counts,
        "summary": {
            "frame_count": len(frames),
            "source_stage_counts": dict(stage_counts),
            "outcome_bucket_counts": dict(outcome_counts),
            "protected_stage4_5_6_frame_count_min": protected_min,
            "protected_cross_stage_evidence_met": protected_met,
            "selector_training_row_count": 0,
            "runtime_authorization_row_count": 0,
            "stage7_training_row_count": 0,
        },
        "frames": frames,
        "decision": {
            "status": (
                "protected_cross_stage_plan_window_evidence_extracted"
                if protected_met
                else "protected_cross_stage_plan_window_evidence_underpowered"
            ),
            "recommended_next_step": "refresh_sequence_policy_readiness_with_protected_plan_window_frames",
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# KRK Protected Plan-Window Frames v0",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        "Replay-free extraction of protected Stage 4/5/6 plan-window evidence from existing handoff packets. This is not runtime PlanCapsule behavior.",
        "",
        "## Summary",
        "",
        f"- frame_count: `{summary['frame_count']}`",
        f"- source_stage_counts: `{summary['source_stage_counts']}`",
        f"- outcome_bucket_counts: `{summary['outcome_bucket_counts']}`",
        f"- protected_cross_stage_evidence_met: `{summary['protected_cross_stage_evidence_met']}`",
        f"- selector_training_row_count: `{summary['selector_training_row_count']}`",
        f"- runtime_authorization_row_count: `{summary['runtime_authorization_row_count']}`",
        "",
        "## Boundary",
        "",
        "- These frames are non-causal replay-free evidence only.",
        "- They do not select moves, score candidates, route providers, promote Stage 7, or train Stage 8.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(json.dumps({
        "decision": payload["decision"]["status"],
        "frame_count": payload["summary"]["frame_count"],
        "source_stage_counts": payload["summary"]["source_stage_counts"],
    }, indent=2))


if __name__ == "__main__":
    main()
