#!/usr/bin/env python3
"""Run bounded candidate-generation capacity evidence labels v2."""

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


MANIFEST = Path(
    "reports/strategy_arbitration/"
    "krk_candidate_generation_capacity_evidence_manifest_v2.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/"
    "krk_candidate_generation_capacity_evidence_labels_v2.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/"
    "krk_candidate_generation_capacity_evidence_labels_v2.md"
)


EXECUTION_LANDMARK_LABELS = {
    "wrong_tempo_control": "edge_trap_wrong_tempo",
}


EXECUTION_BINDING = {
    "black_policy": "adversarial",
    "composition_profile": "handoff_composition_v1",
    "early_stop_stable_suggestions": 3,
    "enable_diagnostic_caches": True,
    "execution_mode": "force_provider_first_white_move_then_release",
    "max_ticks": 200,
    "plasticity_scope": "protected_frozen",
    "profile_settings": {
        "post_break_continuation_bonus": 0.25,
        "post_break_continuation_enabled": True,
        "stagnation_breaker_bonus": 0.5,
        "stagnation_breaker_enabled": True,
        "successor_affordance_layer_enabled": True,
        "successor_role_license_enabled": True,
        "successor_role_scoped_move_shape_bonus": 0.05,
        "successor_role_scoped_move_shape_enabled": True,
        "successor_stage0_drift_penalty": 6.0,
    },
    "provider_version": "protected_provider_pack_v1",
    "suggestion_limit": 10,
    "topology_path": (
        "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/"
        "topology/krk_entry_topology.json"
    ),
    "topology_version": "stage6_overlay_composed_v1",
    "trace_mode": "failures_only",
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


def _execution_job(job: dict[str, Any]) -> dict[str, Any]:
    active = str(job.get("active_landmark_label") or "")
    return {
        **job,
        "frame_id": job.get("state_id"),
        "move_uci": job.get("observed_move_uci"),
        "active_landmark_label": EXECUTION_LANDMARK_LABELS.get(active, active),
        "execution_binding": dict(EXECUTION_BINDING),
    }


def run_labels() -> dict[str, Any]:
    manifest = _load(MANIFEST)
    if manifest.get("causal_status") != "offline_label_manifest_only":
        raise ValueError("manifest must remain offline-only")
    if (manifest.get("summary") or {}).get("stage7_job_count") != 0:
        raise ValueError("Stage 7 jobs are not allowed")
    cache: dict[str, tuple[Any, Any]] = {}
    labels = []
    start = time.monotonic()
    jobs = list(manifest.get("jobs") or [])
    for index, job in enumerate(jobs, start=1):
        print(
            f"[{index}/{len(jobs)}] {job.get('source_stage')} {job.get('provider_id')}",
            file=sys.stderr,
            flush=True,
        )
        label = _compact_label(forced_labels._run_job(ROOT, _execution_job(job), cache))
        label["label_channel"] = "candidate_generation_capacity_evidence_v2"
        label["label_semantics"] = "forced_provider_capacity_not_runtime_ownership"
        label["source_active_landmark_label"] = job.get("active_landmark_label")
        label["observed_move_uci"] = job.get("observed_move_uci")
        label["provider_family"] = job.get("provider_family")
        label["stage7_training_row"] = False
        labels.append(label)
    result_counts = Counter(str(label.get("result") or "unknown") for label in labels)
    by_stage = Counter(f"{label.get('source_stage')}:{label.get('result')}" for label in labels)
    by_family = Counter(f"{label.get('provider_family')}:{label.get('result')}" for label in labels)
    payload = {
        "schema_version": "krk_candidate_generation_capacity_evidence_labels.v2",
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
        "source_artifacts": [str(MANIFEST)],
        "summary": {
            "label_count": len(labels),
            "result_counts": dict(sorted(result_counts.items())),
            "result_counts_by_stage": dict(sorted(by_stage.items())),
            "result_counts_by_provider_family": dict(sorted(by_family.items())),
            "stage7_label_count": sum(1 for label in labels if label.get("source_stage") == "stage7"),
            "stage7_training_label_count": sum(1 for label in labels if label.get("stage7_training_row")),
            "trace_failures_only": True,
            "full_failure_traces_elided": True,
            "wall_time_seconds": round(time.monotonic() - start, 3),
        },
        "labels": labels,
        "decision": {
            "status": "candidate_generation_capacity_evidence_labels_completed",
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": "merge_capacity_evidence_labels_v2_and_rerun_refresh_probe",
        },
    }
    validate_payload(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("causal_status") != "non_causal_label_run":
        raise ValueError("label run must remain non-causal")
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
    if payload["summary"]["stage7_label_count"] != 0:
        raise ValueError("Stage 7 labels are not allowed")
    if payload["summary"]["stage7_training_label_count"] != 0:
        raise ValueError("Stage 7 training labels are not allowed")
    for label in payload.get("labels") or []:
        if label.get("causal_status") != "non_causal_outcome_label":
            raise ValueError("labels must remain non-causal")
        if label.get("label_semantics") != "forced_provider_capacity_not_runtime_ownership":
            raise ValueError("labels must not become ownership labels")


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Candidate-Generation Capacity Evidence Labels v2",
        "",
        "Bounded protected-only offline forced-provider capacity labels. These labels are not runtime inputs and not ownership labels.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Labels", ""])
    for label in payload["labels"]:
        lines.append(
            f"- `{label['job_id']}` stage=`{label['source_stage']}` "
            f"provider=`{label['provider_id']}` family=`{label.get('provider_family')}` "
            f"result=`{label['result']}` plies=`{label['plies']}` "
            f"forced_move=`{label.get('forced_first_move')}`"
        )
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = run_labels()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
