#!/usr/bin/env python3
"""Build abstention labels from forced-provider and selected-playout evidence."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_krk_abstention_training_dataset_v0 as base  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
TARGETS = Path("reports/krk_selector_target_dataset_v0.json")
OUT_JSON = Path("reports/krk_abstention_training_dataset_v1.json")
OUT_MD = Path("reports/krk_abstention_training_dataset_v1.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _map_label(label: str | None) -> str | None:
    if label == "positive":
        return "safe_owner"
    if label == "negative":
        return "unsafe_owner"
    return None


def build_dataset() -> dict[str, Any]:
    dataset = base.build_dataset()
    targets = _load_json(TARGETS)
    if targets.get("causal_status") != "non_causal_target_dataset":
        raise ValueError("selector target dataset must remain non-causal")

    rows = list(dataset["rows"])
    seen = {
        (
            row.get("state_id"),
            row.get("provider_id"),
            row.get("forced_first_move"),
            row.get("abstention_label"),
            row.get("label_source_artifact"),
        )
        for row in rows
    }
    for target in targets.get("rows") or []:
        if target.get("source_stage") == "stage7" or target.get("usable_for_training") is not True:
            continue
        if target.get("target_kind") != "selected_playout_success":
            continue
        abstention_label = _map_label(target.get("label"))
        if abstention_label is None:
            continue
        provider_id = str(target.get("provider_id") or "")
        key = (
            target.get("state_id"),
            provider_id,
            target.get("move_uci"),
            abstention_label,
            str(TARGETS),
        )
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "schema_version": "krk_abstention_training_row.v1",
            "causal_status": "non_causal_training_example",
            "label_source_artifact": str(TARGETS),
            "source_label_job_id": None,
            "target_kind": target.get("target_kind"),
            "state_id": target.get("state_id"),
            "frame_id": target.get("frame_id"),
            "source_stage": target.get("source_stage"),
            "active_landmark_label": target.get("active_landmark_label"),
            "provider_id": provider_id,
            "provider_family": base._provider_family(provider_id),
            "provider_maturity": base._provider_maturity(provider_id),
            "provider_version": None,
            "forced_first_move": target.get("move_uci"),
            "forced_result": target.get("raw_result"),
            "forced_plies": target.get("plies"),
            "engine_decision_count": None,
            "engine_ticks_total": None,
            "abstention_label": abstention_label,
            "usable_for_training": True,
        })

    from collections import Counter

    summary = {
        "row_count": len(rows),
        "state_count": len({row["state_id"] for row in rows}),
        "label_counts": dict(Counter(str(row["abstention_label"]) for row in rows)),
        "stage_counts": dict(Counter(str(row["source_stage"]) for row in rows)),
        "provider_family_counts": dict(Counter(str(row["provider_family"]) for row in rows)),
        "provider_maturity_counts": dict(Counter(str(row["provider_maturity"]) for row in rows)),
        "source_artifact_counts": dict(Counter(str(row["label_source_artifact"]) for row in rows)),
        "stage7_training_rows": sum(1 for row in rows if row["source_stage"] == "stage7"),
        "minimum_training_rows_required": 40,
        "minimum_negative_rows_required": 12,
    }
    status = (
        "abstention_training_dataset_ready_for_probe"
        if summary["row_count"] >= 40 and summary["label_counts"].get("unsafe_owner", 0) >= 12
        else "abstention_training_dataset_under_minimum_requirements"
    )
    payload = {
        "schema_version": "krk_abstention_training_dataset.v1",
        "causal_status": "non_causal_abstention_dataset",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [*dataset["source_artifacts"], str(TARGETS)],
        "summary": summary,
        "rows": rows,
        "decision": {
            "status": status,
            "recommended_next_step": "probe_abstention_dataset_v1_non_causal",
            "runtime_test_allowed_next": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    base.validate_dataset(payload)
    return payload


def main() -> None:
    dataset = build_dataset()
    (ROOT / OUT_JSON).write_text(json.dumps(dataset, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(base.render_markdown(dataset), encoding="utf-8")
    print(json.dumps(dataset["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
