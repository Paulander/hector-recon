#!/usr/bin/env python3
"""Review proposal-frame coverage for protected missing-provider labels."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RANKED_FRAMES = Path("reports/krk_ranked_strategy_proposal_frames_v1.json")
LABELS = Path("reports/krk_protected_missing_provider_capacity_labels_v0.json")
OUT_JSON = Path("reports/krk_ranked_proposal_frame_protected_provider_coverage_review_v0.json")
OUT_MD = Path("reports/krk_ranked_proposal_frame_protected_provider_coverage_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    ranked = _load(RANKED_FRAMES)
    labels_payload = _load(LABELS)
    if ranked.get("causal_status") != "non_causal_ranked_frame_dataset":
        raise ValueError("ranked proposal frames must remain non-causal")
    if labels_payload.get("causal_status") != "non_causal_label_run":
        raise ValueError("protected labels must remain non-causal")

    providers_by_frame: dict[str, set[str]] = defaultdict(set)
    providers_by_state: dict[str, set[str]] = defaultdict(set)
    for row in ranked.get("rows") or []:
        provider = str(row.get("provider_id") or "")
        providers_by_frame[str(row.get("frame_id"))].add(provider)
        providers_by_state[str(row.get("state_id"))].add(provider)

    records = []
    for label in labels_payload.get("labels") or []:
        frame_id = str(label.get("frame_id") or "")
        state_id = str(label.get("state_id") or "")
        provider = str(label.get("provider_id") or "")
        frame_providers = sorted(providers_by_frame.get(frame_id) or [])
        state_providers = sorted(providers_by_state.get(state_id) or [])
        records.append({
            "schema_version": "krk_protected_provider_proposal_coverage_record.v0",
            "job_id": label.get("job_id"),
            "frame_id": frame_id,
            "state_id": state_id,
            "source_stage": label.get("source_stage"),
            "provider_id": provider,
            "label_result": label.get("result"),
            "label_plies": label.get("plies"),
            "frame_present": frame_id in providers_by_frame,
            "state_present": state_id in providers_by_state,
            "provider_present_in_frame": provider in providers_by_frame.get(frame_id, set()),
            "provider_present_in_state": provider in providers_by_state.get(state_id, set()),
            "frame_providers": frame_providers,
            "state_providers": state_providers,
            "causal_status": "non_causal",
        })

    missing = [record for record in records if not record["provider_present_in_frame"]]
    missing_mates = [record for record in missing if record.get("label_result") == "mate"]
    status = "protected_provider_proposal_coverage_ok"
    recommendation = "merge_protected_labels_into_selector_targets"
    if missing_mates:
        status = "proposal_provider_coverage_gap_blocks_selector_training"
        recommendation = "design_non_causal_proposal_coverage_expansion_for_protected_states"
    elif missing:
        status = "proposal_provider_coverage_gap_for_negative_labels"
        recommendation = "review_negative_label_coverage_before_runtime_work"

    payload = {
        "schema_version": "krk_ranked_proposal_frame_protected_provider_coverage_review.v0",
        "causal_status": "non_causal_coverage_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(RANKED_FRAMES), str(LABELS)],
        "summary": {
            "label_count": len(records),
            "frames_present_count": sum(1 for record in records if record["frame_present"]),
            "states_present_count": sum(1 for record in records if record["state_present"]),
            "provider_present_in_frame_count": sum(1 for record in records if record["provider_present_in_frame"]),
            "provider_missing_from_frame_count": len(missing),
            "missing_provider_mate_label_count": len(missing_mates),
            "result_counts": dict(Counter(str(record.get("label_result")) for record in records)),
            "missing_result_counts": dict(Counter(str(record.get("label_result")) for record in missing)),
            "missing_stage_counts": dict(Counter(str(record.get("source_stage")) for record in missing)),
            "missing_provider_counts": dict(Counter(str(record.get("provider_id")) for record in missing)),
            "stage7_label_count": sum(1 for record in records if record.get("source_stage") == "stage7"),
        },
        "records": records,
        "decision": {
            "status": status,
            "recommended_next_step": recommendation,
            "runtime_work_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_review(payload)
    return payload


def validate_review(payload: dict[str, Any]) -> None:
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
    if payload["summary"]["stage7_label_count"] != 0:
        raise ValueError("Stage 7 labels must remain excluded")
    for record in payload.get("records") or []:
        if record.get("causal_status") != "non_causal":
            raise ValueError("coverage records must remain non-causal")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Ranked Proposal Frame Protected Provider Coverage Review v0",
        "",
        "This replay-free review checks whether protected forced-provider labels have corresponding proposal-frame rows.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Missing Provider Records", ""])
    for record in payload["records"]:
        if record["provider_present_in_frame"]:
            continue
        lines.append(
            f"- `{record['job_id']}` stage=`{record['source_stage']}` provider=`{record['provider_id']}` "
            f"result=`{record['label_result']}` frame_providers=`{record['frame_providers']}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
