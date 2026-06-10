#!/usr/bin/env python3
"""Review the state-local paired ownership inventory and probe."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WORK_PACKAGE = Path("reports/krk_state_local_paired_ownership_work_package_v0.json")
INVENTORY = Path("reports/krk_state_local_paired_ownership_inventory_v1.json")
PROBE = Path("reports/krk_state_local_paired_ownership_probe_v0.json")
OUT_JSON = Path("reports/krk_state_local_paired_ownership_review_v0.json")
OUT_MD = Path("reports/krk_state_local_paired_ownership_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    work_package = _load(WORK_PACKAGE)
    inventory = _load(INVENTORY)
    probe = _load(PROBE)
    if work_package.get("causal_status") != "non_causal_work_package":
        raise ValueError("work package must remain non-causal")
    if inventory.get("causal_status") != "non_causal_pair_inventory":
        raise ValueError("inventory must remain non-causal")
    if probe.get("causal_status") != "non_causal_offline_probe":
        raise ValueError("probe must remain non-causal")
    readiness = inventory.get("minimum_readiness") or {}
    best = probe.get("best_balanced_result") or {}
    inventory_ready = all(bool(value) for value in readiness.values())
    prefer_capacity_recall = float(best.get("prefer_capacity_recall") or 0.0)
    selected_preservation_recall = float(best.get("selected_preservation_recall") or 0.0)
    safe_preservation_recall = float(best.get("safe_preservation_recall") or 0.0)
    strong_conflict_accuracy = float(best.get("strong_conflict_accuracy") or 0.0)

    if not inventory_ready:
        status = "paired_inventory_underpowered"
        next_step = "stop_or_run_one_reviewed_bounded_same_state_conflict_expansion"
    elif prefer_capacity_recall >= 0.7 and selected_preservation_recall >= 0.7 and safe_preservation_recall >= 0.8:
        status = "runtime_review_ready_but_not_authorized"
        next_step = "prepare_default_off_runtime_review_packet_only_if_explicitly_requested"
    elif strong_conflict_accuracy >= 0.8 and safe_preservation_recall < 0.8:
        status = "feature_model_insufficient"
        next_step = "design_stronger_safe_preservation_features_before_runtime"
    else:
        status = "label_semantics_still_ambiguous"
        next_step = "review_pair_label_semantics_before_more_data_or_runtime"

    payload = {
        "schema_version": "krk_state_local_paired_ownership_review.v0",
        "causal_status": "non_causal_architecture_review",
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
        "source_artifacts": [str(WORK_PACKAGE), str(INVENTORY), str(PROBE)],
        "summary": {
            "inventory_pair_count": (inventory.get("summary") or {}).get("pair_count"),
            "inventory_state_count": (inventory.get("summary") or {}).get("state_count"),
            "same_state_conflict_pair_count": (inventory.get("summary") or {}).get("same_state_conflict_pair_count"),
            "selected_failure_with_alternative_success_count": (inventory.get("summary") or {}).get("selected_failure_with_alternative_success_count"),
            "safe_preservation_pair_count": (inventory.get("summary") or {}).get("safe_preservation_pair_count"),
            "stage7_row_count": (inventory.get("summary") or {}).get("stage7_row_count"),
            "inventory_ready": inventory_ready,
            "best_balanced_objective": best.get("objective"),
            "prefer_capacity_recall": prefer_capacity_recall,
            "selected_preservation_recall": selected_preservation_recall,
            "safe_preservation_recall": safe_preservation_recall,
            "strong_conflict_accuracy": strong_conflict_accuracy,
        },
        "interpretation": [
            "Replay-free extraction now satisfies the pair-count and same-state-conflict thresholds, so no bounded h40 expansion was needed.",
            "The paired objective is better aligned with the architecture than global provider-row classification because it keeps selected ownership and forced capacity in separate channels.",
            "The current simple family/context feature model still over-selects capacity alternatives in safe-preservation cases; this blocks runtime work.",
            "The next improvement should target safe-preservation features or pair-specific feature interactions, not more blind label collection.",
        ],
        "decision": {
            "status": status,
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "recommended_next_step": next_step,
        },
        "blocked_next_steps": [
            "runtime_selector",
            "selector_training",
            "runtime_arbiter",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }
    validate_review(payload)
    return payload


def validate_review(payload: dict[str, Any]) -> None:
    if payload.get("causal_status") != "non_causal_architecture_review":
        raise ValueError("review must remain non-causal")
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


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK State-Local Paired Ownership Review v0",
        "",
        "Final non-causal review for the paired ownership work package.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Interpretation", ""])
    for item in payload["interpretation"]:
        lines.append(f"- {item}")
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
    payload = build_review()
    write_outputs(repo_root, payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
