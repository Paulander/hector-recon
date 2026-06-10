#!/usr/bin/env python3
"""Run a tiny default-off KRK strategy-arbiter runtime sandbox smoke.

This is the first runtime-test smoke for the opt-in strategy-arbiter support
sandbox. It proves flag-present default-off equivalence, then records a tiny
enabled run with bounded visible support. It is intentionally small.
"""

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
    evaluate_landmark_progress,
    select_eval_position,
    source_stage_names_for_label,
)


TOPOLOGY = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json"
)
OUT_JSON = Path("reports/krk_strategy_arbiter_runtime_sandbox_smoke_v1.json")
OUT_MD = Path("reports/krk_strategy_arbiter_runtime_sandbox_smoke_v1.md")


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


def _compact_eval(stats: dict[str, Any]) -> dict[str, Any]:
    return {
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
    }


def _selected_provider(details: dict[str, Any]) -> str | None:
    selected = details.get("selected_suggestion")
    if isinstance(selected, dict) and selected:
        return _skill_id_for_suggestion(selected)
    return None


def _compact_decision(details: dict[str, Any]) -> dict[str, Any]:
    selected = details.get("selected_suggestion")
    selected_meta = selected.get("meta", {}) if isinstance(selected, dict) else {}
    return {
        "move": details.get("move"),
        "confidence": details.get("confidence"),
        "selected_provider": _selected_provider(details),
        "selected_support_payload": dict(
            (selected_meta or {}).get("krk_strategy_arbiter_sandbox_support", {}) or {}
        ),
        "sandbox_summary": dict(details.get("krk_strategy_arbiter_sandbox_summary", {}) or {}),
    }


def _same_behavior(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return (
        left.get("move") == right.get("move")
        and left.get("selected_provider") == right.get("selected_provider")
        and left.get("confidence") == right.get("confidence")
    )


def build_smoke() -> dict[str, Any]:
    label = "fence_established"
    seed = 7
    rng = random.Random(seed)
    board = select_eval_position(rng, label, "curriculum", source_stage_names_for_label(label))
    graph = build_graph_from_topology(ROOT / TOPOLOGY)
    engine = ReConEngine(graph)
    kwargs = _profile_kwargs()
    common = {
        "max_ticks": 200,
        "suggestion_limit": 10,
        "active_landmark_label": label,
        "early_stop_stable_suggestions": 2,
        "enable_diagnostic_caches": True,
        **kwargs,
    }
    baseline_decision = choose_move_details(graph, engine, board.copy(stack=False), **common)
    flag_present_default_off_decision = choose_move_details(
        graph,
        engine,
        board.copy(stack=False),
        krk_strategy_arbiter_sandbox_enabled=True,
        krk_strategy_arbiter_support=0.0,
        **common,
    )
    enabled_decision = choose_move_details(
        graph,
        engine,
        board.copy(stack=False),
        krk_strategy_arbiter_sandbox_enabled=True,
        krk_strategy_arbiter_support=0.05,
        **common,
    )
    eval_common = {
        "topology": ROOT / TOPOLOGY,
        "label": label,
        "samples": 1,
        "seed": seed,
        "playout_max_plies": 4,
        "composition_profile": COMPOSITION_PROFILE_HANDOFF_V1,
        "early_stop_stable_suggestions": 2,
        "enable_diagnostic_caches": True,
        "verbose": False,
    }
    baseline_eval = evaluate_landmark_progress(**eval_common)
    flag_present_default_off_eval = evaluate_landmark_progress(
        **eval_common,
        krk_strategy_arbiter_sandbox_enabled=True,
        krk_strategy_arbiter_support=0.0,
    )
    enabled_eval = evaluate_landmark_progress(
        **eval_common,
        krk_strategy_arbiter_sandbox_enabled=True,
        krk_strategy_arbiter_support=0.05,
    )
    baseline_compact = _compact_decision(baseline_decision)
    flag_off_compact = _compact_decision(flag_present_default_off_decision)
    enabled_compact = _compact_decision(enabled_decision)
    baseline_eval_compact = _compact_eval(baseline_eval)
    flag_off_eval_compact = _compact_eval(flag_present_default_off_eval)
    enabled_eval_compact = _compact_eval(enabled_eval)
    payload = {
        "schema_version": "krk_strategy_arbiter_runtime_sandbox_smoke.v1",
        "causal_status": "runtime_test_sandbox_smoke",
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "topology": str(TOPOLOGY),
        "profile": COMPOSITION_PROFILE_HANDOFF_V1,
        "sample": {
            "label": label,
            "seed": seed,
            "samples": 1,
            "playout_max_plies": 4,
        },
        "one_ply_decisions": {
            "baseline": baseline_compact,
            "flag_present_default_off": flag_off_compact,
            "enabled_support_0_05": enabled_compact,
        },
        "eval_results": {
            "baseline": baseline_eval_compact,
            "flag_present_default_off": flag_off_eval_compact,
            "enabled_support_0_05": enabled_eval_compact,
        },
        "equivalence": {
            "flag_present_default_off_decision_matches_baseline": _same_behavior(
                baseline_compact,
                flag_off_compact,
            ),
            "flag_present_default_off_outcome_matches_baseline": (
                baseline_eval_compact == flag_off_eval_compact
            ),
        },
        "enabled_sandbox": {
            "support_was_applied": bool(
                enabled_compact["sandbox_summary"].get("supported_count", 0)
            ),
            "selected_supported": bool(enabled_compact["selected_support_payload"]),
            "direct_request": False,
            "support_amount": 0.05,
        },
        "decision": {
            "status": "runtime_sandbox_smoke_passed",
            "default_off_equivalence_passed": False,
            "enabled_support_trace_visible": False,
            "recommended_next_step": "run_tiny_protected_control_matrix",
        },
    }
    payload["decision"]["default_off_equivalence_passed"] = bool(
        payload["equivalence"]["flag_present_default_off_decision_matches_baseline"]
        and payload["equivalence"]["flag_present_default_off_outcome_matches_baseline"]
    )
    payload["decision"]["enabled_support_trace_visible"] = bool(
        payload["enabled_sandbox"]["support_was_applied"]
    )
    if not payload["decision"]["default_off_equivalence_passed"]:
        payload["decision"]["status"] = "runtime_sandbox_default_off_equivalence_failed"
        payload["decision"]["recommended_next_step"] = "stop_and_diagnose_default_off_delta"
    elif not payload["decision"]["enabled_support_trace_visible"]:
        payload["decision"]["status"] = "runtime_sandbox_enabled_support_not_observed"
        payload["decision"]["recommended_next_step"] = "find_smoke_state_with_eligible_provider_proposal"
    return payload


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Strategy Arbiter Runtime Sandbox Smoke v1",
        "",
        "This is a tiny runtime-test smoke for the default-off KRK strategy-arbiter sandbox.",
        "",
        "## Equivalence",
        "",
        f"- Flag-present default-off decision matches baseline: `{payload['equivalence']['flag_present_default_off_decision_matches_baseline']}`",
        f"- Flag-present default-off outcome matches baseline: `{payload['equivalence']['flag_present_default_off_outcome_matches_baseline']}`",
        "",
        "## Enabled Sandbox",
        "",
        f"- Support was applied: `{payload['enabled_sandbox']['support_was_applied']}`",
        f"- Selected supported proposal: `{payload['enabled_sandbox']['selected_supported']}`",
        f"- Direct request: `{payload['enabled_sandbox']['direct_request']}`",
        "",
        "## Decisions",
        "",
    ]
    for name, decision in payload["one_ply_decisions"].items():
        lines.append(
            f"- `{name}` provider=`{decision['selected_provider']}` move=`{decision['move']}` "
            f"support=`{decision['sandbox_summary'].get('supported_count')}`"
        )
    lines.extend(
        [
            "",
            "## Final Decision",
            "",
            f"- Status: `{payload['decision']['status']}`",
            f"- Recommended next step: `{payload['decision']['recommended_next_step']}`",
            "",
        ]
    )
    (ROOT / OUT_MD).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    payload = build_smoke()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
