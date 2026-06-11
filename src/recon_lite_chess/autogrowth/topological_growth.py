"""Topological-growth runway tying legacy KRK controls to current fragments."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Iterable

from recon_lite_chess.triplets import terminal_delta, terminal_distance

from .features import validate_learner_record
from .positions import KRKPositionSet, generate_position_sets
from .script_fragments import ScriptFragmentConfig, ScriptFragmentResult, run_script_fragment_experiment


DEFAULT_LEGACY_MANIFESTS = (
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage2a_fixed2/run_manifest.json",
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage2c_clean/run_manifest.json",
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/run_manifest.json",
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile/run_manifest.json",
)


@dataclass(frozen=True)
class TopologicalGrowthRunwayConfig:
    seed: int = 20260610
    train_count: int = 200
    heldout_weakness_count: int = 100
    heldout_broader_count: int = 100
    min_support: int = 1
    max_candidates: int = 12
    horizon: int = 40
    min_sequence_credit: float = 0.10
    activation_max_distance: float = 0.5
    eta_m3: float = 0.08
    chain_max_distance: float = 1.5
    max_chain_edges: int = 24
    legacy_manifest_paths: tuple[str, ...] = DEFAULT_LEGACY_MANIFESTS


@dataclass(frozen=True)
class TopologicalGrowthRunwayResult:
    config: TopologicalGrowthRunwayConfig
    positions: KRKPositionSet
    fragment_result: ScriptFragmentResult
    legacy_inventory: list[dict[str, Any]]
    triplet_chain_view: dict[str, Any]
    curriculum_decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        validate_learner_record(self.fragment_result.fragment_candidates)
        return {
            "schema_version": "krk_autogrowth_tg_runway.v0",
            "config": asdict(self.config),
            "dataset": {
                "seed": self.positions.seed,
                "digest": self.positions.digest(),
                "train_count": len(self.positions.train),
                "heldout_count": len(self.positions.heldout),
                "heldout_weakness_count": len(self.positions.heldout_weakness),
                "heldout_broader_count": len(self.positions.heldout_broader),
            },
            "research_milestone": {
                "name": "topological_growth",
                "subcheckpoint": "TG17_triplet_chain_runway",
                "note": "Previous M-numbered autogrowth files are subcheckpoints inside this single topological-growth milestone.",
            },
            "legacy_predefined_topology_inventory": self.legacy_inventory,
            "current_fragment_result": self.fragment_result.to_dict(),
            "triplet_chain_view": self.triplet_chain_view,
            "curriculum_decision": self.curriculum_decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_topological_growth_runway(
    *,
    config: TopologicalGrowthRunwayConfig,
    positions: KRKPositionSet | None = None,
) -> TopologicalGrowthRunwayResult:
    positions = positions or generate_position_sets(
        seed=config.seed,
        train_count=config.train_count,
        heldout_weakness_count=config.heldout_weakness_count,
        heldout_broader_count=config.heldout_broader_count,
    )
    fragment_result = run_script_fragment_experiment(
        config=ScriptFragmentConfig(
            seed=config.seed,
            train_count=config.train_count,
            heldout_weakness_count=config.heldout_weakness_count,
            heldout_broader_count=config.heldout_broader_count,
            min_support=config.min_support,
            max_candidates=config.max_candidates,
            horizon=config.horizon,
            min_sequence_credit=config.min_sequence_credit,
            activation_max_distance=config.activation_max_distance,
            eta_m3=config.eta_m3,
        ),
        positions=positions,
    )
    legacy_inventory = inventory_legacy_predefined_topology_runs(config.legacy_manifest_paths)
    triplet_chain_view = build_triplet_chain_view(
        fragment_result.fragment_candidates,
        max_distance=config.chain_max_distance,
        max_edges=config.max_chain_edges,
    )
    curriculum_decision = _curriculum_decision(
        fragment_result=fragment_result,
        chain_view=triplet_chain_view,
        legacy_inventory=legacy_inventory,
    )
    return TopologicalGrowthRunwayResult(
        config=config,
        positions=positions,
        fragment_result=fragment_result,
        legacy_inventory=legacy_inventory,
        triplet_chain_view=triplet_chain_view,
        curriculum_decision=curriculum_decision,
    )


def inventory_legacy_predefined_topology_runs(paths: Iterable[str]) -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            inventory.append({"path": str(path), "exists": False})
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        topology_path = Path(payload.get("topology_path", ""))
        learner_path = Path(payload.get("learner_path", ""))
        training = payload.get("training", {}) or {}
        formal = payload.get("formal_validation", {}) or {}
        readiness = payload.get("learner_readiness", {}) or {}
        inventory.append(
            {
                "path": str(path),
                "exists": True,
                "purpose": payload.get("purpose"),
                "output_dir": payload.get("output_dir"),
                "seed": payload.get("seed"),
                "topology_path": str(topology_path) if topology_path else None,
                "topology_exists": topology_path.exists() if topology_path else False,
                "learner_path": str(learner_path) if learner_path else None,
                "learner_exists": learner_path.exists() if learner_path else False,
                "max_curriculum_stage": training.get("max_curriculum_stage"),
                "start_curriculum_stage": training.get("start_curriculum_stage"),
                "feature_set": training.get("feature_set"),
                "adaptive_curriculum": bool(training.get("adaptive_curriculum", False)),
                "composition_profile": training.get("adaptive_composition_profile"),
                "ready": bool(readiness.get("ready", False)),
                "mature_sensors": readiness.get("mature_sensors"),
                "actuators": readiness.get("actuators"),
                "mate_in_1_goal_memories": readiness.get("mate_in_1_goal_memories"),
                "formal_validated": bool(formal.get("validated", False)),
                "formal_nodes": formal.get("nodes"),
                "formal_edges": formal.get("edges"),
                "used_as_runtime_teacher": False,
                "used_as_move_provider": False,
                "role": "legacy_control_trace_source_only",
            }
        )
    return inventory


def build_triplet_chain_view(
    candidates: list[dict[str, Any]],
    *,
    max_distance: float,
    max_edges: int,
) -> dict[str, Any]:
    validate_learner_record(candidates)
    triplets = [_candidate_triplet_view(candidate) for candidate in candidates]
    edges: list[dict[str, Any]] = []
    for source in triplets:
        for target in triplets:
            if source["candidate_key"] == target["candidate_key"]:
                continue
            names = tuple(
                name
                for name in target["before_terminal"]["feature_names"]
                if name in source["after_terminal"]["prototype"]
            )
            if not names:
                continue
            after = {name: source["after_terminal"]["prototype"][name] for name in names}
            before = {name: target["before_terminal"]["prototype"][name] for name in names}
            distance = terminal_distance(after, before)
            if distance <= float(max_distance):
                edges.append(
                    {
                        "source_after_candidate_key": source["candidate_key"],
                        "target_before_candidate_key": target["candidate_key"],
                        "shared_terminal_features": list(names),
                        "after_to_before_distance": distance,
                        "relation_interpretation": "after_terminal_can_request_target_before_terminal",
                    }
                )
    edges.sort(key=lambda edge: (edge["after_to_before_distance"], edge["source_after_candidate_key"], edge["target_before_candidate_key"]))
    chainable = len(edges) > 0
    return {
        "triplet_model": "before_terminal -> actuator_delta -> after_terminal",
        "node_mapping": {
            "before_terminal": "TERMINAL",
            "actuator_delta": "ACTION",
            "after_terminal": "TERMINAL",
            "chain_relation": "after TERMINAL can locally request/confirm another before TERMINAL",
        },
        "direct_move_choice": False,
        "runtime_provider_override": False,
        "triplets": triplets,
        "chain_edges": edges[: int(max_edges)],
        "chain_edge_count": len(edges),
        "chainable": chainable,
        "chain_max_distance": float(max_distance),
    }


def _candidate_triplet_view(candidate: dict[str, Any]) -> dict[str, Any]:
    before_names = tuple(candidate["before_cluster"]["feature_names"])
    before = {
        name: float(candidate["before_cluster"]["prototype"][name])
        for name in before_names
    }
    after = {
        name: float(candidate["after_cluster"]["prototype"][name])
        for name in candidate["after_cluster"]["feature_names"]
    }
    shared = tuple(name for name in before_names if name in after)
    delta = terminal_delta(before, after, shared)
    return {
        "candidate_key": candidate["candidate_key"],
        "source_candidate_key": candidate.get("source_candidate_key"),
        "before_terminal": {
            "feature_names": list(before_names),
            "prototype": before,
        },
        "actuator_delta": {
            "feature_names": list(shared),
            "delta": delta,
            "represented_as": "ACTION vector between terminal states",
        },
        "after_terminal": {
            "feature_names": sorted(after),
            "prototype": after,
        },
        "script_plan": candidate["script_plan"],
        "chooses_move_directly": False,
    }


def _curriculum_decision(
    *,
    fragment_result: ScriptFragmentResult,
    chain_view: dict[str, Any],
    legacy_inventory: list[dict[str, Any]],
) -> dict[str, Any]:
    fragment_payload = fragment_result.to_dict()
    fragment_decision = fragment_payload["decision"]
    heldout = fragment_payload["arms"]["fragment_script"]["heldout_all"]
    train = fragment_payload["arms"]["fragment_script"]["train_replay"]
    legacy_ready_count = sum(1 for item in legacy_inventory if item.get("ready") and item.get("formal_validated"))
    bounded_curriculum_allowed = (
        bool(fragment_decision["partial_curriculum_ready"])
        and bool(chain_view["chainable"])
        and int(heldout["rook_losses"]) == 0
        and int(heldout["illegal_moves"]) == 0
        and int(heldout["stalemates"]) == 0
    )
    reasons: list[str] = []
    if not fragment_decision["partial_curriculum_ready"]:
        reasons.append("fragment_checkpoint_not_partial_ready")
    if not chain_view["chainable"]:
        reasons.append("no_triplet_chain_edges")
    if int(heldout["mates"]) == 0:
        reasons.append("no_heldout_conversion_yet")
    if legacy_ready_count == 0:
        reasons.append("no_ready_legacy_control_inventory")
    return {
        "status": "bounded_partial_curriculum_allowed" if bounded_curriculum_allowed else "bounded_partial_curriculum_blocked",
        "bounded_partial_curriculum_allowed": bounded_curriculum_allowed,
        "broad_curriculum_allowed": False,
        "legacy_ready_control_runs": legacy_ready_count,
        "train_activation_count": int(train["script_start_count"]),
        "train_mates": int(train["mates"]),
        "heldout_activation_count": int(heldout["script_start_count"]),
        "heldout_chain_edges": int(chain_view["chain_edge_count"]),
        "heldout_mates": int(heldout["mates"]),
        "heldout_rook_losses": int(heldout["rook_losses"]),
        "heldout_illegal_moves": int(heldout["illegal_moves"]),
        "heldout_stalemates": int(heldout["stalemates"]),
        "direct_move_override": False,
        "runtime_teacher_or_provider": False,
        "next_run": "bounded fragment-chain curriculum over activating local triplets only",
        "reasons": reasons,
    }
