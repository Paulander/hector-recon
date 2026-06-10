#!/usr/bin/env python3
"""Write the Stage 5 guardrail semantics split reference artifact."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTROL_DEBT_REVIEW = Path("reports/krk_stage5_guardrail_control_debt_review_v0.json")
OUT_JSON = Path("reports/krk_stage5_guardrail_semantics_split_v0.json")
OUT_MD = Path("reports/krk_stage5_guardrail_semantics_split_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def build_payload() -> dict[str, Any]:
    review = _load(CONTROL_DEBT_REVIEW)
    decision = review.get("decision") or {}
    return {
        "schema_version": "krk_stage5_guardrail_semantics_split.v0",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_artifacts": [str(CONTROL_DEBT_REVIEW)],
        "status": "stage5_guardrail_semantics_split_defined",
        "decision": {
            "stage5_overlay_regressed_vs_base_control": decision.get(
                "stage5_overlay_regressed_vs_base_control"
            ),
            "stage5_conversion_preserved": decision.get("stage5_conversion_preserved"),
            "stage5_one_ply_debt_reproduces_in_base_control": decision.get(
                "stage5_one_ply_debt_reproduces_in_base_control"
            ),
            "clean_stack_replacement_allowed": False,
            "stage6_overlay_use_allowed_as_overlay_only": True,
            "recommended_next_step": "update_clean_retrain_promotion_review_to_accept_overlay_only_with_control_debt_but_block_clean_replacement_until_stage5_local_reward_contract_debt_is_resolved_or_accepted",
        },
        "guardrail_tracks": [
            {
                "track_id": "stage5.conversion_preservation_guardrail",
                "purpose": "Detect whether a later overlay regresses existing Stage 5 conversion behavior.",
                "comparison": "candidate_overlay_guardrail_vs_paired_stage5_base_control",
                "pass_condition": [
                    "mate_rate_delta >= -0.02",
                    "max_plies_rate_delta <= 0.02",
                    "shadow_candidate_delta <= 0",
                ],
                "retry1_result": "passed_no_regression",
                "promotion_effect": "allows_overlay_only_if_target_stage_passes",
            },
            {
                "track_id": "stage5.local_reward_contract_guardrail",
                "purpose": "Track mismatch between Stage 5 local one-ply reward and visible fence-contract success.",
                "comparison": "candidate_and_paired_base_control_against_local_reward_thresholds",
                "pass_condition": [
                    "improved_rate >= 0.70",
                    "worsened_rate <= 0.20",
                ],
                "retry1_result": "failed_but_reproduces_in_base_control",
                "promotion_effect": "blocks_clean_stack_replacement_or_full_promotion_until_reviewed",
            },
        ],
        "clean_retrain_promotion_policy": {
            "stage6_target_failure": "quarantine",
            "stage5_conversion_regression_vs_control": "quarantine",
            "stage5_local_reward_debt_only_in_candidate": "quarantine_or_review",
            "stage5_local_reward_debt_reproduces_in_base_control": "overlay_only_control_debt",
            "no_debt_no_regression_target_passed": "promoted_after_remaining_guardrails",
        },
        "current_retry1_metrics": {
            "overlay": review.get("stage5_overlay"),
            "base_control": review.get("stage5_base_control"),
            "delta_overlay_vs_base_control": review.get("delta_overlay_vs_base_control"),
        },
        "invariants": review.get("invariants") or {},
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Stage 5 Guardrail Semantics Split v0",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Decision",
        "",
    ]
    for key, value in payload["decision"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Guardrail Tracks", ""])
    for track in payload["guardrail_tracks"]:
        lines.append(f"### `{track['track_id']}`")
        lines.append("")
        lines.append(f"- Purpose: {track['purpose']}")
        lines.append(f"- Comparison: `{track['comparison']}`")
        lines.append(f"- Retry1 result: `{track['retry1_result']}`")
        lines.append(f"- Promotion effect: `{track['promotion_effect']}`")
        lines.append("- Pass condition:")
        for condition in track["pass_condition"]:
            lines.append(f"  - `{condition}`")
        lines.append("")
    lines.extend(["## Clean Retrain Promotion Policy", ""])
    for key, value in payload["clean_retrain_promotion_policy"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is an offline guardrail-definition artifact. It does not change runtime behavior, promote Stage 7, train Stage 8, use runtime DTM/tablebase, or mutate topology.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "json_output": str(OUT_JSON)}, indent=2))


if __name__ == "__main__":
    main()
