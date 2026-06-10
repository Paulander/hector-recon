#!/usr/bin/env python3
"""Replay-free capacity annotation review for observed CandidateMoveFrame rows."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OBSERVATION_SOURCE = Path(
    "reports/strategy_arbitration/"
    "krk_candidate_generation_observation_broadened_sample_v1.json"
)
CAPACITY_SOURCE = Path("reports/krk_protected_provider_coverage_frames_v0.json")
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_candidate_move_capacity_annotation_v1.json"
)
OUT_MD = Path("reports/strategy_arbitration/krk_candidate_move_capacity_annotation_v1.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _capacity_index(capacity_payload: dict[str, Any]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    index: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in capacity_payload.get("rows") or []:
        if not isinstance(row, dict) or not row.get("fen") or not row.get("forced_first_move"):
            continue
        if row.get("stage7_challenge_row"):
            continue
        index[(str(row["fen"]), str(row["forced_first_move"]))].append(row)
    return dict(index)


def _iter_candidate_move_frames(observation_payload: dict[str, Any]) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    for case in observation_payload.get("cases") or []:
        observation = ((case.get("enabled_decision") or {}).get("observation") or {})
        for frame in observation.get("frames") or []:
            if not isinstance(frame, dict):
                continue
            if frame.get("candidate_source") != "candidate_move_frame":
                continue
            frames.append(
                {
                    **frame,
                    "_case_id": case.get("case_id"),
                    "_source_stage": case.get("source_stage"),
                    "_held_out": case.get("held_out"),
                }
            )
    return frames


def _annotation_for(
    frame: dict[str, Any],
    capacity_index: dict[tuple[str, str], list[dict[str, Any]]],
) -> dict[str, Any]:
    move = str(frame.get("move_uci") or frame.get("move_id") or "")
    fen = str(frame.get("state_fen") or "")
    rows = capacity_index.get((fen, move), [])
    labels = sorted({str(row.get("capacity_label") or "unknown_capacity") for row in rows})
    providers = sorted({str(row.get("provider_id") or row.get("provider_family")) for row in rows})
    forced_results = sorted({str(row.get("forced_result") or "unknown") for row in rows})
    if not rows:
        kind = "unannotated"
    elif labels == ["positive_capacity"]:
        kind = "positive_capacity"
    elif labels == ["negative_capacity"]:
        kind = "negative_capacity"
    else:
        kind = "ambiguous_capacity"
    return {
        "annotation_kind": kind,
        "matched_capacity_row_count": len(rows),
        "matched_capacity_labels": labels,
        "matched_provider_ids": providers,
        "matched_forced_results": forced_results,
        "annotation_source": str(CAPACITY_SOURCE) if rows else None,
        "label_semantics": "offline_forced_capacity_not_runtime_ownership_label"
        if rows
        else "unannotated_candidate_move",
        "usable_for_selector_training": False,
    }


def build_payload(
    observation_payload: dict[str, Any] | None = None,
    capacity_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    observation_payload = observation_payload or _load(OBSERVATION_SOURCE)
    capacity_payload = capacity_payload or _load(CAPACITY_SOURCE)
    capacity_index = _capacity_index(capacity_payload)
    frames = _iter_candidate_move_frames(observation_payload)

    annotation_counts: Counter[str] = Counter()
    stage_counts: Counter[str] = Counter()
    annotated_by_stage: dict[str, Counter[str]] = defaultdict(Counter)
    matched_providers: Counter[str] = Counter()
    examples: list[dict[str, Any]] = []
    heldout_candidate_move_count = 0

    for frame in frames:
        stage = str(frame.get("_source_stage") or "unknown")
        if frame.get("_held_out"):
            heldout_candidate_move_count += 1
        annotation = _annotation_for(frame, capacity_index)
        kind = annotation["annotation_kind"]
        annotation_counts[kind] += 1
        stage_counts[stage] += 1
        annotated_by_stage[stage][kind] += 1
        for provider_id in annotation.get("matched_provider_ids") or []:
            matched_providers[provider_id] += 1
        if kind != "unannotated" and len(examples) < 12:
            examples.append(
                {
                    "case_id": frame.get("_case_id"),
                    "source_stage": stage,
                    "move_uci": frame.get("move_uci") or frame.get("move_id"),
                    "state_fen": frame.get("state_fen"),
                    **annotation,
                }
            )

    total = len(frames)
    annotated_count = total - annotation_counts.get("unannotated", 0)
    protected_total = total - heldout_candidate_move_count
    protected_annotated_count = sum(
        count
        for stage, counter in annotated_by_stage.items()
        if stage != "stage7"
        for kind, count in counter.items()
        if kind != "unannotated"
    )
    protected_annotation_recall = (
        protected_annotated_count / protected_total if protected_total else 0.0
    )
    status = (
        "candidate_move_capacity_annotation_partial_selector_blocked"
        if protected_annotation_recall < 0.5
        else "candidate_move_capacity_annotation_review_ready"
    )
    return {
        "schema_version": "krk_candidate_move_capacity_annotation.v1",
        "causal_status": "non_causal_replay_free_capacity_annotation",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": {
            "observation_frames": str(OBSERVATION_SOURCE),
            "capacity_labels": str(CAPACITY_SOURCE),
        },
        "summary": {
            "candidate_move_frame_count": total,
            "heldout_stage7_candidate_move_count": heldout_candidate_move_count,
            "stage7_readiness_training_row_count": 0,
            "annotated_candidate_move_count": annotated_count,
            "protected_candidate_move_count": protected_total,
            "protected_annotated_candidate_move_count": protected_annotated_count,
            "protected_annotation_recall": protected_annotation_recall,
            "annotation_counts": dict(sorted(annotation_counts.items())),
            "annotation_counts_by_stage": {
                stage: dict(sorted(counter.items()))
                for stage, counter in sorted(annotated_by_stage.items())
            },
            "candidate_move_count_by_stage": dict(sorted(stage_counts.items())),
            "matched_provider_ids": dict(sorted(matched_providers.items())),
        },
        "examples": examples,
        "interpretation": {
            "replay_free_annotation_possible": annotated_count > 0,
            "annotation_coverage_sufficient_for_selector_review": protected_annotation_recall >= 0.5,
            "capacity_labels_remain_offline_only": True,
            "capacity_labels_are_not_ownership_labels": True,
            "stage7_excluded_from_readiness": True,
        },
        "decision": {
            "status": status,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": "bounded_candidate_move_capacity_label_manifest"
            if protected_annotation_recall < 0.5
            else "candidate_move_capacity_quality_review",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK CandidateMoveFrame Capacity Annotation v1",
        "",
        "This replay-free review annotates observed CandidateMoveFrame rows against existing protected forced-capacity evidence. It is not selector training.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- guardrails_allowed: `{payload['decision']['guardrails_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
        f"- candidate_move_frame_count: {summary['candidate_move_frame_count']}",
        f"- protected_candidate_move_count: {summary['protected_candidate_move_count']}",
        f"- protected_annotated_candidate_move_count: {summary['protected_annotated_candidate_move_count']}",
        f"- protected_annotation_recall: `{summary['protected_annotation_recall']:.3f}`",
        f"- annotation_counts: `{summary['annotation_counts']}`",
        f"- annotation_counts_by_stage: `{summary['annotation_counts_by_stage']}`",
        f"- matched_provider_ids: `{summary['matched_provider_ids']}`",
        "",
        "## Interpretation",
        "",
        f"- replay_free_annotation_possible: `{payload['interpretation']['replay_free_annotation_possible']}`",
        f"- annotation_coverage_sufficient_for_selector_review: `{payload['interpretation']['annotation_coverage_sufficient_for_selector_review']}`",
        f"- capacity_labels_are_not_ownership_labels: `{payload['interpretation']['capacity_labels_are_not_ownership_labels']}`",
        "",
        "## Boundary",
        "",
        "The next step, if pursued, is a bounded non-causal label manifest for candidate-move capacity coverage. This artifact does not authorize selection or routing.",
    ]
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
