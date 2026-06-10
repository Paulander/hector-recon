#!/usr/bin/env python3
"""Build ranked KRK StrategyProposalFrame rows from existing control-plane frames."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FILTERED_FRAMES = Path("reports/krk_control_plane_filtered_frames_v0.json")
PROBE_REVIEW = Path("reports/krk_normalized_selector_probe_review_v1.json")
OUT_JSON = Path("reports/krk_ranked_strategy_proposal_frames_v1.json")
OUT_MD = Path("reports/krk_ranked_strategy_proposal_frames_v1.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _provider_family(provider_id: str | None) -> str | None:
    if not provider_id:
        return None
    if "stage0_basin" in provider_id:
        return "stage0_basin"
    if "drive_to_edge" in provider_id:
        return "drive_to_edge"
    if "edge_trap" in provider_id:
        return "edge_trap"
    if "fence_established" in provider_id:
        return "fence_established"
    if "box_shrink" in provider_id:
        return "box_shrink"
    if "mate_in_1" in provider_id:
        return "mate_in_1"
    return provider_id.split(".")[-1]


def _provider_maturity(provider_id: str | None, source_stage: str | None) -> str:
    family = _provider_family(provider_id)
    if family == "stage0_basin":
        return "foundation_frozen"
    if family in {"edge_trap", "fence_established"}:
        return "validated_low_plasticity"
    if family == "drive_to_edge":
        return "settling_medium_plasticity" if source_stage == "stage7" else "validated_low_plasticity"
    if family == "box_shrink":
        return "quarantined_no_plasticity"
    return "unknown"


def _label_from_outcome(outcome: str) -> str | None:
    if outcome == "mate":
        return "frame_success"
    if outcome == "max_plies":
        return "frame_failure"
    return None


def _global_ranked(proposals: list[dict[str, Any]]) -> list[tuple[int, dict[str, Any]]]:
    def score(item: dict[str, Any]) -> float:
        value = item.get("raw_score")
        return float(value) if isinstance(value, (int, float)) else float("-inf")

    return list(enumerate(sorted(proposals, key=score, reverse=True), start=1))


def build_dataset() -> dict[str, Any]:
    frames_payload = _load_json(FILTERED_FRAMES)
    review = _load_json(PROBE_REVIEW)

    if frames_payload.get("causal_status") != "non_causal_filtered_frame_export":
        raise ValueError("source frames must remain non-causal")
    if review.get("decision", {}).get("status") != "normalized_selector_signal_promising_more_ranked_frames_required":
        raise ValueError("probe review must request ranked proposal frames")

    rows: list[dict[str, Any]] = []
    for frame in frames_payload.get("frames") or []:
        proposals = frame.get("strategy_proposal_frames") or []
        if not proposals:
            continue
        outcome = str(frame.get("outcome") or "unknown")
        frame_label = _label_from_outcome(outcome)
        source_stage = frame.get("source_stage")
        stage7_challenge = source_stage == "stage7"
        for global_rank, proposal in _global_ranked(proposals):
            provider_id = proposal.get("provider_id")
            family = _provider_family(provider_id)
            row = {
                "schema_version": "krk_ranked_strategy_proposal_frame.v1",
                "frame_id": frame.get("frame_id"),
                "state_id": frame.get("state_id"),
                "fen": frame.get("fen"),
                "source_stage": source_stage,
                "active_landmark_label": frame.get("active_landmark_label"),
                "provider_id": provider_id,
                "skill_id": proposal.get("skill_id") or provider_id,
                "provider_family": family,
                "provider_maturity": _provider_maturity(provider_id, source_stage),
                "provider_version": proposal.get("provider_version"),
                "move_uci": proposal.get("move_uci"),
                "raw_score": proposal.get("raw_score"),
                "global_raw_score_rank": global_rank,
                "provider_local_rank": proposal.get("provider_local_rank"),
                "normalized_score": proposal.get("normalized_score"),
                "source_terms": proposal.get("source_terms") or [],
                "role_licenses": proposal.get("role_licenses") or [],
                "move_shape_terms": proposal.get("move_shape_terms") or [],
                "post_move_terms": proposal.get("post_move_terms") or [],
                "safety_terms": proposal.get("safety_terms") or [],
                "frame_outcome": outcome,
                "frame_label": frame_label,
                "label_channel": "frame_outcome_context_only",
                "usable_for_training": bool(frame_label and not stage7_challenge),
                "stage7_challenge_row": stage7_challenge,
                "causal_status": "non_causal",
            }
            rows.append(row)

    summary = {
        "row_count": len(rows),
        "frame_count": len({row["frame_id"] for row in rows}),
        "usable_training_row_count": sum(1 for row in rows if row["usable_for_training"]),
        "stage7_challenge_row_count": sum(1 for row in rows if row["stage7_challenge_row"]),
        "outcome_counts": dict(Counter(str(row["frame_outcome"]) for row in rows)),
        "label_counts": dict(Counter(str(row["frame_label"]) for row in rows)),
        "provider_family_counts": dict(Counter(str(row["provider_family"]) for row in rows)),
        "source_stage_counts": dict(Counter(str(row["source_stage"]) for row in rows)),
        "rows_missing_provider_local_rank": sum(1 for row in rows if row["provider_local_rank"] is None),
        "rows_missing_normalized_score": sum(1 for row in rows if row["normalized_score"] is None),
    }
    dataset = {
        "schema_version": "krk_ranked_strategy_proposal_frames.v1",
        "causal_status": "non_causal_ranked_frame_dataset",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(FILTERED_FRAMES), str(PROBE_REVIEW)],
        "rows": rows,
        "summary": summary,
        "decision": {
            "status": "ranked_strategy_proposal_frames_exported",
            "recommended_next_step": "probe_ranked_strategy_proposal_frames_v1",
            "runtime_test_allowed_next": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_dataset(dataset)
    return dataset


def validate_dataset(dataset: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if dataset.get(key) is not False:
            raise ValueError(f"{key} must be false")
    for row in dataset.get("rows") or []:
        if row.get("causal_status") != "non_causal":
            raise ValueError("all ranked proposal rows must remain non-causal")
        if row.get("stage7_challenge_row") and row.get("usable_for_training"):
            raise ValueError("Stage7 challenge rows must not be training rows")


def render_markdown(dataset: dict[str, Any]) -> str:
    lines = [
        "# KRK Ranked Strategy Proposal Frames v1",
        "",
        "This replay-free dataset exports existing `StrategyProposalFrame` records with ranks and normalized scores. Frame labels are context only; they do not make each proposal a positive owner.",
        "",
        "## Summary",
        "",
    ]
    for key, value in dataset["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Status: `{dataset['decision']['status']}`",
            f"- Recommended next step: `{dataset['decision']['recommended_next_step']}`",
            f"- Runtime test allowed next: `{dataset['decision']['runtime_test_allowed_next']}`",
            f"- Stage 7 promotion allowed: `{dataset['decision']['stage7_promotion_allowed']}`",
            f"- Stage 8 training allowed: `{dataset['decision']['stage8_training_allowed']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    dataset = build_dataset()
    (ROOT / OUT_JSON).write_text(json.dumps(dataset, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(dataset), encoding="utf-8")
    print(json.dumps(dataset["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
