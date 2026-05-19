#!/usr/bin/env python3
"""Build replay-free KRK strategy-owner contrast dataset v0."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FRAMES = Path("reports/krk_control_plane_filtered_frames_with_forced_controls_v0.json")
READINESS = Path("reports/krk_selector_readiness_v2_plan.json")
OUT_JSON = Path("reports/krk_strategy_owner_contrast_dataset_v0.json")
OUT_MD = Path("reports/krk_strategy_owner_contrast_dataset_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _label_result(label: dict[str, Any]) -> str | None:
    return label.get("result") or label.get("playout_result") or label.get("label")


def _provider_family(provider_id: str) -> str:
    if provider_id.startswith("krk.edge_trap"):
        return "edge_trap"
    if provider_id == "krk.stage0_basin":
        return "stage0_basin"
    return provider_id.removeprefix("krk.")


def _proposal_row(proposal: dict[str, Any]) -> dict[str, Any] | None:
    label = proposal.get("known_outcome_label") or {}
    if not isinstance(label, dict):
        return None
    result = _label_result(label)
    provider_id = str(proposal.get("provider_id") or "")
    if not result or not provider_id:
        return None
    return {
        "provider_id": provider_id,
        "provider_family": _provider_family(provider_id),
        "move_uci": proposal.get("move_uci"),
        "result": result,
        "positive": result == "mate",
        "label_source": label.get("source") or (
            "selected_playout" if label.get("selected") is True else "same_move_or_existing_label"
        ),
        "selected": label.get("selected"),
    }


def build_dataset() -> dict[str, Any]:
    frames = _load_json(FRAMES)
    readiness = _load_json(READINESS)
    if frames.get("causal_status") != "non_causal_augmented_frame_export":
        raise ValueError("frames must remain non-causal")
    if readiness.get("causal_status") != "non_causal_design_plan":
        raise ValueError("readiness plan must remain non-causal")
    rows_by_state: dict[str, dict[str, Any]] = {}
    for frame in frames.get("frames") or []:
        proposals = [
            row
            for row in (_proposal_row(proposal) for proposal in frame.get("strategy_proposal_frames") or [])
            if row is not None
        ]
        if len({row["provider_id"] for row in proposals}) < 2 and not any(
            row["positive"] and row["provider_id"] != "krk.stage0_basin" for row in proposals
        ):
            continue
        state_id = str(frame.get("state_id") or "")
        if not state_id:
            continue
        existing = rows_by_state.get(state_id)
        if existing:
            known = {(row["provider_id"], row.get("move_uci"), row["result"]) for row in existing["provider_labels"]}
            for row in proposals:
                key = (row["provider_id"], row.get("move_uci"), row["result"])
                if key not in known:
                    existing["provider_labels"].append(row)
                    known.add(key)
            continue
        stage = str(frame.get("source_stage") or "unknown")
        rows_by_state[state_id] = {
            "schema_version": "krk_strategy_owner_contrast_row.v0",
            "causal_status": "non_causal_contrast_row",
            "state_id": state_id,
            "frame_id": frame.get("frame_id"),
            "source_stage": stage,
            "active_landmark_label": frame.get("active_landmark_label"),
            "fen": frame.get("fen"),
            "training_eligible": stage in {"stage4", "stage5", "stage6"},
            "held_out_challenge": stage == "stage7",
            "provider_labels": proposals,
        }
    rows = list(rows_by_state.values())
    for row in rows:
        positives = [item for item in row["provider_labels"] if item["positive"]]
        non_stage0_positive = [
            item for item in positives if item["provider_id"] != "krk.stage0_basin"
        ]
        families = sorted({item["provider_family"] for item in row["provider_labels"]})
        row["contrast_summary"] = {
            "provider_count": len({item["provider_id"] for item in row["provider_labels"]}),
            "provider_families": families,
            "positive_provider_count": len({item["provider_id"] for item in positives}),
            "non_stage0_positive_provider_count": len(
                {item["provider_id"] for item in non_stage0_positive}
            ),
            "has_non_stage0_positive": bool(non_stage0_positive),
            "all_labeled_providers_max_plies": bool(row["provider_labels"]) and not positives,
        }
    stage_counts = Counter(row["source_stage"] for row in rows)
    training_rows = [row for row in rows if row["training_eligible"]]
    heldout_rows = [row for row in rows if row["held_out_challenge"]]
    training_non_stage0_positive = sum(
        1 for row in training_rows if row["contrast_summary"]["has_non_stage0_positive"]
    )
    heldout_non_stage0_positive = sum(
        1 for row in heldout_rows if row["contrast_summary"]["has_non_stage0_positive"]
    )
    training_provider_labels = [
        label for row in training_rows for label in row["provider_labels"]
    ]
    training_positive_labels = [
        label for label in training_provider_labels if label["positive"]
    ]
    training_negative_labels = [
        label for label in training_provider_labels if not label["positive"]
    ]
    training_positive_families = sorted(
        {label["provider_family"] for label in training_positive_labels}
    )
    selected_training_families = sorted(
        {
            label["provider_family"]
            for label in training_provider_labels
            if label.get("selected") is True
        }
    )
    same_move_compatibility_rows = sum(
        1
        for row in training_rows
        if any(label["label_source"] == "same_move_or_existing_label" for label in row["provider_labels"])
    )
    readiness_blockers: list[str] = []
    if len(training_positive_labels) < 6 or len(training_negative_labels) < 6:
        readiness_blockers.append("insufficient_training_label_balance")
    if training_non_stage0_positive < 4:
        readiness_blockers.append("insufficient_protected_non_stage0_positive_rows")
    if len(training_positive_families) < 2:
        readiness_blockers.append("insufficient_conversion_positive_provider_family_diversity")
    if len(selected_training_families) < 3:
        readiness_blockers.append("insufficient_selected_provider_family_diversity")
    for protected_stage in ("stage4", "stage5", "stage6"):
        if stage_counts.get(protected_stage, 0) == 0:
            readiness_blockers.append(f"missing_{protected_stage}_contrast_rows")
    if same_move_compatibility_rows < 4:
        readiness_blockers.append("insufficient_same_move_compatibility_rows")
    if any(row["source_stage"] == "stage7" and row["training_eligible"] for row in rows):
        readiness_blockers.append("stage7_training_rows_present")

    selected_status = (
        "strategy_owner_contrast_dataset_underpowered_no_selector_sandbox"
        if readiness_blockers
        else "strategy_owner_contrast_dataset_ready_for_non_causal_probe"
    )
    return {
        "schema_version": "krk_strategy_owner_contrast_dataset.v0",
        "causal_status": "non_causal_dataset",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(FRAMES), str(READINESS)],
        "summary": {
            "row_count": len(rows),
            "row_count_by_stage": dict(sorted(stage_counts.items())),
            "training_eligible_row_count": len(training_rows),
            "held_out_challenge_row_count": len(heldout_rows),
            "training_non_stage0_positive_rows": training_non_stage0_positive,
            "heldout_non_stage0_positive_rows": heldout_non_stage0_positive,
            "training_positive_provider_label_count": len(training_positive_labels),
            "training_negative_provider_label_count": len(training_negative_labels),
            "training_positive_provider_families": training_positive_families,
            "selected_training_provider_families": selected_training_families,
            "same_move_compatibility_training_rows": same_move_compatibility_rows,
            "stage7_training_rows": 0,
        },
        "readiness_v2_assessment": {
            "schema_version": "krk_selector_readiness_v2_assessment.v0",
            "selector_sandbox_ready": not readiness_blockers,
            "blockers": readiness_blockers,
            "stage7_training_rows": 0,
            "held_out_challenge_boundary_preserved": True,
        },
        "rows": rows,
        "decision": {
            "status": selected_status,
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "recommended_next_step": (
                "collect_or_derive_more_protected_non_stage0_contrast_rows"
                if training_non_stage0_positive < 4
                else "run_non_causal_strategy_owner_contrast_probe"
            ),
        },
    }


def render_markdown(dataset: dict[str, Any]) -> str:
    summary = dataset["summary"]
    lines = [
        "# KRK Strategy Owner Contrast Dataset v0",
        "",
        "This replay-free dataset separates protected-control strategy-owner contrast "
        "evidence from Stage 7 held-out challenge evidence. It is non-causal and "
        "does not authorize a selector sandbox.",
        "",
        "## Summary",
        "",
        f"- Rows: `{summary['row_count']}`",
        f"- Rows by stage: `{summary['row_count_by_stage']}`",
        f"- Training-eligible rows: `{summary['training_eligible_row_count']}`",
        f"- Held-out challenge rows: `{summary['held_out_challenge_row_count']}`",
        f"- Training non-stage0-positive rows: `{summary['training_non_stage0_positive_rows']}`",
        f"- Held-out non-stage0-positive rows: `{summary['heldout_non_stage0_positive_rows']}`",
        f"- Training positive provider labels: `{summary['training_positive_provider_label_count']}`",
        f"- Training negative provider labels: `{summary['training_negative_provider_label_count']}`",
        f"- Training positive provider families: `{summary['training_positive_provider_families']}`",
        f"- Selected training provider families: `{summary['selected_training_provider_families']}`",
        f"- Same-move compatibility training rows: `{summary['same_move_compatibility_training_rows']}`",
        f"- Stage 7 training rows: `{summary['stage7_training_rows']}`",
        f"- Readiness blockers: `{dataset['readiness_v2_assessment']['blockers']}`",
        "",
        "## Decision",
        "",
        f"- Status: `{dataset['decision']['status']}`",
        f"- Recommended next step: `{dataset['decision']['recommended_next_step']}`",
        "- Runtime arbiter and selector sandbox remain blocked.",
        "",
        "## Rows",
        "",
    ]
    for row in dataset["rows"]:
        lines.append(
            f"- `{row['state_id']}` stage=`{row['source_stage']}` "
            f"providers=`{row['contrast_summary']['provider_count']}` "
            f"non_stage0_positive=`{row['contrast_summary']['has_non_stage0_positive']}` "
            f"training=`{row['training_eligible']}` heldout=`{row['held_out_challenge']}`"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    dataset = build_dataset()
    (ROOT / OUT_JSON).write_text(json.dumps(dataset, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(dataset), encoding="utf-8")
    print(json.dumps(dataset["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
