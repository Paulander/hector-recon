#!/usr/bin/env python3
"""Run a tiny protected-control matrix for the KRK strategy-arbiter sandbox."""

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
OUT_JSON = Path("reports/krk_strategy_arbiter_protected_control_matrix_v1.json")
OUT_MD = Path("reports/krk_strategy_arbiter_protected_control_matrix_v1.md")


LABELS = (
    "edge_trap_wrong_tempo",
    "fence_established",
    "drive_to_edge",
)


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
        "avg_reward": stats.get("avg_reward"),
        "avg_oracle_reward": stats.get("avg_oracle_reward"),
        "handoff_packet_count": stats.get("handoff_packet_count"),
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


def _outcome_signature(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "total": row.get("total"),
        "no_move": row.get("no_move"),
        "improved": row.get("improved"),
        "worsened": row.get("worsened"),
        "optimal": row.get("optimal"),
        "playouts": row.get("playouts"),
        "one_ply_status_counts": row.get("one_ply_status_counts"),
        "conversion_status_counts": row.get("conversion_status_counts"),
        "shadow_candidate_count": row.get("shadow_candidate_count"),
    }


def _run_eval(label: str, *, sandbox_enabled: bool, support: float) -> dict[str, Any]:
    return _compact(
        evaluate_landmark_progress(
            ROOT / TOPOLOGY,
            label=label,
            samples=1,
            seed=7,
            playout_max_plies=20,
            composition_profile=COMPOSITION_PROFILE_HANDOFF_V1,
            early_stop_stable_suggestions=2,
            enable_diagnostic_caches=True,
            krk_strategy_arbiter_sandbox_enabled=sandbox_enabled,
            krk_strategy_arbiter_support=support,
            verbose=False,
        )
    )


def build_matrix() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for label in LABELS:
        baseline = _run_eval(label, sandbox_enabled=False, support=0.0)
        flag_off = _run_eval(label, sandbox_enabled=True, support=0.0)
        enabled = _run_eval(label, sandbox_enabled=True, support=0.05)
        row = {
            "label": label,
            "baseline": baseline,
            "flag_present_default_off": flag_off,
            "enabled_support_0_05": enabled,
            "default_off_equivalence": _outcome_signature(baseline) == _outcome_signature(flag_off),
            "enabled_has_no_no_move_or_draw_spike": (
                int(enabled.get("no_move", 0) or 0) <= int(baseline.get("no_move", 0) or 0)
                and int((enabled.get("playouts", {}) or {}).get("draw", 0) or 0)
                <= int((baseline.get("playouts", {}) or {}).get("draw", 0) or 0)
            ),
            "enabled_conversion_not_worse": (
                int((enabled.get("playouts", {}) or {}).get("mate", 0) or 0)
                >= int((baseline.get("playouts", {}) or {}).get("mate", 0) or 0)
            ),
        }
        rows.append(row)
    default_off_passed = all(row["default_off_equivalence"] for row in rows)
    no_safety_regression = all(row["enabled_has_no_no_move_or_draw_spike"] for row in rows)
    conversion_not_worse = all(row["enabled_conversion_not_worse"] for row in rows)
    support_total = sum(
        int(row["enabled_support_0_05"].get("krk_strategy_arbiter_sandbox_supported_count", 0) or 0)
        for row in rows
    )
    payload = {
        "schema_version": "krk_strategy_arbiter_protected_control_matrix.v1",
        "causal_status": "runtime_test_protected_control_matrix",
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "topology": str(TOPOLOGY),
        "profile": COMPOSITION_PROFILE_HANDOFF_V1,
        "sample": {
            "labels": list(LABELS),
            "samples_per_label": 1,
            "seed": 7,
            "playout_max_plies": 20,
            "support_amount": 0.05,
            "stage7_rows": 0,
        },
        "rows": rows,
        "summary": {
            "default_off_equivalence_passed": default_off_passed,
            "enabled_has_no_no_move_or_draw_spike": no_safety_regression,
            "enabled_conversion_not_worse": conversion_not_worse,
            "enabled_support_total": support_total,
        },
        "decision": {
            "status": "protected_control_matrix_passed",
            "recommended_next_step": "run_small_protected_control_matrix_or_guardrail_smoke",
        },
    }
    if not default_off_passed:
        payload["decision"] = {
            "status": "protected_control_default_off_equivalence_failed",
            "recommended_next_step": "stop_and_diagnose_default_off_delta",
        }
    elif not no_safety_regression or not conversion_not_worse:
        payload["decision"] = {
            "status": "protected_control_enabled_regression_detected",
            "recommended_next_step": "quarantine_strategy_arbiter_sandbox_support",
        }
    elif support_total == 0:
        payload["decision"] = {
            "status": "protected_control_matrix_no_support_observed",
            "recommended_next_step": "find_protected_controls_with_eligible_provider_proposals",
        }
    return payload


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Strategy Arbiter Protected Control Matrix v1",
        "",
        "This runtime-test matrix compares baseline, flag-present default-off, and enabled bounded support on protected Stage 4/5/6 labels only.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Rows", ""])
    for row in payload["rows"]:
        lines.append(
            f"- `{row['label']}` default_off=`{row['default_off_equivalence']}` "
            f"enabled_mate=`{row['enabled_support_0_05']['playouts'].get('mate', 0)}` "
            f"baseline_mate=`{row['baseline']['playouts'].get('mate', 0)}` "
            f"support=`{row['enabled_support_0_05'].get('krk_strategy_arbiter_sandbox_supported_count')}`"
        )
    lines.extend(
        [
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
    payload = build_matrix()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
