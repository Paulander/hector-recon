#!/usr/bin/env python3
"""Audit errors in the KRK state-local paired ownership probe."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = Path("reports/krk_state_local_paired_ownership_inventory_v1.json")
PROBE = Path("reports/krk_state_local_paired_ownership_probe_v0.json")
OUT_JSON = Path("reports/krk_state_local_paired_ownership_error_audit_v0.json")
OUT_MD = Path("reports/krk_state_local_paired_ownership_error_audit_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _row_index(inventory: dict[str, Any]) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    index = {}
    for row in inventory.get("rows") or []:
        key = (
            str(row.get("state_id")),
            str(row.get("owner_a")),
            str(row.get("owner_b")),
            str(row.get("comparison_label")),
        )
        index[key] = row
    return index


def _key(prediction: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(prediction.get("state_id")),
        str(prediction.get("owner_a")),
        str(prediction.get("owner_b")),
        str(prediction.get("comparison_label")),
    )


def _error_record(prediction: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    terminal = row.get("terminal_space_context") or {}
    return {
        "state_id": prediction.get("state_id"),
        "source_stage": row.get("source_stage"),
        "active_landmark_label": row.get("active_landmark_label"),
        "comparison_label": row.get("comparison_label"),
        "evidence_channel": row.get("evidence_channel"),
        "owner_a": row.get("owner_a"),
        "owner_a_family": row.get("owner_a_family"),
        "owner_a_move": row.get("owner_a_move"),
        "owner_a_outcome": row.get("owner_a_outcome"),
        "owner_a_positive": row.get("owner_a_positive"),
        "owner_a_label_source": row.get("owner_a_label_source"),
        "owner_b": row.get("owner_b"),
        "owner_b_family": row.get("owner_b_family"),
        "owner_b_move": row.get("owner_b_move"),
        "owner_b_outcome": row.get("owner_b_outcome"),
        "owner_b_positive": row.get("owner_b_positive"),
        "owner_b_forced_result": row.get("owner_b_forced_result"),
        "owner_b_source_artifact": row.get("owner_b_source_artifact"),
        "feature_key": prediction.get("feature_key"),
        "score": prediction.get("score"),
        "threshold": prediction.get("threshold"),
        "predicted_prefer_capacity": prediction.get("predicted_prefer_capacity"),
        "target_prefer_capacity": prediction.get("target_prefer_capacity"),
        "terminal_context": {
            "black_king_edge_bucket": terminal.get("black_king_edge_bucket"),
            "white_king_support_bucket": terminal.get("white_king_support_bucket"),
            "box_area_relevance": terminal.get("box_area_relevance"),
            "rook_safe_proxy": terminal.get("rook_safe_proxy"),
        },
    }


def build_audit() -> dict[str, Any]:
    inventory = _load(INVENTORY)
    probe = _load(PROBE)
    if inventory.get("causal_status") != "non_causal_pair_inventory":
        raise ValueError("inventory must remain non-causal")
    if probe.get("causal_status") != "non_causal_offline_probe":
        raise ValueError("probe must remain non-causal")
    objective = (probe.get("best_balanced_result") or {}).get("objective")
    result = (probe.get("results") or {}).get(objective) or {}
    rows = _row_index(inventory)
    false_positives = []
    false_negatives = []
    for prediction in result.get("predictions") or []:
        row = rows.get(_key(prediction))
        if not row:
            continue
        predicted = bool(prediction.get("predicted_prefer_capacity"))
        target = bool(prediction.get("target_prefer_capacity"))
        if predicted and not target:
            false_positives.append(_error_record(prediction, row))
        elif target and not predicted:
            false_negatives.append(_error_record(prediction, row))

    fp_by_channel = Counter(str(item.get("evidence_channel")) for item in false_positives)
    fp_by_families = Counter(
        f"{item.get('owner_a_family')}->{item.get('owner_b_family')}" for item in false_positives
    )
    fn_by_families = Counter(
        f"{item.get('owner_a_family')}->{item.get('owner_b_family')}" for item in false_negatives
    )
    fp_by_stage = Counter(str(item.get("source_stage")) for item in false_positives)
    grouped_feature_keys: dict[str, int] = defaultdict(int)
    for item in false_positives:
        grouped_feature_keys[str(item.get("feature_key"))] += 1

    payload = {
        "schema_version": "krk_state_local_paired_ownership_error_audit.v0",
        "causal_status": "non_causal_error_audit",
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
        "source_artifacts": [str(INVENTORY), str(PROBE)],
        "audited_objective": objective,
        "summary": {
            "false_positive_count": len(false_positives),
            "false_negative_count": len(false_negatives),
            "false_positive_by_evidence_channel": dict(sorted(fp_by_channel.items())),
            "false_positive_by_family_pair": dict(sorted(fp_by_families.items())),
            "false_negative_by_family_pair": dict(sorted(fn_by_families.items())),
            "false_positive_by_stage": dict(sorted(fp_by_stage.items())),
            "false_positive_feature_key_counts": dict(sorted(grouped_feature_keys.items())),
            "stage7_row_count": sum(
                1 for item in [*false_positives, *false_negatives] if item.get("source_stage") == "stage7"
            ),
        },
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "candidate_safe_preservation_features": [
            "owner_a_positive",
            "owner_a_evidence_channel=normal_selected_playout",
            "owner_b_evidence_channel=forced_capacity",
            "owner_b_positive",
            "comparison_semantics:selected_mate_plus_forced_mate_preserve_selected",
            "do_not_switch_from_selected_mate_to_forced_capacity_without_selected_failure",
        ],
        "decision": {
            "status": "safe_preservation_false_positives_are_outcome_semantics_errors",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "recommended_next_step": "probe_safe_preservation_gated_pair_models",
        },
    }
    validate_payload(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("causal_status") != "non_causal_error_audit":
        raise ValueError("audit must remain non-causal")
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
        raise ValueError("Stage 7 rows must remain excluded from this audit")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK State-Local Paired Ownership Error Audit v0",
        "",
        "Non-causal audit of paired ownership probe errors.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Interpretation", ""])
    lines.append(
        "- Safe-preservation false positives are mostly cases where normal selected ownership already converted and the alternative is only forced-capacity evidence."
    )
    lines.append(
        "- This supports a semantic gate: do not prefer a forced-capacity alternative over a selected owner that already converted unless the selected owner failed in the same state/context."
    )
    lines.extend(["", "## Candidate Features", ""])
    for item in payload["candidate_safe_preservation_features"]:
        lines.append(f"- `{item}`")
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
    payload = build_audit()
    write_outputs(repo_root, payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
