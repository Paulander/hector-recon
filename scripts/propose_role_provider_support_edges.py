#!/usr/bin/env python3
"""Propose explicit visible role->provider support edges.

This is a non-causal proposal generator. It does not edit the topology. It
turns a blocked candidate-local M3 probe into a concrete structural proposal
that can later be sandbox-compiled and guardrail-tested.
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


def _role_nodes(topology: dict[str, Any], role_id: str) -> list[str]:
    nodes = []
    for node_id, node in topology.get("nodes", {}).items():
        if not isinstance(node, dict):
            continue
        meta = node.get("meta")
        if isinstance(meta, dict) and meta.get("role_id") == role_id:
            nodes.append(str(node_id))
    return sorted(nodes)


def _provider_nodes(topology: dict[str, Any], provider_id: str) -> list[str]:
    nodes = []
    for node_id, node in topology.get("nodes", {}).items():
        if not isinstance(node, dict):
            continue
        meta = node.get("meta")
        if isinstance(meta, dict) and meta.get("skill_id") == provider_id and node_id.startswith("skill."):
            nodes.append(str(node_id))
    return sorted(nodes)


def propose_role_provider_support_edges(
    *,
    topology_path: Path,
    m3_probe_path: Path,
) -> dict[str, Any]:
    topology = _load_json(topology_path)
    probe = _load_json(m3_probe_path)
    role_id = str(probe.get("target_role") or "")
    provider_id = str(probe.get("target_provider") or "")
    role_nodes = _role_nodes(topology, role_id)
    provider_nodes = _provider_nodes(topology, provider_id)
    blocked = probe.get("probe_result") == "blocked_no_candidate_provider_eligibility"
    proposals: list[dict[str, Any]] = []
    if blocked:
        for role_node in role_nodes:
            if not role_node.startswith("script."):
                continue
            for provider_node in provider_nodes:
                proposals.append({
                    "src": role_node,
                    "dst": provider_node,
                    "type": "SUB",
                    "initial_weight": 0.0,
                    "trainable": True,
                    "edge_kind": "visible_role_provider_support",
                    "causal_status": "non_causal_until_sandbox_compiled",
                    "source_terms": [
                        "role_contract_met_provider_not_selected",
                        "candidate_edges_not_firing",
                    ],
                    "activation_rule": "role_script_confirmation_may_support_provider_skill_after_sandbox_promotion",
                })

    return {
        "schema_version": "role_provider_support_proposal.v1",
        "causal_status": "non_causal",
        "topology_source": str(topology_path),
        "m3_probe_source": str(m3_probe_path),
        "target_role": role_id,
        "target_provider": provider_id,
        "source_probe_result": probe.get("probe_result"),
        "proposal_status": "sandbox_ready" if proposals else "not_applicable",
        "candidate_id": f"cand.{role_id}.visible_provider_support.v1".replace("krk.", "krk."),
        "proposed_edges": proposals,
        "proposed_edge_count": len(proposals),
        "required_validation": [
            "compile_sandbox_topology_with_support_edges",
            "stage7_target_smoke",
            "stage6_drive_guardrail",
            "stage5_fence_guardrail",
            "stage1_backchain_guardrail",
            "m1_m4_preservation",
        ],
        "hard_blocks": [
            "do_not_insert_into_default_topology",
            "do_not_train_stage8",
            "do_not_promote_stage7_without_guardrails",
            "do_not_make_probe_or_candidate_causal",
        ],
    }


def _write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Role-Provider Support Edge Proposal",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"Target role: `{payload['target_role']}`",
        f"Target provider: `{payload['target_provider']}`",
        f"Source probe result: `{payload['source_probe_result']}`",
        f"Proposal status: `{payload['proposal_status']}`",
        f"Proposed edge count: `{payload['proposed_edge_count']}`",
        "",
        "## Proposed Edges",
        "",
    ]
    for edge in payload.get("proposed_edges") or []:
        lines.append(
            f"- `{edge['src']}` --`{edge['type']}`/w={edge['initial_weight']}--> `{edge['dst']}` "
            f"({edge['edge_kind']})"
        )
    lines.extend(["", "## Required Validation", ""])
    for item in payload.get("required_validation") or []:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Hard Blocks", ""])
    for item in payload.get("hard_blocks") or []:
        lines.append(f"- `{item}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Propose visible role-provider support edges")
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--m3-probe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = propose_role_provider_support_edges(
        topology_path=args.topology,
        m3_probe_path=args.m3_probe,
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
