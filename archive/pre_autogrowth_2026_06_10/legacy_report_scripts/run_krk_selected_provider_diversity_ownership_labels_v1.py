#!/usr/bin/env python3
"""Run a second bounded ownership-label slice from a fresh protected seed."""

from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_krk_selected_provider_diversity_sampling_manifest as manifest_builder  # noqa: E402
import run_krk_strategy_arbiter_out_of_sample_control_labels as label_runner  # noqa: E402


OUT_MANIFEST_JSON = Path("reports/krk_selected_provider_diversity_sampling_manifest_v1.json")
OUT_MANIFEST_MD = Path("reports/krk_selected_provider_diversity_sampling_manifest_v1.md")
OUT_JSON = Path("reports/krk_selected_provider_diversity_ownership_labels_v1.json")
OUT_MD = Path("reports/krk_selected_provider_diversity_ownership_labels_v1.md")


def _normalize_label(label: dict[str, Any]) -> dict[str, Any]:
    return {
        **label,
        "schema_version": "krk_selected_provider_diversity_ownership_label.v1",
        "causal_status": "non_causal_ownership_outcome_label",
        "label_source": "selected_provider_diversity_fresh_seed_normal_routing_h40",
        "source_manifest": str(OUT_MANIFEST_JSON),
    }


def _build_fresh_manifest() -> dict[str, Any]:
    manifest = manifest_builder.build_manifest(max_jobs=24, per_stage_max=8, base_seed=31, max_sample_index=500)
    manifest["schema_version"] = "krk_selected_provider_diversity_sampling_manifest.v1"
    manifest["selection_policy"]["fresh_seed_label_slice"] = True
    manifest["selection_policy"]["playout_labels"] = True
    manifest["decision"] = {
        "status": "fresh_seed_selected_provider_diversity_manifest_ready_for_bounded_labels",
        "runtime_arbiter_allowed": False,
        "selector_sandbox_ready": False,
        "observations_allowed_now": False,
        "bounded_labels_allowed_by_script": True,
        "recommended_next_step": "run_bounded_selected_provider_diversity_ownership_labels",
    }
    manifest_builder.validate_manifest({**manifest, "selection_policy": {**manifest["selection_policy"], "playout_labels": False}})
    return manifest


def build_labels() -> dict[str, Any]:
    manifest = _build_fresh_manifest()
    if (manifest.get("binding_summary") or {}).get("all_bindings_valid") is not True:
        raise ValueError("fresh seed manifest bindings must be valid")
    if len(manifest.get("jobs") or []) > 24:
        raise ValueError("fresh seed label run is bounded to at most 24 jobs")
    if any(job.get("source_stage") == "stage7" for job in manifest.get("jobs") or []):
        raise ValueError("Stage 7 jobs must remain excluded")

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
        "schema_version": "krk_selected_provider_diversity_ownership_labels.v1",
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
        "source_artifacts": [str(OUT_MANIFEST_JSON)],
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
            "status": "fresh_seed_selected_provider_diversity_ownership_labels_collected",
            "recommended_next_step": "merge_with_expanded_ownership_selection_labels",
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
        "manifest": manifest,
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


def _render_manifest_markdown(manifest: dict[str, Any]) -> str:
    summary = manifest["binding_summary"]
    return "\n".join(
        [
            "# KRK Selected Provider Diversity Sampling Manifest v1",
            "",
            "Fresh-seed bounded protected manifest for non-causal ownership label collection.",
            "",
            "## Summary",
            "",
            f"- Jobs: `{summary['job_count']}`",
            f"- Jobs by stage: `{summary['job_count_by_stage']}`",
            f"- All bindings valid: `{summary['all_bindings_valid']}`",
            f"- Missing paths: `{summary['missing_paths']}`",
            "",
            "## Decision",
            "",
            f"- Status: `{manifest['decision']['status']}`",
            f"- Recommended next step: `{manifest['decision']['recommended_next_step']}`",
            "- Runtime arbiter and selector sandbox remain blocked.",
            "",
        ]
    )


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# KRK Selected Provider Diversity Ownership Labels v1",
        "",
        "Second bounded h40 normal-routing ownership label slice from a fresh protected seed. "
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
    manifest = payload.pop("manifest")
    (ROOT / OUT_MANIFEST_JSON).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MANIFEST_MD).write_text(_render_manifest_markdown(manifest), encoding="utf-8")
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
