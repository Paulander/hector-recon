#!/usr/bin/env python3
"""Run an explicit Stage 7 challenge probe for the KRK strategy-arbiter sandbox."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.test_krk_landmark_progress import (  # noqa: E402
    COMPOSITION_PROFILE_HANDOFF_V1,
    evaluate_landmark_progress,
)


TOPOLOGY = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json"
)
OUT_JSON = Path("reports/krk_strategy_arbiter_stage7_challenge_probe_v1.json")
OUT_MD = Path("reports/krk_strategy_arbiter_stage7_challenge_probe_v1.md")


def _compact(stats: dict[str, Any]) -> dict[str, Any]:
    return {
        "total": stats.get("total"),
        "no_move": stats.get("no_move"),
        "improved": stats.get("improved"),
        "worsened": stats.get("worsened"),
        "optimal": stats.get("optimal"),
        "playouts": dict(stats.get("playouts", {}) or {}),
        "one_ply_status_counts": dict(stats.get("one_ply_status_counts", {}) or {}),
        "conversion_status_counts": dict(stats.get("conversion_status_counts", {}) or {}),
        "shadow_candidate_count": stats.get("shadow_candidate_count"),
        "krk_strategy_arbiter_sandbox_supported_count": stats.get(
            "krk_strategy_arbiter_sandbox_supported_count"
        ),
        "krk_strategy_arbiter_sandbox_selected_supported_count": stats.get(
            "krk_strategy_arbiter_sandbox_selected_supported_count"
        ),
        "krk_strategy_arbiter_sandbox_supported_provider_by_outcome": dict(
            stats.get("krk_strategy_arbiter_sandbox_supported_provider_by_outcome", {}) or {}
        ),
        "krk_strategy_arbiter_sandbox_selected_by_outcome": dict(
            stats.get("krk_strategy_arbiter_sandbox_selected_by_outcome", {}) or {}
        ),
    }


def _run(*, support: float, allow_stage7: bool) -> dict[str, Any]:
    return _compact(
        evaluate_landmark_progress(
            ROOT / TOPOLOGY,
            label="box_shrink",
            samples=3,
            seed=11,
            playout_max_plies=20,
            composition_profile=COMPOSITION_PROFILE_HANDOFF_V1,
            early_stop_stable_suggestions=2,
            enable_diagnostic_caches=True,
            krk_strategy_arbiter_sandbox_enabled=support > 0.0,
            krk_strategy_arbiter_support=support,
            krk_strategy_arbiter_allow_stage7_challenge=allow_stage7,
            verbose=False,
        )
    )


def build_probe() -> dict[str, Any]:
    baseline = _run(support=0.0, allow_stage7=False)
    enabled = _run(support=0.05, allow_stage7=True)
    baseline_mate = int((baseline.get("playouts", {}) or {}).get("mate", 0) or 0)
    enabled_mate = int((enabled.get("playouts", {}) or {}).get("mate", 0) or 0)
    baseline_shadow = int(baseline.get("shadow_candidate_count", 0) or 0)
    enabled_shadow = int(enabled.get("shadow_candidate_count", 0) or 0)
    payload = {
        "schema_version": "krk_strategy_arbiter_stage7_challenge_probe.v1",
        "causal_status": "runtime_test_stage7_challenge_probe",
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "topology": str(TOPOLOGY),
        "profile": COMPOSITION_PROFILE_HANDOFF_V1,
        "sample": {
            "label": "box_shrink",
            "samples": 3,
            "seed": 11,
            "playout_max_plies": 20,
            "support_amount": 0.05,
            "allow_stage7_challenge": True,
        },
        "baseline": baseline,
        "enabled_support_0_05": enabled,
        "summary": {
            "conversion_delta": enabled_mate - baseline_mate,
            "shadow_candidate_delta": enabled_shadow - baseline_shadow,
            "support_total": int(enabled.get("krk_strategy_arbiter_sandbox_supported_count", 0) or 0),
            "selected_supported_count": int(
                enabled.get("krk_strategy_arbiter_sandbox_selected_supported_count", 0) or 0
            ),
            "no_no_move_or_draw_spike": (
                int(enabled.get("no_move", 0) or 0) <= int(baseline.get("no_move", 0) or 0)
                and int((enabled.get("playouts", {}) or {}).get("draw", 0) or 0)
                <= int((baseline.get("playouts", {}) or {}).get("draw", 0) or 0)
            ),
        },
        "decision": {
            "status": "stage7_challenge_probe_no_regression",
            "recommended_next_step": "review_stage7_challenge_effect_before_scaling_or_tuning",
        },
    }
    if payload["summary"]["conversion_delta"] > 0 and payload["summary"]["no_no_move_or_draw_spike"]:
        payload["decision"] = {
            "status": "stage7_challenge_probe_improved_not_promoted",
            "recommended_next_step": "run_paired_stage7_10_sample_runtime_test_with_guardrails_pending",
        }
    elif payload["summary"]["conversion_delta"] < 0 or not payload["summary"]["no_no_move_or_draw_spike"]:
        payload["decision"] = {
            "status": "stage7_challenge_probe_regressed_quarantine",
            "recommended_next_step": "quarantine_stage7_challenge_use_of_strategy_arbiter_support",
        }
    return payload


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Strategy Arbiter Stage 7 Challenge Probe v1",
        "",
        "This runtime-test explicitly allows Stage 7 challenge support. It is not training, promotion, or a Stage 7 repair commit.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Outcomes",
            "",
            f"- Baseline playouts: `{payload['baseline']['playouts']}`",
            f"- Enabled playouts: `{payload['enabled_support_0_05']['playouts']}`",
            f"- Enabled selected supported by outcome: `{payload['enabled_support_0_05']['krk_strategy_arbiter_sandbox_selected_by_outcome']}`",
            "",
            "## Decision",
            "",
            f"- Status: `{payload['decision']['status']}`",
            f"- Recommended next step: `{payload['decision']['recommended_next_step']}`",
            "",
        ]
    )
    (ROOT / OUT_MD).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    payload = build_probe()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
