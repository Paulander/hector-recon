#!/usr/bin/env python3
"""Review stage-conditioned scope for KRK candidate-generation refresh."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTCOME_REVIEW = Path(
    "reports/strategy_arbitration/krk_candidate_generation_cross_stage_label_outcome_review_v3.json"
)
POST_PROBE = Path(
    "reports/strategy_arbitration/krk_candidate_generation_refresh_probe_v2_cross_stage_labels.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_candidate_generation_stage_conditioned_scope_review_v3.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_candidate_generation_stage_conditioned_scope_review_v3.md"
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _classify_stage_family(stats: dict[str, Any]) -> str:
    support = int(stats.get("support") or 0)
    positive = int(stats.get("positive") or 0)
    negative = int(stats.get("negative") or 0)
    if support < 2:
        return "underpowered"
    if positive and not negative:
        return "candidate_generation_positive_scope"
    if negative and not positive:
        return "candidate_generation_risk_scope"
    return "mixed_needs_companion_terms"


def build_payload(
    outcome_review: dict[str, Any] | None = None,
    post_probe: dict[str, Any] | None = None,
) -> dict[str, Any]:
    outcome_review = outcome_review or _load(OUTCOME_REVIEW)
    post_probe = post_probe or _load(POST_PROBE)
    stage_family_rates = post_probe.get("stage_family_rates") or {}
    stage_scopes: dict[str, dict[str, Any]] = {}
    for key, stats in sorted(stage_family_rates.items()):
        stage, _, family = str(key).partition("|")
        entry = {
            "family": family,
            "support": stats.get("support"),
            "positive": stats.get("positive"),
            "negative": stats.get("negative"),
            "positive_rate": stats.get("positive_rate"),
            "scope_class": _classify_stage_family(stats),
        }
        stage_scopes.setdefault(stage, {"families": []})["families"].append(entry)
    for stage, scope in stage_scopes.items():
        families = scope["families"]
        scope["positive_scope_families"] = [
            item["family"]
            for item in families
            if item["scope_class"] == "candidate_generation_positive_scope"
        ]
        scope["risk_scope_families"] = [
            item["family"]
            for item in families
            if item["scope_class"] == "candidate_generation_risk_scope"
        ]
        scope["mixed_scope_families"] = [
            item["family"]
            for item in families
            if item["scope_class"] == "mixed_needs_companion_terms"
        ]
        scope["underpowered_families"] = [
            item["family"] for item in families if item["scope_class"] == "underpowered"
        ]
    outcome_status = (outcome_review.get("decision") or {}).get("status")
    return {
        "schema_version": "krk_candidate_generation_stage_conditioned_scope_review.v3",
        "causal_status": "non_causal_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(OUTCOME_REVIEW), str(POST_PROBE)],
        "input_status": outcome_status,
        "scope_review_goal": (
            "Decide whether the candidate-generation refresh should be scoped by "
            "active protected stage/landmark instead of treated as a global "
            "cross-stage candidate policy."
        ),
        "stage_scopes": stage_scopes,
        "interpretation": {
            "global_cross_stage_refresh_supported": False,
            "stage_conditioned_scope_supported_for_benchmark": (
                outcome_status
                == "cross_stage_capacity_labels_improve_in_sample_but_generalization_blocked"
            ),
            "selector_supported": False,
            "runtime_refresh_supported": False,
            "capacity_labels_are_not_ownership_labels": True,
            "stage4_requires_companion_terms": bool(
                stage_scopes.get("stage4", {}).get("mixed_scope_families")
            ),
            "stage5_has_positive_capacity_scopes": bool(
                stage_scopes.get("stage5", {}).get("positive_scope_families")
            ),
            "stage6_has_mixed_positive_and_risk_scopes": bool(
                stage_scopes.get("stage6", {}).get("positive_scope_families")
                and (
                    stage_scopes.get("stage6", {}).get("risk_scope_families")
                    or stage_scopes.get("stage6", {}).get("underpowered_families")
                )
            ),
        },
        "future_benchmark_requirements": [
            "benchmark stage-conditioned candidate emission separately from selection",
            "do not suppress risk-scope providers at runtime from capacity labels alone",
            "use mixed Stage 4 cells only with companion visible context terms",
            "keep Stage 7 held out as challenge evidence",
            "report candidate-generation recall and risk by protected stage",
            "require separate runtime review before any candidate-generator refresh",
        ],
        "forbidden_uses": [
            "runtime_selector",
            "provider_suppression",
            "score_delta",
            "direct_provider_routing",
            "stage7_training_rows",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
        ],
        "decision": {
            "status": "stage_conditioned_candidate_generation_scope_review_ready",
            "selector_allowed": False,
            "runtime_candidate_generator_refresh_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": "benchmark_stage_conditioned_candidate_generation_non_causal",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Candidate-Generation Stage-Conditioned Scope Review v3",
        "",
        payload["scope_review_goal"],
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- runtime_candidate_generator_refresh_allowed: `{payload['decision']['runtime_candidate_generator_refresh_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Stage Scopes",
        "",
    ]
    for stage, scope in payload["stage_scopes"].items():
        lines.extend(
            [
                f"### {stage}",
                "",
                f"- positive_scope_families: `{scope['positive_scope_families']}`",
                f"- risk_scope_families: `{scope['risk_scope_families']}`",
                f"- mixed_scope_families: `{scope['mixed_scope_families']}`",
                f"- underpowered_families: `{scope['underpowered_families']}`",
                "",
            ]
        )
    lines.extend(["## Interpretation", ""])
    for key, value in payload["interpretation"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Future Benchmark Requirements", ""])
    lines.extend(f"- `{item}`" for item in payload["future_benchmark_requirements"])
    lines.extend(["", "## Forbidden Uses", ""])
    lines.extend(f"- `{item}`" for item in payload["forbidden_uses"])
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
