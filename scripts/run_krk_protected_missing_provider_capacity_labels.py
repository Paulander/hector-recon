#!/usr/bin/env python3
"""Run bounded protected missing-provider capacity labels."""

from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_krk_forced_provider_control_labels as forced_labels  # noqa: E402


MANIFEST = Path("reports/krk_protected_missing_provider_capacity_execution_manifest_v0.json")
REVIEW = Path("reports/krk_protected_missing_provider_capacity_execution_manifest_review_v0.json")
OUT_JSON = Path("reports/krk_protected_missing_provider_capacity_labels_v0.json")
OUT_MD = Path("reports/krk_protected_missing_provider_capacity_labels_v0.md")
EXECUTION_LANDMARK_LABELS = {
    # This is a control stratum name in the reports, but the reward harness
    # needs the underlying KRK landmark label during offline playout.
    "wrong_tempo_control": "edge_trap_wrong_tempo",
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _compact_label(label: dict[str, Any]) -> dict[str, Any]:
    compact = dict(label)
    trace = compact.pop("trace", None)
    if isinstance(trace, list):
        compact["trace_ply_count"] = len(trace)
        compact["trace_first_fen"] = trace[0].get("fen") if trace and isinstance(trace[0], dict) else None
        compact["trace_last_fen"] = trace[-1].get("fen") if trace and isinstance(trace[-1], dict) else None
        compact["full_trace_elided"] = True
    stagnation = compact.pop("stagnation_summary", None)
    if isinstance(stagnation, dict):
        compact["stagnation_summary_compact"] = {
            key: stagnation.get(key)
            for key in (
                "abstract_state_signature",
                "repeated_state_count",
                "repeated_abstract_state_count",
                "max_state_repetition",
                "no_progress_plies",
                "rook_oscillation_detected",
                "post_stagnation_break_continuation_needed",
            )
            if key in stagnation
        }
    return compact


def run_labels() -> dict[str, Any]:
    manifest = _load(MANIFEST)
    review = _load(REVIEW)
    if manifest.get("causal_status") != "non_causal_execution_manifest":
        raise ValueError("manifest must remain non-causal")
    if not (manifest.get("binding_summary") or {}).get("all_bindings_valid"):
        raise ValueError("manifest bindings must be valid before label execution")
    if review.get("causal_status") != "non_causal_manifest_review":
        raise ValueError("review must remain non-causal")
    if not (review.get("decision") or {}).get("labels_allowed"):
        raise ValueError("manifest review must allow labels")
    cache: dict[str, tuple[Any, Any]] = {}
    labels = []
    start = time.monotonic()
    jobs = list(manifest.get("jobs") or [])
    for index, job in enumerate(jobs, start=1):
        print(f"[{index}/{len(jobs)}] {job.get('source_stage')} {job.get('provider_id')}", file=sys.stderr, flush=True)
        execution_job = dict(job)
        execution_job["active_landmark_label"] = EXECUTION_LANDMARK_LABELS.get(
            str(job.get("active_landmark_label") or ""),
            job.get("active_landmark_label"),
        )
        label = _compact_label(forced_labels._run_job(ROOT, execution_job, cache))
        label["label_channel"] = "protected_missing_provider_capacity"
        label["source_active_landmark_label"] = job.get("active_landmark_label")
        label["execution_landmark_label"] = execution_job.get("active_landmark_label")
        label["provider_version"] = (job.get("execution_binding") or {}).get("provider_version")
        label["stage7_training_row"] = bool(job.get("stage7_training_row"))
        labels.append(label)
    wall = time.monotonic() - start
    result_counts = Counter(str(label.get("result") or "unknown") for label in labels)
    by_stage = Counter(f"{label.get('source_stage')}:{label.get('result')}" for label in labels)
    by_provider = Counter(f"{label.get('provider_id')}:{label.get('result')}" for label in labels)
    payload = {
        "schema_version": "krk_protected_missing_provider_capacity_labels.v0",
        "causal_status": "non_causal_label_run",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(MANIFEST), str(REVIEW)],
        "labels": labels,
        "summary": {
            "label_count": len(labels),
            "result_counts": dict(sorted(result_counts.items())),
            "result_counts_by_stage": dict(sorted(by_stage.items())),
            "result_counts_by_provider": dict(sorted(by_provider.items())),
            "stage7_labels": sum(1 for label in labels if label.get("source_stage") == "stage7"),
            "stage7_training_labels": sum(1 for label in labels if label.get("stage7_training_row")),
            "trace_failures_only": True,
            "full_failure_traces_elided": True,
            "wall_time_seconds": round(wall, 3),
        },
        "decision": {
            "status": "protected_missing_provider_capacity_labels_completed",
            "recommended_next_step": "merge_missing_provider_labels_and_refresh_strategy_sequence_inventory",
            "runtime_work_allowed": False,
        },
        "blocked_next_steps": [
            "runtime_selector",
            "runtime_internal_terminal",
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
        raise ValueError("labels must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if payload["summary"]["stage7_labels"] != 0:
        raise ValueError("Stage 7 labels must remain excluded")
    if payload["summary"]["stage7_training_labels"] != 0:
        raise ValueError("Stage 7 training labels must remain excluded")
    for label in payload.get("labels") or []:
        if label.get("causal_status") != "non_causal_outcome_label":
            raise ValueError("labels must remain non-causal")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Protected Missing-Provider Capacity Labels v0",
        "",
        "Bounded non-causal label run over protected max-only frames.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Labels", ""])
    for label in payload["labels"]:
        lines.append(
            f"- `{label['job_id']}` stage=`{label['source_stage']}` provider=`{label['provider_id']}` "
            f"result=`{label['result']}` plies=`{label['plies']}` forced_move=`{label.get('forced_first_move')}`"
        )
    lines.extend(["", f"Recommended next step: `{payload['decision']['recommended_next_step']}`", ""])
    return "\n".join(lines)


def main() -> None:
    payload = run_labels()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
