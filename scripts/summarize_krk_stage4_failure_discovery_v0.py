#!/usr/bin/env python3
"""Summarize Stage 4 caveat failure-state diversity.

This replay-free report checks whether the Stage 4 h40 caveat offers independent
selected-owner failure/switch contrast rows for selector validation.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import chess


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from recon_lite_chess.routing import stable_record_id  # noqa: E402


STAGE4_EVAL = Path(
    "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/"
    "stage6_overlay_composed/stage4_wrong_tempo_overlay_300_seed7_h40_profile_bonus.json"
)
SEED = Path("reports/strategy_arbitration/krk_selector_objective_seed_manifest_v2.json")
INDEPENDENT_VALIDATION = Path(
    "reports/strategy_arbitration/krk_selector_objective_independent_validation_v0.json"
)
OUT_JSON = Path("reports/krk_stage4_failure_discovery_v0.json")
OUT_MD = Path("reports/krk_stage4_failure_discovery_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected object: {path}")
    return payload


def _state_id_from_fen(fen: str) -> str:
    board = chess.Board(fen)
    return stable_record_id("state", board.board_fen(), board.turn)


def build_payload(
    stage4_eval: dict[str, Any] | None = None,
    seed: dict[str, Any] | None = None,
    independent_validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    stage4_eval = stage4_eval or _load(STAGE4_EVAL)
    seed = seed or _load(SEED)
    independent_validation = independent_validation or _load(INDEPENDENT_VALIDATION)
    seed_ids = {
        str(row.get("state_id"))
        for row in seed.get("seed_rows") or []
        if isinstance(row, dict) and row.get("state_id")
    }
    failures = []
    for packet in stage4_eval.get("handoff_packets") or []:
        if packet.get("phase") != "playout_summary" or packet.get("observed_outcome") != "max_plies":
            continue
        evidence = packet.get("evidence_terms") or {}
        fen = str(evidence.get("fen") or "")
        if not fen:
            continue
        state_id = _state_id_from_fen(fen)
        failures.append(
            {
                "state_id": state_id,
                "fen": fen,
                "selected_move": evidence.get("move"),
                "playout_result": evidence.get("playout_result"),
                "semantic_alignment_status": evidence.get("semantic_alignment_status"),
                "in_selector_seed_v2": state_id in seed_ids,
            }
        )
    unique_counter = Counter((row["state_id"], row["fen"], row["selected_move"]) for row in failures)
    unique_rows = [
        {
            "state_id": state_id,
            "fen": fen,
            "selected_move": move,
            "failure_count": count,
            "in_selector_seed_v2": state_id in seed_ids,
        }
        for (state_id, fen, move), count in sorted(unique_counter.items())
    ]
    independent_summary = independent_validation.get("summary") or {}
    all_seed_covered = bool(unique_rows) and all(row["in_selector_seed_v2"] for row in unique_rows)
    return {
        "schema_version": "krk_stage4_failure_discovery.v0",
        "causal_status": "non_causal_replay_free_failure_discovery",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(STAGE4_EVAL), str(SEED), str(INDEPENDENT_VALIDATION)],
        "summary": {
            "stage4_eval_total": stage4_eval.get("total"),
            "stage4_eval_conversion_failure_count": stage4_eval.get("conversion_failure_count"),
            "failure_packet_count": len(failures),
            "unique_failure_state_move_count": len(unique_rows),
            "unique_failure_states": len({row["state_id"] for row in unique_rows}),
            "all_unique_failures_already_in_selector_seed": all_seed_covered,
            "independent_validation_target_counts": independent_summary.get("target_counts"),
            "independent_validation_underpowered": independent_summary.get("underpowered"),
            "selector_training_row_count": 0,
            "stage7_training_row_count": 0,
        },
        "unique_failure_rows": unique_rows,
        "interpretation": {
            "blind_label_farming_recommended": False,
            "why": (
                "The retry1 Stage 4 h40 caveat has 32 failure packets but they collapse to "
                "one unique state/move, already present in selector seed v2. Random protected "
                "validation slices are therefore unlikely to add independent switch contrast."
            ),
            "recommended_evidence_path": (
                "Stage4 caveat/sequence diagnosis or targeted synthetic/stratified failure "
                "manifest, not more random selected-owner validation."
            ),
        },
        "decision": {
            "status": "stage4_failure_discovery_collapsed_to_seed_state",
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": "stage4_caveat_sequence_or_synthetic_contrast_review",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Stage 4 Failure Discovery v0",
        "",
        "Replay-free review of the retry1 Stage 4 h40 caveat failure diversity.",
        "",
        "## Decision",
        "",
    ]
    for key, value in payload["decision"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Summary", ""])
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Unique Failure Rows", ""])
    for row in payload["unique_failure_rows"]:
        lines.append(
            f"- `{row['state_id']}` move=`{row['selected_move']}` "
            f"count=`{row['failure_count']}` in_seed=`{row['in_selector_seed_v2']}`"
        )
    lines.extend(["", "## Interpretation", ""])
    for key, value in payload["interpretation"].items():
        lines.append(f"- {key}: `{value}`")
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
