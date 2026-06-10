#!/usr/bin/env python3
"""Build KRK strategy arbitration dataset v0 from existing artifacts.

This is replay-free and non-causal. It normalizes existing Stage 5/6/7
diagnostic evidence into StrategyProposalFrame records. It does not run
gameplay, train Stage 8, promote Stage 7, mutate topology, or use DTM/tablebase
at runtime.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


STAGE_ARTIFACTS = [
    {
        "stage": "stage5",
        "label": "fence_established",
        "path": Path("snapshots/krk_triplet_pipeline/handoff_observability_check/slice19_role_scoped_move_shape_stage5_25_earlystop2.json"),
        "max_records": 8,
    },
    {
        "stage": "stage6",
        "label": "drive_to_edge",
        "path": Path("snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile/stage6_drive_profile_500_seed7_h40.json"),
        "max_records": 10,
    },
    {
        "stage": "stage4",
        "label": "wrong_tempo_control",
        "path": Path("snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage4_wrong_tempo_overlay_300_seed7_h40.json"),
        "max_records": 6,
    },
]


def _load_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _state_id(fen: str | None, fallback: str = "unknown") -> str:
    text = fen or fallback
    return "state." + hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def _edge_bucket(value: Any) -> str | None:
    if value is None:
        return None
    try:
        distance = int(value)
    except (TypeError, ValueError):
        return None
    if distance <= 0:
        return "at_edge"
    if distance == 1:
        return "near_edge"
    return "central_or_midboard"


def _box_area_relevance(edge_distance: Any, box_area: Any) -> str | None:
    if edge_distance is None or box_area is None:
        return None
    try:
        edge = int(edge_distance)
        box = int(box_area)
    except (TypeError, ValueError):
        return None
    if edge <= 0:
        return "low"
    if edge == 1:
        return "medium" if box >= 8 else "low"
    return "high" if box >= 12 else "medium"


def _context_from_fen(fen: str | None) -> dict[str, Any]:
    if not fen:
        return {}
    try:
        import contextlib
        import io

        import chess

        with contextlib.redirect_stdout(io.StringIO()):
            from recon_lite_chess.krk_baseline_nodes import _compute_krk_context_terms, _krk_geometry_metrics

        board = chess.Board(fen)
        terms = _compute_krk_context_terms(board)
        metrics = _krk_geometry_metrics(board) or {}
    except Exception:
        return {}

    edge_distance = metrics.get("enemy_edge_distance")
    box_area = metrics.get("box_area")
    return {
        "black_king_edge_distance": edge_distance,
        "black_king_edge_bucket": _edge_bucket(edge_distance),
        "box_area": box_area,
        "box_area_relevance": _box_area_relevance(edge_distance, box_area),
        "rook_safe": bool(terms.get("rook_safe")) if terms else None,
        "fence_exists": bool(terms.get("fence_exists")) if terms else None,
        "fence_stable": bool(terms.get("fence_stable")) if terms else None,
        "cut_stable": bool(terms.get("cut_stable")) if terms else None,
        "white_king_support_available": bool(terms.get("white_king_support_available")) if terms else None,
        "white_king_can_improve_support": bool(terms.get("white_king_can_improve_support")) if terms else None,
        "enemy_king_mobility": metrics.get("black_king_escape_count"),
        "mate_in_one_available": bool(terms.get("mate_in_one_available")) if terms else None,
        "mate_basin_readiness": bool(terms.get("mate_basin_available")) if terms else None,
        "edge_net_pressure_proxy": bool(
            terms.get("edge_rook_transfer_recovery_available")
            or terms.get("edge_trap_shape_available")
            or terms.get("enemy_king_near_edge")
        ),
        "corner_net_pressure_proxy": bool(terms.get("corner_net_pressure_available")),
        "stalemate_or_draw_risk": None,
        "active_terminal_terms": sorted(term for term, value in terms.items() if value),
    }


def _merge_context(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key == "active_terminal_terms":
            terms = set(merged.get(key) or [])
            terms.update(value or [])
            merged[key] = sorted(terms)
        elif value is not None:
            merged[key] = value
    return merged


def _context_from_merge_row(row: dict[str, Any]) -> dict[str, Any]:
    src = row.get("terminal_space_context") or {}
    return {
        "black_king_edge_distance": src.get("black_king_edge_distance"),
        "black_king_edge_bucket": src.get("black_king_edge_bucket"),
        "box_area": src.get("box_area"),
        "box_area_relevance": src.get("box_area_relevance"),
        "rook_safe": src.get("rook_safe"),
        "fence_exists": _status_has(src.get("fence_cut_status"), "fence"),
        "fence_stable": src.get("fence_cut_status") == "stable_fence",
        "cut_stable": src.get("fence_cut_status") == "cut_stable",
        "white_king_support_available": src.get("king_support_status") == "support_available",
        "white_king_can_improve_support": src.get("king_support_status") == "support_can_improve",
        "enemy_king_mobility": None,
        "mate_in_one_available": src.get("mate_in_one_available"),
        "mate_basin_readiness": bool(src.get("mate_basin_or_edge_net_proxy")),
        "edge_net_pressure_proxy": bool(src.get("mate_basin_or_edge_net_proxy")),
        "corner_net_pressure_proxy": "corner_net_pressure_available" in str(src.get("mate_basin_or_edge_net_proxy") or ""),
        "stalemate_or_draw_risk": None,
        "active_terminal_terms": src.get("active_terminal_terms") or [],
    }


def _status_has(value: Any, pattern: str) -> bool | None:
    if value is None:
        return None
    return pattern in str(value)


def _proposal_frame(
    *,
    state_id: str,
    fen: str | None,
    active_landmark_label: str | None,
    provider_id: str | None,
    move_uci: str | None,
    raw_score: Any = None,
    provider_local_rank: Any = None,
    normalized_score: Any = None,
    source_terms: list[str] | None = None,
    role_licenses: list[dict[str, Any]] | None = None,
    plan_capsule_context: dict[str, Any] | None = None,
    move_shape_terms: list[str] | None = None,
    post_move_terms: list[str] | None = None,
    safety_terms: list[str] | None = None,
    known_outcome_label: Any = None,
    shadow_failure_labels: list[str] | None = None,
    provider_version: str | None = None,
) -> dict[str, Any]:
    skill_id = provider_id if provider_id and provider_id.startswith("krk.") else provider_id
    return {
        "schema_version": "strategy_proposal_frame.v1",
        "state_id": state_id,
        "fen": fen,
        "active_landmark_label": active_landmark_label,
        "provider_id": provider_id,
        "skill_id": skill_id,
        "provider_version": provider_version,
        "move_uci": move_uci,
        "raw_score": raw_score,
        "provider_local_rank": provider_local_rank,
        "normalized_score": normalized_score,
        "source_terms": source_terms or [],
        "role_licenses": role_licenses or [],
        "plan_capsule_context": plan_capsule_context or {},
        "move_shape_terms": move_shape_terms or [],
        "post_move_terms": post_move_terms or [],
        "safety_terms": safety_terms or [],
        "known_outcome_label": known_outcome_label,
        "shadow_failure_labels": shadow_failure_labels or [],
        "causal_status": "non_causal",
    }


def validate_strategy_proposal_frame(frame: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "state_id",
        "fen",
        "active_landmark_label",
        "provider_id",
        "skill_id",
        "provider_version",
        "move_uci",
        "raw_score",
        "provider_local_rank",
        "normalized_score",
        "source_terms",
        "role_licenses",
        "plan_capsule_context",
        "move_shape_terms",
        "post_move_terms",
        "safety_terms",
        "known_outcome_label",
        "shadow_failure_labels",
        "causal_status",
    }
    missing = required - set(frame)
    if missing:
        raise ValueError(f"strategy proposal frame missing keys: {sorted(missing)}")
    if frame.get("schema_version") != "strategy_proposal_frame.v1":
        raise ValueError("unexpected StrategyProposalFrame schema")
    if frame.get("causal_status") != "non_causal":
        raise ValueError("StrategyProposalFrame must remain non-causal")


def _record(
    *,
    state_id: str,
    fen: str | None,
    source_artifacts: list[str],
    source_stage: str,
    active_landmark_label: str | None,
    result_label: Any,
    terminal_space_context: dict[str, Any],
    proposals: list[dict[str, Any]],
    role_capsule_context: dict[str, Any] | None = None,
    hypothesis_labels: list[str] | None = None,
    sample_support_count: int | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "krk_strategy_arbitration_record.v1",
        "state_id": state_id,
        "fen": fen,
        "source_stage": source_stage,
        "source_artifacts": source_artifacts,
        "active_landmark_label": active_landmark_label,
        "result_label": result_label,
        "sample_support_count": sample_support_count,
        "terminal_space_context": terminal_space_context,
        "role_capsule_context": role_capsule_context or {},
        "strategy_proposals": proposals,
        "hypothesis_labels": hypothesis_labels or [],
        "causal_status": "non_causal",
    }


def _label_from_playout(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return result
    if result is None:
        return {"result": None}
    return {"result": result}


def _build_stage7_records(artifact_root: Path) -> list[dict[str, Any]]:
    merge = _load_optional_json(artifact_root / "stage7_evidence_merge_table.json")
    records: list[dict[str, Any]] = []
    for index, row in enumerate(merge.get("rows") or []):
        identity = row.get("state_identity") or {}
        strategy = row.get("strategy_provider_evidence") or {}
        continuation = row.get("continuation_evidence") or {}
        fen = identity.get("post_reply_fen")
        state_id = identity.get("state_signature") or _state_id(fen, f"stage7.{index}")
        context = _merge_context(_context_from_fen(fen), _context_from_merge_row(row))
        source_artifacts = identity.get("source_artifacts") or ["stage7_evidence_merge_table.json"]
        proposals: list[dict[str, Any]] = []
        for item in strategy.get("provider_local_rank_info") or []:
            known = item.get("playout_label")
            proposals.append(
                _proposal_frame(
                    state_id=state_id,
                    fen=fen,
                    active_landmark_label="box_shrink",
                    provider_id=item.get("provider_id"),
                    move_uci=item.get("move"),
                    raw_score=item.get("raw_score"),
                    provider_local_rank=item.get("provider_local_rank"),
                    normalized_score=item.get("provider_local_normalized_score"),
                    known_outcome_label=known,
                    shadow_failure_labels=row.get("hypothesis_labels") or [],
                )
            )
        forced = strategy.get("forced_provider_results") or {}
        for provider, result in forced.items():
            if not isinstance(result, dict):
                continue
            proposals.append(
                _proposal_frame(
                    state_id=state_id,
                    fen=fen,
                    active_landmark_label="box_shrink",
                    provider_id=provider,
                    move_uci=result.get("first_move"),
                    provider_local_rank=1,
                    normalized_score=1.0,
                    known_outcome_label={
                        "result": result.get("result"),
                        "plies": result.get("plies"),
                        "horizon": result.get("horizon"),
                        "source": "forced_provider_result",
                    },
                    shadow_failure_labels=row.get("hypothesis_labels") or [],
                )
            )
        if not proposals and strategy.get("raw_selected_provider"):
            proposals.append(
                _proposal_frame(
                    state_id=state_id,
                    fen=fen,
                    active_landmark_label="box_shrink",
                    provider_id=strategy.get("raw_selected_provider"),
                    move_uci=strategy.get("raw_selected_move"),
                    known_outcome_label=_label_from_playout(continuation.get("current_graph_result_h40")),
                    shadow_failure_labels=row.get("hypothesis_labels") or [],
                )
            )
        records.append(
            _record(
                state_id=state_id,
                fen=fen,
                source_artifacts=source_artifacts,
                source_stage="stage7",
                active_landmark_label="box_shrink",
                result_label={
                    "current_graph_h40": continuation.get("current_graph_result_h40"),
                    "dtm": continuation.get("dtm_result"),
                    "closed_loop_capsule": continuation.get("closed_loop_capsule_result"),
                },
                terminal_space_context=context,
                proposals=proposals,
                role_capsule_context={"stage7_residual_or_success_context": True},
                hypothesis_labels=row.get("hypothesis_labels") or [],
                sample_support_count=identity.get("sample_support_count"),
            )
        )
    return records


def _sample_packets(payload: dict[str, Any], *, max_records: int) -> list[dict[str, Any]]:
    packets = [
        packet
        for packet in payload.get("handoff_packets") or []
        if isinstance(packet, dict) and packet.get("phase") == "post_opponent_reply"
    ]
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for packet in packets:
        evidence = packet.get("evidence_terms") or {}
        buckets[str(evidence.get("playout_result") or packet.get("observed_outcome") or "unknown")].append(packet)
    selected: list[dict[str, Any]] = []
    for bucket in sorted(buckets):
        selected.extend(buckets[bucket][: max(1, max_records // max(len(buckets), 1))])
    if len(selected) < max_records:
        seen = {id(packet) for packet in selected}
        for packet in packets:
            if id(packet) not in seen:
                selected.append(packet)
            if len(selected) >= max_records:
                break
    return selected[:max_records]


def _build_packet_records(path: Path, source_stage: str, label: str, max_records: int) -> list[dict[str, Any]]:
    payload = _load_optional_json(path)
    records: list[dict[str, Any]] = []
    for packet in _sample_packets(payload, max_records=max_records):
        evidence = packet.get("evidence_terms") or {}
        fen = evidence.get("post_reply_fen") or evidence.get("fen")
        state_id = evidence.get("post_reply_state_signature") or _state_id(fen, packet.get("packet_id") or source_stage)
        context = _context_from_fen(fen)
        visible_terms = evidence.get("visible_terms") or {}
        if isinstance(visible_terms, dict):
            context = _merge_context(
                context,
                {
                    "active_terminal_terms": sorted(term for term, value in visible_terms.items() if value),
                    "rook_safe": visible_terms.get("rook_safe"),
                    "fence_exists": visible_terms.get("fence_exists"),
                    "fence_stable": visible_terms.get("fence_stable"),
                    "cut_stable": visible_terms.get("cut_stable"),
                    "white_king_support_available": visible_terms.get("white_king_support_available"),
                    "white_king_can_improve_support": visible_terms.get("white_king_can_improve_support"),
                    "mate_in_one_available": visible_terms.get("mate_in_one_available"),
                },
            )
        proposals: list[dict[str, Any]] = []
        successor_skills = evidence.get("successor_skills") or {}
        for provider, item in successor_skills.items():
            if not isinstance(item, dict):
                continue
            audit = item.get("visible_move_shape_audit") or {}
            proposals.append(
                _proposal_frame(
                    state_id=state_id,
                    fen=fen,
                    active_landmark_label=label,
                    provider_id=provider,
                    move_uci=item.get("best_move"),
                    raw_score=item.get("raw_score_before_role_bonus", item.get("score")),
                    provider_local_rank=1,
                    normalized_score=1.0,
                    source_terms=[
                        term
                        for license_ in item.get("visible_role_licenses") or []
                        for term in license_.get("source_terms") or []
                        if isinstance(license_, dict)
                    ],
                    role_licenses=item.get("visible_role_licenses") or [],
                    move_shape_terms=audit.get("move_shape_terms") or [],
                    post_move_terms=audit.get("post_move_terms") or [],
                    safety_terms=[term for term in audit.get("post_move_terms") or [] if "safe" in str(term)],
                    known_outcome_label={
                        "playout_result": evidence.get("playout_result"),
                        "plies": evidence.get("plies"),
                        "selected": provider == evidence.get("successor_selected_skill"),
                    },
                    shadow_failure_labels=evidence.get("failure_classes") or [],
                )
            )
        if not proposals and evidence.get("successor_selected_skill"):
            proposals.append(
                _proposal_frame(
                    state_id=state_id,
                    fen=fen,
                    active_landmark_label=label,
                    provider_id=evidence.get("successor_selected_skill"),
                    move_uci=evidence.get("move"),
                    raw_score=evidence.get("successor_best_score"),
                    provider_local_rank=1,
                    normalized_score=1.0,
                    known_outcome_label={"playout_result": evidence.get("playout_result"), "plies": evidence.get("plies")},
                    shadow_failure_labels=evidence.get("failure_classes") or [],
                )
            )
        records.append(
            _record(
                state_id=state_id,
                fen=fen,
                source_artifacts=[str(path)],
                source_stage=source_stage,
                active_landmark_label=label,
                result_label={"playout_result": evidence.get("playout_result"), "plies": evidence.get("plies")},
                terminal_space_context=context,
                proposals=proposals,
                role_capsule_context={
                    "selected_skill_source": evidence.get("selected_skill_source"),
                    "semantic_alignment_status": evidence.get("semantic_alignment_status"),
                    "visible_successor_affordances": sorted((evidence.get("visible_successor_affordances") or {}).keys()),
                },
                hypothesis_labels=[],
            )
        )
    return records


def build_dataset(repo_root: Path, structural_root: Path = Path("reports/structural_candidates")) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    records.extend(_build_stage7_records(repo_root / structural_root))
    for item in STAGE_ARTIFACTS:
        records.extend(
            _build_packet_records(
                repo_root / item["path"],
                source_stage=item["stage"],
                label=item["label"],
                max_records=int(item["max_records"]),
            )
        )

    proposal_count = sum(len(record["strategy_proposals"]) for record in records)
    source_counts = Counter(record["source_stage"] for record in records)
    outcome_counts = Counter(
        str((record.get("result_label") or {}).get("playout_result") or (record.get("result_label") or {}).get("current_graph_h40"))
        for record in records
    )
    dataset = {
        "schema_version": "krk_strategy_arbitration_dataset.v0",
        "causal_status": "non_causal_dataset",
        "runtime_behavior_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "description": "Small replay-free KRK strategy arbitration dataset built from existing Stage 5/6/7 diagnostics.",
        "source_artifacts": {
            "stage7_evidence_merge": str(structural_root / "stage7_evidence_merge_table.json"),
            "stage_artifacts": [str(item["path"]) for item in STAGE_ARTIFACTS],
        },
        "performance_policy": {
            "replay_free": True,
            "new_h40_labels": 0,
            "exhaustive_legal_first_sweeps": False,
            "provider_suggestions_capped": True,
        },
        "summary": {
            "record_count": len(records),
            "proposal_count": proposal_count,
            "records_by_source_stage": dict(source_counts),
            "result_label_counts": dict(outcome_counts),
            "records_with_terminal_context": sum(1 for record in records if record.get("terminal_space_context")),
        },
        "records": records,
        "hard_constraints": [
            "do_not_train_stage8",
            "do_not_promote_stage7",
            "do_not_make_arbitration_causal",
            "do_not_use_dtm_or_tablebase_at_runtime",
            "do_not_mutate_topology_during_gameplay",
        ],
    }
    validate_dataset(dataset)
    return dataset


def validate_dataset(dataset: dict[str, Any]) -> None:
    if dataset.get("schema_version") != "krk_strategy_arbitration_dataset.v0":
        raise ValueError("unexpected dataset schema")
    if dataset.get("causal_status") != "non_causal_dataset":
        raise ValueError("dataset must be non-causal")
    if dataset.get("runtime_behavior_changed") is not False:
        raise ValueError("dataset must not change runtime behavior")
    if dataset.get("runtime_dtm_or_tablebase_lookup") is not False:
        raise ValueError("dataset must not use runtime DTM/tablebase")
    if dataset.get("gameplay_topology_mutation") is not False:
        raise ValueError("dataset must not mutate gameplay topology")
    if dataset.get("stage7_promotion_allowed") is not False or dataset.get("stage8_training_allowed") is not False:
        raise ValueError("Stage 7 promotion and Stage 8 training must remain blocked")
    for record in dataset.get("records") or []:
        if record.get("causal_status") != "non_causal":
            raise ValueError("record must be non-causal")
        for frame in record.get("strategy_proposals") or []:
            validate_strategy_proposal_frame(frame)


def render_markdown(dataset: dict[str, Any]) -> str:
    lines = [
        "# KRK Strategy Arbitration Dataset v0",
        "",
        "This dataset is replay-free and non-causal. It normalizes existing Stage 5/6/7 evidence into StrategyProposalFrame records.",
        "",
        "## Status",
        "",
        f"- Causal status: `{dataset['causal_status']}`",
        f"- Runtime behavior changed: `{dataset['runtime_behavior_changed']}`",
        f"- Stage 7 promotion allowed: `{dataset['stage7_promotion_allowed']}`",
        f"- Stage 8 training allowed: `{dataset['stage8_training_allowed']}`",
        "",
        "## Summary",
        "",
        f"- Record count: `{dataset['summary']['record_count']}`",
        f"- Proposal count: `{dataset['summary']['proposal_count']}`",
        f"- Records by source stage: `{dataset['summary']['records_by_source_stage']}`",
        f"- Result label counts: `{dataset['summary']['result_label_counts']}`",
        f"- New h40 labels: `{dataset['performance_policy']['new_h40_labels']}`",
        "",
        "## Sample Records",
        "",
    ]
    for record in dataset["records"][:8]:
        context = record.get("terminal_space_context") or {}
        lines.append(
            f"- `{record['state_id']}` stage=`{record['source_stage']}` label=`{record['active_landmark_label']}` "
            f"result=`{record['result_label']}` proposals={len(record.get('strategy_proposals') or [])} "
            f"edge_bucket=`{context.get('black_king_edge_bucket')}` box_relevance=`{context.get('box_area_relevance')}`"
        )
    lines.extend(["", "## Hard Constraints", ""])
    lines.extend(f"- {item}" for item in dataset["hard_constraints"])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    dataset = build_dataset(args.repo_root)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(dataset, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(dataset), encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(dataset, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
