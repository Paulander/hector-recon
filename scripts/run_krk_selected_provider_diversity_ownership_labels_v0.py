#!/usr/bin/env python3
"""Run bounded ownership labels for selected-provider diversity jobs.

This converts the existing selected-provider diversity observation set into
normal-routing h40 outcome labels. The labels are offline evidence only: no
selector, arbiter, routing change, Stage 7 promotion, Stage 8 training, runtime
DTM/tablebase lookup, or topology mutation is performed.
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

import run_krk_strategy_arbiter_out_of_sample_control_labels as label_runner  # noqa: E402


MANIFEST = Path("reports/krk_selected_provider_diversity_sampling_manifest_v0.json")
REVIEW = Path("reports/krk_selected_provider_diversity_sampling_manifest_review_v0.json")
OBSERVATION_SCAN = Path("reports/krk_selected_provider_diversity_observation_scan_v0.json")
OUT_JSON = Path("reports/krk_selected_provider_diversity_ownership_labels_v0.json")
OUT_MD = Path("reports/krk_selected_provider_diversity_ownership_labels_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _validate_inputs(manifest: dict[str, Any], review: dict[str, Any], scan: dict[str, Any]) -> None:
    if manifest.get("causal_status") != "non_causal_sampling_manifest":
        raise ValueError("sampling manifest must remain non-causal")
    if review.get("causal_status") != "non_causal_manifest_review":
        raise ValueError("manifest review must remain non-causal")
    if scan.get("causal_status") != "non_causal_observation_scan":
        raise ValueError("observation scan must remain non-causal")
    if not (review.get("decision") or {}).get("observations_allowed"):
        raise ValueError("manifest review must have allowed the bounded observation scan")
    if (manifest.get("binding_summary") or {}).get("all_bindings_valid") is not True:
        raise ValueError("manifest bindings must be valid")
    if (scan.get("summary") or {}).get("stage7_observations") != 0:
        raise ValueError("Stage 7 observations must remain excluded")
    if len(manifest.get("jobs") or []) > 45:
        raise ValueError("label run is bounded to at most 45 selected-provider diversity jobs")
    if any((job.get("source_stage") == "stage7") for job in manifest.get("jobs") or []):
        raise ValueError("Stage 7 jobs must remain excluded")


def _normalize_label(label: dict[str, Any]) -> dict[str, Any]:
    return {
        **label,
        "schema_version": "krk_selected_provider_diversity_ownership_label.v0",
        "causal_status": "non_causal_ownership_outcome_label",
        "label_source": "selected_provider_diversity_normal_routing_h40",
        "source_manifest": str(MANIFEST),
    }


def build_labels() -> dict[str, Any]:
    manifest = _load(MANIFEST)
    review = _load(REVIEW)
    scan = _load(OBSERVATION_SCAN)
    _validate_inputs(manifest, review, scan)

    cache: dict[str, tuple[Any, Any]] = {}
    start = time.perf_counter()
    labels = [
        _normalize_label(label_runner._run_job(ROOT, {**job, "horizon": job.get("horizon") or 40}, cache))
        for job in manifest.get("jobs") or []
    ]
    wall_time = round(time.perf_counter() - start, 6)

    selected_counts = Counter(label["selected_playout_success"].get("result") for label in labels)
    forced_counts = Counter(
        (label.get("forced_provider_conversion_for_selected_provider") or {}).get("result")
        for label in labels
    )
    owner_counts = Counter(
        "selected_owner_converted"
        if label["selected_playout_success"].get("result") == "mate"
        else "selected_owner_failed"
        for label in labels
    )
    by_stage = Counter(
        f"{label.get('source_stage')}:{label['selected_playout_success'].get('result')}"
        for label in labels
    )
    provider_counts = Counter(str(label.get("selected_provider")) for label in labels)

    payload = {
        "schema_version": "krk_selected_provider_diversity_ownership_labels.v0",
        "causal_status": "non_causal_label_run",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(MANIFEST), str(REVIEW), str(OBSERVATION_SCAN)],
        "summary": {
            "label_count": len(labels),
            "wall_time_sec": wall_time,
            "selected_result_counts": dict(selected_counts),
            "forced_selected_provider_result_counts": dict(forced_counts),
            "ownership_label_counts": dict(owner_counts),
            "selected_result_counts_by_stage": dict(by_stage),
            "selected_provider_counts": dict(provider_counts),
            "trace_failures_only": True,
            "stage7_training_rows": 0,
        },
        "labels": labels,
        "decision": {
            "status": "selected_provider_diversity_ownership_labels_collected",
            "recommended_next_step": "merge_with_recovered_ownership_selection_labels",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
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
        "runtime_selector_implemented",
        "runtime_candidate_generator_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if payload["summary"]["stage7_training_rows"] != 0:
        raise ValueError("Stage 7 rows must remain excluded")
    for label in payload.get("labels") or []:
        if label.get("causal_status") != "non_causal_ownership_outcome_label":
            raise ValueError("labels must remain non-causal")
        if label.get("source_stage") == "stage7":
            raise ValueError("Stage 7 must not be a label source")


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# KRK Selected Provider Diversity Ownership Labels v0",
        "",
        "Bounded h40 normal-routing ownership labels for the selected-provider diversity jobs. "
        "This is offline evidence only and does not change runtime behavior.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Labels", ""])
    for label in payload["labels"]:
        forced = label.get("forced_provider_conversion_for_selected_provider") or {}
        lines.append(
            f"- `{label['state_id']}` stage=`{label['source_stage']}` "
            f"selected_provider=`{label.get('selected_provider')}` "
            f"selected=`{label['selected_playout_success'].get('result')}` "
            f"forced_selected=`{forced.get('result')}`"
        )
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_labels()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
