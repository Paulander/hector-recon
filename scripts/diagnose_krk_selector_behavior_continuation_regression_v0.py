#!/usr/bin/env python3
"""Diagnose the quarantined selector_behavior h40 continuation regression.

This script is diagnostic-only. It does not change production behavior and does
not unquarantine the selector behavior path.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

import chess


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_krk_candidate_generation_observation_sandbox_v0 import (  # noqa: E402
    _new_graph_engine,
    _profile_kwargs,
)
from scripts.test_krk_landmark_progress import play_to_mate  # noqa: E402


REGRESSION_AUDIT = Path(
    "reports/strategy_arbitration/krk_selector_behavior_regression_audit_v0.json"
)
REGRESSION_DECISION = Path(
    "reports/strategy_arbitration/krk_selector_behavior_regression_decision_v0.json"
)
VALIDATION_REPORT = Path(
    "reports/strategy_arbitration/krk_selector_behavior_sandbox_validation_v0.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/"
    "krk_selector_behavior_continuation_regression_root_cause_v0.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/"
    "krk_selector_behavior_continuation_regression_root_cause_v0.md"
)

COMMON_FALSE_FLAGS = {
    "production_runtime_behavior_changed": False,
    "selector_unquarantined": False,
    "production_fix_implemented": False,
    "expected_outputs_weakened": False,
    "protected_regression_tests_weakened": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _regressed_case() -> dict[str, Any]:
    validation = _load(VALIDATION_REPORT)
    for row in validation.get("rows") or []:
        if row.get("row_id") == "joined_trace_ownership_4":
            return row
    raise ValueError("joined_trace_ownership_4 not found in validation report")


def _selected_skill(engine: dict[str, Any]) -> str | None:
    selected = engine.get("selected_suggestion")
    if isinstance(selected, dict):
        return selected.get("skill_id") or selected.get("skill") or selected.get("actuator")
    selected_move = engine.get("move")
    for suggestion in engine.get("suggestions") or []:
        if not isinstance(suggestion, dict):
            continue
        if suggestion.get("move") == selected_move:
            return suggestion.get("skill_id") or suggestion.get("skill") or suggestion.get("actuator")
    return None


def _suggestion_provider(suggestion: dict[str, Any]) -> str | None:
    return suggestion.get("skill_id") or suggestion.get("skill") or suggestion.get("actuator")


def _compact_suggestions(engine: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
    compact: list[dict[str, Any]] = []
    for suggestion in list(engine.get("suggestions") or [])[:limit]:
        if not isinstance(suggestion, dict):
            continue
        compact.append(
            {
                "move": suggestion.get("move"),
                "provider": _suggestion_provider(suggestion),
                "score": suggestion.get("score"),
                "raw_score_before_role_bonus": (
                    suggestion.get("meta", {}).get("raw_score_before_role_bonus")
                    if isinstance(suggestion.get("meta"), dict)
                    else None
                ),
                "goal_progress": (
                    suggestion.get("meta", {}).get("goal_progress")
                    if isinstance(suggestion.get("meta"), dict)
                    else None
                ),
            }
        )
    return compact


def _compact_event(event: dict[str, Any]) -> dict[str, Any]:
    engine = event.get("engine") if isinstance(event.get("engine"), dict) else {}
    recommendation = engine.get("krk_selector_objective_recommendation") or {}
    behavior = engine.get("krk_selector_behavior_sandbox_decision") or {}
    return {
        "ply": event.get("ply"),
        "turn": event.get("turn"),
        "fen": event.get("fen"),
        "move": event.get("move"),
        "resulting_fen": event.get("resulting_fen"),
        "selected_provider": _selected_skill(engine),
        "confidence": engine.get("confidence"),
        "recommendation": recommendation.get("recommendation"),
        "recommendation_reason": recommendation.get("decision_reason"),
        "recommendation_terms": list(recommendation.get("explanation_terms") or []),
        "visible_alternatives": [
            {
                "provider_id": item.get("provider_id"),
                "provider_family": item.get("provider_family"),
                "move_id": item.get("move_id"),
                "candidate_source": item.get("candidate_source"),
                "capacity_evidence_kind": item.get("capacity_evidence_kind"),
                "label_semantics": item.get("label_semantics"),
                "causal_status": item.get("causal_status"),
            }
            for item in recommendation.get("visible_alternatives_considered") or []
            if isinstance(item, dict)
        ],
        "behavior_action": behavior.get("action"),
        "behavior_veto_reason": behavior.get("veto_reason"),
        "replacement_provider": behavior.get("replacement_provider"),
        "replacement_move": behavior.get("replacement_move"),
        "original_provider": behavior.get("original_selected_provider"),
        "original_move": behavior.get("original_selected_move"),
        "why_selected_alternative": behavior.get("why_selected_alternative"),
        "top_suggestions": _compact_suggestions(engine),
    }


def _run_trace(case: dict[str, Any], *, variant: str, flags: dict[str, Any]) -> dict[str, Any]:
    graph, engine = _new_graph_engine()
    board = chess.Board(str(case["fen"]))
    result = play_to_mate(
        graph,
        engine,
        board,
        random.Random(40),
        str(case["active_landmark_label"]),
        stage_filter=None,
        max_plies=40,
        black_policy="adversarial",
        trace=True,
        trace_max_plies=50,
        max_ticks=200,
        suggestion_limit=10,
        early_stop_stable_suggestions=2,
        **_profile_kwargs(),
        **flags,
    )
    return {
        "variant": variant,
        "flags": dict(sorted(flags.items())),
        "result": result.get("result"),
        "plies": result.get("plies"),
        "engine_decision_count": result.get("engine_decision_count"),
        "engine_ticks_total": result.get("engine_ticks_total"),
        "engine_ticks_max": result.get("engine_ticks_max"),
        "final_fen": result.get("final_fen"),
        "final_turn": result.get("final_turn"),
        "final_mate_in_one_available": result.get("final_mate_in_one_available"),
        "white_events": [
            _compact_event(event)
            for event in result.get("trace") or []
            if event.get("turn") == "white"
        ],
        "black_events": [
            {
                "ply": event.get("ply"),
                "fen": event.get("fen"),
                "move": event.get("move"),
                "resulting_fen": event.get("resulting_fen"),
            }
            for event in result.get("trace") or []
            if event.get("turn") == "black"
        ],
    }


def _first_divergence(control: dict[str, Any], enabled: dict[str, Any]) -> dict[str, Any]:
    control_events = control.get("white_events") or []
    enabled_events = enabled.get("white_events") or []
    for control_event, enabled_event in zip(control_events, enabled_events):
        differing_fields = [
            field
            for field in ("fen", "move", "selected_provider", "resulting_fen")
            if control_event.get(field) != enabled_event.get(field)
        ]
        if differing_fields:
            return {
                "ply": enabled_event.get("ply"),
                "differing_fields": differing_fields,
                "control": control_event,
                "enabled": enabled_event,
            }
    return {
        "ply": None,
        "differing_fields": [],
        "control": control_events[-1] if control_events else {},
        "enabled": enabled_events[-1] if enabled_events else {},
    }


def _variant_lookup(traces: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item["variant"]): item for item in traces}


def build_payload(*, run_live: bool = True, traces: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    audit = _load(REGRESSION_AUDIT)
    decision = _load(REGRESSION_DECISION)
    case = _regressed_case()
    if traces is None:
        if not run_live:
            raise ValueError("traces are required when run_live is false")
        traces = [
            _run_trace(
                case,
                variant="control_default_off",
                flags={"enable_diagnostic_caches": True},
            ),
            _run_trace(
                case,
                variant="selector_observability_only",
                flags={
                    "krk_refined_selector_objective_observability_enabled": True,
                    "enable_diagnostic_caches": True,
                },
            ),
            _run_trace(
                case,
                variant="selector_behavior_enabled_cached",
                flags={
                    "krk_selector_behavior_sandbox_enabled": True,
                    "enable_diagnostic_caches": True,
                },
            ),
            _run_trace(
                case,
                variant="selector_behavior_enabled_no_cache",
                flags={
                    "krk_selector_behavior_sandbox_enabled": True,
                    "enable_diagnostic_caches": False,
                },
            ),
        ]

    variants = _variant_lookup(traces)
    control = variants["control_default_off"]
    behavior = variants["selector_behavior_enabled_cached"]
    observability = variants["selector_observability_only"]
    no_cache = variants["selector_behavior_enabled_no_cache"]
    first_divergence = _first_divergence(control, behavior)

    return {
        "schema_version": "krk_selector_behavior_continuation_regression_root_cause.v0",
        "causal_status": "diagnostic_only_no_production_behavior_change",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            str(REGRESSION_AUDIT),
            str(REGRESSION_DECISION),
            str(VALIDATION_REPORT),
        ],
        "quarantine_status": decision.get("decision", {}).get("status"),
        "minimal_reproduction": {
            "row_id": case.get("row_id"),
            "state_id": case.get("state_id"),
            "fen": case.get("fen"),
            "active_landmark_label": case.get("active_landmark_label"),
            "rng_seed": 40,
            "black_policy": "adversarial",
            "max_plies": 40,
            "max_ticks": 200,
            "suggestion_limit": 10,
            "early_stop_stable_suggestions": 2,
            "command": (
                "uv run python scripts/"
                "diagnose_krk_selector_behavior_continuation_regression_v0.py"
            ),
        },
        "observed_vs_expected": {
            "expected_control_result": {
                "result": "mate",
                "plies": 17,
                "basis": "protected validation default-off h40 outcome",
            },
            "control_result": {
                "result": control.get("result"),
                "plies": control.get("plies"),
                "engine_decision_count": control.get("engine_decision_count"),
            },
            "selector_observability_only_result": {
                "result": observability.get("result"),
                "plies": observability.get("plies"),
                "engine_decision_count": observability.get("engine_decision_count"),
            },
            "selector_behavior_enabled_result": {
                "result": behavior.get("result"),
                "plies": behavior.get("plies"),
                "engine_decision_count": behavior.get("engine_decision_count"),
            },
            "selector_behavior_enabled_no_cache_result": {
                "result": no_cache.get("result"),
                "plies": no_cache.get("plies"),
                "engine_decision_count": no_cache.get("engine_decision_count"),
            },
            "expected_behavior": (
                "Selector behavior remains quarantined. If enabled diagnostically, "
                "it should not turn a protected safe-control mate into max_plies."
            ),
            "observed_behavior": (
                "The first protected-row decision is preserve/no-op, but a later "
                "h40 continuation state triggers switch_to_visible_alternative and "
                "the playout enters a non-mating rook/king loop."
            ),
        },
        "first_divergence": first_divergence,
        "exact_differing_code_paths": [
            {
                "mode": "safe/control behavior",
                "path": [
                    "scripts/test_krk_landmark_progress.py::play_to_mate",
                    "scripts/test_krk_landmark_progress.py::choose_move_details",
                    "ranked selected_suggestion is used directly",
                ],
                "evidence": (
                    "control_default_off selects e8a8 via krk.fence_established at "
                    "ply 4 and mates in 17 plies"
                ),
            },
            {
                "mode": "selector observability only",
                "path": [
                    "play_to_mate",
                    "choose_move_details",
                    "_krk_selector_objective_recommendation_for_observation",
                    "recommendation recorded but not applied",
                ],
                "evidence": (
                    "selector_observability_only records prefer_visible_alternative "
                    "at ply 4 but still selects e8a8 and mates in 17"
                ),
            },
            {
                "mode": "selector_behavior enabled behavior",
                "path": [
                    "play_to_mate",
                    "choose_move_details",
                    "_krk_selector_objective_recommendation_for_observation",
                    "_krk_selector_behavior_sandbox_choice",
                    "replacement_suggestion becomes selected_suggestion",
                ],
                "evidence": (
                    "selector_behavior_enabled_cached switches e8a8/"
                    "krk.fence_established to e8b8/krk.edge_trap_close at ply 4"
                ),
            },
        ],
        "hypotheses": [
            {
                "name": "continuation-state mutation",
                "assessment": "against_hidden_mutation_for_move_induced_state_change",
                "evidence_for": (
                    "The enabled path changes the legal move at ply 4, so subsequent "
                    "positions differ by normal chess state transition."
                ),
                "evidence_against": (
                    "No topology mutation, DTM/tablebase lookup, illegal move, or "
                    "out-of-band board mutation is observed; the divergence follows "
                    "the selected legal replacement move."
                ),
            },
            {
                "name": "selector arbitration state leaking across rows",
                "assessment": "unlikely",
                "evidence_for": "No positive evidence.",
                "evidence_against": (
                    "The minimal reproduction uses a single row with a fresh graph and "
                    "engine per variant, and no-cache behavior reproduces the same "
                    "max_plies regression."
                ),
            },
            {
                "name": "h40-specific heuristic interaction",
                "assessment": "primary_cause",
                "evidence_for": (
                    "The first-row decision is preserve/no-op. The failing switch is "
                    "only encountered during h40 continuation at ply 4, where near-edge "
                    "medium-box/far-support terms recommend a visible alternative."
                ),
                "evidence_against": (
                    "The recommendation is deterministic and not limited to h40 code, "
                    "but h40 is the first validation path that exposes the downstream "
                    "effect of later continuation switches."
                ),
            },
            {
                "name": "candidate ordering instability",
                "assessment": "unlikely",
                "evidence_for": (
                    "The behavior selector uses current suggestion order to choose the "
                    "first visible alternative not equal to the original selection."
                ),
                "evidence_against": (
                    "The suggestion order is stable across control and enabled traces. "
                    "The selected replacement is deterministic: original e8a8 entries "
                    "are skipped, then the first e8b8 edge_trap_close entry is chosen."
                ),
            },
            {
                "name": "unsafe fallback behavior",
                "assessment": "contributing_invariant_gap",
                "evidence_for": (
                    "The switch logic has no continuation safety check and no fallback "
                    "to the ranked selected move when the visible alternative has lower "
                    "score/progress evidence in the current state."
                ),
                "evidence_against": (
                    "The switch is bounded to an already-visible suggestion; it does "
                    "not create candidates or route directly."
                ),
            },
            {
                "name": "cache/reuse contamination",
                "assessment": "unlikely",
                "evidence_for": "No positive evidence.",
                "evidence_against": (
                    "selector_behavior_enabled_cached and "
                    "selector_behavior_enabled_no_cache both choose e8b8 at ply 4 and "
                    "both hit max_plies."
                ),
            },
            {
                "name": "another invariant violation",
                "assessment": "safe_continuation_preservation_invariant_missing",
                "evidence_for": (
                    "A protected safe-control h40 playout permits a later "
                    "prefer_visible_alternative switch from a safe fence-established "
                    "choice to an edge-trap alternative using capacity evidence rather "
                    "than ownership/outcome evidence."
                ),
                "evidence_against": (
                    "The diagnostic confirms capacity labels were not treated as "
                    "ownership labels; the issue is insufficient causal evidence for "
                    "safe continuation switching, not a label field mix-up."
                ),
            },
        ],
        "root_cause": {
            "summary": (
                "The regression is caused by a deterministic later h40 continuation "
                "switch, not by the protected row's first selector decision. Enabling "
                "selector_behavior activates recommendation application at every white "
                "decision in play_to_mate. At ply 4 it applies a "
                "prefer_visible_alternative recommendation and replaces the ranked "
                "fence-established move e8a8 with edge_trap_close move e8b8. That "
                "legal switch loses the mating continuation and creates a loop."
            ),
            "suspected_invariant_violation": (
                "Visible positive-capacity alternatives are being treated as sufficient "
                "to override a safe ranked continuation move during h40, even when the "
                "row is a protected safe-preservation control and no runtime-visible "
                "outcome proof supports the override."
            ),
            "why_not_first_row_switch": (
                "At ply 0 the behavior action is no_op with recommendation "
                "preserve_selected_owner. The first move remains a7a8 in both runs. "
                "The first behavior switch appears at white ply 4."
            ),
        },
        "affected_functions_modules": [
            "scripts/test_krk_landmark_progress.py::play_to_mate",
            "scripts/test_krk_landmark_progress.py::choose_move_details",
            "scripts/test_krk_landmark_progress.py::_krk_selector_objective_recommendation_for_observation",
            "scripts/test_krk_landmark_progress.py::_krk_selector_behavior_sandbox_choice",
            "scripts/run_krk_selector_behavior_sandbox_validation_v0.py::_run_h40",
        ],
        "recommended_fix_plan": [
            "Keep selector_behavior quarantined.",
            "Add continuation-level selector behavior trace capture for every h40 white decision.",
            "Create a separate diagnostic-only shadow veto that records when a switch would override a safe ranked continuation move; do not change production behavior.",
            "Review runtime-visible safe-continuation proxies before any veto implementation; do not use offline ownership labels or capacity labels as ownership.",
            "Require protected h40 validation to show zero safe-control regressions and positive target improvements before any future unquarantine review.",
            "If a fix is later proposed, gate it behind an explicit non-production diagnostic flag first and prove default-off equivalence.",
        ],
        "risks_of_fixing": [
            "A broad safe-preservation veto may erase the two observed target improvements.",
            "Using offline row classes or capacity labels at runtime would violate label semantics.",
            "A term-specific veto based only on this row may overfit and miss other continuation regressions.",
            "Adding h40 outcome checks to runtime would violate the no runtime DTM/tablebase/outcome-probe constraint.",
        ],
        "tests_required_before_unquarantine": [
            "current selector behavior regression audit tests",
            "current protected selector behavior sandbox validation tests",
            "new continuation root-cause diagnostic tests",
            "protected h40 validation with full continuation selector decision trace",
            "default-off equivalence",
            "zero score/routing/topology/DTM deltas",
            "zero Stage7 promotion and zero Stage8/selector training rows",
            "full repository test suite",
        ],
        "variant_traces": traces,
        "audit_summary": audit.get("summary"),
    }


def write_markdown(payload: dict[str, Any]) -> None:
    repro = payload["minimal_reproduction"]
    observed = payload["observed_vs_expected"]
    divergence = payload["first_divergence"]
    root = payload["root_cause"]
    lines = [
        "# KRK Selector Behavior Continuation Regression Root Cause v0",
        "",
        "This report is diagnostic-only. It does not change production behavior or unquarantine selector_behavior.",
        "",
        "## Minimal Reproduction",
        "",
    ]
    for key, value in repro.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Observed vs Expected", ""])
    for key, value in observed.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## First Divergence", ""])
    lines.append(f"- ply: `{divergence['ply']}`")
    lines.append(f"- differing_fields: `{divergence['differing_fields']}`")
    lines.append(
        "- control: "
        f"`{divergence['control'].get('move')} / {divergence['control'].get('selected_provider')}`"
    )
    lines.append(
        "- enabled: "
        f"`{divergence['enabled'].get('move')} / {divergence['enabled'].get('selected_provider')}`"
    )
    lines.append(
        "- behavior_action: "
        f"`{divergence['enabled'].get('behavior_action')}`"
    )
    lines.append(
        "- replacement: "
        f"`{divergence['enabled'].get('replacement_provider')} / {divergence['enabled'].get('replacement_move')}`"
    )
    lines.extend(["", "## Root Cause", ""])
    for key, value in root.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Affected Code Paths", ""])
    for item in payload["exact_differing_code_paths"]:
        lines.append(f"- {item['mode']}: `{item['path']}` - {item['evidence']}")
    lines.extend(["", "## Hypotheses", ""])
    for item in payload["hypotheses"]:
        lines.append(
            f"- {item['name']}: `{item['assessment']}`; for: {item['evidence_for']}; against: {item['evidence_against']}"
        )
    lines.extend(["", "## Recommended Fix Plan", ""])
    lines.extend(f"- {item}" for item in payload["recommended_fix_plan"])
    lines.extend(["", "## Risks Of Fixing", ""])
    lines.extend(f"- {item}" for item in payload["risks_of_fixing"])
    lines.extend(["", "## Tests Required Before Unquarantine", ""])
    lines.extend(f"- {item}" for item in payload["tests_required_before_unquarantine"])
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(payload)
    print(OUT_JSON)
    print(OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
