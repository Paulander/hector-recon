#!/usr/bin/env python3
"""Build non-causal protected provider coverage frames from forced labels."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN = Path("reports/krk_protected_proposal_coverage_expansion_plan_v0.json")
RANKED_FRAMES = Path("reports/krk_ranked_strategy_proposal_frames_v1.json")
LABELS = Path("reports/krk_protected_missing_provider_capacity_labels_v0.json")
OUT_JSON = Path("reports/krk_protected_provider_coverage_frames_v0.json")
OUT_MD = Path("reports/krk_protected_provider_coverage_frames_v0.md")


def _load(path: Path) -> dict[str, Any]:
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


def _result_label(result: str | None) -> str | None:
    if result == "mate":
        return "positive_capacity"
    if result == "max_plies":
        return "negative_capacity"
    return None


def build_frames() -> dict[str, Any]:
    plan = _load(PLAN)
    ranked = _load(RANKED_FRAMES)
    labels_payload = _load(LABELS)
    if plan.get("causal_status") != "non_causal_design_plan":
        raise ValueError("coverage expansion plan must remain non-causal")
    if ranked.get("causal_status") != "non_causal_ranked_frame_dataset":
        raise ValueError("ranked proposal frames must remain non-causal")
    if labels_payload.get("causal_status") != "non_causal_label_run":
        raise ValueError("protected labels must remain non-causal")

    ranked_by_frame: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in ranked.get("rows") or []:
        ranked_by_frame[str(row.get("frame_id"))].append(row)

    rows = []
    for label in labels_payload.get("labels") or []:
        frame_id = str(label.get("frame_id") or "")
        provider_id = str(label.get("provider_id") or "")
        existing_frame_rows = ranked_by_frame.get(frame_id) or []
        frame_providers = sorted({str(row.get("provider_id")) for row in existing_frame_rows})
        if provider_id in frame_providers:
            continue
        context = existing_frame_rows[0] if existing_frame_rows else {}
        row = {
            "schema_version": "krk_protected_provider_coverage_frame.v0",
            "causal_status": "non_causal_capacity_evidence",
            "proposal_source": "offline_forced_provider_label_not_runtime_proposal",
            "label_semantics": "forced_provider_capacity_label",
            "state_id": label.get("state_id"),
            "frame_id": frame_id,
            "fen": context.get("fen"),
            "source_stage": label.get("source_stage"),
            "active_landmark_label": context.get("active_landmark_label") or label.get("source_active_landmark_label"),
            "provider_id": provider_id,
            "provider_family": _provider_family(provider_id),
            "provider_version": label.get("provider_version"),
            "forced_result": label.get("result"),
            "forced_plies": label.get("plies"),
            "forced_first_move": label.get("forced_first_move"),
            "forced_successor_available": label.get("forced_successor_available"),
            "capacity_label": _result_label(label.get("result")),
            "existing_frame_providers": frame_providers,
            "has_runtime_proposal_frame": False,
            "usable_for_training": False,
            "training_block_reason": (
                "forced-provider capacity label is not direct runtime proposal evidence; "
                "requires label-semantics review before any training use"
            ),
            "stage7_challenge_row": False,
            "source_label_job_id": label.get("job_id"),
        }
        rows.append(row)

    summary = {
        "row_count": len(rows),
        "capacity_label_counts": dict(Counter(str(row.get("capacity_label")) for row in rows)),
        "forced_result_counts": dict(Counter(str(row.get("forced_result")) for row in rows)),
        "source_stage_counts": dict(Counter(str(row.get("source_stage")) for row in rows)),
        "provider_family_counts": dict(Counter(str(row.get("provider_family")) for row in rows)),
        "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
        "training_row_count": sum(1 for row in rows if row.get("usable_for_training")),
        "runtime_proposal_row_count": sum(1 for row in rows if row.get("has_runtime_proposal_frame")),
    }
    payload = {
        "schema_version": "krk_protected_provider_coverage_frames.v0",
        "causal_status": "non_causal_capacity_frame_dataset",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(PLAN), str(RANKED_FRAMES), str(LABELS)],
        "summary": summary,
        "rows": rows,
        "decision": {
            "status": "protected_provider_coverage_frames_built",
            "recommended_next_step": "review_capacity_frame_training_semantics_before_selector_use",
            "runtime_work_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_payload(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if payload["summary"]["stage7_row_count"] != 0:
        raise ValueError("Stage 7 rows must remain excluded")
    if payload["summary"]["training_row_count"] != 0:
        raise ValueError("coverage capacity rows must not be training rows initially")
    if payload["summary"]["runtime_proposal_row_count"] != 0:
        raise ValueError("coverage rows must not be represented as runtime proposal rows")
    for row in payload.get("rows") or []:
        if row.get("causal_status") != "non_causal_capacity_evidence":
            raise ValueError("coverage rows must remain non-causal")
        if row.get("usable_for_training"):
            raise ValueError("coverage rows require review before training use")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Protected Provider Coverage Frames v0",
        "",
        "These rows materialize protected forced-provider capacity labels as non-causal evidence frames. They are not runtime proposals and are not training rows.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Rows", ""])
    for row in payload["rows"]:
        lines.append(
            f"- `{row['source_label_job_id']}` stage=`{row['source_stage']}` provider=`{row['provider_id']}` "
            f"capacity=`{row['capacity_label']}` forced_move=`{row.get('forced_first_move')}` "
            f"existing_frame_providers=`{row['existing_frame_providers']}`"
        )
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_frames()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
