#!/usr/bin/env python3
"""Probe safer KRK state-local paired ownership models non-causally."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = Path("reports/krk_state_local_paired_ownership_inventory_v1.json")
ERROR_AUDIT = Path("reports/krk_state_local_paired_ownership_error_audit_v0.json")
OUT_JSON = Path("reports/krk_state_local_paired_ownership_probe_v1.json")
OUT_MD = Path("reports/krk_state_local_paired_ownership_probe_v1.md")


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


def target_prefer_capacity(row: dict[str, Any]) -> bool:
    return row.get("comparison_label") == "prefer_capacity_alternative"


def safe_preservation_gate_predict(row: dict[str, Any]) -> bool:
    """Outcome-semantics gate: only prefer capacity when selected owner failed and alternative converted."""
    return row.get("owner_a_positive") is False and row.get("owner_b_positive") is True


def conflict_only_predict(row: dict[str, Any]) -> bool:
    """Only strong selected-fail/alternative-success conflicts request capacity preference."""
    return (
        row.get("evidence_channel") == "strong_same_state_conflict"
        and row.get("owner_a_positive") is False
        and row.get("owner_b_positive") is True
    )


def _score(train: list[dict[str, Any]], row: dict[str, Any], keys: tuple[str, ...]) -> float:
    global_rate = (
        sum(1 for item in train if target_prefer_capacity(item)) / len(train)
        if train
        else 0.5
    )
    counts: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    for item in train:
        counts[_feature_key(item, keys)]["prefer_capacity" if target_prefer_capacity(item) else "preserve_selected"] += 1
    counter = counts.get(_feature_key(row, keys))
    if not counter:
        return global_rate
    total = counter["prefer_capacity"] + counter["preserve_selected"]
    return counter["prefer_capacity"] / total if total else global_rate


def _prediction_metrics(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    tp = sum(1 for item in predictions if item["predicted_prefer_capacity"] and item["target_prefer_capacity"])
    fp = sum(1 for item in predictions if item["predicted_prefer_capacity"] and not item["target_prefer_capacity"])
    tn = sum(1 for item in predictions if not item["predicted_prefer_capacity"] and not item["target_prefer_capacity"])
    fn = sum(1 for item in predictions if not item["predicted_prefer_capacity"] and item["target_prefer_capacity"])
    total = len(predictions)
    strong = [item for item in predictions if item["evidence_channel"] == "strong_same_state_conflict"]
    safe = [item for item in predictions if item["evidence_channel"] == "safe_preservation"]
    return {
        "row_count": total,
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
        "safe_preservation_false_positive_count": sum(
            1 for item in safe if item["predicted_prefer_capacity"]
        ),
        "prefer_capacity_false_negative_count": fn,
        "predictions": predictions,
    }


def _rule_metrics(
    rows: list[dict[str, Any]],
    model_id: str,
    predict: Callable[[dict[str, Any]], bool],
    *,
    runtime_feature_eligible: bool,
    notes: str,
) -> dict[str, Any]:
    predictions = []
    for row in rows:
        predicted = predict(row)
        predictions.append(
            {
                "state_id": row.get("state_id"),
                "source_stage": row.get("source_stage"),
                "owner_a": row.get("owner_a"),
                "owner_b": row.get("owner_b"),
                "comparison_label": row.get("comparison_label"),
                "evidence_channel": row.get("evidence_channel"),
                "predicted_prefer_capacity": predicted,
                "target_prefer_capacity": target_prefer_capacity(row),
                "model_id": model_id,
            }
        )
    return {
        "model_id": model_id,
        "model_kind": "semantic_rule",
        "runtime_feature_eligible": runtime_feature_eligible,
        "notes": notes,
        **_prediction_metrics(predictions),
    }


def _statistical_metrics(
    rows: list[dict[str, Any]],
    model_id: str,
    keys: tuple[str, ...],
    threshold: float,
) -> dict[str, Any]:
    predictions = []
    for state_id in sorted({str(row.get("state_id")) for row in rows}):
        train = [row for row in rows if str(row.get("state_id")) != state_id]
        test = [row for row in rows if str(row.get("state_id")) == state_id]
        for row in test:
            score = _score(train, row, keys)
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
                    "feature_key": list(_feature_key(row, keys)),
                    "predicted_prefer_capacity": score >= threshold,
                    "target_prefer_capacity": target_prefer_capacity(row),
                    "model_id": model_id,
                }
            )
    return {
        "model_id": model_id,
        "model_kind": "leave_state_out_feature_model",
        "runtime_feature_eligible": True,
        "features": list(keys),
        "threshold": threshold,
        **_prediction_metrics(predictions),
    }


def _passes_thresholds(result: dict[str, Any]) -> bool:
    return (
        (result.get("prefer_capacity_recall") or 0.0) >= 0.70
        and (result.get("selected_preservation_recall") or 0.0) >= 0.70
        and (result.get("safe_preservation_recall") or 0.0) >= 0.80
        and (result.get("strong_conflict_accuracy") or 0.0) >= 0.80
    )


def build_probe() -> dict[str, Any]:
    inventory = _load(INVENTORY)
    audit = _load(ERROR_AUDIT)
    if inventory.get("causal_status") != "non_causal_pair_inventory":
        raise ValueError("inventory must remain non-causal")
    if audit.get("causal_status") != "non_causal_error_audit":
        raise ValueError("error audit must remain non-causal")
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

    results: dict[str, dict[str, Any]] = {}
    results["baseline_owner_family_pair@0.25"] = _statistical_metrics(
        rows,
        "baseline_owner_family_pair@0.25",
        ("owner_a_family", "owner_b_family"),
        0.25,
    )
    results["pair_interaction_stage_landmark@0.25"] = _statistical_metrics(
        rows,
        "pair_interaction_stage_landmark@0.25",
        ("source_stage", "active_landmark_label", "owner_a_family", "owner_b_family"),
        0.25,
    )
    results["context_augmented_pair@0.25"] = _statistical_metrics(
        rows,
        "context_augmented_pair@0.25",
        (
            "owner_a_family",
            "owner_b_family",
            "ctx:terminal_space_context.black_king_edge_bucket",
            "ctx:terminal_space_context.white_king_support_bucket",
        ),
        0.25,
    )
    results["safe_preservation_gated_model"] = _rule_metrics(
        rows,
        "safe_preservation_gated_model",
        safe_preservation_gate_predict,
        runtime_feature_eligible=False,
        notes=(
            "Uses offline owner_a/owner_b outcome semantics; validates objective semantics "
            "but is not directly runtime-feature eligible."
        ),
    )
    results["conflict_only_model"] = _rule_metrics(
        rows,
        "conflict_only_model",
        conflict_only_predict,
        runtime_feature_eligible=False,
        notes=(
            "Uses evidence-channel/outcome labels to prefer capacity only for selected-fail "
            "plus alternative-success conflicts."
        ),
    )

    threshold_passing = {
        name: result for name, result in results.items() if _passes_thresholds(result)
    }
    runtime_feature_passing = {
        name: result
        for name, result in threshold_passing.items()
        if result.get("runtime_feature_eligible") is True
    }
    best_name, best = max(
        results.items(),
        key=lambda item: (
            _passes_thresholds(item[1]),
            item[1].get("safe_preservation_recall") or 0.0,
            item[1].get("prefer_capacity_recall") or 0.0,
            item[1].get("selected_preservation_recall") or 0.0,
            item[1].get("strong_conflict_accuracy") or 0.0,
        ),
    )
    status = (
        "runtime_feature_model_review_ready"
        if runtime_feature_passing
        else "semantic_gate_review_ready_runtime_feature_translation_needed"
        if threshold_passing
        else "paired_objective_feature_model_insufficient"
    )
    payload = {
        "schema_version": "krk_state_local_paired_ownership_probe.v1",
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
        "source_artifacts": [str(INVENTORY), str(ERROR_AUDIT)],
        "summary": {
            "row_count": len(rows),
            "state_count": len({row.get("state_id") for row in rows}),
            "prefer_capacity_count": sum(1 for row in rows if target_prefer_capacity(row)),
            "preserve_selected_count": sum(1 for row in rows if not target_prefer_capacity(row)),
            "safe_preservation_pair_count": sum(1 for row in rows if row.get("evidence_channel") == "safe_preservation"),
            "strong_conflict_pair_count": sum(1 for row in rows if row.get("evidence_channel") == "strong_same_state_conflict"),
            "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
            "threshold_passing_model_count": len(threshold_passing),
            "runtime_feature_passing_model_count": len(runtime_feature_passing),
        },
        "results": results,
        "best_result": {"objective": best_name, **{key: value for key, value in best.items() if key != "predictions"}},
        "threshold_passing_models": {
            name: {key: value for key, value in result.items() if key != "predictions"}
            for name, result in threshold_passing.items()
        },
        "runtime_feature_passing_models": {
            name: {key: value for key, value in result.items() if key != "predictions"}
            for name, result in runtime_feature_passing.items()
        },
        "decision": {
            "status": status,
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "recommended_next_step": (
                "prepare_runtime_review_packet_for_explicit_approval"
                if threshold_passing
                else "write_paired_ownership_blocker_review"
            ),
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
        "# KRK State-Local Paired Ownership Probe v1",
        "",
        "Non-causal comparison of safer paired-ownership models.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Best Result", ""])
    for key, value in payload["best_result"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Threshold-Passing Models", ""])
    for name, result in payload["threshold_passing_models"].items():
        lines.append(
            f"- `{name}`: prefer_capacity_recall=`{result.get('prefer_capacity_recall')}`, "
            f"selected_preservation_recall=`{result.get('selected_preservation_recall')}`, "
            f"safe_preservation_recall=`{result.get('safe_preservation_recall')}`, "
            f"runtime_feature_eligible=`{result.get('runtime_feature_eligible')}`"
        )
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
