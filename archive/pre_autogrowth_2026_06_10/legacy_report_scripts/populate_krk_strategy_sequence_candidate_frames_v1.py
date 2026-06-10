#!/usr/bin/env python3
"""Populate non-causal KRK StrategySequenceCandidateFrame v1 artifacts.

This is replay-free evidence assembly. It converts existing capacity,
proposal, progress-window, and internal-monitor artifacts into a common
candidate-frame shape without creating a runtime candidate generator or
selector.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

CAPACITY_FRAMES = Path("reports/krk_protected_provider_coverage_frames_v0.json")
RANKED_FRAMES = Path("reports/krk_ranked_strategy_proposal_frames_v1.json")
POST_ACTIVATION_AUDIT = Path(
    "reports/krk_progress_window_reconsideration_post_activation_audit_v0.json"
)
INTERNAL_TERMINAL_EVIDENCE = Path(
    "reports/strategy_arbitration/krk_internal_terminal_evidence_v1.json"
)
FRAME_SPEC = Path("reports/strategy_arbitration/krk_strategy_sequence_candidate_frame_v1.json")

OUT_FRAMES_JSON = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_candidate_frames_v1.json"
)
OUT_FRAMES_MD = Path("reports/strategy_arbitration/krk_strategy_sequence_candidate_frames_v1.md")
OUT_QUALITY_JSON = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_candidate_frame_quality_v1.json"
)
OUT_QUALITY_MD = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_candidate_frame_quality_v1.md"
)


RUNTIME_FALSE_KEYS = (
    "runtime_behavior_changed",
    "runtime_defaults_changed",
    "runtime_selector_implemented",
    "runtime_candidate_generator_implemented",
    "runtime_terminals_added",
    "runtime_dtm_or_tablebase_lookup",
    "gameplay_topology_mutation",
    "stage7_promotion_allowed",
    "stage8_training_allowed",
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    full = ROOT / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _runtime_false_block() -> dict[str, bool]:
    return {key: False for key in RUNTIME_FALSE_KEYS}


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
    if text == "krk.box_shrink":
        return "box_shrink"
    if "post_box" in text or "plan_capsule" in text:
        return "plan_or_sequence"
    return "other"


def _base_frame(
    *,
    frame_id: str,
    state_id: str,
    fen: str | None,
    source_stage: str | None,
    active_landmark_label: str | None,
    frame_type: str,
    candidate_id: str,
    stage7_challenge_row: bool,
    label_semantics: str,
) -> dict[str, Any]:
    return {
        "schema_version": "krk_strategy_sequence_candidate_frame.v1",
        "frame_id": frame_id,
        "state_id": state_id,
        "fen": fen,
        "source_stage": source_stage,
        "active_landmark_label": active_landmark_label,
        "frame_type": frame_type,
        "candidate_id": candidate_id,
        "candidate_provider_id": None,
        "candidate_move_uci": None,
        "candidate_plan_id": None,
        "candidate_strategy_family": None,
        "source_terms": [],
        "move_shape_terms": [],
        "post_move_terms": [],
        "safety_terms": [],
        "internal_monitor_terms": [],
        "capacity_evidence": {},
        "ownership_evidence": {},
        "sequence_evidence": {},
        "label_semantics": label_semantics,
        "stage7_challenge_row": stage7_challenge_row,
        "usable_for_selector_training": False,
        "usable_for_candidate_generation_training": False,
        "causal_status": "non_causal",
    }


def capacity_candidate_frames(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        provider = str(row.get("provider_id") or "unknown")
        state_id = str(row.get("state_id") or f"capacity_state_{idx}")
        frame = _base_frame(
            frame_id=f"ssf.capacity.{state_id}.{provider}.{idx}",
            state_id=state_id,
            fen=row.get("fen"),
            source_stage=row.get("source_stage"),
            active_landmark_label=row.get("active_landmark_label"),
            frame_type="validated_provider_candidate",
            candidate_id=f"candidate.provider.{provider}",
            stage7_challenge_row=bool(row.get("stage7_challenge_row", False)),
            label_semantics="capacity_evidence_not_ownership_label",
        )
        frame["candidate_provider_id"] = provider
        frame["candidate_move_uci"] = row.get("forced_first_move")
        frame["candidate_strategy_family"] = row.get("provider_family") or _provider_family(provider)
        frame["source_terms"] = ["offline_forced_provider_capacity_label"]
        frame["capacity_evidence"] = {
            "capacity_label": row.get("capacity_label"),
            "forced_result": row.get("forced_result"),
            "forced_plies": row.get("forced_plies"),
            "forced_first_move": row.get("forced_first_move"),
            "source_label_job_id": row.get("source_label_job_id"),
            "source_artifact": str(CAPACITY_FRAMES),
        }
        frame["usable_for_candidate_generation_training"] = (
            row.get("capacity_label") == "positive_capacity"
            and not frame["stage7_challenge_row"]
        )
        frames.append(frame)
    return frames


def proposal_candidate_frames(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        provider = str(row.get("provider_id") or "unknown")
        state_id = str(row.get("state_id") or f"proposal_state_{idx}")
        stage7 = bool(row.get("stage7_challenge_row", False))
        frame = _base_frame(
            frame_id=f"ssf.proposal.{state_id}.{provider}.{idx}",
            state_id=state_id,
            fen=row.get("fen"),
            source_stage=row.get("source_stage"),
            active_landmark_label=row.get("active_landmark_label"),
            frame_type="validated_provider_candidate",
            candidate_id=f"candidate.visible_provider.{provider}",
            stage7_challenge_row=stage7,
            label_semantics="visible_provider_proposal_context_not_capacity_or_ownership_label",
        )
        frame["candidate_provider_id"] = provider
        frame["candidate_move_uci"] = row.get("move_uci")
        frame["candidate_strategy_family"] = row.get("provider_family") or _provider_family(provider)
        frame["source_terms"] = list(row.get("source_terms") or [])
        frame["move_shape_terms"] = list(row.get("move_shape_terms") or [])
        frame["post_move_terms"] = list(row.get("post_move_terms") or [])
        frame["safety_terms"] = list(row.get("safety_terms") or [])
        frame["ownership_evidence"] = {
            "frame_label": row.get("frame_label"),
            "frame_outcome": row.get("frame_outcome"),
            "global_raw_score_rank": row.get("global_raw_score_rank"),
            "provider_local_rank": row.get("provider_local_rank"),
            "raw_score": row.get("raw_score"),
            "normalized_score": row.get("normalized_score"),
            "label_channel": row.get("label_channel"),
            "source_artifact": str(RANKED_FRAMES),
        }
        frame["usable_for_selector_training"] = bool(row.get("usable_for_training")) and not stage7
        frames.append(frame)
    return frames


def progress_window_candidate_frames(payload: dict[str, Any]) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    target_state = str(payload.get("target_frame_id") or "progress_window_target")
    target_fen = payload.get("target_fen")
    for rec_idx, record in enumerate(payload.get("activation_records") or []):
        fen = record.get("fen") or target_fen
        continuation_by_move = _continuation_index(record.get("candidate_continuations_h40"))
        for cand_idx, candidate in enumerate(record.get("all_supported_candidates") or []):
            support = candidate.get("support_payload") or {}
            provider = str(candidate.get("provider_id") or support.get("provider_skill_id") or "unknown")
            move = str(candidate.get("move") or support.get("move") or "unknown")
            frame = _base_frame(
                frame_id=f"ssf.progress_window.{target_state}.{rec_idx}.{provider}.{move}.{cand_idx}",
                state_id=target_state,
                fen=fen,
                source_stage="stage7",
                active_landmark_label=payload.get("active_landmark_label") or "box_shrink",
                frame_type="candidate_move_hypothesis",
                candidate_id=f"candidate.progress_window.{provider}.{move}",
                stage7_challenge_row=True,
                label_semantics="sandbox_supported_move_hypothesis_not_selector_label",
            )
            frame["candidate_provider_id"] = provider
            frame["candidate_move_uci"] = move
            frame["candidate_strategy_family"] = _provider_family(provider)
            frame["source_terms"] = list(support.get("source_terms") or [])
            frame["move_shape_terms"] = list(support.get("move_shape_terms") or [])
            frame["post_move_terms"] = list(support.get("post_move_terms") or [])
            frame["safety_terms"] = [
                term for term in frame["source_terms"] + frame["post_move_terms"]
                if "safe" in term or "draw" in term or "stalemate" in term
            ]
            frame["internal_monitor_terms"] = list(record.get("progress_window_terms") or [])
            continuation = continuation_by_move.get(move) or {}
            frame["sequence_evidence"] = {
                "sandbox_id": payload.get("sandbox_id"),
                "activation_record_index": rec_idx,
                "supported": bool(candidate.get("supported", True)),
                "score_after_support": candidate.get("score") or support.get("score_after_support"),
                "continuation_h40": continuation,
                "selected_by_reconsideration": (
                    (record.get("reconsideration_selected") or {}).get("move") == move
                    and (record.get("reconsideration_selected") or {}).get("provider_id") == provider
                ),
                "source_artifact": str(POST_ACTIVATION_AUDIT),
            }
            frames.append(frame)
    return frames


def _continuation_index(raw: Any) -> dict[str, dict[str, Any]]:
    if isinstance(raw, dict):
        return {str(key): value for key, value in raw.items() if isinstance(value, dict)}
    if not isinstance(raw, list):
        return {}
    indexed: dict[str, dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        move = item.get("move")
        continuation = item.get("continuation")
        if move and isinstance(continuation, dict):
            indexed[str(move)] = continuation
    return indexed


def internal_monitor_strategy_frames(payload: dict[str, Any]) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    for terminal in payload.get("terminal_evidence") or []:
        terminal_id = str(terminal.get("terminal_id") or "unknown_terminal")
        for idx, example in enumerate(terminal.get("examples_of_firing_states") or []):
            state_id = str(example.get("state_id") or f"monitor_state_{idx}")
            frame = _base_frame(
                frame_id=f"ssf.monitor.{terminal_id}.{state_id}.{idx}",
                state_id=state_id,
                fen=example.get("fen"),
                source_stage=example.get("stage"),
                active_landmark_label=example.get("active_landmark_label"),
                frame_type="broader_krk_strategy_candidate",
                candidate_id=f"candidate.strategy_monitor.{terminal_id}",
                stage7_challenge_row=example.get("stage") == "stage7",
                label_semantics="internal_monitor_context_not_runtime_route",
            )
            frame["candidate_strategy_family"] = terminal_id
            frame["internal_monitor_terms"] = [terminal_id]
            frame["source_terms"] = list(terminal.get("missing_companion_terms") or [])
            frame["sequence_evidence"] = {
                "associated_outcome": example.get("outcome"),
                "candidate_maturity": terminal.get("candidate_maturity"),
                "failure_precision": terminal.get("failure_precision"),
                "stage7_only": terminal.get("stage7_only"),
                "source_artifact": str(INTERNAL_TERMINAL_EVIDENCE),
            }
            frames.append(frame)
    return frames


def build_frames_payload() -> dict[str, Any]:
    capacity = _load(CAPACITY_FRAMES)
    ranked = _load(RANKED_FRAMES)
    post_activation = _load(POST_ACTIVATION_AUDIT)
    internal = _load(INTERNAL_TERMINAL_EVIDENCE)
    spec = _load(FRAME_SPEC)
    frames = (
        capacity_candidate_frames(list(capacity.get("rows") or []))
        + proposal_candidate_frames(list(ranked.get("rows") or []))
        + progress_window_candidate_frames(post_activation)
        + internal_monitor_strategy_frames(internal)
    )
    summary = summarize_frames(frames)
    return {
        "schema_version": "krk_strategy_sequence_candidate_frames.v1",
        "causal_status": "non_causal_frame_population",
        **_runtime_false_block(),
        "source_artifacts": [
            str(CAPACITY_FRAMES),
            str(RANKED_FRAMES),
            str(POST_ACTIVATION_AUDIT),
            str(INTERNAL_TERMINAL_EVIDENCE),
            str(FRAME_SPEC),
        ],
        "frame_spec_version": spec.get("schema_version"),
        "summary": summary,
        "frames": frames,
        "decision": {
            "status": "strategy_sequence_frames_populated_non_causal",
            "runtime_sandbox_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "recommended_next_step": "probe_strategy_sequence_candidate_frame_quality_v1",
        },
    }


def summarize_frames(frames: list[dict[str, Any]]) -> dict[str, Any]:
    stage7_count = sum(1 for frame in frames if frame.get("stage7_challenge_row"))
    selector_rows = [frame for frame in frames if frame.get("usable_for_selector_training")]
    generator_rows = [frame for frame in frames if frame.get("usable_for_candidate_generation_training")]
    return {
        "frame_count": len(frames),
        "state_count": len({frame.get("state_id") for frame in frames}),
        "frame_type_counts": dict(sorted(Counter(frame.get("frame_type") for frame in frames).items())),
        "source_stage_counts": dict(sorted(Counter(frame.get("source_stage") for frame in frames).items())),
        "candidate_strategy_family_counts": dict(
            sorted(Counter(frame.get("candidate_strategy_family") for frame in frames).items())
        ),
        "stage7_challenge_row_count": stage7_count,
        "readiness_training_stage7_row_count": sum(
            1 for frame in frames
            if frame.get("stage7_challenge_row")
            and (
                frame.get("usable_for_selector_training")
                or frame.get("usable_for_candidate_generation_training")
            )
        ),
        "selector_training_row_count": len(selector_rows),
        "candidate_generation_training_row_count": len(generator_rows),
        "capacity_evidence_row_count": sum(1 for frame in frames if frame.get("capacity_evidence")),
        "ownership_evidence_row_count": sum(1 for frame in frames if frame.get("ownership_evidence")),
        "sequence_evidence_row_count": sum(1 for frame in frames if frame.get("sequence_evidence")),
        "internal_monitor_row_count": sum(1 for frame in frames if frame.get("internal_monitor_terms")),
    }


def build_quality_payload(frames_payload: dict[str, Any]) -> dict[str, Any]:
    frames = list(frames_payload.get("frames") or [])
    protected = [frame for frame in frames if not frame.get("stage7_challenge_row")]
    stage7 = [frame for frame in frames if frame.get("stage7_challenge_row")]
    label_counts = Counter(frame.get("label_semantics") for frame in frames)
    capacity_positive = [
        frame for frame in protected
        if (frame.get("capacity_evidence") or {}).get("capacity_label") == "positive_capacity"
    ]
    visible_provider_proposals = [
        frame for frame in protected
        if frame.get("label_semantics") == "visible_provider_proposal_context_not_capacity_or_ownership_label"
    ]
    sequence_candidates = [
        frame for frame in frames
        if frame.get("frame_type") == "candidate_move_hypothesis"
    ]
    quality = {
        "schema_version": "krk_strategy_sequence_candidate_frame_quality.v1",
        "causal_status": "non_causal_frame_quality_probe",
        **_runtime_false_block(),
        "source_artifacts": [str(OUT_FRAMES_JSON)],
        "summary": {
            "total_frames": len(frames),
            "protected_frame_count": len(protected),
            "stage7_challenge_frame_count": len(stage7),
            "stage7_readiness_training_row_count": frames_payload["summary"].get(
                "readiness_training_stage7_row_count"
            ),
            "label_semantics_counts": dict(sorted(label_counts.items())),
            "protected_positive_capacity_candidate_count": len(capacity_positive),
            "protected_visible_provider_proposal_count": len(visible_provider_proposals),
            "sequence_candidate_count": len(sequence_candidates),
            "sequence_candidate_mate_count": sum(
                1 for frame in sequence_candidates
                if ((frame.get("sequence_evidence") or {}).get("continuation_h40") or {}).get("result")
                == "mate"
            ),
        },
        "quality_checks": {
            "capacity_not_selector_label": all(
                frame.get("usable_for_selector_training") is False
                for frame in frames
                if frame.get("label_semantics") == "capacity_evidence_not_ownership_label"
            ),
            "stage7_excluded_from_training_readiness": frames_payload["summary"].get(
                "readiness_training_stage7_row_count"
            )
            == 0,
            "runtime_flags_false": all(frames_payload.get(key) is False for key in RUNTIME_FALSE_KEYS),
            "sequence_candidates_all_heldout": all(
                frame.get("stage7_challenge_row") for frame in sequence_candidates
            ),
        },
        "decision": {
            "status": "frame_quality_probe_supports_next_sequence_candidate_benchmark",
            "runtime_sandbox_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "recommended_next_step": "benchmark_candidate_frame_sources_before_runtime",
        },
    }
    if not all(quality["quality_checks"].values()):
        quality["decision"]["status"] = "frame_quality_blocked"
        quality["decision"]["recommended_next_step"] = "fix_frame_semantics_before_any_probe"
    return quality


def _write_frames_md(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK StrategySequenceCandidateFrame Population v1",
        "",
        "This artifact materializes replay-free, non-causal candidate frames for the KRK strategy/sequence control plane.",
        "",
        "## Summary",
        "",
        f"- frame_count: {summary['frame_count']}",
        f"- state_count: {summary['state_count']}",
        f"- frame_type_counts: `{summary['frame_type_counts']}`",
        f"- source_stage_counts: `{summary['source_stage_counts']}`",
        f"- stage7_challenge_row_count: {summary['stage7_challenge_row_count']}",
        f"- readiness_training_stage7_row_count: {summary['readiness_training_stage7_row_count']}",
        f"- selector_training_row_count: {summary['selector_training_row_count']}",
        f"- candidate_generation_training_row_count: {summary['candidate_generation_training_row_count']}",
        "",
        "## Semantics",
        "",
        "- Capacity evidence remains candidate-generation evidence, not ownership selection.",
        "- Visible proposal frames preserve normal-routing context, not final selector authority.",
        "- Progress-window candidate moves are held-out Stage 7 challenge evidence.",
        "- Internal-monitor strategy candidates remain non-causal control-plane evidence.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        f"- runtime_sandbox_allowed: `{payload['decision']['runtime_sandbox_allowed']}`",
    ]
    (ROOT / OUT_FRAMES_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_quality_md(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    checks = payload["quality_checks"]
    lines = [
        "# KRK StrategySequenceCandidateFrame Quality Probe v1",
        "",
        "This replay-free quality probe checks whether populated frames preserve the candidate-generation / selection split.",
        "",
        "## Summary",
        "",
        f"- total_frames: {summary['total_frames']}",
        f"- protected_frame_count: {summary['protected_frame_count']}",
        f"- stage7_challenge_frame_count: {summary['stage7_challenge_frame_count']}",
        f"- stage7_readiness_training_row_count: {summary['stage7_readiness_training_row_count']}",
        f"- protected_positive_capacity_candidate_count: {summary['protected_positive_capacity_candidate_count']}",
        f"- protected_visible_provider_proposal_count: {summary['protected_visible_provider_proposal_count']}",
        f"- sequence_candidate_count: {summary['sequence_candidate_count']}",
        f"- sequence_candidate_mate_count: {summary['sequence_candidate_mate_count']}",
        "",
        "## Quality Checks",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in checks.items())
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- status: `{payload['decision']['status']}`",
            f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
            f"- runtime_sandbox_allowed: `{payload['decision']['runtime_sandbox_allowed']}`",
        ]
    )
    (ROOT / OUT_QUALITY_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    frames = build_frames_payload()
    quality = build_quality_payload(frames)
    _write_json(OUT_FRAMES_JSON, frames)
    _write_frames_md(frames)
    _write_json(OUT_QUALITY_JSON, quality)
    _write_quality_md(quality)
    print(json.dumps({"frames": frames["summary"], "decision": quality["decision"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
