#!/usr/bin/env python3
"""Check that the KRK strategy-arbiter sandbox keeps Stage 7 held out by default."""

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
OUT_JSON = Path("reports/krk_strategy_arbiter_stage7_holdout_lock_v1.json")
OUT_MD = Path("reports/krk_strategy_arbiter_stage7_holdout_lock_v1.md")


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
    }


def _run(*, sandbox_enabled: bool, support: float, allow_stage7: bool = False) -> dict[str, Any]:
    return _compact(
        evaluate_landmark_progress(
            ROOT / TOPOLOGY,
            label="box_shrink",
            samples=1,
            seed=7,
            playout_max_plies=20,
            composition_profile=COMPOSITION_PROFILE_HANDOFF_V1,
            early_stop_stable_suggestions=2,
            enable_diagnostic_caches=True,
            krk_strategy_arbiter_sandbox_enabled=sandbox_enabled,
            krk_strategy_arbiter_support=support,
            krk_strategy_arbiter_allow_stage7_challenge=allow_stage7,
            verbose=False,
        )
    )


def build_report() -> dict[str, Any]:
    baseline = _run(sandbox_enabled=False, support=0.0)
    enabled_blocked = _run(sandbox_enabled=True, support=0.05, allow_stage7=False)
    equivalence = baseline == enabled_blocked
    support_blocked = int(enabled_blocked.get("krk_strategy_arbiter_sandbox_supported_count", 0) or 0) == 0
    payload = {
        "schema_version": "krk_strategy_arbiter_stage7_holdout_lock.v1",
        "causal_status": "runtime_test_stage7_holdout_lock",
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "topology": str(TOPOLOGY),
        "profile": COMPOSITION_PROFILE_HANDOFF_V1,
        "sample": {
            "label": "box_shrink",
            "samples": 1,
            "seed": 7,
            "playout_max_plies": 20,
            "support_amount": 0.05,
            "allow_stage7_challenge": False,
        },
        "baseline": baseline,
        "enabled_stage7_blocked": enabled_blocked,
        "equivalence": {
            "enabled_blocked_matches_baseline": equivalence,
            "support_blocked": support_blocked,
        },
        "decision": {
            "status": "stage7_holdout_lock_passed",
            "recommended_next_step": "run_small_protected_control_matrix_or_explicit_stage7_challenge_review",
        },
    }
    if not equivalence or not support_blocked:
        payload["decision"] = {
            "status": "stage7_holdout_lock_failed",
            "recommended_next_step": "stop_and_diagnose_stage7_holdout_leak",
        }
    return payload


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Strategy Arbiter Stage 7 Holdout Lock v1",
        "",
        "This runtime-test verifies that Stage 7 `box_shrink` remains held out by default.",
        "",
        "## Result",
        "",
        f"- Enabled blocked matches baseline: `{payload['equivalence']['enabled_blocked_matches_baseline']}`",
        f"- Support blocked: `{payload['equivalence']['support_blocked']}`",
        f"- Baseline playouts: `{payload['baseline']['playouts']}`",
        f"- Enabled blocked playouts: `{payload['enabled_stage7_blocked']['playouts']}`",
        "",
        "## Decision",
        "",
        f"- Status: `{payload['decision']['status']}`",
        f"- Recommended next step: `{payload['decision']['recommended_next_step']}`",
        "",
    ]
    (ROOT / OUT_MD).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    payload = build_report()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
