#!/usr/bin/env python3
"""Review KRK strategy-arbiter observation frames for separability.

This is a replay-free report over trace-only observation metadata. It decides
whether the observation layer is ready to support sandbox design, or whether the
trace needs richer non-causal context before any causal work.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OBSERVATIONS = Path("reports/krk_strategy_arbiter_observation_frames_v0.json")
OUT_JSON = Path("reports/krk_strategy_arbiter_observation_separability_review_v0.json")
OUT_MD = Path("reports/krk_strategy_arbiter_observation_separability_review_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _record_term_counts(record: dict[str, Any]) -> int:
    observation = record.get("observation") if isinstance(record.get("observation"), dict) else {}
    return len(list(observation.get("source_terms", []) or []))


def _proposal_provider_count(record: dict[str, Any]) -> int:
    observation = record.get("observation") if isinstance(record.get("observation"), dict) else {}
    unique_provider_count = observation.get("unique_provider_count")
    if unique_provider_count is not None:
        return int(unique_provider_count or 0)
    providers = {
        str(candidate.get("provider_id") or "unknown")
        for candidate in list(observation.get("provider_candidates", []) or [])
        if isinstance(candidate, dict)
    }
    return len(providers)


def build_review(root: Path = ROOT) -> dict[str, Any]:
    payload = _load_json(OBSERVATIONS)
    records = list(payload.get("records", []) or [])
    stage_counts = Counter(str(record.get("source_stage") or "unknown") for record in records)
    selected_provider_counts = Counter(
        str(record.get("selected_provider") or "unknown") for record in records
    )
    term_count_distribution = Counter(str(_record_term_counts(record)) for record in records)
    proposal_provider_distribution = Counter(
        str(_proposal_provider_count(record)) for record in records
    )
    stage7_records = [
        record for record in records if str(record.get("source_stage") or "") == "stage7"
    ]
    stage7_selected = Counter(
        str(record.get("selected_provider") or "unknown") for record in stage7_records
    )
    underinstrumented_records = [
        str(record.get("state_id") or record.get("frame_id") or "unknown")
        for record in records
        if _record_term_counts(record) <= 1
    ]
    single_provider_records = [
        str(record.get("state_id") or record.get("frame_id") or "unknown")
        for record in records
        if _proposal_provider_count(record) <= 1
    ]
    sandbox_ready = False
    status = "observation_context_underinstrumented"
    if records and not underinstrumented_records and single_provider_records:
        status = "observation_provider_diversity_underinstrumented"
    elif records and not underinstrumented_records and not single_provider_records:
        status = "observation_frames_ready_for_non_causal_selector_probe"
    recommended_next = (
        "enrich_trace_only_observation_with_existing_context_terms"
        if status == "observation_context_underinstrumented"
        else "enrich_trace_only_observation_with_provider_summary"
        if status == "observation_provider_diversity_underinstrumented"
        else "run_replay_free_observation_selector_probe"
    )
    findings = [
        "Stage7 holdout rows are visible and mostly selected by krk.stage0_basin.",
    ]
    if underinstrumented_records:
        findings.append(
            "Observation source terms are under-instrumented; most records expose only active_landmark_label."
        )
    else:
        findings.append(
            "Trace-only KRK context terms are now present in observation source terms."
        )
    if single_provider_records:
        findings.append(
            "Several rows expose only one provider family in the retained proposals, limiting strategy separability."
        )
    else:
        findings.append(
            "Provider summaries expose multiple provider families for selector analysis."
        )
    findings.append(
        "The current observation export is useful for auditability but is not a causal sandbox."
    )
    return {
        "schema_version": "krk_strategy_arbiter_observation_separability_review.v0",
        "causal_status": "non_causal_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "source_artifact": str(OBSERVATIONS),
        "record_count": len(records),
        "stage_counts": dict(sorted(stage_counts.items())),
        "selected_provider_counts": dict(sorted(selected_provider_counts.items())),
        "term_count_distribution": dict(sorted(term_count_distribution.items())),
        "proposal_provider_distribution": dict(sorted(proposal_provider_distribution.items())),
        "stage7_selected_provider_counts": dict(sorted(stage7_selected.items())),
        "underinstrumented_record_count": len(underinstrumented_records),
        "underinstrumented_records": underinstrumented_records,
        "single_provider_record_count": len(single_provider_records),
        "single_provider_records": single_provider_records,
        "findings": findings,
        "decision": {
            "status": status,
            "sandbox_ready": sandbox_ready,
            "runtime_arbiter_allowed": False,
            "recommended_next_step": recommended_next
        },
        "blocked_next_steps": [
            "runtime_arbiter",
            "provider_support_adapter",
            "score_bonus_or_penalty",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training"
        ],
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# KRK Strategy Arbiter Observation Separability Review v0",
        "",
        "This is a replay-free review of trace-only observation frames.",
        "",
        "## Summary",
        "",
        f"- Records: `{payload['record_count']}`",
        f"- Stage counts: `{payload['stage_counts']}`",
        f"- Selected provider counts: `{payload['selected_provider_counts']}`",
        f"- Source-term count distribution: `{payload['term_count_distribution']}`",
        f"- Proposal-provider count distribution: `{payload['proposal_provider_distribution']}`",
        f"- Under-instrumented records: `{payload['underinstrumented_record_count']}`",
        f"- Single-provider records: `{payload['single_provider_record_count']}`",
        "",
        "## Findings",
        "",
    ]
    lines.extend(f"- {finding}" for finding in payload["findings"])
    lines.extend([
        "",
        "## Decision",
        "",
        f"Status: `{payload['decision']['status']}`",
        f"Sandbox ready: `{payload['decision']['sandbox_ready']}`",
        f"Runtime arbiter allowed: `{payload['decision']['runtime_arbiter_allowed']}`",
        f"Recommended next step: `{payload['decision']['recommended_next_step']}`",
        "",
        "The next step should remain trace-only. Do not add provider support, score changes, Stage 7 repair, Stage 7 promotion, or Stage 8 training.",
    ])
    (ROOT / path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload, OUT_MD)


if __name__ == "__main__":
    main()
