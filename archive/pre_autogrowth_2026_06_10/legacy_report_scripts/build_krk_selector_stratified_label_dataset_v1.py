#!/usr/bin/env python3
"""Build replay-free stratified selector labels from reviewed planned jobs."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REVIEW = Path("reports/krk_selector_label_plan_replay_free_review_v1.json")
OUT_JSON = Path("reports/krk_selector_stratified_label_dataset_v1.json")
OUT_MD = Path("reports/krk_selector_stratified_label_dataset_v1.md")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _choose_label(review: dict[str, Any]) -> tuple[str | None, str | None]:
    for target in review.get("target_labels", []) or []:
        label = target.get("label")
        if label in {"positive", "negative"}:
            return label, target.get("label_source")
    for proposal in review.get("proposal_labels", []) or []:
        result = proposal.get("result")
        if result == "mate":
            return "positive", "proposal_result"
        if result in {"max_plies", "draw", "illegal", "no_move"}:
            return "negative", "proposal_result"
    return None, None


def build_dataset() -> dict[str, Any]:
    payload = _load_json(REVIEW)
    rows = []
    for item in payload.get("reviews", []) or []:
        label, label_source = _choose_label(item)
        rows.append({
            "schema_version": "krk_selector_stratified_label_example.v1",
            "causal_status": "non_causal_label_example",
            "job_id": item.get("job_id"),
            "state_id": item.get("state_id"),
            "source_stage": item.get("source_stage"),
            "provider_id": item.get("provider_id"),
            "target_kind": item.get("target_kind"),
            "label": label,
            "label_source": label_source,
            "fill_status": item.get("fill_status"),
            "execute_playout_needed": bool(item.get("execute_playout_needed")),
            "stage7_training_row": False,
            "target_label_count": len(item.get("target_labels", []) or []),
            "proposal_label_count": len(item.get("proposal_labels", []) or []),
        })
    label_counts = Counter(str(row.get("label") or "none") for row in rows)
    stage_counts = Counter(str(row.get("source_stage") or "unknown") for row in rows)
    target_counts = Counter(str(row.get("target_kind") or "unknown") for row in rows)
    return {
        "schema_version": "krk_selector_stratified_label_dataset.v1",
        "causal_status": "non_causal_label_dataset",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "source_artifact": str(REVIEW),
        "row_count": len(rows),
        "label_counts": dict(sorted(label_counts.items())),
        "stage_counts": dict(sorted(stage_counts.items())),
        "target_kind_counts": dict(sorted(target_counts.items())),
        "stage7_training_rows": 0,
        "rows": rows,
        "decision": {
            "status": "stratified_selector_label_dataset_built_replay_free",
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "recommended_next_step": "probe_stratified_selector_label_balance",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Selector Stratified Label Dataset v1",
        "",
        "This dataset fills the bounded selector label plan from existing artifacts only.",
        "",
        "## Summary",
        "",
        f"- Rows: `{payload['row_count']}`",
        f"- Label counts: `{payload['label_counts']}`",
        f"- Stage counts: `{payload['stage_counts']}`",
        f"- Target kind counts: `{payload['target_kind_counts']}`",
        f"- Stage7 training rows: `{payload['stage7_training_rows']}`",
        f"- Runtime arbiter allowed: `{payload['decision']['runtime_arbiter_allowed']}`",
        f"- Selector sandbox ready: `{payload['decision']['selector_sandbox_ready']}`",
        "",
        "## Rows",
        "",
    ]
    for row in payload["rows"]:
        lines.append(
            f"- `{row['job_id']}` label=`{row['label']}` stage=`{row['source_stage']}` "
            f"provider=`{row['provider_id']}` target=`{row['target_kind']}`"
        )
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_dataset()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload)


if __name__ == "__main__":
    main()
