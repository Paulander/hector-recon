#!/usr/bin/env python3
"""Propose Stage 7 family-specific support adapters from family diagnosis.

This is non-causal. It derives narrow adapter proposals only when visible
current terms separate a forced-success family from non-converting families for
the same provider. If terms do not separate, the candidate remains diagnostic.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _safe_id(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value).strip("_")


def _probe_terms(family: dict[str, Any], provider: str, key: str) -> set[str]:
    probe = (
        family.get("forced_provider_results", {})
        .get(provider, {})
        .get("first_move_probe", {})
    )
    values = probe.get(key)
    if not isinstance(values, list):
        return set()
    return {str(item) for item in values}


def _result_for_provider(family: dict[str, Any], provider: str) -> str:
    payload = family.get("forced_provider_results", {}).get(provider, {})
    if not isinstance(payload, dict):
        return "missing"
    if payload.get("result") == "mate" or payload.get("h80_result") == "mate":
        return "mate"
    return str(payload.get("h80_result") or payload.get("result") or "unknown")


def _terms_separate_target(
    *,
    family: dict[str, Any],
    provider: str,
    required_terms: set[str],
    all_families: list[dict[str, Any]],
) -> dict[str, Any]:
    target_terms = _probe_terms(family, provider, "current_terms")
    target_matches = required_terms <= target_terms
    false_positive_families: list[str] = []
    for other in all_families:
        if other.get("state_id") == family.get("state_id"):
            continue
        other_terms = _probe_terms(other, provider, "current_terms")
        other_result = _result_for_provider(other, provider)
        if required_terms <= other_terms and other_result != "mate":
            false_positive_families.append(str(other.get("state_id")))
    return {
        "target_matches": target_matches,
        "false_positive_families": false_positive_families,
        "separates": bool(target_matches and not false_positive_families),
    }


def _proposal_for_family(
    *,
    family: dict[str, Any],
    provider: str,
    required_terms: set[str],
    separation: dict[str, Any],
) -> dict[str, Any]:
    role_id = "krk.box_shrink_to_drive_repair"
    provider_node = f"skill.{provider}"
    source_role_script = "script.krk.successor.box_shrink_to_drive_repair_affordance"
    suffix = str(family.get("state_id", "state.unknown")).removeprefix("state.")
    provider_suffix = provider.removeprefix("krk.").replace(".", "_")
    relation = {
        "source_role_script": source_role_script,
        "target_provider_skill": provider_node,
        "relation_type": "visible_role_provider_support",
        "initial_weight": 0.05,
        "trainable": True,
        "causal_status": "non_causal_scaffold",
        "direct_graph_edge_emitted": False,
        "requires_support_adapter": True,
        "support_required_terms": sorted(required_terms),
        "support_veto_terms": ["mate_in_one_available"],
        "source_terms": sorted(required_terms | {f"forced_{provider_suffix}_converted"}),
        "adapter_contract": {
            "kind": "gated_visible_support_adapter",
            "confirm_when": [
                "source_role_script_confirmed",
                "role_contract_met",
                *sorted(required_terms),
                "provider_execution_eligible",
            ],
            "must_not": [
                "request_provider_before_role_confirmation",
                "bypass visible provider eligibility",
                "mutate default_topology",
            ],
        },
    }
    status = "sandbox_ready" if separation["separates"] else "needs_more_terms"
    return {
        "schema_version": "role_provider_support_proposal.v1",
        "causal_status": "non_causal",
        "target_role": role_id,
        "target_provider": provider,
        "source_family_id": family.get("family_id"),
        "source_state_id": family.get("state_id"),
        "source_forced_provider_result": (
            family.get("forced_provider_results", {}).get(provider, {})
        ),
        "proposal_status": status,
        "candidate_id": (
            f"cand.krk.box_shrink.family_{suffix}.{provider_suffix}_visible_support.v1"
        ),
        "term_separation": separation,
        "proposed_support_relations": [relation] if separation["separates"] else [],
        "proposed_relation_count": 1 if separation["separates"] else 0,
        "unsafe_direct_graph_edges_emitted": False,
        "sandbox_compile_strategy": "compile_gated_support_adapter_not_direct_sub_edge",
        "requires_role_provider_augmentation": provider != "krk.drive_to_edge",
        "required_validation": [
            "compile_sandbox_topology_with_gated_support_adapter",
            "default_off_equivalence",
            "stage7_target_smoke",
            "stage6_drive_guardrail",
            "stage5_fence_guardrail",
            "m1_m4_preservation",
        ],
        "hard_blocks": [
            "do_not_insert_into_default_topology",
            "do_not_train_stage8",
            "do_not_promote_stage7_without_guardrails",
            "do_not_make_candidate_causal_without_sandbox_validation",
        ],
    }


def propose_family_support_adapters(*, family_diagnosis_path: Path) -> dict[str, Any]:
    family_diagnosis = _load_json(family_diagnosis_path)
    families = list(family_diagnosis.get("families") or [])
    provider_splits = family_diagnosis.get("provider_term_splits", {})
    proposals: list[dict[str, Any]] = []
    for family in families:
        provider = family.get("best_forced_provider")
        if not provider:
            continue
        provider = str(provider)
        split = provider_splits.get(provider, {})
        current_terms = set(
            split.get("current_terms", {}).get("success_common_minus_failure_common", [])
        )
        # Fall back to target-only terms if there is no split; still require a
        # separation pass before declaring sandbox-ready.
        if not current_terms:
            current_terms = _probe_terms(family, provider, "current_terms")
        separation = _terms_separate_target(
            family=family,
            provider=provider,
            required_terms=current_terms,
            all_families=families,
        )
        proposals.append(_proposal_for_family(
            family=family,
            provider=provider,
            required_terms=current_terms,
            separation=separation,
        ))

    return {
        "schema_version": "stage7_family_support_adapter_proposals.v1",
        "causal_status": "non_causal",
        "source_family_diagnosis": str(family_diagnosis_path),
        "proposal_count": len(proposals),
        "sandbox_ready_count": sum(1 for item in proposals if item.get("proposal_status") == "sandbox_ready"),
        "proposals": proposals,
        "recommended_next_action": (
            "compile_sandbox_ready_family_adapters"
            if any(item.get("proposal_status") == "sandbox_ready" for item in proposals)
            else "collect_more_family_terms_before_adapter_compilation"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Propose Stage 7 family-specific support adapters")
    parser.add_argument("--family-diagnosis", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--split-output-dir", type=Path, default=None)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = propose_family_support_adapters(family_diagnosis_path=args.family_diagnosis)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.split_output_dir:
        args.split_output_dir.mkdir(parents=True, exist_ok=True)
        for proposal in payload.get("proposals") or []:
            candidate_id = str(proposal.get("candidate_id") or "candidate")
            path = args.split_output_dir / f"{_safe_id(candidate_id)}.json"
            path.write_text(json.dumps(proposal, indent=2) + "\n", encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
