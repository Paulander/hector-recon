#!/usr/bin/env python3
"""Analyze non-causal Plan Capsule marker evidence from diagnostics."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _marker_rows(diagnostic: dict[str, Any], capsule_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for packet in diagnostic.get("handoff_packets") or []:
        if not isinstance(packet, dict):
            continue
        evidence = packet.get("evidence_terms") or {}
        if not isinstance(evidence, dict):
            continue
        marker = (evidence.get("plan_capsule_markers") or {}).get(capsule_id)
        if not isinstance(marker, dict):
            continue
        rows.append(
            {
                "phase": packet.get("phase"),
                "outcome": evidence.get("playout_result") or packet.get("observed_outcome"),
                "selected_successor": evidence.get("successor_selected_skill"),
                "post_reply_state_signature": evidence.get("post_reply_state_signature"),
                "post_reply_fen": evidence.get("post_reply_fen"),
                "marker": marker,
            }
        )
    return rows


def analyze_markers(diagnostic: dict[str, Any], *, capsule_id: str) -> dict[str, Any]:
    rows = _marker_rows(diagnostic, capsule_id)
    outcome_counts = Counter(str(row.get("outcome") or "unknown") for row in rows)
    status_counts = Counter(
        f"entry={bool(row['marker'].get('entry_confirmed'))}|"
        f"abort={bool(row['marker'].get('abort_confirmed'))}|"
        f"outcome={row.get('outcome') or 'unknown'}"
        for row in rows
    )
    term_by_outcome: dict[str, dict[str, dict[str, int]]] = {}
    for term_field in (
        "entry_terms_met",
        "progress_terms_met",
        "exit_terms_met",
        "abort_terms_met",
    ):
        counts: dict[str, Counter] = defaultdict(Counter)
        for row in rows:
            outcome = str(row.get("outcome") or "unknown")
            for term in row["marker"].get(term_field) or []:
                counts[str(term)][outcome] += 1
        term_by_outcome[term_field] = {
            term: dict(counter) for term, counter in sorted(counts.items())
        }

    entry_confirmed_max = sum(
        1
        for row in rows
        if row.get("outcome") == "max_plies" and row["marker"].get("entry_confirmed")
    )
    entry_confirmed_mate = sum(
        1
        for row in rows
        if row.get("outcome") == "mate" and row["marker"].get("entry_confirmed")
    )
    mate_exit_count = sum(
        1
        for row in rows
        if row.get("outcome") == "mate" and row["marker"].get("exit_terms_met")
    )
    max_no_abort_count = sum(
        1
        for row in rows
        if row.get("outcome") == "max_plies" and not row["marker"].get("abort_terms_met")
    )
    recommendations = []
    if entry_confirmed_max and not entry_confirmed_mate:
        recommendations.append(
            "entry_terms_separate_candidate_ownership_from_already_successful_exit_states"
        )
    if mate_exit_count:
        recommendations.append("treat_mate_in_one_or_finish_terms_as_exit_interrupts")
    if max_no_abort_count:
        recommendations.append("add_owned_move_progress_or_ttl_failure_monitor_before_causal_capsule")

    return {
        "schema_version": "plan_capsule_marker_analysis.v1",
        "causal_status": "non_causal",
        "capsule_id": capsule_id,
        "marker_record_count": len(rows),
        "outcome_counts": dict(outcome_counts),
        "entry_abort_status_by_outcome": dict(status_counts),
        "term_by_outcome": term_by_outcome,
        "representative_rows": rows[:10],
        "diagnosis": {
            "entry_confirmed_max_plies_count": entry_confirmed_max,
            "entry_confirmed_mate_count": entry_confirmed_mate,
            "mate_exit_count": mate_exit_count,
            "max_plies_without_abort_count": max_no_abort_count,
        },
        "recommendations": recommendations,
        "next_action": "design_non_causal_owned_move_progress_monitor",
    }


def _write_md(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Plan Capsule Marker Analysis",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"Capsule: `{payload['capsule_id']}`",
        f"Marker records: `{payload['marker_record_count']}`",
        "",
        "## Outcomes",
        "",
    ]
    for key, value in sorted((payload.get("outcome_counts") or {}).items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Diagnosis", ""])
    for key, value in sorted((payload.get("diagnosis") or {}).items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Recommendations", ""])
    for item in payload.get("recommendations") or []:
        lines.append(f"- `{item}`")
    lines.extend(["", f"Next action: `{payload.get('next_action')}`"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("diagnostic", type=Path)
    parser.add_argument("--capsule-id", default="krk.post_box_shrink_continuation")
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = analyze_markers(_load_json(args.diagnostic), capsule_id=args.capsule_id)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_md(payload, args.markdown_output)
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
