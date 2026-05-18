#!/usr/bin/env python3
"""Analyze residual Stage 7 Plan Capsule owned-arbitration failures.

This is a replay-free diagnostic: it reads a landmark diagnostic artifact and
groups the remaining max-plies cases by visible plan-capsule ownership/support
evidence. It does not change runtime behavior.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


CAPSULE_ID = "krk.post_box_shrink_continuation"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _plan_marker(evidence: dict[str, Any]) -> dict[str, Any]:
    return _as_dict(_as_dict(evidence.get("plan_capsule_markers")).get(CAPSULE_ID))


def _visible_terms(evidence: dict[str, Any]) -> dict[str, Any]:
    return _as_dict(evidence.get("visible_terms"))


def _selected_license(evidence: dict[str, Any]) -> dict[str, Any]:
    return _as_dict(evidence.get("plan_capsule_selected_license"))


def _owned_arbitration(evidence: dict[str, Any]) -> dict[str, Any]:
    return _as_dict(evidence.get("visible_stage7_plan_capsule_owned_arbitration"))


def _failure_rows(diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for packet in diagnostic.get("handoff_packets") or []:
        if not isinstance(packet, dict) or packet.get("phase") != "post_opponent_reply":
            continue
        evidence = _as_dict(packet.get("evidence_terms"))
        outcome = evidence.get("playout_result") or packet.get("observed_outcome")
        if outcome != "max_plies":
            continue

        marker = _plan_marker(evidence)
        license_payload = _selected_license(evidence)
        arbitration = _owned_arbitration(evidence)
        terms = _visible_terms(evidence)
        selected_provider = (
            license_payload.get("provider_skill_id")
            or arbitration.get("selected_skill")
            or evidence.get("successor_selected_skill")
            or "unknown"
        )
        selected_move = (
            license_payload.get("move")
            or arbitration.get("selected_move")
            or evidence.get("successor_selected_move")
            or evidence.get("move")
        )
        row = {
            "packet_id": packet.get("packet_id"),
            "outcome": outcome,
            "fen": evidence.get("fen"),
            "post_reply_fen": evidence.get("post_reply_fen"),
            "post_reply_state_signature": evidence.get("post_reply_state_signature"),
            "initial_box_shrink_move": evidence.get("move"),
            "black_reply": evidence.get("black_reply"),
            "selected_provider": selected_provider,
            "selected_move": selected_move,
            "raw_selected_skill": arbitration.get("raw_selected_skill"),
            "raw_selected_move": arbitration.get("raw_selected_move"),
            "raw_selected_score": arbitration.get("raw_selected_score"),
            "selected_score": arbitration.get("selected_score"),
            "owned_arbitration_candidate_count": arbitration.get("candidate_count"),
            "plan_status": _as_dict(marker.get("plan_state")).get("plan_status")
            or evidence.get("plan_capsule_status"),
            "ttl_remaining": _as_dict(marker.get("plan_state")).get("ttl_remaining"),
            "entry_terms_met": _as_list(marker.get("entry_terms_met")),
            "progress_terms_met": _as_list(marker.get("progress_terms_met")),
            "exit_terms_met": _as_list(marker.get("exit_terms_met")),
            "abort_terms_met": _as_list(marker.get("abort_terms_met")),
            "license_source_terms": _as_list(license_payload.get("source_terms")),
            "license_progress_terms": _as_list(license_payload.get("progress_terms")),
            "license_move_shape_terms": _as_list(license_payload.get("move_shape_terms")),
            "license_post_move_terms": _as_list(license_payload.get("post_move_terms")),
            "failure_classes": _as_list(evidence.get("failure_classes")),
            "semantic_alignment_status": evidence.get("semantic_alignment_status"),
            "reward_contract_mismatch": bool(
                evidence.get("reward_contract_mismatch")
                or terms.get("reward_contract_mismatch")
            ),
            "visible_terms": {
                key: bool(terms.get(key))
                for key in (
                    "box_shrink_drive_repair_available",
                    "drive_to_edge_role_confirmed",
                    "repair_or_reestablish_cut_available",
                    "fence_or_cut_restored",
                    "fence_or_cut_not_preserved",
                    "edge_trap_role_confirmed",
                    "safe_check_available",
                    "safe_followup_available",
                    "stagnation_avoided",
                    "white_king_can_improve_support",
                    "white_king_support_improves",
                    "enemy_king_mobility_decreases",
                    "mate_in_one_available",
                )
            },
        }
        rows.append(row)
    return rows


def _count_terms(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        for term in row.get(field) or []:
            counter[str(term)] += 1
    return dict(counter.most_common())


def _group_rows(rows: list[dict[str, Any]], *fields: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        key = "|".join(str(row.get(field) or "unknown") for field in fields)
        counter[key] += 1
    return dict(counter.most_common())


def analyze_owned_failures(diagnostic: dict[str, Any]) -> dict[str, Any]:
    rows = _failure_rows(diagnostic)
    provider_counts = _group_rows(rows, "selected_provider")
    provider_semantic_counts = _group_rows(rows, "selected_provider", "semantic_alignment_status")
    provider_raw_counts = _group_rows(rows, "selected_provider", "raw_selected_skill")
    failure_class_counts = Counter(
        str(cls) for row in rows for cls in (row.get("failure_classes") or ["unclassified"])
    )
    visible_true_by_provider: dict[str, dict[str, int]] = {}
    for row in rows:
        provider = str(row.get("selected_provider") or "unknown")
        counter = visible_true_by_provider.setdefault(provider, defaultdict(int))  # type: ignore[arg-type]
        for term, value in (row.get("visible_terms") or {}).items():
            if value:
                counter[term] += 1

    diagnosis: list[str] = []
    if rows and provider_counts:
        diagnosis.append("capsule_owned_failures_are_provider_specific")
    if provider_counts.get("krk.edge_trap_close", 0):
        diagnosis.append("edge_trap_close_ownership_still_has_max_plies_residuals")
    if provider_counts.get("krk.fence_established", 0):
        diagnosis.append("fence_established_ownership_still_has_max_plies_residuals")
    if any(row.get("raw_selected_skill") == "krk.stage0_basin" for row in rows):
        diagnosis.append("owned_arbitration_overrode_stage0_basin_but_conversion_still_failed")
    if any(row.get("reward_contract_mismatch") for row in rows):
        diagnosis.append("upstream_reward_contract_mismatch_remains_in_failure_set")

    next_actions = [
        "do_not_promote_stage7_plan_capsule",
        "do_not_increase_broad_support_bonus",
        "derive provider-specific post-owned-window audits for edge_trap_close and fence_established residuals",
    ]
    if provider_counts.get("krk.edge_trap_close", 0):
        next_actions.append("audit why edge_trap_close licensed moves fail despite visible progress terms")
    if provider_counts.get("krk.fence_established", 0):
        next_actions.append("audit whether fence_established is acting as repair, re-establish, or stale fallback")

    return {
        "schema_version": "stage7_plan_capsule_owned_failure_analysis.v1",
        "causal_status": "non_causal",
        "capsule_id": CAPSULE_ID,
        "sample_count": diagnostic.get("total"),
        "playout_results": diagnostic.get("playouts"),
        "shadow_candidate_count": diagnostic.get("shadow_candidate_count"),
        "summary_counters": {
            "plan_capsule_active_decision_count": diagnostic.get("plan_capsule_active_decision_count"),
            "plan_capsule_supported_suggestion_count": diagnostic.get("plan_capsule_supported_suggestion_count"),
            "plan_capsule_selected_supported_count": diagnostic.get("plan_capsule_selected_supported_count"),
            "plan_capsule_owned_arbitration_selected_count": diagnostic.get("plan_capsule_owned_arbitration_selected_count"),
            "plan_capsule_active_without_support_count": diagnostic.get("plan_capsule_active_without_support_count"),
            "plan_capsule_selected_supported_by_outcome": diagnostic.get("plan_capsule_selected_supported_by_outcome"),
            "plan_capsule_owned_arbitration_provider_by_outcome": diagnostic.get("plan_capsule_owned_arbitration_provider_by_outcome"),
            "semantic_alignment_status_counts": diagnostic.get("semantic_alignment_status_counts"),
        },
        "max_plies_rows_analyzed": len(rows),
        "selected_provider_counts": provider_counts,
        "selected_provider_by_semantic_alignment": provider_semantic_counts,
        "selected_provider_by_raw_selected_skill": provider_raw_counts,
        "failure_class_counts": dict(failure_class_counts.most_common()),
        "entry_terms_met_counts": _count_terms(rows, "entry_terms_met"),
        "progress_terms_met_counts": _count_terms(rows, "progress_terms_met"),
        "exit_terms_met_counts": _count_terms(rows, "exit_terms_met"),
        "abort_terms_met_counts": _count_terms(rows, "abort_terms_met"),
        "license_move_shape_term_counts": _count_terms(rows, "license_move_shape_terms"),
        "license_progress_term_counts": _count_terms(rows, "license_progress_terms"),
        "license_post_move_term_counts": _count_terms(rows, "license_post_move_terms"),
        "visible_true_by_provider": {
            provider: dict(counter)
            for provider, counter in sorted(visible_true_by_provider.items())
        },
        "representative_failures": rows[:12],
        "diagnosis": diagnosis,
        "next_actions": next_actions,
    }


def _write_md(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Stage 7 Plan Capsule Owned-Failure Analysis",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"Capsule: `{payload['capsule_id']}`",
        f"Samples: `{payload.get('sample_count')}`",
        f"Playouts: `{payload.get('playout_results')}`",
        f"Shadow candidates: `{payload.get('shadow_candidate_count')}`",
        f"Max-plies rows analyzed: `{payload.get('max_plies_rows_analyzed')}`",
        "",
        "## Provider Buckets",
        "",
    ]
    for key, value in (payload.get("selected_provider_counts") or {}).items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Provider By Semantic Alignment", ""])
    for key, value in (payload.get("selected_provider_by_semantic_alignment") or {}).items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Failure Classes", ""])
    for key, value in (payload.get("failure_class_counts") or {}).items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Diagnosis", ""])
    for item in payload.get("diagnosis") or []:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Next Actions", ""])
    for item in payload.get("next_actions") or []:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This analysis is replay-free and non-causal. It must not promote Stage 7, mutate topology, or alter runtime routing.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("diagnostic", type=Path)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = analyze_owned_failures(_load_json(args.diagnostic))
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_md(payload, args.markdown_output)
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
