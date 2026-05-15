"""
Baseline to ReCoN Graph Compiler

Converts learned baseline patterns (sensors/actuators) into proper ReCoN graph
structure following Article.md constraints.

Output: krk_entry_topology.json with:
- Root → Hub → Legs hierarchy
- 3-part micro-scripts (precond → actuator → postcond)
- Stable IDs (not indices)
- Blackboard caching
- Parallel Legs (SUB, not POR)
"""

import json
import pickle
from pathlib import Path
from typing import Dict, List, Any
import numpy as np

from recon_lite_hector.learning.baseline import BaselineLearner, SensorSpec, ActuatorSpec
from recon_lite_chess.routing import SkillContractSpec
from recon_lite_chess.training.krk_landmarks import KRK_LANDMARK_STAGE_SPECS


_LANDMARK_TARGETS = {spec.label: spec.target_label for spec in KRK_LANDMARK_STAGE_SPECS}


def canonicalize_skill_id(curriculum_label: str | None) -> str:
    """Map training labels to stable skill IDs without merging skills yet."""
    raw = curriculum_label or "uncategorized"
    normalized = "".join(ch if ch.isalnum() else "_" for ch in raw.lower()).strip("_")
    return f"krk.{normalized or 'uncategorized'}"


def target_goal_label_for_curriculum(label: str | None) -> str:
    """Return the lower-stage goal bank a learned actuator should optimize toward."""
    if label == "stage0_basin":
        return "mate_in_1"
    if label in _LANDMARK_TARGETS:
        return _LANDMARK_TARGETS[label]
    return "mate_in_1"


def provider_metadata_for_label(topology: Dict[str, Any], label: str | None) -> Dict[str, Any]:
    """Return provider provenance defaults for a compiled curriculum label."""
    preservation = dict(topology.get("meta", {}).get("provider_preservation", {}) or {})
    return {
        "provider_version": preservation.get("provider_version"),
        "source_stage": None,
        "source_checkpoint": preservation.get("source_checkpoint"),
        "frozen_provider": bool(preservation.get("frozen_provider", False)),
        "overlay_provider": bool(preservation.get("overlay_provider", False)),
        "validated_profile": preservation.get("validated_profile"),
        "guardrail_status": dict(preservation.get("guardrail_status", {}) or {}),
        "promotion_status": preservation.get("promotion_status"),
    }


def _provider_metadata_payload(
    *,
    skill_id: str,
    curriculum_label: str | None,
    provider_metadata: Dict[str, Any] | None,
    source_stage: int | None = None,
) -> Dict[str, Any]:
    metadata = dict(provider_metadata or {})
    if source_stage is not None:
        metadata["source_stage"] = int(source_stage)
    return {
        "skill_id": skill_id,
        "curriculum_label": curriculum_label,
        "provider_version": metadata.get("provider_version"),
        "source_stage": metadata.get("source_stage"),
        "source_checkpoint": metadata.get("source_checkpoint"),
        "frozen_provider": bool(metadata.get("frozen_provider", False)),
        "overlay_provider": bool(metadata.get("overlay_provider", False)),
        "validated_profile": metadata.get("validated_profile"),
        "guardrail_status": dict(metadata.get("guardrail_status", {}) or {}),
        "promotion_status": metadata.get("promotion_status"),
    }


def annotate_provider_metadata(
    topology: Dict[str, Any],
    *,
    provider_version: str,
    source_checkpoint: str,
    frozen_provider: bool,
    overlay_provider: bool,
    validated_profile: str | None,
    guardrail_status: Dict[str, Any] | None = None,
    only_missing: bool = False,
) -> None:
    """Annotate existing skill/leg/actuator nodes with provider provenance."""
    for node_id, node in topology.get("nodes", {}).items():
        if not isinstance(node, dict):
            continue
        meta = node.setdefault("meta", {})
        if not isinstance(meta, dict):
            continue
        is_provider_node = (
            node_id.startswith("skill.krk.")
            or node_id.startswith("leg_")
            or node_id.startswith("act_script_")
            or node_id.startswith("actuator_")
        )
        if not is_provider_node:
            continue
        if only_missing and meta.get("provider_version"):
            continue
        curriculum_label = meta.get("curriculum_label")
        skill_id = meta.get("skill_id") or canonicalize_skill_id(curriculum_label)
        payload = _provider_metadata_payload(
            skill_id=skill_id,
            curriculum_label=curriculum_label,
            provider_metadata={
                "provider_version": provider_version,
                "source_stage": meta.get("stage"),
                "source_checkpoint": source_checkpoint,
                "frozen_provider": frozen_provider,
                "overlay_provider": overlay_provider,
                "validated_profile": validated_profile,
                "guardrail_status": guardrail_status or {},
            },
            source_stage=meta.get("stage") if meta.get("stage") is not None else None,
        )
        meta.update(payload)


def compile_baseline_to_topology(
    learner_path: Path,
    output_path: Path,
    *,
    provider_version: str | None = None,
    source_checkpoint: str | None = None,
    frozen_provider: bool = False,
    overlay_provider: bool = False,
    validated_profile: str | None = None,
    guardrail_status: Dict[str, Any] | None = None,
) -> Dict:
    """
    Main compilation function.
    
    Args:
        learner_path: Path to pickled BaselineLearner
        output_path: Path to save topology JSON
    
    Returns:
        Topology dictionary
    """
    # Load learner
    with open(learner_path, 'rb') as f:
        learner = pickle.load(f)
    
    print(f"Loaded learner: {len(learner.sensors)} sensors, {len(learner.actuators)} actuators")
    
    # Filter mature sensors
    mature_sensors = [s for s in learner.sensors if s.is_mature]
    print(f"Mature sensors: {len(mature_sensors)}")
    
    # Build topology
    goal_banks = build_goal_banks(learner)
    goal_bank = goal_banks.get("mate_in_1")
    topology = {
        "nodes": {},
        "edges": [],
        "meta": {
            "origin": "baseline_compilation",
            "feature_set": getattr(learner, "feature_set", "legacy"),
            "feature_names": list(getattr(learner, "feature_names", [])),
            "mature_sensors": len(mature_sensors),
            "total_actuators": len(learner.actuators),
            "baseline_xp_avg": float(np.mean([s.xp for s in mature_sensors])) if mature_sensors else 0.0,
            "goal_bank": goal_bank,
            "goal_banks": goal_banks,
            "goal_label": "mate_in_1",
            "goal_normalize": bool(getattr(learner, "normalize_goals", True)),
            "goal_weight": 0.7,
            "goal_lookahead": "max",
            "goal_min_overlap": 8,
            "goal_handoff_threshold": 0.2,
            "successor_contract_gate_enabled": False,
            "successor_contract_mismatch_penalty": 10.0,
            "successor_role_license_enabled": False,
            "successor_role_license_bonus": 0.05,
            "provider_preservation": {
                "schema_version": "provider_preservation.v1",
                "provider_version": provider_version,
                "source_checkpoint": source_checkpoint or str(learner_path),
                "frozen_provider": bool(frozen_provider),
                "overlay_provider": bool(overlay_provider),
                "validated_profile": validated_profile,
                "guardrail_status": guardrail_status or {},
            },
        }
    }
    
    # Create Root
    create_root_node(topology, goal_bank)
    
    # Create Hub
    create_hub_node(topology)
    create_successor_affordance_layer(topology)
    
    # Create Legs (one per actuator), grouped by canonical curriculum skill.
    for actuator in learner.actuators:
        skill_node_id = ensure_skill_node(
            topology,
            getattr(actuator, "curriculum_label", None),
            provider_metadata=provider_metadata_for_label(
                topology,
                getattr(actuator, "curriculum_label", None),
            ),
        )
        create_leg_micro_script(
            topology,
            actuator,
            mature_sensors,
            skill_node_id,
            provider_metadata=provider_metadata_for_label(
                topology,
                getattr(actuator, "curriculum_label", None),
            ),
        )
    
    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(topology, f, indent=2)
    
    print(f"\n✓ Saved topology: {output_path}")
    print(f"  Nodes: {len(topology['nodes'])}")
    print(f"  Edges: {len(topology['edges'])}")
    
    return topology


def compile_overlay_topology(
    *,
    base_topology_path: Path,
    overlay_learner_path: Path,
    output_path: Path,
    overlay_label: str,
    base_provider_version: str = "stage5_validated_v1",
    overlay_provider_version: str = "stage6_overlay_v1",
    base_source_checkpoint: str | None = None,
    overlay_source_checkpoint: str | None = None,
    validated_profile: str | None = "handoff_composition_v1",
) -> Dict[str, Any]:
    """Compose a frozen validated topology with an additive later-stage overlay.

    This intentionally does not replace lower-stage providers. It keeps the
    base topology in place, annotates its providers as frozen, then adds only
    overlay-label actuators from the overlay learner under their own provider
    version.
    """
    topology = json.loads(base_topology_path.read_text(encoding="utf-8"))
    topology.setdefault("nodes", {})
    topology.setdefault("edges", [])
    topology.setdefault("meta", {})
    topology["meta"].setdefault("provider_preservation", {})
    topology["meta"]["provider_preservation"].update({
        "schema_version": "provider_preservation.v1",
        "composition_mode": "frozen_base_plus_overlay",
        "base_topology": str(base_topology_path),
        "overlay_learner": str(overlay_learner_path),
        "base_provider_version": base_provider_version,
        "overlay_provider_version": overlay_provider_version,
        "overlay_label": overlay_label,
        "validated_profile": validated_profile,
        "promotion_status": "overlay_candidate",
    })
    annotate_provider_metadata(
        topology,
        provider_version=base_provider_version,
        source_checkpoint=base_source_checkpoint or str(base_topology_path),
        frozen_provider=True,
        overlay_provider=False,
        validated_profile=validated_profile,
        guardrail_status={
            "stage4_wrong_tempo": "passed_pre_overlay",
            "stage5_fence": "passed_pre_overlay",
        },
        only_missing=True,
    )

    with overlay_learner_path.open("rb") as fh:
        learner = pickle.load(fh)
    mature_sensors = [s for s in learner.sensors if s.is_mature]
    overlay_actuators = [
        actuator
        for actuator in learner.actuators
        if getattr(actuator, "curriculum_label", None) == overlay_label
    ]
    if not overlay_actuators:
        raise ValueError(f"No overlay actuators found for curriculum label {overlay_label!r}")

    overlay_metadata = {
        "provider_version": overlay_provider_version,
        "source_stage": int(max((getattr(a, "stage", 0) or 0) for a in overlay_actuators)),
        "source_checkpoint": overlay_source_checkpoint or str(overlay_learner_path),
        "frozen_provider": False,
        "overlay_provider": True,
        "validated_profile": validated_profile,
        "guardrail_status": {},
        "promotion_status": "overlay_candidate",
    }

    added = []
    for actuator in overlay_actuators:
        skill_node_id = ensure_skill_node(
            topology,
            getattr(actuator, "curriculum_label", None),
            provider_metadata=overlay_metadata,
        )
        create_leg_micro_script(
            topology,
            actuator,
            mature_sensors,
            skill_node_id,
            provider_metadata=overlay_metadata,
            allow_existing=False,
        )
        added.append(f"actuator_{actuator.id}")

    topology["meta"]["provider_preservation"]["overlay_actuators_added"] = added
    topology["meta"]["provider_preservation"]["frozen_base_provider_count"] = sum(
        1
        for node in topology["nodes"].values()
        if isinstance(node, dict) and node.get("meta", {}).get("frozen_provider")
    )
    topology["meta"]["provider_preservation"]["overlay_provider_count"] = sum(
        1
        for node in topology["nodes"].values()
        if isinstance(node, dict) and node.get("meta", {}).get("overlay_provider")
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(topology, indent=2) + "\n", encoding="utf-8")
    print(f"\n✓ Saved overlay topology: {output_path}")
    print(f"  Base topology: {base_topology_path}")
    print(f"  Overlay actuators: {len(overlay_actuators)} ({overlay_label})")
    print(f"  Nodes: {len(topology['nodes'])}")
    print(f"  Edges: {len(topology['edges'])}")
    return topology


def create_root_node(topology: Dict, goal_bank: Dict | None = None):
    """Create KRK_entry root node with blackboard cache"""
    topology["nodes"]["krk_entry"] = {
        "id": "krk_entry",
        "type": "SCRIPT",
        "factory": "recon_lite_chess.krk_baseline_nodes:create_krk_entry_root",
        "meta": {
            "blackboard": {},  # Will cache features + sensor outputs
            "goal_bank": topology.get("meta", {}).get("goal_bank"),
            "goal_banks": topology.get("meta", {}).get("goal_banks", {}),
            "goal_label": topology.get("meta", {}).get("goal_label", "mate_in_1"),
            "goal_normalize": topology.get("meta", {}).get("goal_normalize", True),
            "goal_weight": topology.get("meta", {}).get("goal_weight", 0.7),
            "goal_lookahead": topology.get("meta", {}).get("goal_lookahead", "max"),
            "goal_min_overlap": topology.get("meta", {}).get("goal_min_overlap", 8),
            "goal_handoff_threshold": topology.get("meta", {}).get("goal_handoff_threshold", 0.2),
            "successor_contract_gate_enabled": topology.get("meta", {}).get("successor_contract_gate_enabled", False),
            "successor_contract_mismatch_penalty": topology.get("meta", {}).get("successor_contract_mismatch_penalty", 10.0),
            "successor_role_license_enabled": topology.get("meta", {}).get("successor_role_license_enabled", False),
            "successor_role_license_bonus": topology.get("meta", {}).get("successor_role_license_bonus", 0.05),
            "feature_set": topology.get("meta", {}).get("feature_set", "legacy"),
            "feature_names": topology.get("meta", {}).get("feature_names", []),
            "description": "KRK entry point with feature extraction"
        }
    }
    
    print("Created root: krk_entry")


def create_hub_node(topology: Dict):
    """Create Hub with bandit selection"""
    topology["nodes"]["krk_hub"] = {
        "id": "krk_hub",
        "type": "SCRIPT",
        "factory": "recon_lite_chess.krk_baseline_nodes:create_krk_hub",
        "meta": {
            "bandit_enabled": True,
            "description": "Bandit selector for Leg alternatives"
        }
    }
    
    # Edge: Root → Hub
    topology["edges"].append({
        "src": "krk_entry",
        "dst": "krk_hub",
        "type": "SUB",
        "weight": 1.0
    })
    # SUR confirmation: Hub → Root
    topology["edges"].append({
        "src": "krk_hub",
        "dst": "krk_entry",
        "type": "SUR",
        "weight": 1.0
    })
    
    print("Created hub: krk_hub")


KRK_SUCCESSOR_CONTEXT_TERMS = [
    "fence_exists",
    "fence_stable",
    "fence_needs_repair",
    "fence_already_satisfied",
    "post_fence_conversion_needed",
    "enemy_king_not_at_edge",
    "enemy_king_edge_distance_bin",
    "box_area_large",
    "box_shrink_available",
    "white_king_support_available",
    "white_king_can_improve_support",
    "king_support_improvement_move_exists",
    "wrong_tempo_detected",
    "wrong_tempo_geometry",
    "mate_in_one_available",
    "mate_basin_available",
    "goal_basin_proximity_low",
    "goal_distance_can_decrease",
    "enemy_king_restricted",
    "enemy_king_near_edge",
    "king_approach_after_fence_available",
    "enemy_between_king_and_rook_axis",
    "edge_trap_shape_available",
    "edge_trap_close_geometry",
    "enemy_between_geometry",
    "rook_has_safe_lateral_transfer",
    "safe_rook_long_transfer_available",
    "safe_rook_edge_transfer_available",
    "safe_check_available",
    "rook_transfer_after_fence_available",
    "edge_rook_transfer_recovery_available",
    "corner_net_pressure_available",
    "repeated_abstract_state",
    "rook_oscillation_loop",
    "no_box_progress_recently",
    "no_edge_progress_recently",
    "no_mate_progress_recently",
    "safe_loop_breaking_move_available",
    "loop_breaking_rook_transfer_available",
    "loop_breaking_check_or_cut_available",
    "rook_oscillation_loop_recently_broken",
    "confinement_preserved_after_break",
    "enemy_king_edge_control_preserved",
    "post_stagnation_break_continuation_needed",
    "safe_followup_available",
    "rook_safe",
    "cut_stable",
    "black_king_escape_available",
]


KRK_SUCCESSOR_AFFORDANCES = {
    "krk.stage0_finish": {
        "provider_skill_ids": ["krk.stage0_basin"],
        "source_terms": ["mate_in_one_available", "rook_safe"],
        "required_terms": ["mate_in_one_available", "rook_safe"],
        "veto_terms": [],
    },
    "krk.stage0_king_approach_after_fence": {
        "provider_skill_ids": ["krk.stage0_basin"],
        "source_terms": [
            "king_approach_after_fence_available",
            "post_fence_conversion_needed",
            "rook_safe",
            "white_king_can_improve_support",
            "king_support_improvement_move_exists",
        ],
        "required_terms": ["king_approach_after_fence_available", "rook_safe"],
        "veto_terms": ["mate_in_one_available", "edge_trap_shape_available"],
    },
    "krk.stage0_goal_basin_approach": {
        "provider_skill_ids": ["krk.stage0_basin"],
        "source_terms": [
            "post_fence_conversion_needed",
            "enemy_king_restricted",
            "rook_safe",
            "white_king_support_available",
            "king_support_improvement_move_exists",
            "safe_check_available",
        ],
        "required_terms": ["post_fence_conversion_needed", "rook_safe", "enemy_king_restricted"],
        "veto_terms": ["mate_in_one_available", "edge_trap_shape_available"],
    },
    "krk.rook_transfer_after_fence": {
        "provider_skill_ids": [
            "krk.edge_trap_close",
            "krk.edge_trap_enemy_between",
            "krk.edge_trap_wrong_tempo",
        ],
        "source_terms": [
            "rook_transfer_after_fence_available",
            "safe_rook_long_transfer_available",
            "safe_rook_edge_transfer_available",
            "rook_has_safe_lateral_transfer",
            "post_fence_conversion_needed",
            "rook_safe",
        ],
        "required_terms": ["rook_transfer_after_fence_available", "rook_safe"],
        "veto_terms": ["mate_in_one_available"],
    },
    "krk.edge_rook_transfer_recovery": {
        "provider_skill_ids": [
            "krk.edge_trap_close",
            "krk.edge_trap_enemy_between",
            "krk.edge_trap_wrong_tempo",
        ],
        "source_terms": [
            "edge_rook_transfer_recovery_available",
            "corner_net_pressure_available",
            "safe_rook_edge_transfer_available",
            "enemy_king_near_edge",
            "post_fence_conversion_needed",
            "rook_safe",
        ],
        "required_terms": ["edge_rook_transfer_recovery_available", "rook_safe"],
        "veto_terms": ["mate_in_one_available"],
    },
    "krk.edge_trap_close_recovery": {
        "provider_skill_ids": ["krk.edge_trap_close"],
        "source_terms": [
            "fence_exists",
            "edge_trap_close_geometry",
            "edge_trap_shape_available",
            "rook_has_safe_lateral_transfer",
            "rook_safe",
            "post_fence_conversion_needed",
        ],
        "required_terms": ["fence_exists", "edge_trap_close_geometry", "rook_safe"],
        "veto_terms": ["mate_in_one_available"],
    },
    "krk.edge_trap_enemy_between_recovery": {
        "provider_skill_ids": ["krk.edge_trap_enemy_between"],
        "source_terms": [
            "fence_exists",
            "enemy_between_geometry",
            "enemy_between_king_and_rook_axis",
            "edge_trap_shape_available",
            "rook_has_safe_lateral_transfer",
            "rook_safe",
            "post_fence_conversion_needed",
        ],
        "required_terms": ["fence_exists", "enemy_between_geometry", "rook_safe"],
        "veto_terms": ["mate_in_one_available"],
    },
    "krk.edge_trap_wrong_tempo_recovery": {
        "provider_skill_ids": ["krk.edge_trap_wrong_tempo"],
        "source_terms": [
            "fence_exists",
            "wrong_tempo_geometry",
            "enemy_between_king_and_rook_axis",
            "wrong_tempo_detected",
            "rook_safe",
            "post_fence_conversion_needed",
        ],
        "required_terms": [
            "fence_exists",
            "wrong_tempo_geometry",
            "enemy_between_king_and_rook_axis",
            "rook_safe",
        ],
        "veto_terms": ["mate_in_one_available"],
    },
    "krk.fence_repair": {
        "provider_skill_ids": ["krk.fence_maintenance"],
        "source_terms": ["fence_needs_repair", "rook_safe"],
        "required_terms": ["fence_needs_repair", "rook_safe"],
        "veto_terms": ["fence_already_satisfied"],
    },
    "krk.fence_maintenance": {
        "provider_skill_ids": ["krk.fence_maintenance"],
        "source_terms": [
            "fence_exists",
            "fence_needs_repair",
            "rook_safe",
            "post_fence_conversion_needed",
        ],
        "required_terms": ["fence_exists", "rook_safe"],
        "veto_terms": ["fence_already_satisfied", "mate_in_one_available"],
    },
    "krk.stagnation_breaker_affordance": {
        "provider_skill_ids": [
            "krk.stage0_basin",
            "krk.edge_trap_close",
            "krk.edge_trap_enemy_between",
            "krk.edge_trap_wrong_tempo",
        ],
        "source_terms": [
            "rook_oscillation_loop",
            "no_box_progress_recently",
            "no_edge_progress_recently",
            "no_mate_progress_recently",
            "safe_loop_breaking_move_available",
            "loop_breaking_rook_transfer_available",
            "loop_breaking_check_or_cut_available",
        ],
        "required_terms": [
            "rook_oscillation_loop",
            "no_box_progress_recently",
            "safe_loop_breaking_move_available",
        ],
        "veto_terms": ["mate_in_one_available"],
    },
    "krk.post_stagnation_break_continuation": {
        "provider_skill_ids": [
            "krk.stage0_basin",
            "krk.edge_trap_close",
            "krk.edge_trap_enemy_between",
            "krk.edge_trap_wrong_tempo",
        ],
        "source_terms": [
            "rook_oscillation_loop_recently_broken",
            "confinement_preserved_after_break",
            "enemy_king_edge_control_preserved",
            "post_stagnation_break_continuation_needed",
            "safe_followup_available",
        ],
        "required_terms": [
            "rook_oscillation_loop_recently_broken",
            "confinement_preserved_after_break",
            "post_stagnation_break_continuation_needed",
            "safe_followup_available",
        ],
        "veto_terms": ["mate_in_one_available"],
    },
}


def create_successor_affordance_layer(topology: Dict) -> None:
    """Create visible, opt-in KRK successor-affordance evidence nodes."""
    hub_id = "krk_successor_affordance_hub"
    topology["nodes"][hub_id] = {
        "id": hub_id,
        "type": "SCRIPT",
        "factory": None,
        "meta": {
            "successor_affordance_layer": True,
            "enabled_by_default": False,
            "description": "Visible KRK successor-affordance evidence hub; non-causal unless enabled.",
        },
    }
    topology["edges"].append({
        "src": "krk_hub",
        "dst": hub_id,
        "type": "SUB",
        "weight": 1.0,
    })
    topology["edges"].append({
        "src": hub_id,
        "dst": "krk_hub",
        "type": "SUR",
        "weight": 1.0,
    })

    for term in KRK_SUCCESSOR_CONTEXT_TERMS:
        term_id = f"terminal.krk.{term}"
        topology["nodes"][term_id] = {
            "id": term_id,
            "type": "TERMINAL",
            "factory": "recon_lite_chess.krk_baseline_nodes:create_krk_context_terminal",
            "meta": {
                "term": term,
                "visible_successor_term": True,
                "description": f"Visible KRK context term: {term}",
            },
        }
        topology["edges"].append({
            "src": hub_id,
            "dst": term_id,
            "type": "SUB",
            "weight": 1.0,
        })
        topology["edges"].append({
            "src": term_id,
            "dst": hub_id,
            "type": "SUR",
            "weight": 1.0,
        })

    for role_id, config in KRK_SUCCESSOR_AFFORDANCES.items():
        role_name = role_id.split(".", 1)[1]
        provider_skill_ids = list(config.get("provider_skill_ids", [role_id]))
        node_id = f"script.krk.successor.{role_name}_affordance"
        marker_id = f"terminal.krk.successor.{role_name}_marker"
        topology["nodes"][node_id] = {
            "id": node_id,
            "type": "SCRIPT",
            "factory": "recon_lite_chess.krk_baseline_nodes:create_krk_successor_affordance",
            "meta": {
                "successor_skill_id": role_id,
                "role_id": role_id,
                "provider_skill_ids": provider_skill_ids,
                "source_terms": config["source_terms"],
                "required_terms": config["required_terms"],
                "veto_terms": config["veto_terms"],
                "visible_successor_affordance": True,
                "description": f"Visible successor role {role_id} licensing {provider_skill_ids}",
            },
        }
        topology["edges"].append({
            "src": hub_id,
            "dst": node_id,
            "type": "SUB",
            "weight": 1.0,
        })
        topology["edges"].append({
            "src": node_id,
            "dst": hub_id,
            "type": "SUR",
            "weight": 1.0,
        })
        topology["nodes"][marker_id] = {
            "id": marker_id,
            "type": "TERMINAL",
            "factory": "recon_lite_chess.krk_baseline_nodes:create_krk_affordance_marker_terminal",
            "meta": {
                "successor_skill_id": role_id,
                "role_id": role_id,
                "provider_skill_ids": provider_skill_ids,
                "visible_successor_affordance_marker": True,
                "description": f"Marker terminal for {role_id} role affordance SCRIPT execution",
            },
        }
        topology["edges"].append({
            "src": node_id,
            "dst": marker_id,
            "type": "SUB",
            "weight": 1.0,
        })
        topology["edges"].append({
            "src": marker_id,
            "dst": node_id,
            "type": "SUR",
            "weight": 1.0,
        })

    topology["meta"]["successor_affordance_layer"] = {
        "enabled_by_default": False,
        "context_terms": KRK_SUCCESSOR_CONTEXT_TERMS,
        "successor_roles": sorted(KRK_SUCCESSOR_AFFORDANCES),
        "successor_skills": sorted({
            provider
            for config in KRK_SUCCESSOR_AFFORDANCES.values()
            for provider in config.get("provider_skill_ids", [])
        }),
    }
    print("Created visible successor-affordance layer")


def ensure_skill_node(
    topology: Dict,
    curriculum_label: str | None,
    provider_metadata: Dict[str, Any] | None = None,
) -> str:
    """Create or return the ReCoN skill node for a curriculum label."""
    skill_id = canonicalize_skill_id(curriculum_label)
    skill_name = skill_id.split(".", 1)[1]
    node_id = f"skill.{skill_id}"
    if node_id in topology["nodes"]:
        topology["nodes"][node_id].setdefault("meta", {}).update(
            _provider_metadata_payload(
                skill_id=skill_id,
                curriculum_label=curriculum_label,
                provider_metadata=provider_metadata,
            )
        )
        return node_id

    contract = SkillContractSpec(
        skill_id=skill_id,
        source_node_id=node_id,
        scope="krk",
        affordance_terms=[
            f"affordance.{skill_id}",
            f"curriculum_label.{curriculum_label or 'uncategorized'}",
        ],
        request_terms=[f"request.{skill_id}"],
        confirmation_terms=[f"confirm.{skill_id}"],
        continuation_exports={
            f"target_goal.{target_goal_label_for_curriculum(curriculum_label)}": 1.0,
        },
        evidence_terms={
            "curriculum_label": curriculum_label,
            "canonical_skill_id": skill_id,
            "target_goal_label": target_goal_label_for_curriculum(curriculum_label),
        },
    )
    topology["nodes"][node_id] = {
        "id": node_id,
        "type": "SCRIPT",
        "factory": None,
        "meta": {
            "skill_id": skill_id,
            "canonical_skill_id": skill_id,
            "curriculum_label": curriculum_label,
            "target_goal_label": target_goal_label_for_curriculum(curriculum_label),
            "skill_contract": contract.to_dict(),
            **_provider_metadata_payload(
                skill_id=skill_id,
                curriculum_label=curriculum_label,
                provider_metadata=provider_metadata,
            ),
            "description": f"KRK skill group {skill_name}",
        },
    }
    topology["edges"].append({
        "src": "krk_hub",
        "dst": node_id,
        "type": "SUB",
        "weight": 1.0,
    })
    topology["edges"].append({
        "src": node_id,
        "dst": "krk_hub",
        "type": "SUR",
        "weight": 1.0,
    })
    print(f"Created skill: {node_id}")
    return node_id


def create_leg_micro_script(
    topology: Dict,
    actuator: Any,
    sensors: List[Any],
    skill_node_id: str | None = None,
    provider_metadata: Dict[str, Any] | None = None,
    allow_existing: bool = True,
):
    """
    Create 3-part micro-script for one actuator pattern.
    
    Structure:
    Leg (SCRIPT)
    ├─ SUB → Precondition (SCRIPT, and-gate)
    │   ├─ SUB → sensor_X (TERMINAL)
    │   └─ SUB → sensor_Y (TERMINAL)
    ├─ SUB → Actuator (TERMINAL)
    │   └─ POR from Precondition
    └─ SUB → Postcondition (SCRIPT, and-gate)
        ├─ SUB → sensor_X_post (TERMINAL)
        └─ SUB → sensor_Y_post (TERMINAL)
        └─ POR from Actuator
    """
    leg_id = f"leg_{actuator.id}"
    precond_id = f"precond_{actuator.id}"
    act_script_id = f"act_script_{actuator.id}"
    actuator_id = f"actuator_{actuator.id}"
    postcond_id = f"postcond_{actuator.id}"
    if skill_node_id is None:
        skill_node_id = ensure_skill_node(
            topology,
            getattr(actuator, "curriculum_label", None),
            provider_metadata=provider_metadata,
        )
    existing_ids = {leg_id, precond_id, act_script_id, actuator_id, postcond_id}
    conflicts = sorted(existing_ids.intersection(topology.get("nodes", {})))
    if conflicts and not allow_existing:
        raise ValueError(
            "Overlay provider conflicts with existing topology node IDs: "
            + ", ".join(conflicts)
        )
    if conflicts and allow_existing:
        for node_id in conflicts:
            topology["nodes"][node_id].setdefault("meta", {}).update(
                _provider_metadata_payload(
                    skill_id=topology["nodes"][skill_node_id]["meta"]["skill_id"],
                    curriculum_label=getattr(actuator, "curriculum_label", None),
                    provider_metadata=provider_metadata,
                    source_stage=getattr(actuator, "stage", None),
                )
            )
        return
    provider_payload = _provider_metadata_payload(
        skill_id=topology["nodes"][skill_node_id]["meta"]["skill_id"],
        curriculum_label=getattr(actuator, "curriculum_label", None),
        provider_metadata=provider_metadata,
        source_stage=getattr(actuator, "stage", None),
    )
    
    # Leg SCRIPT
    topology["nodes"][leg_id] = {
        "id": leg_id,
        "type": "SCRIPT",
        "factory": "recon_lite_chess.krk_baseline_nodes:create_leg_script",
        "meta": {
            "actuator_id": actuator.id,
            "skill_id": topology["nodes"][skill_node_id]["meta"]["skill_id"],
            "curriculum_label": getattr(actuator, "curriculum_label", None),
            "target_goal_label": target_goal_label_for_curriculum(
                getattr(actuator, "curriculum_label", None)
            ),
            **provider_payload,
            "description": f"Leg for actuator pattern {actuator.id}"
        }
    }
    
    # Edge: Skill → Leg (parallel alternative within a skill group)
    topology["edges"].append({
        "src": skill_node_id,
        "dst": leg_id,
        "type": "SUB",
        "weight": 1.0
    })
    # SUR confirmation: Leg → Skill
    topology["edges"].append({
        "src": leg_id,
        "dst": skill_node_id,
        "type": "SUR",
        "weight": 1.0
    })
    
    # Part 1: Precondition gate
    topology["nodes"][precond_id] = {
        "id": precond_id,
        "type": "SCRIPT",
        "factory": "recon_lite_chess.krk_baseline_nodes:create_and_gate",
        "meta": {
            "aggregation": "and",
            "description": "Precondition sensors must all fire"
        }
    }
    
    topology["edges"].append({
        "src": leg_id,
        "dst": precond_id,
        "type": "SUB",
        "weight": 1.0
    })
    # SUR confirmation: Precond → Leg
    topology["edges"].append({
        "src": precond_id,
        "dst": leg_id,
        "type": "SUR",
        "weight": 1.0
    })
    
    # Add precondition sensors
    sensor_map = {s.id: s for s in sensors}
    for sensor_idx in actuator.actuator_spec.sensor_indices:
        sensor = None
        # Actuator spec indices are relative to the mature sensor list
        if 0 <= sensor_idx < len(sensors):
            sensor = sensors[sensor_idx]
        elif sensor_idx in sensor_map:
            # Fallback: treat as absolute sensor id
            sensor = sensor_map[sensor_idx]
        if sensor is not None:
            sensor_id = f"sensor_{sensor.id}"
            
            create_sensor_terminal(topology, sensor_id, sensor)
            
            topology["edges"].append({
                "src": precond_id,
                "dst": sensor_id,
                "type": "SUB",
                "weight": 1.0
            })
            # SUR confirmation: sensor → precond
            topology["edges"].append({
                "src": sensor_id,
                "dst": precond_id,
                "type": "SUR",
                "weight": 1.0
            })
    
    # Part 2: Actuator script wrapper (SCRIPT)
    topology["nodes"][act_script_id] = {
        "id": act_script_id,
        "type": "SCRIPT",
        "factory": "recon_lite_chess.krk_baseline_nodes:create_act_script",
        "meta": {
            "curriculum_label": getattr(actuator, "curriculum_label", None),
            "target_goal_label": target_goal_label_for_curriculum(
                getattr(actuator, "curriculum_label", None)
            ),
            **provider_payload,
            "description": "Actuator wrapper (SCRIPT)"
        }
    }
    
    topology["edges"].append({
        "src": leg_id,
        "dst": act_script_id,
        "type": "SUB",
        "weight": 1.0
    })
    # SUR confirmation: act_script → leg
    topology["edges"].append({
        "src": act_script_id,
        "dst": leg_id,
        "type": "SUR",
        "weight": 1.0
    })
    
    # Actuator terminal (SUB under actuator script)
    create_actuator_terminal(
        topology,
        actuator_id,
        actuator,
        sensors,
        provider_metadata=provider_metadata,
    )
    
    topology["edges"].append({
        "src": act_script_id,
        "dst": actuator_id,
        "type": "SUB",
        "weight": 1.0
    })
    # SUR confirmation: actuator → act_script
    topology["edges"].append({
        "src": actuator_id,
        "dst": act_script_id,
        "type": "SUR",
        "weight": 1.0
    })
    
    # Part 3: Postcondition gate (verify Δs)
    topology["nodes"][postcond_id] = {
        "id": postcond_id,
        "type": "SCRIPT",
        "factory": "recon_lite_chess.krk_baseline_nodes:create_and_gate",
        "meta": {
            "aggregation": "and",
            "description": "Postcondition verification"
        }
    }
    
    topology["edges"].append({
        "src": leg_id,
        "dst": postcond_id,
        "type": "SUB",
        "weight": 1.0
    })
    # SUR confirmation: postcond → leg
    topology["edges"].append({
        "src": postcond_id,
        "dst": leg_id,
        "type": "SUR",
        "weight": 1.0
    })
    
    # POR sequencing between scripts only
    topology["edges"].append({
        "src": precond_id,
        "dst": act_script_id,
        "type": "POR",
        "weight": 1.0
    })
    # RET (temporal return): Act → Precond
    topology["edges"].append({
        "src": act_script_id,
        "dst": precond_id,
        "type": "RET",
        "weight": 1.0
    })
    
    topology["edges"].append({
        "src": act_script_id,
        "dst": postcond_id,
        "type": "POR",
        "weight": 1.0
    })
    # RET (temporal return): Postcond → Act
    topology["edges"].append({
        "src": postcond_id,
        "dst": act_script_id,
        "type": "RET",
        "weight": 1.0
    })
    
    # Add postcondition sensors (same as precondition, different instances)
    for sensor_idx in actuator.actuator_spec.sensor_indices:
        sensor = None
        if 0 <= sensor_idx < len(sensors):
            sensor = sensors[sensor_idx]
        elif sensor_idx in sensor_map:
            sensor = sensor_map[sensor_idx]
        if sensor is not None:
            sensor_post_id = f"sensor_{sensor.id}_post_{actuator.id}"
            
            create_sensor_terminal(topology, sensor_post_id, sensor)
            
            topology["edges"].append({
                "src": postcond_id,
                "dst": sensor_post_id,
                "type": "SUB",
                "weight": 1.0
            })
            # SUR confirmation: sensor_post → postcond
            topology["edges"].append({
                "src": sensor_post_id,
                "dst": postcond_id,
                "type": "SUR",
                "weight": 1.0
            })
    
    print(f"Created leg: {leg_id} with {len(actuator.actuator_spec.sensor_indices)} sensors")


def create_sensor_terminal(topology: Dict, sensor_id: str, sensor: Any):
    """Create TERMINAL node for sensor with stable IDs"""
    if sensor_id in topology["nodes"]:
        return  # Already created
    
    # Get feature keys (stable, not indices)
    feature_mask_keys = get_feature_keys_from_mask(sensor.sensor_spec.feature_mask)
    
    topology["nodes"][sensor_id] = {
        "id": sensor_id,
        "type": "TERMINAL",
        "factory": "recon_lite_chess.krk_baseline_nodes:create_sensor_terminal",
        "meta": {
            "origin": "baseline",
            "stage": sensor.stage,
            "baseline_xp": float(sensor.xp),
            "readout_type": sensor.sensor_spec.readout_type,
            "feature_mask_keys": feature_mask_keys,
            "readout_params": sensor.sensor_spec.readout_params,
            "is_mature": sensor.is_mature,
            "activations": sensor.activations,
            "cycles_alive": sensor.cycles_alive
        }
    }


def create_actuator_terminal(
    topology: Dict,
    actuator_id: str,
    actuator: Any,
    sensors: List[Any],
    provider_metadata: Dict[str, Any] | None = None,
):
    """Create TERMINAL node for actuator with stable target IDs"""
    sensor_map = {s.id: s for s in sensors}
    
    # Build targets list (stable IDs)
    targets = []
    goal_delta = {}
    
    for idx, delta_val in zip(
        actuator.actuator_spec.sensor_indices,
        actuator.actuator_spec.goal_delta
    ):
        sensor = None
        if 0 <= idx < len(sensors):
            sensor = sensors[idx]
        elif idx in sensor_map:
            sensor = sensor_map[idx]
        if sensor is not None:
            sensor_id = f"sensor_{sensor.id}"
            targets.append(sensor_id)
            goal_delta[sensor_id] = float(delta_val)
    
    topology["nodes"][actuator_id] = {
        "id": actuator_id,
        "type": "TERMINAL",
        "factory": "recon_lite_chess.krk_baseline_nodes:create_actuator_terminal",
        "meta": {
            "origin": "baseline",
            "stage": actuator.stage,
            "skill_id": canonicalize_skill_id(getattr(actuator, "curriculum_label", None)),
            "curriculum_label": getattr(actuator, "curriculum_label", None),
            "target_goal_label": target_goal_label_for_curriculum(
                getattr(actuator, "curriculum_label", None)
            ),
            **_provider_metadata_payload(
                skill_id=canonicalize_skill_id(getattr(actuator, "curriculum_label", None)),
                curriculum_label=getattr(actuator, "curriculum_label", None),
                provider_metadata=provider_metadata,
                source_stage=getattr(actuator, "stage", None),
            ),
            "baseline_xp": float(actuator.xp),
            "targets": targets,  # Stable IDs
            "goal_delta": goal_delta,  # Keyed by stable IDs
            "match_mode": actuator.actuator_spec.match_mode,
            "activations": actuator.activations,
            "cycles_alive": actuator.cycles_alive
        }
    }


def get_feature_keys_from_mask(feature_mask: np.ndarray) -> List[str]:
    """
    Convert boolean feature mask to stable feature keys.
    
    For now, use indices as keys. In future, map to named features.
    """
    indices = np.where(feature_mask)[0]
    return [f"feature_{i}" for i in indices]


def build_goal_bank(learner: BaselineLearner, label: str = "mate_in_1") -> Dict[str, Any] | None:
    """
    Build a compact goal bank for runtime scoring.

    Returns a dict with:
      - label
      - goals: list of {values: {sensor_id: value}, count}
      - sensor_specs: map of sensor_id -> spec
      - goal_eps: merge threshold used in training
    """
    goals = [g for g in learner.goal_memories if g.label == label]
    if not goals:
        return None

    # Prefer goals with explicit sensor_ids
    sensor_ids = None
    for g in goals:
        if getattr(g, "sensor_ids", None):
            sensor_ids = g.sensor_ids
            break

    if sensor_ids is None:
        # Best-effort fallback: cannot safely align goal vectors without sensor ids
        print("⚠️  Warning: goal prototypes missing sensor_ids; skipping goal bank export.")
        return None

    sensor_map = {s.id: s for s in learner.sensors}
    sensor_specs: Dict[str, Any] = {}
    sensor_weights: Dict[str, float] = {}
    for sid in sensor_ids:
        sensor = sensor_map.get(sid)
        if sensor is None:
            continue
        weight = 1.0 + max(0.0, float(sensor.xp))
        sensor_specs[f"sensor_{sid}"] = {
            "readout_type": sensor.sensor_spec.readout_type,
            "feature_mask_keys": get_feature_keys_from_mask(sensor.sensor_spec.feature_mask),
            "readout_params": sensor.sensor_spec.readout_params,
            "weight": weight,
        }
        sensor_weights[f"sensor_{sid}"] = weight

    goals_payload = []
    for g in goals:
        if getattr(g, "sensor_ids", None) != sensor_ids:
            continue
        values = {f"sensor_{sid}": float(val) for sid, val in zip(sensor_ids, g.s0.tolist())}
        goals_payload.append({
            "values": values,
            "count": int(getattr(g, "count", 1)),
        })

    if not goals_payload:
        return None

    return {
        "label": label,
        "sensor_ids": list(sensor_ids),
        "goals": goals_payload,
        "sensor_specs": sensor_specs,
        "sensor_weights": sensor_weights,
        "goal_eps": float(getattr(learner, "goal_eps", 0.15)),
    }


def build_goal_banks(learner: BaselineLearner) -> Dict[str, Dict[str, Any]]:
    """Export every labelled goal bank with enough sensor alignment for runtime scoring."""
    labels = sorted({getattr(g, "label", "") for g in learner.goal_memories if getattr(g, "label", "")})
    banks: Dict[str, Dict[str, Any]] = {}
    for label in labels:
        bank = build_goal_bank(learner, label=label)
        if bank:
            banks[label] = bank
    return banks


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Compile baseline to ReCoN topology")
    parser.add_argument("--learner", type=Path, default=None,
                       help="Path to pickled learner (e.g., final_learner.pkl)")
    parser.add_argument("--output", type=Path, default=Path("topologies/krk_entry_topology.json"),
                       help="Output topology JSON path")
    parser.add_argument("--provider-version", default=None,
                       help="Optional provider version metadata for monolithic compilation")
    parser.add_argument("--source-checkpoint", default=None,
                       help="Optional source checkpoint metadata")
    parser.add_argument("--frozen-provider", action="store_true",
                       help="Mark compiled providers as frozen")
    parser.add_argument("--overlay-provider", action="store_true",
                       help="Mark compiled providers as overlay providers")
    parser.add_argument("--validated-profile", default=None,
                       help="Optional validated composition profile metadata")
    parser.add_argument("--base-topology", type=Path, default=None,
                       help="Validated base topology for overlay compilation")
    parser.add_argument("--overlay-learner", type=Path, default=None,
                       help="Learner containing overlay providers")
    parser.add_argument("--overlay-label", default=None,
                       help="Curriculum label to extract from --overlay-learner")
    parser.add_argument("--base-provider-version", default="stage5_validated_v1")
    parser.add_argument("--overlay-provider-version", default="stage6_overlay_v1")
    parser.add_argument("--base-source-checkpoint", default=None)
    parser.add_argument("--overlay-source-checkpoint", default=None)
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("Baseline → ReCoN Graph Compiler")
    print("=" * 70)
    
    if args.base_topology or args.overlay_learner or args.overlay_label:
        if not (args.base_topology and args.overlay_learner and args.overlay_label):
            raise SystemExit(
                "--base-topology, --overlay-learner, and --overlay-label are required together"
            )
        topology = compile_overlay_topology(
            base_topology_path=args.base_topology,
            overlay_learner_path=args.overlay_learner,
            output_path=args.output,
            overlay_label=args.overlay_label,
            base_provider_version=args.base_provider_version,
            overlay_provider_version=args.overlay_provider_version,
            base_source_checkpoint=args.base_source_checkpoint,
            overlay_source_checkpoint=args.overlay_source_checkpoint,
            validated_profile=args.validated_profile,
        )
    else:
        if args.learner is None:
            raise SystemExit("--learner is required unless overlay compilation is used")
        topology = compile_baseline_to_topology(
            args.learner,
            args.output,
            provider_version=args.provider_version,
            source_checkpoint=args.source_checkpoint,
            frozen_provider=args.frozen_provider,
            overlay_provider=args.overlay_provider,
            validated_profile=args.validated_profile,
        )
    
    print("\n" + "=" * 70)
    print("✓ Compilation complete!")
    print("=" * 70)
