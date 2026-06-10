#!/usr/bin/env python3
"""Replay-free selector probe over KRK strategy-arbiter observations."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OBSERVATIONS = Path("reports/krk_strategy_arbiter_observation_frames_v0.json")
FRAMES = Path("reports/krk_control_plane_filtered_frames_with_forced_controls_v0.json")
OUT_JSON = Path("reports/krk_strategy_arbiter_observation_selector_probe_v0.json")
OUT_MD = Path("reports/krk_strategy_arbiter_observation_selector_probe_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _provider_label(proposal: dict[str, Any]) -> str | None:
    forced = proposal.get("forced_control_outcome_label")
    if isinstance(forced, dict) and forced.get("result"):
        return str(forced.get("result"))
    known = proposal.get("known_outcome_label")
    if isinstance(known, dict) and known.get("playout_result"):
        return str(known.get("playout_result"))
    return None


def _labels_by_state(frames_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    labels: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "positive_providers": set(),
            "negative_providers": set(),
            "unknown_providers": set(),
            "proposal_count": 0,
        }
    )
    for frame in frames_payload.get("frames", []) or []:
        state_id = str(frame.get("state_id") or "")
        if not state_id:
            continue
        target = labels[state_id]
        for proposal in frame.get("strategy_proposal_frames", []) or []:
            if not isinstance(proposal, dict):
                continue
            provider = str(proposal.get("provider_id") or proposal.get("skill_id") or "")
            if not provider:
                continue
            target["proposal_count"] += 1
            label = _provider_label(proposal)
            if label == "mate":
                target["positive_providers"].add(provider)
            elif label in {"max_plies", "draw", "no_move", "illegal_move"}:
                target["negative_providers"].add(provider)
            else:
                target["unknown_providers"].add(provider)
    return {
        state_id: {
            "positive_providers": sorted(value["positive_providers"]),
            "negative_providers": sorted(value["negative_providers"]),
            "unknown_providers": sorted(value["unknown_providers"]),
            "proposal_count": int(value["proposal_count"]),
        }
        for state_id, value in labels.items()
    }


def build_probe(root: Path = ROOT) -> dict[str, Any]:
    observations = _load_json(OBSERVATIONS)
    labels = _labels_by_state(_load_json(FRAMES))
    rows: list[dict[str, Any]] = []
    selected_positive = 0
    selected_negative = 0
    selected_unknown = 0
    labeled_rows = 0
    stage_counts = Counter()
    status_counts = Counter()
    for record in observations.get("records", []) or []:
        state_id = str(record.get("state_id") or "")
        stage = str(record.get("source_stage") or "unknown")
        selected_provider = str(record.get("selected_provider") or "")
        label_info = labels.get(state_id, {
            "positive_providers": [],
            "negative_providers": [],
            "unknown_providers": [],
            "proposal_count": 0,
        })
        positives = set(label_info["positive_providers"])
        negatives = set(label_info["negative_providers"])
        if selected_provider in positives:
            selected_label = "positive"
            selected_positive += 1
        elif selected_provider in negatives:
            selected_label = "negative"
            selected_negative += 1
        else:
            selected_label = "unknown"
            selected_unknown += 1
        if positives or negatives:
            labeled_rows += 1
        stage_counts[stage] += 1
        status_counts[selected_label] += 1
        observation = record.get("observation") if isinstance(record.get("observation"), dict) else {}
        rows.append({
            "state_id": state_id,
            "source_stage": stage,
            "active_landmark_label": record.get("active_landmark_label"),
            "selected_provider": selected_provider,
            "selected_move": record.get("selected_move"),
            "selected_label": selected_label,
            "positive_providers": sorted(positives),
            "negative_providers": sorted(negatives),
            "known_label_proposal_count": label_info["proposal_count"],
            "observation_unique_provider_count": int(observation.get("unique_provider_count", 0) or 0),
            "observation_source_term_count": len(observation.get("source_terms", []) or []),
        })
    positive_hit_rate = (
        selected_positive / labeled_rows
        if labeled_rows
        else None
    )
    underlabeled = labeled_rows < max(3, len(rows) // 2)
    status = (
        "observation_selector_probe_underlabeled"
        if underlabeled
        else "observation_selector_probe_ready_for_review"
    )
    return {
        "schema_version": "krk_strategy_arbiter_observation_selector_probe.v0",
        "causal_status": "non_causal_selector_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "source_artifacts": [str(OBSERVATIONS), str(FRAMES)],
        "record_count": len(rows),
        "labeled_row_count": labeled_rows,
        "stage_counts": dict(sorted(stage_counts.items())),
        "selected_label_counts": dict(sorted(status_counts.items())),
        "selected_positive_count": selected_positive,
        "selected_negative_count": selected_negative,
        "selected_unknown_count": selected_unknown,
        "selected_positive_hit_rate_on_labeled_rows": positive_hit_rate,
        "underlabeled": underlabeled,
        "rows": rows,
        "decision": {
            "status": status,
            "runtime_arbiter_allowed": False,
            "sandbox_ready": False,
            "recommended_next_step": (
                "add_small_labeled_observation_controls_before_sandbox_review"
                if underlabeled
                else "architecture_review_before_any_default_off_selector_sandbox"
            ),
        },
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# KRK Strategy Arbiter Observation Selector Probe v0",
        "",
        "This is a replay-free probe over trace-only observation frames and existing provider labels.",
        "",
        "## Summary",
        "",
        f"- Records: `{payload['record_count']}`",
        f"- Labeled rows: `{payload['labeled_row_count']}`",
        f"- Stage counts: `{payload['stage_counts']}`",
        f"- Selected label counts: `{payload['selected_label_counts']}`",
        f"- Positive hit rate on labeled rows: `{payload['selected_positive_hit_rate_on_labeled_rows']}`",
        f"- Underlabeled: `{payload['underlabeled']}`",
        "",
        "## Rows",
        "",
    ]
    for row in payload["rows"]:
        lines.append(
            f"- `{row['state_id']}` stage=`{row['source_stage']}` selected=`{row['selected_provider']}` "
            f"label=`{row['selected_label']}` positives=`{row['positive_providers']}` "
            f"negatives=`{row['negative_providers']}`"
        )
    lines.extend([
        "",
        "## Decision",
        "",
        f"Status: `{payload['decision']['status']}`",
        f"Sandbox ready: `{payload['decision']['sandbox_ready']}`",
        f"Runtime arbiter allowed: `{payload['decision']['runtime_arbiter_allowed']}`",
        f"Recommended next step: `{payload['decision']['recommended_next_step']}`",
        "",
        "Do not implement a runtime selector from this probe.",
    ])
    (ROOT / path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_probe()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload, OUT_MD)


if __name__ == "__main__":
    main()
