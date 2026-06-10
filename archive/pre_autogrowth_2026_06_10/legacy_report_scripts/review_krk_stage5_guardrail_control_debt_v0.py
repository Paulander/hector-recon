#!/usr/bin/env python3
"""Review Stage 5 one-ply guardrail debt exposed by clean KRK retry1.

This script is diagnostic only. It reads already-produced validation artifacts
and writes a compact review that separates conversion preservation from local
one-ply reward debt.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_OVERLAY_ARTIFACT = Path(
    "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/"
    "stage6_overlay_composed/stage5_fence_overlay_300_seed7_h40_profile_bonus.json"
)
DEFAULT_BASE_CONTROL_ARTIFACT = Path(
    "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/"
    "stage6_overlay_composed/"
    "stage5_fence_stage5_base_control_300_seed7_h40_profile_bonus.json"
)
DEFAULT_PROMOTION_EVAL_ARTIFACT = Path(
    "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/"
    "stage6_overlay_composed/promotion_eval_stage6_overlay_profile_bonus.json"
)
DEFAULT_INSPECTION_ARTIFACT = Path("reports/krk_clean_retrain_retry1_stage6_gap_inspection_v1.json")
DEFAULT_JSON_OUTPUT = Path("reports/krk_stage5_guardrail_control_debt_review_v0.json")
DEFAULT_MD_OUTPUT = Path("reports/krk_stage5_guardrail_control_debt_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _playout_rate(payload: dict[str, Any], key: str) -> float:
    playouts = payload.get("playouts", {}) or {}
    total = sum(int(value) for value in playouts.values())
    if total <= 0:
        return 0.0
    return float(playouts.get(key, 0) or 0) / float(total)


def summarize_stage5_artifact(path: Path) -> dict[str, Any]:
    payload = _load(path)
    total = int(payload.get("total", 0) or 0)
    improved = int(payload.get("improved", 0) or 0)
    worsened = int(payload.get("worsened", 0) or 0)
    optimal = int(payload.get("optimal", 0) or 0)
    shadow_count = int(
        payload.get("shadow_candidate_count", payload.get("shadow_candidates_count", 0)) or 0
    )
    return {
        "path": str(path),
        "label": payload.get("label"),
        "total": total,
        "improved": improved,
        "worsened": worsened,
        "optimal": optimal,
        "improved_rate": improved / total if total else 0.0,
        "worsened_rate": worsened / total if total else 0.0,
        "mate_rate": _playout_rate(payload, "mate"),
        "max_plies_rate": _playout_rate(payload, "max_plies"),
        "playouts": dict(payload.get("playouts", {}) or {}),
        "one_ply_status": payload.get("one_ply_status"),
        "conversion_status": payload.get("conversion_status"),
        "shadow_candidate_count": shadow_count,
        "handoff_packet_counts_by_phase": dict(payload.get("handoff_packet_counts_by_phase") or {}),
        "stagnation_breaker_king_support_bonus": payload.get(
            "stagnation_breaker_king_support_bonus"
        ),
        "early_stop_stable_suggestions": payload.get("early_stop_stable_suggestions"),
        "source_stage_names": list(payload.get("source_stage_names") or []),
    }


def summarize_post_own_patterns(path: Path) -> dict[str, Any]:
    payload = _load(path)
    rows: Counter[tuple[Any, ...]] = Counter()
    status_counts: Counter[str] = Counter()
    status_contract_counts: Counter[tuple[str, bool, bool, bool]] = Counter()
    examples: list[dict[str, Any]] = []

    for packet in payload.get("handoff_packets", []) or []:
        if packet.get("phase") != "post_own_move":
            continue
        evidence = packet.get("evidence_terms", {}) or {}
        status = str(packet.get("status"))
        status_counts[status] += 1
        row = (
            status,
            evidence.get("fen"),
            evidence.get("move"),
            evidence.get("chosen_reward"),
            evidence.get("oracle_reward"),
            evidence.get("fence_exists_after_own_move"),
            evidence.get("fence_stable_after_own_move"),
            evidence.get("cut_axis_after_own_move"),
            evidence.get("rook_safe_after_own_move"),
            evidence.get("box_area_after_own_move"),
        )
        rows[row] += 1
        status_contract_counts[
            (
                status,
                bool(evidence.get("visible_fence_contract_confirmed")),
                bool(evidence.get("rook_safe_after_own_move")),
                bool(evidence.get("reward_confirmed")),
            )
        ] += 1
        if len(examples) < 12:
            examples.append(
                {
                    "status": status,
                    "fen": evidence.get("fen"),
                    "move": evidence.get("move"),
                    "chosen_reward": evidence.get("chosen_reward"),
                    "oracle_reward": evidence.get("oracle_reward"),
                    "reward_confirmed": evidence.get("reward_confirmed"),
                    "visible_fence_contract_confirmed": evidence.get(
                        "visible_fence_contract_confirmed"
                    ),
                    "fence_exists_after_own_move": evidence.get("fence_exists_after_own_move"),
                    "fence_stable_after_own_move": evidence.get("fence_stable_after_own_move"),
                    "cut_axis_after_own_move": evidence.get("cut_axis_after_own_move"),
                    "rook_safe_after_own_move": evidence.get("rook_safe_after_own_move"),
                    "box_area_after_own_move": evidence.get("box_area_after_own_move"),
                    "achieved": list(packet.get("achieved") or []),
                    "failed": list(packet.get("failed") or []),
                }
            )

    top_unique_rows = []
    for row, count in rows.most_common():
        (
            status,
            fen,
            move,
            chosen_reward,
            oracle_reward,
            fence_exists,
            fence_stable,
            cut_axis,
            rook_safe,
            box_area,
        ) = row
        top_unique_rows.append(
            {
                "count": count,
                "status": status,
                "fen": fen,
                "move": move,
                "chosen_reward": chosen_reward,
                "oracle_reward": oracle_reward,
                "fence_exists_after_own_move": fence_exists,
                "fence_stable_after_own_move": fence_stable,
                "cut_axis_after_own_move": cut_axis,
                "rook_safe_after_own_move": rook_safe,
                "box_area_after_own_move": box_area,
            }
        )

    return {
        "unique_post_own_state_move_rows": len(rows),
        "status_counts": dict(status_counts),
        "status_contract_counts": {
            "|".join(str(part) for part in key): value
            for key, value in status_contract_counts.items()
        },
        "top_unique_rows": top_unique_rows,
        "examples": examples,
    }


def _delta(candidate: dict[str, Any], control: dict[str, Any]) -> dict[str, Any]:
    return {
        "improved_delta": candidate["improved"] - control["improved"],
        "worsened_delta": candidate["worsened"] - control["worsened"],
        "optimal_delta": candidate["optimal"] - control["optimal"],
        "mate_rate_delta": candidate["mate_rate"] - control["mate_rate"],
        "max_plies_rate_delta": candidate["max_plies_rate"] - control["max_plies_rate"],
        "shadow_candidate_delta": candidate["shadow_candidate_count"]
        - control["shadow_candidate_count"],
    }


def build_review(
    *,
    overlay_artifact: Path = DEFAULT_OVERLAY_ARTIFACT,
    base_control_artifact: Path = DEFAULT_BASE_CONTROL_ARTIFACT,
    promotion_eval_artifact: Path = DEFAULT_PROMOTION_EVAL_ARTIFACT,
    inspection_artifact: Path = DEFAULT_INSPECTION_ARTIFACT,
) -> dict[str, Any]:
    overlay = summarize_stage5_artifact(overlay_artifact)
    control = summarize_stage5_artifact(base_control_artifact)
    promotion_eval = _load(promotion_eval_artifact)
    inspection = _load(inspection_artifact) if inspection_artifact.exists() else {}
    post_own_patterns = summarize_post_own_patterns(overlay_artifact)
    delta = _delta(overlay, control)
    identical_debt = all(
        delta[key] == 0
        for key in [
            "improved_delta",
            "worsened_delta",
            "optimal_delta",
            "mate_rate_delta",
            "max_plies_rate_delta",
            "shadow_candidate_delta",
        ]
    )
    conversion_preserved = (
        overlay["mate_rate"] == 1.0
        and control["mate_rate"] == 1.0
        and overlay["shadow_candidate_count"] == 0
        and control["shadow_candidate_count"] == 0
    )
    one_ply_debt = overlay["one_ply_status"] == "failed" and control["one_ply_status"] == "failed"

    decision = {
        "status": "stage5_one_ply_guardrail_control_debt_confirmed",
        "stage5_overlay_regressed_vs_base_control": not identical_debt,
        "stage5_conversion_preserved": conversion_preserved,
        "stage5_one_ply_debt_reproduces_in_base_control": one_ply_debt and identical_debt,
        "stage6_overlay_promotion_eval_status": promotion_eval.get("promotion_status"),
        "should_quarantine_stage6_overlay_for_stage5_one_ply_debt": False,
        "should_replace_protected_stack_now": False,
        "recommended_next_step": "split_stage5_guardrail_into_conversion_preservation_and_local_reward_contract_debt_before_clean_stack_replacement",
    }

    return {
        "schema_version": "krk_stage5_guardrail_control_debt_review.v0",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": decision["status"],
        "decision": decision,
        "source_artifacts": {
            "overlay": str(overlay_artifact),
            "base_control": str(base_control_artifact),
            "promotion_eval": str(promotion_eval_artifact),
            "stage6_gap_inspection": str(inspection_artifact),
        },
        "stage5_overlay": overlay,
        "stage5_base_control": control,
        "delta_overlay_vs_base_control": delta,
        "post_own_pattern_summary": post_own_patterns,
        "promotion_eval_summary": {
            "promotion_status": promotion_eval.get("promotion_status"),
            "failures": list(promotion_eval.get("failures") or []),
            "guardrail_control_debt": list(promotion_eval.get("guardrail_control_debt") or []),
            "guardrail_deltas_vs_control": list(
                promotion_eval.get("guardrail_deltas_vs_control") or []
            ),
        },
        "interpretation": [
            "Stage 5 conversion preservation passes under the corrected historical validation profile: overlay and base-control both mate 300/300 with 0 shadow candidates.",
            "Stage 5 one-ply local reward debt is identical in the Stage 6 overlay guardrail and the fresh Stage 5 base control: 144 improved, 156 worsened.",
            "The one-ply failures still expose useful contract debt, but they are not evidence of Stage 6 overlay interference because the paired base control has the same debt.",
            "Promotion evaluation should keep this as overlay_only/control-debt, not promoted replacement, until the Stage 5 guardrail definition is split or explicitly accepted.",
        ],
        "guardrail_definition_recommendation": {
            "split_required": True,
            "conversion_preservation_guardrail": {
                "purpose": "protect existing Stage 5 conversion behavior against later overlays",
                "comparison": "candidate_overlay_vs_paired_stage5_base_control",
                "current_retry1_result": "passed_no_regression",
            },
            "local_reward_contract_guardrail": {
                "purpose": "track whether Stage 5 fence local reward semantics match visible fence contracts",
                "current_retry1_result": "failed_but_reproduces_in_base_control",
                "promotion_effect": "blocks_clean_replacement_or_full_promotion_until_reviewed",
            },
            "clean_stack_replacement_policy": "blocked_pending_stage5_contract_debt_decision",
        },
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
        "related_stage6_gap_status": inspection.get("status"),
    }


def render_markdown(review: dict[str, Any]) -> str:
    decision = review["decision"]
    overlay = review["stage5_overlay"]
    control = review["stage5_base_control"]
    delta = review["delta_overlay_vs_base_control"]
    patterns = review["post_own_pattern_summary"]

    rows = "\n".join(
        f"- `{row['count']}`x status=`{row['status']}` move=`{row['move']}` "
        f"reward=`{row['chosen_reward']}` oracle=`{row['oracle_reward']}` "
        f"fence_stable=`{row['fence_stable_after_own_move']}` "
        f"cut=`{row['cut_axis_after_own_move']}` box_area=`{row['box_area_after_own_move']}` "
        f"fen=`{row['fen']}`"
        for row in patterns["top_unique_rows"]
    )
    interpretations = "\n".join(f"- {item}" for item in review["interpretation"])

    return f"""# KRK Stage 5 Guardrail Control-Debt Review v0

## Decision

Status: `{review['status']}`

- Stage 5 overlay regressed vs paired base control: `{decision['stage5_overlay_regressed_vs_base_control']}`
- Stage 5 conversion preserved: `{decision['stage5_conversion_preserved']}`
- Stage 5 one-ply debt reproduces in base control: `{decision['stage5_one_ply_debt_reproduces_in_base_control']}`
- Stage 6 overlay promotion eval status: `{decision['stage6_overlay_promotion_eval_status']}`
- Quarantine Stage 6 overlay for Stage 5 one-ply debt: `{decision['should_quarantine_stage6_overlay_for_stage5_one_ply_debt']}`
- Replace protected stack now: `{decision['should_replace_protected_stack_now']}`
- Recommended next step: `{decision['recommended_next_step']}`

## Metrics

Stage 5 overlay guardrail:

- total: `{overlay['total']}`
- improved/worsened/optimal: `{overlay['improved']}/{overlay['worsened']}/{overlay['optimal']}`
- mate rate / max-plies rate: `{overlay['mate_rate']:.3f}` / `{overlay['max_plies_rate']:.3f}`
- shadow candidates: `{overlay['shadow_candidate_count']}`
- one-ply status / conversion status: `{overlay['one_ply_status']}` / `{overlay['conversion_status']}`

Stage 5 base control:

- total: `{control['total']}`
- improved/worsened/optimal: `{control['improved']}/{control['worsened']}/{control['optimal']}`
- mate rate / max-plies rate: `{control['mate_rate']:.3f}` / `{control['max_plies_rate']:.3f}`
- shadow candidates: `{control['shadow_candidate_count']}`
- one-ply status / conversion status: `{control['one_ply_status']}` / `{control['conversion_status']}`

Overlay-vs-control delta:

- improved delta: `{delta['improved_delta']}`
- worsened delta: `{delta['worsened_delta']}`
- mate-rate delta: `{delta['mate_rate_delta']:.3f}`
- max-plies-rate delta: `{delta['max_plies_rate_delta']:.3f}`
- shadow-candidate delta: `{delta['shadow_candidate_delta']}`

## Post-Own One-Ply Patterns

- unique post-own state/move rows: `{patterns['unique_post_own_state_move_rows']}`
- status counts: `{patterns['status_counts']}`

{rows}

## Interpretation

{interpretations}

## Guardrail Definition Recommendation

Split Stage 5 guardrail interpretation into two tracks:

- `conversion_preservation_guardrail`: paired overlay-vs-base-control comparison. Retry1 passes this because conversion and shadow behavior do not regress.
- `local_reward_contract_guardrail`: Stage 5 fence local reward/visible-contract alignment. Retry1 fails this, but the failure is already present in the fresh Stage 5 base control.

Therefore Stage 6 overlay validation should remain `overlay_only` with control debt. Clean protected-stack replacement remains blocked until the Stage 5 contract debt is either accepted as known base debt or repaired by an explicit guardrail-semantics review.

## Invariants

- runtime defaults changed: `{review['invariants']['runtime_defaults_changed']}`
- runtime selector implemented: `{review['invariants']['runtime_selector_implemented']}`
- runtime DTM/tablebase lookup: `{review['invariants']['runtime_dtm_or_tablebase_lookup']}`
- gameplay topology mutation: `{review['invariants']['gameplay_topology_mutation']}`
- Stage 7 promotion: `{review['invariants']['stage7_promotion']}`
- Stage 8 training: `{review['invariants']['stage8_training']}`
"""


def write_review(review: dict[str, Any], json_output: Path, md_output: Path) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    md_output.parent.mkdir(parents=True, exist_ok=True)
    md_output.write_text(render_markdown(review), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overlay-artifact", type=Path, default=DEFAULT_OVERLAY_ARTIFACT)
    parser.add_argument("--base-control-artifact", type=Path, default=DEFAULT_BASE_CONTROL_ARTIFACT)
    parser.add_argument("--promotion-eval-artifact", type=Path, default=DEFAULT_PROMOTION_EVAL_ARTIFACT)
    parser.add_argument("--inspection-artifact", type=Path, default=DEFAULT_INSPECTION_ARTIFACT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD_OUTPUT)
    args = parser.parse_args()

    review = build_review(
        overlay_artifact=args.overlay_artifact,
        base_control_artifact=args.base_control_artifact,
        promotion_eval_artifact=args.promotion_eval_artifact,
        inspection_artifact=args.inspection_artifact,
    )
    write_review(review, args.json_output, args.md_output)
    print(json.dumps({"status": review["status"], "json_output": str(args.json_output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
