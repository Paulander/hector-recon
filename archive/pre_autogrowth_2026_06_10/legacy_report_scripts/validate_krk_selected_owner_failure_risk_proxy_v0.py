#!/usr/bin/env python3
"""Validate selected-owner failure-risk proxy on independent protected pairs.

This script creates a bounded protected-only validation set, runs h40 labels for
the current selected owner and one forced alternative owner, and evaluates the
visible proxy discovered in v0. It remains non-causal and does not implement a
runtime selector or terminal.
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
from build_krk_ownership_selection_context_dataset_v0 import _post_move_context  # noqa: E402
from extract_krk_selected_owner_failure_risk_terms_v0 import _classification_metrics  # noqa: E402
from generate_krk_strategy_arbiter_out_of_sample_execution_manifest import (  # noqa: E402
    STAGE_CONFIGS,
    _binding_for_stage,
)
from recon_lite.engine import ReConEngine  # noqa: E402
from recon_lite_chess.routing import stable_record_id  # noqa: E402
from run_krk_strategy_arbiter_out_of_sample_control_labels import (  # noqa: E402
    _choose_initial,
    _label_from_result,
    _load_graph_engine,
    _run_playout,
    _selected_provider,
)


DISCOVERY_DATASET = Path("reports/krk_state_local_paired_runtime_proxy_dataset_v0.json")
DISCOVERY_REVIEW = Path("reports/krk_selected_owner_failure_risk_visible_proxy_review_v0.json")

OUT_MANIFEST_JSON = Path("reports/krk_selected_owner_failure_risk_proxy_independent_manifest_v0.json")
OUT_MANIFEST_MD = Path("reports/krk_selected_owner_failure_risk_proxy_independent_manifest_v0.md")
OUT_LABELS_JSON = Path("reports/krk_selected_owner_failure_risk_proxy_independent_labels_v0.json")
OUT_LABELS_MD = Path("reports/krk_selected_owner_failure_risk_proxy_independent_labels_v0.md")
OUT_VALIDATION_JSON = Path("reports/krk_selected_owner_failure_risk_proxy_independent_validation_v0.json")
OUT_VALIDATION_MD = Path("reports/krk_selected_owner_failure_risk_proxy_independent_validation_v0.md")
OUT_PACKET_JSON = Path("reports/krk_state_local_paired_selector_runtime_proxy_review_packet_v0.json")
OUT_PACKET_MD = Path("reports/krk_state_local_paired_selector_runtime_proxy_review_packet_v0.md")


RUNTIME_FALSE_KEYS = (
    "runtime_behavior_changed",
    "runtime_defaults_changed",
    "runtime_selector_implemented",
    "runtime_candidate_generator_implemented",
    "runtime_terminals_added",
    "runtime_dtm_or_tablebase_lookup",
    "gameplay_topology_mutation",
    "stage7_promotion_allowed",
    "stage8_training_allowed",
    "selector_training_allowed",
)

EDGE_TRAP_ALTERNATIVES = (
    "krk.edge_trap_close",
    "krk.edge_trap_enemy_between",
    "krk.edge_trap_wrong_tempo",
)


def _runtime_false_block() -> dict[str, bool]:
    return {key: False for key in RUNTIME_FALSE_KEYS}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _stable_seed(*parts: Any) -> int:
    text = "|".join(str(part) for part in parts)
    return int(hashlib.sha1(text.encode("utf-8")).hexdigest()[:8], 16)


def _state_id_from_board(board: chess.Board) -> str:
    return stable_record_id("state", board.board_fen(), board.turn)


def _provider_family(provider_id: str | None) -> str:
    text = str(provider_id or "")
    if text == "krk.stage0_basin":
        return "stage0_basin"
    if text == "krk.drive_to_edge":
        return "drive_to_edge"
    if text == "krk.fence_established":
        return "fence_established"
    if text.startswith("krk.edge_trap"):
        return "edge_trap"
    return "other"


def _runtime_features(
    *,
    fen: str,
    active_landmark_label: str,
    source_stage: str,
    selected_provider: str,
    selected_move: str | None,
    alternative_provider: str,
) -> dict[str, Any]:
    move_context = _post_move_context(fen, selected_move)
    terminal = move_context.get("post_terminal_context") or {}
    # Initial-state context is not required by the proxy definition; keep this
    # small and avoid additional searches.
    selected_family = _provider_family(selected_provider)
    alt_family = _provider_family(alternative_provider)
    return {
        "active_landmark_label": active_landmark_label,
        "alternative_owner_family": alt_family,
        "black_king_edge_bucket": terminal.get("black_king_edge_bucket") or "missing",
        "box_area_delta": move_context.get("box_area_delta_bucket") or "missing",
        "box_area_relevance": terminal.get("box_area_relevance") or "missing",
        "family_pair": f"{selected_family}->{alt_family}",
        "king_distance_delta": move_context.get("king_distance_delta_bucket") or "missing",
        "normal_selected_owner_visible": True,
        "protected_stage": source_stage in {"stage4", "stage5", "stage6"},
        "rook_distance_delta": move_context.get("rook_distance_delta_bucket") or "missing",
        "rook_safe_after_proxy": str(move_context.get("rook_safe_after_proxy")),
        "rook_safe_proxy": str(terminal.get("rook_safe_proxy")),
        "selected_owner_family": selected_family,
        "selected_piece": move_context.get("selected_piece") or "missing",
        "selected_provider_validated_family": selected_family in {
            "stage0_basin",
            "edge_trap",
            "fence_established",
            "drive_to_edge",
        },
        "source_stage": source_stage,
        "white_king_support_bucket": terminal.get("white_king_support_bucket") or "missing",
    }


def _proxy_fires(features: dict[str, Any]) -> bool:
    stage0_vs_edge = (
        features.get("family_pair") == "stage0_basin->edge_trap"
        and features.get("selected_piece") == "king"
        and features.get("box_area_delta") == "same"
        and features.get("rook_distance_delta") == "worsens"
    )
    edge_drive_box = (
        features.get("family_pair") == "edge_trap->stage0_basin"
        and features.get("active_landmark_label") == "drive_to_edge"
        and features.get("selected_piece") == "rook"
        and features.get("box_area_delta") == "worsens"
    )
    return stage0_vs_edge or edge_drive_box


def _alternative_candidates(selected_provider: str, source_stage: str) -> list[str]:
    family = _provider_family(selected_provider)
    if family == "stage0_basin" and source_stage in {"stage4", "stage5"}:
        return list(EDGE_TRAP_ALTERNATIVES)
    if family == "edge_trap" and source_stage == "stage6":
        return ["krk.stage0_basin"]
    if family == "fence_established":
        return ["krk.edge_trap_close"]
    if family == "drive_to_edge":
        return ["krk.stage0_basin", "krk.edge_trap_close"]
    return ["krk.edge_trap_close"]


def _used_discovery_states() -> set[str]:
    payload = _load(DISCOVERY_DATASET)
    if payload.get("causal_status") != "non_causal_proxy_validation_dataset":
        raise ValueError("discovery dataset must remain non-causal")
    return {str(row.get("state_id")) for row in payload.get("rows") or [] if row.get("state_id")}


def _scan_candidate_jobs(
    repo_root: Path,
    *,
    max_jobs: int,
    max_sample_index: int,
    base_seed: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    used_states = _used_discovery_states()
    graph_cache: dict[str, tuple[Any, ReConEngine]] = {}
    selected_jobs: list[dict[str, Any]] = []
    selected_state_ids: set[str] = set()
    scan_counts: Counter[str] = Counter()
    selected_counts: Counter[str] = Counter()
    proxy_positive_count = 0
    proxy_negative_count = 0
    target_proxy_positive = max(2, max_jobs // 2)
    target_proxy_negative = max_jobs - target_proxy_positive

    stage_order = ("stage4", "stage5", "stage6")
    for stage in stage_order:
        config = STAGE_CONFIGS[stage]
        binding = _binding_for_stage(stage)
        topology_path = str(binding["topology_path"])
        if topology_path not in graph_cache:
            graph_cache[topology_path] = _load_graph_engine(repo_root, topology_path)
        graph, engine = graph_cache[topology_path]
        source_names = tuple(diag.source_stage_names_for_label(str(config["label"])))
        for sample_index in range(max_sample_index):
            if len(selected_jobs) >= max_jobs:
                break
            seed = _stable_seed("failure-risk-proxy-validation", base_seed, stage, sample_index)
            rng = random.Random(seed)
            random.seed(seed)
            board = diag.select_eval_position(
                rng,
                str(config["label"]),
                "curriculum",
                source_names,
            )
            state_id = _state_id_from_board(board)
            scan_counts[stage] += 1
            if state_id in used_states or state_id in selected_state_ids:
                continue
            job_stub = {
                "execution_binding": binding,
                "active_landmark_label": config["label"],
            }
            initial = _choose_initial(graph, engine, board, job_stub)
            selected_provider = _selected_provider(initial)
            selected_move = initial.get("move")
            if not selected_provider or not selected_move:
                continue
            alternatives = _alternative_candidates(selected_provider, stage)
            for alternative in alternatives:
                if alternative == selected_provider:
                    continue
                features = _runtime_features(
                    fen=board.fen(),
                    active_landmark_label=str(config["label"]),
                    source_stage=stage,
                    selected_provider=selected_provider,
                    selected_move=selected_move,
                    alternative_provider=alternative,
                )
                fires = _proxy_fires(features)
                if fires and proxy_positive_count >= target_proxy_positive:
                    continue
                if not fires and proxy_negative_count >= target_proxy_negative:
                    continue
                job_id = stable_record_id(
                    "job.krk.failure_risk_proxy_validation",
                    state_id,
                    selected_provider,
                    alternative,
                )
                selected_state_ids.add(state_id)
                selected_counts[f"{stage}:{'proxy_positive' if fires else 'proxy_negative'}"] += 1
                if fires:
                    proxy_positive_count += 1
                else:
                    proxy_negative_count += 1
                selected_jobs.append(
                    {
                        "schema_version": "krk_selected_owner_failure_risk_proxy_validation_job.v0",
                        "job_id": job_id,
                        "causal_status": "non_causal_label_job",
                        "labels_generated": False,
                        "source_stage": stage,
                        "active_landmark_label": config["label"],
                        "stage_role": config["stage_role"],
                        "state_id": state_id,
                        "frame_id": f"cp.krk.{state_id}",
                        "fen": board.fen(),
                        "selected_provider_at_manifest": selected_provider,
                        "selected_move_at_manifest": selected_move,
                        "forced_alternative_provider": alternative,
                        "proxy_fires_at_manifest": fires,
                        "runtime_visible_candidate_features": features,
                        "horizon": 40,
                        "diagnostic_caches_required": True,
                        "parallel_workers_allowed": True,
                        "exhaustive_legal_first_sweeps": False,
                        "stage7_training_row": False,
                        "generation": {
                            "base_seed": base_seed,
                            "sample_index": sample_index,
                            "sample_seed": seed,
                            "position_mode": "curriculum",
                            "source_stage_names": list(source_names),
                        },
                        "execution_binding": binding,
                    }
                )
                break
        if len(selected_jobs) >= max_jobs:
            break
    return selected_jobs, {
        "scanned_by_stage": dict(scan_counts),
        "selected_by_stage_and_proxy": dict(selected_counts),
        "proxy_positive_job_count": proxy_positive_count,
        "proxy_negative_job_count": proxy_negative_count,
        "discovery_state_exclusion_count": len(used_states),
    }


def build_manifest(
    repo_root: Path,
    *,
    max_jobs: int = 8,
    max_sample_index: int = 260,
    base_seed: int = 83,
) -> dict[str, Any]:
    review = _load(DISCOVERY_REVIEW)
    if review.get("causal_status") != "non_causal_architecture_review":
        raise ValueError("discovery review must remain non-causal")
    jobs, scan_summary = _scan_candidate_jobs(
        repo_root,
        max_jobs=max_jobs,
        max_sample_index=max_sample_index,
        base_seed=base_seed,
    )
    missing_paths: list[str] = []
    for job in jobs:
        binding = job["execution_binding"]
        for path_key in ("topology_path", "source_checkpoint"):
            path = repo_root / str(binding[path_key])
            if not path.exists():
                missing_paths.append(str(path))
    payload = {
        "schema_version": "krk_selected_owner_failure_risk_proxy_independent_manifest.v0",
        "causal_status": "non_causal_execution_manifest",
        **_runtime_false_block(),
        "labels_generated_in_this_slice": False,
        "implementation_allowed_by_this_manifest": False,
        "source_artifacts": [str(DISCOVERY_DATASET), str(DISCOVERY_REVIEW)],
        "selection_policy": {
            "max_jobs": max_jobs,
            "max_sample_index": max_sample_index,
            "base_seed": base_seed,
            "stage7_training_rows": 0,
            "exclude_discovery_states": True,
            "target_proxy_positive_jobs": max(2, max_jobs // 2),
            "target_proxy_negative_jobs": max_jobs - max(2, max_jobs // 2),
        },
        "scan_summary": scan_summary,
        "binding_summary": {
            "job_count": len(jobs),
            "job_count_by_stage": dict(Counter(job["source_stage"] for job in jobs)),
            "proxy_fires_at_manifest_counts": dict(
                Counter(str(job["proxy_fires_at_manifest"]) for job in jobs)
            ),
            "stage7_job_count": sum(1 for job in jobs if job.get("source_stage") == "stage7"),
            "missing_path_count": len(missing_paths),
            "missing_paths": sorted(set(missing_paths)),
            "all_bindings_valid": not missing_paths,
        },
        "jobs": jobs,
        "decision": {
            "status": (
                "independent_proxy_validation_manifest_ready"
                if jobs and not missing_paths
                else "independent_proxy_validation_manifest_blocked"
            ),
            "execute_labels_now": bool(jobs and not missing_paths),
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "recommended_next_step": "run_bounded_independent_proxy_validation_labels",
        },
    }
    _validate_non_causal(payload)
    return payload


def _run_job(repo_root: Path, job: dict[str, Any], cache: dict[str, tuple[Any, ReConEngine]]) -> dict[str, Any]:
    binding = job.get("execution_binding") or {}
    topology_path = str(binding.get("topology_path") or "")
    if topology_path not in cache:
        cache[topology_path] = _load_graph_engine(repo_root, topology_path)
    graph, engine = cache[topology_path]
    board = chess.Board(str(job.get("fen") or ""))
    base_seed = _stable_seed("run", job.get("job_id"))

    initial = _choose_initial(graph, engine, board, job)
    selected_provider = _selected_provider(initial)
    selected_move = initial.get("move")
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
    alternative = str(job.get("forced_alternative_provider") or "")
    forced_result = _run_playout(
        graph,
        engine,
        board.copy(),
        random.Random(base_seed),
        job,
        forced_successor_skill=alternative,
        trace=False,
    )
    if forced_result.get("result") != "mate":
        forced_result = _run_playout(
            graph,
            engine,
            board.copy(),
            random.Random(base_seed),
            job,
            forced_successor_skill=alternative,
            trace=True,
        )
    features = _runtime_features(
        fen=str(job.get("fen")),
        active_landmark_label=str(job.get("active_landmark_label")),
        source_stage=str(job.get("source_stage")),
        selected_provider=str(selected_provider),
        selected_move=selected_move,
        alternative_provider=alternative,
    )
    proxy_fires = _proxy_fires(features)
    selected_label = _label_from_result(selected_result)
    forced_label = _label_from_result(forced_result)
    target_failure_risk = selected_label.get("result") != "mate" and forced_label.get("result") == "mate"
    safe_preservation_target = not target_failure_risk
    return {
        "schema_version": "krk_selected_owner_failure_risk_proxy_independent_label.v0",
        "causal_status": "non_causal_proxy_validation_label",
        "job_id": job.get("job_id"),
        "state_id": job.get("state_id"),
        "frame_id": job.get("frame_id"),
        "source_stage": job.get("source_stage"),
        "active_landmark_label": job.get("active_landmark_label"),
        "fen": job.get("fen"),
        "horizon": job.get("horizon"),
        "selected_provider": selected_provider,
        "selected_move": selected_move,
        "forced_alternative_provider": alternative,
        "selected_playout_success": selected_label,
        "forced_alternative_result": forced_label,
        "selected_owner_failure_risk_target": target_failure_risk,
        "safe_preservation_confidence_target": safe_preservation_target,
        "proxy_fires": proxy_fires,
        "runtime_visible_candidate_features": features,
        "manifest_selected_provider_preserved": selected_provider == job.get("selected_provider_at_manifest"),
        "manifest_proxy_firing_preserved": proxy_fires == job.get("proxy_fires_at_manifest"),
        "stage7_training_row": False,
        "runtime_behavior_changed": False,
        "labels_generated": True,
    }


def run_labels(repo_root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("causal_status") != "non_causal_execution_manifest":
        raise ValueError("manifest must remain non-causal")
    if manifest.get("decision", {}).get("execute_labels_now") is not True:
        raise ValueError("manifest does not allow label execution")
    cache: dict[str, tuple[Any, ReConEngine]] = {}
    start = time.perf_counter()
    labels = [_run_job(repo_root, job, cache) for job in manifest.get("jobs") or []]
    wall = round(time.perf_counter() - start, 6)
    payload = {
        "schema_version": "krk_selected_owner_failure_risk_proxy_independent_labels.v0",
        "causal_status": "non_causal_label_run",
        **_runtime_false_block(),
        "implementation_allowed_by_this_label_run": False,
        "source_artifacts": [str(OUT_MANIFEST_JSON)],
        "summary": {
            "label_count": len(labels),
            "wall_time_sec": wall,
            "selected_result_counts": dict(Counter((label["selected_playout_success"] or {}).get("result") for label in labels)),
            "forced_alternative_result_counts": dict(Counter((label["forced_alternative_result"] or {}).get("result") for label in labels)),
            "target_failure_risk_count": sum(1 for label in labels if label["selected_owner_failure_risk_target"]),
            "proxy_fire_count": sum(1 for label in labels if label["proxy_fires"]),
            "manifest_selected_provider_preserved_count": sum(1 for label in labels if label["manifest_selected_provider_preserved"]),
            "manifest_proxy_firing_preserved_count": sum(1 for label in labels if label["manifest_proxy_firing_preserved"]),
            "stage7_training_rows": 0,
            "trace_failures_only": True,
        },
        "labels": labels,
        "decision": {
            "status": "independent_proxy_validation_labels_collected",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "recommended_next_step": "validate_proxy_on_independent_labels",
        },
    }
    _validate_non_causal(payload)
    return payload


def build_validation(labels_payload: dict[str, Any]) -> dict[str, Any]:
    labels = labels_payload.get("labels") or []
    rows = [
        {
            "extracted_terms": {"selected_owner_failure_risk_proxy_v0": label.get("proxy_fires")},
            "selected_owner_failure_risk_target": label.get("selected_owner_failure_risk_target"),
        }
        for label in labels
    ]
    metrics = _classification_metrics(rows, "selected_owner_failure_risk_proxy_v0")
    threshold_met = (
        (metrics.get("precision") or 0.0) >= 0.70
        and (metrics.get("recall") or 0.0) >= 0.70
        and (metrics.get("safe_preservation_recall") or 0.0) >= 0.80
        and labels_payload["summary"]["stage7_training_rows"] == 0
    )
    payload = {
        "schema_version": "krk_selected_owner_failure_risk_proxy_independent_validation.v0",
        "causal_status": "non_causal_proxy_validation",
        **_runtime_false_block(),
        "implementation_allowed_by_this_validation": False,
        "source_artifacts": [str(OUT_LABELS_JSON), str(OUT_MANIFEST_JSON)],
        "summary": {
            "label_count": len(labels),
            "stage7_row_count": 0,
            "proxy_precision": metrics.get("precision"),
            "proxy_recall": metrics.get("recall"),
            "safe_preservation_recall": metrics.get("safe_preservation_recall"),
            "threshold_met": threshold_met,
            "manifest_selected_provider_preserved_count": labels_payload["summary"].get("manifest_selected_provider_preserved_count"),
            "manifest_proxy_firing_preserved_count": labels_payload["summary"].get("manifest_proxy_firing_preserved_count"),
        },
        "metrics": metrics,
        "decision": {
            "status": (
                "independent_proxy_validation_passed"
                if threshold_met
                else "independent_proxy_validation_failed_or_underpowered"
            ),
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "recommended_next_step": (
                "prepare_runtime_proxy_review_packet"
                if threshold_met
                else "review_visible_failure_risk_proxy_or_collect_more_independent_pairs"
            ),
        },
    }
    _validate_non_causal(payload)
    return payload


def build_packet(validation: dict[str, Any]) -> dict[str, Any] | None:
    if validation["decision"]["status"] != "independent_proxy_validation_passed":
        return None
    payload = {
        "schema_version": "krk_state_local_paired_selector_runtime_proxy_review_packet.v0",
        "causal_status": "non_causal_runtime_review_packet",
        **_runtime_false_block(),
        "implementation_allowed_by_this_packet": False,
        "source_artifacts": [
            str(DISCOVERY_REVIEW),
            str(OUT_VALIDATION_JSON),
            "reports/krk_state_local_paired_runtime_proxy_review_v0.json",
        ],
        "summary": {
            "independent_validation_status": validation["decision"]["status"],
            "proxy_precision": validation["summary"]["proxy_precision"],
            "proxy_recall": validation["summary"]["proxy_recall"],
            "safe_preservation_recall": validation["summary"]["safe_preservation_recall"],
            "stage7_row_count": validation["summary"]["stage7_row_count"],
        },
        "required_default_off_sandbox_properties": [
            "default_off",
            "profile_scoped_to_handoff_composition_v1_or_successor_review_profile",
            "visible_proxy_terms_in_trace",
            "no_direct_provider_request_from_proxy_metadata",
            "no_DTM_or_tablebase_runtime_lookup",
            "no_gameplay_topology_mutation",
            "rollback_tag_before_implementation",
        ],
        "required_guardrails": [
            "default_off_equivalence",
            "protected_stage4_control",
            "protected_stage5_fence",
            "protected_stage6_drive",
            "Stage7_holdout_challenge_no_regression",
            "M1_M4_preservation_suite",
        ],
        "decision": {
            "status": "runtime_proxy_review_packet_ready",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "recommended_next_step": "explicit_approval_required_before_default_off_runtime_sandbox",
        },
    }
    _validate_non_causal(payload)
    if payload.get("implementation_allowed_by_this_packet") is not False:
        raise ValueError("packet must not authorize implementation")
    return payload


def _validate_non_causal(payload: dict[str, Any]) -> None:
    if not str(payload.get("causal_status") or "").startswith("non_causal"):
        raise ValueError("payload must remain non-causal")
    for key in RUNTIME_FALSE_KEYS:
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    for key, value in payload.items():
        if key.startswith("implementation_allowed") and value is not False:
            raise ValueError(f"{key} must be false")
    summary = payload.get("summary") or {}
    if summary.get("stage7_training_rows", 0) not in {0, None}:
        raise ValueError("Stage 7 rows must remain excluded")
    if summary.get("stage7_row_count", 0) not in {0, None}:
        raise ValueError("Stage 7 rows must remain excluded")


def _write_json(repo_root: Path, path: Path, payload: dict[str, Any]) -> None:
    (repo_root / path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _render_manifest_md(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Selected-Owner Failure-Risk Proxy Independent Manifest v0",
        "",
        "Bounded protected-only validation manifest. No labels are generated by the manifest itself.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["binding_summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Jobs", ""])
    for job in payload["jobs"]:
        lines.append(
            f"- `{job['state_id']}` stage=`{job['source_stage']}` selected=`{job['selected_provider_at_manifest']}` "
            f"alt=`{job['forced_alternative_provider']}` proxy=`{job['proxy_fires_at_manifest']}`"
        )
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def _render_labels_md(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Selected-Owner Failure-Risk Proxy Independent Labels v0",
        "",
        "Bounded non-causal h40 labels for independent proxy validation.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Labels", ""])
    for label in payload["labels"]:
        lines.append(
            f"- `{label['state_id']}` selected=`{label.get('selected_provider')}` "
            f"selected_result=`{(label.get('selected_playout_success') or {}).get('result')}` "
            f"alt=`{label.get('forced_alternative_provider')}` alt_result=`{(label.get('forced_alternative_result') or {}).get('result')}` "
            f"proxy=`{label.get('proxy_fires')}` target=`{label.get('selected_owner_failure_risk_target')}`"
        )
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def _render_validation_md(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Selected-Owner Failure-Risk Proxy Independent Validation v0",
        "",
        "Validation of the visible proxy on independent protected pairs.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Metrics", ""])
    for key, value in payload["metrics"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def _render_packet_md(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK State-Local Paired Selector Runtime Proxy Review Packet v0",
        "",
        "This packet packages independent non-causal proxy evidence. It does not authorize implementation.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Required Default-Off Sandbox Properties", ""])
    for item in payload["required_default_off_sandbox_properties"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Required Guardrails", ""])
    for item in payload["required_guardrails"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def write_outputs(
    repo_root: Path,
    manifest: dict[str, Any],
    labels: dict[str, Any],
    validation: dict[str, Any],
    packet: dict[str, Any] | None,
) -> None:
    _write_json(repo_root, OUT_MANIFEST_JSON, manifest)
    (repo_root / OUT_MANIFEST_MD).write_text(_render_manifest_md(manifest), encoding="utf-8")
    _write_json(repo_root, OUT_LABELS_JSON, labels)
    (repo_root / OUT_LABELS_MD).write_text(_render_labels_md(labels), encoding="utf-8")
    _write_json(repo_root, OUT_VALIDATION_JSON, validation)
    (repo_root / OUT_VALIDATION_MD).write_text(_render_validation_md(validation), encoding="utf-8")
    if packet is not None:
        _write_json(repo_root, OUT_PACKET_JSON, packet)
        (repo_root / OUT_PACKET_MD).write_text(_render_packet_md(packet), encoding="utf-8")


def build_and_run(
    repo_root: Path,
    *,
    max_jobs: int = 8,
    max_sample_index: int = 260,
    base_seed: int = 83,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    manifest = build_manifest(
        repo_root,
        max_jobs=max_jobs,
        max_sample_index=max_sample_index,
        base_seed=base_seed,
    )
    labels = run_labels(repo_root, manifest)
    validation = build_validation(labels)
    packet = build_packet(validation)
    return manifest, labels, validation, packet


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--max-jobs", type=int, default=8)
    parser.add_argument("--max-sample-index", type=int, default=260)
    parser.add_argument("--base-seed", type=int, default=83)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    manifest, labels, validation, packet = build_and_run(
        repo_root,
        max_jobs=args.max_jobs,
        max_sample_index=args.max_sample_index,
        base_seed=args.base_seed,
    )
    write_outputs(repo_root, manifest, labels, validation, packet)
    print(json.dumps(validation["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
