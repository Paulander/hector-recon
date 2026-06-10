#!/usr/bin/env python3
"""Build replay-free protected-control labels for abstention-first selector work."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LABEL_SOURCES = (
    Path("reports/krk_forced_provider_control_labels_v0.json"),
    Path("reports/krk_strategy_owner_contrast_control_labels_v0.json"),
    Path("reports/krk_diverse_contrast_labels_v1.json"),
)
OBJECTIVE = Path("reports/krk_abstention_first_selector_objective_v0.json")
OUT_JSON = Path("reports/krk_abstention_training_dataset_v0.json")
OUT_MD = Path("reports/krk_abstention_training_dataset_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _provider_family(provider_id: str) -> str:
    if provider_id == "krk.stage0_basin":
        return "stage0_basin"
    if provider_id == "krk.drive_to_edge":
        return "drive_to_edge"
    if provider_id == "krk.fence_established":
        return "fence_established"
    if provider_id.startswith("krk.edge_trap"):
        return "edge_trap"
    if provider_id.startswith("krk.box_shrink"):
        return "box_shrink"
    return "other"


def _provider_maturity(provider_id: str) -> str:
    if provider_id == "krk.stage0_basin":
        return "foundation_frozen"
    if provider_id == "krk.drive_to_edge":
        return "settling_medium_plasticity"
    if provider_id in {
        "krk.fence_established",
        "krk.edge_trap_close",
        "krk.edge_trap_enemy_between",
        "krk.edge_trap_wrong_tempo",
    }:
        return "validated_low_plasticity"
    return "unknown"


def _contrast_label(result: str | None) -> str | None:
    if result == "mate":
        return "safe_owner"
    if result == "max_plies":
        return "unsafe_owner"
    return None


def build_dataset() -> dict[str, Any]:
    objective = _load_json(OBJECTIVE)
    if objective.get("causal_status") != "non_causal_design":
        raise ValueError("abstention objective must remain non-causal design")

    rows = []
    seen = set()
    for path in LABEL_SOURCES:
        payload = _load_json(path)
        if payload.get("causal_status") != "non_causal_label_run":
            raise ValueError(f"{path}: label run must remain non-causal")
        for label in payload.get("labels") or []:
            source_stage = str(label.get("source_stage") or "")
            if source_stage == "stage7" or label.get("stage7_challenge_row"):
                continue
            contrast = _contrast_label(label.get("result"))
            if contrast is None:
                continue
            provider_id = str(label.get("provider_id") or "")
            key = (label.get("job_id"), source_stage, label.get("state_id"), provider_id)
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "schema_version": "krk_abstention_training_row.v0",
                "causal_status": "non_causal_training_example",
                "label_source_artifact": str(path),
                "source_label_job_id": label.get("job_id"),
                "state_id": label.get("state_id"),
                "frame_id": label.get("frame_id"),
                "source_stage": source_stage,
                "provider_id": provider_id,
                "provider_family": label.get("provider_family") or _provider_family(provider_id),
                "provider_maturity": label.get("provider_maturity") or _provider_maturity(provider_id),
                "provider_version": label.get("provider_version"),
                "forced_first_move": label.get("forced_first_move"),
                "forced_result": label.get("result"),
                "forced_plies": label.get("plies"),
                "engine_decision_count": label.get("engine_decision_count"),
                "engine_ticks_total": label.get("engine_ticks_total"),
                "abstention_label": contrast,
                "usable_for_training": True,
            })

    summary = {
        "row_count": len(rows),
        "state_count": len({row["state_id"] for row in rows}),
        "label_counts": dict(Counter(str(row["abstention_label"]) for row in rows)),
        "stage_counts": dict(Counter(str(row["source_stage"]) for row in rows)),
        "provider_family_counts": dict(Counter(str(row["provider_family"]) for row in rows)),
        "provider_maturity_counts": dict(Counter(str(row["provider_maturity"]) for row in rows)),
        "stage7_training_rows": sum(1 for row in rows if row["source_stage"] == "stage7"),
        "minimum_training_rows_required": (objective.get("data_requirements_before_runtime_review") or {}).get("minimum_training_rows"),
        "minimum_negative_rows_required": (objective.get("data_requirements_before_runtime_review") or {}).get("minimum_negative_training_rows"),
    }
    negative_count = summary["label_counts"].get("unsafe_owner", 0)
    row_requirement = int(summary["minimum_training_rows_required"] or 0)
    neg_requirement = int(summary["minimum_negative_rows_required"] or 0)
    status = (
        "abstention_training_dataset_ready_for_probe"
        if len(rows) >= row_requirement and negative_count >= neg_requirement
        else "abstention_training_dataset_under_minimum_requirements"
    )
    dataset = {
        "schema_version": "krk_abstention_training_dataset.v0",
        "causal_status": "non_causal_abstention_dataset",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(OBJECTIVE), *(str(path) for path in LABEL_SOURCES)],
        "summary": summary,
        "rows": rows,
        "decision": {
            "status": status,
            "recommended_next_step": "probe_abstention_dataset_non_causal" if rows else "collect_more_protected_controls",
            "runtime_test_allowed_next": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_dataset(dataset)
    return dataset


def validate_dataset(dataset: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if dataset.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if dataset["summary"]["stage7_training_rows"] != 0:
        raise ValueError("Stage7 rows must not be used for abstention training")


def render_markdown(dataset: dict[str, Any]) -> str:
    lines = [
        "# KRK Abstention Training Dataset v0",
        "",
        "This replay-free dataset reconstructs protected-control abstention labels from existing forced-provider outcomes. It is non-causal and does not run playouts.",
        "",
        "## Summary",
        "",
    ]
    for key, value in dataset["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Status: `{dataset['decision']['status']}`",
            f"- Recommended next step: `{dataset['decision']['recommended_next_step']}`",
            f"- Runtime test allowed next: `{dataset['decision']['runtime_test_allowed_next']}`",
            f"- Stage 7 promotion allowed: `{dataset['decision']['stage7_promotion_allowed']}`",
            f"- Stage 8 training allowed: `{dataset['decision']['stage8_training_allowed']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    dataset = build_dataset()
    (ROOT / OUT_JSON).write_text(json.dumps(dataset, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(dataset), encoding="utf-8")
    print(json.dumps(dataset["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
