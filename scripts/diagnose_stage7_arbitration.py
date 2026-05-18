#!/usr/bin/env python3
"""Diagnose Stage 7 provider arbitration without changing behavior.

This consumes the family-split Stage 7 diagnosis and compares normal routing
against forced-provider candidates. The output is evidence for the Plasticity
Balance Protocol: it distinguishes a missing/wired adapter from a provider score
scale problem that should be handled by bounded calibration rather than a new
topology patch.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import chess

sys.path.insert(0, str(Path(__file__).resolve().parent))

from recon_lite.engine import ReConEngine

from test_krk_landmark_progress import (
    build_graph_from_topology,
    choose_move_details,
    stable_record_id,
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _parse_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _load_forced_probe_results(path: Path | None) -> dict[str, dict[str, dict[str, Any]]]:
    if path is None:
        return {}
    payload = _load_json(path)
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for record in payload.get("records") or []:
        if not isinstance(record, dict):
            continue
        state_id = str(record.get("state_id") or "")
        if not state_id:
            continue
        provider_results: dict[str, dict[str, Any]] = {}
        for probe in record.get("playout_probes") or []:
            if not isinstance(probe, dict):
                continue
            provider = str(probe.get("provider") or "")
            if not provider:
                continue
            current = provider_results.get(provider)
            candidate = {
                "result": probe.get("result"),
                "plies": probe.get("plies"),
                "first_move": probe.get("first_move"),
                "horizon": probe.get("horizon"),
                "source": str(path),
            }
            if current is None:
                provider_results[provider] = candidate
                continue
            current_mate = current.get("result") == "mate"
            candidate_mate = candidate.get("result") == "mate"
            if candidate_mate and not current_mate:
                provider_results[provider] = candidate
                continue
            if candidate_mate == current_mate:
                current_plies = int(current.get("plies", 999999) or 999999)
                candidate_plies = int(candidate.get("plies", 999999) or 999999)
                if candidate_plies < current_plies:
                    provider_results[provider] = candidate
        out[state_id] = provider_results
    return out


def _canonical_skill_id(label: str | None, stage: Any = None) -> str:
    if label:
        raw = str(label)
        if raw.startswith("krk."):
            return raw
        normalized = "".join(ch if ch.isalnum() else "_" for ch in raw.lower()).strip("_")
        return f"krk.{normalized or 'unknown'}"
    return f"krk.stage_{stage}" if stage is not None else "krk.unknown"


def _skill_id_for_suggestion(item: dict[str, Any]) -> str:
    meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
    return _canonical_skill_id(
        meta.get("skill_id")
        or meta.get("curriculum_label")
        or item.get("skill_id")
        or item.get("curriculum_label"),
        meta.get("stage") or item.get("stage"),
    )


def _move_uci(item: dict[str, Any]) -> str | None:
    move = item.get("move")
    if move is None:
        return None
    return move.uci() if hasattr(move, "uci") else str(move)


def _compact_suggestion(item: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
    adapter = meta.get("visible_role_provider_support_adapter")
    visible_licenses = meta.get("visible_role_licenses")
    return {
        "move": _move_uci(item),
        "skill_id": _skill_id_for_suggestion(item),
        "score": float(item.get("score", 0.0) or 0.0),
        "actuator": item.get("actuator"),
        "curriculum_label": meta.get("curriculum_label") or item.get("curriculum_label"),
        "stage": meta.get("stage") or item.get("stage"),
        "raw_score_before_role_bonus": meta.get("raw_score_before_role_bonus"),
        "visible_affordance_bonus": meta.get("visible_affordance_bonus"),
        "visible_role_license_bonus": meta.get("visible_role_license_bonus"),
        "role_bonus_total": meta.get("role_bonus_total"),
        "explicit_role_provider_move_shape_support_bonus": meta.get(
            "explicit_role_provider_move_shape_support_bonus"
        ),
        "visible_role_provider_support_adapter": dict(adapter) if isinstance(adapter, dict) else {},
        "visible_role_licenses": list(visible_licenses) if isinstance(visible_licenses, list) else [],
    }


def _best_by_skill(suggestions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    for item in suggestions:
        skill = _skill_id_for_suggestion(item)
        current = best.get(skill)
        if current is None or float(item.get("score", 0.0) or 0.0) > float(
            current.get("score", 0.0) or 0.0
        ):
            best[skill] = item
    return best


def _families(diagnosis: dict[str, Any], state_ids: tuple[str, ...]) -> list[dict[str, Any]]:
    allowed = set(state_ids)
    records = list(diagnosis.get("families") or diagnosis.get("unique_failed_post_reply_states") or [])
    out: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict) or not record.get("post_reply_fen"):
            continue
        try:
            board = chess.Board(str(record["post_reply_fen"]))
            state_id = record.get("state_id") or stable_record_id("state", board.board_fen(), chess.WHITE)
        except Exception:
            continue
        if allowed and str(state_id) not in allowed:
            continue
        item = dict(record)
        item["state_id"] = str(state_id)
        out.append(item)
    return out


def _choose(
    graph,
    engine: ReConEngine,
    board: chess.Board,
    *,
    max_ticks: int,
    suggestion_limit: int,
    forced_successor_skill: str | None,
    enable_explicit_support: bool,
) -> dict[str, Any]:
    return choose_move_details(
        graph,
        engine,
        board,
        max_ticks=max_ticks,
        suggestion_limit=suggestion_limit,
        successor_affordance_layer_enabled=True,
        successor_role_license_enabled=True,
        successor_role_scoped_move_shape_enabled=True,
        explicit_role_provider_support_enabled=enable_explicit_support,
        forced_successor_skill=forced_successor_skill,
        early_stop_stable_suggestions=2,
        enable_diagnostic_caches=True,
    )


def diagnose_stage7_arbitration(
    *,
    family_diagnosis_path: Path,
    topology_path: Path,
    providers: tuple[str, ...],
    forced_probe_path: Path | None = None,
    state_ids: tuple[str, ...] = (),
    max_ticks: int = 40,
    suggestion_limit: int = 200,
) -> dict[str, Any]:
    diagnosis = _load_json(family_diagnosis_path)
    forced_probe_results = _load_forced_probe_results(forced_probe_path)
    graph = build_graph_from_topology(topology_path)
    engine = ReConEngine(graph)
    records: list[dict[str, Any]] = []

    for family in _families(diagnosis, state_ids):
        board = chess.Board(str(family["post_reply_fen"]))
        normal = _choose(
            graph,
            engine,
            board,
            max_ticks=max_ticks,
            suggestion_limit=suggestion_limit,
            forced_successor_skill=None,
            enable_explicit_support=True,
        )
        normal_suggestions = list(normal.get("suggestions") or [])
        normal_best = _compact_suggestion(normal_suggestions[0] if normal_suggestions else None)
        normal_best_score = float(normal_best.get("score", 0.0) if normal_best else 0.0)
        normal_best_skill = str(normal_best.get("skill_id") if normal_best else "krk.none")
        normal_best_by_skill = _best_by_skill(normal_suggestions)

        provider_rows: list[dict[str, Any]] = []
        for provider in providers:
            forced = _choose(
                graph,
                engine,
                board,
                max_ticks=max_ticks,
                suggestion_limit=max(10, suggestion_limit),
                forced_successor_skill=provider,
                enable_explicit_support=True,
            )
            forced_suggestions = list(forced.get("suggestions") or [])
            forced_best = _compact_suggestion(forced_suggestions[0] if forced_suggestions else None)
            normal_provider_best = _compact_suggestion(normal_best_by_skill.get(provider))
            forced_score = float(forced_best.get("score", 0.0) if forced_best else 0.0)
            support = (
                forced_best.get("visible_role_provider_support_adapter", {})
                if isinstance(forced_best, dict)
                else {}
            )
            support_amount = float(support.get("support_amount", 0.0) or 0.0)
            score_gap = max(0.0, normal_best_score - forced_score)
            required_to_overtake = score_gap + 1e-6 if normal_best_skill != provider else 0.0
            forced_provider_result = (
                family.get("forced_provider_results", {}).get(provider, {})
                if isinstance(family.get("forced_provider_results"), dict)
                else {}
            )
            if not forced_provider_result:
                forced_provider_result = forced_probe_results.get(str(family.get("state_id")), {}).get(provider, {})
            row = {
                "provider": provider,
                "forced_successor_available": bool(forced.get("forced_successor_available")),
                "forced_best": forced_best,
                "normal_provider_best": normal_provider_best,
                "forced_known_outcome": forced_provider_result.get("result"),
                "forced_known_plies": forced_provider_result.get("plies"),
                "score_gap_to_selected": score_gap,
                "required_support_to_overtake_selected": required_to_overtake,
                "adapter_support_amount": support_amount,
                "adapter_support_ratio_to_required": (
                    support_amount / required_to_overtake if required_to_overtake > 0 else None
                ),
                "adapter_fired_under_forced_provider": bool(support.get("enabled")),
                "diagnosis": _provider_diagnosis(
                    selected_skill=normal_best_skill,
                    provider=provider,
                    forced_best=forced_best,
                    forced_known_outcome=forced_provider_result.get("result"),
                    adapter_fired=bool(support.get("enabled")),
                    support_amount=support_amount,
                    required_to_overtake=required_to_overtake,
                ),
            }
            provider_rows.append(row)

        records.append({
            "state_id": family.get("state_id"),
            "family_id": family.get("family_id"),
            "post_reply_fen": family.get("post_reply_fen"),
            "source_selected_successor": family.get("selected_successor"),
            "source_selected_move": family.get("selected_move"),
            "source_conversion_result": family.get("conversion_result"),
            "normal_selected": normal_best,
            "normal_top_suggestions": [
                _compact_suggestion(item) for item in normal_suggestions[:10]
            ],
            "provider_arbitration": provider_rows,
        })

    counts: dict[str, int] = {}
    for record in records:
        for row in record["provider_arbitration"]:
            for label in row.get("diagnosis", []):
                counts[str(label)] = counts.get(str(label), 0) + 1

    return {
        "schema_version": "stage7_arbitration_diagnosis.v1",
        "causal_status": "non_causal",
        "family_diagnosis_source": str(family_diagnosis_path),
        "forced_probe_source": str(forced_probe_path) if forced_probe_path is not None else None,
        "topology": str(topology_path),
        "providers": list(providers),
        "state_ids": list(state_ids),
        "record_count": len(records),
        "diagnosis_counts": counts,
        "candidate_update": _candidate_update(counts),
        "records": records,
    }


def _provider_diagnosis(
    *,
    selected_skill: str,
    provider: str,
    forced_best: dict[str, Any] | None,
    forced_known_outcome: Any,
    adapter_fired: bool,
    support_amount: float,
    required_to_overtake: float,
) -> list[str]:
    labels: list[str] = []
    if selected_skill != provider:
        labels.append("selected_provider_differs_from_forced_candidate")
    if forced_known_outcome == "mate":
        labels.append("forced_provider_can_convert")
    if adapter_fired:
        labels.append("adapter_wired_and_visible_under_forced_provider")
    else:
        labels.append("adapter_not_visible_for_forced_provider")
    if forced_best and required_to_overtake > 0:
        if support_amount > 0 and required_to_overtake > support_amount * 10:
            labels.append("provider_score_scale_mismatch")
        elif support_amount > 0:
            labels.append("candidate_local_support_may_be_sufficient")
        else:
            labels.append("no_candidate_support_available")
    return labels


def _candidate_update(counts: dict[str, int]) -> dict[str, Any]:
    if counts.get("provider_score_scale_mismatch", 0):
        status = "needs_weight_or_score_normalization_probe"
        diagnosis = [
            "forced_provider_can_convert",
            "adapter_wired",
            "visible_support_too_small_relative_to_provider_score_gap",
        ]
        next_action = "run_bounded_candidate_local_calibration_or_score_scale_audit_before_new_topology"
    elif counts.get("adapter_not_visible_for_forced_provider", 0):
        status = "needs_visible_term_refinement"
        diagnosis = ["adapter_not_visible_for_forced_provider"]
        next_action = "refine_adapter_terms_before_calibration"
    else:
        status = "needs_more_samples"
        diagnosis = ["arbitration_not_decisive"]
        next_action = "collect_more_family_arbitration_examples"
    return {
        "candidate_id": "cand.krk.box_shrink.stage0_fallback_arbitration.v1",
        "candidate_type": "weight_vs_topology_arbitration_diagnosis",
        "status": status,
        "diagnosis": diagnosis,
        "causal_status": "non_causal",
        "promotion_status": "proposed",
        "next_action": next_action,
        "hard_blocks": [
            "do_not_promote_stage7",
            "do_not_train_stage8",
            "do_not_add_broad_stage0_penalty",
            "do_not_make_handoff_packets_or_candidates_causal",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose Stage 7 arbitration")
    parser.add_argument("--family-diagnosis", type=Path, required=True)
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--providers", default="krk.drive_to_edge")
    parser.add_argument("--forced-probe", type=Path, default=None)
    parser.add_argument("--state-ids", default="")
    parser.add_argument("--max-ticks", type=int, default=40)
    parser.add_argument("--suggestion-limit", type=int, default=200)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = diagnose_stage7_arbitration(
        family_diagnosis_path=args.family_diagnosis,
        topology_path=args.topology,
        providers=_parse_csv(args.providers),
        forced_probe_path=args.forced_probe,
        state_ids=_parse_csv(args.state_ids),
        max_ticks=args.max_ticks,
        suggestion_limit=args.suggestion_limit,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
