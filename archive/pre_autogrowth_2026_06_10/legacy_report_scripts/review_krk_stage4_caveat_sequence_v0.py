#!/usr/bin/env python3
"""Review the single-state Stage 4 h40 caveat sequence failure."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STAGE4_EVAL = Path(
    "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/"
    "stage6_overlay_composed/stage4_wrong_tempo_overlay_300_seed7_h40_profile_bonus.json"
)
STAGE4_BASE = Path(
    "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/"
    "stage6_overlay_composed/stage4_wrong_tempo_stage5_base_control_300_seed7_h40_profile_bonus.json"
)
DISCOVERY = Path("reports/krk_stage4_failure_discovery_v0.json")
OUT_JSON = Path("reports/krk_stage4_caveat_sequence_review_v0.json")
OUT_MD = Path("reports/krk_stage4_caveat_sequence_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected object: {path}")
    return payload


def _failure_packets(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        packet
        for packet in payload.get("handoff_packets") or []
        if packet.get("phase") == "playout_summary" and packet.get("observed_outcome") == "max_plies"
    ]


def _packets_for(payload: dict[str, Any], fen: str, move: str) -> list[dict[str, Any]]:
    rows = []
    for packet in payload.get("handoff_packets") or []:
        evidence = packet.get("evidence_terms") or {}
        if evidence.get("fen") == fen and evidence.get("move") == move:
            rows.append(packet)
    return rows


def _phase_snapshot(packets: list[dict[str, Any]], phase: str) -> dict[str, Any]:
    for packet in packets:
        if packet.get("phase") != phase:
            continue
        evidence = packet.get("evidence_terms") or {}
        return {
            "phase": phase,
            "status": packet.get("status"),
            "observed_outcome": packet.get("observed_outcome"),
            "failed": packet.get("failed"),
            "achieved": packet.get("achieved"),
            "fen": evidence.get("fen"),
            "move": evidence.get("move"),
            "post_reply_fen": evidence.get("post_reply_fen"),
            "black_reply": evidence.get("black_reply"),
            "playout_result": evidence.get("playout_result"),
            "plies": evidence.get("plies"),
            "semantic_alignment_status": evidence.get("semantic_alignment_status"),
            "reward_confirmed": evidence.get("reward_confirmed"),
            "visible_fence_contract_confirmed": evidence.get("visible_fence_contract_confirmed"),
            "fence_survived_reply": evidence.get("fence_survived_reply"),
            "handoff_gap": evidence.get("handoff_gap"),
            "route_conflict": evidence.get("route_conflict"),
            "successor_selected_skill": evidence.get("successor_selected_skill"),
            "selected_skill_source": evidence.get("selected_skill_source"),
            "selected_successor_contract_met": evidence.get("selected_successor_contract_met"),
            "provider_selected_without_role_license": evidence.get("provider_selected_without_role_license"),
            "successor_best_score": evidence.get("successor_best_score"),
            "successor_second_score": evidence.get("successor_second_score"),
            "failure_classes": evidence.get("failure_classes"),
            "final_mate_in_one_available": evidence.get("final_mate_in_one_available"),
            "stagnation_summary_present": evidence.get("stagnation_summary") is not None,
        }
    return {"phase": phase, "missing": True}


def build_payload(
    stage4_eval: dict[str, Any] | None = None,
    stage4_base: dict[str, Any] | None = None,
    discovery: dict[str, Any] | None = None,
) -> dict[str, Any]:
    stage4_eval = stage4_eval or _load(STAGE4_EVAL)
    stage4_base = stage4_base or _load(STAGE4_BASE)
    discovery = discovery or _load(DISCOVERY)
    unique_rows = discovery.get("unique_failure_rows") or []
    target = unique_rows[0] if unique_rows else {}
    fen = str(target.get("fen") or "")
    move = str(target.get("selected_move") or "")
    packets = _packets_for(stage4_eval, fen, move)
    phase_counts = Counter((p.get("phase"), p.get("observed_outcome"), p.get("status")) for p in packets)
    base_failures = _failure_packets(stage4_base)
    overlay_failures = _failure_packets(stage4_eval)
    phase_snapshots = {
        phase: _phase_snapshot(packets, phase)
        for phase in ("post_own_move", "post_opponent_reply", "playout_summary")
    }
    post_reply = phase_snapshots["post_opponent_reply"]
    return {
        "schema_version": "krk_stage4_caveat_sequence_review.v0",
        "causal_status": "non_causal_sequence_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(STAGE4_EVAL), str(STAGE4_BASE), str(DISCOVERY)],
        "summary": {
            "target_state_id": target.get("state_id"),
            "target_fen": fen,
            "target_selected_move": move,
            "overlay_failure_packet_count": len(overlay_failures),
            "base_failure_packet_count": len(base_failures),
            "target_packet_count": len(packets),
            "target_phase_counts": {str(key): value for key, value in phase_counts.items()},
            "single_unique_failure": len(unique_rows) == 1,
            "base_control_reproduces_failure_count": len(base_failures) == len(overlay_failures),
            "selector_training_row_count": 0,
            "stage7_training_row_count": 0,
        },
        "phase_snapshots": phase_snapshots,
        "diagnosis": {
            "primary": "stage4_sequence_followup_gap_single_state",
            "support": [
                "all Stage 4 h40 failures collapse to one unique state/move",
                "same failure count reproduces in the paired Stage 5 base control",
                "post-own move confirms visible fence but fails local reward confirmation",
                "post-reply continuation selects stage0_basin by actuator score without a visible role license",
                "failure is max_plies after follow-up, not immediate illegal move or runtime mutation",
            ],
            "risk": [
                "the target is a repeated curriculum state, so selector labels are too narrow",
                "a direct state/move patch would violate the no exact-state runtime exception invariant",
                "a broad stage0 penalty would risk protected safe-preservation cases",
            ],
        },
        "recommended_next_options": [
            {
                "option": "stage4_sequence_candidate_review",
                "why": "Need to identify visible follow-up candidates after b8h8/a5a4 before any runtime change.",
                "causal_status": "non_causal_review_first",
            },
            {
                "option": "synthetic_stage4_contrast_generation",
                "why": "One repeated failure state is not enough for selector validation; generate stratified variants without hand-authoring policy.",
                "causal_status": "non_causal_data_design_first",
            },
            {
                "option": "keep_stage4_known_residual_guardrail",
                "why": "The caveat is isolated and non-regressive; selector work can stay blocked while broader KRK sequence work proceeds.",
                "causal_status": "no_runtime_change",
            },
        ],
        "decision": {
            "status": "stage4_caveat_sequence_followup_gap_review_ready",
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": "review_stage4_sequence_candidates_or_keep_as_known_residual",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Stage 4 Caveat Sequence Review v0",
        "",
        "Non-causal review of the single repeated Stage 4 h40 caveat failure.",
        "",
        "## Decision",
        "",
    ]
    for key, value in payload["decision"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Summary", ""])
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Phase Snapshots", ""])
    for phase, snapshot in payload["phase_snapshots"].items():
        lines.append(f"- `{phase}`: `{snapshot}`")
    lines.extend(["", "## Diagnosis", ""])
    lines.append(f"- primary: `{payload['diagnosis']['primary']}`")
    for item in payload["diagnosis"]["support"]:
        lines.append(f"- support: `{item}`")
    for item in payload["diagnosis"]["risk"]:
        lines.append(f"- risk: `{item}`")
    lines.extend(["", "## Recommended Next Options", ""])
    for item in payload["recommended_next_options"]:
        lines.append(f"- `{item['option']}`: {item['why']} (`{item['causal_status']}`)")
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
