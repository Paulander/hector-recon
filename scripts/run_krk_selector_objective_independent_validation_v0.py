#!/usr/bin/env python3
"""Run bounded independent validation for selector-objective visible heuristic.

This is a protected Stage 4/5/6 offline label/validation slice. It does not
train or implement a selector. The validation target is selected-owner failure
risk only: selected h40 mate means preserve, selected h40 max_plies means switch
risk. It does not convert forced capacity evidence into ownership labels.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import benchmark_krk_selector_objective_v2 as benchmark  # noqa: E402
import build_krk_ownership_selection_context_dataset_v0 as context_features  # noqa: E402
import generate_krk_selected_provider_diversity_sampling_manifest as manifest_builder  # noqa: E402
import run_krk_strategy_arbiter_out_of_sample_control_labels as label_runner  # noqa: E402


BENCHMARK_REVIEW = Path(
    "reports/strategy_arbitration/krk_selector_objective_benchmark_review_packet_v2.json"
)
SEED = Path("reports/strategy_arbitration/krk_selector_objective_seed_manifest_v2.json")
OUT_MANIFEST_JSON = Path(
    "reports/strategy_arbitration/krk_selector_objective_independent_validation_manifest_v0.json"
)
OUT_MANIFEST_MD = Path(
    "reports/strategy_arbitration/krk_selector_objective_independent_validation_manifest_v0.md"
)
OUT_LABELS_JSON = Path(
    "reports/strategy_arbitration/krk_selector_objective_independent_validation_labels_v0.json"
)
OUT_LABELS_MD = Path(
    "reports/strategy_arbitration/krk_selector_objective_independent_validation_labels_v0.md"
)
OUT_JSON = Path("reports/strategy_arbitration/krk_selector_objective_independent_validation_v0.json")
OUT_MD = Path("reports/strategy_arbitration/krk_selector_objective_independent_validation_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected object: {path}")
    return payload


def _seed_state_ids() -> set[str]:
    seed = _load(SEED)
    return {
        str(row.get("state_id"))
        for row in seed.get("seed_rows") or []
        if isinstance(row, dict) and row.get("state_id")
    }


def build_manifest(max_jobs: int = 12, base_seed: int = 131) -> dict[str, Any]:
    review = _load(BENCHMARK_REVIEW)
    if review.get("decision", {}).get("independent_validation_review_ready") is not True:
        raise ValueError("benchmark review must be ready for independent validation")
    if max_jobs > 12:
        raise ValueError("independent validation v0 is capped at 12 jobs")

    seed_ids = _seed_state_ids()
    source = manifest_builder.build_manifest(
        max_jobs=60,
        per_stage_max=20,
        base_seed=base_seed,
        max_sample_index=800,
    )
    stage_caps = {"stage4": 8, "stage5": 0, "stage6": 4}
    jobs: list[dict[str, Any]] = []
    stage_counts: Counter[str] = Counter()
    for job in source.get("jobs") or []:
        if job.get("source_stage") in {"stage7", "stage8"}:
            continue
        if str(job.get("state_id")) in seed_ids:
            continue
        stage = str(job.get("source_stage"))
        if stage_counts[stage] >= stage_caps.get(stage, 0):
            continue
        job = {
            **job,
            "schema_version": "krk_selector_objective_independent_validation_job.v0",
            "causal_status": "non_causal_independent_validation_job",
            "horizon": 40,
            "validation_role": "normal_selected_owner_outcome",
            "stage7_training_row": False,
        }
        jobs.append(job)
        stage_counts[stage] += 1
        if len(jobs) >= max_jobs:
            break

    missing_paths = []
    for job in jobs:
        binding = job.get("execution_binding") or {}
        for key in ("topology_path", "source_checkpoint"):
            path = binding.get(key)
            if path and not (ROOT / path).exists():
                missing_paths.append(str(path))

    manifest = {
        "schema_version": "krk_selector_objective_independent_validation_manifest.v0",
        "causal_status": "non_causal_validation_manifest",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(BENCHMARK_REVIEW), str(SEED)],
        "selection_policy": {
            "max_jobs": max_jobs,
            "base_seed": base_seed,
            "stage_caps": stage_caps,
            "excluded_seed_state_count": len(seed_ids),
            "protected_stages": ["stage4", "stage5", "stage6"],
            "excluded_stages": ["stage7", "stage8"],
            "stage7_training_rows": 0,
        },
        "binding_summary": {
            "job_count": len(jobs),
            "job_count_by_stage": dict(sorted(stage_counts.items())),
            "missing_path_count": len(set(missing_paths)),
            "missing_paths": sorted(set(missing_paths)),
            "all_bindings_valid": not missing_paths,
        },
        "jobs": jobs,
        "decision": {
            "status": (
                "selector_objective_independent_validation_manifest_ready"
                if jobs and not missing_paths
                else "selector_objective_independent_validation_manifest_invalid"
            ),
            "labels_allowed_by_review": True,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
        },
    }
    validate_common(manifest)
    if manifest["binding_summary"]["job_count"] > max_jobs:
        raise ValueError("job cap exceeded")
    return manifest


def validate_common(payload: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_score_changes",
        "runtime_direct_routing",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")


def _normalize_label(label: dict[str, Any]) -> dict[str, Any]:
    return {
        **label,
        "schema_version": "krk_selector_objective_independent_validation_label.v0",
        "causal_status": "non_causal_selected_owner_outcome_label",
        "label_semantics": "normal_selected_owner_outcome_not_capacity_label",
        "source_manifest": str(OUT_MANIFEST_JSON),
    }


def run_labels(manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("decision", {}).get("status") != "selector_objective_independent_validation_manifest_ready":
        raise ValueError("manifest must be ready before labels")
    cache: dict[str, tuple[Any, Any]] = {}
    start = time.perf_counter()
    labels = [
        _normalize_label(label_runner._run_job(ROOT, job, cache))
        for job in manifest.get("jobs") or []
    ]
    wall_time = round(time.perf_counter() - start, 6)
    result_counts = Counter((label.get("selected_playout_success") or {}).get("result") for label in labels)
    by_stage = Counter(
        f"{label.get('source_stage')}:{(label.get('selected_playout_success') or {}).get('result')}"
        for label in labels
    )
    payload = {
        "schema_version": "krk_selector_objective_independent_validation_labels.v0",
        "causal_status": "non_causal_label_run",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(OUT_MANIFEST_JSON)],
        "summary": {
            "label_count": len(labels),
            "wall_time_sec": wall_time,
            "selected_result_counts": dict(result_counts),
            "selected_result_counts_by_stage": dict(by_stage),
            "selector_training_row_count": 0,
            "stage7_training_row_count": 0,
        },
        "labels": labels,
        "decision": {
            "status": "selector_objective_independent_validation_labels_collected",
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
        },
    }
    validate_common(payload)
    if any(label.get("source_stage") == "stage7" for label in labels):
        raise ValueError("Stage 7 labels are excluded")
    return payload


def _context_row(label: dict[str, Any]) -> dict[str, Any]:
    fen = str(label.get("fen") or "")
    selected_move = label.get("selected_move")
    terminal = context_features._terminal_context_from_fen(fen)
    move_context = context_features._post_move_context(fen, selected_move)
    row = {
        "state_id": label.get("state_id"),
        "source_stage": label.get("source_stage"),
        "selected_provider": label.get("selected_provider"),
        "active_landmark_label": label.get("active_landmark_label"),
        "positive_trace_provider_candidate_count": max(
            1,
            int(label.get("initial_provider_count") or 0),
        ),
        "terminal_space_context": terminal,
        "selected_move_context": move_context,
    }
    row["context_terms"] = context_features._context_terms(row)
    return benchmark._augment_row(row, {str(row.get("state_id")): row})


def _target_action(label: dict[str, Any]) -> str | None:
    result = (label.get("selected_playout_success") or {}).get("result")
    if result == "mate":
        return "preserve"
    if result == "max_plies":
        return "switch"
    return None


def _metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def count(pred: str, target: str) -> int:
        return sum(1 for row in rows if row["predicted_action"] == pred and row["target_action"] == target)

    switch_tp = count("switch", "switch")
    switch_fp = sum(1 for row in rows if row["predicted_action"] == "switch" and row["target_action"] != "switch")
    switch_fn = sum(1 for row in rows if row["predicted_action"] != "switch" and row["target_action"] == "switch")
    preserve_tp = count("preserve", "preserve")
    preserve_fn = sum(1 for row in rows if row["predicted_action"] != "preserve" and row["target_action"] == "preserve")
    correct = sum(1 for row in rows if row["predicted_action"] == row["target_action"])
    total = len(rows)
    return {
        "row_count": total,
        "correct_count": correct,
        "accuracy": correct / total if total else 0.0,
        "switch_precision": switch_tp / (switch_tp + switch_fp) if switch_tp + switch_fp else None,
        "switch_recall": switch_tp / (switch_tp + switch_fn) if switch_tp + switch_fn else 0.0,
        "preserve_recall": preserve_tp / (preserve_tp + preserve_fn) if preserve_tp + preserve_fn else 0.0,
        "target_counts": dict(Counter(row["target_action"] for row in rows)),
        "prediction_counts": dict(Counter(row["predicted_action"] for row in rows)),
    }


def build_validation(labels: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for label in labels.get("labels") or []:
        target = _target_action(label)
        if target is None:
            continue
        context_row = _context_row(label)
        predicted = benchmark._visible_failure_risk_heuristic(context_row)
        if predicted == "abstain":
            predicted = "preserve"
        rows.append(
            {
                "schema_version": "krk_selector_objective_independent_validation_row.v0",
                "state_id": label.get("state_id"),
                "source_stage": label.get("source_stage"),
                "active_landmark_label": label.get("active_landmark_label"),
                "selected_provider": label.get("selected_provider"),
                "selected_move": label.get("selected_move"),
                "target_action": target,
                "predicted_action": predicted,
                "selected_playout_result": (label.get("selected_playout_success") or {}).get("result"),
                "visible_context_terms": context_row.get("context_terms"),
                "label_semantics": "selected_owner_outcome_validation_not_capacity_label",
            }
        )
    metrics = _metrics(rows)
    switch_count = metrics["target_counts"].get("switch", 0)
    preserve_count = metrics["target_counts"].get("preserve", 0)
    pass_thresholds = (
        switch_count >= 2
        and preserve_count >= 4
        and (metrics["switch_precision"] or 0.0) >= 0.70
        and metrics["switch_recall"] >= 0.70
        and metrics["preserve_recall"] >= 0.80
    )
    underpowered = switch_count < 2 or preserve_count < 4
    payload = {
        "schema_version": "krk_selector_objective_independent_validation.v0",
        "causal_status": "non_causal_independent_validation",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(OUT_LABELS_JSON), str(BENCHMARK_REVIEW)],
        "summary": {
            **metrics,
            "underpowered": underpowered,
            "selector_training_row_count": 0,
            "stage7_training_row_count": 0,
            "runtime_review_ready": False,
        },
        "rows": rows,
        "decision": {
            "status": (
                "selector_objective_independent_validation_passed_for_failure_risk_only"
                if pass_thresholds
                else (
                    "selector_objective_independent_validation_underpowered"
                    if underpowered
                    else "selector_objective_independent_validation_failed"
                )
            ),
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": (
                "write_runtime_review_packet_only_after_separate_candidate_evidence_validation"
                if pass_thresholds
                else "collect_more_independent_switch_rows_or_keep_selector_blocked"
            ),
        },
    }
    validate_common(payload)
    return payload


def _write_md(path: Path, title: str, payload: dict[str, Any], rows_key: str) -> None:
    lines = [f"# {title}", ""]
    for key, value in (payload.get("summary") or payload.get("binding_summary") or {}).items():
        lines.append(f"- {key}: `{value}`")
    if "decision" in payload:
        lines.extend(["", "## Decision", ""])
        for key, value in payload["decision"].items():
            lines.append(f"- {key}: `{value}`")
    rows = payload.get(rows_key) or []
    if rows:
        lines.extend(["", "## Rows", ""])
        for row in rows:
            lines.append(
                f"- `{row.get('state_id')}` stage=`{row.get('source_stage')}` "
                f"target=`{row.get('target_action') or row.get('validation_role')}` "
                f"predicted=`{row.get('predicted_action', '')}`"
            )
    (ROOT / path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    manifest = build_manifest()
    (ROOT / OUT_MANIFEST_JSON).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_md(OUT_MANIFEST_MD, "KRK Selector Objective Independent Validation Manifest v0", manifest, "jobs")
    labels = run_labels(manifest)
    (ROOT / OUT_LABELS_JSON).write_text(
        json.dumps(labels, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_md(OUT_LABELS_MD, "KRK Selector Objective Independent Validation Labels v0", labels, "labels")
    validation = build_validation(labels)
    (ROOT / OUT_JSON).write_text(
        json.dumps(validation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_md(OUT_MD, "KRK Selector Objective Independent Validation v0", validation, "rows")
    print(json.dumps(validation["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
