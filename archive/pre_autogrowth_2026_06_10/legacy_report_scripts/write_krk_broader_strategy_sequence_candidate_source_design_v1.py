#!/usr/bin/env python3
"""Write design review for broader KRK strategy/sequence candidate sources."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
QUALITY_DECISION = Path("reports/strategy_arbitration/krk_candidate_proposal_quality_decision_v1.json")
GAP_REVIEW = Path("reports/strategy_arbitration/krk_candidate_generation_observation_gap_review_v1.json")
OUT_JSON = Path(
    "reports/strategy_arbitration/"
    "krk_broader_strategy_sequence_candidate_source_design_v1.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/"
    "krk_broader_strategy_sequence_candidate_source_design_v1.md"
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_payload(
    quality_decision: dict[str, Any] | None = None,
    gap_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    quality_decision = quality_decision or _load(QUALITY_DECISION)
    gap_review = gap_review or _load(GAP_REVIEW)
    return {
        "schema_version": "krk_broader_strategy_sequence_candidate_source_design.v1",
        "causal_status": "non_causal_design_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_candidate_generator_changes_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(QUALITY_DECISION), str(GAP_REVIEW)],
        "motivation": {
            "quality_decision_status": (quality_decision.get("decision") or {}).get("status"),
            "gap_review_status": (gap_review.get("decision") or {}).get("status"),
            "reason": "provider-pack and legal-move frames are visible but not quality-sufficient; PlanCapsule and broader strategy sources are absent from observation frames",
        },
        "candidate_source_contracts": [
            {
                "candidate_source": "plan_capsule_sequence_candidate",
                "purpose": "Expose bounded sequence/continuation candidates that are already present as plan/capsule evidence.",
                "required_fields": [
                    "plan_capsule_id",
                    "entry_terms_confirmed",
                    "progress_terms_available",
                    "exit_terms_available",
                    "abort_terms_available",
                    "ttl_white_moves",
                    "handoff_targets",
                    "source_terms",
                    "capacity_evidence_kind",
                    "direct_request=false",
                    "score_delta=0.0",
                    "causal_status=observation_only",
                ],
                "forbidden_uses": [
                    "force_plan_entry",
                    "alter_ttl",
                    "select_provider",
                    "change_scores",
                    "route_to_plan",
                ],
                "implementation_status": "design_only_requires_separate_review",
            },
            {
                "candidate_source": "broader_strategy_candidate",
                "purpose": "Expose strategy-level alternatives such as edge-net, king-support continuation, fence repair, mate-basin finish, or owner-exit candidates as visible hypotheses.",
                "required_fields": [
                    "strategy_id",
                    "strategy_family",
                    "source_monitor_records",
                    "licensed_provider_families",
                    "candidate_scope_terms",
                    "risk_terms",
                    "handoff_or_exit_terms",
                    "capacity_evidence_kind",
                    "direct_request=false",
                    "score_delta=0.0",
                    "causal_status=observation_only",
                ],
                "forbidden_uses": [
                    "select_strategy",
                    "suppress_current_provider",
                    "boost_provider",
                    "direct_role_to_provider_edge",
                    "mutate_topology",
                ],
                "implementation_status": "design_only_requires_separate_review",
            },
        ],
        "source_quality_requirements": [
            "candidate count must be bounded per state/source",
            "Stage 7 rows remain held-out challenge only",
            "capacity evidence remains separate from ownership labels",
            "source terms must be visible and explainable",
            "default-off equivalence must pass before any runtime source expansion",
            "source expansion alone must not trigger guardrails or selector review",
        ],
        "recommended_next_artifacts": [
            "reports/strategy_arbitration/krk_broader_strategy_sequence_candidate_source_review_v1.json",
            "reports/strategy_arbitration/krk_plan_capsule_sequence_candidate_observation_review_v1.json",
            "reports/strategy_arbitration/krk_broader_strategy_candidate_observation_review_v1.json",
        ],
        "forbidden_next_steps": [
            "runtime_selector",
            "score_changes",
            "provider_routing",
            "guardrail_campaign",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "hidden_python_controller",
            "runtime_source_expansion_without_review",
        ],
        "decision": {
            "status": "broader_strategy_sequence_candidate_source_design_ready",
            "implementation_allowed_by_this_artifact": False,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": "review_plan_capsule_and_broader_strategy_observation_sources",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Broader Strategy / Sequence Candidate Source Design v1",
        "",
        "This design responds to the candidate proposal quality decision. It does not implement runtime source expansion.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- implementation_allowed_by_this_artifact: `{payload['decision']['implementation_allowed_by_this_artifact']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Motivation",
        "",
        f"- quality_decision_status: `{payload['motivation']['quality_decision_status']}`",
        f"- gap_review_status: `{payload['motivation']['gap_review_status']}`",
        f"- reason: {payload['motivation']['reason']}",
        "",
        "## Candidate Source Contracts",
        "",
    ]
    for source in payload["candidate_source_contracts"]:
        lines.extend(
            [
                f"### {source['candidate_source']}",
                "",
                f"- purpose: {source['purpose']}",
                f"- implementation_status: `{source['implementation_status']}`",
                f"- required_fields: `{source['required_fields']}`",
                f"- forbidden_uses: `{source['forbidden_uses']}`",
                "",
            ]
        )
    lines.extend(["## Source Quality Requirements", ""])
    lines.extend(f"- {item}" for item in payload["source_quality_requirements"])
    lines.extend(["", "## Forbidden Next Steps", ""])
    lines.extend(f"- `{item}`" for item in payload["forbidden_next_steps"])
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
