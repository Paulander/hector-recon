#!/usr/bin/env python3
"""Build replay-free state-local paired ownership inventory."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN = Path("reports/krk_state_local_paired_ownership_objective_plan_v0.json")
OWNERSHIP = Path("reports/krk_ownership_selection_label_dataset_v5.json")
CAPACITY = Path("reports/krk_protected_provider_coverage_frames_v0.json")
OUT_JSON = Path("reports/krk_state_local_paired_ownership_inventory_v0.json")
OUT_MD = Path("reports/krk_state_local_paired_ownership_inventory_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _is_positive_selected(row: dict[str, Any]) -> bool:
    return row.get("target_label") == "selected_owner_converted" or row.get("owner_positive") is True


def _is_positive_capacity(row: dict[str, Any]) -> bool:
    return row.get("capacity_label") == "positive_capacity" or row.get("forced_result") == "mate"


def _pair_label(selected: dict[str, Any], capacity: dict[str, Any]) -> str:
    selected_positive = _is_positive_selected(selected)
    capacity_positive = _is_positive_capacity(capacity)
    if selected_positive and not capacity_positive:
        return "prefer_selected_owner"
    if not selected_positive and capacity_positive:
        return "prefer_capacity_alternative"
    if selected_positive and capacity_positive:
        return "equivalent_positive_or_preserve_selected"
    if not selected_positive and not capacity_positive:
        return "abstain_or_insufficient_safe_owner"
    return "insufficient_evidence"


def build_inventory() -> dict[str, Any]:
    plan = _load(PLAN)
    ownership = _load(OWNERSHIP)
    capacity = _load(CAPACITY)
    if plan.get("causal_status") != "non_causal_design_plan":
        raise ValueError("paired objective plan must remain non-causal")
    if ownership.get("causal_status") != "non_causal_ownership_label_dataset":
        raise ValueError("ownership labels must remain non-causal")
    if capacity.get("causal_status") not in {
        "non_causal_capacity_frame_dataset",
        "non_causal_capacity_evidence_dataset",
    } and not str(capacity.get("causal_status") or "").startswith("non_causal"):
        raise ValueError("capacity frames must remain non-causal")

    capacity_by_state: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in capacity.get("rows") or []:
        if row.get("stage7_challenge_row") or row.get("source_stage") == "stage7":
            continue
        capacity_by_state[str(row.get("state_id") or "")].append(row)

    rows = []
    for selected in ownership.get("rows") or []:
        if selected.get("source_stage") == "stage7":
            continue
        state_id = str(selected.get("state_id") or "")
        for candidate in capacity_by_state.get(state_id, []):
            if candidate.get("provider_id") == selected.get("provider_id"):
                continue
            comparison_label = _pair_label(selected, candidate)
            rows.append(
                {
                    "schema_version": "state_local_owner_pair.v0",
                    "causal_status": "non_causal_pair_label",
                    "objective_id": "krk.selector.state_local_paired_ownership.v0",
                    "state_id": state_id,
                    "frame_id": selected.get("frame_id") or candidate.get("frame_id"),
                    "fen": selected.get("fen") or candidate.get("fen"),
                    "source_stage": selected.get("source_stage") or candidate.get("source_stage"),
                    "active_landmark_label": selected.get("active_landmark_label")
                    or candidate.get("active_landmark_label"),
                    "owner_a_role": "normal_selected_owner",
                    "owner_a": selected.get("provider_id"),
                    "owner_a_family": selected.get("provider_family"),
                    "owner_a_move": selected.get("move_uci"),
                    "owner_a_outcome": selected.get("target_label"),
                    "owner_a_evidence_channel": "normal_selected_playout",
                    "owner_b_role": "forced_capacity_alternative",
                    "owner_b": candidate.get("provider_id"),
                    "owner_b_family": candidate.get("provider_family"),
                    "owner_b_move": candidate.get("forced_first_move"),
                    "owner_b_outcome": candidate.get("capacity_label"),
                    "owner_b_forced_result": candidate.get("forced_result"),
                    "owner_b_evidence_channel": "forced_capacity",
                    "comparison_label": comparison_label,
                    "pair_strength": (
                        "strong_same_state_conflict"
                        if comparison_label
                        in {"prefer_selected_owner", "prefer_capacity_alternative"}
                        else "weak_same_state_context"
                    ),
                    "usable_for_offline_probe": True,
                    "usable_for_selector_training": False,
                    "training_block_reason": (
                        "paired ownership inventory requires non-causal benchmark and review"
                    ),
                    "stage7_training_row": False,
                }
            )

    summary = {
        "pair_count": len(rows),
        "state_count": len({row.get("state_id") for row in rows}),
        "comparison_label_counts": dict(Counter(str(row.get("comparison_label")) for row in rows)),
        "pair_strength_counts": dict(Counter(str(row.get("pair_strength")) for row in rows)),
        "source_stage_counts": dict(Counter(str(row.get("source_stage")) for row in rows)),
        "owner_a_family_counts": dict(Counter(str(row.get("owner_a_family")) for row in rows)),
        "owner_b_family_counts": dict(Counter(str(row.get("owner_b_family")) for row in rows)),
        "same_state_conflict_pair_count": sum(
            1 for row in rows if row.get("pair_strength") == "strong_same_state_conflict"
        ),
        "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
        "selector_training_row_count": sum(1 for row in rows if row.get("usable_for_selector_training")),
    }
    req = plan.get("minimum_benchmark_requirements") or {}
    readiness = {
        "protected_pair_count_met": summary["pair_count"] >= int(req.get("protected_pair_count") or 0),
        "same_state_conflict_pair_count_met": summary["same_state_conflict_pair_count"]
        >= int(req.get("same_state_conflict_pair_count") or 0),
        "stage7_training_rows_met": summary["stage7_row_count"] == int(req.get("stage7_training_rows") or 0),
    }
    payload = {
        "schema_version": "krk_state_local_paired_ownership_inventory.v0",
        "causal_status": "non_causal_pair_inventory",
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
        "source_artifacts": [str(PLAN), str(OWNERSHIP), str(CAPACITY)],
        "summary": summary,
        "minimum_readiness": readiness,
        "rows": rows,
        "decision": {
            "status": (
                "paired_inventory_ready_for_non_causal_probe"
                if readiness["protected_pair_count_met"]
                and readiness["same_state_conflict_pair_count_met"]
                and readiness["stage7_training_rows_met"]
                else "paired_inventory_underpowered"
            ),
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "recommended_next_step": "probe_state_local_paired_ownership_objective_if_ready",
        },
    }
    validate_inventory(payload)
    return payload


def validate_inventory(payload: dict[str, Any]) -> None:
    if payload.get("causal_status") != "non_causal_pair_inventory":
        raise ValueError("inventory must remain non-causal")
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
        "# KRK State-Local Paired Ownership Inventory v0",
        "",
        "Replay-free non-causal inventory of same-state selected-owner vs forced-capacity alternatives.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Minimum Readiness", ""])
    for key, value in payload["minimum_readiness"].items():
        lines.append(f"- `{key}`: `{value}`")
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
    payload = build_inventory()
    write_outputs(repo_root, payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
