#!/usr/bin/env python3
"""Diagnose visible support-term separability for Stage 7 family adapters.

This is non-causal. It asks whether a forced-success provider/family can be
separated from non-converting families using currently available visible terms.
It considers current-state, move-shape, and post-move terms from the provider's
forced first-move probe.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path
from typing import Any

import chess

sys.path.insert(0, str(Path(__file__).resolve().parent))

from recon_lite_chess.krk_baseline_nodes import krk_move_shape_audit


TERM_KEYS = ("current_terms", "move_shape_terms", "post_move_terms", "worst_reply_terms")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _probe(family: dict[str, Any], provider: str) -> dict[str, Any]:
    cached = family.setdefault("_recomputed_probe_cache", {})
    if provider in cached:
        return cached[provider]
    result = family.get("forced_provider_results", {}).get(provider, {})
    if not isinstance(result, dict):
        cached[provider] = {}
        return cached[provider]
    fen = family.get("post_reply_fen")
    first_move = result.get("first_move")
    if fen and first_move:
        try:
            board = chess.Board(str(fen))
            move = chess.Move.from_uci(str(first_move))
            if move in board.legal_moves:
                cached[provider] = krk_move_shape_audit(
                    board,
                    move,
                    include_worst_reply=False,
                )
                return cached[provider]
        except Exception:
            pass
    cached[provider] = result.get("first_move_probe", {}) if isinstance(
        result.get("first_move_probe"), dict
    ) else {}
    return cached[provider]


def _terms(family: dict[str, Any], provider: str, key: str) -> set[str]:
    probe = _probe(family, provider)
    values = probe.get(key)
    if not isinstance(values, list):
        return set()
    return {str(item) for item in values}


def _provider_result(family: dict[str, Any], provider: str) -> str:
    payload = family.get("forced_provider_results", {}).get(provider, {})
    if not isinstance(payload, dict):
        return "missing"
    if payload.get("result") == "mate" or payload.get("h80_result") == "mate":
        return "mate"
    return str(payload.get("h80_result") or payload.get("result") or "unknown")


def _all_terms(family: dict[str, Any], provider: str) -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    for key in TERM_KEYS:
        out.update((key, term) for term in _terms(family, provider, key))
    return out


def _matches(family: dict[str, Any], provider: str, combo: tuple[tuple[str, str], ...]) -> bool:
    for key, term in combo:
        if term not in _terms(family, provider, key):
            return False
    return True


def _combo_payload(combo: tuple[tuple[str, str], ...]) -> dict[str, list[str]]:
    payload = {key: [] for key in TERM_KEYS}
    for key, term in combo:
        payload[key].append(term)
    return {key: sorted(values) for key, values in payload.items() if values}


def _find_separating_combos(
    *,
    target: dict[str, Any],
    provider: str,
    families: list[dict[str, Any]],
    max_terms: int,
    limit: int,
) -> list[dict[str, Any]]:
    target_terms = sorted(_all_terms(target, provider))
    combos: list[dict[str, Any]] = []
    for size in range(1, max_terms + 1):
        for combo in itertools.combinations(target_terms, size):
            false_positive_families = []
            for family in families:
                if family.get("state_id") == target.get("state_id"):
                    continue
                if not _matches(family, provider, combo):
                    continue
                if _provider_result(family, provider) != "mate":
                    false_positive_families.append(str(family.get("state_id")))
            if false_positive_families:
                continue
            combos.append({
                "term_count": size,
                "terms_by_kind": _combo_payload(combo),
                "combo": [f"{key}:{term}" for key, term in combo],
            })
            if len(combos) >= limit:
                return combos
        if combos:
            return combos
    return combos


def diagnose_support_term_separation(
    *,
    family_diagnosis_path: Path,
    target_state_id: str,
    provider: str,
    max_terms: int = 3,
    limit: int = 10,
) -> dict[str, Any]:
    family_diagnosis = _load_json(family_diagnosis_path)
    families = [item for item in family_diagnosis.get("families") or [] if isinstance(item, dict)]
    target = next((item for item in families if item.get("state_id") == target_state_id), None)
    if target is None:
        raise ValueError(f"target state not found: {target_state_id}")
    result = _provider_result(target, provider)
    combos = _find_separating_combos(
        target=target,
        provider=provider,
        families=families,
        max_terms=max_terms,
        limit=limit,
    )
    false_positive_by_kind: dict[str, list[str]] = {}
    for key in TERM_KEYS:
        target_key_terms = _terms(target, provider, key)
        if not target_key_terms:
            continue
        fps = []
        for family in families:
            if family.get("state_id") == target_state_id:
                continue
            if _provider_result(family, provider) == "mate":
                continue
            if target_key_terms <= _terms(family, provider, key):
                fps.append(str(family.get("state_id")))
        false_positive_by_kind[key] = fps
    if combos:
        status = "separable_with_existing_visible_terms"
        next_action = "compile_move_shape_gated_support_adapter_in_sandbox"
    else:
        status = "not_separable_with_existing_visible_terms"
        next_action = "add_or_audit_missing_geometry_terms_before_adapter_compilation"
    return {
        "schema_version": "stage7_support_term_separation.v1",
        "causal_status": "non_causal",
        "family_diagnosis_source": str(family_diagnosis_path),
        "target_state_id": target_state_id,
        "provider": provider,
        "provider_result": result,
        "target_first_move": (
            target.get("forced_provider_results", {}).get(provider, {}).get("first_move")
        ),
        "target_terms_by_kind": {
            key: sorted(_terms(target, provider, key))
            for key in TERM_KEYS
        },
        "false_positive_families_by_kind": false_positive_by_kind,
        "separating_combos": combos,
        "candidate_update": {
            "candidate_id": (
                "cand.krk.box_shrink."
                f"{target_state_id.removeprefix('state.')}.{provider.removeprefix('krk.')}"
                ".visible_support_terms.v1"
            ),
            "candidate_type": "visible_support_term_separation",
            "target_provider": provider,
            "status": status,
            "causal_status": "non_causal",
            "promotion_status": "proposed",
            "next_action": next_action,
            "suggested_missing_term_families": (
                [
                    "king_opposition_geometry",
                    "rook_cut_axis_relative_to_kings",
                    "post_move_black_escape_count_delta",
                    "post_move_fence_repair_durability",
                ]
                if not combos else []
            ),
            "hard_blocks": [
                "do_not_compile_adapter_without_separating_visible_terms",
                "do_not_promote_stage7",
                "do_not_train_stage8",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose Stage 7 support-term separation")
    parser.add_argument("--family-diagnosis", type=Path, required=True)
    parser.add_argument("--target-state-id", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--max-terms", type=int, default=3)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = diagnose_support_term_separation(
        family_diagnosis_path=args.family_diagnosis,
        target_state_id=args.target_state_id,
        provider=args.provider,
        max_terms=args.max_terms,
        limit=args.limit,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
