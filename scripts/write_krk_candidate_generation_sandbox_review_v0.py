#!/usr/bin/env python3
"""Write the KRK candidate-generation sandbox review packet.

This is design/review only. It does not implement runtime candidate generation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

SOURCE_ARTIFACTS = [
    "reports/strategy_arbitration/krk_candidate_proposal_coverage_v0.json",
    "reports/strategy_arbitration/krk_candidate_generation_strategy_review_v0.json",
    "reports/strategy_arbitration/krk_strategy_sequence_candidate_frames_v1.json",
    "reports/strategy_arbitration/krk_strategy_sequence_candidate_frame_quality_v1.json",
    "reports/strategy_arbitration/krk_candidate_frame_source_benchmark_v1.json",
    "reports/strategy_arbitration/krk_strategy_sequence_control_plane_decision_v1.json",
]

OUT_JSON = Path("reports/strategy_arbitration/krk_candidate_generation_sandbox_review_v0.json")
OUT_MD = Path("reports/strategy_arbitration/krk_candidate_generation_sandbox_review_v0.md")


RUNTIME_FALSE = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "runtime_selector_implemented": False,
    "runtime_candidate_generator_implemented": False,
    "runtime_terminals_added": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
}


def _load(path: str) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review_payload() -> dict[str, Any]:
    coverage = _load(SOURCE_ARTIFACTS[0])
    frame_quality = _load(SOURCE_ARTIFACTS[3])
    source_benchmark = _load(SOURCE_ARTIFACTS[4])
    decision = _load(SOURCE_ARTIFACTS[5])
    evidence = decision.get("evidence", {})
    return {
        "schema_version": "krk_candidate_generation_sandbox_review.v0",
        "causal_status": "review_packet_only_non_runtime",
        **RUNTIME_FALSE,
        "source_artifacts": SOURCE_ARTIFACTS,
        "decision": {
            "status": "candidate_generation_observation_sandbox_review_ready",
            "recommended_first_sandbox": "default_off_observation_only_candidate_generation",
            "implementation_authorized_by_this_packet": False,
            "runtime_sandbox_allowed_by_this_packet": False,
            "selector_allowed": False,
            "score_changes_allowed": False,
            "routing_changes_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "allowed_candidate_channels": [
            {
                "channel": "validated_provider_pack_proposals",
                "allowed_output": "visible candidate/proposal frames for protected validated providers",
                "source_evidence": "forced-provider capacity and visible provider proposal artifacts",
                "label_semantics": "capacity_evidence_not_ownership_label",
                "runtime_effect_allowed": "observation_only",
            },
            {
                "channel": "CandidateMoveFrame_legal_move_hypotheses",
                "allowed_output": "visible legal-move hypotheses with move-shape/post-move/safety terms",
                "source_evidence": "CandidateMoveFrame and progress-window candidate evidence",
                "label_semantics": "move_hypothesis_not_selector_decision",
                "runtime_effect_allowed": "observation_only",
            },
            {
                "channel": "PlanCapsule_sequence_candidates",
                "allowed_output": "visible bounded sequence-candidate frames and plan context",
                "source_evidence": "PlanCapsuleSpec and sequence-window diagnostics",
                "label_semantics": "sequence_candidate_not_runtime_commitment",
                "runtime_effect_allowed": "observation_only",
            },
            {
                "channel": "broader_KRK_strategy_proposal_candidates",
                "allowed_output": "visible strategy-family/context candidates from monitors and phase-boundary evidence",
                "source_evidence": "InternalTerminalSpec/StrategyMonitor evidence",
                "label_semantics": "strategy_candidate_not_provider_route",
                "runtime_effect_allowed": "observation_only",
            },
        ],
        "explicitly_forbidden": [
            "selecting_a_provider",
            "selecting_a_move",
            "changing_scores",
            "suppressing_providers",
            "routing_directly_to_a_provider",
            "direct_request_true",
            "promoting_Stage7",
            "training_Stage8",
            "runtime_DTM_or_tablebase",
            "gameplay_time_topology_mutation",
            "hidden_Python_routing",
            "treating_capacity_labels_as_selector_labels",
            "guardrail_validation_before_target_smoke",
        ],
        "generation_vs_selection": {
            "candidate_generation": (
                "Expands the visible consideration set by emitting traceable candidate/proposal "
                "frames with source terms and non-causal evidence."
            ),
            "selection": (
                "Chooses, scores, suppresses, or routes among candidates. Selection remains blocked "
                "and requires a separate review."
            ),
            "review_boundary": (
                "The proposed sandbox may emit candidates but must preserve the existing selected "
                "move/provider and score ordering."
            ),
        },
        "sandbox_modes": [
            {
                "mode": "A",
                "name": "observation_only_candidate_generation",
                "status": "recommended_first_runtime_sandbox_if_explicitly_approved_later",
                "behavior": "generate candidate frames after normal selection",
                "scoring_effect": 0.0,
                "routing_effect": "none",
                "selection_effect": "none",
            },
            {
                "mode": "B",
                "name": "proposal_set_expansion_only",
                "status": "review_later",
                "behavior": "make additional candidates visible to later non-causal evaluation",
                "scoring_effect": 0.0,
                "routing_effect": "none",
                "selection_effect": "none",
            },
            {
                "mode": "C",
                "name": "candidate_generation_plus_selector_handoff",
                "status": "not_allowed",
                "behavior": "candidate generator hands off to selector",
                "blocked_by": "requires separate selector review",
            },
        ],
        "required_candidate_frame_fields": [
            "generated_candidate_source",
            "provider_id_or_move_id",
            "source_terms",
            "capacity_evidence_type",
            "protected_or_stage7_or_heldout_flag",
            "direct_request_false",
            "score_delta_zero",
            "causal_status_sandbox_observation_only_or_candidate_generation_only",
        ],
        "supporting_evidence": {
            "protected_positive_capacity_candidates": evidence.get("protected_positive_capacity_candidates"),
            "protected_negative_capacity_ratio": evidence.get("protected_negative_capacity_ratio"),
            "stage7_training_row_count": evidence.get("stage7_training_row_count"),
            "progress_window_supported_move_h40_mate_count": evidence.get(
                "progress_window_supported_move_h40_mate_count"
            ),
            "candidate_proposal_coverage_status": (coverage.get("decision") or {}).get("status"),
            "frame_quality_status": (frame_quality.get("decision") or {}).get("status"),
            "source_benchmark_status": (source_benchmark.get("decision") or {}).get("status"),
        },
        "remaining_risks": [
            "validated provider pack includes negative-capacity candidates",
            "capacity labels are not ownership labels",
            "Stage 7 sequence candidates are held-out challenge evidence only",
            "selection policy remains blocked",
            "candidate explosion and performance risk",
            "accidental hidden selector risk",
            "observation-only data may still be too narrow for later selector design",
        ],
        "acceptance_criteria_before_implementation": {
            "observation_only_sandbox": [
                "explicit approval after this review",
                "default-off equivalence",
                "generated candidate count bounded",
                "no selected-move/provider delta",
                "score_delta = 0.0",
                "no topology mutation",
                "trace includes source terms",
                "Stage 7 rows remain held-out",
                "focused tests pass",
                "tiny smoke before any guardrail validation",
            ],
            "beyond_observation_only": [
                "separate review required",
                "selector semantics reviewed separately",
                "target smoke improvement required before guardrails",
            ],
        },
        "recommended_first_runtime_sandbox": {
            "name": "default_off_observation_only_candidate_generation",
            "implementation_status": "not_implemented",
            "authorization_status": "review_ready_requires_explicit_approval",
            "scoring": "none",
            "routing": "none",
            "selector": "none",
            "guardrails": "not_yet; default-off equivalence and tiny smoke first",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    ev = payload["supporting_evidence"]
    lines = [
        "# KRK Candidate-Generation Sandbox Review v0",
        "",
        "This packet reviews a possible default-off candidate-generation sandbox scope. It does not authorize or implement runtime behavior.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- recommended_first_sandbox: `{payload['decision']['recommended_first_sandbox']}`",
        f"- implementation_authorized_by_this_packet: `{payload['decision']['implementation_authorized_by_this_packet']}`",
        f"- runtime_sandbox_allowed_by_this_packet: `{payload['decision']['runtime_sandbox_allowed_by_this_packet']}`",
        "",
        "## Allowed Candidate Channels",
        "",
    ]
    for channel in payload["allowed_candidate_channels"]:
        lines.extend(
            [
                f"### {channel['channel']}",
                "",
                f"- allowed_output: {channel['allowed_output']}",
                f"- label_semantics: `{channel['label_semantics']}`",
                f"- runtime_effect_allowed: `{channel['runtime_effect_allowed']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Generation vs Selection",
            "",
            f"- candidate_generation: {payload['generation_vs_selection']['candidate_generation']}",
            f"- selection: {payload['generation_vs_selection']['selection']}",
            f"- review_boundary: {payload['generation_vs_selection']['review_boundary']}",
            "",
            "## Sandbox Modes",
            "",
        ]
    )
    for mode in payload["sandbox_modes"]:
        lines.extend(
            [
                f"- Mode {mode['mode']} `{mode['name']}`: `{mode['status']}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Supporting Evidence",
            "",
            f"- protected_positive_capacity_candidates: {ev['protected_positive_capacity_candidates']}",
            f"- protected_negative_capacity_ratio: {ev['protected_negative_capacity_ratio']}",
            f"- stage7_training_row_count: {ev['stage7_training_row_count']}",
            f"- progress_window_supported_move_h40_mate_count: {ev['progress_window_supported_move_h40_mate_count']}",
            f"- candidate_proposal_coverage_status: `{ev['candidate_proposal_coverage_status']}`",
            f"- frame_quality_status: `{ev['frame_quality_status']}`",
            f"- source_benchmark_status: `{ev['source_benchmark_status']}`",
            "",
            "## Explicitly Forbidden",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in payload["explicitly_forbidden"])
    lines.extend(
        [
            "",
            "## Remaining Risks",
            "",
        ]
    )
    lines.extend(f"- {risk}" for risk in payload["remaining_risks"])
    lines.extend(
        [
            "",
            "## Acceptance Criteria Before Implementation",
            "",
            "Observation-only sandbox:",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["acceptance_criteria_before_implementation"]["observation_only_sandbox"])
    lines.extend(
        [
            "",
            "Beyond observation-only:",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["acceptance_criteria_before_implementation"]["beyond_observation_only"])
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_review_payload()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
