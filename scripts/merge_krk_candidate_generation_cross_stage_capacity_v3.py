#!/usr/bin/env python3
"""Merge cross-stage capacity labels and rerun candidate-generation refresh probe."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import probe_krk_candidate_generation_refresh_v2 as refresh_probe  # noqa: E402
from merge_krk_candidate_generation_capacity_evidence_v2 import _capacity_label  # noqa: E402


BASE_DATASET = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_dataset_v2_capacity_merged.json"
)
LABELS = Path(
    "reports/strategy_arbitration/krk_candidate_generation_cross_stage_capacity_labels_v3.json"
)
QUALITY = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v2_quality_probe.json")
OUT_DATASET_JSON = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_dataset_v2_cross_stage_capacity_merged.json"
)
OUT_DATASET_MD = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_dataset_v2_cross_stage_capacity_merged.md"
)
OUT_PROBE_JSON = Path(
    "reports/strategy_arbitration/krk_candidate_generation_refresh_probe_v2_cross_stage_labels.json"
)
OUT_PROBE_MD = Path(
    "reports/strategy_arbitration/krk_candidate_generation_refresh_probe_v2_cross_stage_labels.md"
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def label_to_row(label: dict[str, Any]) -> dict[str, Any]:
    capacity_label = _capacity_label(label.get("result"))
    return {
        "schema_version": "krk_strategy_sequence_dataset_row.v2",
        "row_id": f"cg_cross_stage_capacity_label_v3.{label.get('job_id')}",
        "state_id": label.get("state_id"),
        "fen": label.get("trace_first_fen") or label.get("fen"),
        "source_stage": label.get("source_stage"),
        "active_landmark_label": label.get("source_active_landmark_label"),
        "evidence_channel": "validated_provider_capacity",
        "frame_type": "validated_provider_candidate",
        "candidate_strategy_family": label.get("provider_family"),
        "candidate_provider_id": label.get("provider_id"),
        "candidate_move_uci": label.get("forced_first_move") or label.get("observed_move_uci"),
        "label_semantics": "forced_provider_capacity_not_runtime_ownership",
        "stage_family_cell": label.get("stage_family_cell"),
        "target_cell_maturity": label.get("target_cell_maturity"),
        "stage7_challenge_row": False,
        "legacy_usable_for_selector_training": False,
        "usable_for_selector_training_v2": False,
        "usable_for_candidate_generation_training_v2": capacity_label == "positive_capacity",
        "capacity_label": capacity_label,
        "source_terms": ["offline_cross_stage_candidate_generation_capacity_evidence_v3"],
        "move_shape_terms": [],
        "post_move_terms": [],
        "safety_terms": [],
        "internal_monitor_terms": [],
        "sequence_evidence_keys": [],
        "source_artifact": str(LABELS),
        "causal_status": "non_causal_dataset_row",
    }


def _summarize(rows: list[dict[str, Any]], label_rows: list[dict[str, Any]]) -> dict[str, Any]:
    channel_counts = Counter(row.get("evidence_channel") for row in rows)
    stage_counts = Counter(str(row.get("source_stage") or "unknown") for row in rows)
    generator_counts = Counter(
        row.get("evidence_channel")
        for row in rows
        if row.get("usable_for_candidate_generation_training_v2")
    )
    selector_count = sum(1 for row in rows if row.get("usable_for_selector_training_v2"))
    return {
        "row_count": len(rows),
        "row_count_by_channel": dict(sorted(channel_counts.items())),
        "source_stage_counts": dict(sorted(stage_counts.items())),
        "candidate_generation_training_row_count": sum(
            1 for row in rows if row.get("usable_for_candidate_generation_training_v2")
        ),
        "candidate_generation_training_row_count_by_channel": dict(
            sorted(generator_counts.items())
        ),
        "selector_training_row_count": selector_count,
        "stage7_challenge_row_count": sum(1 for row in rows if row.get("stage7_challenge_row")),
        "stage7_readiness_training_row_count": sum(
            1
            for row in rows
            if row.get("stage7_challenge_row")
            and (
                row.get("usable_for_selector_training_v2")
                or row.get("usable_for_candidate_generation_training_v2")
            )
        ),
        "merged_cross_stage_label_row_count": len(label_rows),
        "merged_cross_stage_label_capacity_counts": dict(
            sorted(Counter(row.get("capacity_label") for row in label_rows).items())
        ),
    }


def build_dataset_payload(
    base_dataset: dict[str, Any] | None = None,
    labels: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base_dataset = base_dataset or _load(BASE_DATASET)
    labels = labels or _load(LABELS)
    if labels.get("causal_status") != "non_causal_label_run":
        raise ValueError("labels must remain non-causal")
    if (labels.get("summary") or {}).get("stage7_label_count") != 0:
        raise ValueError("Stage 7 labels are not allowed")
    rows = list(base_dataset.get("rows") or [])
    label_rows = [
        label_to_row(label)
        for label in labels.get("labels") or []
        if _capacity_label(label.get("result")) in {"positive_capacity", "negative_capacity"}
    ]
    rows.extend(label_rows)
    summary = _summarize(rows, label_rows)
    return {
        "schema_version": "krk_strategy_sequence_dataset.v2_cross_stage_capacity_merged",
        "causal_status": "non_causal_dataset_refresh",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(BASE_DATASET), str(LABELS)],
        "summary": summary,
        "rows": rows,
        "decision": {
            "status": "strategy_sequence_dataset_v2_cross_stage_capacity_merged_non_causal",
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": "rerun_candidate_generation_refresh_probe",
        },
    }


def _write_dataset_md(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Strategy-Sequence Dataset v2 Cross-Stage Capacity-Merged",
        "",
        "This non-causal refresh merges bounded cross-stage forced-provider capacity labels into dataset v2. Labels remain capacity evidence, not ownership labels.",
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
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    (ROOT / OUT_DATASET_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_probe_md(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Candidate-Generation Refresh Probe v2 Cross-Stage Labels",
        "",
        "This reruns the non-causal candidate-generation refresh probe after merging cross-stage capacity labels.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
        f"- capacity_row_count: {summary['capacity_row_count']}",
        f"- capacity_label_counts: `{summary['capacity_label_counts']}`",
        f"- best_non_oracle_policy: `{summary['best_non_oracle_policy']}`",
        f"- best_non_oracle_metrics: `{summary['best_non_oracle_metrics']}`",
        f"- leave_stage_out_aggregate: `{summary['leave_stage_out_aggregate']}`",
    ]
    (ROOT / OUT_PROBE_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    dataset_payload = build_dataset_payload()
    (ROOT / OUT_DATASET_JSON).write_text(
        json.dumps(dataset_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_dataset_md(dataset_payload)
    probe_payload = refresh_probe.build_payload(
        dataset=dataset_payload,
        quality=_load(QUALITY),
    )
    probe_payload["source_artifacts"] = [str(OUT_DATASET_JSON), str(QUALITY)]
    (ROOT / OUT_PROBE_JSON).write_text(
        json.dumps(probe_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_probe_md(probe_payload)
    print(json.dumps(probe_payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
