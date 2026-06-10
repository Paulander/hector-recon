#!/usr/bin/env python3
"""Export replay-free KRK ControlPlaneEvidenceFrame records.

Frames are built from existing reports only. They are non-causal evidence
records and do not alter runtime selection, scoring, topology, or training.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


CONTRACT = Path("reports/krk_control_plane_evidence_contract_v0.json")
GAP_REPORT = Path("reports/krk_control_plane_gap_report_v0.json")
PROTECTED_STATUS = Path("reports/krk_protected_stage_status.json")
STRATEGY_DATASET = Path("reports/strategy_arbitration/krk_strategy_arbitration_dataset_v0.json")
MONITOR_RECORDS = Path("reports/strategy_arbitration/krk_strategy_monitor_records_v0.json")
PLAN_WINDOWS = Path("reports/structural_candidates/stage7_plan_capsule_owned_window_25_h40.json")
DTM_SEED_JSONL = Path("reports/structural_candidates/stage7_post_box_dtm_trajectory_seed_h40.jsonl")
DTM_EXPANDED_JSONL = Path(
    "reports/structural_candidates/stage7_post_box_dtm_trajectory_seed_expanded_h40.jsonl"
)
STAGE6_PROMOTION = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/"
    "promotion_eval_stage6_overlay.json"
)
STAGE7_CLOSURE = Path("reports/structural_candidates/stage7_post_decision_closure.json")


def _load_json(root: Path, relative_path: Path) -> dict[str, Any]:
    payload = json.loads((root / relative_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {relative_path}")
    return payload


def _load_optional_json(root: Path, relative_path: Path) -> dict[str, Any]:
    path = root / relative_path
    if not path.exists():
        return {}
    return _load_json(root, relative_path)


def _load_jsonl_by_fen(root: Path, relative_path: Path) -> dict[str, list[dict[str, Any]]]:
    path = root / relative_path
    by_fen: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if not path.exists():
        return by_fen
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        fen = payload.get("fen")
        if fen:
            by_fen[str(fen)].append(payload)
    return by_fen


def _provider_provenance(source_stage: str, active_label: str | None) -> list[dict[str, Any]]:
    if source_stage == "stage6":
        return [
            {
                "skill_id": "krk.drive_to_edge",
                "provider_version": "stage6_overlay_v1",
                "source_stage": "stage6",
                "source_checkpoint": "adaptive_krk_stage6_drive_profile_king_support/best_by_stage/drive_to_edge.pkl",
                "validated_profile": "handoff_composition_v1",
                "provider_maturity": "validated_low_plasticity",
                "frozen_provider": False,
                "overlay_provider": True,
                "plasticity_scope": "protected_overlay",
                "guardrail_status": "promoted_against_stage5_guardrail",
            }
        ]
    if source_stage == "stage5":
        return [
            {
                "skill_id": "krk.fence_established",
                "provider_version": "stage5_validated_v1",
                "source_stage": "stage5",
                "source_checkpoint": "adaptive_krk_stage5_fence_clean/best_by_stage/fence_established.pkl",
                "validated_profile": "handoff_composition_v1",
                "provider_maturity": "foundation_frozen",
                "frozen_provider": True,
                "overlay_provider": False,
                "plasticity_scope": "protected_frozen",
                "guardrail_status": "protected_guardrail_passed",
            }
        ]
    if source_stage == "stage4":
        return [
            {
                "skill_id": "krk.edge_trap_wrong_tempo",
                "provider_version": "stage5_validated_v1",
                "source_stage": "stage4",
                "source_checkpoint": "stage5_validated_provider_pack",
                "validated_profile": "handoff_composition_v1",
                "provider_maturity": "validated_low_plasticity",
                "frozen_provider": True,
                "overlay_provider": False,
                "plasticity_scope": "protected_frozen",
                "guardrail_status": "profile_passed_with_h40_overlay_control_caveat",
            }
        ]
    return [
        {
            "skill_id": f"krk.{active_label or 'unknown'}",
            "provider_version": "stage7_quarantined_or_challenge",
            "source_stage": source_stage or "unknown",
            "source_checkpoint": None,
            "validated_profile": "handoff_composition_v1",
            "provider_maturity": "quarantined_no_plasticity",
            "frozen_provider": False,
            "overlay_provider": True,
            "plasticity_scope": "diagnostic_only",
            "guardrail_status": "not_promoted",
        }
    ]


def _normalize_strategy_proposal(proposal: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "strategy_proposal_frame.v1",
        "provider_id": proposal.get("provider_id"),
        "skill_id": proposal.get("skill_id") or proposal.get("provider_id"),
        "provider_version": proposal.get("provider_version"),
        "move_uci": proposal.get("move_uci") or proposal.get("move"),
        "raw_score": proposal.get("raw_score"),
        "provider_local_rank": proposal.get("provider_local_rank"),
        "normalized_score": proposal.get("normalized_score")
        if proposal.get("normalized_score") is not None
        else proposal.get("provider_local_normalized_score"),
        "source_terms": proposal.get("source_terms") or [],
        "role_licenses": proposal.get("role_licenses") or [],
        "move_shape_terms": proposal.get("move_shape_terms") or [],
        "post_move_terms": proposal.get("post_move_terms") or [],
        "safety_terms": proposal.get("safety_terms") or [],
        "known_outcome_label": proposal.get("known_outcome_label") or {},
        "causal_status": "non_causal",
    }


def _normalize_monitor(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "internal_monitor_evidence.v1",
        "terminal_id": record.get("source_candidate_id") or record.get("monitor_id"),
        "monitor_id": record.get("monitor_id"),
        "monitor_type": record.get("monitor_type"),
        "source_terms_met": record.get("source_terms") or [],
        "missing_terms": record.get("missing_terms") or [],
        "confidence": record.get("confidence"),
        "associated_outcome": record.get("associated_outcome"),
        "maturity_status": record.get("promotion_status") or "proposed",
        "causal_ready": False,
        "causal_status": "non_causal",
    }


def _normalize_window(window: dict[str, Any]) -> dict[str, Any]:
    status = "expired" if window.get("ttl_failure") else "progress_recorded"
    return {
        "schema_version": "plan_capsule_window_evidence.v1",
        "plan_id": "krk.post_box_shrink_continuation",
        "plan_status": status,
        "ttl_white_moves": window.get("ttl_white_moves"),
        "owned_white_move_count": window.get("owned_white_move_count"),
        "entry_terms_confirmed": ["entry_confirmed"] if window.get("entry_confirmed") else [],
        "progress_terms_confirmed": window.get("progress_terms") or [],
        "exit_terms_confirmed": [],
        "abort_terms_confirmed": window.get("abort_terms_at_entry") or [],
        "handoff_target": None,
        "window_outcome": window.get("result"),
        "causal_status": "non_causal",
    }


def _sequence_examples_for_fen(fen: str, seed_by_fen: dict[str, list[dict[str, Any]]], expanded_by_fen: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    examples = []
    for source_name, rows in (("seed", seed_by_fen.get(fen, [])), ("expanded", expanded_by_fen.get(fen, []))):
        for index, row in enumerate(rows):
            positives = [
                item.get("move")
                for item in row.get("legal_move_labels") or []
                if item.get("label") == 1 or item.get("target_class") == "optimal_dtm_move"
            ]
            hard_negatives = [
                item.get("move")
                for item in row.get("legal_move_labels") or []
                if item.get("target_class") == "winning_nonoptimal_move"
            ]
            vetoes = [
                item.get("move")
                for item in row.get("legal_move_labels") or []
                if item.get("target_class") == "non_winning_move"
            ]
            examples.append(
                {
                    "schema_version": "sequence_training_example.v1",
                    "example_id": (
                        f"seq.{source_name}."
                        f"{hashlib.sha1(f'{fen}|{index}'.encode('utf-8')).hexdigest()[:12]}"
                    ),
                    "family_id": row.get("target_skill") or "krk.post_box_shrink_continuation",
                    "trajectory_id": source_name,
                    "ply_index": row.get("ply_index"),
                    "candidate_moves": [
                        item.get("move") for item in row.get("legal_move_labels") or [] if item.get("move")
                    ],
                    "positive_moves": [move for move in positives if move],
                    "hard_negative_moves": [move for move in hard_negatives if move],
                    "draw_or_safety_veto_moves": [move for move in vetoes if move],
                    "label_source": "offline_dtm_supervision",
                    "offline_only": True,
                    "causal_status": "non_causal",
                }
            )
    return examples


def _guardrail_summaries(protected: dict[str, Any]) -> list[dict[str, Any]]:
    summaries = []
    for stage in protected.get("stage_statuses") or []:
        evidence = stage.get("evidence") or {}
        for key, value in evidence.items():
            if not isinstance(value, dict) or "playouts" not in value:
                continue
            summaries.append(
                {
                    "schema_version": "guardrail_result_summary.v1",
                    "guardrail_id": f"{stage.get('stage')}.{key}",
                    "stage_or_domain": stage.get("stage"),
                    "sample_count": value.get("total"),
                    "horizon": "h40_or_profile_artifact",
                    "mate_count": (value.get("playouts") or {}).get("mate", 0),
                    "max_plies_count": (value.get("playouts") or {}).get("max_plies", 0),
                    "shadow_candidate_count": value.get("shadow_candidate_count"),
                    "passed": (value.get("playouts") or {}).get("max_plies", 0) == 0,
                    "source_artifact": key,
                }
            )
    return summaries


def _growth_status(source_stage: str) -> dict[str, Any]:
    if source_stage == "stage7":
        status = "growth_blocked_by_architecture_review"
        reason = "Stage 7 micro-work stopped; evidence must flow through control-plane review."
    elif source_stage in {"stage5", "stage6", "stage4"}:
        status = "settling_or_protected"
        reason = "Validated/protected provider evidence; no structural growth requested."
    else:
        status = "monitoring_only"
        reason = "No growth decision attached to this frame."
    return {
        "schema_version": "growth_governor_status.v1",
        "stage_or_provider": source_stage,
        "status": status,
        "active_candidate_count": None,
        "guardrail_pass_rate": None,
        "plasticity_improvement_slope": None,
        "repeated_failure_family_count": None,
        "reason": reason,
    }


def _promotion_status(source_stage: str, stage6_promotion: dict[str, Any], stage7_closure: dict[str, Any]) -> dict[str, Any]:
    if source_stage == "stage6":
        return {
            "schema_version": "promotion_gate_status.v1",
            "candidate_id": "krk.drive_to_edge.stage6_overlay_v1",
            "promotion_status": stage6_promotion.get("promotion_status") or "promoted",
            "target_validation_status": "passed",
            "protected_guardrail_status": "stage5_passed",
            "shadow_candidate_delta": 0,
            "causal_status": "non_causal",
            "source_artifact": str(STAGE6_PROMOTION),
        }
    if source_stage == "stage7":
        return {
            "schema_version": "promotion_gate_status.v1",
            "candidate_id": "krk.box_shrink.stage7",
            "promotion_status": "quarantined",
            "target_validation_status": stage7_closure.get("decision", {}).get("benchmark_status")
            if isinstance(stage7_closure.get("decision"), dict)
            else "model_expression_gap_persists",
            "protected_guardrail_status": "not_applicable_no_promotion",
            "shadow_candidate_delta": None,
            "causal_status": "non_causal",
            "source_artifact": str(STAGE7_CLOSURE),
        }
    return {
        "schema_version": "promotion_gate_status.v1",
        "candidate_id": f"krk.{source_stage}.protected",
        "promotion_status": "protected_existing_provider",
        "target_validation_status": "passed_or_caveated",
        "protected_guardrail_status": "protected_stack",
        "shadow_candidate_delta": None,
        "causal_status": "non_causal",
        "source_artifact": str(PROTECTED_STATUS),
    }


def build_frames(repo_root: Path) -> dict[str, Any]:
    contract = _load_json(repo_root, CONTRACT)
    gap = _load_json(repo_root, GAP_REPORT)
    protected = _load_json(repo_root, PROTECTED_STATUS)
    strategy = _load_json(repo_root, STRATEGY_DATASET)
    monitors = _load_json(repo_root, MONITOR_RECORDS)
    plan_windows = _load_optional_json(repo_root, PLAN_WINDOWS)
    stage6_promotion = _load_optional_json(repo_root, STAGE6_PROMOTION)
    stage7_closure = _load_optional_json(repo_root, STAGE7_CLOSURE)
    seed_by_fen = _load_jsonl_by_fen(repo_root, DTM_SEED_JSONL)
    expanded_by_fen = _load_jsonl_by_fen(repo_root, DTM_EXPANDED_JSONL)

    if contract.get("causal_status") != "non_causal_schema_contract":
        raise ValueError("control-plane contract must remain non-causal")
    if gap.get("recommended_next_slice", {}).get("slice_id") != "export_replay_free_control_plane_frames_v0":
        raise ValueError("gap report does not select frame export")

    monitors_by_state: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in monitors.get("records") or []:
        state_id = record.get("state_id")
        if state_id:
            monitors_by_state[str(state_id)].append(_normalize_monitor(record))

    windows_by_fen: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for window in plan_windows.get("windows") or []:
        fen = window.get("start_fen")
        if fen:
            windows_by_fen[str(fen)].append(_normalize_window(window))

    guardrails = _guardrail_summaries(protected)
    frames = []
    for record in strategy.get("records") or []:
        state_id = str(record.get("state_id") or f"unknown.{len(frames)}")
        fen = str(record.get("fen") or "")
        source_stage = str(record.get("source_stage") or "unknown")
        active_label = record.get("active_landmark_label")
        frame = {
            "schema_version": "control_plane_evidence_frame.v1",
            "frame_id": f"cp.krk.{state_id}",
            "domain": "KRK",
            "state_id": state_id,
            "fen": fen,
            "source_stage": source_stage,
            "active_landmark_label": active_label,
            "protected_provider_provenance": _provider_provenance(source_stage, active_label),
            "strategy_proposal_frames": [
                _normalize_strategy_proposal(proposal)
                for proposal in record.get("strategy_proposals") or []
                if isinstance(proposal, dict)
            ],
            "internal_monitor_records": monitors_by_state.get(state_id, []),
            "plan_capsule_window_records": windows_by_fen.get(fen, []),
            "sequence_training_examples": _sequence_examples_for_fen(fen, seed_by_fen, expanded_by_fen),
            "outcome_labels": {
                "result_label": record.get("result_label") or {},
                "hypothesis_labels": record.get("hypothesis_labels") or [],
                "sample_support_count": record.get("sample_support_count"),
            },
            "guardrail_result_summaries": guardrails,
            "growth_governor_status": _growth_status(source_stage),
            "promotion_gate_status": _promotion_status(source_stage, stage6_promotion, stage7_closure),
            "source_artifacts": record.get("source_artifacts") or [],
            "causal_status": "non_causal",
        }
        frames.append(frame)

    summary_counts = {
        "frame_count": len(frames),
        "frames_by_source_stage": dict(Counter(frame["source_stage"] for frame in frames)),
        "strategy_proposal_frame_count": sum(len(frame["strategy_proposal_frames"]) for frame in frames),
        "internal_monitor_record_count": sum(len(frame["internal_monitor_records"]) for frame in frames),
        "plan_capsule_window_record_count": sum(len(frame["plan_capsule_window_records"]) for frame in frames),
        "sequence_training_example_count": sum(len(frame["sequence_training_examples"]) for frame in frames),
        "new_playouts_added": 0,
    }
    export = {
        "schema_version": "krk_control_plane_frames_export.v0",
        "causal_status": "non_causal_frame_export",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "hidden_python_controller": False,
        "gameplay_topology_mutation": False,
        "runtime_arbiter_added": False,
        "runtime_terminals_added": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "contract_artifact": str(CONTRACT),
        "source_artifacts": [
            str(STRATEGY_DATASET),
            str(MONITOR_RECORDS),
            str(PLAN_WINDOWS),
            str(DTM_SEED_JSONL),
            str(DTM_EXPANDED_JSONL),
            str(PROTECTED_STATUS),
            str(STAGE6_PROMOTION),
            str(STAGE7_CLOSURE),
        ],
        "frames": frames,
        "summary": summary_counts,
        "remaining_gaps": [
            "sequence_examples_are_stage7_only",
            "plan_capsule_windows_are_stage7_only",
            "growth_governor_status_is_inferred_summary_not_runtime_export",
            "cross_domain_bridge_frames_not_exported_yet",
        ],
        "recommended_next_slice": "control_plane_frame_quality_report_v0",
    }
    validate_export(export)
    return export


def validate_export(export: dict[str, Any]) -> None:
    if export.get("causal_status") != "non_causal_frame_export":
        raise ValueError("frame export must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_score_changes",
        "runtime_direct_routing",
        "runtime_dtm_or_tablebase_lookup",
        "hidden_python_controller",
        "gameplay_topology_mutation",
        "runtime_arbiter_added",
        "runtime_terminals_added",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if export.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if export["summary"]["new_playouts_added"] != 0:
        raise ValueError("frame export must be replay-free")
    for frame in export.get("frames") or []:
        if frame.get("causal_status") != "non_causal":
            raise ValueError("all frames must be non-causal")
        for proposal in frame.get("strategy_proposal_frames") or []:
            if proposal.get("causal_status") != "non_causal":
                raise ValueError("all strategy proposals must be non-causal")
        for example in frame.get("sequence_training_examples") or []:
            if example.get("offline_only") is not True:
                raise ValueError("sequence labels must remain offline-only")


def render_markdown(export: dict[str, Any]) -> str:
    summary = export["summary"]
    lines = [
        "# KRK Control-Plane Frames v0",
        "",
        "This replay-free export creates non-causal `ControlPlaneEvidenceFrame` "
        "records from existing artifacts. It does not add runtime consumers, "
        "DTM/tablebase lookup, terminals, arbiters, promotions, training, or topology changes.",
        "",
        "## Summary",
        "",
        f"- Frames: `{summary['frame_count']}`",
        f"- Frames by source stage: `{summary['frames_by_source_stage']}`",
        f"- Strategy proposal frames: `{summary['strategy_proposal_frame_count']}`",
        f"- Internal monitor records attached: `{summary['internal_monitor_record_count']}`",
        f"- Plan-capsule window records attached: `{summary['plan_capsule_window_record_count']}`",
        f"- Sequence training examples attached: `{summary['sequence_training_example_count']}`",
        f"- New playouts added: `{summary['new_playouts_added']}`",
        "",
        "## Remaining Gaps",
        "",
    ]
    lines.extend(f"- `{gap}`" for gap in export["remaining_gaps"])
    lines.extend(
        [
            "",
            "## Recommended Next Slice",
            "",
            f"`{export['recommended_next_slice']}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(export: dict[str, Any], report_root: Path) -> None:
    report_root.mkdir(parents=True, exist_ok=True)
    (report_root / "krk_control_plane_frames_v0.json").write_text(
        json.dumps(export, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (report_root / "krk_control_plane_frames_v0.md").write_text(
        render_markdown(export), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--report-root", type=Path, default=Path("reports"))
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    report_root = args.report_root
    if not report_root.is_absolute():
        report_root = repo_root / report_root
    export = build_frames(repo_root)
    write_outputs(export, report_root)
    print(json.dumps(export["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
