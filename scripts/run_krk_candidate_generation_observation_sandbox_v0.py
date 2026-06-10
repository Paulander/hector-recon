#!/usr/bin/env python3
"""Run the default-off KRK candidate-generation observation sandbox smoke."""

from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import chess

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from recon_lite.engine import ReConEngine  # noqa: E402
from recon_lite_chess.graph.builder import build_graph_from_topology  # noqa: E402
from scripts.test_krk_landmark_progress import (  # noqa: E402
    COMPOSITION_PROFILE_HANDOFF_V1,
    HANDOFF_COMPOSITION_V1_SETTINGS,
    _skill_id_for_suggestion,
    choose_move_details,
    play_to_mate,
)


TOPOLOGY = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json"
)
CAPACITY_FRAMES = Path("reports/krk_protected_provider_coverage_frames_v0.json")
RANKED_FRAMES = Path("reports/krk_ranked_strategy_proposal_frames_v1.json")
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_candidate_generation_observation_sandbox_v0.json"
)
OUT_MD = Path("reports/strategy_arbitration/krk_candidate_generation_observation_sandbox_v0.md")


def _profile_kwargs() -> dict[str, Any]:
    settings = dict(HANDOFF_COMPOSITION_V1_SETTINGS)
    return {
        "successor_affordance_layer_enabled": bool(settings["successor_affordance_layer_enabled"]),
        "successor_role_license_enabled": bool(settings["successor_role_license_enabled"]),
        "successor_role_scoped_move_shape_enabled": bool(
            settings["successor_role_scoped_move_shape_enabled"]
        ),
        "successor_role_scoped_move_shape_bonus": float(
            settings["successor_role_scoped_move_shape_bonus"]
        ),
        "stagnation_breaker_enabled": bool(settings["stagnation_breaker_enabled"]),
        "stagnation_breaker_bonus": float(settings["stagnation_breaker_bonus"]),
        "post_break_continuation_enabled": bool(settings["post_break_continuation_enabled"]),
        "post_break_continuation_bonus": float(settings["post_break_continuation_bonus"]),
        "successor_stage0_drift_penalty": float(settings["successor_stage0_drift_penalty"]),
    }


def _new_graph_engine() -> tuple[Any, ReConEngine]:
    graph = build_graph_from_topology(ROOT / TOPOLOGY)
    return graph, ReConEngine(graph)


def _selected_provider(details: dict[str, Any]) -> str | None:
    selected = details.get("selected_suggestion")
    if isinstance(selected, dict) and selected:
        return _skill_id_for_suggestion(selected)
    return None


def _compact_decision(details: dict[str, Any]) -> dict[str, Any]:
    return {
        "move": details.get("move"),
        "selected_provider": _selected_provider(details),
        "confidence": details.get("confidence"),
        "observation_present": bool(details.get("krk_candidate_generation_observation")),
        "observation": _compact_observation(
            details.get("krk_candidate_generation_observation") or {}
        ),
    }


def _compact_observation(observation: dict[str, Any]) -> dict[str, Any]:
    if not observation:
        return {}
    return {
        "schema_version": observation.get("schema_version"),
        "sandbox_id": observation.get("sandbox_id"),
        "causal_status": observation.get("causal_status"),
        "direct_request": observation.get("direct_request"),
        "score_delta": observation.get("score_delta"),
        "candidate_count": observation.get("candidate_count"),
        "candidate_count_by_source": dict(observation.get("candidate_count_by_source") or {}),
        "capacity_evidence_counts": dict(observation.get("capacity_evidence_counts") or {}),
        "protected_status_counts": dict(observation.get("protected_status_counts") or {}),
        "frames": list(observation.get("frames") or []),
        "selected_provider_before_observation": observation.get(
            "selected_provider_before_observation"
        ),
        "selected_move_before_observation": observation.get("selected_move_before_observation"),
        "sample_frames": list(observation.get("frames") or [])[:5],
    }


def _same_decision(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return (
        left.get("move") == right.get("move")
        and left.get("selected_provider") == right.get("selected_provider")
        and left.get("confidence") == right.get("confidence")
    )


def _load_cases() -> list[dict[str, Any]]:
    capacity = json.loads((ROOT / CAPACITY_FRAMES).read_text(encoding="utf-8"))
    ranked = json.loads((ROOT / RANKED_FRAMES).read_text(encoding="utf-8"))
    cases: list[dict[str, Any]] = []
    seen_stages: set[str] = set()
    for row in capacity.get("rows") or []:
        stage = str(row.get("source_stage") or "")
        if stage in {"stage5", "stage6"} and stage not in seen_stages:
            cases.append({
                "case_id": f"protected_{stage}",
                "fen": row["fen"],
                "active_landmark_label": row.get("active_landmark_label") or row.get("provider_family"),
                "source_stage": stage,
                "held_out": False,
            })
            seen_stages.add(stage)
    for row in ranked.get("rows") or []:
        if row.get("stage7_challenge_row") and row.get("fen"):
            cases.append({
                "case_id": "heldout_stage7",
                "fen": row["fen"],
                "active_landmark_label": row.get("active_landmark_label") or "box_shrink",
                "source_stage": "stage7",
                "held_out": True,
            })
            break
    return cases


def _run_decision(case: dict[str, Any], *, enabled: bool) -> dict[str, Any]:
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
        krk_candidate_generation_observability_enabled=enabled,
        enable_diagnostic_caches=True,
        **_profile_kwargs(),
    )
    return _compact_decision(details)


def _run_playout(case: dict[str, Any], *, enabled: bool) -> dict[str, Any]:
    graph, engine = _new_graph_engine()
    board = chess.Board(str(case["fen"]))
    result = play_to_mate(
        graph,
        engine,
        board,
        random.Random(7),
        label=str(case["active_landmark_label"]),
        stage_filter=None,
        max_plies=8,
        black_policy="adversarial",
        trace=False,
        max_ticks=200,
        suggestion_limit=10,
        early_stop_stable_suggestions=2,
        krk_candidate_generation_observability_enabled=enabled,
        enable_diagnostic_caches=True,
        **_profile_kwargs(),
    )
    return {
        "result": result.get("result"),
        "plies": result.get("plies"),
        "engine_decision_count": result.get("engine_decision_count"),
        "engine_ticks_total": result.get("engine_ticks_total"),
    }


def _aggregate_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    source_counts: Counter[str] = Counter()
    capacity_counts: Counter[str] = Counter()
    protected_counts: Counter[str] = Counter()
    candidate_count = 0
    protected_candidate_count = 0
    heldout_candidate_count = 0
    selected_changed = False
    playout_changed = False
    default_off_no_frames = True
    frame_invariants_hold = True
    for row in cases:
        disabled = row["flag_off_decision"]
        enabled = row["enabled_decision"]
        obs = enabled.get("observation") or {}
        candidate_count += int(obs.get("candidate_count", 0) or 0)
        source_counts.update(obs.get("candidate_count_by_source") or {})
        capacity_counts.update(obs.get("capacity_evidence_counts") or {})
        protected_counts.update(obs.get("protected_status_counts") or {})
        protected_candidate_count += int(
            (obs.get("protected_status_counts") or {}).get("protected_control", 0) or 0
        )
        heldout_candidate_count += int(
            (obs.get("protected_status_counts") or {}).get("held_out_stage7_challenge", 0) or 0
        )
        selected_changed = selected_changed or not _same_decision(disabled, enabled)
        playout_changed = playout_changed or (
            row["flag_off_playout"].get("result") != row["enabled_playout"].get("result")
            or row["flag_off_playout"].get("plies") != row["enabled_playout"].get("plies")
        )
        default_off_no_frames = default_off_no_frames and not disabled.get("observation_present")
        for frame in obs.get("sample_frames") or []:
            frame_invariants_hold = frame_invariants_hold and (
                frame.get("direct_request") is False
                and float(frame.get("score_delta", 1.0) or 0.0) == 0.0
                and frame.get("causal_status") == "observation_only"
            )
    return {
        "generated_candidate_count": candidate_count,
        "generated_candidate_count_by_source": dict(sorted(source_counts.items())),
        "protected_candidate_count": protected_candidate_count,
        "stage7_heldout_candidate_count": heldout_candidate_count,
        "capacity_evidence_counts": dict(sorted(capacity_counts.items())),
        "protected_status_counts": dict(sorted(protected_counts.items())),
        "selected_move_or_provider_changed": selected_changed,
        "playout_result_or_plies_changed": playout_changed,
        "default_off_emitted_no_observation_frames": default_off_no_frames,
        "frame_invariants_hold_for_samples": frame_invariants_hold,
    }


def build_smoke() -> dict[str, Any]:
    rows = []
    for case in _load_cases():
        flag_off_decision = _run_decision(case, enabled=False)
        enabled_decision = _run_decision(case, enabled=True)
        flag_off_playout = _run_playout(case, enabled=False)
        enabled_playout = _run_playout(case, enabled=True)
        rows.append({
            **case,
            "flag_off_decision": flag_off_decision,
            "enabled_decision": enabled_decision,
            "flag_off_playout": flag_off_playout,
            "enabled_playout": enabled_playout,
            "selected_move_provider_score_equivalent": _same_decision(
                flag_off_decision,
                enabled_decision,
            ),
            "playout_equivalent": (
                flag_off_playout.get("result") == enabled_playout.get("result")
                and flag_off_playout.get("plies") == enabled_playout.get("plies")
            ),
        })
    summary = _aggregate_cases(rows)
    equivalence_passed = (
        bool(rows)
        and all(row["selected_move_provider_score_equivalent"] for row in rows)
        and all(row["playout_equivalent"] for row in rows)
        and summary["default_off_emitted_no_observation_frames"]
        and not summary["selected_move_or_provider_changed"]
        and not summary["playout_result_or_plies_changed"]
    )
    frames_emitted = summary["generated_candidate_count"] > 0
    invariant_passed = summary["frame_invariants_hold_for_samples"]
    decision_status = "observation_sandbox_ready_for_non_causal_coverage_analysis"
    if not equivalence_passed:
        decision_status = "observation_sandbox_failed_equivalence"
    elif not frames_emitted or not invariant_passed:
        decision_status = "observation_sandbox_emits_unusable_frames"
    return {
        "schema_version": "krk_candidate_generation_observation_sandbox_smoke.v0",
        "sandbox_id": "sandbox.krk.candidate_generation_observation_v0",
        "causal_status": "runtime_observation_only_sandbox_smoke",
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_provider_suppression": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "topology": str(TOPOLOGY),
        "profile": COMPOSITION_PROFILE_HANDOFF_V1,
        "summary": summary,
        "cases": rows,
        "decision": {
            "status": decision_status,
            "default_off_equivalence_passed": equivalence_passed,
            "observation_frames_emitted": frames_emitted,
            "frame_invariants_passed": invariant_passed,
            "recommended_next_step": "non_causal_candidate_coverage_analysis_using_emitted_frames",
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Candidate-Generation Observation Sandbox v0",
        "",
        "This runtime smoke exercises the approved default-off observation-only candidate-generation sandbox.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- default_off_equivalence_passed: `{payload['decision']['default_off_equivalence_passed']}`",
        f"- observation_frames_emitted: `{payload['decision']['observation_frames_emitted']}`",
        f"- frame_invariants_passed: `{payload['decision']['frame_invariants_passed']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        "",
        "## Summary",
        "",
        f"- generated_candidate_count: {summary['generated_candidate_count']}",
        f"- generated_candidate_count_by_source: `{summary['generated_candidate_count_by_source']}`",
        f"- protected_candidate_count: {summary['protected_candidate_count']}",
        f"- stage7_heldout_candidate_count: {summary['stage7_heldout_candidate_count']}",
        f"- capacity_evidence_counts: `{summary['capacity_evidence_counts']}`",
        f"- selected_move_or_provider_changed: `{summary['selected_move_or_provider_changed']}`",
        f"- playout_result_or_plies_changed: `{summary['playout_result_or_plies_changed']}`",
        "",
        "## Cases",
        "",
    ]
    for row in payload["cases"]:
        lines.extend([
            f"### {row['case_id']}",
            "",
            f"- source_stage: `{row['source_stage']}`",
            f"- held_out: `{row['held_out']}`",
            f"- selected_move_provider_score_equivalent: `{row['selected_move_provider_score_equivalent']}`",
            f"- playout_equivalent: `{row['playout_equivalent']}`",
            f"- enabled_candidate_count: {row['enabled_decision']['observation'].get('candidate_count', 0)}",
            "",
        ])
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_smoke()
    (ROOT / OUT_JSON).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
