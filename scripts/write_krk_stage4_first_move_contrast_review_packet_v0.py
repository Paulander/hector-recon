#!/usr/bin/env python3
"""Write a review packet for a narrow Stage 4 first-move contrast sandbox."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SEQUENCE_CANDIDATES = ROOT / "reports/krk_stage4_sequence_candidate_review_v0.json"
FEATURE_REVIEW = ROOT / "reports/krk_stage4_first_move_feature_review_v0.json"
STRATIFIED_VALIDATION = ROOT / "reports/krk_stage4_stratified_contrast_validation_v0.json"
OUTPUT_JSON = ROOT / "reports/krk_stage4_first_move_contrast_runtime_review_packet_v0.json"
OUTPUT_MD = ROOT / "reports/krk_stage4_first_move_contrast_runtime_review_packet_v0.md"

SCHEMA_VERSION = "krk_stage4_first_move_contrast_runtime_review_packet.v0"


COMMON_FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "runtime_selector_implemented": False,
    "runtime_score_changes": False,
    "runtime_direct_routing": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "hidden_python_controller": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_payload(
    *,
    sequence_candidates: dict[str, Any] | None = None,
    feature_review: dict[str, Any] | None = None,
    stratified_validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sequence_candidates = sequence_candidates or _load(SEQUENCE_CANDIDATES)
    feature_review = feature_review or _load(FEATURE_REVIEW)
    stratified_validation = stratified_validation or _load(STRATIFIED_VALIDATION)

    evidence_passed = (
        sequence_candidates.get("classification", {}).get("primary")
        == "stage4_first_move_ranking_gap"
        and feature_review.get("decision", {}).get("status")
        == "stage4_first_move_feature_contrast_found_single_state"
        and stratified_validation.get("summary", {}).get("gap_variant_count") == 4
    )
    status = (
        "stage4_first_move_contrast_runtime_review_ready_pending_explicit_approval"
        if evidence_passed
        else "stage4_first_move_contrast_review_needs_more_evidence"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "review_packet_only",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/krk_stage4_sequence_candidate_review_v0.json",
            "reports/krk_stage4_first_move_feature_review_v0.json",
            "reports/krk_stage4_stratified_contrast_validation_v0.json",
        ],
        "review_summary": {
            "evidence_passed": evidence_passed,
            "sequence_candidate_status": sequence_candidates.get("classification", {}).get("primary"),
            "feature_review_status": feature_review.get("decision", {}).get("status"),
            "stratified_validation_status": stratified_validation.get("decision", {}).get("status"),
            "stratified_gap_variant_count": stratified_validation.get("summary", {}).get("gap_variant_count"),
            "positive_terms": feature_review.get("interpretation", {}).get("candidate_positive_terms", []),
            "failure_terms": feature_review.get("interpretation", {}).get("candidate_failure_terms", []),
        },
        "approved_if_later_explicitly_authorized": {
            "sandbox_id": "sandbox.krk.stage4_first_move_contrast_v0",
            "default_off": True,
            "scope": {
                "domain": "KRK",
                "stage": "stage4",
                "active_landmark_label": "edge_trap_wrong_tempo",
                "exact_state_exception_allowed": False,
                "stage5_stage6_guardrails_required_before_promotion": True,
                "stage7_allowed": False,
                "stage8_allowed": False,
            },
            "allowed_runtime_behavior": [
                "enumerate legal CandidateMoveFrame first-move hypotheses in Stage 4 contexts",
                "attach visible first-move contrast terms to candidate frames",
                "apply a bounded default-off support only if a later packet explicitly authorizes it",
            ],
            "candidate_positive_terms": feature_review.get("interpretation", {}).get(
                "candidate_positive_terms",
                [],
            ),
            "candidate_failure_terms": feature_review.get("interpretation", {}).get(
                "candidate_failure_terms",
                [],
            ),
        },
        "explicitly_forbidden": [
            "implementation_without_explicit_approval",
            "default_enablement",
            "exact_state_or_exact_move_runtime_exception",
            "runtime_dtm_or_tablebase",
            "hidden_python_controller",
            "broad_stage0_penalty",
            "provider_suppression",
            "selector_training_from_forced_first_move_labels",
            "stage7_training_or_promotion",
            "stage8_training",
            "gameplay_topology_mutation",
        ],
        "implementation_boundaries": {
            "implementation_allowed_by_this_packet": False,
            "requires_later_explicit_approval": True,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "promotion_allowed": False,
            "guardrails_before_target_smoke": False,
            "target_smoke_before_guardrails": True,
        },
        "acceptance_if_later_approved": {
            "default_off_equivalence_passes": True,
            "target_smoke_required": [
                "identity Stage 4 caveat state",
                "file-mirrored Stage 4 caveat state",
                "rank-mirrored Stage 4 caveat state",
                "rotated Stage 4 caveat state",
            ],
            "default_off_selected_move_delta_count": 0,
            "default_off_score_delta_count": 0,
            "stage7_training_row_count": 0,
            "stage8_training_row_count": 0,
            "runtime_dtm_or_tablebase_lookup": False,
            "topology_mutation": False,
        },
        "risks": [
            "Evidence is synthetic/symmetry-stratified, not broad random KRK coverage.",
            "The scope is Stage 4-specific and must not become a general selector.",
            "Forced-first-move conversion labels are contrast evidence, not ownership labels.",
            "A broad penalty on stage0_basin would risk protected safe-preservation behavior.",
        ],
        "decision": {
            "status": status,
            "runtime_review_ready": bool(evidence_passed),
            "implementation_authorized_by_this_packet": False,
            "requires_explicit_approval_before_implementation": True,
            "runtime_changes_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    summary = payload["review_summary"]
    decision = payload["decision"]
    lines = [
        "# KRK Stage 4 First-Move Contrast Runtime Review Packet v0",
        "",
        "## Decision",
        "",
        f"- status: `{decision['status']}`",
        f"- runtime_review_ready: `{decision['runtime_review_ready']}`",
        "- implementation_authorized_by_this_packet: `false`",
        "- requires_explicit_approval_before_implementation: `true`",
        "",
        "## Evidence",
        "",
        f"- sequence_candidate_status: `{summary['sequence_candidate_status']}`",
        f"- feature_review_status: `{summary['feature_review_status']}`",
        f"- stratified_validation_status: `{summary['stratified_validation_status']}`",
        f"- stratified_gap_variant_count: `{summary['stratified_gap_variant_count']}`",
        f"- positive_terms: `{summary['positive_terms']}`",
        f"- failure_terms: `{summary['failure_terms']}`",
        "",
        "## Approved Scope If Later Explicitly Authorized",
        "",
        "- default-off Stage 4 first-move contrast sandbox only",
        "- CandidateMoveFrame legal first-move hypotheses only",
        "- no exact-state or exact-move runtime exception",
        "- no selector, provider suppression, broad stage0 penalty, Stage 7 promotion, or Stage 8 training",
        "",
        "## Risks",
        "",
    ]
    lines.extend(f"- {risk}" for risk in payload["risks"])
    lines.extend([
        "",
        "## Boundaries",
        "",
        "- This packet does not implement or authorize runtime behavior.",
        "- A later explicit approval is required before any sandbox code is added.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(json.dumps({
        "decision": payload["decision"]["status"],
        "runtime_review_ready": payload["decision"]["runtime_review_ready"],
        "implementation_authorized_by_this_packet": False,
    }, indent=2))


if __name__ == "__main__":
    main()
