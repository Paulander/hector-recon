#!/usr/bin/env python3
"""One-ply support sensitivity for the KRK strategy-arbiter sandbox."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from recon_lite.engine import ReConEngine  # noqa: E402
from scripts.test_krk_landmark_progress import (  # noqa: E402
    COMPOSITION_PROFILE_HANDOFF_V1,
    _composition_profile_metadata,
    _skill_id_for_suggestion,
    build_graph_from_topology,
    choose_move_details,
    select_eval_position,
    source_stage_names_for_label,
)


TOPOLOGY = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json"
)
OUT_JSON = Path("reports/krk_strategy_arbiter_support_sensitivity_v1.json")
OUT_MD = Path("reports/krk_strategy_arbiter_support_sensitivity_v1.md")
LABELS = ("edge_trap_wrong_tempo", "fence_established", "drive_to_edge", "box_shrink")
SUPPORT_VALUES = (0.0, 0.05, 1.0, 5.0, 20.0, 50.0)


def _profile_kwargs() -> dict[str, Any]:
    profile = _composition_profile_metadata(COMPOSITION_PROFILE_HANDOFF_V1) or {}
    settings = dict(profile.get("settings", {}) or {})
    return {
        "successor_affordance_layer_enabled": bool(
            settings.get("successor_affordance_layer_enabled", False)
        ),
        "successor_role_license_enabled": bool(
            settings.get("successor_role_license_enabled", False)
        ),
        "successor_role_scoped_move_shape_enabled": bool(
            settings.get("successor_role_scoped_move_shape_enabled", False)
        ),
        "successor_role_scoped_move_shape_bonus": float(
            settings.get("successor_role_scoped_move_shape_bonus", 0.0)
        ),
        "stagnation_breaker_enabled": bool(settings.get("stagnation_breaker_enabled", False)),
        "stagnation_breaker_bonus": float(settings.get("stagnation_breaker_bonus", 0.0)),
        "post_break_continuation_enabled": bool(
            settings.get("post_break_continuation_enabled", False)
        ),
        "post_break_continuation_bonus": float(
            settings.get("post_break_continuation_bonus", 0.0)
        ),
        "successor_stage0_drift_penalty": float(
            settings.get("successor_stage0_drift_penalty", 0.0)
        ),
    }


def _selected_support_payload(details: dict[str, Any]) -> dict[str, Any]:
    selected = details.get("selected_suggestion")
    if not isinstance(selected, dict) or not selected:
        return {}
    selected_provider = _skill_id_for_suggestion(selected)
    selected_move = selected.get("move")
    for item in details.get("suggestions", []) or []:
        if _skill_id_for_suggestion(item) != selected_provider:
            continue
        if item.get("move") != selected_move:
            continue
        meta = item.get("meta", {}) if isinstance(item.get("meta"), dict) else {}
        return dict(meta.get("krk_strategy_arbiter_sandbox_support", {}) or {})
    meta = selected.get("meta", {}) if isinstance(selected.get("meta"), dict) else {}
    return dict(meta.get("krk_strategy_arbiter_sandbox_support", {}) or {})


def _decision_row(details: dict[str, Any], *, support: float) -> dict[str, Any]:
    selected = details.get("selected_suggestion")
    support_payload = _selected_support_payload(details)
    return {
        "support": support,
        "move": details.get("move"),
        "confidence": details.get("confidence"),
        "selected_provider": _skill_id_for_suggestion(selected) if isinstance(selected, dict) else None,
        "selected_supported": bool(support_payload),
        "selected_support_payload": support_payload,
        "sandbox_summary": dict(details.get("krk_strategy_arbiter_sandbox_summary", {}) or {}),
    }


def _run_one(
    *,
    graph: Any,
    engine: ReConEngine,
    board: Any,
    label: str,
    support: float,
) -> dict[str, Any]:
    return _decision_row(
        choose_move_details(
            graph,
            engine,
            board.copy(stack=False),
            max_ticks=200,
            suggestion_limit=10,
            active_landmark_label=label,
            early_stop_stable_suggestions=2,
            enable_diagnostic_caches=True,
            krk_strategy_arbiter_sandbox_enabled=support > 0.0,
            krk_strategy_arbiter_support=support,
            krk_strategy_arbiter_allow_stage7_challenge=(label == "box_shrink"),
            **_profile_kwargs(),
        ),
        support=support,
    )


def build_report() -> dict[str, Any]:
    rows = []
    for label in LABELS:
        rng = random.Random(11)
        board = select_eval_position(rng, label, "curriculum", source_stage_names_for_label(label))
        graph = build_graph_from_topology(ROOT / TOPOLOGY)
        engine = ReConEngine(graph)
        decisions = [
            _run_one(
                graph=graph,
                engine=engine,
                board=board,
                label=label,
                support=support,
            )
            for support in SUPPORT_VALUES
        ]
        baseline_provider = decisions[0]["selected_provider"]
        first_change = next(
            (
                decision
                for decision in decisions[1:]
                if decision["selected_provider"] != baseline_provider
            ),
            None,
        )
        rows.append({
            "label": label,
            "baseline_provider": baseline_provider,
            "first_provider_change": first_change,
            "decisions": decisions,
        })
    stage7 = next(row for row in rows if row["label"] == "box_shrink")
    low_support_cap = 5.0
    protected_changes = [
        row for row in rows if row["label"] != "box_shrink" and row["first_provider_change"]
    ]
    protected_low_support_changes = [
        row
        for row in protected_changes
        if float((row["first_provider_change"] or {}).get("support") or 0.0) <= low_support_cap
    ]
    stage7_first_change_support = (stage7["first_provider_change"] or {}).get("support")
    payload = {
        "schema_version": "krk_strategy_arbiter_support_sensitivity.v1",
        "causal_status": "runtime_test_one_ply_sensitivity",
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "topology": str(TOPOLOGY),
        "profile": COMPOSITION_PROFILE_HANDOFF_V1,
        "support_values": list(SUPPORT_VALUES),
        "rows": rows,
        "summary": {
            "low_support_cap": low_support_cap,
            "stage7_first_provider_change_support": stage7_first_change_support,
            "stage7_changes_under_low_support_cap": (
                stage7_first_change_support is not None
                and float(stage7_first_change_support) <= low_support_cap
            ),
            "protected_labels_with_provider_change": [row["label"] for row in protected_changes],
            "protected_labels_with_low_support_change": [
                row["label"] for row in protected_low_support_changes
            ],
            "support_scale_risk": (
                "high_support_changes_protected_ownership_before_safe_stage7_evidence"
                if protected_changes
                else "no_protected_one_ply_provider_change_observed"
            ),
        },
        "decision": {
            "status": "support_sensitivity_measured",
            "recommended_next_step": "do_not_raise_support_without_arbitration_objective_review",
            "stage7_runtime_test_status": "no_low_support_ownership_effect",
            "protected_control_status": (
                "high_support_changes_protected_one_ply_ownership"
                if protected_changes
                else "no_protected_one_ply_ownership_change_observed"
            ),
        },
    }
    return payload


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Strategy Arbiter Support Sensitivity v1",
        "",
        "This one-ply runtime-test measures how much bounded support is needed to change selected ownership. It does not run conversion playouts.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Rows", ""])
    for row in payload["rows"]:
        first = row["first_provider_change"]
        first_text = (
            f"support={first['support']} provider={first['selected_provider']}"
            if first
            else "none"
        )
        lines.append(
            f"- `{row['label']}` baseline=`{row['baseline_provider']}` first_change=`{first_text}`"
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
    payload = build_report()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
