#!/usr/bin/env python3
"""Write clean retrain retry1 replacement-readiness review.

This review consumes the Stage 5 debt audit and corrected Stage 6 promotion
eval. It does not promote or replace any protected checkpoint.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STAGE5_DEBT_AUDIT = Path("reports/krk_stage5_local_reward_contract_debt_audit_v0.json")
STAGE5_SEMANTICS_SPLIT = Path("reports/krk_stage5_guardrail_semantics_split_v0.json")
STAGE6_GAP_INSPECTION = Path("reports/krk_clean_retrain_retry1_stage6_gap_inspection_v1.json")
PROMOTION_EVAL = Path(
    "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/"
    "stage6_overlay_composed/promotion_eval_stage6_overlay_profile_bonus.json"
)
OUT_JSON = Path("reports/krk_clean_retrain_retry1_replacement_readiness_review_v0.json")
OUT_MD = Path("reports/krk_clean_retrain_retry1_replacement_readiness_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def build_payload() -> dict[str, Any]:
    debt_audit = _load(STAGE5_DEBT_AUDIT)
    semantics_split = _load(STAGE5_SEMANTICS_SPLIT)
    stage6_gap = _load(STAGE6_GAP_INSPECTION)
    promotion_eval = _load(PROMOTION_EVAL)

    stage6_target_passed = bool((promotion_eval.get("stage") or {}).get("passed"))
    conversion_track = (
        (promotion_eval.get("guardrail_semantics") or {})
        .get("conversion_preservation", [{}])[0]
        .get("passed")
    )
    local_debt = bool(
        (promotion_eval.get("guardrail_semantics") or {}).get("local_reward_contract_debt")
    )
    debt_accepted_for_overlay_review = (
        debt_audit.get("status")
        == "stage5_local_reward_contract_debt_is_guardrail_semantics_debt"
        and local_debt
        and conversion_track is True
    )
    status = (
        "retry1_ready_for_remaining_preservation_checks_not_replacement"
        if stage6_target_passed and debt_accepted_for_overlay_review
        else "retry1_replacement_review_blocked"
    )
    remaining_checks = [
        {
            "check_id": "stage4_overlay_caveat_control_review",
            "required": True,
            "status": "pending",
            "reason": "Stage 4 has a known h40 overlay-control caveat and was not rerun after the corrected Stage 6 validation-profile inspection.",
        },
        {
            "check_id": "m1_m4_preservation_suite",
            "required": True,
            "status": "pending",
            "reason": "Clean-stack replacement must preserve plasticity/consolidation semantics beyond KRK artifact-level checks.",
        },
        {
            "check_id": "kpk_kqk_bridge_preservation",
            "required": True,
            "status": "pending",
            "reason": "Endgame domain handoff and bridge eligibility must remain intact before replacing protected KRK checkpoints.",
        },
        {
            "check_id": "protected_stack_snapshot_manifest",
            "required": True,
            "status": "pending",
            "reason": "Replacement requires an explicit snapshot/rollback manifest naming old and candidate checkpoints.",
        },
    ]
    return {
        "schema_version": "krk_clean_retrain_retry1_replacement_readiness_review.v0",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": status,
        "decision": {
            "stage6_target_passed_corrected_profile": stage6_target_passed,
            "stage5_conversion_preservation_passed": conversion_track is True,
            "stage5_local_reward_debt_accepted_as_known_base_control_debt_for_overlay_review": debt_accepted_for_overlay_review,
            "clean_stack_replacement_allowed": False,
            "runtime_behavior_changed": False,
            "recommended_next_step": "run_remaining_preservation_checks_and_stage4_caveat_review_before_any_clean_stack_replacement_packet",
        },
        "source_artifacts": {
            "stage5_debt_audit": str(STAGE5_DEBT_AUDIT),
            "stage5_semantics_split": str(STAGE5_SEMANTICS_SPLIT),
            "stage6_gap_inspection": str(STAGE6_GAP_INSPECTION),
            "corrected_promotion_eval": str(PROMOTION_EVAL),
        },
        "promotion_eval_summary": {
            "promotion_status": promotion_eval.get("promotion_status"),
            "promotion_status_semantics": promotion_eval.get("promotion_status_semantics"),
            "stage_passed": stage6_target_passed,
            "failures": list(promotion_eval.get("failures") or []),
            "guardrail_semantics": promotion_eval.get("guardrail_semantics"),
        },
        "stage5_debt_summary": {
            "status": debt_audit.get("status"),
            "pattern_summary": debt_audit.get("pattern_summary"),
            "recommended_next_step": (debt_audit.get("decision") or {}).get(
                "recommended_next_step"
            ),
        },
        "semantics_split_summary": {
            "status": semantics_split.get("status"),
            "clean_retrain_promotion_policy": semantics_split.get(
                "clean_retrain_promotion_policy"
            ),
        },
        "remaining_required_checks": remaining_checks,
        "replacement_policy": {
            "allowed_now": False,
            "stage5_local_reward_debt_effect": "accepted_only_as_known_base_control_debt_for_overlay_review",
            "stage6_overlay_effect": "can_continue_as_overlay_only_candidate_for_remaining_preservation_checks",
            "stage7_effect": "unchanged_quarantined_held_out",
            "stage8_effect": "unchanged_blocked",
        },
        "invariants": {
            "runtime_defaults_changed": False,
            "runtime_selector_implemented": False,
            "runtime_score_changes": False,
            "runtime_direct_routing": False,
            "runtime_dtm_or_tablebase_lookup": False,
            "gameplay_topology_mutation": False,
            "stage7_promotion": False,
            "stage8_training": False,
        },
        "related_stage6_gap_status": stage6_gap.get("status"),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    decision = payload["decision"]
    checks = "\n".join(
        f"- `{item['check_id']}` status=`{item['status']}` required=`{item['required']}`: {item['reason']}"
        for item in payload["remaining_required_checks"]
    )
    return f"""# KRK Clean Retrain Retry1 Replacement Readiness Review v0

Status: `{payload['status']}`

## Decision

- Stage 6 target passed corrected profile: `{decision['stage6_target_passed_corrected_profile']}`
- Stage 5 conversion preservation passed: `{decision['stage5_conversion_preservation_passed']}`
- Stage 5 local reward debt accepted as known base-control debt for overlay review: `{decision['stage5_local_reward_debt_accepted_as_known_base_control_debt_for_overlay_review']}`
- Clean stack replacement allowed: `{decision['clean_stack_replacement_allowed']}`
- Recommended next step: `{decision['recommended_next_step']}`

## Meaning

Retry1 can proceed as an `overlay_only` candidate into the remaining preservation checks. It is not approved as a protected-stack replacement. The Stage 5 local reward debt is accepted only as known base-control debt for overlay review, not as a solved contract issue.

## Remaining Required Checks

{checks}

## Replacement Policy

- allowed now: `{payload['replacement_policy']['allowed_now']}`
- Stage 5 debt effect: `{payload['replacement_policy']['stage5_local_reward_debt_effect']}`
- Stage 6 overlay effect: `{payload['replacement_policy']['stage6_overlay_effect']}`
- Stage 7 effect: `{payload['replacement_policy']['stage7_effect']}`
- Stage 8 effect: `{payload['replacement_policy']['stage8_effect']}`

## Boundary

This review does not replace checkpoints, promote Stage 7, train Stage 8, change runtime behavior, use runtime DTM/tablebase, or mutate topology.
"""


def main() -> None:
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "json_output": str(OUT_JSON)}, indent=2))


if __name__ == "__main__":
    main()
