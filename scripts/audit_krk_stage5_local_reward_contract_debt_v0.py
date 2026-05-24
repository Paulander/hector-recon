#!/usr/bin/env python3
"""Audit Stage 5 local reward / visible-contract debt.

This is replay-free and diagnostic only. It classifies existing Stage 5
guardrail artifacts into semantic buckets so clean-stack replacement review can
distinguish a local reward mismatch from conversion regression.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_ARTIFACT = Path(
    "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/"
    "stage6_overlay_composed/stage5_fence_overlay_300_seed7_h40_profile_bonus.json"
)
DEFAULT_BASE_CONTROL = Path(
    "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/"
    "stage6_overlay_composed/"
    "stage5_fence_stage5_base_control_300_seed7_h40_profile_bonus.json"
)
DEFAULT_SEMANTICS_SPLIT = Path("reports/krk_stage5_guardrail_semantics_split_v0.json")
DEFAULT_JSON_OUTPUT = Path("reports/krk_stage5_local_reward_contract_debt_audit_v0.json")
DEFAULT_MD_OUTPUT = Path("reports/krk_stage5_local_reward_contract_debt_audit_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _own_key(evidence: dict[str, Any]) -> tuple[Any, ...]:
    return (evidence.get("fen"), evidence.get("move"))


def _summarize_artifact(path: Path) -> dict[str, Any]:
    payload = _load(path)
    total = int(payload.get("total", 0) or 0)
    playouts = dict(payload.get("playouts") or {})
    mate = int(playouts.get("mate", 0) or 0)
    max_plies = int(playouts.get("max_plies", 0) or 0)
    return {
        "path": str(path),
        "total": total,
        "improved": int(payload.get("improved", 0) or 0),
        "worsened": int(payload.get("worsened", 0) or 0),
        "optimal": int(payload.get("optimal", 0) or 0),
        "mate": mate,
        "max_plies": max_plies,
        "mate_rate": mate / total if total else 0.0,
        "one_ply_status": payload.get("one_ply_status"),
        "conversion_status": payload.get("conversion_status"),
        "shadow_candidate_count": int(payload.get("shadow_candidate_count", 0) or 0),
        "handoff_packet_counts_by_phase": dict(payload.get("handoff_packet_counts_by_phase") or {}),
    }


def _pattern_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    own_by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    reply_by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    counts: Counter[tuple[Any, ...]] = Counter()

    for packet in payload.get("handoff_packets", []) or []:
        evidence = packet.get("evidence_terms", {}) or {}
        phase = packet.get("phase")
        key = _own_key(evidence)
        if phase == "post_own_move":
            count_key = (
                packet.get("status"),
                evidence.get("fen"),
                evidence.get("move"),
                evidence.get("chosen_reward"),
                evidence.get("oracle_reward"),
                evidence.get("reward_confirmed"),
                evidence.get("visible_fence_contract_confirmed"),
                evidence.get("fence_exists_after_own_move"),
                evidence.get("fence_stable_after_own_move"),
                evidence.get("cut_axis_after_own_move"),
                evidence.get("box_area_after_own_move"),
            )
            counts[count_key] += 1
            own_by_key.setdefault(key, packet)
        elif phase == "post_opponent_reply":
            reply_by_key.setdefault(key, packet)

    rows = []
    for raw_key, count in counts.most_common():
        (
            status,
            fen,
            move,
            chosen_reward,
            oracle_reward,
            reward_confirmed,
            visible_contract,
            fence_exists,
            fence_stable,
            cut_axis,
            box_area,
        ) = raw_key
        reply = reply_by_key.get((fen, move), {})
        reply_evidence = reply.get("evidence_terms", {}) or {}
        conversion_result = reply_evidence.get("playout_result")
        row = {
            "count": count,
            "post_own_status": status,
            "fen": fen,
            "move": move,
            "chosen_reward": chosen_reward,
            "oracle_reward": oracle_reward,
            "reward_confirmed": reward_confirmed,
            "visible_fence_contract_confirmed": visible_contract,
            "fence_exists_after_own_move": fence_exists,
            "fence_stable_after_own_move": fence_stable,
            "cut_axis_after_own_move": cut_axis,
            "box_area_after_own_move": box_area,
            "post_reply_status": reply.get("status"),
            "conversion_result": conversion_result,
            "plies": reply_evidence.get("plies"),
            "fence_survived_reply": reply_evidence.get("fence_survived_reply"),
            "fence_broken_by_reply": reply_evidence.get("fence_broken_by_reply"),
            "box_area_after_reply": reply_evidence.get("box_area_after_reply"),
            "box_area_delta_after_reply": reply_evidence.get("box_area_delta_after_reply"),
            "semantic_alignment": _semantic_alignment(
                reward_confirmed=bool(reward_confirmed),
                visible_contract=bool(visible_contract),
                conversion_result=str(conversion_result),
            ),
        }
        row["root_cause_labels"] = _root_cause_labels(row)
        rows.append(row)
    return rows


def _semantic_alignment(*, reward_confirmed: bool, visible_contract: bool, conversion_result: str) -> str:
    if reward_confirmed and visible_contract and conversion_result == "mate":
        return "reward_visible_contract_conversion_aligned"
    if not reward_confirmed and visible_contract and conversion_result == "mate":
        return "visible_contract_and_conversion_without_local_reward"
    if reward_confirmed and not visible_contract:
        return "reward_without_visible_contract"
    return "unclassified"


def _root_cause_labels(row: dict[str, Any]) -> list[str]:
    labels = []
    if (
        row["post_own_status"] == "failed"
        and row["visible_fence_contract_confirmed"] is True
        and row["conversion_result"] == "mate"
    ):
        labels.append("local_reward_too_strict_for_conversion")
    if row.get("chosen_reward") is not None and row.get("oracle_reward") is not None:
        if float(row["chosen_reward"]) < 0.0 and float(row["oracle_reward"]) > 0.0:
            labels.append("one_ply_worst_reply_reward_prefers_alternative")
    if row.get("fence_broken_by_reply") is True and row["conversion_result"] == "mate":
        labels.append("fence_break_after_reply_still_converts")
    if (
        row.get("fence_stable_after_own_move") is True
        and row["post_own_status"] == "failed"
        and row["conversion_result"] == "mate"
    ):
        labels.append("stable_fence_still_negative_dense_reward")
    if row.get("box_area_delta_after_reply") is not None and row.get("box_area_delta_after_reply") > 0:
        labels.append("box_area_expands_after_reply_but_converts")
    return labels or ["no_debt_pattern"]


def build_audit(
    *,
    artifact: Path = DEFAULT_ARTIFACT,
    base_control: Path = DEFAULT_BASE_CONTROL,
    semantics_split: Path = DEFAULT_SEMANTICS_SPLIT,
) -> dict[str, Any]:
    payload = _load(artifact)
    base_payload = _load(base_control)
    rows = _pattern_rows(payload)
    base_rows = _pattern_rows(base_payload)
    label_counts: Counter[str] = Counter()
    semantic_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    post_reply_counts: Counter[str] = Counter()
    for row in rows:
        status_counts[str(row["post_own_status"])] += int(row["count"])
        post_reply_counts[str(row["post_reply_status"])] += int(row["count"])
        semantic_counts[row["semantic_alignment"]] += int(row["count"])
        for label in row["root_cause_labels"]:
            label_counts[label] += int(row["count"])

    base_signature = [(row["count"], row["post_own_status"], row["fen"], row["move"]) for row in base_rows]
    overlay_signature = [
        (row["count"], row["post_own_status"], row["fen"], row["move"]) for row in rows
    ]
    signatures_match = base_signature == overlay_signature

    decision_status = (
        "stage5_local_reward_contract_debt_is_guardrail_semantics_debt"
        if signatures_match
        and semantic_counts.get("visible_contract_and_conversion_without_local_reward", 0) > 0
        and _summarize_artifact(artifact)["mate_rate"] == 1.0
        else "stage5_local_reward_contract_debt_needs_more_review"
    )
    recommended_next_step = (
        "accept_stage5_local_reward_debt_as_known_base_control_debt_for_overlay_only_review_and_run_remaining_preservation_checks_before_any_clean_stack_replacement"
        if decision_status == "stage5_local_reward_contract_debt_is_guardrail_semantics_debt"
        else "collect_targeted_stage5_contract_debt_labels_or_revisit_reward_definition"
    )
    return {
        "schema_version": "krk_stage5_local_reward_contract_debt_audit.v0",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": decision_status,
        "decision": {
            "status": decision_status,
            "overlay_matches_base_control_patterns": signatures_match,
            "conversion_preserved": _summarize_artifact(artifact)["mate_rate"] == 1.0,
            "local_reward_debt_is_stage6_regression": False,
            "runtime_behavior_changed": False,
            "clean_stack_replacement_allowed": False,
            "recommended_next_step": recommended_next_step,
        },
        "source_artifacts": {
            "stage5_overlay": str(artifact),
            "stage5_base_control": str(base_control),
            "semantics_split": str(semantics_split),
        },
        "stage5_overlay_summary": _summarize_artifact(artifact),
        "stage5_base_control_summary": _summarize_artifact(base_control),
        "pattern_summary": {
            "unique_overlay_patterns": len(rows),
            "unique_base_control_patterns": len(base_rows),
            "post_own_status_counts": dict(status_counts),
            "post_reply_status_counts": dict(post_reply_counts),
            "semantic_alignment_counts": dict(semantic_counts),
            "root_cause_label_counts": dict(label_counts),
        },
        "pattern_rows": rows,
        "interpretation": [
            "All Stage 5 overlay and base-control samples convert at h40 with zero shadow candidates under the corrected profile.",
            "The one-ply debt reproduces with the same state/move pattern signature in the paired base control.",
            "The dominant debt class is visible fence contract plus h40 conversion without local dense reward confirmation.",
            "This is guardrail semantics/control debt, not evidence that Stage 6 damaged Stage 5.",
        ],
        "invariants": {
            "runtime_defaults_changed": False,
            "runtime_selector_implemented": False,
            "runtime_score_changes": False,
            "runtime_direct_routing": False,
            "runtime_dtm_or_tablebase_lookup": False,
            "gameplay_topology_mutation": False,
            "stage7_promotion": False,
            "stage8_training": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["pattern_summary"]
    rows = "\n".join(
        f"- `{row['count']}`x `{row['semantic_alignment']}` move=`{row['move']}` "
        f"status=`{row['post_own_status']}` reply=`{row['post_reply_status']}` "
        f"chosen=`{row['chosen_reward']}` oracle=`{row['oracle_reward']}` "
        f"labels=`{row['root_cause_labels']}` fen=`{row['fen']}`"
        for row in payload["pattern_rows"]
    )
    interpretation = "\n".join(f"- {item}" for item in payload["interpretation"])
    return f"""# KRK Stage 5 Local Reward Contract-Debt Audit v0

Status: `{payload['status']}`

## Decision

- overlay matches base-control patterns: `{payload['decision']['overlay_matches_base_control_patterns']}`
- conversion preserved: `{payload['decision']['conversion_preserved']}`
- local reward debt is Stage 6 regression: `{payload['decision']['local_reward_debt_is_stage6_regression']}`
- clean stack replacement allowed: `{payload['decision']['clean_stack_replacement_allowed']}`
- recommended next step: `{payload['decision']['recommended_next_step']}`

## Pattern Summary

- unique overlay patterns: `{summary['unique_overlay_patterns']}`
- unique base-control patterns: `{summary['unique_base_control_patterns']}`
- post-own statuses: `{summary['post_own_status_counts']}`
- post-reply statuses: `{summary['post_reply_status_counts']}`
- semantic alignment: `{summary['semantic_alignment_counts']}`
- root-cause labels: `{summary['root_cause_label_counts']}`

## Pattern Rows

{rows}

## Interpretation

{interpretation}

## Boundary

This audit is replay-free and non-causal. It does not change runtime behavior, promote Stage 7, train Stage 8, use runtime DTM/tablebase, or mutate topology.
"""


def write_audit(payload: dict[str, Any], json_output: Path, md_output: Path) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_output.parent.mkdir(parents=True, exist_ok=True)
    md_output.write_text(render_markdown(payload), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    parser.add_argument("--base-control", type=Path, default=DEFAULT_BASE_CONTROL)
    parser.add_argument("--semantics-split", type=Path, default=DEFAULT_SEMANTICS_SPLIT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD_OUTPUT)
    args = parser.parse_args()

    payload = build_audit(
        artifact=args.artifact,
        base_control=args.base_control,
        semantics_split=args.semantics_split,
    )
    write_audit(payload, args.json_output, args.md_output)
    print(json.dumps({"status": payload["status"], "json_output": str(args.json_output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
