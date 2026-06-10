#!/usr/bin/env python3
"""Build a replay-free dataset for selected Stage 7 path targets."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TARGET_SPEC = Path("reports/structural_candidates/stage7_selected_path_target_spec_v0.json")
ABSTENTION_CONTEXT_DATASET = Path("reports/krk_abstention_context_feature_dataset_v0.json")
STATE_LOCAL_CONTRAST = Path("reports/krk_state_local_contrast_labels_v2.json")
OUT_JSON = Path("reports/structural_candidates/stage7_selected_path_target_dataset_v0.json")
OUT_MD = Path("reports/structural_candidates/stage7_selected_path_target_dataset_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _provider_family(provider_id: str | None) -> str | None:
    if not provider_id:
        return None
    if "stage0" in provider_id:
        return "stage0_basin"
    if "drive" in provider_id:
        return "drive_to_edge"
    if "fence" in provider_id:
        return "fence_established"
    if "edge_trap" in provider_id:
        return "edge_trap"
    return provider_id.split(".")[-1]


def _safe_owner_controls(rows: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    controls = []
    for row in rows:
        if row.get("source_stage") not in {"stage5", "stage6", "stage4"}:
            continue
        if row.get("label") != "safe_owner" or row.get("frame_outcome") != "mate":
            continue
        controls.append({
            "schema_version": "stage7_selected_path_target_row.v0",
            "target_id": "stage7.selected_path.strategy_ownership_gap.v0",
            "row_role": "protected_safe_owner_control",
            "state_id": row.get("state_id"),
            "source_stage": row.get("source_stage"),
            "active_landmark_label": row.get("active_landmark_label"),
            "selected_provider": row.get("provider_id"),
            "selected_provider_family": row.get("provider_family"),
            "selected_move": row.get("move_uci"),
            "target_provider": row.get("provider_id"),
            "outcome": row.get("frame_outcome"),
            "label": "selected_owner_safe",
            "features": {
                "provider_family": row.get("provider_family"),
                "monitor_signature": (row.get("monitor_context") or {}).get("monitor_signature"),
                "white_king_support_bucket": (row.get("terminal_space_context") or {}).get("white_king_support_bucket"),
                "source_stage": row.get("source_stage"),
            },
            "causal_status": "non_causal_replay_free_label",
        })
        if len(controls) >= limit:
            break
    return controls


def _ownership_positive_rows(target_spec: dict[str, Any]) -> list[dict[str, Any]]:
    spec = next(
        target for target in target_spec.get("target_specs") or []
        if target.get("target_id") == "stage7.selected_path.strategy_ownership_gap.v0"
    )
    rows = []
    for state in spec.get("states") or []:
        rows.append({
            "schema_version": "stage7_selected_path_target_row.v0",
            "target_id": spec["target_id"],
            "row_role": "stage7_selected_owner_failed_positive",
            "state_id": state.get("state_id"),
            "source_stage": "stage7",
            "active_landmark_label": "box_shrink",
            "selected_provider": state.get("selected_provider"),
            "selected_provider_family": _provider_family(state.get("selected_provider")),
            "selected_move": state.get("selected_move"),
            "target_provider": state.get("target_provider"),
            "target_provider_family": _provider_family(state.get("target_provider")),
            "outcome": "max_plies",
            "label": state.get("recommended_label"),
            "features": {
                "local_provider_competition_failed": True,
                "selected_owner_failed_h40": True,
                "alternative_provider_known_conversion_h40": True,
                "source_stage": "stage7",
            },
            "causal_status": "non_causal_replay_free_label",
        })
    return rows


def _sequence_gap_rows(target_spec: dict[str, Any]) -> list[dict[str, Any]]:
    spec = next(
        target for target in target_spec.get("target_specs") or []
        if target.get("target_id") == "stage7.selected_path.sequence_continuation_gap.v0"
    )
    rows = []
    for state in spec.get("states") or []:
        rows.append({
            "schema_version": "stage7_selected_path_target_row.v0",
            "target_id": spec["target_id"],
            "row_role": "stage7_sequence_gap_unresolved",
            "state_id": state.get("state_id"),
            "source_stage": "stage7",
            "active_landmark_label": "box_shrink",
            "selected_provider": state.get("selected_provider"),
            "selected_provider_family": _provider_family(state.get("selected_provider")),
            "selected_move": state.get("selected_move"),
            "target_provider": None,
            "outcome": "max_plies",
            "label": state.get("recommended_label"),
            "features": {
                "post_plan_stagnation": True,
                "forced_providers_h40_no_mate": True,
                "legal_first_h40_no_mate": True,
                "source_stage": "stage7",
            },
            "causal_status": "non_causal_replay_free_label",
        })
    return rows


def _sequence_controls(contrast_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    controls = []
    for row in contrast_rows:
        if row.get("source_stage") == "stage7" and row.get("frame_outcome") == "mate":
            controls.append({
                "schema_version": "stage7_selected_path_target_row.v0",
                "target_id": "stage7.selected_path.sequence_continuation_gap.v0",
                "row_role": "stage7_sequence_success_control",
                "state_id": row.get("state_id"),
                "source_stage": row.get("source_stage"),
                "active_landmark_label": row.get("active_landmark_label"),
                "selected_provider": row.get("provider_id"),
                "selected_provider_family": row.get("provider_family"),
                "selected_move": row.get("move_uci"),
                "target_provider": row.get("provider_id"),
                "outcome": row.get("frame_outcome"),
                "label": "sequence_continuation_success",
                "features": {
                    "provider_family": row.get("provider_family"),
                    "provider_local_rank": row.get("provider_local_rank"),
                    "source_stage": row.get("source_stage"),
                },
                "causal_status": "non_causal_replay_free_label",
            })
    return controls


def build_dataset() -> dict[str, Any]:
    spec = _load(TARGET_SPEC)
    abstention_rows = _load(ABSTENTION_CONTEXT_DATASET).get("rows") or []
    contrast_rows = _load(STATE_LOCAL_CONTRAST).get("rows") or []
    rows = (
        _ownership_positive_rows(spec)
        + _safe_owner_controls(abstention_rows)
        + _sequence_gap_rows(spec)
        + _sequence_controls(contrast_rows)
    )
    target_counts = Counter(row["target_id"] for row in rows)
    role_counts = Counter(row["row_role"] for row in rows)
    stage_counts = Counter(row["source_stage"] for row in rows)
    sequence_success_controls = role_counts.get("stage7_sequence_success_control", 0)
    ownership_positive_count = role_counts.get("stage7_selected_owner_failed_positive", 0)
    protected_safe_controls = role_counts.get("protected_safe_owner_control", 0)
    sequence_gap_count = role_counts.get("stage7_sequence_gap_unresolved", 0)
    ownership_trainable = ownership_positive_count >= 2 and protected_safe_controls >= 8
    sequence_trainable = sequence_gap_count >= 2 and sequence_success_controls >= 2
    return {
        "schema_version": "stage7_selected_path_target_dataset.v0",
        "causal_status": "non_causal_replay_free_dataset",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "hidden_python_controller": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(TARGET_SPEC), str(ABSTENTION_CONTEXT_DATASET), str(STATE_LOCAL_CONTRAST)],
        "rows": rows,
        "summary": {
            "row_count": len(rows),
            "target_counts": dict(target_counts),
            "row_role_counts": dict(role_counts),
            "stage_counts": dict(stage_counts),
            "ownership_target_minimally_trainable": ownership_trainable,
            "sequence_target_minimally_trainable": sequence_trainable,
            "benchmark_underpowered": not (ownership_trainable and sequence_trainable),
        },
        "decision": {
            "status": (
                "ownership_target_minimal_sequence_target_underpowered"
                if ownership_trainable and not sequence_trainable
                else "selected_path_dataset_underpowered"
            ),
            "recommended_next_step": (
                "collect_or_recover_successful_post_box_sequence_controls_before_sequence_policy_runtime_work"
                if not sequence_trainable
                else "run_non_causal_split_target_probe"
            ),
            "blocked_runtime_work": [
                "runtime arbiter",
                "abstention penalty tuning",
                "Stage 7 promotion",
                "Stage 8 training",
                "causal internal terminals",
            ],
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 Selected Path Target Dataset v0",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        "Replay-free dataset assembled from existing target specs, abstention context labels, and state-local contrast labels.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend([
        "",
        "## Interpretation",
        "",
        "The strategy-ownership target has a minimal positive/control split, but only two Stage 7 positive states. The sequence/continuation target has unresolved negative/gap states but no replay-free successful Stage 7 sequence controls in this dataset.",
        "",
        f"Recommended next step: `{payload['decision']['recommended_next_step']}`",
        "",
        "Blocked runtime work:",
        "",
    ])
    for item in payload["decision"]["blocked_runtime_work"]:
        lines.append(f"- `{item}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_dataset()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
