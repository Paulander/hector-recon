#!/usr/bin/env python3
"""Audit Stage 7 box-shrink successor ownership candidates.

This consumes the non-causal structural candidate audit and the original Stage 7
diagnostic trace. It classifies observed successor ownership patterns into
candidate handoff roles without changing runtime behavior.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from audit_stage7_structural_candidates import _derived_terms, _load_json, _packets_by_phase, _representative
except ModuleNotFoundError:
    _audit_module_path = Path(__file__).resolve().with_name("audit_stage7_structural_candidates.py")
    _audit_spec = importlib.util.spec_from_file_location("audit_stage7_structural_candidates", _audit_module_path)
    if _audit_spec is None or _audit_spec.loader is None:
        raise
    _audit_module = importlib.util.module_from_spec(_audit_spec)
    _audit_spec.loader.exec_module(_audit_module)
    _derived_terms = _audit_module._derived_terms
    _load_json = _audit_module._load_json
    _packets_by_phase = _audit_module._packets_by_phase
    _representative = _audit_module._representative


ROLE_IDS = (
    "krk.box_shrink_to_edge_trap_handoff",
    "krk.box_shrink_to_drive_repair",
    "krk.box_shrink_post_reply_continuation",
)


def _status_for_role(role_id: str, positive: int, negative: int, unsupported: int) -> str:
    if role_id == "krk.box_shrink_to_edge_trap_handoff" and positive and not negative:
        return "sandbox_candidate"
    if role_id == "krk.box_shrink_post_reply_continuation" and negative:
        return "needs_role_split_or_successor_sweep"
    if unsupported:
        return "needs_counterfactual_evidence"
    return "no_current_evidence"


def _role_term_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, Counter] = {
        "box_area_decreased_after_own_move": Counter(),
        "box_area_not_increased_after_reply": Counter(),
        "fence_or_cut_preserved": Counter(),
        "rook_safe_after_reply": Counter(),
        "enemy_king_mobility_reduced": Counter(),
    }
    for evidence in rows:
        terms = _derived_terms(evidence)
        for key in counts:
            value = terms.get(key)
            if value is True:
                bucket = "true"
            elif value is False:
                bucket = "false"
            else:
                bucket = "unknown"
            counts[key][bucket] += 1
    return {key: dict(counter) for key, counter in counts.items()}


def audit_successor_ownership(
    *,
    candidate_audit_path: Path,
    diagnostic_path: Path,
) -> dict[str, Any]:
    candidate_audit = _load_json(candidate_audit_path)
    diagnostic = _load_json(diagnostic_path)
    audits = candidate_audit.get("audits") or []
    handoff_audits = [
        audit for audit in audits
        if isinstance(audit, dict)
        and audit.get("candidate_id") == "cand.krk.box_shrink.handoff_role_refinement.v1"
        and audit.get("audit_status") == "handoff_role_audit_required"
    ]
    post_reply_packets = _packets_by_phase(diagnostic, "post_opponent_reply")
    rows: list[dict[str, Any]] = [
        pkt.get("evidence_terms") or {}
        for pkt in post_reply_packets
        if isinstance(pkt, dict) and isinstance(pkt.get("evidence_terms"), dict)
    ]
    successor_outcomes = Counter(
        f"{row.get('successor_selected_skill') or 'none'}:{row.get('playout_result') or 'not_checked'}"
        for row in rows
    )
    stage0_failures = [
        row for row in rows
        if row.get("successor_selected_skill") == "krk.stage0_basin"
        and row.get("playout_result") == "max_plies"
    ]
    edge_trap_successes = [
        row for row in rows
        if str(row.get("successor_selected_skill") or "").startswith("krk.edge_trap")
        and row.get("playout_result") == "mate"
    ]
    no_successor_mates = [
        row for row in rows
        if row.get("successor_selected_skill") is None and row.get("playout_result") == "mate"
    ]

    role_audits: list[dict[str, Any]] = []
    for role_id in ROLE_IDS:
        if role_id == "krk.box_shrink_to_edge_trap_handoff":
            positive_rows = edge_trap_successes
            negative_rows = [
                row for row in rows
                if str(row.get("successor_selected_skill") or "").startswith("krk.edge_trap")
                and row.get("playout_result") != "mate"
            ]
            unsupported = 0
            proposed_terms = [
                "box_area_not_increased_after_reply",
                "rook_safe_after_reply",
                "fence_or_cut_preserved",
                "successor_edge_trap_close_available",
            ]
        elif role_id == "krk.box_shrink_post_reply_continuation":
            positive_rows = no_successor_mates
            negative_rows = stage0_failures
            unsupported = 0
            proposed_terms = [
                "post_box_shrink_conversion_needed",
                "stage0_basin_fallback_detected",
                "stage0_basin_unlicensed_after_box_shrink",
                "edge_or_drive_repair_not_selected",
            ]
        else:
            positive_rows = []
            negative_rows = []
            unsupported = len(stage0_failures)
            proposed_terms = [
                "box_shrink_reward_confirmed",
                "fence_or_cut_not_preserved",
                "drive_to_edge_affordance_after_box_shrink",
                "repair_or_reestablish_cut_available",
            ]

        representatives = [_representative(row) for row in (negative_rows or positive_rows)[:5]]
        role_audits.append({
            "role_id": role_id,
            "audit_status": _status_for_role(role_id, len(positive_rows), len(negative_rows), unsupported),
            "positive_support": len(positive_rows),
            "negative_support": len(negative_rows),
            "unsupported_failure_support": unsupported,
            "proposed_visible_terms": proposed_terms,
            "term_summary": _role_term_summary(positive_rows + negative_rows),
            "representative_fens": representatives,
        })

    return {
        "schema_version": "stage7_successor_ownership_audit.v1",
        "causal_status": "non_causal",
        "candidate_audit_source": str(candidate_audit_path),
        "diagnostic_source": str(diagnostic_path),
        "source_candidate_id": "cand.krk.box_shrink.handoff_role_refinement.v1",
        "source_candidate_ready": bool(handoff_audits),
        "successor_outcome_counts": dict(successor_outcomes),
        "stage0_basin_max_plies_count": len(stage0_failures),
        "edge_trap_mate_count": len(edge_trap_successes),
        "no_successor_mate_count": len(no_successor_mates),
        "role_audits": role_audits,
        "recommended_next_action": (
            "sandbox_edge_trap_handoff_role_and_counterfactual_stage0_failures"
            if edge_trap_successes and stage0_failures
            else "collect_more_evidence"
        ),
    }


def _write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Stage 7 Successor Ownership Audit",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"Source candidate ready: `{payload['source_candidate_ready']}`",
        "",
        "## Successor Outcomes",
        "",
    ]
    for key, value in sorted((payload.get("successor_outcome_counts") or {}).items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Role Audits", ""])
    for role in payload.get("role_audits", []):
        lines.append(f"### {role.get('role_id')}")
        lines.append("")
        lines.append(f"- Audit status: `{role.get('audit_status')}`")
        lines.append(f"- Positive support: `{role.get('positive_support')}`")
        lines.append(f"- Negative support: `{role.get('negative_support')}`")
        lines.append(f"- Unsupported failure support: `{role.get('unsupported_failure_support')}`")
        terms = ", ".join(f"`{term}`" for term in role.get("proposed_visible_terms") or [])
        lines.append(f"- Proposed visible terms: {terms}")
        lines.append("")
    lines.append(f"Recommended next action: `{payload.get('recommended_next_action')}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Stage 7 successor ownership")
    parser.add_argument("--candidate-audit", type=Path, required=True)
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = audit_successor_ownership(
        candidate_audit_path=args.candidate_audit,
        diagnostic_path=args.diagnostic,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        _write_markdown(payload, args.markdown_output)
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
