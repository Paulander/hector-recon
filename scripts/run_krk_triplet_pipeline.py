"""Replayable KRK Stage-0/Stage-1 triplet-growth pipeline.

The runner intentionally keeps structural growth conservative: it produces a
fresh learner/topology, validates formal ReCoN pairs, evaluates mate-in-1
stability, evaluates Stage-1 goal-distance improvement, and writes a manifest.
Triplet growth experiments can then use the same output directory as a stable
baseline instead of relying on stale pickles.
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from recon_lite_chess.graph.builder import build_graph_from_topology, validate_formal_pairs


@dataclass(frozen=True)
class PipelinePlan:
    output_dir: Path
    learner_path: Path
    topology_path: Path
    manifest_path: Path
    commands: List[List[str]]


def build_plan(args: argparse.Namespace) -> PipelinePlan:
    output_dir = args.output_dir
    learner_path = output_dir / "baseline" / "final_learner.pkl"
    topology_path = output_dir / "topology" / "krk_entry_topology.json"
    manifest_path = output_dir / "run_manifest.json"

    train_cmd = [
        sys.executable,
        "scripts/train_baseline_krk_chain.py",
        "--stage0-cycles",
        str(args.stage0_cycles),
        "--stage1-cycles",
        str(args.stage1_cycles),
        "--samples-per-cycle",
        str(args.samples_per_cycle),
        "--output-dir",
        str(output_dir / "baseline"),
        "--save-learner",
        str(learner_path),
        "--device",
        args.device,
        "--seed",
        str(args.seed),
        "--snapshot-every",
        str(args.snapshot_every),
        "--min-mature-for-goals",
        str(args.min_mature_for_goals),
        "--feature-set",
        getattr(args, "feature_set", "legacy"),
        "--max-curriculum-stage",
        str(getattr(args, "max_curriculum_stage", 1)),
        "--start-curriculum-stage",
        str(getattr(args, "start_curriculum_stage", 2)),
        "--landmark-cycles",
        str(getattr(args, "landmark_cycles", 10)),
        "--stage1-position-mode",
        args.stage1_position_mode,
    ]
    if getattr(args, "load_learner", None):
        train_cmd.extend(["--load-learner", str(args.load_learner)])
    if getattr(args, "adaptive_curriculum", False):
        train_cmd.extend([
            "--adaptive-curriculum",
            "--eval-every",
            str(getattr(args, "eval_every", 5)),
            "--patience",
            str(getattr(args, "patience", 3)),
            "--min-cycles-per-stage",
            str(getattr(args, "min_cycles_per_stage", 10)),
            "--max-cycles-per-stage",
            str(getattr(args, "max_cycles_per_stage", 80)),
            "--adaptive-eval-samples",
            str(getattr(args, "adaptive_eval_samples", None) or args.stage1_eval_samples),
            "--adaptive-playout-max-plies",
            str(getattr(args, "adaptive_playout_max_plies", 80)),
        ])
    if getattr(args, "allow_prune_foundation", False):
        train_cmd.append("--allow-prune-foundation")
    if args.stage1_position_mode == "hybrid":
        train_cmd.extend(["--stage1-hybrid-random-ratio", str(args.stage1_hybrid_random_ratio)])
    if args.stage0_balance_corners:
        train_cmd.append("--stage0-balance-corners")

    compile_cmd = [
        sys.executable,
        "scripts/baseline_to_recon.py",
        "--learner",
        str(learner_path),
        "--output",
        str(topology_path),
    ]

    stage0_eval_cmd = [
        sys.executable,
        "scripts/test_krk_entry.py",
        "--topology",
        str(topology_path),
        "--samples",
        str(args.stage0_eval_samples),
    ]

    stage1_eval_cmd = [
        sys.executable,
        "scripts/test_stage1_backchain.py",
        "--topology",
        str(topology_path),
        "--learner",
        str(learner_path),
        "--samples",
        str(args.stage1_eval_samples),
        "--seed",
        str(args.seed),
        "--stage-filter",
        "1",
        "--position-mode",
        args.stage1_eval_position_mode,
    ]
    if args.stage1_eval_position_mode == "hybrid":
        stage1_eval_cmd.extend(["--hybrid-random-ratio", str(args.stage1_eval_hybrid_random_ratio)])

    return PipelinePlan(
        output_dir=output_dir,
        learner_path=learner_path,
        topology_path=topology_path,
        manifest_path=manifest_path,
        commands=[train_cmd, compile_cmd, stage0_eval_cmd, stage1_eval_cmd],
    )


def manifest_for(args: argparse.Namespace, plan: PipelinePlan) -> Dict[str, Any]:
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "fresh_krk_stage0_stage1_triplet_growth_baseline",
        "output_dir": str(plan.output_dir),
        "learner_path": str(plan.learner_path),
        "topology_path": str(plan.topology_path),
        "seed": args.seed,
        "training": {
            "stage0_cycles": args.stage0_cycles,
            "stage1_cycles": args.stage1_cycles,
            "samples_per_cycle": args.samples_per_cycle,
            "device": args.device,
            "stage0_balance_corners": args.stage0_balance_corners,
            "snapshot_every": args.snapshot_every,
            "min_mature_for_goals": args.min_mature_for_goals,
            "feature_set": getattr(args, "feature_set", "legacy"),
            "max_curriculum_stage": getattr(args, "max_curriculum_stage", 1),
            "start_curriculum_stage": getattr(args, "start_curriculum_stage", 2),
            "landmark_cycles": getattr(args, "landmark_cycles", 10),
            "allow_prune_foundation": getattr(args, "allow_prune_foundation", False),
            "adaptive_curriculum": getattr(args, "adaptive_curriculum", False),
            "eval_every": getattr(args, "eval_every", 5),
            "patience": getattr(args, "patience", 3),
            "min_cycles_per_stage": getattr(args, "min_cycles_per_stage", 10),
            "max_cycles_per_stage": getattr(args, "max_cycles_per_stage", 80),
            "adaptive_eval_samples": getattr(args, "adaptive_eval_samples", None) or args.stage1_eval_samples,
            "adaptive_playout_max_plies": getattr(args, "adaptive_playout_max_plies", 80),
            "load_learner": str(args.load_learner) if getattr(args, "load_learner", None) else None,
            "stage1_position_mode": args.stage1_position_mode,
            "stage1_hybrid_random_ratio": args.stage1_hybrid_random_ratio,
        },
        "evaluation": {
            "stage0_eval_samples": args.stage0_eval_samples,
            "stage1_eval_samples": args.stage1_eval_samples,
            "stage1_stage_filter": 1,
            "stage1_eval_position_mode": args.stage1_eval_position_mode,
            "stage1_eval_hybrid_random_ratio": args.stage1_eval_hybrid_random_ratio,
        },
        "formal_validation": {
            "mode": "strict_pairs",
            "validated": False,
        },
        "commands": plan.commands,
    }


def write_manifest(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def run_command(command: List[str]) -> None:
    print("\n$ " + " ".join(command))
    subprocess.run(command, check=True)


def validate_topology(topology_path: Path) -> Dict[str, int]:
    graph = build_graph_from_topology(topology_path, formal_pairs="validate")
    validate_formal_pairs(graph)
    return {"nodes": len(graph.nodes), "edges": len(graph.edges)}


def learner_readiness(learner_path: Path) -> Dict[str, Any]:
    with learner_path.open("rb") as fh:
        learner = pickle.load(fh)
    mature = [s for s in getattr(learner, "sensors", []) if getattr(s, "is_mature", False)]
    goal_memories = [
        g for g in getattr(learner, "goal_memories", [])
        if getattr(g, "label", "") == "mate_in_1"
    ]
    actuators = list(getattr(learner, "actuators", []))
    ready = bool(mature and goal_memories and actuators)
    return {
        "ready": ready,
        "sensors": len(getattr(learner, "sensors", [])),
        "mature_sensors": len(mature),
        "actuators": len(actuators),
        "mate_in_1_goal_memories": len(goal_memories),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fresh KRK Stage-0/Stage-1 pipeline")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--stage0-cycles", type=int, default=10)
    parser.add_argument("--stage1-cycles", type=int, default=10)
    parser.add_argument("--load-learner", type=Path, default=None,
                        help="Resume training from an existing learner pickle")
    parser.add_argument("--samples-per-cycle", type=int, default=50)
    parser.add_argument("--stage0-eval-samples", type=int, default=50)
    parser.add_argument("--stage1-eval-samples", type=int, default=50)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--snapshot-every", type=int, default=1)
    parser.add_argument("--min-mature-for-goals", type=int, default=6)
    parser.add_argument("--feature-set", choices=["legacy", "krk_rich_v1"], default="legacy")
    parser.add_argument("--max-curriculum-stage", type=int, default=1)
    parser.add_argument("--start-curriculum-stage", type=int, default=2)
    parser.add_argument("--landmark-cycles", type=int, default=10)
    parser.add_argument("--allow-prune-foundation", action="store_true", default=False)
    parser.add_argument("--adaptive-curriculum", action="store_true", default=False)
    parser.add_argument("--eval-every", type=int, default=5)
    parser.add_argument("--patience", type=int, default=3)
    parser.add_argument("--min-cycles-per-stage", type=int, default=10)
    parser.add_argument("--max-cycles-per-stage", type=int, default=80)
    parser.add_argument("--adaptive-eval-samples", type=int, default=None)
    parser.add_argument("--adaptive-playout-max-plies", type=int, default=80)
    parser.add_argument("--stage1-position-mode", choices=["mate_in_2", "random", "hybrid"], default="hybrid")
    parser.add_argument("--stage1-hybrid-random-ratio", type=float, default=0.5)
    parser.add_argument("--stage1-eval-position-mode", choices=["mate_in_2", "random", "hybrid"], default="random")
    parser.add_argument("--stage1-eval-hybrid-random-ratio", type=float, default=0.5)
    parser.add_argument("--stage0-balance-corners", action="store_true", default=True)
    parser.add_argument("--no-stage0-balance-corners", action="store_false", dest="stage0_balance_corners")
    parser.add_argument("--dry-run", action="store_true", help="Write manifest and print commands only")
    args = parser.parse_args()

    if args.output_dir is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output_dir = Path("snapshots/krk_triplet_pipeline") / stamp

    plan = build_plan(args)
    manifest = manifest_for(args, plan)
    write_manifest(plan.manifest_path, manifest)

    if args.dry_run:
        print(json.dumps(manifest, indent=2))
        return

    env_seed = str(args.seed)
    os.environ.setdefault("PYTHONHASHSEED", env_seed)

    run_command(plan.commands[0])
    readiness = learner_readiness(plan.learner_path)
    manifest["learner_readiness"] = readiness
    if not readiness["ready"]:
        manifest["status"] = "insufficient_stage0_basis"
        manifest["recommendation"] = (
            "Increase --stage0-cycles and --samples-per-cycle until Stage 0 creates "
            "mature sensors, actuators, and mate_in_1 goal memories, or lower "
            "--min-mature-for-goals for exploratory/presentation runs."
        )
        write_manifest(plan.manifest_path, manifest)
        print("\nPipeline stopped after training: insufficient Stage-0 basis.")
        print(json.dumps(readiness, indent=2))
        print(f"Manifest updated: {plan.manifest_path}")
        return

    run_command(plan.commands[1])
    validation = validate_topology(plan.topology_path)
    manifest["formal_validation"] = {
        "mode": "strict_pairs",
        "validated": True,
        **validation,
    }
    write_manifest(plan.manifest_path, manifest)
    run_command(plan.commands[2])
    run_command(plan.commands[3])


if __name__ == "__main__":
    main()
