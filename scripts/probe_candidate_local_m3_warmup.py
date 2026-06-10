#!/usr/bin/env python3
"""Probe whether a candidate-local M3 warmup has eligible evidence.

This consumes a candidate-local M3 warmup plan and a diagnostic artifact. It
does not run gameplay, mutate weights, consolidate M4, or alter topology. Its
job is to answer whether candidate-local edges actually fired often enough for
bounded M3 to be meaningful.
"""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _role_payload(evidence: dict[str, Any], provider: str, role: str) -> dict[str, Any]:
    licenses = evidence.get("visible_successor_provider_licenses")
    if not isinstance(licenses, dict):
        return {}
    provider_payload = licenses.get(provider)
    if not isinstance(provider_payload, dict):
        return {}
    payload = provider_payload.get(role)
    return payload if isinstance(payload, dict) else {}


def _post_reply_packets(diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        packet
        for packet in diagnostic.get("handoff_packets") or []
        if isinstance(packet, dict) and packet.get("phase") == "post_opponent_reply"
    ]


def _edge_delta_preview(
    *,
    selected_successes: int,
    selected_failures: int,
    eligible_edges: list[dict[str, Any]],
    eta_eff: float,
    max_delta_episode: float,
) -> list[dict[str, Any]]:
    if selected_successes + selected_failures <= 0:
        return []
    reward_sum = float(selected_successes - selected_failures)
    delta = max(-max_delta_episode, min(max_delta_episode, eta_eff * reward_sum))
    return [
        {
            "edge_key": f"{edge['src']}->{edge['dst']}:{edge['type']}",
            "src": edge["src"],
            "dst": edge["dst"],
            "type": edge["type"],
            "preview_delta_sum": delta,
            "reason": edge.get("reason"),
        }
        for edge in eligible_edges
    ]


def probe_candidate_local_m3_warmup(
    *,
    warmup_plan_path: Path,
    diagnostic_path: Path,
) -> dict[str, Any]:
    start = time.perf_counter()
    warmup_plan = _load_json(warmup_plan_path)
    diagnostic = _load_json(diagnostic_path)
    target_role = str(warmup_plan.get("target_role") or "")
    providers = [str(item) for item in warmup_plan.get("target_providers") or []]
    if not providers:
        raise ValueError("warmup plan has no target_providers")
    target_provider = providers[0]
    eligible_edges = [
        edge
        for edge in warmup_plan.get("eligible_edge_whitelist") or []
        if isinstance(edge, dict)
    ]

    counts: Counter[str] = Counter()
    sample_rows: list[dict[str, Any]] = []
    for packet in _post_reply_packets(diagnostic):
        evidence = packet.get("evidence_terms")
        if not isinstance(evidence, dict):
            continue
        role = _role_payload(evidence, target_provider, target_role)
        contract_met = bool(role.get("contract_met"))
        selected = str(evidence.get("successor_selected_skill") or "")
        result = str(evidence.get("playout_result") or "")
        if contract_met:
            counts["role_contract_met"] += 1
            if selected == target_provider:
                counts["candidate_provider_selected"] += 1
                if result == "mate":
                    counts["candidate_provider_selected_mate"] += 1
                else:
                    counts["candidate_provider_selected_failed"] += 1
            else:
                counts["role_met_provider_not_selected"] += 1
                counts[f"role_met_selected:{selected or 'unknown'}"] += 1
        elif selected == target_provider:
            counts["candidate_selected_without_role_contract"] += 1

        if contract_met or selected == target_provider:
            sample_rows.append({
                "packet_id": packet.get("packet_id"),
                "fen": evidence.get("fen"),
                "post_reply_fen": evidence.get("post_reply_fen"),
                "move": evidence.get("move"),
                "black_reply": evidence.get("black_reply"),
                "role_contract_met": contract_met,
                "selected_successor": selected,
                "playout_result": result,
                "source_terms": role.get("source_terms") or [],
            })

    selected_total = counts["candidate_provider_selected"]
    selected_successes = counts["candidate_provider_selected_mate"]
    selected_failures = counts["candidate_provider_selected_failed"]
    candidate_edge_eligibility_events = selected_total * len(eligible_edges)

    if counts["role_contract_met"] > 0 and selected_total == 0:
        result = "blocked_no_candidate_provider_eligibility"
        recommendation = "compile_visible_role_provider_support_or_owner_eligibility_before_m3"
        diagnostic_labels = [
            "role_contract_met_provider_not_selected",
            "candidate_edges_not_firing",
            "topology_present_but_not_eligible_for_weight_update",
        ]
    elif selected_total > 0:
        result = "candidate_local_m3_warmup_feasible"
        recommendation = "run_bounded_candidate_local_m3_warmup"
        diagnostic_labels = ["candidate_edges_have_eligibility"]
    else:
        result = "insufficient_role_or_provider_evidence"
        recommendation = "collect_more_targeted_diagnostics"
        diagnostic_labels = ["insufficient_evidence"]

    limits = warmup_plan.get("training_limits") or {}
    eta_eff = float(limits.get("eta_eff", 0.02) or 0.02)
    max_delta_episode = float(limits.get("max_delta_episode", 0.25) or 0.25)
    return {
        "schema_version": "candidate_local_m3_warmup_probe.v1",
        "causal_status": "non_causal",
        "warmup_plan_source": str(warmup_plan_path),
        "diagnostic_source": str(diagnostic_path),
        "target_role": target_role,
        "target_provider": target_provider,
        "probe_result": result,
        "recommended_next_action": recommendation,
        "diagnostic_labels": diagnostic_labels,
        "counts": dict(counts),
        "eligible_edge_count": len(eligible_edges),
        "candidate_edge_eligibility_events": candidate_edge_eligibility_events,
        "edge_delta_preview": _edge_delta_preview(
            selected_successes=selected_successes,
            selected_failures=selected_failures,
            eligible_edges=eligible_edges,
            eta_eff=eta_eff,
            max_delta_episode=max_delta_episode,
        ),
        "sample_rows": sample_rows[:20],
        "safety": {
            "m4_consolidation_enabled": bool(limits.get("m4_consolidation_enabled", False)),
            "topology_mutation_enabled": bool(limits.get("topology_mutation_enabled", False)),
            "protected_provider_mutation_enabled": bool(
                limits.get("protected_provider_mutation_enabled", False)
            ),
            "hard_blocks": warmup_plan.get("hard_blocks") or [],
        },
        "performance": {
            "wall_time_seconds": time.perf_counter() - start,
            "post_reply_packets": len(_post_reply_packets(diagnostic)),
        },
    }


def _write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Candidate-Local M3 Warmup Probe",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"Target role: `{payload['target_role']}`",
        f"Target provider: `{payload['target_provider']}`",
        f"Probe result: `{payload['probe_result']}`",
        f"Recommended next action: `{payload['recommended_next_action']}`",
        "",
        "## Counts",
        "",
    ]
    for key, value in sorted((payload.get("counts") or {}).items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend([
        f"- `eligible_edge_count`: {payload.get('eligible_edge_count')}",
        f"- `candidate_edge_eligibility_events`: {payload.get('candidate_edge_eligibility_events')}",
        "",
        "## Diagnostic Labels",
        "",
    ])
    for item in payload.get("diagnostic_labels") or []:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Safety", ""])
    for key, value in sorted((payload.get("safety") or {}).items()):
        if key == "hard_blocks":
            continue
        lines.append(f"- `{key}`: `{value}`")
    for item in (payload.get("safety") or {}).get("hard_blocks") or []:
        lines.append(f"- hard block: `{item}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe candidate-local M3 warmup feasibility")
    parser.add_argument("--warmup-plan", type=Path, required=True)
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = probe_candidate_local_m3_warmup(
        warmup_plan_path=args.warmup_plan,
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
