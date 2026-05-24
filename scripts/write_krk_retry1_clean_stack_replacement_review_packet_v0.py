#!/usr/bin/env python3
"""Write retry1 clean-stack replacement review packet.

The packet decides whether retry1 has enough evidence to be *review-ready* for
protected-stack replacement. It does not perform replacement.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

STAGE4_REVIEW = Path("reports/krk_clean_retrain_retry1_stage4_caveat_control_review_v0.json")
PRESERVATION_CHECKS = Path("reports/krk_clean_retrain_retry1_preservation_checks_v0.json")
SNAPSHOT_MANIFEST = Path(
    "reports/krk_clean_retrain_retry1_protected_stack_snapshot_manifest_v0.json"
)
REPLACEMENT_READINESS = Path(
    "reports/krk_clean_retrain_retry1_replacement_readiness_review_v0.json"
)
OUT_JSON = Path("reports/krk_clean_retrain_retry1_clean_stack_replacement_review_packet_v0.json")
OUT_MD = Path("reports/krk_clean_retrain_retry1_clean_stack_replacement_review_packet_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def build_payload() -> dict[str, Any]:
    readiness = _load(REPLACEMENT_READINESS)
    stage4 = _load(STAGE4_REVIEW)
    preservation = _load(PRESERVATION_CHECKS)
    manifest = _load(SNAPSHOT_MANIFEST)

    prerequisites = {
        "stage6_target_passed_corrected_profile": bool(
            readiness.get("decision", {}).get("stage6_target_passed_corrected_profile")
        ),
        "stage5_conversion_preservation_passed": bool(
            readiness.get("decision", {}).get("stage5_conversion_preservation_passed")
        ),
        "stage5_local_reward_debt_accepted_as_known_base_control_debt": bool(
            readiness.get("decision", {}).get(
                "stage5_local_reward_debt_accepted_as_known_base_control_debt_for_overlay_review"
            )
        ),
        "stage4_caveat_control_review_passed": bool(
            stage4.get("decision", {}).get("stage4_caveat_reproduces_in_base_control")
        )
        and not bool(stage4.get("decision", {}).get("stage4_overlay_regressed_vs_base_control")),
        "m1_m4_preservation_passed": bool(
            preservation.get("decision", {}).get("m1_m4_preservation_passed")
        ),
        "kpk_kqk_bridge_preservation_passed": bool(
            preservation.get("decision", {}).get("kpk_kqk_bridge_preservation_passed")
        ),
        "snapshot_manifest_ready": manifest.get("status")
        == "retry1_protected_stack_snapshot_manifest_ready_no_replacement",
        "snapshot_manifest_paths_exist": bool(
            manifest.get("decision", {}).get("all_referenced_paths_exist")
        ),
    }
    review_ready = all(prerequisites.values())
    return {
        "schema_version": "krk_clean_retrain_retry1_clean_stack_replacement_review_packet.v0",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": (
            "retry1_clean_stack_replacement_review_ready_explicit_approval_required"
            if review_ready
            else "retry1_clean_stack_replacement_review_blocked"
        ),
        "source_artifacts": [
            str(REPLACEMENT_READINESS),
            str(STAGE4_REVIEW),
            str(PRESERVATION_CHECKS),
            str(SNAPSHOT_MANIFEST),
        ],
        "prerequisites": prerequisites,
        "decision": {
            "replacement_review_ready": review_ready,
            "implementation_allowed_by_this_packet": False,
            "clean_stack_replacement_performed": False,
            "explicit_human_approval_required_before_any_file_change": True,
            "recommended_next_step": (
                "request_explicit_clean_stack_replacement_approval_or_keep_current_protected_stack"
                if review_ready
                else "resolve_failed_prerequisites_before_replacement_review"
            ),
        },
        "current_protected_stack": manifest.get("current_protected_stack", {}),
        "retry1_candidate_stack": manifest.get("retry1_candidate_stack", {}),
        "known_caveats": [
            {
                "caveat_id": "stage4_wrong_tempo_h40_caveat",
                "status": "reproduces_in_base_control_not_overlay_regression",
                "metrics": {
                    "mate": stage4.get("stage4_overlay", {}).get("mate"),
                    "max_plies": stage4.get("stage4_overlay", {}).get("max_plies"),
                    "total": stage4.get("stage4_overlay", {}).get("total"),
                },
                "replacement_impact": "does_not_block_overlay_replacement_review_but_remains_known_caveat",
            },
            {
                "caveat_id": "stage5_local_reward_contract_debt",
                "status": "known_base_control_debt",
                "replacement_impact": "accepted_only_as_guardrail_semantics_debt_not_as_solved_contract",
            },
        ],
        "required_approval_scope_if_approved_later": {
            "allowed": [
                "update protected Stage 5/6 stack references only if a later explicit approval says so",
                "preserve rollback paths recorded in the snapshot manifest",
                "rerun default protected validation after any approved replacement",
            ],
            "forbidden": [
                "promote Stage 7",
                "train Stage 8",
                "change runtime defaults",
                "add runtime selector behavior",
                "use runtime DTM/tablebase",
                "mutate topology during gameplay",
                "delete or overwrite rollback sources",
            ],
        },
        "post_approval_validation_required": [
            "Stage 5 conversion-preservation guardrail",
            "Stage 6 drive_to_edge h40 validation with historical validation bonus",
            "Stage 4 caveat/control check remains no-regression vs base control",
            "M1-M4 preservation tests",
            "KPK-to-KQK bridge/routing preservation tests",
            "rollback dry-run plan",
        ],
        "invariants": {
            "files_copied_or_replaced": False,
            "runtime_defaults_changed": False,
            "runtime_selector_implemented": False,
            "runtime_score_changes": False,
            "runtime_direct_routing": False,
            "runtime_dtm_or_tablebase_lookup": False,
            "gameplay_topology_mutation": False,
            "stage7_promotion": False,
            "stage8_training": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    prereqs = "\n".join(
        f"- {key}: `{value}`" for key, value in payload["prerequisites"].items()
    )
    caveats = "\n".join(
        f"- `{item['caveat_id']}`: `{item['status']}`; impact: `{item['replacement_impact']}`"
        for item in payload["known_caveats"]
    )
    allowed = "\n".join(
        f"- {item}" for item in payload["required_approval_scope_if_approved_later"]["allowed"]
    )
    forbidden = "\n".join(
        f"- {item}" for item in payload["required_approval_scope_if_approved_later"]["forbidden"]
    )
    validation = "\n".join(f"- {item}" for item in payload["post_approval_validation_required"])
    return f"""# KRK Retry1 Clean Stack Replacement Review Packet v0

Status: `{payload['status']}`

## Decision

- Replacement review ready: `{payload['decision']['replacement_review_ready']}`
- Implementation allowed by this packet: `{payload['decision']['implementation_allowed_by_this_packet']}`
- Clean stack replacement performed: `{payload['decision']['clean_stack_replacement_performed']}`
- Explicit human approval required before any file change: `{payload['decision']['explicit_human_approval_required_before_any_file_change']}`
- Recommended next step: `{payload['decision']['recommended_next_step']}`

## Prerequisites

{prereqs}

## Known Caveats

{caveats}

## Later Approval Scope

Allowed only if explicitly approved later:

{allowed}

Forbidden:

{forbidden}

## Post-Approval Validation Required

{validation}

## Boundary

This packet is review-only. It does not copy, replace, delete, promote, train, route, score, mutate topology, or change runtime defaults.
"""


def main() -> None:
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "json_output": str(OUT_JSON)}, indent=2))


if __name__ == "__main__":
    main()
