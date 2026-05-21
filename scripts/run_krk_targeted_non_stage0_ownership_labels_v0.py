#!/usr/bin/env python3
"""Run bounded labels for historical non-stage0 selected-owner states.

This diagnostic checks whether current handoff composition preserves historical
non-stage0 ownership in protected states. It records non-causal evidence only.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from recon_lite.engine import ReConEngine  # noqa: E402
from run_krk_strategy_arbiter_out_of_sample_control_labels import _run_job  # noqa: E402


MANIFEST = Path("reports/krk_targeted_non_stage0_ownership_manifest_v0.json")
OUT_JSON = Path("reports/krk_targeted_non_stage0_ownership_labels_v0.json")
OUT_MD = Path("reports/krk_targeted_non_stage0_ownership_labels_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _annotate_label(label: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
    historical_provider = str(job.get("historical_selected_provider") or "")
    historical_move = str(job.get("historical_selected_move") or "")
    current_provider = str(label.get("selected_provider") or "")
    current_move = str(label.get("selected_move") or "")
    selected_result = (label.get("selected_playout_success") or {}).get("result")
    forced_result = (label.get("forced_provider_conversion_for_selected_provider") or {}).get(
        "result"
    )
    return {
        **label,
        "schema_version": "krk_targeted_non_stage0_ownership_label.v0",
        "historical_selected_provider": historical_provider,
        "historical_selected_move": historical_move,
        "historical_negative_providers": job.get("historical_negative_providers") or [],
        "current_profile_selected_provider": current_provider,
        "current_profile_selected_move": current_move,
        "historical_selection_preserved": current_provider == historical_provider,
        "historical_move_preserved": bool(historical_move) and current_move == historical_move,
        "current_profile_collapsed_to_stage0": current_provider == "krk.stage0_basin",
        "current_profile_selected_owner_converted": selected_result == "mate",
        "forced_current_selected_provider_converted": forced_result == "mate",
        "targeted_source_diversity_signal": (
            "historical_non_stage0_preserved"
            if current_provider == historical_provider
            else "current_profile_owner_shifted"
        ),
    }


def run_labels(repo_root: Path) -> dict[str, Any]:
    manifest = _load_json(repo_root / MANIFEST)
    if manifest.get("causal_status") != "non_causal_execution_manifest":
        raise ValueError("manifest must remain non-causal")
    if manifest.get("decision", {}).get("execute_labels_now") is not True:
        raise ValueError("manifest must explicitly allow this bounded label run")
    if not (manifest.get("binding_summary") or {}).get("all_bindings_valid"):
        raise ValueError("manifest bindings must be valid")

    cache: dict[str, tuple[Any, ReConEngine]] = {}
    start = time.perf_counter()
    labels = [
        _annotate_label(_run_job(repo_root, job, cache), job)
        for job in manifest.get("jobs") or []
    ]
    wall_time = round(time.perf_counter() - start, 6)

    current_provider_counts = Counter(label["current_profile_selected_provider"] for label in labels)
    historical_provider_counts = Counter(label["historical_selected_provider"] for label in labels)
    preservation_counts = Counter(
        "preserved" if label["historical_selection_preserved"] else "shifted"
        for label in labels
    )
    collapse_counts = Counter(
        "stage0_collapse" if label["current_profile_collapsed_to_stage0"] else "non_stage0_current"
        for label in labels
    )
    result_counts = Counter(
        (label.get("selected_playout_success") or {}).get("result") for label in labels
    )
    provider_result_counts = Counter(
        f"{label['current_profile_selected_provider']}:{(label.get('selected_playout_success') or {}).get('result')}"
        for label in labels
    )

    non_stage0_current = sum(
        1 for label in labels if label["current_profile_selected_provider"] != "krk.stage0_basin"
    )
    stage0_collapse_count = sum(
        1 for label in labels if label["current_profile_collapsed_to_stage0"]
    )
    preserved_count = sum(1 for label in labels if label["historical_selection_preserved"])

    if preserved_count:
        status = "current_profile_preserves_some_historical_non_stage0_ownership"
        next_step = "merge_preserved_non_stage0_labels_then_reprobe_selector_features"
    elif stage0_collapse_count == len(labels) and labels:
        status = "current_profile_collapses_historical_non_stage0_states_to_stage0"
        next_step = "review_routing_profile_dominance_before_more_label_farming"
    else:
        status = "current_profile_shifts_historical_non_stage0_ownership_to_other_providers"
        next_step = "review_owner_shift_semantics_before_selector_training"

    payload = {
        "schema_version": "krk_targeted_non_stage0_ownership_labels.v0",
        "causal_status": "non_causal_label_run",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "selector_training_allowed": False,
        "source_artifacts": [str(MANIFEST)],
        "summary": {
            "label_count": len(labels),
            "wall_time_sec": wall_time,
            "historical_selected_provider_counts": dict(sorted(historical_provider_counts.items())),
            "current_selected_provider_counts": dict(sorted(current_provider_counts.items())),
            "historical_selection_preservation_counts": dict(sorted(preservation_counts.items())),
            "stage0_collapse_counts": dict(sorted(collapse_counts.items())),
            "selected_result_counts": dict(sorted(result_counts.items())),
            "current_provider_result_counts": dict(sorted(provider_result_counts.items())),
            "current_non_stage0_selected_owner_count": non_stage0_current,
            "current_stage0_collapse_count": stage0_collapse_count,
            "preserved_historical_non_stage0_count": preserved_count,
            "trace_failures_only": True,
            "stage7_training_rows": 0,
        },
        "labels": labels,
        "decision": {
            "status": status,
            "selector_training_allowed": False,
            "runtime_arbiter_allowed": False,
            "recommended_next_step": next_step,
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
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
        "selector_training_allowed",
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
        "# KRK Targeted Non-Stage0 Ownership Labels v0",
        "",
        "This is a bounded offline label run. It asks whether the current handoff "
        "profile preserves historical non-stage0 selected ownership. It does not "
        "train a selector, change runtime defaults, or alter topology.",
        "",
        "## Summary",
        "",
        f"- Label count: `{summary['label_count']}`",
        f"- Wall time sec: `{summary['wall_time_sec']}`",
        f"- Historical provider counts: `{summary['historical_selected_provider_counts']}`",
        f"- Current provider counts: `{summary['current_selected_provider_counts']}`",
        f"- Historical preservation counts: `{summary['historical_selection_preservation_counts']}`",
        f"- Stage0 collapse counts: `{summary['stage0_collapse_counts']}`",
        f"- Selected result counts: `{summary['selected_result_counts']}`",
        f"- Current provider/result counts: `{summary['current_provider_result_counts']}`",
        f"- Stage 7 training rows: `{summary['stage7_training_rows']}`",
        "",
        "## Labels",
        "",
    ]
    for label in payload["labels"]:
        selected = label.get("selected_playout_success") or {}
        lines.append(
            f"- `{label['state_id']}` stage=`{label['source_stage']}` "
            f"historical=`{label['historical_selected_provider']}` "
            f"current=`{label['current_profile_selected_provider']}` "
            f"preserved=`{label['historical_selection_preserved']}` "
            f"stage0_collapse=`{label['current_profile_collapsed_to_stage0']}` "
            f"result=`{selected.get('result')}`"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Status: `{payload['decision']['status']}`",
            f"- Recommended next step: `{payload['decision']['recommended_next_step']}`",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


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
