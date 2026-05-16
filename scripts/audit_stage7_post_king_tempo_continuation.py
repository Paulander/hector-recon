#!/usr/bin/env python3
"""Audit Stage 7 continuation after the king-tempo sandbox provider fires.

This is a non-causal Growth Lab diagnostic. It consumes an existing Stage 7
diagnostic artifact, groups unique post-king-tempo continuation families, and
optionally replays those families at bounded horizons. The output is a
StructuralCandidate update, not a runtime rule.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import chess

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from recon_lite.engine import ReConEngine  # noqa: E402
from recon_lite_chess.graph.builder import build_graph_from_topology  # noqa: E402
from recon_lite_chess.krk_baseline_nodes import (  # noqa: E402
    _compute_krk_context_terms,
    _stage7_king_tempo_move_audit,
    krk_move_shape_audit,
)
from test_krk_landmark_progress import play_to_mate  # noqa: E402


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _skill_id_from_suggestion(suggestion: dict[str, Any] | None) -> str | None:
    if not isinstance(suggestion, dict):
        return None
    meta = suggestion.get("meta") or {}
    if not isinstance(meta, dict):
        meta = {}
    skill = (
        suggestion.get("skill_id")
        or meta.get("skill_id")
        or suggestion.get("curriculum_label")
        or meta.get("curriculum_label")
    )
    if not skill:
        return None
    skill = str(skill)
    return skill if skill.startswith("krk.") else f"krk.{skill}"


def _selected_skill_from_engine(engine: dict[str, Any] | None, move: str | None) -> str | None:
    if not isinstance(engine, dict) or not move:
        return None
    for suggestion in engine.get("suggestions") or []:
        if isinstance(suggestion, dict) and suggestion.get("move") == move:
            return _skill_id_from_suggestion(suggestion)
    suggestions = engine.get("suggestions") or []
    if suggestions and isinstance(suggestions[0], dict):
        return _skill_id_from_suggestion(suggestions[0])
    return None


def _first_white_event(result: dict[str, Any]) -> dict[str, Any] | None:
    for event in result.get("trace") or []:
        if isinstance(event, dict) and event.get("turn") == "white":
            return event
    return None


def _active_terms(mapping: dict[str, Any]) -> list[str]:
    return sorted(str(key) for key, value in mapping.items() if bool(value))


def _post_tempo_record(*, post_reply_fen: str, tempo_move: str) -> dict[str, Any]:
    board = chess.Board(post_reply_fen)
    move = chess.Move.from_uci(tempo_move)
    shape = krk_move_shape_audit(board, move, {}, include_worst_reply=True)
    tempo = _stage7_king_tempo_move_audit(board, move)
    post = board.copy(stack=False)
    post.push(move)
    post_context = _compute_krk_context_terms(post)
    current_metrics = shape.get("current_metrics") or {}
    post_metrics = shape.get("post_move_metrics") or {}
    return {
        "post_reply_fen": post_reply_fen,
        "tempo_move": tempo_move,
        "post_tempo_fen": post.fen(),
        "stage7_king_tempo_audit": tempo,
        "move_shape_terms": list(shape.get("move_shape_terms") or []),
        "post_move_terms": list(shape.get("post_move_terms") or []),
        "worst_reply_terms": list(shape.get("worst_reply_terms") or []),
        "post_tempo_context_terms": _active_terms(post_context),
        "metrics": {
            "current_box_area": current_metrics.get("box_area"),
            "post_box_area": post_metrics.get("box_area"),
            "current_enemy_edge_distance": current_metrics.get("enemy_edge_distance"),
            "post_enemy_edge_distance": post_metrics.get("enemy_edge_distance"),
            "current_enemy_corner_distance": current_metrics.get("enemy_corner_distance"),
            "post_enemy_corner_distance": post_metrics.get("enemy_corner_distance"),
            "current_white_king_enemy_distance": current_metrics.get("white_king_enemy_distance"),
            "post_white_king_enemy_distance": post_metrics.get("white_king_enemy_distance"),
        },
    }


def extract_king_tempo_records(diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for packet in diagnostic.get("handoff_packets") or []:
        if not isinstance(packet, dict) or packet.get("phase") != "post_opponent_reply":
            continue
        evidence = packet.get("evidence_terms") or {}
        if not isinstance(evidence, dict):
            continue
        license_payload = evidence.get("visible_stage7_king_tempo_license")
        if not isinstance(license_payload, dict) or not license_payload:
            continue
        post_reply_fen = evidence.get("post_reply_fen")
        tempo_move = license_payload.get("move")
        if not post_reply_fen or not tempo_move:
            continue
        record = {
            "sample_fen": evidence.get("fen"),
            "box_shrink_move": evidence.get("move"),
            "black_reply": evidence.get("black_reply"),
            "playout_result": evidence.get("playout_result"),
            "plies": evidence.get("plies"),
            "failure_classes": list(evidence.get("failure_classes") or []),
            "selected_successor": evidence.get("successor_selected_skill"),
            "visible_stage7_king_tempo_license": license_payload,
            **_post_tempo_record(
                post_reply_fen=str(post_reply_fen),
                tempo_move=str(tempo_move),
            ),
        }
        records.append(record)
    return records


def group_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[(str(record["post_reply_fen"]), str(record["tempo_move"]))].append(record)

    families: list[dict[str, Any]] = []
    for index, ((post_reply_fen, tempo_move), items) in enumerate(sorted(grouped.items()), start=1):
        prototype = items[0]
        outcomes = Counter(str(item.get("playout_result")) for item in items)
        failure_classes = Counter(
            failure_class
            for item in items
            for failure_class in item.get("failure_classes", [])
        )
        families.append({
            "family_id": f"stage7.post_king_tempo.family_{index:02d}",
            "support": len(items),
            "outcome_counts": dict(outcomes),
            "failure_class_counts": dict(failure_classes),
            "prototype": {
                key: prototype.get(key)
                for key in (
                    "sample_fen",
                    "box_shrink_move",
                    "black_reply",
                    "post_reply_fen",
                    "tempo_move",
                    "post_tempo_fen",
                    "metrics",
                    "post_tempo_context_terms",
                    "move_shape_terms",
                    "post_move_terms",
                    "worst_reply_terms",
                    "stage7_king_tempo_audit",
                )
            },
        })
    return families


def _config_from_diagnostic(diagnostic: dict[str, Any]) -> dict[str, Any]:
    return {
        "successor_affordance_layer_enabled": bool(diagnostic.get("successor_affordance_layer_enabled")),
        "successor_contract_gate_enabled": bool(diagnostic.get("successor_contract_gate_enabled")),
        "successor_role_license_enabled": bool(diagnostic.get("successor_role_license_enabled")),
        "explicit_role_provider_support_enabled": bool(diagnostic.get("explicit_role_provider_support_enabled", False)),
        "successor_role_veto_penalty": float(diagnostic.get("successor_role_veto_penalty", 0.0) or 0.0),
        "successor_stage0_drift_penalty": float(diagnostic.get("successor_stage0_drift_penalty", 0.0) or 0.0),
        "successor_role_scoped_move_shape_enabled": bool(diagnostic.get("successor_role_scoped_move_shape_enabled")),
        "successor_role_scoped_move_shape_bonus": float(diagnostic.get("successor_role_scoped_move_shape_bonus", 0.0) or 0.0),
        "successor_role_scoped_move_shape_require_worst_reply": bool(
            diagnostic.get("successor_role_scoped_move_shape_require_worst_reply")
        ),
        "stagnation_breaker_enabled": bool(diagnostic.get("stagnation_breaker_enabled")),
        "stagnation_breaker_bonus": float(diagnostic.get("stagnation_breaker_bonus", 0.0) or 0.0),
        "stagnation_breaker_king_support_bonus": float(diagnostic.get("stagnation_breaker_king_support_bonus", 0.0) or 0.0),
        "post_break_continuation_enabled": bool(diagnostic.get("post_break_continuation_enabled")),
        "post_break_continuation_bonus": float(diagnostic.get("post_break_continuation_bonus", 0.0) or 0.0),
        "early_stop_stable_suggestions": int(diagnostic.get("early_stop_stable_suggestions", 0) or 0),
        "enable_diagnostic_caches": bool(diagnostic.get("diagnostic_caches_enabled", False)),
    }


def replay_post_tempo_families(
    families: list[dict[str, Any]],
    *,
    topology: Path,
    diagnostic: dict[str, Any],
    horizons: list[int],
    seed: int,
    black_policy: str,
    max_ticks: int,
    suggestion_limit: int,
) -> dict[str, Any]:
    graph = build_graph_from_topology(topology)
    engine = ReConEngine(graph)
    config = _config_from_diagnostic(diagnostic)
    replay: dict[str, Any] = {}
    for family_index, family in enumerate(families):
        prototype = family["prototype"]
        board = chess.Board(str(prototype["post_tempo_fen"]))
        family_replay: dict[str, Any] = {}
        for horizon in horizons:
            result = play_to_mate(
                graph,
                engine,
                board,
                random.Random(seed + family_index * 1000 + horizon),
                label=str(diagnostic.get("label") or "box_shrink"),
                stage_filter=None,
                max_plies=int(horizon),
                black_policy=black_policy,
                trace=True,
                trace_max_plies=10,
                max_ticks=max_ticks,
                suggestion_limit=suggestion_limit,
                stage7_king_tempo_enabled=False,
                **config,
            )
            first_white = _first_white_event(result)
            first_move = first_white.get("move") if first_white else None
            first_skill = _selected_skill_from_engine(
                first_white.get("engine") if first_white else None,
                first_move,
            )
            family_replay[str(horizon)] = {
                "result": result.get("result"),
                "plies": result.get("plies"),
                "first_white_move": first_move,
                "first_white_skill": first_skill,
                "first_white_fen": first_white.get("fen") if first_white else None,
                "first_reply": result.get("first_reply"),
                "final_fen": result.get("final_fen"),
                "stagnation_summary": result.get("stagnation_summary"),
            }
        replay[str(family["family_id"])] = family_replay
    return replay


def classify_family(family: dict[str, Any], replay: dict[str, Any] | None = None) -> str:
    outcomes = family.get("outcome_counts") or {}
    metrics = (family.get("prototype") or {}).get("metrics") or {}
    post_corner_distance = metrics.get("post_enemy_corner_distance")
    if outcomes.get("mate") and not outcomes.get("max_plies"):
        return "post_king_tempo_converts"
    if replay and any(item.get("result") == "mate" for item in replay.values()):
        return "horizon_or_followup_routing_issue"
    if post_corner_distance is not None and int(post_corner_distance) > 1:
        return "post_king_tempo_lacks_corner_net_pressure"
    return "post_king_tempo_continuation_gap"


def audit_post_king_tempo_continuation(
    *,
    diagnostic_path: Path,
    topology: Path | None = None,
    horizons: list[int] | None = None,
    seed: int = 7,
    black_policy: str = "adversarial",
    max_ticks: int = 40,
    suggestion_limit: int = 5,
) -> dict[str, Any]:
    diagnostic = _load_json(diagnostic_path)
    records = extract_king_tempo_records(diagnostic)
    families = group_records(records)
    replay: dict[str, Any] = {}
    if topology is not None:
        replay = replay_post_tempo_families(
            families,
            topology=topology,
            diagnostic=diagnostic,
            horizons=horizons or [20, 40, 60],
            seed=seed,
            black_policy=black_policy,
            max_ticks=max_ticks,
            suggestion_limit=suggestion_limit,
        )

    family_classes = {
        family["family_id"]: classify_family(family, replay.get(str(family["family_id"])))
        for family in families
    }
    class_counts = Counter(family_classes.values())
    outcome_counts = Counter(str(record.get("playout_result")) for record in records)
    failed_support = sum(
        int(family.get("support", 0) or 0)
        for family in families
        if (family.get("outcome_counts") or {}).get("max_plies")
    )

    needs_post_tempo_role = any(
        label in {
            "post_king_tempo_lacks_corner_net_pressure",
            "post_king_tempo_continuation_gap",
            "horizon_or_followup_routing_issue",
        }
        for label in family_classes.values()
    )
    return {
        "schema_version": "stage7_post_king_tempo_continuation_audit.v1",
        "causal_status": "non_causal",
        "candidate_id": "cand.krk.box_shrink.post_king_tempo_continuation.v1",
        "diagnostic_artifact": str(diagnostic_path),
        "topology_artifact": str(topology) if topology else None,
        "counts": {
            "records": len(records),
            "families": len(families),
            "outcome_counts": dict(outcome_counts),
            "failed_support": failed_support,
        },
        "family_classes": family_classes,
        "family_class_counts": dict(class_counts),
        "families": families,
        "replay_horizons": horizons or ([] if topology is None else [20, 40, 60]),
        "replay": replay,
        "diagnosis": (
            "post_king_tempo_followup_needed"
            if needs_post_tempo_role and failed_support
            else "king_tempo_followup_sufficient"
        ),
        "candidate_update": {
            "schema_version": "structural_candidate_update.v1",
            "candidate_id": "cand.krk.box_shrink.post_king_tempo_continuation.v1",
            "candidate_status": "proposed",
            "diagnostic_labels": sorted(class_counts),
            "source_monitor_script": "growth.monitor.successor_miscalibration",
            "source_terms": [
                "stage7_king_tempo_license_confirmed",
                "selected_successor_miscalibrated",
                "repeated_conversion_failure",
            ],
            "trigger_failure_classes": [
                "selected_successor_miscalibrated",
                "repeated_conversion_failure",
                "high_score_conversion_failure",
            ],
            "target_skill": "krk.box_shrink",
            "parent_skill": "krk.drive_to_edge",
            "proposed_change": {
                "kind": "post_king_tempo_continuation_role_audit",
                "candidate_role": "krk.post_king_tempo_continuation",
                "notes": (
                    "The first king-tempo handoff improves Stage 7 but leaves a compact repeated "
                    "post-tempo failure family. Next repair should target follow-up ownership "
                    "after the king-tempo move, not broaden the first king-tempo license."
                ),
            },
            "promotion_status": "proposed",
            "causal_status": "non_causal",
            "credit": 0.0,
        },
    }


def _write_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 Post-King-Tempo Continuation Audit",
        "",
        f"- Candidate: `{payload['candidate_id']}`",
        f"- Causal status: `{payload['causal_status']}`",
        f"- Diagnosis: `{payload['diagnosis']}`",
        f"- Counts: {payload['counts']}",
        f"- Family classes: {payload['family_class_counts']}",
        "",
        "## Families",
        "",
    ]
    for family in payload.get("families", []):
        prototype = family.get("prototype") or {}
        lines.extend([
            f"### `{family['family_id']}`",
            "",
            f"- Support: {family.get('support')}",
            f"- Outcomes: {family.get('outcome_counts')}",
            f"- Class: `{payload.get('family_classes', {}).get(family['family_id'])}`",
            f"- Post-reply FEN: `{prototype.get('post_reply_fen')}`",
            f"- King-tempo move: `{prototype.get('tempo_move')}`",
            f"- Post-tempo FEN: `{prototype.get('post_tempo_fen')}`",
            f"- Metrics: {prototype.get('metrics')}",
            f"- Context terms: {prototype.get('post_tempo_context_terms')}",
            "",
        ])
        replay = payload.get("replay", {}).get(str(family["family_id"]), {})
        if replay:
            lines.extend(["Replay:", ""])
            for horizon, item in replay.items():
                lines.append(
                    f"- h={horizon}: {item.get('result')} in {item.get('plies')} plies; "
                    f"first white `{item.get('first_white_move')}` via `{item.get('first_white_skill')}`"
                )
            lines.append("")
    lines.extend([
        "## Candidate Update",
        "",
        "```json",
        json.dumps(payload["candidate_update"], indent=2),
        "```",
    ])
    return "\n".join(lines) + "\n"


def _parse_horizons(raw: str) -> list[int]:
    horizons = [int(item.strip()) for item in raw.split(",") if item.strip()]
    if not horizons:
        raise ValueError("at least one horizon is required")
    return horizons


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--topology", type=Path)
    parser.add_argument("--horizons", default="20,40,60")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--black-policy", choices=["random", "adversarial"], default="adversarial")
    parser.add_argument("--max-ticks", type=int, default=40)
    parser.add_argument("--suggestion-limit", type=int, default=5)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = audit_post_king_tempo_continuation(
        diagnostic_path=args.diagnostic,
        topology=args.topology,
        horizons=_parse_horizons(args.horizons),
        seed=args.seed,
        black_policy=args.black_policy,
        max_ticks=args.max_ticks,
        suggestion_limit=args.suggestion_limit,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(_write_markdown(payload), encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps({
            "candidate_id": payload["candidate_id"],
            "diagnosis": payload["diagnosis"],
            "counts": payload["counts"],
            "family_class_counts": payload["family_class_counts"],
        }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
