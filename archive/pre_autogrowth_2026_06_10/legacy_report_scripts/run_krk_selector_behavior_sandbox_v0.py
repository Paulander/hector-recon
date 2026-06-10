#!/usr/bin/env python3
"""Run the default-off narrow KRK selector behavior sandbox."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable

import chess

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_krk_candidate_generation_observation_sandbox_v0 import (  # noqa: E402
    _new_graph_engine,
    _profile_kwargs,
)
from scripts.run_krk_selector_observability_expansion_v0 import (  # noqa: E402
    build_manifest,
)
from scripts.test_krk_landmark_progress import (  # noqa: E402
    _skill_id_for_suggestion,
    choose_move_details,
)


REVIEW_PACKET = Path(
    "reports/strategy_arbitration/krk_selector_behavior_sandbox_review_packet_v0.json"
)
OUT_JSON = Path("reports/strategy_arbitration/krk_selector_behavior_sandbox_v0.json")
OUT_MD = Path("reports/strategy_arbitration/krk_selector_behavior_sandbox_v0.md")

COMMON_FALSE_FLAGS = {
    "runtime_defaults_changed": False,
    "runtime_score_changes": False,
    "runtime_provider_suppression": False,
    "runtime_direct_routing": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "hidden_python_controller": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
}

POSSIBLE_STATUSES = [
    "selector_behavior_sandbox_wired_default_off_equivalent",
    "selector_behavior_sandbox_target_improved",
    "selector_behavior_sandbox_no_target_improvement",
    "selector_behavior_sandbox_regressed_safe_controls",
    "selector_behavior_sandbox_failed_equivalence",
    "selector_behavior_sandbox_quarantined",
]


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _selected_provider(details: dict[str, Any]) -> str | None:
    selected = details.get("selected_suggestion")
    if isinstance(selected, dict) and selected:
        return _skill_id_for_suggestion(selected)
    return None


def _compact_decision(details: dict[str, Any]) -> dict[str, Any]:
    rec = details.get("krk_selector_objective_recommendation") or {}
    behavior = details.get("krk_selector_behavior_sandbox_decision") or {}
    return {
        "move": details.get("move"),
        "selected_provider": _selected_provider(details),
        "confidence": details.get("confidence"),
        "selector_recommendation_present": bool(rec),
        "selector_recommendation": rec,
        "behavior_sandbox_decision_present": bool(behavior),
        "behavior_sandbox_decision": behavior,
        "selected_by_selector_behavior_sandbox": bool(
            details.get("selected_by_selector_behavior_sandbox")
        ),
    }


def _run_decision(case: dict[str, Any], enabled: bool) -> dict[str, Any]:
    graph, engine = _new_graph_engine()
    board = chess.Board(str(case["fen"]))
    details = choose_move_details(
        graph,
        engine,
        board,
        max_ticks=200,
        suggestion_limit=10,
        active_landmark_label=str(case["active_landmark_label"]),
        early_stop_stable_suggestions=2,
        krk_selector_behavior_sandbox_enabled=enabled,
        enable_diagnostic_caches=True,
        **_profile_kwargs(),
    )
    return _compact_decision(details)


def build_payload(
    *,
    decision_runner: Callable[[dict[str, Any], bool], dict[str, Any]] | None = None,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    review = _load(REVIEW_PACKET)
    manifest = manifest or build_manifest()
    runner = decision_runner or _run_decision
    rows = []
    for case in manifest.get("cases") or []:
        default_off = runner(case, False)
        enabled = runner(case, True)
        rec = enabled.get("selector_recommendation") or {}
        behavior = enabled.get("behavior_sandbox_decision") or {}
        action = behavior.get("action") or "not_evaluated"
        selected_move_delta = default_off.get("move") != enabled.get("move")
        selected_provider_delta = (
            default_off.get("selected_provider") != enabled.get("selected_provider")
        )
        selected_score_delta = default_off.get("confidence") != enabled.get("confidence")
        switched = action == "switch_to_visible_alternative"
        target_improved = (
            switched
            and rec.get("recommendation") == "prefer_visible_alternative"
            and case.get("selected_owner_label") == "selected_owner_failed"
        )
        safe_regression = switched and case.get("selected_owner_label") == (
            "selected_owner_converted"
        )
        rows.append({
            **case,
            "flag_off_decision": default_off,
            "enabled_decision": enabled,
            "flag_off_behavior_metadata_count": int(
                bool(default_off.get("behavior_sandbox_decision_present"))
            ),
            "enabled_behavior_metadata_count": int(bool(behavior)),
            "recommendation": rec.get("recommendation"),
            "behavior_action": action,
            "behavior_veto_reason": behavior.get("veto_reason"),
            "selected_move_delta": selected_move_delta,
            "selected_provider_delta": selected_provider_delta,
            "selected_score_delta": selected_score_delta,
            "score_delta": float(behavior.get("score_delta", 0.0) or 0.0),
            "routing_delta": False,
            "target_improved": target_improved,
            "safe_regression": safe_regression,
            "switch_used_visible_alternative": (
                switched
                and bool(behavior.get("replacement_provider"))
                and bool(behavior.get("replacement_move"))
            ),
            "stage7_training_row": False,
            "selector_training_row": False,
            "runtime_dtm_or_tablebase": bool(
                behavior.get("runtime_dtm_or_tablebase", False)
            ),
            "gameplay_topology_mutation": bool(
                behavior.get("gameplay_topology_mutation", False)
            ),
        })

    action_counts = Counter(str(row["behavior_action"]) for row in rows)
    recommendation_counts = Counter(str(row.get("recommendation") or "") for row in rows)
    enabled_switch_count = int(action_counts.get("switch_to_visible_alternative", 0))
    preserve_noop_count = sum(
        1
        for row in rows
        if row.get("recommendation") == "preserve_selected_owner"
        and row["behavior_action"] == "no_op"
    )
    abstain_noop_count = sum(
        1
        for row in rows
        if row.get("recommendation") == "abstain_context_only"
        and row["behavior_action"] == "no_op"
    )
    selected_move_delta_count = sum(1 for row in rows if row["selected_move_delta"])
    selected_provider_delta_count = sum(1 for row in rows if row["selected_provider_delta"])
    selected_score_delta_count = sum(1 for row in rows if row["selected_score_delta"])
    score_delta_count = sum(1 for row in rows if row["score_delta"] != 0.0)
    routing_delta_count = sum(1 for row in rows if row["routing_delta"])
    target_improvement_count = sum(1 for row in rows if row["target_improved"])
    safe_regression_count = sum(1 for row in rows if row["safe_regression"])
    flag_off_metadata_count = sum(int(row["flag_off_behavior_metadata_count"]) for row in rows)
    stage7_training_row_count = sum(1 for row in rows if row["stage7_training_row"])
    selector_training_row_count = sum(1 for row in rows if row["selector_training_row"])
    runtime_dtm_or_tablebase = any(row["runtime_dtm_or_tablebase"] for row in rows)
    topology_mutation = any(row["gameplay_topology_mutation"] for row in rows)
    bad_switch_count = sum(
        1
        for row in rows
        if row["behavior_action"] == "switch_to_visible_alternative"
        and row.get("recommendation") != "prefer_visible_alternative"
    )
    default_off_equivalence_passed = (
        bool(rows)
        and flag_off_metadata_count == 0
        and score_delta_count == 0
        and routing_delta_count == 0
        and stage7_training_row_count == 0
        and selector_training_row_count == 0
        and not runtime_dtm_or_tablebase
        and not topology_mutation
    )
    switch_scope_valid = (
        bad_switch_count == 0
        and selected_move_delta_count == enabled_switch_count
        and selected_provider_delta_count <= enabled_switch_count
        and all(
            row["switch_used_visible_alternative"]
            for row in rows
            if row["behavior_action"] == "switch_to_visible_alternative"
        )
    )
    if not default_off_equivalence_passed:
        status = "selector_behavior_sandbox_failed_equivalence"
    elif not switch_scope_valid:
        status = "selector_behavior_sandbox_quarantined"
    elif safe_regression_count:
        status = "selector_behavior_sandbox_regressed_safe_controls"
    elif target_improvement_count:
        status = "selector_behavior_sandbox_target_improved"
    elif enabled_switch_count:
        status = "selector_behavior_sandbox_wired_default_off_equivalent"
    else:
        status = "selector_behavior_sandbox_no_target_improvement"

    summary = {
        "attempted_row_count": len(rows),
        "default_off_equivalence_passed": default_off_equivalence_passed,
        "enabled_switch_count": enabled_switch_count,
        "preserve_noop_count": preserve_noop_count,
        "abstain_noop_count": abstain_noop_count,
        "behavior_action_counts": dict(sorted(action_counts.items())),
        "recommendation_counts_by_class": dict(sorted(recommendation_counts.items())),
        "flag_off_behavior_metadata_count": flag_off_metadata_count,
        "selected_move_delta_count": selected_move_delta_count,
        "selected_provider_delta_count": selected_provider_delta_count,
        "selected_score_delta_count": selected_score_delta_count,
        "score_delta_count": score_delta_count,
        "routing_delta_count": routing_delta_count,
        "target_improvement_count": target_improvement_count,
        "safe_regression_count": safe_regression_count,
        "bad_switch_count": bad_switch_count,
        "stage7_training_row_count": stage7_training_row_count,
        "selector_training_row_count": selector_training_row_count,
        "runtime_dtm_or_tablebase": runtime_dtm_or_tablebase,
        "topology_mutation": topology_mutation,
        "enabled_behavior_changed": enabled_switch_count > 0,
    }
    return {
        "schema_version": "krk_selector_behavior_sandbox.v0",
        "sandbox_id": "sandbox.krk.selector_behavior_v0",
        "causal_status": "default_off_behavior_sandbox_smoke",
        **COMMON_FALSE_FLAGS,
        "runtime_behavior_changed": False,
        "runtime_selector_implemented": False,
        "behavior_sandbox_implemented": True,
        "source_artifacts": [str(REVIEW_PACKET)],
        "approval": {
            "approval_status": "explicitly_approved_for_first_selector_behavior_sandbox",
            "flag_required": "--enable-krk-selector-behavior-sandbox",
            "review_packet_status": review.get("decision", {}).get("status"),
        },
        "summary": summary,
        "rows": rows,
        "possible_statuses": POSSIBLE_STATUSES,
        "decision": {
            "status": status,
            "promote": False,
            "make_default": False,
            "run_broad_guardrails": target_improvement_count > 0 and safe_regression_count == 0,
            "train_anything": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "runtime_dtm_or_tablebase_allowed": False,
            "gameplay_topology_mutation_allowed": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Selector Behavior Sandbox v0",
        "",
        "This report records the explicitly approved default-off narrow selector behavior sandbox smoke. The sandbox can switch only to an already-visible alternative when enabled and when the refined selector recommends `prefer_visible_alternative`.",
        "",
        "## Decision",
        "",
    ]
    for key, value in payload["decision"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Summary", ""])
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Rows", ""])
    for row in payload["rows"]:
        lines.append(
            "- "
            f"`{row.get('row_id') or row.get('case_id')}` "
            f"stage={row.get('source_stage')} "
            f"recommendation=`{row.get('recommendation')}` "
            f"action=`{row.get('behavior_action')}` "
            f"move_delta={row.get('selected_move_delta')} "
            f"provider_delta={row.get('selected_provider_delta')} "
            f"target_improved={row.get('target_improved')} "
            f"safe_regression={row.get('safe_regression')}"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run default-off narrow KRK selector behavior sandbox"
    )
    parser.add_argument(
        "--enable-krk-selector-behavior-sandbox",
        action="store_true",
        help="Execute the explicitly approved bounded selector behavior sandbox smoke.",
    )
    args = parser.parse_args()
    if not args.enable_krk_selector_behavior_sandbox:
        raise SystemExit("refusing_to_execute_without_--enable-krk-selector-behavior-sandbox")
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ROOT / OUT_MD).write_text(write_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
