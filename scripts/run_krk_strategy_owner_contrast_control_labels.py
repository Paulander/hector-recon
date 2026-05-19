#!/usr/bin/env python3
"""Run bounded KRK strategy-owner contrast control labels.

This is an offline diagnostic label run from a reviewed manifest. It writes
non-causal outcome labels only and does not change runtime behavior, implement
a selector, promote Stage 7, or train Stage 8.
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

import run_krk_forced_provider_control_labels as forced_labels  # noqa: E402


MANIFEST = Path("reports/krk_strategy_owner_contrast_execution_manifest_v0.json")
REVIEW = Path("reports/krk_strategy_owner_contrast_execution_manifest_review_v0.json")
OUT_JSON = Path("reports/krk_strategy_owner_contrast_control_labels_v0.json")
OUT_MD = Path("reports/krk_strategy_owner_contrast_control_labels_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def run_labels() -> dict[str, Any]:
    manifest = _load_json(MANIFEST)
    review = _load_json(REVIEW)
    if manifest.get("causal_status") != "non_causal_execution_manifest":
        raise ValueError("manifest must remain non-causal")
    if review.get("causal_status") != "non_causal_manifest_review":
        raise ValueError("manifest review must remain non-causal")
    if not (review.get("decision") or {}).get("labels_allowed"):
        raise ValueError("manifest review must allow labels")
    cache: dict[str, tuple[Any, Any]] = {}
    start = time.monotonic()
    labels = [forced_labels._run_job(ROOT, job, cache) for job in manifest.get("jobs") or []]
    wall_time = time.monotonic() - start
    result_counts = Counter(str(label.get("result") or "unknown") for label in labels)
    by_stage = Counter(f"{label.get('source_stage')}:{label.get('result')}" for label in labels)
    by_provider = Counter(f"{label.get('provider_id')}:{label.get('result')}" for label in labels)
    payload = {
        "schema_version": "krk_strategy_owner_contrast_control_labels.v0",
        "causal_status": "non_causal_label_run",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(MANIFEST), str(REVIEW)],
        "summary": {
            "label_count": len(labels),
            "result_counts": dict(sorted(result_counts.items())),
            "result_counts_by_stage": dict(sorted(by_stage.items())),
            "result_counts_by_provider": dict(sorted(by_provider.items())),
            "stage7_labels": sum(1 for label in labels if label.get("source_stage") == "stage7"),
            "trace_failures_only": True,
            "wall_time_seconds": round(wall_time, 3),
        },
        "labels": labels,
        "recommended_next_step": "merge_contrast_labels_and_rebuild_strategy_owner_contrast_dataset",
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
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if payload["summary"]["stage7_labels"] != 0:
        raise ValueError("Stage 7 labels must remain excluded")
    for label in payload.get("labels") or []:
        if label.get("causal_status") != "non_causal_outcome_label":
            raise ValueError("labels must remain non-causal")


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# KRK Strategy Owner Contrast Control Labels v0",
        "",
        "This is an offline non-causal label run. It forced each configured provider "
        "only for the first White move, then released to the normal topology.",
        "",
        "## Summary",
        "",
        f"- Label count: `{summary['label_count']}`",
        f"- Result counts: `{summary['result_counts']}`",
        f"- Result counts by stage: `{summary['result_counts_by_stage']}`",
        f"- Result counts by provider: `{summary['result_counts_by_provider']}`",
        f"- Stage 7 labels: `{summary['stage7_labels']}`",
        f"- Wall time seconds: `{summary['wall_time_seconds']}`",
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


def main() -> None:
    payload = run_labels()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
