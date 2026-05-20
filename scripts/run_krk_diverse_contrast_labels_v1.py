#!/usr/bin/env python3
"""Run bounded diverse KRK contrast labels from the reviewed v1 manifest."""

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


MANIFEST = Path("reports/krk_diverse_contrast_execution_manifest_v1.json")
OUT_JSON = Path("reports/krk_diverse_contrast_labels_v1.json")
OUT_MD = Path("reports/krk_diverse_contrast_labels_v1.md")

EXECUTION_LANDMARK_LABELS = {
    # `wrong_tempo_control` is a diagnostic stratum name, not a reward family.
    # Keep it in report metadata, but execute with the underlying KRK label.
    "wrong_tempo_control": "edge_trap_wrong_tempo",
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _compact_stagnation_summary(summary: Any) -> dict[str, Any] | None:
    if not isinstance(summary, dict):
        return None
    keys = (
        "abstract_state_signature",
        "repeated_state_count",
        "repeated_abstract_state_count",
        "max_state_repetition",
        "rook_oscillation_loop",
        "rook_oscillation_detected",
        "rook_reversal_count",
        "no_progress_plies",
        "no_box_progress_recently",
        "no_edge_progress_recently",
        "no_mate_progress_recently",
        "post_stagnation_break_continuation_needed",
        "safe_loop_breaking_move_available",
        "safe_followup_available",
    )
    return {key: summary.get(key) for key in keys if key in summary}


def _compact_label(label: dict[str, Any]) -> dict[str, Any]:
    compact = dict(label)
    trace = compact.pop("trace", None)
    if isinstance(trace, list):
        compact["trace_ply_count"] = len(trace)
        compact["trace_first_fen"] = trace[0].get("fen") if trace and isinstance(trace[0], dict) else None
        compact["trace_last_fen"] = trace[-1].get("fen") if trace and isinstance(trace[-1], dict) else None
        compact["full_trace_elided"] = True
    compact_summary = _compact_stagnation_summary(compact.pop("stagnation_summary", None))
    if compact_summary is not None:
        compact["stagnation_summary_compact"] = compact_summary
    return compact


def compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    compact = dict(payload)
    compact["labels"] = [_compact_label(label) for label in payload.get("labels") or []]
    compact.setdefault("summary", {})["full_failure_traces_elided"] = True
    return compact


def run_labels() -> dict[str, Any]:
    manifest = _load_json(MANIFEST)
    if manifest.get("causal_status") != "non_causal_execution_manifest":
        raise ValueError("execution manifest must remain non-causal")
    if not (manifest.get("binding_summary") or {}).get("all_bindings_valid"):
        raise ValueError("all bindings must be valid before running labels")

    cache: dict[str, tuple[Any, Any]] = {}
    start = time.monotonic()
    labels = []
    jobs = list(manifest.get("jobs") or [])
    for index, job in enumerate(jobs, start=1):
        print(
            f"[{index}/{len(jobs)}] {job.get('source_stage')} {job.get('state_id')} {job.get('provider_id')}",
            file=sys.stderr,
            flush=True,
        )
        execution_job = dict(job)
        execution_job["active_landmark_label"] = EXECUTION_LANDMARK_LABELS.get(
            str(job.get("active_landmark_label") or ""),
            job.get("active_landmark_label"),
        )
        label = _compact_label(forced_labels._run_job(ROOT, execution_job, cache))
        label["source_active_landmark_label"] = job.get("active_landmark_label")
        label["execution_landmark_label"] = execution_job.get("active_landmark_label")
        label["stratum_id"] = job.get("stratum_id")
        label["provider_family"] = job.get("provider_family")
        label["provider_maturity"] = job.get("provider_maturity")
        label["provider_local_rank"] = job.get("provider_local_rank")
        label["normalized_score"] = job.get("normalized_score")
        label["global_raw_score_rank"] = job.get("global_raw_score_rank")
        label["frame_outcome"] = job.get("frame_outcome")
        label["stage7_challenge_row"] = bool(job.get("stage7_challenge_row"))
        label["usable_for_training"] = bool(job.get("usable_for_training"))
        label["label_channel"] = "forced_provider_state_local_contrast"
        labels.append(label)
    wall_time = time.monotonic() - start

    summary = {
        "label_count": len(labels),
        "training_label_count": sum(1 for label in labels if label.get("usable_for_training")),
        "stage7_eval_only_label_count": sum(1 for label in labels if label.get("stage7_challenge_row")),
        "result_counts": dict(Counter(str(label.get("result") or "unknown") for label in labels)),
        "result_counts_by_stage": dict(
            Counter(f"{label.get('source_stage')}:{label.get('result')}" for label in labels)
        ),
        "result_counts_by_provider_family": dict(
            Counter(f"{label.get('provider_family')}:{label.get('result')}" for label in labels)
        ),
        "forced_successor_available_counts": dict(
            Counter(str(label.get("forced_successor_available")) for label in labels)
        ),
        "wall_time_seconds": round(wall_time, 3),
        "trace_failures_only": True,
    }
    payload = {
        "schema_version": "krk_diverse_contrast_labels.v1",
        "causal_status": "non_causal_label_run",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifact": str(MANIFEST),
        "summary": summary,
        "labels": labels,
        "decision": {
            "status": "diverse_contrast_labels_completed",
            "recommended_next_step": "merge_diverse_contrast_labels_and_probe_selector",
            "runtime_test_allowed_next": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "blocked_next_steps": [
            "runtime_selector",
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
        if label.get("stage7_challenge_row") and label.get("usable_for_training"):
            raise ValueError("Stage7 labels must remain eval-only")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Diverse Contrast Labels v1",
        "",
        "This bounded label run forces each configured provider for the first White move, then releases to the normal topology. It is non-causal evidence only.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Labels", ""])
    for label in payload["labels"]:
        lines.append(
            f"- `{label['job_id']}` stage=`{label['source_stage']}` stratum=`{label.get('stratum_id')}` "
            f"provider=`{label['provider_id']}` forced_move=`{label.get('forced_first_move')}` "
            f"result=`{label['result']}` plies=`{label['plies']}` stage7_eval=`{label.get('stage7_challenge_row')}`"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Status: `{payload['decision']['status']}`",
            f"- Recommended next step: `{payload['decision']['recommended_next_step']}`",
            f"- Runtime test allowed next: `{payload['decision']['runtime_test_allowed_next']}`",
            f"- Stage 7 promotion allowed: `{payload['decision']['stage7_promotion_allowed']}`",
            f"- Stage 8 training allowed: `{payload['decision']['stage8_training_allowed']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    payload = run_labels()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
