#!/usr/bin/env python3
"""Build a unified non-causal KRK sequence-control contrast dataset v0.

The dataset folds together current Stage 4 first-move contrast evidence,
protected Stage 4/5/6 ownership-seed evidence, and held-out Stage 7 clean
sequence controls. It is not a training set and does not authorize runtime
selection; it exists to make the remaining KRK control-plane gaps explicit.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STAGE4_STRATIFIED = ROOT / "reports/krk_stage4_stratified_contrast_validation_v0.json"
SELECTOR_SEED = ROOT / "reports/strategy_arbitration/krk_selector_objective_seed_manifest_v2.json"
STAGE7_CLEAN = ROOT / "reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json"
STAGE4_PACKET = ROOT / "reports/krk_stage4_first_move_contrast_runtime_review_packet_v0.json"
OUTPUT_JSON = ROOT / "reports/strategy_arbitration/krk_sequence_control_contrast_dataset_v0.json"
OUTPUT_MD = ROOT / "reports/strategy_arbitration/krk_sequence_control_contrast_dataset_v0.md"

SCHEMA_VERSION = "krk_sequence_control_contrast_dataset.v0"


COMMON_FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "runtime_selector_implemented": False,
    "runtime_score_changes": False,
    "runtime_direct_routing": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _stage4_rows(stage4: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for variant in stage4.get("variants", []):
        for row in variant.get("rows", []):
            rows.append({
                "schema_version": "krk_sequence_control_contrast_row.v0",
                "row_id": f"stage4.{variant['variant_id']}.{row['first_move']}",
                "row_type": "forced_first_move_candidate",
                "source_stage": "stage4",
                "source_family": "edge_trap_wrong_tempo",
                "source_artifact": "reports/krk_stage4_stratified_contrast_validation_v0.json",
                "state_id": f"stage4.{variant['variant_id']}",
                "fen": row["fen"],
                "move_uci": row["first_move"],
                "selected_analog": bool(row.get("selected_analog", False)),
                "result": row["result"],
                "target_label": "conversion_positive" if row["result"] == "mate" else "conversion_failure",
                "evidence_channel": "symmetry_stratified_forced_first_move_capacity",
                "features": dict(row.get("canonical_features") or {}),
                "stage7_heldout_challenge": False,
                "usable_for_selector_training": False,
                "usable_for_runtime_authorization": False,
                "causal_status": "non_causal_contrast_evidence",
            })
    return rows


def _selector_rows(seed: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in seed.get("seed_rows", []):
        rows.append({
            "schema_version": "krk_sequence_control_contrast_row.v0",
            "row_id": f"selector_seed.{row.get('state_id')}",
            "row_type": "ownership_seed_context",
            "source_stage": row.get("source_stage"),
            "source_family": row.get("selected_provider_family"),
            "source_artifact": "reports/strategy_arbitration/krk_selector_objective_seed_manifest_v2.json",
            "state_id": row.get("state_id"),
            "fen": row.get("fen"),
            "move_uci": None,
            "selected_provider": row.get("selected_provider"),
            "selected_owner_label": row.get("selected_owner_label"),
            "target_label": row.get("objective_channel"),
            "evidence_channel": "selected_owner_seed_context_not_training",
            "positive_trace_provider_candidate_count": int(
                row.get("positive_trace_provider_candidate_count", 0) or 0
            ),
            "stage7_heldout_challenge": False,
            "usable_for_selector_training": False,
            "usable_for_runtime_authorization": False,
            "causal_status": "non_causal_context_evidence",
        })
    return rows


def _stage7_rows(stage7: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in stage7.get("controls", []):
        rows.append({
            "schema_version": "krk_sequence_control_contrast_row.v0",
            "row_id": f"stage7.{row.get('state_id')}",
            "row_type": "stage7_clean_sequence_control",
            "source_stage": "stage7",
            "source_family": row.get("selected_provider"),
            "source_artifact": row.get("source_artifact"),
            "state_id": row.get("state_id"),
            "fen": row.get("fen"),
            "move_uci": row.get("move_uci"),
            "selected_provider": row.get("selected_provider"),
            "result": row.get("result"),
            "target_label": "conversion_positive" if row.get("result") == "mate" else "conversion_failure",
            "control_role": row.get("control_role"),
            "evidence_channel": "heldout_stage7_clean_sequence_control",
            "stage7_heldout_challenge": True,
            "usable_for_selector_training": False,
            "usable_for_runtime_authorization": False,
            "causal_status": "non_causal_heldout_challenge_evidence",
        })
    return rows


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "row_count": len(rows),
        "row_type_counts": dict(Counter(str(row.get("row_type")) for row in rows)),
        "source_stage_counts": dict(Counter(str(row.get("source_stage")) for row in rows)),
        "target_label_counts": dict(Counter(str(row.get("target_label")) for row in rows)),
        "stage7_heldout_row_count": sum(1 for row in rows if row.get("stage7_heldout_challenge")),
        "selector_training_row_count": sum(1 for row in rows if row.get("usable_for_selector_training")),
        "runtime_authorization_row_count": sum(
            1 for row in rows if row.get("usable_for_runtime_authorization")
        ),
    }


def build_payload(
    *,
    stage4: dict[str, Any] | None = None,
    seed: dict[str, Any] | None = None,
    stage7: dict[str, Any] | None = None,
    packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    stage4 = stage4 or _load(STAGE4_STRATIFIED)
    seed = seed or _load(SELECTOR_SEED)
    stage7 = stage7 or _load(STAGE7_CLEAN)
    packet = packet or _load(STAGE4_PACKET)
    rows = _stage4_rows(stage4) + _selector_rows(seed) + _stage7_rows(stage7)
    summary = _summarize(rows)
    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_sequence_control_contrast_dataset",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/krk_stage4_stratified_contrast_validation_v0.json",
            "reports/strategy_arbitration/krk_selector_objective_seed_manifest_v2.json",
            "reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json",
            "reports/krk_stage4_first_move_contrast_runtime_review_packet_v0.json",
        ],
        "summary": summary,
        "stage4_review_gate": {
            "status": packet.get("decision", {}).get("status"),
            "runtime_review_ready": bool(packet.get("decision", {}).get("runtime_review_ready")),
            "implementation_authorized_by_packet": bool(
                packet.get("decision", {}).get("implementation_authorized_by_this_packet")
            ),
        },
        "label_semantics": {
            "forced_first_move_capacity_is_not_runtime_ownership": True,
            "stage7_rows_are_heldout_challenge_only": True,
            "selector_seed_rows_are_context_evidence_not_training_rows": True,
        },
        "rows": rows,
        "decision": {
            "status": "krk_sequence_control_contrast_dataset_ready_non_causal",
            "runtime_changes_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# KRK Sequence-Control Contrast Dataset v0",
        "",
        "Status: `krk_sequence_control_contrast_dataset_ready_non_causal`",
        "",
        "## Summary",
        "",
        f"- row_count: `{summary['row_count']}`",
        f"- row_type_counts: `{summary['row_type_counts']}`",
        f"- source_stage_counts: `{summary['source_stage_counts']}`",
        f"- target_label_counts: `{summary['target_label_counts']}`",
        f"- stage7_heldout_row_count: `{summary['stage7_heldout_row_count']}`",
        f"- selector_training_row_count: `{summary['selector_training_row_count']}`",
        f"- runtime_authorization_row_count: `{summary['runtime_authorization_row_count']}`",
        "",
        "## Semantics",
        "",
        "- Forced-first-move capacity is not runtime ownership.",
        "- Stage 7 rows are held-out challenge evidence only.",
        "- Selector seed rows are context evidence, not training rows.",
        "- The Stage 4 runtime review packet is ready but not implementation-authorizing.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(json.dumps({
        "decision": payload["decision"]["status"],
        "row_count": payload["summary"]["row_count"],
        "row_type_counts": payload["summary"]["row_type_counts"],
    }, indent=2))


if __name__ == "__main__":
    main()
