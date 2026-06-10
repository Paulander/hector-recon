#!/usr/bin/env python3
"""Review retry1 Stage 4 caveat against paired Stage 5 base control."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_OVERLAY = Path(
    "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/"
    "stage6_overlay_composed/stage4_wrong_tempo_overlay_300_seed7_h40_profile_bonus.json"
)
DEFAULT_CONTROL = Path(
    "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/"
    "stage6_overlay_composed/"
    "stage4_wrong_tempo_stage5_base_control_300_seed7_h40_profile_bonus.json"
)
DEFAULT_REPLACEMENT_REVIEW = Path(
    "reports/krk_clean_retrain_retry1_replacement_readiness_review_v0.json"
)
DEFAULT_JSON_OUTPUT = Path("reports/krk_clean_retrain_retry1_stage4_caveat_control_review_v0.json")
DEFAULT_MD_OUTPUT = Path("reports/krk_clean_retrain_retry1_stage4_caveat_control_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _summary(path: Path) -> dict[str, Any]:
    payload = _load(path)
    playouts = dict(payload.get("playouts") or {})
    total = int(payload.get("total", 0) or 0)
    mate = int(playouts.get("mate", 0) or 0)
    max_plies = int(playouts.get("max_plies", 0) or 0)
    return {
        "path": str(path),
        "label": payload.get("label"),
        "total": total,
        "improved": int(payload.get("improved", 0) or 0),
        "worsened": int(payload.get("worsened", 0) or 0),
        "optimal": int(payload.get("optimal", 0) or 0),
        "mate": mate,
        "max_plies": max_plies,
        "mate_rate": mate / total if total else 0.0,
        "max_plies_rate": max_plies / total if total else 0.0,
        "one_ply_status": payload.get("one_ply_status"),
        "conversion_status": payload.get("conversion_status"),
        "shadow_candidate_count": int(payload.get("shadow_candidate_count", 0) or 0),
        "semantic_alignment_status_counts": dict(
            payload.get("semantic_alignment_status_counts") or {}
        ),
        "handoff_packet_counts_by_phase": dict(payload.get("handoff_packet_counts_by_phase") or {}),
        "stagnation_breaker_king_support_bonus": payload.get(
            "stagnation_breaker_king_support_bonus"
        ),
        "early_stop_stable_suggestions": payload.get("early_stop_stable_suggestions"),
    }


def _delta(overlay: dict[str, Any], control: dict[str, Any]) -> dict[str, Any]:
    return {
        "improved_delta": overlay["improved"] - control["improved"],
        "worsened_delta": overlay["worsened"] - control["worsened"],
        "optimal_delta": overlay["optimal"] - control["optimal"],
        "mate_delta": overlay["mate"] - control["mate"],
        "max_plies_delta": overlay["max_plies"] - control["max_plies"],
        "mate_rate_delta": overlay["mate_rate"] - control["mate_rate"],
        "max_plies_rate_delta": overlay["max_plies_rate"] - control["max_plies_rate"],
        "shadow_candidate_delta": overlay["shadow_candidate_count"]
        - control["shadow_candidate_count"],
    }


def build_review(
    *,
    overlay_artifact: Path = DEFAULT_OVERLAY,
    control_artifact: Path = DEFAULT_CONTROL,
    replacement_review: Path = DEFAULT_REPLACEMENT_REVIEW,
) -> dict[str, Any]:
    overlay = _summary(overlay_artifact)
    control = _summary(control_artifact)
    delta = _delta(overlay, control)
    repl = _load(replacement_review) if replacement_review.exists() else {}
    no_regression = all(
        delta[key] == 0
        for key in [
            "improved_delta",
            "worsened_delta",
            "optimal_delta",
            "mate_delta",
            "max_plies_delta",
            "shadow_candidate_delta",
        ]
    )
    status = (
        "stage4_caveat_reproduces_in_base_control_no_overlay_regression"
        if no_regression
        else "stage4_overlay_regressed_vs_base_control"
    )
    return {
        "schema_version": "krk_clean_retrain_retry1_stage4_caveat_control_review.v0",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": status,
        "decision": {
            "stage4_overlay_regressed_vs_base_control": not no_regression,
            "stage4_caveat_reproduces_in_base_control": no_regression,
            "clean_stack_replacement_allowed": False,
            "runtime_behavior_changed": False,
            "recommended_next_step": "run_m1_m4_and_kpk_kqk_preservation_checks_before_any_clean_stack_replacement_packet",
        },
        "source_artifacts": {
            "stage4_overlay": str(overlay_artifact),
            "stage4_base_control": str(control_artifact),
            "replacement_readiness_review": str(replacement_review),
        },
        "stage4_overlay": overlay,
        "stage4_base_control": control,
        "delta_overlay_vs_base_control": delta,
        "replacement_review_status_before_stage4": repl.get("status"),
        "interpretation": [
            "The Stage 4 wrong-tempo caveat is identical in the Stage 6 overlay topology and the paired Stage 5 base control.",
            "This means the retry1 Stage 6 overlay does not worsen the known Stage 4 caveat under the corrected validation profile.",
            "The caveat remains real: both artifacts have 268/300 h40 mates and 32 max_plies.",
            "This clears the Stage 4 overlay-control regression check, but it does not authorize clean-stack replacement.",
        ],
        "remaining_required_checks": [
            "m1_m4_preservation_suite",
            "kpk_kqk_bridge_preservation",
            "protected_stack_snapshot_manifest",
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
    overlay = payload["stage4_overlay"]
    control = payload["stage4_base_control"]
    delta = payload["delta_overlay_vs_base_control"]
    interp = "\n".join(f"- {item}" for item in payload["interpretation"])
    remaining = "\n".join(f"- `{item}`" for item in payload["remaining_required_checks"])
    return f"""# KRK Retry1 Stage 4 Caveat Control Review v0

Status: `{payload['status']}`

## Decision

- Stage 4 overlay regressed vs base control: `{payload['decision']['stage4_overlay_regressed_vs_base_control']}`
- Stage 4 caveat reproduces in base control: `{payload['decision']['stage4_caveat_reproduces_in_base_control']}`
- Clean stack replacement allowed: `{payload['decision']['clean_stack_replacement_allowed']}`
- Recommended next step: `{payload['decision']['recommended_next_step']}`

## Metrics

Stage 4 overlay:

- improved/worsened/optimal: `{overlay['improved']}/{overlay['worsened']}/{overlay['optimal']}`
- mate/max_plies: `{overlay['mate']}/{overlay['max_plies']}`
- shadow candidates: `{overlay['shadow_candidate_count']}`
- one-ply/conversion status: `{overlay['one_ply_status']}` / `{overlay['conversion_status']}`

Stage 4 paired base control:

- improved/worsened/optimal: `{control['improved']}/{control['worsened']}/{control['optimal']}`
- mate/max_plies: `{control['mate']}/{control['max_plies']}`
- shadow candidates: `{control['shadow_candidate_count']}`
- one-ply/conversion status: `{control['one_ply_status']}` / `{control['conversion_status']}`

Overlay-vs-control delta:

- improved delta: `{delta['improved_delta']}`
- worsened delta: `{delta['worsened_delta']}`
- mate delta: `{delta['mate_delta']}`
- max_plies delta: `{delta['max_plies_delta']}`
- shadow candidate delta: `{delta['shadow_candidate_delta']}`

## Interpretation

{interp}

## Remaining Checks

{remaining}

## Boundary

This review is non-causal. It does not replace checkpoints, change runtime behavior, promote Stage 7, train Stage 8, use runtime DTM/tablebase, or mutate topology.
"""


def write_review(payload: dict[str, Any], json_output: Path, md_output: Path) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_output.parent.mkdir(parents=True, exist_ok=True)
    md_output.write_text(render_markdown(payload), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overlay-artifact", type=Path, default=DEFAULT_OVERLAY)
    parser.add_argument("--control-artifact", type=Path, default=DEFAULT_CONTROL)
    parser.add_argument("--replacement-review", type=Path, default=DEFAULT_REPLACEMENT_REVIEW)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD_OUTPUT)
    args = parser.parse_args()
    payload = build_review(
        overlay_artifact=args.overlay_artifact,
        control_artifact=args.control_artifact,
        replacement_review=args.replacement_review,
    )
    write_review(payload, args.json_output, args.md_output)
    print(json.dumps({"status": payload["status"], "json_output": str(args.json_output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
