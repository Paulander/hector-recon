#!/usr/bin/env python3
"""Diagnose Stage 7 move-shape separation after family adapter failure.

Provider-level support can be too broad: it may correctly support a provider
family in one state while boosting the wrong first-move shape elsewhere. This
script compares forced-success first moves against adapter-supported max-plies
moves and emits non-causal move-shape candidate records.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import chess

sys.path.insert(0, str(Path(__file__).resolve().parent))

from recon_lite_chess.krk_baseline_nodes import krk_move_shape_audit


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _terms(audit: dict[str, Any] | None, key: str) -> set[str]:
    if not isinstance(audit, dict):
        return set()
    values = audit.get(key)
    if not isinstance(values, list):
        return set()
    return {str(item) for item in values}


def _audit_from_fen_move(fen: str | None, move_uci: str | None) -> dict[str, Any] | None:
    if not fen or not move_uci:
        return None
    try:
        board = chess.Board(str(fen))
        move = chess.Move.from_uci(str(move_uci))
        if move not in board.legal_moves:
            return None
        return krk_move_shape_audit(board, move, include_worst_reply=False)
    except Exception:
        return None


def _forced_success_examples(family_diagnosis: dict[str, Any], provider: str) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for family in family_diagnosis.get("families") or []:
        if not isinstance(family, dict):
            continue
        result = family.get("forced_provider_results", {}).get(provider, {})
        if not isinstance(result, dict) or result.get("result") != "mate":
            continue
        first_probe = result.get("first_move_probe")
        if not isinstance(first_probe, dict):
            continue
        audit = {
            "current_terms": first_probe.get("current_terms") or [],
            "move_shape_terms": first_probe.get("move_shape_terms") or [],
            "post_move_terms": first_probe.get("post_move_terms") or [],
            "worst_reply_terms": first_probe.get("worst_reply_terms") or [],
        }
        examples.append({
            "state_id": family.get("state_id"),
            "family_id": family.get("family_id"),
            "provider": provider,
            "move": result.get("first_move"),
            "plies": result.get("plies"),
            "result": "mate",
            "move_shape_audit": audit,
        })
    return examples


def _adapter_supported_failures(adapter_diagnostic: dict[str, Any], provider: str) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for packet in adapter_diagnostic.get("handoff_packets") or []:
        if not isinstance(packet, dict):
            continue
        evidence = packet.get("evidence_terms")
        if not isinstance(evidence, dict):
            continue
        if evidence.get("playout_result") == "mate":
            continue
        provider_counts = evidence.get("adapter_supported_provider_counts")
        move_counts = evidence.get("adapter_supported_move_counts")
        if not isinstance(provider_counts, dict) or not provider_counts.get(provider):
            continue
        if not isinstance(move_counts, dict):
            continue
        fen = evidence.get("fen")
        for move_uci, count in move_counts.items():
            audit = _audit_from_fen_move(str(fen) if fen else None, str(move_uci))
            examples.append({
                "packet_id": packet.get("packet_id"),
                "provider": provider,
                "fen": fen,
                "move": str(move_uci),
                "count": int(count or 0),
                "result": evidence.get("playout_result") or packet.get("observed_outcome"),
                "selected_successor": evidence.get("successor_selected_skill"),
                "selected_move": evidence.get("move"),
                "move_shape_audit": audit,
            })
    return examples


def _common(examples: list[dict[str, Any]], key: str) -> set[str]:
    sets = [_terms(item.get("move_shape_audit"), key) for item in examples if item.get("move_shape_audit")]
    if not sets:
        return set()
    acc = set(sets[0])
    for item in sets[1:]:
        acc &= item
    return acc


def _counts(examples: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for item in examples:
        counter.update(_terms(item.get("move_shape_audit"), key))
    return dict(counter)


def diagnose_move_shape_separation(
    *,
    family_diagnosis_path: Path,
    adapter_diagnostic_path: Path,
    provider: str,
) -> dict[str, Any]:
    family_diagnosis = _load_json(family_diagnosis_path)
    adapter_diagnostic = _load_json(adapter_diagnostic_path)
    positive = _forced_success_examples(family_diagnosis, provider)
    negative = _adapter_supported_failures(adapter_diagnostic, provider)

    splits: dict[str, Any] = {}
    separating_terms: dict[str, list[str]] = {}
    for key in ("current_terms", "move_shape_terms", "post_move_terms", "worst_reply_terms"):
        pos_common = _common(positive, key)
        neg_common = _common(negative, key)
        pos_counts = _counts(positive, key)
        neg_counts = _counts(negative, key)
        split_terms = sorted(
            term for term in pos_common
            if neg_counts.get(term, 0) == 0
        )
        splits[key] = {
            "positive_common": sorted(pos_common),
            "negative_common": sorted(neg_common),
            "positive_counts": pos_counts,
            "negative_counts": neg_counts,
            "positive_common_absent_from_negative": split_terms,
        }
        if split_terms:
            separating_terms[key] = split_terms

    move_shape_terms = separating_terms.get("move_shape_terms", [])
    post_terms = separating_terms.get("post_move_terms", [])
    if move_shape_terms:
        status = "move_shape_gate_candidate"
        next_action = "compile_only_after_move_shape_level_support_exists"
        diagnosis = [
            "provider_level_support_overbroad",
            "forced_success_move_shape_separates_from_adapter_supported_failures",
        ]
    else:
        status = "needs_more_move_shape_terms"
        next_action = "collect_more_examples_or_add_continuation_oracle"
        diagnosis = [
            "provider_level_support_overbroad",
            "move_shape_terms_do_not_yet_separate",
        ]

    candidate_id = (
        f"cand.krk.box_shrink.{provider.removeprefix('krk.').replace('.', '_')}"
        ".move_shape_gate.v1"
    )
    return {
        "schema_version": "stage7_move_shape_separation.v1",
        "causal_status": "non_causal",
        "family_diagnosis_source": str(family_diagnosis_path),
        "adapter_diagnostic_source": str(adapter_diagnostic_path),
        "provider": provider,
        "positive_example_count": len(positive),
        "negative_example_count": len(negative),
        "positive_examples": positive,
        "negative_examples": negative,
        "term_splits": splits,
        "candidate_update": {
            "candidate_id": candidate_id,
            "candidate_type": "move_shape_level_support_gate",
            "target_provider": provider,
            "status": status,
            "diagnosis": diagnosis,
            "required_move_shape_terms": move_shape_terms,
            "required_post_move_terms": post_terms,
            "causal_status": "non_causal",
            "promotion_status": "proposed",
            "next_action": next_action,
            "hard_blocks": [
                "do_not_increase_provider_level_bonus",
                "do_not_run_m3_on_provider_adapter",
                "do_not_promote_stage7",
                "do_not_train_stage8",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose Stage 7 move-shape separation")
    parser.add_argument("--family-diagnosis", type=Path, required=True)
    parser.add_argument("--adapter-diagnostic", type=Path, required=True)
    parser.add_argument("--provider", default="krk.drive_to_edge")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = diagnose_move_shape_separation(
        family_diagnosis_path=args.family_diagnosis,
        adapter_diagnostic_path=args.adapter_diagnostic,
        provider=args.provider,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
