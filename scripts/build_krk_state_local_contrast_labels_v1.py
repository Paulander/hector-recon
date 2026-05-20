#!/usr/bin/env python3
"""Join ranked proposal frames with forced-provider outcome labels."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RANKED_FRAMES = Path("reports/krk_ranked_strategy_proposal_frames_v1.json")
FORCED_LABELS = (
    Path("reports/krk_forced_provider_control_labels_v0.json"),
    Path("reports/krk_strategy_owner_contrast_control_labels_v0.json"),
)
OUT_JSON = Path("reports/krk_state_local_contrast_labels_v1.json")
OUT_MD = Path("reports/krk_state_local_contrast_labels_v1.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _load_labels() -> list[dict[str, Any]]:
    labels = []
    for path in FORCED_LABELS:
        payload = _load_json(path)
        if payload.get("causal_status") != "non_causal_label_run":
            # Older contrast-label artifacts use per-label causal status only.
            for item in payload.get("labels") or []:
                if item.get("causal_status") != "non_causal_outcome_label":
                    raise ValueError(f"{path}: forced label must be non-causal")
        labels.extend(payload.get("labels") or [])
    return labels


def _result_label(result: str | None) -> str | None:
    if result == "mate":
        return "positive"
    if result == "max_plies":
        return "negative"
    return None


def build_dataset() -> dict[str, Any]:
    ranked = _load_json(RANKED_FRAMES)
    if ranked.get("causal_status") != "non_causal_ranked_frame_dataset":
        raise ValueError("ranked proposal frames must remain non-causal")

    by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for label in _load_labels():
        key = (str(label.get("state_id")), str(label.get("provider_id")))
        by_key[key].append(label)

    rows = []
    unmatched_labels = []
    matched_label_ids = set()
    for proposal in ranked.get("rows") or []:
        key = (str(proposal.get("state_id")), str(proposal.get("provider_id")))
        matches = by_key.get(key) or []
        if not matches:
            continue
        # If duplicate labels exist, prefer the shortest successful result; otherwise keep the first.
        ordered = sorted(
            matches,
            key=lambda item: (
                0 if item.get("result") == "mate" else 1,
                int(item.get("plies") or 999),
                str(item.get("job_id")),
            ),
        )
        label = ordered[0]
        matched_label_ids.add(label.get("job_id"))
        result_label = _result_label(label.get("result"))
        rows.append({
            "schema_version": "krk_state_local_contrast_label.v1",
            "frame_id": proposal.get("frame_id"),
            "state_id": proposal.get("state_id"),
            "source_stage": proposal.get("source_stage"),
            "active_landmark_label": proposal.get("active_landmark_label"),
            "provider_id": proposal.get("provider_id"),
            "provider_family": proposal.get("provider_family"),
            "provider_maturity": proposal.get("provider_maturity"),
            "move_uci": proposal.get("move_uci"),
            "raw_score": proposal.get("raw_score"),
            "global_raw_score_rank": proposal.get("global_raw_score_rank"),
            "provider_local_rank": proposal.get("provider_local_rank"),
            "normalized_score": proposal.get("normalized_score"),
            "frame_outcome": proposal.get("frame_outcome"),
            "forced_result": label.get("result"),
            "forced_plies": label.get("plies"),
            "forced_first_move": label.get("forced_first_move"),
            "forced_successor_available": label.get("forced_successor_available"),
            "contrast_label": result_label,
            "label_channel": "forced_provider_state_local_contrast",
            "usable_for_training": bool(result_label and not proposal.get("stage7_challenge_row")),
            "stage7_challenge_row": bool(proposal.get("stage7_challenge_row")),
            "source_label_job_id": label.get("job_id"),
            "causal_status": "non_causal",
        })

    proposal_keys = {
        (str(proposal.get("state_id")), str(proposal.get("provider_id")))
        for proposal in ranked.get("rows") or []
    }
    for labels in by_key.values():
        for label in labels:
            if (str(label.get("state_id")), str(label.get("provider_id"))) not in proposal_keys:
                unmatched_labels.append(label.get("job_id"))

    summary = {
        "row_count": len(rows),
        "usable_training_row_count": sum(1 for row in rows if row["usable_for_training"]),
        "stage7_challenge_row_count": sum(1 for row in rows if row["stage7_challenge_row"]),
        "contrast_label_counts": dict(Counter(str(row["contrast_label"]) for row in rows)),
        "forced_result_counts": dict(Counter(str(row["forced_result"]) for row in rows)),
        "provider_family_counts": dict(Counter(str(row["provider_family"]) for row in rows)),
        "source_stage_counts": dict(Counter(str(row["source_stage"]) for row in rows)),
        "matched_forced_label_count": len(matched_label_ids),
        "unmatched_forced_label_count": len(unmatched_labels),
        "unmatched_forced_label_job_ids": sorted(str(item) for item in unmatched_labels if item),
    }
    dataset = {
        "schema_version": "krk_state_local_contrast_labels.v1",
        "causal_status": "non_causal_state_local_contrast_dataset",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(RANKED_FRAMES), *(str(path) for path in FORCED_LABELS)],
        "rows": rows,
        "summary": summary,
        "decision": {
            "status": "state_local_contrast_labels_joined",
            "recommended_next_step": "probe_state_local_contrast_selector_v1",
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
            raise ValueError("all contrast rows must remain non-causal")
        if row.get("stage7_challenge_row") and row.get("usable_for_training"):
            raise ValueError("Stage7 challenge rows must not be training rows")


def render_markdown(dataset: dict[str, Any]) -> str:
    lines = [
        "# KRK State-Local Contrast Labels v1",
        "",
        "This replay-free dataset joins ranked proposal frames with forced-provider labels by state/provider. It is non-causal and does not run playouts.",
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
