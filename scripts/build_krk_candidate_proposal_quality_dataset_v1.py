#!/usr/bin/env python3
"""Build non-causal KRK candidate proposal quality dataset v1."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OBSERVATION_SOURCE = Path(
    "reports/strategy_arbitration/"
    "krk_candidate_generation_observation_broadened_sample_v1.json"
)
ANNOTATION_SOURCE = Path("reports/strategy_arbitration/krk_candidate_move_capacity_annotation_v2.json")
CAPACITY_SOURCE = Path("reports/krk_protected_provider_coverage_frames_v0.json")
LABEL_SOURCE = Path("reports/strategy_arbitration/krk_candidate_move_capacity_labels_v1.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_candidate_proposal_quality_dataset_v1.json")
OUT_MD = Path("reports/strategy_arbitration/krk_candidate_proposal_quality_dataset_v1.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _candidate_move_annotation_index(
    capacity_payload: dict[str, Any],
    label_payload: dict[str, Any],
) -> dict[tuple[str, str], str]:
    index: dict[tuple[str, str], str] = {}
    rows: list[dict[str, Any]] = []
    for row in capacity_payload.get("rows") or []:
        if not isinstance(row, dict) or row.get("stage7_challenge_row"):
            continue
        rows.append(
            {
                "fen": row.get("fen"),
                "move": row.get("forced_first_move"),
                "capacity_label": row.get("capacity_label"),
            }
        )
    for label in label_payload.get("labels") or []:
        if not isinstance(label, dict) or label.get("source_stage") == "stage7":
            continue
        rows.append(
            {
                "fen": label.get("fen"),
                "move": label.get("forced_first_move"),
                "capacity_label": label.get("capacity_label"),
            }
        )
    labels_by_key: dict[tuple[str, str], set[str]] = {}
    for row in rows:
        fen = str(row.get("fen") or "")
        move = str(row.get("move") or "")
        label = str(row.get("capacity_label") or "")
        if not fen or not move or not label:
            continue
        labels_by_key.setdefault((fen, move), set()).add(label)
    for key, labels in labels_by_key.items():
        if labels == {"positive_capacity"}:
            index[key] = "positive_capacity"
        elif labels == {"negative_capacity"}:
            index[key] = "negative_capacity"
        else:
            index[key] = "ambiguous_capacity"
    return index


def _term_count(frame: dict[str, Any], key: str) -> int:
    value = frame.get(key)
    return len(value) if isinstance(value, list) else 0


def _capacity_kind(frame: dict[str, Any], move_index: dict[tuple[str, str], str]) -> str:
    if frame.get("protected_status") == "held_out_stage7_challenge":
        return "held_out_challenge"
    if frame.get("candidate_source") == "candidate_move_frame":
        key = (
            str(frame.get("state_fen") or ""),
            str(frame.get("move_uci") or frame.get("move_id") or ""),
        )
        kind = move_index.get(key)
        if kind in {"positive_capacity", "negative_capacity", "ambiguous_capacity"}:
            return kind
        return "unknown_capacity"
    return str(frame.get("capacity_evidence_kind") or "unknown_capacity")


def _quality_bucket(row: dict[str, Any]) -> str:
    if row["capacity_evidence_kind"] == "positive_capacity":
        return "known_positive"
    if row["capacity_evidence_kind"] == "negative_capacity":
        return "known_negative"
    if row["capacity_evidence_kind"] == "held_out_challenge":
        return "held_out_challenge"
    if row["visible_term_density"] == 0:
        return "unknown_low_information"
    if row["safety_term_count"] > 0 or row["post_move_term_count"] > 0:
        return "unknown_with_visible_terms"
    return "unknown_unqualified"


def build_payload(
    observation_payload: dict[str, Any] | None = None,
    annotation_payload: dict[str, Any] | None = None,
    capacity_payload: dict[str, Any] | None = None,
    label_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    observation_payload = observation_payload or _load(OBSERVATION_SOURCE)
    annotation_payload = annotation_payload or _load(ANNOTATION_SOURCE)
    capacity_payload = capacity_payload or _load(CAPACITY_SOURCE)
    label_payload = label_payload or _load(LABEL_SOURCE)
    move_index = _candidate_move_annotation_index(capacity_payload, label_payload)
    rows: list[dict[str, Any]] = []
    counts_by_source: Counter[str] = Counter()
    counts_by_bucket: Counter[str] = Counter()
    counts_by_capacity: Counter[str] = Counter()
    quality_training_rows = 0
    stage7_rows = 0
    for case in observation_payload.get("cases") or []:
        observation = ((case.get("enabled_decision") or {}).get("observation") or {})
        selected_move = observation.get("selected_move_before_observation")
        selected_provider = observation.get("selected_provider_before_observation")
        for index, frame in enumerate(observation.get("frames") or [], start=1):
            if not isinstance(frame, dict):
                continue
            move = frame.get("move_uci") or frame.get("move_id")
            source = str(frame.get("candidate_source") or "unknown")
            capacity = _capacity_kind(frame, move_index)
            row = {
                "schema_version": "krk_candidate_proposal_quality_row.v1",
                "causal_status": "non_causal_quality_dataset_row",
                "row_id": f"{case.get('case_id')}.{index:03d}",
                "case_id": case.get("case_id"),
                "state_id": case.get("state_id"),
                "fen": frame.get("state_fen") or case.get("fen"),
                "source_stage": case.get("source_stage"),
                "active_landmark_label": case.get("active_landmark_label"),
                "stage7_challenge_row": bool(case.get("held_out")),
                "candidate_source": source,
                "provider_id": frame.get("provider_id"),
                "move_uci": move,
                "selected_move_before_observation": selected_move,
                "selected_provider_before_observation": selected_provider,
                "selected_move_relation": "same_as_selected"
                if move == selected_move
                else "distinct_from_selected",
                "provider_relation": "same_as_selected_provider"
                if frame.get("provider_id") == selected_provider
                else "distinct_or_no_provider",
                "protected_status": frame.get("protected_status"),
                "capacity_evidence_kind": capacity,
                "source_term_count": _term_count(frame, "source_terms"),
                "move_shape_term_count": _term_count(frame, "move_shape_terms"),
                "post_move_term_count": _term_count(frame, "post_move_terms"),
                "safety_term_count": _term_count(frame, "safety_terms"),
                "visible_term_density": (
                    _term_count(frame, "source_terms")
                    + _term_count(frame, "move_shape_terms")
                    + _term_count(frame, "post_move_terms")
                    + _term_count(frame, "safety_terms")
                ),
                "direct_request": frame.get("direct_request"),
                "score_delta": frame.get("score_delta"),
                "usable_for_selector_training": False,
                "usable_for_quality_probe": (
                    not bool(case.get("held_out"))
                    and capacity in {"positive_capacity", "negative_capacity"}
                ),
                "label_semantics": "capacity_or_quality_evidence_not_ownership_label",
            }
            row["quality_bucket"] = _quality_bucket(row)
            rows.append(row)
            counts_by_source[source] += 1
            counts_by_bucket[row["quality_bucket"]] += 1
            counts_by_capacity[capacity] += 1
            if row["usable_for_quality_probe"]:
                quality_training_rows += 1
            if row["stage7_challenge_row"]:
                stage7_rows += 1

    status = (
        "candidate_proposal_quality_dataset_ready_for_probe"
        if quality_training_rows >= 10
        else "candidate_proposal_quality_dataset_underpowered"
    )
    return {
        "schema_version": "krk_candidate_proposal_quality_dataset.v1",
        "causal_status": "non_causal_quality_dataset",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            str(OBSERVATION_SOURCE),
            str(ANNOTATION_SOURCE),
            str(CAPACITY_SOURCE),
            str(LABEL_SOURCE),
        ],
        "summary": {
            "row_count": len(rows),
            "row_count_by_candidate_source": dict(sorted(counts_by_source.items())),
            "row_count_by_quality_bucket": dict(sorted(counts_by_bucket.items())),
            "row_count_by_capacity_evidence": dict(sorted(counts_by_capacity.items())),
            "quality_probe_row_count": quality_training_rows,
            "stage7_challenge_row_count": stage7_rows,
            "stage7_readiness_training_row_count": 0,
        },
        "rows": rows,
        "decision": {
            "status": status,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": "probe_candidate_proposal_quality_axes"
            if quality_training_rows >= 10
            else "collect_targeted_quality_labels_or_review_underpowering",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Candidate Proposal Quality Dataset v1",
        "",
        "This dataset joins observation-only candidate frames with non-causal capacity/quality annotations. It does not train or select.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
        f"- row_count: {summary['row_count']}",
        f"- row_count_by_candidate_source: `{summary['row_count_by_candidate_source']}`",
        f"- row_count_by_quality_bucket: `{summary['row_count_by_quality_bucket']}`",
        f"- row_count_by_capacity_evidence: `{summary['row_count_by_capacity_evidence']}`",
        f"- quality_probe_row_count: {summary['quality_probe_row_count']}",
        f"- stage7_challenge_row_count: {summary['stage7_challenge_row_count']}",
        "",
        "## Boundary",
        "",
        "Rows are capacity/quality evidence, not selector labels. Stage 7 rows are held-out challenge rows only.",
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
