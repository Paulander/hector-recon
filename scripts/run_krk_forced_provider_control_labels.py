#!/usr/bin/env python3
"""Run bounded KRK forced-provider control labels.

This is an offline diagnostic label run. It forces the configured provider only
for the first White decision, releases to the normal topology afterward, and
writes non-causal outcome labels. It does not change runtime defaults, topology,
promotion status, or training state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import chess

sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_krk_landmark_progress as diag  # noqa: E402
from recon_lite.engine import ReConEngine  # noqa: E402


MANIFEST = Path("reports/krk_forced_provider_label_execution_manifest_v0.json")


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


def _run_job(repo_root: Path, job: dict[str, Any], cache: dict[str, tuple[Any, ReConEngine]]) -> dict[str, Any]:
    binding = job.get("execution_binding") or {}
    topology_path = str(binding.get("topology_path") or "")
    if topology_path not in cache:
        cache[topology_path] = _load_graph_engine(repo_root, topology_path)
    graph, engine = cache[topology_path]
    board = chess.Board(str(job.get("fen") or ""))
    settings = binding.get("profile_settings") or {}
    horizon = int(job.get("horizon") or 40)
    rng = random.Random(_stable_seed(str(job.get("job_id") or "")))
    result = diag.play_to_mate(
        graph,
        engine,
        board,
        rng,
        str(job.get("active_landmark_label") or "forced_provider_control"),
        None,
        horizon,
        str(binding.get("black_policy") or "adversarial"),
        trace=False,
        max_ticks=int(binding.get("max_ticks") or 200),
        suggestion_limit=int(binding.get("suggestion_limit") or 10),
        successor_affordance_layer_enabled=bool(settings.get("successor_affordance_layer_enabled")),
        successor_role_license_enabled=bool(settings.get("successor_role_license_enabled")),
        successor_role_scoped_move_shape_enabled=bool(settings.get("successor_role_scoped_move_shape_enabled")),
        successor_role_scoped_move_shape_bonus=float(settings.get("successor_role_scoped_move_shape_bonus") or 0.0),
        stagnation_breaker_enabled=bool(settings.get("stagnation_breaker_enabled")),
        stagnation_breaker_bonus=float(settings.get("stagnation_breaker_bonus") or 0.0),
        post_break_continuation_enabled=bool(settings.get("post_break_continuation_enabled")),
        post_break_continuation_bonus=float(settings.get("post_break_continuation_bonus") or 0.0),
        successor_stage0_drift_penalty=float(settings.get("successor_stage0_drift_penalty") or 0.0),
        forced_successor_skill=str(job.get("provider_id") or ""),
        early_stop_stable_suggestions=int(binding.get("early_stop_stable_suggestions") or 0),
        enable_diagnostic_caches=bool(binding.get("enable_diagnostic_caches")),
    )
    if result.get("result") != "mate" and str(binding.get("trace_mode")) == "failures_only":
        rng = random.Random(_stable_seed(str(job.get("job_id") or "")))
        result = diag.play_to_mate(
            graph,
            engine,
            board,
            rng,
            str(job.get("active_landmark_label") or "forced_provider_control"),
            None,
            horizon,
            str(binding.get("black_policy") or "adversarial"),
            trace=True,
            trace_max_plies=horizon,
            max_ticks=int(binding.get("max_ticks") or 200),
            suggestion_limit=int(binding.get("suggestion_limit") or 10),
            successor_affordance_layer_enabled=bool(settings.get("successor_affordance_layer_enabled")),
            successor_role_license_enabled=bool(settings.get("successor_role_license_enabled")),
            successor_role_scoped_move_shape_enabled=bool(settings.get("successor_role_scoped_move_shape_enabled")),
            successor_role_scoped_move_shape_bonus=float(settings.get("successor_role_scoped_move_shape_bonus") or 0.0),
            stagnation_breaker_enabled=bool(settings.get("stagnation_breaker_enabled")),
            stagnation_breaker_bonus=float(settings.get("stagnation_breaker_bonus") or 0.0),
            post_break_continuation_enabled=bool(settings.get("post_break_continuation_enabled")),
            post_break_continuation_bonus=float(settings.get("post_break_continuation_bonus") or 0.0),
            successor_stage0_drift_penalty=float(settings.get("successor_stage0_drift_penalty") or 0.0),
            forced_successor_skill=str(job.get("provider_id") or ""),
            early_stop_stable_suggestions=int(binding.get("early_stop_stable_suggestions") or 0),
            enable_diagnostic_caches=bool(binding.get("enable_diagnostic_caches")),
        )
    first = result.get("first_successor") if isinstance(result.get("first_successor"), dict) else {}
    engine_details = first.get("engine") if isinstance(first.get("engine"), dict) else {}
    label = {
        "schema_version": "krk_forced_provider_control_label.v0",
        "causal_status": "non_causal_outcome_label",
        "job_id": job.get("job_id"),
        "frame_id": job.get("frame_id"),
        "state_id": job.get("state_id"),
        "source_stage": job.get("source_stage"),
        "provider_id": job.get("provider_id"),
        "requested_reference_move": job.get("move_uci"),
        "forced_first_move": first.get("move"),
        "forced_successor_available": engine_details.get("forced_successor_available"),
        "result": result.get("result"),
        "plies": result.get("plies"),
        "horizon": horizon,
        "black_policy": binding.get("black_policy"),
        "topology_path": binding.get("topology_path"),
        "topology_version": binding.get("topology_version"),
        "composition_profile": binding.get("composition_profile"),
        "provider_version": binding.get("provider_version"),
        "engine_decision_count": result.get("engine_decision_count"),
        "engine_ticks_total": result.get("engine_ticks_total"),
        "engine_early_stop_count": result.get("engine_early_stop_count"),
        "trace_included": "trace" in result,
    }
    if "trace" in result:
        label["trace"] = result["trace"]
        label["final_fen"] = result.get("final_fen")
        label["stagnation_summary"] = result.get("stagnation_summary")
    return label


def run_labels(repo_root: Path) -> dict[str, Any]:
    manifest = _load_json(repo_root / MANIFEST)
    if manifest.get("causal_status") != "non_causal_execution_manifest":
        raise ValueError("execution manifest must remain non-causal")
    if not (manifest.get("binding_summary") or {}).get("all_bindings_valid"):
        raise ValueError("execution manifest bindings must be valid before label run")
    cache: dict[str, tuple[Any, ReConEngine]] = {}
    labels = [_run_job(repo_root, job, cache) for job in manifest.get("jobs") or []]
    result_counts = Counter(str(label.get("result") or "unknown") for label in labels)
    by_stage = Counter(f"{label.get('source_stage')}:{label.get('result')}" for label in labels)
    payload = {
        "schema_version": "krk_forced_provider_control_labels.v0",
        "causal_status": "non_causal_label_run",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(MANIFEST)],
        "summary": {
            "label_count": len(labels),
            "result_counts": dict(result_counts),
            "result_counts_by_stage": dict(by_stage),
            "trace_failures_only": True,
        },
        "labels": labels,
        "recommended_next_step": "merge_forced_provider_control_labels_and_rerun_stratified_probe",
        "blocked_next_steps": [
            "runtime_arbiter",
            "runtime_internal_terminal",
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


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Forced Provider Control Labels v0",
        "",
        "This is an offline non-causal label run. It forced each configured provider "
        "only for the first White move, then released control to the normal topology.",
        "",
        "## Summary",
        "",
        f"- Label count: `{payload['summary']['label_count']}`",
        f"- Result counts: `{payload['summary']['result_counts']}`",
        f"- Result counts by stage: `{payload['summary']['result_counts_by_stage']}`",
        "",
        "## Labels",
        "",
    ]
    for label in payload["labels"]:
        lines.append(
            f"- `{label['job_id']}` stage=`{label['source_stage']}` provider=`{label['provider_id']}` "
            f"forced_move=`{label.get('forced_first_move')}` result=`{label['result']}` plies=`{label['plies']}`"
        )
    lines.extend(["", "## Recommended Next Step", "", f"`{payload['recommended_next_step']}`", ""])
    return "\n".join(lines)


def write_outputs(payload: dict[str, Any], report_root: Path) -> None:
    report_root.mkdir(parents=True, exist_ok=True)
    (report_root / "krk_forced_provider_control_labels_v0.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (report_root / "krk_forced_provider_control_labels_v0.md").write_text(
        render_markdown(payload), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--report-root", type=Path, default=Path("reports"))
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    report_root = args.report_root
    if not report_root.is_absolute():
        report_root = repo_root / report_root
    payload = run_labels(repo_root)
    write_outputs(payload, report_root)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
