#!/usr/bin/env python3
"""Compile an opt-in Stage 7 king-tempo sandbox provider into a KRK topology."""

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


def _edge_exists(topology: dict[str, Any], src: str, dst: str, edge_type: str) -> bool:
    for edge in topology.get("edges", []) or []:
        if not isinstance(edge, dict):
            continue
        if edge.get("src") == src and edge.get("dst") == dst and edge.get("type") == edge_type:
            return True
    return False


def _add_edge(topology: dict[str, Any], src: str, dst: str, edge_type: str, weight: float = 1.0, **meta) -> None:
    if _edge_exists(topology, src, dst, edge_type):
        return
    edge = {"src": src, "dst": dst, "type": edge_type, "weight": weight}
    edge.update(meta)
    topology.setdefault("edges", []).append(edge)


def compile_stage7_king_tempo_sandbox(
    *,
    topology_path: Path,
    output_path: Path,
    score: float = 25.0,
    drive_repair_score: float = 28.0,
    post_king_tempo_score: float = 30.0,
    post_box_continuation_score: float = 32.0,
    include_drive_repair: bool = False,
    include_post_king_tempo: bool = False,
    include_post_box_continuation: bool = False,
    enable_by_default: bool = False,
) -> dict[str, Any]:
    topology = _load_json(topology_path)
    topology.setdefault("nodes", {})
    topology.setdefault("edges", [])
    topology.setdefault("meta", {})
    hub_id = "krk_hub"
    if hub_id not in topology["nodes"]:
        raise ValueError(f"topology missing {hub_id}")

    node_id = "terminal.krk.stage7_king_tempo"
    topology["nodes"][node_id] = {
        "id": node_id,
        "type": "TERMINAL",
        "factory": "recon_lite_chess.krk_baseline_nodes:create_krk_stage7_king_tempo_terminal",
        "meta": {
            "stage7_king_tempo_provider": True,
            "score": float(score),
            "causal_status": "sandbox_opt_in",
            "enabled_by_default": bool(enable_by_default),
            "provider_skill_id": "krk.stage0_basin",
            "role_id": "krk.box_shrink_king_tempo_handoff",
            "description": (
                "Opt-in visible Stage 7 king-tempo provider. It proposes quiet "
                "king tempo/support-positioning moves only when graph-visible "
                "post-box-shrink terms license the handoff."
            ),
        },
    }
    _add_edge(topology, hub_id, node_id, "SUB", 1.0, consolidate=False)
    _add_edge(topology, node_id, hub_id, "SUR", 1.0, consolidate=False)

    drive_repair_node_id = "terminal.krk.stage7_drive_repair"
    if include_drive_repair:
        topology["nodes"][drive_repair_node_id] = {
            "id": drive_repair_node_id,
            "type": "TERMINAL",
            "factory": "recon_lite_chess.krk_baseline_nodes:create_krk_stage7_drive_repair_terminal",
            "meta": {
                "stage7_drive_repair_provider": True,
                "score": float(drive_repair_score),
                "causal_status": "sandbox_opt_in",
                "enabled_by_default": bool(enable_by_default),
                "provider_skill_id": "krk.stage7_drive_repair",
                "role_id": "krk.box_shrink_drive_repair_move",
                "description": (
                    "Opt-in visible Stage 7 drive-repair provider. It proposes "
                    "a safe repair move only when post-box-shrink visible terms "
                    "say the cut/fence failed and drive repair is available."
                ),
            },
        }
        _add_edge(topology, hub_id, drive_repair_node_id, "SUB", 1.0, consolidate=False)
        _add_edge(topology, drive_repair_node_id, hub_id, "SUR", 1.0, consolidate=False)

    post_node_id = "terminal.krk.stage7_post_king_tempo"
    if include_post_king_tempo:
        topology["nodes"][post_node_id] = {
            "id": post_node_id,
            "type": "TERMINAL",
            "factory": "recon_lite_chess.krk_baseline_nodes:create_krk_stage7_post_king_tempo_terminal",
            "meta": {
                "stage7_post_king_tempo_provider": True,
                "score": float(post_king_tempo_score),
                "causal_status": "sandbox_opt_in",
                "enabled_by_default": bool(enable_by_default),
                "provider_skill_id": "krk.stage7_post_king_tempo",
                "role_id": "krk.post_king_tempo_continuation",
                "description": (
                    "Opt-in visible Stage 7 follow-up provider. It can fire only "
                    "after the king-tempo provider has fired, and it proposes "
                    "audited rook follow-up moves through visible geometry terms."
                ),
            },
        }
        _add_edge(topology, hub_id, post_node_id, "SUB", 1.0, consolidate=False)
        _add_edge(topology, post_node_id, hub_id, "SUR", 1.0, consolidate=False)

    post_box_node_id = "terminal.krk.stage7_post_box_continuation"
    if include_post_box_continuation:
        topology["nodes"][post_box_node_id] = {
            "id": post_box_node_id,
            "type": "TERMINAL",
            "factory": "recon_lite_chess.krk_baseline_nodes:create_krk_stage7_post_box_continuation_terminal",
            "meta": {
                "stage7_post_box_continuation_provider": True,
                "score": float(post_box_continuation_score),
                "causal_status": "sandbox_opt_in",
                "enabled_by_default": bool(enable_by_default),
                "provider_skill_id": "krk.stage7_post_box_continuation",
                "role_id": "krk.post_box_shrink_continuation",
                "runtime_forbidden_terms": [
                    "tablebase_lookup",
                    "dtm_oracle_move_selection",
                    "state_hash_exception",
                ],
                "description": (
                    "Opt-in visible Stage 7 post-box continuation provider. "
                    "It proposes king-support or rook-confinement follow-up "
                    "moves using visible move/post terms only; DTM artifacts "
                    "are offline evidence and are not read at runtime."
                ),
            },
        }
        _add_edge(topology, hub_id, post_box_node_id, "SUB", 1.0, consolidate=False)
        _add_edge(topology, post_box_node_id, hub_id, "SUR", 1.0, consolidate=False)

    topology["meta"]["stage7_king_tempo_sandbox"] = {
        "schema_version": "stage7_king_tempo_sandbox.v1",
        "source_topology": str(topology_path),
        "node_id": node_id,
        "drive_repair_node_id": drive_repair_node_id if include_drive_repair else None,
        "post_king_tempo_node_id": post_node_id if include_post_king_tempo else None,
        "post_box_continuation_node_id": post_box_node_id if include_post_box_continuation else None,
        "score": float(score),
        "drive_repair_score": float(drive_repair_score),
        "post_king_tempo_score": float(post_king_tempo_score),
        "post_box_continuation_score": float(post_box_continuation_score),
        "include_drive_repair": bool(include_drive_repair),
        "include_post_king_tempo": bool(include_post_king_tempo),
        "include_post_box_continuation": bool(include_post_box_continuation),
        "enabled_by_default": bool(enable_by_default),
        "causal_status": "sandbox_opt_in",
    }
    if enable_by_default:
        root = topology.get("nodes", {}).get("krk_entry", {})
        if isinstance(root, dict):
            root.setdefault("meta", {})["stage7_king_tempo_enabled"] = True
            if include_drive_repair:
                root.setdefault("meta", {})["stage7_drive_repair_enabled"] = True
            if include_post_king_tempo:
                root.setdefault("meta", {})["stage7_post_king_tempo_enabled"] = True
            if include_post_box_continuation:
                root.setdefault("meta", {})["stage7_post_box_continuation_enabled"] = True

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(topology, indent=2) + "\n", encoding="utf-8")
    return topology


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile Stage 7 king-tempo sandbox provider into topology")
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--score", type=float, default=25.0)
    parser.add_argument("--drive-repair-score", type=float, default=28.0)
    parser.add_argument("--post-king-tempo-score", type=float, default=30.0)
    parser.add_argument("--post-box-continuation-score", type=float, default=32.0)
    parser.add_argument("--include-drive-repair", action="store_true")
    parser.add_argument("--include-post-king-tempo", action="store_true")
    parser.add_argument("--include-post-box-continuation", action="store_true")
    parser.add_argument("--enable-by-default", action="store_true")
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    topology = compile_stage7_king_tempo_sandbox(
        topology_path=args.topology,
        output_path=args.output,
        score=args.score,
        drive_repair_score=args.drive_repair_score,
        post_king_tempo_score=args.post_king_tempo_score,
        post_box_continuation_score=args.post_box_continuation_score,
        include_drive_repair=args.include_drive_repair,
        include_post_king_tempo=args.include_post_king_tempo,
        include_post_box_continuation=args.include_post_box_continuation,
        enable_by_default=args.enable_by_default,
    )
    summary = topology.get("meta", {}).get("stage7_king_tempo_sandbox", {})
    if not args.no_json_stdout:
        print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
