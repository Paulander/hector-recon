import json
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from recon_lite import FormalReConEngine, ReConEngine
from recon_lite.graph import Graph, LinkType, Node, NodeType
from recon_lite_chess.graph.builder import (
    build_graph_from_topology,
    ensure_formal_pairs,
    validate_formal_pairs,
)
from recon_lite_chess.spawn_point import SpawnPoint, TrialMicroScript
from recon_lite_chess.spawn_point import SpawnPointConfig, SpawnPointManager
from recon_lite_chess.triplets import TripletGrowthProfile
from recon_lite_hector.engine import create_recon_engine
from recon_lite_hector.plasticity.bandit import BanditArmState
from recon_lite_hector.plasticity.fast import init_plasticity_state

_baseline_to_recon = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "baseline_to_recon",
        Path(__file__).resolve().parents[1] / "scripts" / "baseline_to_recon.py",
    )
)
assert _baseline_to_recon.__spec__ is not None
assert _baseline_to_recon.__spec__.loader is not None
_baseline_to_recon.__spec__.loader.exec_module(_baseline_to_recon)
create_root_node = _baseline_to_recon.create_root_node
create_hub_node = _baseline_to_recon.create_hub_node
create_leg_micro_script = _baseline_to_recon.create_leg_micro_script
target_goal_label_for_curriculum = _baseline_to_recon.target_goal_label_for_curriculum

_provider_promotion = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "evaluate_provider_promotion",
        Path(__file__).resolve().parents[1] / "scripts" / "evaluate_provider_promotion.py",
    )
)
assert _provider_promotion.__spec__ is not None
assert _provider_promotion.__spec__.loader is not None
_provider_promotion.__spec__.loader.exec_module(_provider_promotion)

_structural_candidates = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "generate_structural_candidates",
        Path(__file__).resolve().parents[1] / "scripts" / "generate_structural_candidates.py",
    )
)
assert _structural_candidates.__spec__ is not None
assert _structural_candidates.__spec__.loader is not None
_structural_candidates.__spec__.loader.exec_module(_structural_candidates)


def test_engine_selector_preserves_pragmatic_default_and_exposes_formal():
    pragmatic = create_recon_engine(Graph())
    assert isinstance(pragmatic, ReConEngine)

    graph = Graph()
    graph.add_node(Node("root", NodeType.SCRIPT))
    graph.add_node(Node("sensor", NodeType.TERMINAL, predicate=lambda _n, _e: (True, True)))
    graph.add_hierarchy_pair("root", "sensor")

    formal = create_recon_engine(graph, mode="formal")
    assert isinstance(formal, FormalReConEngine)


def test_topology_builder_can_normalize_or_validate_formal_pairs(tmp_path):
    topology_path = tmp_path / "topology.json"
    topology_path.write_text(
        json.dumps(
            {
                "nodes": [
                    {"id": "root", "type": "SCRIPT"},
                    {"id": "sensor", "type": "TERMINAL"},
                ],
                "edges": [
                    {"src": "root", "dst": "sensor", "type": "SUB"},
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="requires reverse SUR"):
        build_graph_from_topology(topology_path, formal_pairs="validate")

    graph = build_graph_from_topology(topology_path, formal_pairs="normalize")
    validate_formal_pairs(graph)
    assert _has_edge(graph, "root", "sensor", LinkType.SUB)
    assert _has_edge(graph, "sensor", "root", LinkType.SUR)


def test_baseline_compiled_triplet_topology_passes_formal_pair_validation(tmp_path):
    topology = {"nodes": {}, "edges": [], "meta": {}}
    sensor = _dummy_sensor()
    actuator = _dummy_actuator()

    create_root_node(topology)
    create_hub_node(topology)
    create_leg_micro_script(topology, actuator, [sensor])

    topology_path = tmp_path / "baseline_triplet.json"
    topology_path.write_text(json.dumps(topology), encoding="utf-8")

    graph = build_graph_from_topology(topology_path, formal_pairs="validate")

    validate_formal_pairs(graph)
    assert _has_edge(graph, "precond_7", "act_script_7", LinkType.POR)
    assert _has_edge(graph, "act_script_7", "precond_7", LinkType.RET)
    assert _has_edge(graph, "act_script_7", "postcond_7", LinkType.POR)
    assert _has_edge(graph, "postcond_7", "act_script_7", LinkType.RET)


def test_baseline_compiler_marks_stage_target_goal_label():
    topology = {"nodes": {}, "edges": [], "meta": {}}
    sensor = _dummy_sensor()
    actuator = _dummy_actuator()
    actuator.curriculum_label = "edge_trap_close"
    actuator.stage = 2

    create_root_node(topology)
    create_hub_node(topology)
    create_leg_micro_script(topology, actuator, [sensor])

    assert target_goal_label_for_curriculum("stage0_basin") == "mate_in_1"
    assert target_goal_label_for_curriculum("edge_trap_close") == "stage0_basin"
    assert topology["nodes"]["leg_7"]["meta"]["target_goal_label"] == "stage0_basin"
    assert topology["nodes"]["actuator_7"]["meta"]["target_goal_label"] == "stage0_basin"


def test_baseline_compiler_records_provider_provenance_metadata():
    topology = {"nodes": {}, "edges": [], "meta": {}}
    sensor = _dummy_sensor()
    actuator = _dummy_actuator()
    actuator.curriculum_label = "fence_established"
    provider_metadata = {
        "provider_version": "stage5_validated_v1",
        "source_stage": 5,
        "source_checkpoint": "stage5.pkl",
        "frozen_provider": True,
        "overlay_provider": False,
        "validated_profile": "handoff_composition_v1",
        "guardrail_status": {"stage5_fence": "passed"},
    }

    create_root_node(topology)
    create_hub_node(topology)
    skill_node_id = _baseline_to_recon.ensure_skill_node(
        topology,
        "fence_established",
        provider_metadata=provider_metadata,
    )
    create_leg_micro_script(
        topology,
        actuator,
        [sensor],
        skill_node_id,
        provider_metadata=provider_metadata,
    )

    for node_id in ("skill.krk.fence_established", "leg_7", "actuator_7"):
        meta = topology["nodes"][node_id]["meta"]
        assert meta["provider_version"] == "stage5_validated_v1"
        assert meta["source_checkpoint"] == "stage5.pkl"
        assert meta["frozen_provider"] is True
        assert meta["overlay_provider"] is False
        assert meta["validated_profile"] == "handoff_composition_v1"


def test_annotate_provider_metadata_marks_existing_provider_nodes():
    topology = {
        "nodes": {
            "skill.krk.stage0_basin": {
                "id": "skill.krk.stage0_basin",
                "type": "SCRIPT",
                "meta": {"skill_id": "krk.stage0_basin", "curriculum_label": "stage0_basin"},
            },
            "leg_2": {
                "id": "leg_2",
                "type": "SCRIPT",
                "meta": {"skill_id": "krk.stage0_basin", "curriculum_label": "stage0_basin"},
            },
            "terminal.krk.rook_safe": {
                "id": "terminal.krk.rook_safe",
                "type": "TERMINAL",
                "meta": {"term": "rook_safe"},
            },
        },
        "edges": [],
        "meta": {},
    }

    _baseline_to_recon.annotate_provider_metadata(
        topology,
        provider_version="stage5_validated_v1",
        source_checkpoint="stage5_topology.json",
        frozen_provider=True,
        overlay_provider=False,
        validated_profile="handoff_composition_v1",
    )

    assert topology["nodes"]["skill.krk.stage0_basin"]["meta"]["frozen_provider"] is True
    assert topology["nodes"]["leg_2"]["meta"]["provider_version"] == "stage5_validated_v1"
    assert "provider_version" not in topology["nodes"]["terminal.krk.rook_safe"]["meta"]


def test_provider_promotion_eval_promotes_when_stage_and_guardrails_pass(tmp_path):
    stage_path = tmp_path / "stage.json"
    guardrail_path = tmp_path / "guardrail.json"
    payload = {
        "total": 100,
        "improved": 100,
        "worsened": 0,
        "playouts": {"mate": 100},
        "shadow_candidates": [],
    }
    stage_path.write_text(json.dumps(payload), encoding="utf-8")
    guardrail_path.write_text(json.dumps(payload), encoding="utf-8")

    result = _provider_promotion.evaluate_promotion(
        stage_artifact=stage_path,
        guardrail_artifacts=[guardrail_path],
        min_improved_rate=0.70,
        max_worsened_rate=0.20,
        min_mate_rate=0.65,
        max_max_plies_rate=0.25,
        max_shadow_candidates=0,
    )

    assert result["schema_version"] == "provider_promotion_eval.v1"
    assert result["promotion_status"] == "promoted"
    assert result["stage"]["passed"] is True
    assert result["guardrails"][0]["passed"] is True


def test_provider_promotion_eval_keeps_stage_as_overlay_when_guardrail_fails(tmp_path):
    stage_path = tmp_path / "stage.json"
    guardrail_path = tmp_path / "guardrail.json"
    stage_path.write_text(
        json.dumps({
            "total": 100,
            "improved": 100,
            "worsened": 0,
            "playouts": {"mate": 100},
            "shadow_candidates": [],
        }),
        encoding="utf-8",
    )
    guardrail_path.write_text(
        json.dumps({
            "total": 100,
            "improved": 100,
            "worsened": 0,
            "playouts": {"mate": 50, "max_plies": 50},
            "shadow_candidates": [],
        }),
        encoding="utf-8",
    )

    result = _provider_promotion.evaluate_promotion(
        stage_artifact=stage_path,
        guardrail_artifacts=[guardrail_path],
        min_improved_rate=0.70,
        max_worsened_rate=0.20,
        min_mate_rate=0.65,
        max_max_plies_rate=0.25,
        max_shadow_candidates=0,
    )

    assert result["promotion_status"] == "overlay_only"
    assert result["stage"]["passed"] is True
    assert result["guardrails"][0]["passed"] is False


def test_stage7_growth_monitor_generates_structural_candidates(tmp_path):
    diagnostic_path = tmp_path / "stage7.json"
    analysis_path = tmp_path / "stage7.md"
    promotion_path = tmp_path / "promotion.json"
    diagnostic_path.write_text(
        json.dumps({
            "label": "box_shrink",
            "total": 50,
            "conversion_status": "failed",
            "playouts": {"mate": 19, "max_plies": 31},
            "semantic_alignment_status_counts": {
                "reward_contract_mismatch": 24,
            },
            "shadow_candidate_count": 86,
            "shadow_trigger_counts": {
                "repeated_conversion_failure": 31,
                "high_score_conversion_failure": 31,
                "reward_contract_mismatch": 24,
            },
        }),
        encoding="utf-8",
    )
    analysis_path.write_text(
        "selected_successor_miscalibrated\nrepeated_conversion_failure\nreward_contract_mismatch\n",
        encoding="utf-8",
    )
    promotion_path.write_text(
        json.dumps({"schema_version": "provider_promotion_eval.v1", "promotion_status": "quarantine"}),
        encoding="utf-8",
    )

    candidates = _structural_candidates.generate_stage7_box_shrink_candidates(
        diagnostic_path=diagnostic_path,
        analysis_path=analysis_path,
        promotion_eval_path=promotion_path,
    )

    assert {candidate.candidate_type for candidate in candidates} == {
        "contract_refinement",
        "successor_contract_refinement",
        "quarantine_overlay",
    }
    assert all(candidate.causal_status == "non_causal" for candidate in candidates)
    assert all(candidate.credit == 0.0 for candidate in candidates)
    assert {
        candidate.source_monitor_script for candidate in candidates
    } == {
        "growth.monitor.reward_contract_mismatch",
        "growth.monitor.successor_miscalibration",
        "growth.monitor.stage_overlay_quarantine",
    }


def test_spawn_point_promoted_trial_materializes_formal_triplet_pairs():
    graph = Graph()
    graph.add_node(Node("leg_parent", NodeType.SCRIPT))
    sensor = Node("sensor_1", NodeType.TERMINAL, predicate=lambda _n, _e: (True, True))
    sensor.meta.update({
        "readout_type": "identity",
        "feature_mask_keys": ["feature_0"],
        "readout_params": {},
    })
    graph.add_node(sensor)

    bandit_state = {}
    manager = SpawnPointManager(graph=graph, bandit_state=bandit_state)
    spawn_point = SpawnPoint(spawn_point_id="spawn_leg_parent", leg_id="leg_parent")
    trial = TrialMicroScript(
        trial_id="trial_1",
        spawn_point_id=spawn_point.spawn_point_id,
        sensor_ids=["sensor_1"],
        delta_mean=np.array([1.0], dtype=np.float32),
    )

    materialized = manager._promote_trial_to_graph(spawn_point, trial)

    assert materialized == "trial_1_leg"
    validate_formal_pairs(graph)
    assert _has_edge(graph, "trial_1_precond", "trial_1_act_script", LinkType.POR)
    assert _has_edge(graph, "trial_1_act_script", "trial_1_precond", LinkType.RET)
    assert _has_edge(graph, "trial_1_act_script", "trial_1_postcond", LinkType.POR)
    assert _has_edge(graph, "trial_1_postcond", "trial_1_act_script", LinkType.RET)
    assert _has_edge(graph, "trial_1_precond", "sensor_1", LinkType.SUB)
    assert _has_edge(graph, "sensor_1", "trial_1_precond", LinkType.SUR)
    assert _has_edge(graph, "trial_1_postcond", "trial_1_after_verify", LinkType.SUB)
    assert _has_edge(graph, "trial_1_after_verify", "trial_1_postcond", LinkType.SUR)
    assert graph.nodes["trial_1_after_verify"].meta["triplet_role"] == "after_verify"

    por_edge = _edge(graph, "trial_1_precond", "trial_1_act_script", LinkType.POR)
    ret_edge = _edge(graph, "trial_1_act_script", "trial_1_precond", LinkType.RET)
    assert por_edge.meta["trainable"] is True
    assert ret_edge.meta["structural_fixed"] is True

    plasticity = init_plasticity_state(graph)
    assert "trial_1_precond->trial_1_act_script:POR" in plasticity
    assert "trial_1_act_script->trial_1_precond:RET" not in plasticity

    assert isinstance(bandit_state["leg_parent"]["trial_1_leg"], BanditArmState)


def test_spawn_point_observe_only_profile_does_not_promote_or_prune():
    config = SpawnPointConfig(growth_profile=TripletGrowthProfile.full_game_observe())
    spawn_point = SpawnPoint(
        spawn_point_id="spawn_leg_parent",
        leg_id="leg_parent",
        config=config,
    )
    promote = TrialMicroScript(
        trial_id="promote_trial",
        spawn_point_id=spawn_point.spawn_point_id,
        sensor_ids=["sensor_1"],
        samples=20,
        checkmate_hits=20,
        xp=1.0,
        delta_mean=np.array([1.0], dtype=np.float32),
    )
    prune = TrialMicroScript(
        trial_id="prune_trial",
        spawn_point_id=spawn_point.spawn_point_id,
        sensor_ids=["sensor_1"],
        samples=20,
        non_mate_hits=20,
        xp=0.0,
        last_update_tick=0,
    )
    spawn_point.active_trials[promote.trial_id] = promote
    spawn_point.active_trials[prune.trial_id] = prune

    promoted, pruned = spawn_point.prune_and_promote(tick=100)

    assert promoted == []
    assert pruned == []
    assert set(spawn_point.active_trials) == {"promote_trial", "prune_trial"}


def test_ensure_formal_pairs_adds_missing_ret_for_existing_por():
    graph = Graph()
    graph.add_node(Node("parent", NodeType.SCRIPT))
    graph.add_node(Node("a", NodeType.SCRIPT))
    graph.add_node(Node("b", NodeType.SCRIPT))
    graph.add_node(Node("a_done", NodeType.TERMINAL, predicate=lambda _n, _e: (True, True)))
    graph.add_node(Node("b_done", NodeType.TERMINAL, predicate=lambda _n, _e: (True, True)))
    graph.add_hierarchy_pair("parent", "a")
    graph.add_hierarchy_pair("parent", "b")
    graph.add_hierarchy_pair("a", "a_done")
    graph.add_hierarchy_pair("b", "b_done")
    graph.add_edge("a", "b", LinkType.POR)

    assert ensure_formal_pairs(graph) == 1
    assert _has_edge(graph, "b", "a", LinkType.RET)
    validate_formal_pairs(graph)


def _dummy_sensor():
    return SimpleNamespace(
        id=3,
        stage=0,
        xp=0.8,
        is_mature=True,
        activations=10,
        cycles_alive=5,
        sensor_spec=SimpleNamespace(
            feature_mask=np.array([True, False, False], dtype=bool),
            readout_type="identity",
            readout_params={},
        ),
    )


def _dummy_actuator():
    return SimpleNamespace(
        id=7,
        stage=1,
        xp=0.9,
        activations=12,
        cycles_alive=6,
        actuator_spec=SimpleNamespace(
            sensor_indices=[0],
            goal_delta=np.array([1.0], dtype=np.float32),
            match_mode="l2",
        ),
    )


def _has_edge(graph, src, dst, ltype):
    return any(e.src == src and e.dst == dst and e.ltype == ltype for e in graph.edges)


def _edge(graph, src, dst, ltype):
    for edge in graph.edges:
        if edge.src == src and edge.dst == dst and edge.ltype == ltype:
            return edge
    raise AssertionError(f"missing edge {src}->{dst}:{ltype.name}")
