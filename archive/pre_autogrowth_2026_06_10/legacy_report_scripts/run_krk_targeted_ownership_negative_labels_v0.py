#!/usr/bin/env python3
"""Run bounded targeted ownership-negative label jobs."""

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


MANIFEST = Path("reports/krk_targeted_ownership_negative_manifest_v0.json")
OUT_JSON = Path("reports/krk_targeted_ownership_negative_labels_v0.json")
OUT_MD = Path("reports/krk_targeted_ownership_negative_labels_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _annotate(label: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
    selected_provider = str(label.get("selected_provider") or "")
    preselected_provider = str(job.get("current_profile_preselected_provider") or "")
    result = (label.get("selected_playout_success") or {}).get("result")
    return {
        **label,
        "schema_version": "krk_targeted_ownership_negative_label.v0",
        "target_cell_id": job.get("target_cell_id"),
        "target_cell_reason": job.get("target_cell_reason"),
        "preselected_provider": preselected_provider,
        "preselected_move": job.get("current_profile_preselected_move"),
        "preselection_preserved": selected_provider == preselected_provider,
        "targeted_owner_failed": result != "mate",
        "targeted_owner_converted": result == "mate",
        "label_semantics": "current_profile_selected_owner_outcome_in_false_positive_risk_cell",
    }


def run_labels(repo_root: Path) -> dict[str, Any]:
    manifest = _load_json(repo_root / MANIFEST)
    if manifest.get("causal_status") != "non_causal_execution_manifest":
        raise ValueError("manifest must remain non-causal")
    if manifest.get("decision", {}).get("execute_labels_now") is not True:
        raise ValueError("manifest must allow bounded label execution")
    cache: dict[str, tuple[Any, ReConEngine]] = {}
    start = time.perf_counter()
    labels = [
        _annotate(_run_job(repo_root, job, cache), job)
        for job in manifest.get("jobs") or []
    ]
    wall_time = round(time.perf_counter() - start, 6)
    result_counts = Counter((label.get("selected_playout_success") or {}).get("result") for label in labels)
    provider_result_counts = Counter(
        f"{label.get('selected_provider')}:{(label.get('selected_playout_success') or {}).get('result')}"
        for label in labels
    )
    cell_result_counts = Counter(
        f"{label.get('target_cell_id')}:{(label.get('selected_playout_success') or {}).get('result')}"
        for label in labels
    )
    payload = {
        "schema_version": "krk_targeted_ownership_negative_labels.v0",
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
        "selector_training_allowed": False,
        "source_artifacts": [str(MANIFEST)],
        "summary": {
            "label_count": len(labels),
            "wall_time_sec": wall_time,
            "selected_result_counts": dict(sorted(result_counts.items())),
            "provider_result_counts": dict(sorted(provider_result_counts.items())),
            "target_cell_result_counts": dict(sorted(cell_result_counts.items())),
            "targeted_owner_failed_count": sum(1 for label in labels if label["targeted_owner_failed"]),
            "targeted_owner_converted_count": sum(1 for label in labels if label["targeted_owner_converted"]),
            "preselection_preserved_count": sum(1 for label in labels if label["preselection_preserved"]),
            "trace_failures_only": True,
            "stage7_training_rows": 0,
        },
        "labels": labels,
        "decision": {
            "status": "targeted_ownership_negative_labels_collected",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "recommended_next_step": "merge_targeted_ownership_negative_labels_and_reprobe",
        },
        "blocked_next_steps": [
            "runtime_arbiter",
            "runtime_selector",
            "selector_training",
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
        raise ValueError("payload must remain non-causal")
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
        "selector_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    for label in payload.get("labels") or []:
        if label.get("source_stage") == "stage7":
            raise ValueError("Stage 7 must remain excluded")
        if label.get("causal_status") != "non_causal_outcome_label":
            raise ValueError("labels must remain non-causal")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Targeted Ownership Negative Labels v0",
        "",
        "Bounded non-causal h40 labels for false-positive ownership risk cells. "
        "No selector was trained or run.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Labels", ""])
    for label in payload["labels"]:
        lines.append(
            f"- `{label['state_id']}` cell=`{label['target_cell_id']}` "
            f"provider=`{label.get('selected_provider')}` "
            f"result=`{(label.get('selected_playout_success') or {}).get('result')}`"
        )
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
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
