#!/usr/bin/env python3
"""Probe the state-local paired ownership objective non-causally."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = Path("reports/krk_state_local_paired_ownership_inventory_v1.json")
OUT_JSON = Path("reports/krk_state_local_paired_ownership_probe_v0.json")
OUT_MD = Path("reports/krk_state_local_paired_ownership_probe_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _nested(row: dict[str, Any], path: str) -> Any:
    value: Any = row
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _feature_value(row: dict[str, Any], key: str) -> str:
    if key.startswith("ctx:"):
        return str(_nested(row, key.split(":", 1)[1]))
    return str(row.get(key))


def _feature_key(row: dict[str, Any], keys: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_feature_value(row, key) for key in keys)


def _target_prefer_capacity(row: dict[str, Any]) -> bool:
    return row.get("comparison_label") == "prefer_capacity_alternative"


def _score(train: list[dict[str, Any]], row: dict[str, Any], keys: tuple[str, ...]) -> float:
    global_rate = (
        sum(1 for item in train if _target_prefer_capacity(item)) / len(train)
        if train
        else 0.5
    )
    counts: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    for item in train:
        counts[_feature_key(item, keys)]["prefer_capacity" if _target_prefer_capacity(item) else "preserve_selected"] += 1
    counter = counts.get(_feature_key(row, keys))
    if not counter:
        return global_rate
    total = counter["prefer_capacity"] + counter["preserve_selected"]
    return counter["prefer_capacity"] / total if total else global_rate


def _metrics(rows: list[dict[str, Any]], keys: tuple[str, ...], threshold: float) -> dict[str, Any]:
    predictions = []
    for state_id in sorted({str(row.get("state_id")) for row in rows}):
        train = [row for row in rows if str(row.get("state_id")) != state_id]
        test = [row for row in rows if str(row.get("state_id")) == state_id]
        for row in test:
            score = _score(train, row, keys)
            predicted_capacity = score >= threshold
            target_capacity = _target_prefer_capacity(row)
            predictions.append(
                {
                    "state_id": row.get("state_id"),
                    "source_stage": row.get("source_stage"),
                    "owner_a": row.get("owner_a"),
                    "owner_b": row.get("owner_b"),
                    "comparison_label": row.get("comparison_label"),
                    "evidence_channel": row.get("evidence_channel"),
                    "score": score,
                    "threshold": threshold,
                    "predicted_prefer_capacity": predicted_capacity,
                    "target_prefer_capacity": target_capacity,
                    "feature_key": list(_feature_key(row, keys)),
                }
            )
    tp = sum(1 for item in predictions if item["predicted_prefer_capacity"] and item["target_prefer_capacity"])
    fp = sum(1 for item in predictions if item["predicted_prefer_capacity"] and not item["target_prefer_capacity"])
    tn = sum(1 for item in predictions if not item["predicted_prefer_capacity"] and not item["target_prefer_capacity"])
    fn = sum(1 for item in predictions if not item["predicted_prefer_capacity"] and item["target_prefer_capacity"])
    total = len(predictions)
    strong = [item for item in predictions if item["evidence_channel"] == "strong_same_state_conflict"]
    safe = [item for item in predictions if item["evidence_channel"] == "safe_preservation"]
    return {
        "row_count": total,
        "threshold": threshold,
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "accuracy": (tp + tn) / total if total else None,
        "prefer_capacity_precision": tp / (tp + fp) if tp + fp else None,
        "prefer_capacity_recall": tp / (tp + fn) if tp + fn else None,
        "selected_preservation_recall": tn / (tn + fp) if tn + fp else None,
        "strong_conflict_accuracy": (
            sum(
                1
                for item in strong
                if item["predicted_prefer_capacity"] == item["target_prefer_capacity"]
            )
            / len(strong)
            if strong
            else None
        ),
        "safe_preservation_recall": (
            sum(1 for item in safe if not item["predicted_prefer_capacity"]) / len(safe)
            if safe
            else None
        ),
        "predictions": predictions,
    }


def build_probe() -> dict[str, Any]:
    inventory = _load(INVENTORY)
    if inventory.get("causal_status") != "non_causal_pair_inventory":
        raise ValueError("paired inventory must remain non-causal")
    readiness = inventory.get("minimum_readiness") or {}
    rows = [
        row
        for row in inventory.get("rows") or []
        if row.get("source_stage") != "stage7"
        and row.get("comparison_label")
        in {
            "prefer_selected_owner",
            "prefer_capacity_alternative",
            "equivalent_positive_or_preserve_selected",
        }
    ]
    specs = {
        "owner_family_pair": ("owner_a_family", "owner_b_family"),
        "stage_owner_family_pair": ("source_stage", "owner_a_family", "owner_b_family"),
        "landmark_owner_family_pair": (
            "active_landmark_label",
            "owner_a_family",
            "owner_b_family",
        ),
        "context_owner_pair": (
            "owner_a_family",
            "owner_b_family",
            "ctx:terminal_space_context.black_king_edge_bucket",
            "ctx:terminal_space_context.white_king_support_bucket",
        ),
        "stage_context_owner_pair": (
            "source_stage",
            "owner_a_family",
            "owner_b_family",
            "ctx:terminal_space_context.black_king_edge_bucket",
            "ctx:terminal_space_context.white_king_support_bucket",
        ),
    }
    thresholds = (0.25, 0.4, 0.5, 0.6)
    results = {
        f"{name}@{threshold}": {"features": list(keys), **_metrics(rows, keys, threshold)}
        for name, keys in specs.items()
        for threshold in thresholds
    }
    best_name, best = max(
        results.items(),
        key=lambda item: (
            item[1].get("prefer_capacity_recall") or 0.0,
            item[1].get("selected_preservation_recall") or 0.0,
            item[1].get("safe_preservation_recall") or 0.0,
            item[1].get("accuracy") or 0.0,
        ),
    )
    balanced_candidates = [
        (name, result)
        for name, result in results.items()
        if (result.get("prefer_capacity_recall") or 0.0) >= 0.7
        and (result.get("selected_preservation_recall") or 0.0) >= 0.7
    ]
    balanced_name, balanced = max(
        balanced_candidates or list(results.items()),
        key=lambda item: (
            item[1].get("prefer_capacity_recall") or 0.0,
            item[1].get("selected_preservation_recall") or 0.0,
            item[1].get("safe_preservation_recall") or 0.0,
            item[1].get("accuracy") or 0.0,
        ),
    )
    ready = all(bool(value) for value in readiness.values())
    balanced_ready = (
        (balanced.get("prefer_capacity_recall") or 0.0) >= 0.7
        and (balanced.get("selected_preservation_recall") or 0.0) >= 0.7
        and (balanced.get("safe_preservation_recall") or 0.0) >= 0.8
    )
    payload = {
        "schema_version": "krk_state_local_paired_ownership_probe.v0",
        "causal_status": "non_causal_offline_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "selector_training_allowed": False,
        "source_artifacts": [str(INVENTORY)],
        "summary": {
            "row_count": len(rows),
            "state_count": len({row.get("state_id") for row in rows}),
            "prefer_capacity_count": sum(1 for row in rows if _target_prefer_capacity(row)),
            "preserve_selected_count": sum(1 for row in rows if not _target_prefer_capacity(row)),
            "safe_preservation_pair_count": sum(1 for row in rows if row.get("evidence_channel") == "safe_preservation"),
            "strong_conflict_pair_count": sum(1 for row in rows if row.get("evidence_channel") == "strong_same_state_conflict"),
            "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
            "inventory_ready": ready,
        },
        "results": results,
        "best_result": {
            "objective": best_name,
            **{key: value for key, value in best.items() if key != "predictions"},
        },
        "best_balanced_result": {
            "objective": balanced_name,
            **{key: value for key, value in balanced.items() if key != "predictions"},
        },
        "decision": {
            "status": (
                "paired_objective_promising_non_causal"
                if ready and balanced_ready
                else "paired_objective_feature_model_insufficient"
            ),
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "recommended_next_step": "review_paired_objective_before_any_runtime_work",
        },
    }
    validate_probe(payload)
    return payload


def validate_probe(payload: dict[str, Any]) -> None:
    if payload.get("causal_status") != "non_causal_offline_probe":
        raise ValueError("probe must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
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
    if payload["summary"]["stage7_row_count"] != 0:
        raise ValueError("Stage 7 rows must remain excluded")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK State-Local Paired Ownership Probe v0",
        "",
        "Non-causal leave-state-out probe over state-local owner pairs.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Best Result", ""])
    for key, value in payload["best_result"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Best Balanced Result", ""])
    for key, value in payload["best_balanced_result"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def write_outputs(repo_root: Path, payload: dict[str, Any]) -> None:
    (repo_root / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (repo_root / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    payload = build_probe()
    write_outputs(repo_root, payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
