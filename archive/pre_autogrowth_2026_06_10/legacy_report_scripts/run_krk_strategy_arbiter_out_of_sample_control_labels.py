#!/usr/bin/env python3
"""Run bounded KRK strategy-arbiter out-of-sample control labels.

This is an offline diagnostic label run from a reviewed manifest. It writes
non-causal evidence only and does not change runtime defaults, topology,
promotion status, training state, or provider routing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import chess


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import test_krk_landmark_progress as diag  # noqa: E402
from recon_lite.engine import ReConEngine  # noqa: E402


MANIFEST = Path("reports/krk_strategy_arbiter_out_of_sample_execution_manifest_v0.json")
REVIEW = Path("reports/krk_strategy_arbiter_out_of_sample_execution_manifest_review_v0.json")
OUT_JSON = Path("reports/krk_strategy_arbiter_out_of_sample_control_labels_v0.json")
OUT_MD = Path("reports/krk_strategy_arbiter_out_of_sample_control_labels_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _stable_seed(value: str) -> int:
    return int(hashlib.sha1(value.encode("utf-8")).hexdigest()[:8], 16)


def _load_graph_engine(repo_root: Path, topology_path: str) -> tuple[Any, ReConEngine]:
    graph = diag.build_graph_from_topology(repo_root / topology_path)
    return graph, ReConEngine(graph)


def _settings(binding: dict[str, Any]) -> dict[str, Any]:
    return binding.get("profile_settings") or {}


def _choose_initial(
    graph: Any,
    engine: ReConEngine,
    board: chess.Board,
    job: dict[str, Any],
) -> dict[str, Any]:
    binding = job.get("execution_binding") or {}
    settings = _settings(binding)
    return diag.choose_move_details(
        graph,
        engine,
        board,
        max_ticks=int(binding.get("max_ticks") or 200),
        stage_filter=None,
        suggestion_limit=int(binding.get("suggestion_limit") or 10),
        successor_affordance_layer_enabled=bool(settings.get("successor_affordance_layer_enabled")),
        successor_role_license_enabled=bool(settings.get("successor_role_license_enabled")),
        successor_role_scoped_move_shape_enabled=bool(
            settings.get("successor_role_scoped_move_shape_enabled")
        ),
        successor_role_scoped_move_shape_bonus=float(
            settings.get("successor_role_scoped_move_shape_bonus") or 0.0
        ),
        stagnation_breaker_enabled=bool(settings.get("stagnation_breaker_enabled")),
        stagnation_breaker_bonus=float(settings.get("stagnation_breaker_bonus") or 0.0),
        post_break_continuation_enabled=bool(settings.get("post_break_continuation_enabled")),
        post_break_continuation_bonus=float(settings.get("post_break_continuation_bonus") or 0.0),
        successor_stage0_drift_penalty=float(settings.get("successor_stage0_drift_penalty") or 0.0),
        early_stop_stable_suggestions=int(binding.get("early_stop_stable_suggestions") or 0),
        active_landmark_label=str(job.get("active_landmark_label") or ""),
        enable_diagnostic_caches=bool(binding.get("enable_diagnostic_caches")),
    )


def _selected_provider(move_details: dict[str, Any]) -> str | None:
    suggestion = diag._selected_engine_suggestion(move_details)
    if not suggestion:
        return None
    return diag._skill_id_for_suggestion(suggestion)


def _same_move_providers(move_details: dict[str, Any], selected_move: str | None) -> list[dict[str, Any]]:
    if not selected_move:
        return []
    providers = []
    for item in move_details.get("suggestions") or []:
        if item.get("move") != selected_move:
            continue
        providers.append(
            {
                "provider_id": diag._skill_id_for_suggestion(item),
                "actuator": item.get("actuator"),
                "score": item.get("score"),
                "move_uci": item.get("move"),
            }
        )
    return providers


def _run_playout(
    graph: Any,
    engine: ReConEngine,
    board: chess.Board,
    rng: random.Random,
    job: dict[str, Any],
    *,
    forced_successor_skill: str | None = None,
    trace: bool = False,
) -> dict[str, Any]:
    binding = job.get("execution_binding") or {}
    settings = _settings(binding)
    horizon = int(job.get("horizon") or 40)
    return diag.play_to_mate(
        graph,
        engine,
        board,
        rng,
        str(job.get("active_landmark_label") or "out_of_sample_control"),
        None,
        horizon,
        str(binding.get("black_policy") or "adversarial"),
        trace=trace,
        trace_max_plies=horizon if trace else None,
        max_ticks=int(binding.get("max_ticks") or 200),
        suggestion_limit=int(binding.get("suggestion_limit") or 10),
        successor_affordance_layer_enabled=bool(settings.get("successor_affordance_layer_enabled")),
        successor_role_license_enabled=bool(settings.get("successor_role_license_enabled")),
        successor_role_scoped_move_shape_enabled=bool(
            settings.get("successor_role_scoped_move_shape_enabled")
        ),
        successor_role_scoped_move_shape_bonus=float(
            settings.get("successor_role_scoped_move_shape_bonus") or 0.0
        ),
        stagnation_breaker_enabled=bool(settings.get("stagnation_breaker_enabled")),
        stagnation_breaker_bonus=float(settings.get("stagnation_breaker_bonus") or 0.0),
        post_break_continuation_enabled=bool(settings.get("post_break_continuation_enabled")),
        post_break_continuation_bonus=float(settings.get("post_break_continuation_bonus") or 0.0),
        successor_stage0_drift_penalty=float(settings.get("successor_stage0_drift_penalty") or 0.0),
        forced_successor_skill=forced_successor_skill,
        early_stop_stable_suggestions=int(binding.get("early_stop_stable_suggestions") or 0),
        enable_diagnostic_caches=bool(binding.get("enable_diagnostic_caches")),
    )


def _label_from_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "result": result.get("result"),
        "plies": result.get("plies"),
        "engine_decision_count": result.get("engine_decision_count"),
        "engine_ticks_total": result.get("engine_ticks_total"),
        "engine_ticks_max": result.get("engine_ticks_max"),
        "engine_early_stop_count": result.get("engine_early_stop_count"),
        "trace_included": "trace" in result,
        "final_fen": result.get("final_fen"),
        "stagnation_summary": result.get("stagnation_summary"),
    }


def _run_job(
    repo_root: Path,
    job: dict[str, Any],
    cache: dict[str, tuple[Any, ReConEngine]],
) -> dict[str, Any]:
    binding = job.get("execution_binding") or {}
    topology_path = str(binding.get("topology_path") or "")
    if topology_path not in cache:
        cache[topology_path] = _load_graph_engine(repo_root, topology_path)
    graph, engine = cache[topology_path]
    board = chess.Board(str(job.get("fen") or ""))
    initial = _choose_initial(graph, engine, board, job)
    selected_move = initial.get("move")
    selected_provider = _selected_provider(initial)
    same_move_providers = _same_move_providers(initial, selected_move)
    base_seed = _stable_seed(str(job.get("job_id") or ""))

    selected_result = _run_playout(
        graph,
        engine,
        board.copy(),
        random.Random(base_seed),
        job,
        forced_successor_skill=None,
        trace=False,
    )
    if selected_result.get("result") != "mate":
        selected_result = _run_playout(
            graph,
            engine,
            board.copy(),
            random.Random(base_seed),
            job,
            forced_successor_skill=None,
            trace=True,
        )

    forced_result: dict[str, Any] | None = None
    if selected_provider:
        forced_result = _run_playout(
            graph,
            engine,
            board.copy(),
            random.Random(base_seed),
            job,
            forced_successor_skill=selected_provider,
            trace=False,
        )
        if forced_result.get("result") != "mate":
            forced_result = _run_playout(
                graph,
                engine,
                board.copy(),
                random.Random(base_seed),
                job,
                forced_successor_skill=selected_provider,
                trace=True,
            )

    selected_label = _label_from_result(selected_result)
    forced_label = _label_from_result(forced_result or {}) if forced_result else None
    return {
        "schema_version": "krk_strategy_arbiter_out_of_sample_control_label.v0",
        "causal_status": "non_causal_outcome_label",
        "job_id": job.get("job_id"),
        "frame_id": job.get("frame_id"),
        "state_id": job.get("state_id"),
        "source_stage": job.get("source_stage"),
        "active_landmark_label": job.get("active_landmark_label"),
        "fen": job.get("fen"),
        "horizon": job.get("horizon"),
        "topology_path": binding.get("topology_path"),
        "topology_version": binding.get("topology_version"),
        "composition_profile": binding.get("composition_profile"),
        "selected_provider": selected_provider,
        "selected_move": selected_move,
        "initial_same_move_providers": same_move_providers,
        "initial_provider_count": len({item.get("provider_id") for item in same_move_providers}),
        "selected_playout_success": selected_label,
        "forced_provider_conversion_for_selected_provider": forced_label,
        "same_move_provider_compatibility_when_available": {
            "available": bool(same_move_providers),
            "executed": False,
            "reason": "recorded_initial_same_move_provider_set_only_to_keep_label_run_bounded",
            "provider_count": len({item.get("provider_id") for item in same_move_providers}),
        },
        "guardrail_safe_ownership": {
            "safe": selected_label.get("result") == "mate",
            "basis": "selected_playout_success_h40",
        },
        "shadow_candidate_delta": {
            "available": False,
            "reason": "shadow deltas require paired selector intervention; no selector was run",
        },
        "runtime_behavior_changed": False,
        "labels_generated": True,
    }


def run_labels(repo_root: Path) -> dict[str, Any]:
    manifest = _load_json(repo_root / MANIFEST)
    review = _load_json(repo_root / REVIEW)
    if manifest.get("causal_status") != "non_causal_execution_manifest":
        raise ValueError("manifest must remain non-causal")
    if review.get("decision", {}).get("bounded_label_run_allowed_after_review") is not True:
        raise ValueError("manifest review must allow bounded label run before execution")
    if not (manifest.get("binding_summary") or {}).get("all_bindings_valid"):
        raise ValueError("manifest bindings must be valid")
    cache: dict[str, tuple[Any, ReConEngine]] = {}
    start = time.perf_counter()
    labels = [_run_job(repo_root, job, cache) for job in manifest.get("jobs") or []]
    wall_time = round(time.perf_counter() - start, 6)
    selected_counts = Counter(label["selected_playout_success"].get("result") for label in labels)
    forced_counts = Counter(
        (label.get("forced_provider_conversion_for_selected_provider") or {}).get("result")
        for label in labels
    )
    by_stage = Counter(
        f"{label.get('source_stage')}:{label['selected_playout_success'].get('result')}"
        for label in labels
    )
    payload = {
        "schema_version": "krk_strategy_arbiter_out_of_sample_control_labels.v0",
        "causal_status": "non_causal_label_run",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(MANIFEST), str(REVIEW)],
        "summary": {
            "label_count": len(labels),
            "wall_time_sec": wall_time,
            "selected_result_counts": dict(selected_counts),
            "forced_selected_provider_result_counts": dict(forced_counts),
            "selected_result_counts_by_stage": dict(by_stage),
            "trace_failures_only": True,
            "stage7_training_rows": 0,
        },
        "labels": labels,
        "recommended_next_step": "probe_out_of_sample_control_labels_before_any_selector_sandbox",
        "blocked_next_steps": [
            "runtime_arbiter",
            "selector_sandbox",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }
    validate_payload(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("causal_status") != "non_causal_label_run":
        raise ValueError("label run must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_arbiter_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    for label in payload.get("labels") or []:
        if label.get("causal_status") != "non_causal_outcome_label":
            raise ValueError("labels must remain non-causal")
        if label.get("source_stage") == "stage7":
            raise ValueError("Stage 7 must not be a training/control label source")


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# KRK Strategy Arbiter Out-of-Sample Control Labels v0",
        "",
        "This is a bounded offline non-causal label run. It did not implement a selector, "
        "change runtime defaults, promote Stage 7, train Stage 8, or mutate topology.",
        "",
        "## Summary",
        "",
        f"- Label count: `{summary['label_count']}`",
        f"- Wall time sec: `{summary['wall_time_sec']}`",
        f"- Selected result counts: `{summary['selected_result_counts']}`",
        f"- Forced selected-provider result counts: `{summary['forced_selected_provider_result_counts']}`",
        f"- Selected result counts by stage: `{summary['selected_result_counts_by_stage']}`",
        f"- Stage 7 training rows: `{summary['stage7_training_rows']}`",
        "",
        "## Labels",
        "",
    ]
    for label in payload["labels"]:
        forced = label.get("forced_provider_conversion_for_selected_provider") or {}
        lines.append(
            f"- `{label['state_id']}` stage=`{label['source_stage']}` "
            f"selected_provider=`{label.get('selected_provider')}` "
            f"selected=`{label['selected_playout_success'].get('result')}` "
            f"forced_selected=`{forced.get('result')}`"
        )
    lines.extend(
        [
            "",
            "## Recommended Next Step",
            "",
            f"`{payload['recommended_next_step']}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(repo_root: Path, payload: dict[str, Any]) -> None:
    (repo_root / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (repo_root / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    payload = run_labels(repo_root)
    write_outputs(repo_root, payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
