#!/usr/bin/env python3
"""Merge protected capacity labels into CandidateMoveFrame annotation v2."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.annotate_krk_candidate_move_capacity_v1 import (  # noqa: E402
    CAPACITY_SOURCE,
    OBSERVATION_SOURCE,
    _iter_candidate_move_frames,
)


NEW_LABEL_SOURCE = Path("reports/strategy_arbitration/krk_candidate_move_capacity_labels_v1.json")
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_candidate_move_capacity_annotation_v2.json"
)
OUT_MD = Path("reports/strategy_arbitration/krk_candidate_move_capacity_annotation_v2.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _capacity_index(
    capacity_payload: dict[str, Any],
    label_payload: dict[str, Any],
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    index: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in capacity_payload.get("rows") or []:
        if not isinstance(row, dict) or row.get("stage7_challenge_row"):
            continue
        if not row.get("fen") or not row.get("forced_first_move"):
            continue
        index[(str(row["fen"]), str(row["forced_first_move"]))].append(
            {
                "capacity_label": row.get("capacity_label"),
                "result": row.get("forced_result"),
                "provider_id": row.get("provider_id"),
                "source": str(CAPACITY_SOURCE),
                "label_semantics": "provider_forced_capacity_not_runtime_ownership_label",
            }
        )
    for label in label_payload.get("labels") or []:
        if not isinstance(label, dict):
            continue
        if label.get("source_stage") == "stage7" or label.get("stage7_training_row"):
            continue
        if not label.get("fen") or not label.get("forced_first_move"):
            continue
        index[(str(label["fen"]), str(label["forced_first_move"]))].append(
            {
                "capacity_label": label.get("capacity_label"),
                "result": label.get("result"),
                "provider_id": "candidate_move_forced_first_move",
                "source": str(NEW_LABEL_SOURCE),
                "label_semantics": label.get("label_semantics"),
            }
        )
    return dict(index)


def _kind(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "unannotated"
    labels = sorted({str(row.get("capacity_label") or "unknown") for row in rows})
    if labels == ["positive_capacity"]:
        return "positive_capacity"
    if labels == ["negative_capacity"]:
        return "negative_capacity"
    return "ambiguous_capacity"


def build_payload(
    observation_payload: dict[str, Any] | None = None,
    capacity_payload: dict[str, Any] | None = None,
    label_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    observation_payload = observation_payload or _load(OBSERVATION_SOURCE)
    capacity_payload = capacity_payload or _load(CAPACITY_SOURCE)
    label_payload = label_payload or _load(NEW_LABEL_SOURCE)
    index = _capacity_index(capacity_payload, label_payload)
    frames = _iter_candidate_move_frames(observation_payload)
    counts: Counter[str] = Counter()
    counts_by_stage: dict[str, Counter[str]] = defaultdict(Counter)
    counts_by_source: Counter[str] = Counter()
    examples: list[dict[str, Any]] = []
    heldout_count = 0
    for frame in frames:
        stage = str(frame.get("_source_stage") or "unknown")
        if frame.get("_held_out"):
            heldout_count += 1
        key = (str(frame.get("state_fen") or ""), str(frame.get("move_uci") or frame.get("move_id") or ""))
        rows = index.get(key, [])
        kind = _kind(rows)
        counts[kind] += 1
        counts_by_stage[stage][kind] += 1
        for row in rows:
            counts_by_source[str(row.get("source") or "unknown")] += 1
        if rows and len(examples) < 16:
            examples.append(
                {
                    "case_id": frame.get("_case_id"),
                    "source_stage": stage,
                    "move_uci": key[1],
                    "annotation_kind": kind,
                    "matched_sources": sorted({str(row.get("source")) for row in rows}),
                    "matched_capacity_labels": sorted(
                        {str(row.get("capacity_label")) for row in rows}
                    ),
                    "matched_results": sorted({str(row.get("result")) for row in rows}),
                }
            )

    total = len(frames)
    annotated = total - counts.get("unannotated", 0)
    protected_total = total - heldout_count
    protected_annotated = sum(
        count
        for stage, counter in counts_by_stage.items()
        if stage != "stage7"
        for kind, count in counter.items()
        if kind != "unannotated"
    )
    recall = protected_annotated / protected_total if protected_total else 0.0
    status = (
        "candidate_move_capacity_annotation_improved_but_selector_blocked"
        if recall < 0.5
        else "candidate_move_capacity_annotation_review_ready"
    )
    return {
        "schema_version": "krk_candidate_move_capacity_annotation.v2",
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
            "existing_capacity": str(CAPACITY_SOURCE),
            "new_candidate_move_labels": str(NEW_LABEL_SOURCE),
        },
        "summary": {
            "candidate_move_frame_count": total,
            "heldout_stage7_candidate_move_count": heldout_count,
            "stage7_readiness_training_row_count": 0,
            "annotated_candidate_move_count": annotated,
            "protected_candidate_move_count": protected_total,
            "protected_annotated_candidate_move_count": protected_annotated,
            "protected_annotation_recall": recall,
            "annotation_counts": dict(sorted(counts.items())),
            "annotation_counts_by_stage": {
                stage: dict(sorted(counter.items()))
                for stage, counter in sorted(counts_by_stage.items())
            },
            "matched_annotation_source_counts": dict(sorted(counts_by_source.items())),
        },
        "examples": examples,
        "interpretation": {
            "annotation_coverage_improved": True,
            "annotation_coverage_sufficient_for_selector_review": recall >= 0.5,
            "capacity_labels_are_not_ownership_labels": True,
            "stage7_excluded_from_readiness": True,
        },
        "decision": {
            "status": status,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": "candidate_generation_label_blocker_review"
            if recall < 0.5
            else "candidate_move_capacity_quality_review",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK CandidateMoveFrame Capacity Annotation v2",
        "",
        "This merges the bounded candidate-move capacity label run back into the observation-frame annotation view.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
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
        f"- matched_annotation_source_counts: `{summary['matched_annotation_source_counts']}`",
        "",
        "## Boundary",
        "",
        "The merged labels improve coverage but remain capacity evidence only. They do not authorize selector training or runtime behavior.",
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
