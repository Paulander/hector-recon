#!/usr/bin/env python3
"""Build expanded replay-free state-local paired ownership inventory v1."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WORK_PACKAGE = Path("reports/krk_state_local_paired_ownership_work_package_v0.json")
OWNERSHIP = Path("reports/krk_ownership_selection_label_dataset_v5.json")
CONTEXT = Path("reports/krk_ownership_selection_context_dataset_v3.json")
CAPACITY_SOURCES = [
    Path("reports/krk_protected_provider_coverage_frames_v0.json"),
    Path("reports/krk_hard_negative_selector_target_dataset_v2.json"),
    Path("reports/krk_balanced_hard_negative_labels_v0.json"),
    Path("reports/krk_balanced_hard_negative_labels_v1.json"),
    Path("reports/krk_state_local_contrast_labels_v2.json"),
]
OUT_JSON = Path("reports/krk_state_local_paired_ownership_inventory_v1.json")
OUT_MD = Path("reports/krk_state_local_paired_ownership_inventory_v1.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _provider_family(provider_id: str | None) -> str:
    text = str(provider_id or "")
    if text == "krk.stage0_basin":
        return "stage0_basin"
    if text == "krk.drive_to_edge":
        return "drive_to_edge"
    if text == "krk.fence_established":
        return "fence_established"
    if text.startswith("krk.edge_trap"):
        return "edge_trap"
    if text.startswith("krk.box_shrink"):
        return "box_shrink"
    return "other"


def _selected_positive(row: dict[str, Any]) -> bool:
    return row.get("target_label") == "selected_owner_converted" or row.get("owner_positive") is True


def _capacity_positive(row: dict[str, Any]) -> bool:
    label = row.get("capacity_label") or row.get("contrast_label")
    result = row.get("forced_result") or row.get("result")
    return label in {"positive_capacity", "positive"} or result == "mate"


def _normalize_capacity_row(row: dict[str, Any], source_path: Path) -> dict[str, Any] | None:
    if row.get("stage7_challenge_row") or row.get("source_stage") == "stage7":
        return None
    provider_id = row.get("provider_id")
    state_id = row.get("state_id")
    if not provider_id or not state_id:
        return None
    has_capacity_signal = (
        row.get("capacity_label") is not None
        or row.get("contrast_label") is not None
        or row.get("forced_result") is not None
        or row.get("label_channel") in {"protected_missing_provider_capacity", "forced_provider_state_local_contrast"}
    )
    if not has_capacity_signal:
        return None
    positive = _capacity_positive(row)
    return {
        "state_id": str(state_id),
        "frame_id": row.get("frame_id"),
        "fen": row.get("fen"),
        "source_stage": row.get("source_stage"),
        "active_landmark_label": row.get("active_landmark_label")
        or row.get("source_active_landmark_label")
        or row.get("execution_landmark_label"),
        "provider_id": provider_id,
        "provider_family": row.get("provider_family") or _provider_family(str(provider_id)),
        "move_uci": row.get("forced_first_move") or row.get("move_uci"),
        "capacity_label": "positive_capacity" if positive else "negative_capacity",
        "forced_result": row.get("forced_result") or row.get("result"),
        "forced_plies": row.get("forced_plies") or row.get("plies"),
        "source_artifact": str(source_path),
        "source_label_channel": row.get("label_channel") or row.get("label_semantics"),
        "evidence_channel": "forced_capacity",
    }


def _capacity_index() -> dict[str, dict[str, dict[str, Any]]]:
    by_state: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    # Prefer direct outcome-bearing sources over derived datasets.
    source_priority = {str(path): index for index, path in enumerate(CAPACITY_SOURCES)}
    for path in CAPACITY_SOURCES:
        payload = _load(path)
        if not str(payload.get("causal_status") or "").startswith("non_causal"):
            raise ValueError(f"capacity source must remain non-causal: {path}")
        for raw in payload.get("rows") or payload.get("labels") or []:
            row = _normalize_capacity_row(raw, path)
            if row is None:
                continue
            state_id = row["state_id"]
            provider_id = row["provider_id"]
            existing = by_state[state_id].get(provider_id)
            if existing is None:
                by_state[state_id][provider_id] = row
                continue
            existing_positive = existing["capacity_label"] == "positive_capacity"
            row_positive = row["capacity_label"] == "positive_capacity"
            if row_positive != existing_positive:
                # Keep explicit failures over positives for risk visibility.
                if not row_positive:
                    by_state[state_id][provider_id] = row
                continue
            if source_priority.get(row["source_artifact"], 999) < source_priority.get(existing["source_artifact"], 999):
                by_state[state_id][provider_id] = row
    return by_state


def _context_index() -> dict[tuple[str, str], dict[str, Any]]:
    payload = _load(CONTEXT)
    if payload.get("causal_status") != "non_causal_context_feature_dataset":
        raise ValueError("context dataset must remain non-causal")
    return {
        (str(row.get("state_id")), str(row.get("provider_id"))): row
        for row in payload.get("rows") or []
        if row.get("source_stage") != "stage7"
    }


def _comparison_label(selected: dict[str, Any], capacity: dict[str, Any]) -> tuple[str, str]:
    selected_positive = _selected_positive(selected)
    capacity_positive = capacity.get("capacity_label") == "positive_capacity"
    if selected_positive and not capacity_positive:
        return "prefer_selected_owner", "strong_same_state_conflict"
    if not selected_positive and capacity_positive:
        return "prefer_capacity_alternative", "strong_same_state_conflict"
    if selected_positive and capacity_positive:
        return "equivalent_positive_or_preserve_selected", "safe_preservation"
    if not selected_positive and not capacity_positive:
        return "abstain_or_insufficient_safe_owner", "abstain_or_insufficient_safe_owner"
    return "insufficient_evidence", "weak_capacity_context"


def build_inventory() -> dict[str, Any]:
    work_package = _load(WORK_PACKAGE)
    ownership = _load(OWNERSHIP)
    if work_package.get("causal_status") != "non_causal_work_package":
        raise ValueError("work package must remain non-causal")
    if ownership.get("causal_status") != "non_causal_ownership_label_dataset":
        raise ValueError("ownership labels must remain non-causal")
    capacity_by_state = _capacity_index()
    contexts = _context_index()
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for selected in ownership.get("rows") or []:
        if selected.get("source_stage") == "stage7":
            continue
        state_id = str(selected.get("state_id"))
        selected_provider = str(selected.get("provider_id"))
        selected_context = contexts.get((state_id, selected_provider), {})
        for capacity in sorted(capacity_by_state.get(state_id, {}).values(), key=lambda item: item["provider_id"]):
            if capacity["provider_id"] == selected_provider:
                continue
            comparison_label, evidence_channel = _comparison_label(selected, capacity)
            key = (state_id, selected_provider, capacity["provider_id"], comparison_label)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "schema_version": "state_local_owner_pair.v1",
                    "causal_status": "non_causal_pair_label",
                    "objective_id": "krk.selector.state_local_paired_ownership.v0",
                    "state_id": state_id,
                    "frame_id": selected.get("frame_id") or capacity.get("frame_id"),
                    "fen": selected.get("fen") or capacity.get("fen") or selected_context.get("fen"),
                    "source_stage": selected.get("source_stage") or capacity.get("source_stage"),
                    "active_landmark_label": selected.get("active_landmark_label")
                    or capacity.get("active_landmark_label"),
                    "terminal_space_context": selected_context.get("terminal_space_context"),
                    "context_terms": selected_context.get("context_terms") or [],
                    "owner_a_role": "normal_selected_owner",
                    "owner_a": selected_provider,
                    "owner_a_family": selected.get("provider_family") or _provider_family(selected_provider),
                    "owner_a_move": selected.get("move_uci"),
                    "owner_a_outcome": selected.get("target_label"),
                    "owner_a_positive": _selected_positive(selected),
                    "owner_a_evidence_channel": "normal_selected_playout",
                    "owner_a_label_source": selected.get("label_source"),
                    "owner_b_role": "forced_capacity_alternative",
                    "owner_b": capacity["provider_id"],
                    "owner_b_family": capacity["provider_family"],
                    "owner_b_move": capacity.get("move_uci"),
                    "owner_b_outcome": capacity.get("capacity_label"),
                    "owner_b_positive": capacity.get("capacity_label") == "positive_capacity",
                    "owner_b_forced_result": capacity.get("forced_result"),
                    "owner_b_forced_plies": capacity.get("forced_plies"),
                    "owner_b_evidence_channel": capacity.get("evidence_channel"),
                    "owner_b_source_artifact": capacity.get("source_artifact"),
                    "comparison_label": comparison_label,
                    "evidence_channel": evidence_channel,
                    "pair_strength": (
                        "strong_same_state_conflict"
                        if evidence_channel == "strong_same_state_conflict"
                        else "weak_same_state_context"
                    ),
                    "selected_failure_with_alternative_success": (
                        comparison_label == "prefer_capacity_alternative"
                    ),
                    "safe_preservation_pair": evidence_channel == "safe_preservation",
                    "usable_for_offline_probe": True,
                    "usable_for_selector_training": False,
                    "training_block_reason": "paired inventory requires non-causal probe and review",
                    "stage7_training_row": False,
                }
            )
    rows = sorted(rows, key=lambda row: (row["state_id"], row["owner_a"], row["owner_b"], row["comparison_label"]))
    thresholds = work_package.get("thresholds") or {}
    summary = {
        "pair_count": len(rows),
        "state_count": len({row.get("state_id") for row in rows}),
        "comparison_label_counts": dict(Counter(str(row.get("comparison_label")) for row in rows)),
        "evidence_channel_counts": dict(Counter(str(row.get("evidence_channel")) for row in rows)),
        "pair_strength_counts": dict(Counter(str(row.get("pair_strength")) for row in rows)),
        "source_stage_counts": dict(Counter(str(row.get("source_stage")) for row in rows)),
        "owner_a_family_counts": dict(Counter(str(row.get("owner_a_family")) for row in rows)),
        "owner_b_family_counts": dict(Counter(str(row.get("owner_b_family")) for row in rows)),
        "same_state_conflict_pair_count": sum(1 for row in rows if row.get("evidence_channel") == "strong_same_state_conflict"),
        "selected_failure_with_alternative_success_count": sum(1 for row in rows if row.get("selected_failure_with_alternative_success")),
        "safe_preservation_pair_count": sum(1 for row in rows if row.get("safe_preservation_pair")),
        "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
        "selector_training_row_count": sum(1 for row in rows if row.get("usable_for_selector_training")),
    }
    readiness = {
        "protected_pair_count_met": summary["pair_count"] >= int(thresholds.get("protected_pair_count") or 30),
        "same_state_conflict_pair_count_met": summary["same_state_conflict_pair_count"] >= int(thresholds.get("same_state_conflict_pair_count") or 8),
        "selected_failure_with_alternative_success_count_met": summary["selected_failure_with_alternative_success_count"] >= int(thresholds.get("selected_failure_with_alternative_success_count") or 4),
        "safe_preservation_pair_count_met": summary["safe_preservation_pair_count"] >= int(thresholds.get("safe_preservation_pair_count") or 12),
        "stage7_training_rows_met": summary["stage7_row_count"] == int(thresholds.get("stage7_training_rows") or 0),
    }
    ready = all(readiness.values())
    payload = {
        "schema_version": "krk_state_local_paired_ownership_inventory.v1",
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
        "source_artifacts": [str(WORK_PACKAGE), str(OWNERSHIP), str(CONTEXT), *map(str, CAPACITY_SOURCES)],
        "summary": summary,
        "minimum_readiness": readiness,
        "rows": rows,
        "decision": {
            "status": "paired_inventory_ready_for_non_causal_probe" if ready else "paired_inventory_underpowered",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "recommended_next_step": (
                "probe_state_local_paired_ownership_objective"
                if ready
                else "review_or_run_one_bounded_same_state_conflict_expansion"
            ),
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
        raise ValueError("Stage 7 rows must remain excluded from readiness inventory")
    for row in payload.get("rows") or []:
        if row.get("causal_status") != "non_causal_pair_label":
            raise ValueError("pair rows must remain non-causal")
        if row.get("usable_for_selector_training") is not False:
            raise ValueError("pair rows must not be training rows")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK State-Local Paired Ownership Inventory v1",
        "",
        "Expanded replay-free non-causal inventory across selected-owner and forced-capacity artifacts.",
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
    (repo_root / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
