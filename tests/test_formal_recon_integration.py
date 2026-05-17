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

_structural_candidate_audit = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "audit_stage7_structural_candidates",
        Path(__file__).resolve().parents[1] / "scripts" / "audit_stage7_structural_candidates.py",
    )
)
assert _structural_candidate_audit.__spec__ is not None
assert _structural_candidate_audit.__spec__.loader is not None
_structural_candidate_audit.__spec__.loader.exec_module(_structural_candidate_audit)

_stage7_successor_ownership = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "audit_stage7_successor_ownership",
        Path(__file__).resolve().parents[1] / "scripts" / "audit_stage7_successor_ownership.py",
    )
)
assert _stage7_successor_ownership.__spec__ is not None
assert _stage7_successor_ownership.__spec__.loader is not None
_stage7_successor_ownership.__spec__.loader.exec_module(_stage7_successor_ownership)

_stage7_counterfactual_summary = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "summarize_stage7_counterfactual_evidence",
        Path(__file__).resolve().parents[1] / "scripts" / "summarize_stage7_counterfactual_evidence.py",
    )
)
assert _stage7_counterfactual_summary.__spec__ is not None
assert _stage7_counterfactual_summary.__spec__.loader is not None
_stage7_counterfactual_summary.__spec__.loader.exec_module(_stage7_counterfactual_summary)

_growth_governor_plan = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "plan_structural_candidate_evaluation",
        Path(__file__).resolve().parents[1] / "scripts" / "plan_structural_candidate_evaluation.py",
    )
)
assert _growth_governor_plan.__spec__ is not None
assert _growth_governor_plan.__spec__.loader is not None
_growth_governor_plan.__spec__.loader.exec_module(_growth_governor_plan)

_stage7_post_box_diagnosis = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "diagnose_stage7_post_box_continuation",
        Path(__file__).resolve().parents[1] / "scripts" / "diagnose_stage7_post_box_continuation.py",
    )
)
assert _stage7_post_box_diagnosis.__spec__ is not None
assert _stage7_post_box_diagnosis.__spec__.loader is not None
_stage7_post_box_diagnosis.__spec__.loader.exec_module(_stage7_post_box_diagnosis)

_stage7_post_box_probe = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "probe_stage7_post_box_continuation",
        Path(__file__).resolve().parents[1] / "scripts" / "probe_stage7_post_box_continuation.py",
    )
)
assert _stage7_post_box_probe.__spec__ is not None
assert _stage7_post_box_probe.__spec__.loader is not None
_stage7_post_box_probe.__spec__.loader.exec_module(_stage7_post_box_probe)

_stage7_family_diagnosis = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "diagnose_stage7_post_box_families",
        Path(__file__).resolve().parents[1] / "scripts" / "diagnose_stage7_post_box_families.py",
    )
)
assert _stage7_family_diagnosis.__spec__ is not None
assert _stage7_family_diagnosis.__spec__.loader is not None
_stage7_family_diagnosis.__spec__.loader.exec_module(_stage7_family_diagnosis)

_stage7_family_support = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "propose_stage7_family_support_adapters",
        Path(__file__).resolve().parents[1] / "scripts" / "propose_stage7_family_support_adapters.py",
    )
)
assert _stage7_family_support.__spec__ is not None
assert _stage7_family_support.__spec__.loader is not None
_stage7_family_support.__spec__.loader.exec_module(_stage7_family_support)

_stage7_family_adapter_outcome = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "evaluate_stage7_family_adapter_outcome",
        Path(__file__).resolve().parents[1] / "scripts" / "evaluate_stage7_family_adapter_outcome.py",
    )
)
assert _stage7_family_adapter_outcome.__spec__ is not None
assert _stage7_family_adapter_outcome.__spec__.loader is not None
_stage7_family_adapter_outcome.__spec__.loader.exec_module(_stage7_family_adapter_outcome)

_stage7_move_shape_separation = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "diagnose_stage7_move_shape_separation",
        Path(__file__).resolve().parents[1] / "scripts" / "diagnose_stage7_move_shape_separation.py",
    )
)
assert _stage7_move_shape_separation.__spec__ is not None
assert _stage7_move_shape_separation.__spec__.loader is not None
_stage7_move_shape_separation.__spec__.loader.exec_module(_stage7_move_shape_separation)

_stage7_arbitration = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "diagnose_stage7_arbitration",
        Path(__file__).resolve().parents[1] / "scripts" / "diagnose_stage7_arbitration.py",
    )
)
assert _stage7_arbitration.__spec__ is not None
assert _stage7_arbitration.__spec__.loader is not None
_stage7_arbitration.__spec__.loader.exec_module(_stage7_arbitration)

_stage7_score_calibration = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "plan_stage7_score_calibration",
        Path(__file__).resolve().parents[1] / "scripts" / "plan_stage7_score_calibration.py",
    )
)
assert _stage7_score_calibration.__spec__ is not None
assert _stage7_score_calibration.__spec__.loader is not None
_stage7_score_calibration.__spec__.loader.exec_module(_stage7_score_calibration)

_stage7_score_normalization = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "probe_stage7_score_normalization",
        Path(__file__).resolve().parents[1] / "scripts" / "probe_stage7_score_normalization.py",
    )
)
assert _stage7_score_normalization.__spec__ is not None
assert _stage7_score_normalization.__spec__.loader is not None
_stage7_score_normalization.__spec__.loader.exec_module(_stage7_score_normalization)

_candidate_m3_warmup_plan = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "plan_candidate_local_m3_warmup",
        Path(__file__).resolve().parents[1] / "scripts" / "plan_candidate_local_m3_warmup.py",
    )
)
assert _candidate_m3_warmup_plan.__spec__ is not None
assert _candidate_m3_warmup_plan.__spec__.loader is not None
_candidate_m3_warmup_plan.__spec__.loader.exec_module(_candidate_m3_warmup_plan)

_candidate_m3_warmup_probe = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "probe_candidate_local_m3_warmup",
        Path(__file__).resolve().parents[1] / "scripts" / "probe_candidate_local_m3_warmup.py",
    )
)
assert _candidate_m3_warmup_probe.__spec__ is not None
assert _candidate_m3_warmup_probe.__spec__.loader is not None
_candidate_m3_warmup_probe.__spec__.loader.exec_module(_candidate_m3_warmup_probe)

_role_provider_support = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "propose_role_provider_support_edges",
        Path(__file__).resolve().parents[1] / "scripts" / "propose_role_provider_support_edges.py",
    )
)
assert _role_provider_support.__spec__ is not None
assert _role_provider_support.__spec__.loader is not None
_role_provider_support.__spec__.loader.exec_module(_role_provider_support)

_compile_role_provider_support = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "compile_role_provider_support_sandbox",
        Path(__file__).resolve().parents[1] / "scripts" / "compile_role_provider_support_sandbox.py",
    )
)
assert _compile_role_provider_support.__spec__ is not None
assert _compile_role_provider_support.__spec__.loader is not None
_compile_role_provider_support.__spec__.loader.exec_module(_compile_role_provider_support)

_compile_stage7_king_tempo = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "compile_stage7_king_tempo_sandbox",
        Path(__file__).resolve().parents[1] / "scripts" / "compile_stage7_king_tempo_sandbox.py",
    )
)
assert _compile_stage7_king_tempo.__spec__ is not None
assert _compile_stage7_king_tempo.__spec__.loader is not None
_compile_stage7_king_tempo.__spec__.loader.exec_module(_compile_stage7_king_tempo)

_stage7_king_tempo_audit = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "audit_stage7_king_tempo_move_shapes",
        Path(__file__).resolve().parents[1] / "scripts" / "audit_stage7_king_tempo_move_shapes.py",
    )
)
assert _stage7_king_tempo_audit.__spec__ is not None
assert _stage7_king_tempo_audit.__spec__.loader is not None
_stage7_king_tempo_audit.__spec__.loader.exec_module(_stage7_king_tempo_audit)


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
        assert meta["provider_maturity"] == "foundation_frozen"
        assert meta["plasticity_scope"] == "none"
        assert meta["can_m3_update"] is False
        assert meta["can_m4_consolidate"] is False


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
    assert topology["nodes"]["skill.krk.stage0_basin"]["meta"]["provider_maturity"] == "foundation_frozen"
    assert topology["nodes"]["skill.krk.stage0_basin"]["meta"]["plasticity_scope"] == "none"
    assert topology["nodes"]["leg_2"]["meta"]["provider_version"] == "stage5_validated_v1"
    assert "provider_version" not in topology["nodes"]["terminal.krk.rook_safe"]["meta"]


def test_annotate_provider_metadata_backfills_plasticity_masks_without_relabeling_existing_provider():
    topology = {
        "nodes": {
            "skill.krk.drive_to_edge": {
                "id": "skill.krk.drive_to_edge",
                "type": "SCRIPT",
                "meta": {
                    "skill_id": "krk.drive_to_edge",
                    "curriculum_label": "drive_to_edge",
                    "provider_version": "stage6_overlay_v1",
                    "overlay_provider": True,
                    "frozen_provider": False,
                },
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
        only_missing=True,
    )

    meta = topology["nodes"]["skill.krk.drive_to_edge"]["meta"]
    assert meta["provider_version"] == "stage6_overlay_v1"
    assert meta["overlay_provider"] is True
    assert meta["frozen_provider"] is False
    assert meta["provider_maturity"] == "candidate_high_plasticity"
    assert meta["plasticity_scope"] == "overlay_local"
    assert meta["can_m3_update"] is True
    assert meta["can_m4_consolidate"] is True


def test_overlay_compiler_remaps_conflicting_overlay_actuator_ids(tmp_path):
    base_topology = {"nodes": {}, "edges": [], "meta": {}}
    base_sensor = _dummy_sensor()
    base_actuator = _dummy_actuator()
    base_actuator.curriculum_label = "box_shrink"
    create_root_node(base_topology)
    create_hub_node(base_topology)
    create_leg_micro_script(base_topology, base_actuator, [base_sensor])
    base_path = tmp_path / "base_topology.json"
    base_path.write_text(json.dumps(base_topology), encoding="utf-8")

    overlay_sensor = _dummy_sensor()
    overlay_actuator = _dummy_actuator()
    overlay_actuator.curriculum_label = "opposition_tempo"
    overlay_learner = SimpleNamespace(
        sensors=[overlay_sensor],
        actuators=[overlay_actuator],
        feature_set="krk_rich_v1",
        feature_names=("x", "y", "z"),
    )
    overlay_path = tmp_path / "overlay.pkl"
    import pickle

    with overlay_path.open("wb") as fh:
        pickle.dump(overlay_learner, fh)

    output_path = tmp_path / "composed.json"
    topology = _baseline_to_recon.compile_overlay_topology(
        base_topology_path=base_path,
        overlay_learner_path=overlay_path,
        output_path=output_path,
        overlay_label="opposition_tempo",
        base_provider_version="stage7_scoped_validated_v1",
        overlay_provider_version="stage8_opposition_overlay_v1",
    )

    remap = topology["meta"]["provider_preservation"]["overlay_actuator_id_remap"]
    assert remap == [{"source_actuator_id": 7, "overlay_actuator_id": 8}]
    assert "actuator_7" in topology["nodes"]
    assert "actuator_8" in topology["nodes"]
    assert topology["nodes"]["actuator_7"]["meta"]["curriculum_label"] == "box_shrink"
    assert topology["nodes"]["actuator_8"]["meta"]["curriculum_label"] == "opposition_tempo"
    assert topology["nodes"]["actuator_8"]["meta"]["source_actuator_id"] == 7


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


def test_provider_promotion_eval_keeps_overlay_only_when_control_guardrail_has_debt(tmp_path):
    stage_path = tmp_path / "stage.json"
    guardrail_path = tmp_path / "guardrail.json"
    control_path = tmp_path / "control.json"
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
    weak_guardrail = {
        "total": 50,
        "improved": 50,
        "worsened": 0,
        "playouts": {"mate": 19, "max_plies": 31},
        "shadow_candidates": [{}] * 10,
    }
    guardrail_path.write_text(json.dumps(weak_guardrail), encoding="utf-8")
    control_path.write_text(json.dumps(weak_guardrail), encoding="utf-8")

    result = _provider_promotion.evaluate_promotion(
        stage_artifact=stage_path,
        guardrail_artifacts=[guardrail_path],
        guardrail_control_artifacts=[control_path],
        min_improved_rate=0.70,
        max_worsened_rate=0.20,
        min_mate_rate=0.65,
        max_max_plies_rate=0.25,
        max_shadow_candidates=100,
    )

    assert result["promotion_status"] == "overlay_only"
    assert result["failures"] == []
    assert result["guardrail_control_debt"][0]["path"] == str(control_path)


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


def test_provider_promotion_eval_can_use_guardrail_controls(tmp_path):
    stage_path = tmp_path / "stage.json"
    stage_baseline_path = tmp_path / "stage_baseline.json"
    guardrail_path = tmp_path / "guardrail.json"
    guardrail_control_path = tmp_path / "guardrail_control.json"
    stage_path.write_text(
        json.dumps({"total": 10, "improved": 10, "worsened": 0, "playouts": {"mate": 8, "max_plies": 2}, "shadow_candidates": []}),
        encoding="utf-8",
    )
    stage_baseline_path.write_text(
        json.dumps({"total": 10, "improved": 10, "worsened": 0, "playouts": {"max_plies": 10}, "shadow_candidates": [1, 2]}),
        encoding="utf-8",
    )
    guardrail_payload = {
        "total": 10,
        "improved": 10,
        "worsened": 0,
        "playouts": {"mate": 8, "max_plies": 2},
        "shadow_candidates": [1],
    }
    guardrail_path.write_text(json.dumps(guardrail_payload), encoding="utf-8")
    guardrail_control_path.write_text(json.dumps(guardrail_payload), encoding="utf-8")

    result = _provider_promotion.evaluate_promotion(
        stage_artifact=stage_path,
        stage_baseline_artifact=stage_baseline_path,
        guardrail_artifacts=[guardrail_path],
        guardrail_control_artifacts=[guardrail_control_path],
        min_improved_rate=0.70,
        max_worsened_rate=0.20,
        min_mate_rate=0.65,
        max_max_plies_rate=0.25,
        max_shadow_candidates=1,
        min_target_mate_delta=0.10,
    )

    assert result["promotion_status"] == "promoted"
    assert result["target_improved_vs_baseline"] is True
    assert result["target_delta_vs_baseline"]["mate_rate_delta"] == 0.8
    assert result["guardrails"][0]["passed"] is True
    assert result["guardrail_deltas_vs_control"][0]["regressed_vs_control"] is False


def test_provider_promotion_eval_blocks_guardrail_delta_regression(tmp_path):
    stage_path = tmp_path / "stage.json"
    stage_baseline_path = tmp_path / "stage_baseline.json"
    guardrail_path = tmp_path / "guardrail.json"
    guardrail_control_path = tmp_path / "guardrail_control.json"
    stage_path.write_text(
        json.dumps({"total": 10, "improved": 10, "worsened": 0, "playouts": {"mate": 8, "max_plies": 2}, "shadow_candidates": []}),
        encoding="utf-8",
    )
    stage_baseline_path.write_text(
        json.dumps({"total": 10, "improved": 10, "worsened": 0, "playouts": {"max_plies": 10}, "shadow_candidates": []}),
        encoding="utf-8",
    )
    guardrail_path.write_text(
        json.dumps({"total": 10, "improved": 10, "worsened": 0, "playouts": {"mate": 7, "max_plies": 3}, "shadow_candidates": [1]}),
        encoding="utf-8",
    )
    guardrail_control_path.write_text(
        json.dumps({"total": 10, "improved": 10, "worsened": 0, "playouts": {"mate": 10}, "shadow_candidates": []}),
        encoding="utf-8",
    )

    result = _provider_promotion.evaluate_promotion(
        stage_artifact=stage_path,
        stage_baseline_artifact=stage_baseline_path,
        guardrail_artifacts=[guardrail_path],
        guardrail_control_artifacts=[guardrail_control_path],
        min_improved_rate=0.70,
        max_worsened_rate=0.20,
        min_mate_rate=0.65,
        max_max_plies_rate=0.35,
        max_shadow_candidates=1,
        min_target_mate_delta=0.10,
        max_guardrail_mate_regression=0.02,
        max_guardrail_max_plies_regression=0.02,
        max_guardrail_shadow_regression=0,
    )

    assert result["promotion_status"] == "quarantine"
    assert result["guardrail_deltas_vs_control"][0]["regressed_vs_control"] is True
    assert result["failures"][0]["kind"] == "guardrail_delta"


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
    assert all(candidate.governor_metadata["schema_version"] == "growth_governor_snapshot.v0" for candidate in candidates)
    assert all(candidate.topology_weight_diagnosis["schema_version"] == "topology_weight_diagnosis.v0" for candidate in candidates)
    assert {
        candidate.governor_status for candidate in candidates
    } == {"growth_allowed", "growth_blocked_by_guardrail"}
    assert {
        candidate.source_monitor_script for candidate in candidates
    } == {
        "growth.monitor.reward_contract_mismatch",
        "growth.monitor.successor_miscalibration",
        "growth.monitor.stage_overlay_quarantine",
    }


def test_stage7_structural_candidate_audit_remains_non_causal(tmp_path):
    candidates_path = tmp_path / "candidates.json"
    diagnostic_path = tmp_path / "diagnostic.json"
    promotion_path = tmp_path / "promotion.json"
    candidates_path.write_text(
        json.dumps({
            "schema_version": "structural_candidate_set.v1",
            "source_stage": "stage7_box_shrink",
            "candidate_count": 3,
            "candidates": [
                {
                    "schema_version": "structural_candidate.v1",
                    "candidate_id": "cand.krk.box_shrink.reward_contract_refinement.v1",
                    "candidate_type": "contract_refinement",
                    "source_monitor_script": "growth.monitor.reward_contract_mismatch",
                    "source_terms": ["reward_confirmed", "visible_contract_not_confirmed"],
                    "trigger_failure_classes": ["reward_contract_mismatch"],
                    "target_skill": "krk.box_shrink",
                    "parent_skill": "krk.drive_to_edge",
                    "proposed_change": {
                        "kind": "visible_contract_audit",
                        "suggested_terms": [
                            "box_area_decreased_after_own_move",
                            "box_area_not_increased_after_reply",
                            "fence_or_cut_preserved",
                            "rook_safe_after_reply",
                            "enemy_king_mobility_reduced",
                        ],
                    },
                    "evidence_artifacts": [],
                    "promotion_status": "proposed",
                    "causal_status": "non_causal",
                    "credit": 0.0,
                },
                {
                    "schema_version": "structural_candidate.v1",
                    "candidate_id": "cand.krk.box_shrink.handoff_role_refinement.v1",
                    "candidate_type": "successor_contract_refinement",
                    "source_monitor_script": "growth.monitor.successor_miscalibration",
                    "source_terms": ["selected_successor_miscalibrated"],
                    "trigger_failure_classes": ["selected_successor_miscalibrated"],
                    "target_skill": "krk.box_shrink",
                    "parent_skill": "krk.drive_to_edge",
                    "proposed_change": {"kind": "handoff_role_audit"},
                    "evidence_artifacts": [],
                    "promotion_status": "proposed",
                    "causal_status": "non_causal",
                    "credit": 0.0,
                },
                {
                    "schema_version": "structural_candidate.v1",
                    "candidate_id": "cand.krk.box_shrink.overlay_quarantine_confirmed.v1",
                    "candidate_type": "quarantine_overlay",
                    "source_monitor_script": "growth.monitor.stage_overlay_quarantine",
                    "source_terms": ["target_stage_conversion_failure"],
                    "trigger_failure_classes": ["stage_overlay_quarantine"],
                    "target_skill": "krk.box_shrink",
                    "parent_skill": "krk.drive_to_edge",
                    "proposed_change": {"kind": "promotion_gate_record"},
                    "evidence_artifacts": [],
                    "promotion_status": "quarantined",
                    "causal_status": "non_causal",
                    "credit": 0.0,
                },
            ],
        }),
        encoding="utf-8",
    )
    diagnostic_path.write_text(
        json.dumps({
            "playouts": {"mate": 0, "max_plies": 1},
            "shadow_candidate_count": 2,
            "handoff_packets": [
                {
                    "phase": "post_opponent_reply",
                    "evidence_terms": {
                        "fen": "8/8/8/8/R7/8/2k1K3/8 w - - 0 1",
                        "move": "a4h4",
                        "black_reply": "c2c3",
                        "post_reply_fen": "8/8/8/8/7R/2k5/4K3/8 w - - 2 2",
                        "playout_result": "max_plies",
                        "reward_confirmed": True,
                        "reward_contract_mismatch": True,
                        "successor_selected_skill": "krk.stage0_basin",
                        "provider_selected_without_role_license": True,
                        "failure_classes": ["selected_successor_miscalibrated"],
                        "box_area_after_own_move": 21,
                        "box_area_after_reply": 21,
                        "box_area_delta_after_reply": 0,
                        "fence_survived_reply": False,
                        "rook_safe_after_reply": True,
                    },
                }
            ],
        }),
        encoding="utf-8",
    )
    promotion_path.write_text(
        json.dumps({
            "schema_version": "provider_promotion_eval.v1",
            "promotion_status": "quarantine",
            "failure_reasons": ["target shadow candidates exceed threshold"],
        }),
        encoding="utf-8",
    )

    audit = _structural_candidate_audit.audit_stage7_candidates(
        candidates_path=candidates_path,
        diagnostic_path=diagnostic_path,
        promotion_eval_path=promotion_path,
    )

    assert audit["schema_version"] == "structural_candidate_audit.v1"
    assert audit["causal_status"] == "non_causal"
    statuses = {item["candidate_id"]: item["audit_status"] for item in audit["audits"]}
    assert statuses["cand.krk.box_shrink.reward_contract_refinement.v1"] == "needs_more_terms"
    assert statuses["cand.krk.box_shrink.handoff_role_refinement.v1"] == "handoff_role_audit_required"
    assert statuses["cand.krk.box_shrink.overlay_quarantine_confirmed.v1"] == "quarantine_confirmed"
    reward_audit = next(
        item for item in audit["audits"]
        if item["candidate_id"] == "cand.krk.box_shrink.reward_contract_refinement.v1"
    )
    assert reward_audit["suggested_term_counts"]["box_area_not_increased_after_reply"]["true"] == 1
    assert reward_audit["representative_mismatch_fens"][0]["fen"].startswith("8/8/8/8/R7")


def test_stage7_successor_ownership_audit_is_candidate_driven(tmp_path):
    candidate_audit_path = tmp_path / "candidate_audit.json"
    diagnostic_path = tmp_path / "diagnostic.json"
    candidate_audit_path.write_text(
        json.dumps({
            "schema_version": "structural_candidate_audit.v1",
            "causal_status": "non_causal",
            "audits": [
                {
                    "candidate_id": "cand.krk.box_shrink.handoff_role_refinement.v1",
                    "audit_status": "handoff_role_audit_required",
                    "candidate_update": {"from": "proposed", "to": "sandbox_ready"},
                }
            ],
        }),
        encoding="utf-8",
    )
    diagnostic_path.write_text(
        json.dumps({
            "handoff_packets": [
                {
                    "phase": "post_opponent_reply",
                    "evidence_terms": {
                        "fen": "8/8/8/8/R7/8/2k1K3/8 w - - 0 1",
                        "move": "a4h4",
                        "post_reply_fen": "8/8/8/8/7R/2k5/4K3/8 w - - 2 2",
                        "successor_selected_skill": "krk.stage0_basin",
                        "playout_result": "max_plies",
                        "rook_safe_after_reply": True,
                    },
                },
                {
                    "phase": "post_opponent_reply",
                    "evidence_terms": {
                        "fen": "8/8/8/8/8/5K2/5R2/6k1 w - - 0 1",
                        "move": "f3g3",
                        "post_reply_fen": "8/8/8/8/8/6K1/5R2/7k w - - 2 2",
                        "successor_selected_skill": "krk.edge_trap_close",
                        "playout_result": "mate",
                        "rook_safe_after_reply": True,
                    },
                },
            ],
        }),
        encoding="utf-8",
    )

    audit = _stage7_successor_ownership.audit_successor_ownership(
        candidate_audit_path=candidate_audit_path,
        diagnostic_path=diagnostic_path,
    )

    assert audit["schema_version"] == "stage7_successor_ownership_audit.v1"
    assert audit["causal_status"] == "non_causal"
    assert audit["source_candidate_ready"] is True
    assert audit["successor_outcome_counts"]["krk.stage0_basin:max_plies"] == 1
    assert audit["successor_outcome_counts"]["krk.edge_trap_close:mate"] == 1
    role_statuses = {role["role_id"]: role["audit_status"] for role in audit["role_audits"]}
    assert role_statuses["krk.box_shrink_to_edge_trap_handoff"] == "sandbox_candidate"
    assert role_statuses["krk.box_shrink_post_reply_continuation"] == "needs_role_split_or_successor_sweep"


def test_stage7_counterfactual_summary_updates_candidates_without_causality(tmp_path):
    successor_audit_path = tmp_path / "successor_audit.json"
    sweep_path = tmp_path / "sweep.json"
    successor_audit_path.write_text(
        json.dumps({
            "schema_version": "stage7_successor_ownership_audit.v1",
            "causal_status": "non_causal",
            "source_candidate_id": "cand.krk.box_shrink.handoff_role_refinement.v1",
        }),
        encoding="utf-8",
    )
    sweep_path.write_text(
        json.dumps({
            "schema_version": "krk_counterfactual_successor_sweep.v1",
            "counterfactual_successor_sweeps": [
                {
                    "state_signature": "state.1",
                    "actual_selected_successor": "krk.stage0_basin",
                    "actual_result": "max_plies",
                    "counterfactual_results": {
                        "krk.drive_to_edge": {
                            "result": "mate",
                            "plies": 7,
                            "first_move": "e2e3",
                            "confidence": 0.1,
                            "forced_successor_available": True,
                        },
                        "krk.stage0_basin": {
                            "result": "max_plies",
                            "plies": 8,
                            "first_move": "e2d1",
                            "confidence": 13.0,
                            "forced_successor_available": True,
                        },
                    },
                }
            ],
        }),
        encoding="utf-8",
    )

    summary = _stage7_counterfactual_summary.summarize_counterfactual_evidence(
        successor_audit_path=successor_audit_path,
        sweep_path=sweep_path,
    )

    assert summary["schema_version"] == "stage7_counterfactual_candidate_update.v1"
    assert summary["causal_status"] == "non_causal"
    assert summary["best_mating_successor_counts"]["krk.drive_to_edge"] == 1
    updates = {item["candidate_role"]: item["status"] for item in summary["candidate_updates"]}
    assert updates["krk.box_shrink_to_drive_repair"] == "counterfactual_supported"
    assert updates["krk.stage0_basin_after_box_shrink"] == "negative_counterfactual_evidence"


def test_growth_governor_plans_bounded_weight_probe_before_new_topology(tmp_path):
    candidates_path = tmp_path / "candidates.json"
    counterfactual_path = tmp_path / "counterfactual_update.json"
    sandbox_smoke_path = tmp_path / "sandbox_smoke.json"

    candidates_path.write_text(
        json.dumps({
            "schema_version": "structural_candidate_set.v1",
            "source_stage": "stage7_box_shrink",
            "candidate_count": 3,
            "candidates": [
                {
                    "candidate_id": "cand.krk.box_shrink.reward_contract_refinement.v1",
                    "governor_status": "growth_allowed",
                },
                {
                    "candidate_id": "cand.krk.box_shrink.handoff_role_refinement.v1",
                    "governor_status": "growth_allowed",
                },
                {
                    "candidate_id": "cand.krk.box_shrink.overlay_quarantine_confirmed.v1",
                    "governor_status": "growth_blocked_by_guardrail",
                },
            ],
        }),
        encoding="utf-8",
    )
    counterfactual_path.write_text(
        json.dumps({
            "schema_version": "stage7_counterfactual_candidate_update.v1",
            "causal_status": "non_causal",
            "candidate_updates": [
                {
                    "candidate_role": "krk.box_shrink_to_drive_repair",
                    "status": "counterfactual_supported",
                    "support": 1,
                    "topology_weight_diagnosis": {
                        "diagnostic_labels": ["topology_present_untrained", "trainable_candidate"],
                    },
                },
                {
                    "candidate_role": "krk.box_shrink_post_reply_continuation",
                    "status": "counterfactual_partial",
                    "support": 2,
                    "topology_weight_diagnosis": {
                        "diagnostic_labels": ["provider_capacity_missing"],
                    },
                },
                {
                    "candidate_role": "krk.stage0_basin_after_box_shrink",
                    "status": "negative_counterfactual_evidence",
                    "support": 4,
                    "topology_weight_diagnosis": {
                        "diagnostic_labels": ["parameter_miscalibrated"],
                    },
                },
            ],
        }),
        encoding="utf-8",
    )
    sandbox_smoke_path.write_text(
        json.dumps({
            "total": 10,
            "playouts": {"mate": 3, "max_plies": 7},
            "shadow_candidate_count": 19,
            "handoff_packets": [
                {
                    "phase": "post_opponent_reply",
                    "evidence_terms": {
                        "successor_selected_skill": "krk.stage0_basin",
                        "visible_successor_provider_licenses": {
                            "krk.drive_to_edge": {
                                "krk.box_shrink_to_drive_repair": {
                                    "contract_met": True,
                                },
                            },
                        },
                    },
                }
            ],
        }),
        encoding="utf-8",
    )

    plan = _growth_governor_plan.plan_candidate_evaluation(
        candidates_path=candidates_path,
        counterfactual_update_path=counterfactual_path,
        sandbox_smoke_path=sandbox_smoke_path,
    )

    assert plan["schema_version"] == "growth_governor_evaluation_plan.v1"
    assert plan["causal_status"] == "non_causal"
    assert plan["recommended_next_action"] == "bounded_m3_warmup_for_box_shrink_to_drive_repair"
    assert "do_not_promote_stage7" in plan["hard_blocks"]

    role_plans = {item["candidate_role"]: item for item in plan["role_plans"]}
    drive_plan = role_plans["krk.box_shrink_to_drive_repair"]
    assert drive_plan["evaluation_phase"] == "phase_3_bounded_plasticity_warmup"
    assert drive_plan["governor_decision"] == "needs_more_weight_training"
    assert drive_plan["next_action"] == "run_candidate_local_m3_warmup_probe"
    assert drive_plan["sandbox_smoke"]["role_contract_met_count"] == 1
    assert drive_plan["sandbox_smoke"]["role_selected_count"] == 0
    assert "candidate_local_m3_only" in drive_plan["required_probes"]

    continuation_plan = role_plans["krk.box_shrink_post_reply_continuation"]
    assert continuation_plan["evaluation_phase"] == "phase_2_forced_oracle_probe"
    assert continuation_plan["governor_decision"] == "growth_blocked_by_cooldown"

    stage0_plan = role_plans["krk.stage0_basin_after_box_shrink"]
    assert stage0_plan["governor_decision"] == "growth_blocked_by_guardrail"
    assert stage0_plan["next_action"] == "do_not_sandbox_as_default_continuation"


def test_candidate_local_m3_warmup_plan_whitelists_only_overlay_provider_edges(tmp_path):
    topology_path = tmp_path / "topology.json"
    growth_plan_path = tmp_path / "growth_plan.json"
    topology_path.write_text(
        json.dumps({
            "nodes": {
                "skill.krk.stage0_basin": {
                    "type": "SCRIPT",
                    "meta": {
                        "skill_id": "krk.stage0_basin",
                        "frozen_provider": True,
                        "provider_version": "stage5_validated_v1",
                        "provider_maturity": "foundation_frozen",
                        "can_m3_update": False,
                    },
                },
                "leg_1": {
                    "type": "SCRIPT",
                    "meta": {
                        "skill_id": "krk.stage0_basin",
                        "frozen_provider": True,
                        "provider_version": "stage5_validated_v1",
                        "provider_maturity": "foundation_frozen",
                        "can_m3_update": False,
                    },
                },
                "skill.krk.drive_to_edge": {
                    "type": "SCRIPT",
                    "meta": {
                        "skill_id": "krk.drive_to_edge",
                        "overlay_provider": True,
                        "provider_version": "stage6_overlay_v1",
                        "provider_maturity": "candidate_high_plasticity",
                        "plasticity_scope": "overlay_local",
                        "can_m3_update": True,
                    },
                },
                "leg_34": {
                    "type": "SCRIPT",
                    "meta": {
                        "skill_id": "krk.drive_to_edge",
                        "overlay_provider": True,
                        "provider_version": "stage6_overlay_v1",
                        "provider_maturity": "candidate_high_plasticity",
                        "plasticity_scope": "overlay_local",
                        "can_m3_update": True,
                    },
                },
                "precond_34": {
                    "type": "SCRIPT",
                    "meta": {
                        "skill_id": "krk.drive_to_edge",
                        "overlay_provider": True,
                        "can_m3_update": True,
                    },
                },
                "act_script_34": {
                    "type": "SCRIPT",
                    "meta": {
                        "skill_id": "krk.drive_to_edge",
                        "overlay_provider": True,
                        "can_m3_update": True,
                    },
                },
                "script.krk.successor.box_shrink_to_drive_repair_affordance": {
                    "type": "SCRIPT",
                    "meta": {
                        "role_id": "krk.box_shrink_to_drive_repair",
                        "provider_skill_ids": ["krk.drive_to_edge"],
                    },
                },
                "terminal.krk.successor.box_shrink_to_drive_repair_marker": {
                    "type": "TERMINAL",
                    "meta": {
                        "role_id": "krk.box_shrink_to_drive_repair",
                        "provider_skill_ids": ["krk.drive_to_edge"],
                    },
                },
                "krk_hub": {"type": "SCRIPT", "meta": {}},
            },
            "edges": [
                {"src": "skill.krk.stage0_basin", "dst": "leg_1", "type": "SUB", "weight": 1.0},
                {"src": "skill.krk.drive_to_edge", "dst": "leg_34", "type": "SUB", "weight": 1.0},
                {"src": "leg_34", "dst": "precond_34", "type": "SUB", "weight": 1.0},
                {"src": "precond_34", "dst": "act_script_34", "type": "POR", "weight": 1.0},
                {
                    "src": "script.krk.successor.box_shrink_to_drive_repair_affordance",
                    "dst": "terminal.krk.successor.box_shrink_to_drive_repair_marker",
                    "type": "SUB",
                    "weight": 1.0,
                },
                {"src": "krk_hub", "dst": "skill.krk.drive_to_edge", "type": "SUB", "weight": 1.0},
            ],
        }),
        encoding="utf-8",
    )
    growth_plan_path.write_text(
        json.dumps({
            "schema_version": "growth_governor_evaluation_plan.v1",
            "causal_status": "non_causal",
            "hard_blocks": ["do_not_promote_stage7"],
            "role_plans": [
                {
                    "candidate_role": "krk.box_shrink_to_drive_repair",
                    "governor_decision": "needs_more_weight_training",
                    "evaluation_phase": "phase_3_bounded_plasticity_warmup",
                    "guardrails": ["stage7_box_shrink_target", "stage5_fence"],
                }
            ],
        }),
        encoding="utf-8",
    )

    plan = _candidate_m3_warmup_plan.plan_candidate_local_m3_warmup(
        topology_path=topology_path,
        growth_plan_path=growth_plan_path,
    )

    assert plan["schema_version"] == "candidate_local_m3_warmup_plan.v1"
    assert plan["causal_status"] == "non_causal"
    assert plan["target_providers"] == ["krk.drive_to_edge"]
    assert plan["growth_governor_decision"] == "needs_more_weight_training"
    assert plan["training_limits"]["m4_consolidation_enabled"] is False
    assert plan["training_limits"]["topology_mutation_enabled"] is False
    assert plan["protected_provider_versions"] == ["stage5_validated_v1"]

    whitelisted = {(edge["src"], edge["dst"], edge["type"]) for edge in plan["eligible_edge_whitelist"]}
    assert ("skill.krk.drive_to_edge", "leg_34", "SUB") in whitelisted
    assert ("leg_34", "precond_34", "SUB") in whitelisted
    assert ("precond_34", "act_script_34", "POR") in whitelisted
    assert ("skill.krk.stage0_basin", "leg_1", "SUB") not in whitelisted
    assert ("krk_hub", "skill.krk.drive_to_edge", "SUB") not in whitelisted

    role_support = {
        (edge["src"], edge["dst"], edge["type"], edge["trainable"])
        for edge in plan["observe_only_role_support_edges"]
    }
    assert (
        "script.krk.successor.box_shrink_to_drive_repair_affordance",
        "terminal.krk.successor.box_shrink_to_drive_repair_marker",
        "SUB",
        False,
    ) in role_support


def test_candidate_local_m3_probe_blocks_when_role_fires_but_provider_never_selected(tmp_path):
    warmup_plan_path = tmp_path / "warmup_plan.json"
    diagnostic_path = tmp_path / "diagnostic.json"
    warmup_plan_path.write_text(
        json.dumps({
            "schema_version": "candidate_local_m3_warmup_plan.v1",
            "target_role": "krk.box_shrink_to_drive_repair",
            "target_providers": ["krk.drive_to_edge"],
            "eligible_edge_whitelist": [
                {"src": "skill.krk.drive_to_edge", "dst": "leg_34", "type": "SUB", "reason": "candidate_provider_leg_selection"},
                {"src": "precond_34", "dst": "act_script_34", "type": "POR", "reason": "candidate_provider_triplet_temporal"},
            ],
            "training_limits": {
                "eta_eff": 0.02,
                "max_delta_episode": 0.25,
                "m4_consolidation_enabled": False,
                "topology_mutation_enabled": False,
                "protected_provider_mutation_enabled": False,
            },
            "hard_blocks": ["do_not_promote_stage7"],
        }),
        encoding="utf-8",
    )
    diagnostic_path.write_text(
        json.dumps({
            "handoff_packets": [
                {
                    "packet_id": "packet.1",
                    "phase": "post_opponent_reply",
                    "evidence_terms": {
                        "fen": "8/8/8/8/R7/8/2k1K3/8 w - - 0 1",
                        "successor_selected_skill": "krk.stage0_basin",
                        "playout_result": "max_plies",
                        "visible_successor_provider_licenses": {
                            "krk.drive_to_edge": {
                                "krk.box_shrink_to_drive_repair": {
                                    "contract_met": True,
                                    "source_terms": ["box_shrink_drive_repair_available"],
                                },
                            },
                        },
                    },
                }
            ],
        }),
        encoding="utf-8",
    )

    probe = _candidate_m3_warmup_probe.probe_candidate_local_m3_warmup(
        warmup_plan_path=warmup_plan_path,
        diagnostic_path=diagnostic_path,
    )

    assert probe["schema_version"] == "candidate_local_m3_warmup_probe.v1"
    assert probe["causal_status"] == "non_causal"
    assert probe["probe_result"] == "blocked_no_candidate_provider_eligibility"
    assert probe["recommended_next_action"] == "compile_visible_role_provider_support_or_owner_eligibility_before_m3"
    assert probe["counts"]["role_contract_met"] == 1
    assert probe["counts"]["role_met_provider_not_selected"] == 1
    assert probe["candidate_edge_eligibility_events"] == 0
    assert probe["edge_delta_preview"] == []
    assert probe["safety"]["m4_consolidation_enabled"] is False
    assert probe["safety"]["topology_mutation_enabled"] is False


def test_candidate_local_m3_probe_previews_bounded_edge_deltas_when_provider_fires(tmp_path):
    warmup_plan_path = tmp_path / "warmup_plan.json"
    diagnostic_path = tmp_path / "diagnostic.json"
    warmup_plan_path.write_text(
        json.dumps({
            "target_role": "krk.box_shrink_to_drive_repair",
            "target_providers": ["krk.drive_to_edge"],
            "eligible_edge_whitelist": [
                {"src": "skill.krk.drive_to_edge", "dst": "leg_34", "type": "SUB", "reason": "candidate_provider_leg_selection"},
            ],
            "training_limits": {"eta_eff": 0.5, "max_delta_episode": 0.25},
        }),
        encoding="utf-8",
    )
    diagnostic_path.write_text(
        json.dumps({
            "handoff_packets": [
                {
                    "phase": "post_opponent_reply",
                    "evidence_terms": {
                        "successor_selected_skill": "krk.drive_to_edge",
                        "playout_result": "mate",
                        "visible_successor_provider_licenses": {
                            "krk.drive_to_edge": {
                                "krk.box_shrink_to_drive_repair": {"contract_met": True},
                            },
                        },
                    },
                }
            ],
        }),
        encoding="utf-8",
    )

    probe = _candidate_m3_warmup_probe.probe_candidate_local_m3_warmup(
        warmup_plan_path=warmup_plan_path,
        diagnostic_path=diagnostic_path,
    )

    assert probe["probe_result"] == "candidate_local_m3_warmup_feasible"
    assert probe["candidate_edge_eligibility_events"] == 1
    assert probe["edge_delta_preview"][0]["preview_delta_sum"] == 0.25


def test_role_provider_support_proposal_remains_non_causal_and_sandbox_only(tmp_path):
    topology_path = tmp_path / "topology.json"
    probe_path = tmp_path / "probe.json"
    topology_path.write_text(
        json.dumps({
            "nodes": {
                "script.krk.successor.box_shrink_to_drive_repair_affordance": {
                    "type": "SCRIPT",
                    "meta": {"role_id": "krk.box_shrink_to_drive_repair"},
                },
                "terminal.krk.successor.box_shrink_to_drive_repair_marker": {
                    "type": "TERMINAL",
                    "meta": {"role_id": "krk.box_shrink_to_drive_repair"},
                },
                "skill.krk.drive_to_edge": {
                    "type": "SCRIPT",
                    "meta": {"skill_id": "krk.drive_to_edge"},
                },
            },
            "edges": [],
        }),
        encoding="utf-8",
    )
    probe_path.write_text(
        json.dumps({
            "probe_result": "blocked_no_candidate_provider_eligibility",
            "target_role": "krk.box_shrink_to_drive_repair",
            "target_provider": "krk.drive_to_edge",
        }),
        encoding="utf-8",
    )

    proposal = _role_provider_support.propose_role_provider_support_edges(
        topology_path=topology_path,
        m3_probe_path=probe_path,
    )

    assert proposal["schema_version"] == "role_provider_support_proposal.v1"
    assert proposal["causal_status"] == "non_causal"
    assert proposal["proposal_status"] == "sandbox_ready"
    assert proposal["proposed_relation_count"] == 1
    assert proposal["unsafe_direct_graph_edges_emitted"] is False
    assert proposal["sandbox_compile_strategy"] == "compile_gated_support_adapter_not_direct_sub_edge"
    edge = proposal["proposed_support_relations"][0]
    assert edge["source_role_script"] == "script.krk.successor.box_shrink_to_drive_repair_affordance"
    assert edge["target_provider_skill"] == "skill.krk.drive_to_edge"
    assert edge["relation_type"] == "visible_role_provider_support"
    assert edge["initial_weight"] == 0.0
    assert edge["causal_status"] == "non_causal_scaffold"
    assert edge["direct_graph_edge_emitted"] is False
    assert edge["requires_support_adapter"] is True
    assert "WAITING" in edge["unsafe_direct_edge"]["reason"]
    assert "do_not_insert_into_default_topology" in proposal["hard_blocks"]


def test_compile_role_provider_support_sandbox_adds_adapter_not_direct_provider_edge(tmp_path):
    topology_path = tmp_path / "topology.json"
    proposal_path = tmp_path / "proposal.json"
    output_path = tmp_path / "sandbox.json"
    topology_path.write_text(
        json.dumps({
            "nodes": {
                "krk_entry": {"type": "SCRIPT", "meta": {}},
                "krk_successor_affordance_hub": {"type": "SCRIPT", "meta": {}},
                "script.krk.successor.box_shrink_to_drive_repair_affordance": {
                    "type": "SCRIPT",
                    "meta": {"role_id": "krk.box_shrink_to_drive_repair"},
                },
                "skill.krk.drive_to_edge": {
                    "type": "SCRIPT",
                    "meta": {"skill_id": "krk.drive_to_edge"},
                },
            },
            "edges": [],
            "meta": {},
        }),
        encoding="utf-8",
    )
    proposal_path.write_text(
        json.dumps({
            "target_role": "krk.box_shrink_to_drive_repair",
            "target_provider": "krk.drive_to_edge",
            "sandbox_compile_strategy": "compile_gated_support_adapter_not_direct_sub_edge",
            "proposed_support_relations": [
                {
                    "source_role_script": "script.krk.successor.box_shrink_to_drive_repair_affordance",
                    "target_provider_skill": "skill.krk.drive_to_edge",
                    "requires_support_adapter": True,
                    "initial_weight": 0.0,
                    "support_required_terms": ["white_king_support_available"],
                }
            ],
        }),
        encoding="utf-8",
    )

    topology = _compile_role_provider_support.compile_support_sandbox(
        topology_path=topology_path,
        proposal_path=proposal_path,
        output_path=output_path,
    )

    meta = topology["meta"]["role_provider_support_sandbox"]
    assert meta["adapter_count"] == 1
    assert meta["enabled_by_default"] is False
    adapter_id = meta["adapters"][0]
    assert topology["nodes"][adapter_id]["factory"].endswith("create_krk_role_provider_support_adapter")
    assert topology["nodes"][adapter_id]["meta"]["support_required_terms"] == [
        "white_king_support_available"
    ]
    direct_edges = [
        edge for edge in topology["edges"]
        if edge["src"] == "script.krk.successor.box_shrink_to_drive_repair_affordance"
        and edge["dst"] == "skill.krk.drive_to_edge"
    ]
    assert direct_edges == []
    support_edges = [
        edge for edge in topology["edges"]
        if edge["src"] == adapter_id and edge.get("edge_kind") == "visible_role_provider_support_weight"
    ]
    assert support_edges
    assert support_edges[0]["weight"] == 0.0
    assert support_edges[0]["trainable"] is True
    assert topology["nodes"]["krk_entry"]["meta"].get("explicit_role_provider_support_enabled") is None


def test_compile_role_provider_support_can_augment_role_provider_ids_in_sandbox(tmp_path):
    topology_path = tmp_path / "topology.json"
    proposal_path = tmp_path / "proposal.json"
    output_path = tmp_path / "sandbox.json"
    role_node = "script.krk.successor.box_shrink_to_drive_repair_affordance"
    topology_path.write_text(
        json.dumps({
            "nodes": {
                "krk_entry": {"type": "SCRIPT", "meta": {}},
                "krk_successor_affordance_hub": {"type": "SCRIPT", "meta": {}},
                role_node: {
                    "type": "SCRIPT",
                    "meta": {
                        "role_id": "krk.box_shrink_to_drive_repair",
                        "provider_skill_ids": ["krk.drive_to_edge"],
                    },
                },
                "skill.krk.fence_established": {
                    "type": "SCRIPT",
                    "meta": {"skill_id": "krk.fence_established"},
                },
            },
            "edges": [],
            "meta": {},
        }),
        encoding="utf-8",
    )
    proposal_path.write_text(
        json.dumps({
            "target_role": "krk.box_shrink_to_drive_repair",
            "target_provider": "krk.fence_established",
            "sandbox_compile_strategy": "compile_gated_support_adapter_not_direct_sub_edge",
            "proposed_support_relations": [
                {
                    "source_role_script": role_node,
                    "target_provider_skill": "skill.krk.fence_established",
                    "requires_support_adapter": True,
                    "initial_weight": 0.05,
                }
            ],
        }),
        encoding="utf-8",
    )

    topology = _compile_role_provider_support.compile_support_sandbox(
        topology_path=topology_path,
        proposal_path=proposal_path,
        output_path=output_path,
        augment_role_provider_ids=True,
    )

    role_meta = topology["nodes"][role_node]["meta"]
    assert role_meta["provider_skill_ids"] == ["krk.drive_to_edge", "krk.fence_established"]
    assert role_meta["provider_augmentation_sources"][0]["causal_status"] == "sandbox_opt_in"
    assert topology["meta"]["role_provider_support_sandbox"]["augment_role_provider_ids"] is True


def test_compile_stage7_king_tempo_sandbox_adds_default_off_visible_terminal(tmp_path):
    topology_path = tmp_path / "topology.json"
    output_path = tmp_path / "king_tempo.json"
    topology_path.write_text(
        json.dumps({
            "nodes": {
                "krk_entry": {"type": "SCRIPT", "meta": {}},
                "krk_hub": {"type": "SCRIPT", "meta": {}},
            },
            "edges": [],
            "meta": {},
        }),
        encoding="utf-8",
    )

    topology = _compile_stage7_king_tempo.compile_stage7_king_tempo_sandbox(
        topology_path=topology_path,
        output_path=output_path,
        score=25.0,
    )

    meta = topology["meta"]["stage7_king_tempo_sandbox"]
    node_id = meta["node_id"]
    assert meta["enabled_by_default"] is False
    assert meta["causal_status"] == "sandbox_opt_in"
    assert topology["nodes"][node_id]["factory"].endswith("create_krk_stage7_king_tempo_terminal")
    assert topology["nodes"][node_id]["meta"]["provider_skill_id"] == "krk.stage0_basin"
    assert topology["nodes"]["krk_entry"]["meta"].get("stage7_king_tempo_enabled") is None
    assert any(edge["src"] == "krk_hub" and edge["dst"] == node_id and edge["type"] == "SUB" for edge in topology["edges"])
    assert any(edge["src"] == node_id and edge["dst"] == "krk_hub" and edge["type"] == "SUR" for edge in topology["edges"])


def test_stage7_king_tempo_move_shape_audit_proposes_non_causal_refinement(tmp_path):
    probe_path = tmp_path / "probe.json"
    diagnostic_path = tmp_path / "diagnostic.json"
    probe_path.write_text(
        json.dumps({
            "source_failure_fen": "6k1/R7/8/8/8/8/5K2/8 w - - 2 2",
            "records": [
                {"move": "f2e2", "converts_to_mate": True},
                {"move": "f2e3", "converts_to_mate": False},
            ],
        }),
        encoding="utf-8",
    )
    diagnostic_path.write_text(
        json.dumps({
            "handoff_packets": [
                {
                    "phase": "post_opponent_reply",
                    "evidence_terms": {
                        "post_reply_fen": "6k1/8/8/8/R7/8/4K3/8 w - - 2 2",
                        "playout_result": "max_plies",
                        "visible_stage7_king_tempo_license": {
                            "move": "e2d2",
                            "direct_request": False,
                        },
                    },
                }
            ],
        }),
        encoding="utf-8",
    )

    audit = _stage7_king_tempo_audit.audit_king_tempo_move_shapes(
        probe_path=probe_path,
        diagnostic_path=diagnostic_path,
    )

    assert audit["schema_version"] == "stage7_king_tempo_move_shape_audit.v1"
    assert audit["causal_status"] == "non_causal"
    assert audit["diagnosis"] == "king_tempo_contract_too_broad"
    update = audit["candidate_update"]
    assert update["causal_status"] == "non_causal"
    assert update["promotion_status"] == "sandboxed"
    assert "compact_box_area_before_move" in update["proposed_change"]["required_terms"]
    assert "box_area_large_before_move" in update["proposed_change"]["veto_terms"]


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


def test_stage7_post_box_continuation_diagnosis_marks_non_causal_quarantine(tmp_path):
    diagnostic = {
        "handoff_packets": [
            {
                "phase": "post_own_move",
                "evidence_terms": {
                    "fen": "8/8/8/8/3k4/8/3K4/R7 w - - 0 1",
                    "move": "a1d1",
                    "reward_confirmed": True,
                },
            },
            {
                "phase": "post_opponent_reply",
                "evidence_terms": {
                    "fen": "8/8/8/8/3k4/8/3K4/R7 w - - 0 1",
                    "black_reply": "d4c4",
                    "post_reply_fen": "8/8/8/8/2k5/8/3K4/3R4 w - - 2 2",
                    "fence_survived_reply": True,
                    "rook_safe_after_reply": True,
                    "successor_selected_skill": "krk.stage0_basin",
                    "failure_classes": ["selected_successor_miscalibrated"],
                    "playout_result": "max_plies",
                },
            },
            {
                "phase": "playout_summary",
                "evidence_terms": {
                    "playout_result": "max_plies",
                    "conversion_status": "failed",
                    "semantic_alignment_status": "reward_visible_fence_aligned_survived",
                    "failure_classes": ["selected_successor_miscalibrated"],
                    "plies": 80,
                },
            },
            {
                "phase": "post_own_move",
                "evidence_terms": {
                    "fen": "8/8/8/8/3k4/8/3K4/R7 w - - 0 1",
                    "move": "a1a8",
                    "reward_confirmed": True,
                },
            },
            {
                "phase": "post_opponent_reply",
                "evidence_terms": {
                    "fen": "8/8/8/8/3k4/8/3K4/R7 w - - 0 1",
                    "black_reply": "d4c4",
                    "post_reply_fen": "R7/8/8/8/2k5/8/3K4/8 w - - 2 2",
                    "fence_survived_reply": False,
                    "rook_safe_after_reply": True,
                    "successor_selected_skill": None,
                    "playout_result": "mate",
                },
            },
            {
                "phase": "playout_summary",
                "evidence_terms": {
                    "playout_result": "mate",
                    "conversion_status": "passed",
                    "semantic_alignment_status": "reward_contract_mismatch",
                    "plies": 12,
                },
            },
        ]
    }
    path = tmp_path / "stage7.json"
    path.write_text(json.dumps(diagnostic), encoding="utf-8")

    payload = _stage7_post_box_diagnosis.diagnose_stage7_post_box_continuation(
        diagnostic_path=path
    )

    assert payload["schema_version"] == "stage7_post_box_continuation_diagnosis.v1"
    assert payload["causal_status"] == "non_causal"
    assert payload["stage7_status"] == "local_valid_composition_quarantined"
    assert payload["conversion_failed_count"] == 1
    assert payload["recommended_next_action"] == "targeted_forced_provider_probe_before_new_topology"
    updates = {item["candidate_id"]: item for item in payload["candidate_updates"]}
    assert updates["cand.krk.box_shrink.handoff_role_refinement.v1"]["status"] == (
        "needs_bounded_forced_provider_probe"
    )
    assert updates["cand.krk.box_shrink.overlay_quarantine_confirmed.v1"]["status"] == (
        "local_valid_composition_quarantined"
    )
    assert "do_not_promote_stage7" in payload["hard_blocks"]


def test_stage7_post_box_probe_summarizes_weight_vs_topology_without_causality():
    records = [
        {
            "state_id": "state.a",
            "first_move_probes": [
                {
                    "provider": "krk.edge_trap_close",
                    "forced_successor_available": True,
                    "legal": True,
                    "move": "a1a8",
                },
                {
                    "provider": "krk.stage0_basin",
                    "forced_successor_available": False,
                    "legal": False,
                    "move": None,
                },
            ],
            "playout_probes": [],
        }
    ]

    summary = _stage7_post_box_probe.summarize_probe(records)

    assert summary["states_with_any_available_provider"] == 1
    assert summary["topology_weight_diagnosis"] == (
        "existing_provider_first_moves_available_playout_pending"
    )
    assert summary["first_move_available_counts"]["krk.edge_trap_close:available"] == 1

    records[0]["playout_probes"] = [
        {
            "provider": "krk.edge_trap_close",
            "horizon": 40,
            "result": "mate",
        }
    ]
    summary = _stage7_post_box_probe.summarize_probe(records)

    assert summary["states_with_any_mating_forced_playout"] == 1
    assert summary["forced_playout_mate_by_provider"]["krk.edge_trap_close"] == 1
    assert summary["topology_weight_diagnosis"] == "topology_present_untrained_or_miscalibrated"


def test_stage7_family_diagnosis_splits_forced_success_and_unresolved(tmp_path):
    diagnosis_path = tmp_path / "diagnosis.json"
    forced_path = tmp_path / "forced_h40.json"
    unresolved_path = tmp_path / "unresolved_h80.json"
    adapter_path = tmp_path / "adapter.json"
    diagnosis_path.write_text(
        json.dumps(
            {
                "unique_failed_post_reply_states": [
                    {
                        "post_reply_fen": "8/8/8/8/4R3/2k5/4K3/8 w - - 2 2",
                        "selected_successor": "krk.stage0_basin",
                        "selected_move": "e4e8",
                        "conversion_result": "max_plies",
                        "failure_classes": ["selected_successor_miscalibrated"],
                    },
                    {
                        "post_reply_fen": "8/8/8/8/4K3/4R3/3k4/8 w - - 2 2",
                        "selected_successor": "krk.stage0_basin",
                        "selected_move": "e3a3",
                        "conversion_result": "max_plies",
                        "failure_classes": ["selected_successor_miscalibrated"],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    forced_path.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "state_id": "state.ff",
                        "post_reply_fen": "8/8/8/8/4R3/2k5/4K3/8 w - - 2 2",
                        "first_move_probes": [
                            {
                                "provider": "krk.drive_to_edge",
                                "move": "e4h4",
                                "forced_successor_available": True,
                                "legal": True,
                                "move_shape_audit": {
                                    "current_terms": ["box_shrink_drive_repair_available"],
                                    "move_shape_terms": ["candidate_is_rook_transfer"],
                                    "post_move_terms": ["rook_safe_after_move"],
                                },
                            }
                        ],
                        "playout_probes": [
                            {
                                "provider": "krk.drive_to_edge",
                                "result": "mate",
                                "plies": 7,
                                "first_move": "e4h4",
                                "horizon": 40,
                            }
                        ],
                    },
                    {
                        "state_id": "state.0a",
                        "post_reply_fen": "8/8/8/8/4K3/4R3/3k4/8 w - - 2 2",
                        "first_move_probes": [
                            {
                                "provider": "krk.drive_to_edge",
                                "move": "e3a3",
                                "forced_successor_available": True,
                                "legal": True,
                                "move_shape_audit": {
                                    "current_terms": ["enemy_king_near_edge"],
                                    "move_shape_terms": ["candidate_is_rook_transfer"],
                                    "post_move_terms": ["rook_safe_after_move"],
                                },
                            }
                        ],
                        "playout_probes": [
                            {
                                "provider": "krk.drive_to_edge",
                                "result": "max_plies",
                                "plies": 40,
                                "first_move": "e3a3",
                                "horizon": 40,
                            }
                        ],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    unresolved_path.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "state_id": "state.0a",
                        "post_reply_fen": "8/8/8/8/4K3/4R3/3k4/8 w - - 2 2",
                        "playout_probes": [
                            {
                                "provider": "krk.drive_to_edge",
                                "result": "max_plies",
                                "plies": 80,
                                "first_move": "e3a3",
                                "horizon": 80,
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    adapter_path.write_text(
        json.dumps(
            {
                "adapter_fire_count": 2,
                "adapter_supported_provider_by_outcome": {"krk.drive_to_edge:max_plies": 2},
            }
        ),
        encoding="utf-8",
    )

    payload = _stage7_family_diagnosis.diagnose_families(
        diagnosis_path=diagnosis_path,
        forced_h40_path=forced_path,
        unresolved_h80_path=unresolved_path,
        adapter_smoke_path=adapter_path,
    )

    assert payload["schema_version"] == "stage7_post_box_family_diagnosis.v1"
    assert payload["causal_status"] == "non_causal"
    assert payload["family_diagnosis_counts"] == {
        "existing_provider_can_convert_if_family_role_selects_it": 1,
        "unresolved_by_existing_forced_providers_at_h80": 1,
    }
    statuses = {item["candidate_id"]: item["status"] for item in payload["candidate_updates"]}
    assert statuses["cand.krk.box_shrink.family_ff.drive_to_edge_adapter.v1"] == (
        "sandbox_ready_if_terms_separate"
    )
    assert statuses["cand.krk.box_shrink.family_0a.unresolved_continuation.v1"] == (
        "needs_legal_first_or_longer_horizon_sweep"
    )
    assert payload["overbroad_adapter_status"]["status"] == "overbroad_adapter_candidate"


def test_stage7_family_support_proposals_require_term_separation(tmp_path):
    family_path = tmp_path / "family.json"
    family_path.write_text(
        json.dumps(
            {
                "families": [
                    {
                        "family_id": "stage7.post_box.family_ff",
                        "state_id": "state.ff",
                        "best_forced_provider": "krk.drive_to_edge",
                        "forced_provider_results": {
                            "krk.drive_to_edge": {
                                "result": "mate",
                                "first_move_probe": {
                                    "current_terms": ["box", "support"],
                                },
                            }
                        },
                    },
                    {
                        "family_id": "stage7.post_box.family_0a",
                        "state_id": "state.0a",
                        "best_forced_provider": None,
                        "forced_provider_results": {
                            "krk.drive_to_edge": {
                                "result": "max_plies",
                                "first_move_probe": {
                                    "current_terms": ["box"],
                                },
                            }
                        },
                    },
                ],
                "provider_term_splits": {
                    "krk.drive_to_edge": {
                        "current_terms": {
                            "success_common_minus_failure_common": ["support"],
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    payload = _stage7_family_support.propose_family_support_adapters(
        family_diagnosis_path=family_path
    )

    assert payload["schema_version"] == "stage7_family_support_adapter_proposals.v1"
    assert payload["causal_status"] == "non_causal"
    assert payload["sandbox_ready_count"] == 1
    proposal = payload["proposals"][0]
    assert proposal["proposal_status"] == "sandbox_ready"
    relation = proposal["proposed_support_relations"][0]
    assert relation["support_required_terms"] == ["support"]
    assert relation["requires_support_adapter"] is True


def test_stage7_family_adapter_outcome_quarantines_max_only_support(tmp_path):
    proposals_path = tmp_path / "proposals.json"
    equivalence_path = tmp_path / "equivalence.json"
    diagnostic_path = tmp_path / "diagnostic.json"
    proposals_path.write_text(
        json.dumps(
            {
                "proposals": [
                    {
                        "candidate_id": "cand.krk.box_shrink.family_ff.drive_to_edge_visible_support.v1",
                        "proposal_status": "sandbox_ready",
                    },
                    {
                        "candidate_id": "cand.krk.box_shrink.family_ac.fence_established_visible_support.v1",
                        "proposal_status": "needs_more_terms",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    equivalence_path.write_text(json.dumps({"equivalent": True}), encoding="utf-8")
    diagnostic_path.write_text(
        json.dumps(
            {
                "adapter_fire_count": 3,
                "adapter_supported_provider_by_outcome": {
                    "krk.drive_to_edge:max_plies": 3,
                },
            }
        ),
        encoding="utf-8",
    )

    payload = _stage7_family_adapter_outcome.evaluate_family_adapter_outcome(
        proposals_path=proposals_path,
        default_off_equivalence_path=equivalence_path,
        adapter_on_diagnostic_path=diagnostic_path,
    )

    assert payload["schema_version"] == "stage7_family_adapter_outcome.v1"
    assert payload["causal_status"] == "non_causal"
    updates = {item["candidate_id"]: item for item in payload["candidate_updates"]}
    assert updates[
        "cand.krk.box_shrink.family_ff.drive_to_edge_visible_support.v1"
    ]["status"] == "overbroad_or_misdirected_candidate"
    assert updates[
        "cand.krk.box_shrink.family_ff.drive_to_edge_visible_support.v1"
    ]["promotion_status"] == "quarantined"
    assert updates[
        "cand.krk.box_shrink.family_ac.fence_established_visible_support.v1"
    ]["status"] == "needs_more_terms"


def test_stage7_family_adapter_outcome_distinguishes_arbitration_dominated_support(tmp_path):
    proposals_path = tmp_path / "proposals.json"
    equivalence_path = tmp_path / "equivalence.json"
    diagnostic_path = tmp_path / "diagnostic.json"
    targeted_path = tmp_path / "targeted.json"
    proposals_path.write_text(
        json.dumps(
            {
                "proposals": [
                    {
                        "candidate_id": "cand.krk.box_shrink.family_ff.drive_to_edge_visible_support.v1",
                        "proposal_status": "sandbox_ready",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    equivalence_path.write_text(json.dumps({"equivalent": True}), encoding="utf-8")
    diagnostic_path.write_text(
        json.dumps({"adapter_fire_count": 0, "adapter_supported_provider_by_outcome": {}}),
        encoding="utf-8",
    )
    targeted_path.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "first_move_probes": [
                            {
                                "top_suggestions": [
                                    {
                                        "visible_role_provider_support_adapter": {
                                            "enabled": True,
                                            "direct_request": False,
                                        }
                                    }
                                ]
                            }
                        ],
                        "playout_probes": [{"result": "mate"}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    payload = _stage7_family_adapter_outcome.evaluate_family_adapter_outcome(
        proposals_path=proposals_path,
        default_off_equivalence_path=equivalence_path,
        adapter_on_diagnostic_path=diagnostic_path,
        targeted_probe_path=targeted_path,
    )

    assert payload["targeted_adapter_fire_count"] == 1
    assert payload["targeted_forced_mate_count"] == 1
    update = payload["candidate_updates"][0]
    assert update["status"] == "wired_but_arbitration_dominated"
    assert "provider_score_arbitration_dominates_visible_support" in update["diagnosis"]
    assert update["causal_status"] == "non_causal"


def test_stage7_move_shape_separation_detects_provider_adapter_overbreadth(tmp_path):
    family_path = tmp_path / "family.json"
    adapter_path = tmp_path / "adapter.json"
    family_path.write_text(
        json.dumps(
            {
                "families": [
                    {
                        "family_id": "stage7.post_box.family_ff",
                        "state_id": "state.ff",
                        "forced_provider_results": {
                            "krk.drive_to_edge": {
                                "result": "mate",
                                "plies": 7,
                                "first_move": "e4h4",
                                "first_move_probe": {
                                    "current_terms": ["box_shrink_drive_repair_available"],
                                    "move_shape_terms": [
                                        "candidate_is_rook_transfer",
                                        "rook_lateral_transfer",
                                    ],
                                    "post_move_terms": ["rook_safe_after_move"],
                                },
                            }
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    adapter_path.write_text(
        json.dumps(
            {
                "handoff_packets": [
                    {
                        "packet_id": "packet.1",
                        "evidence_terms": {
                            "fen": "8/8/8/8/R7/8/2k1K3/8 w - - 0 1",
                            "move": "a4h4",
                            "successor_selected_skill": "krk.stage0_basin",
                            "playout_result": "max_plies",
                            "adapter_supported_provider_counts": {"krk.drive_to_edge": 1},
                            "adapter_supported_move_counts": {"e2e3": 1},
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    payload = _stage7_move_shape_separation.diagnose_move_shape_separation(
        family_diagnosis_path=family_path,
        adapter_diagnostic_path=adapter_path,
        provider="krk.drive_to_edge",
    )

    assert payload["schema_version"] == "stage7_move_shape_separation.v1"
    assert payload["causal_status"] == "non_causal"
    update = payload["candidate_update"]
    assert update["status"] == "move_shape_gate_candidate"
    assert "candidate_is_rook_transfer" in update["required_move_shape_terms"]
    assert "do_not_run_m3_on_provider_adapter" in update["hard_blocks"]


def test_stage7_arbitration_candidate_update_prefers_weight_probe_over_topology():
    counts = {
        "forced_provider_can_convert": 1,
        "adapter_wired_and_visible_under_forced_provider": 1,
        "provider_score_scale_mismatch": 1,
    }

    update = _stage7_arbitration._candidate_update(counts)

    assert update["candidate_id"] == "cand.krk.box_shrink.stage0_fallback_arbitration.v1"
    assert update["status"] == "needs_weight_or_score_normalization_probe"
    assert "visible_support_too_small_relative_to_provider_score_gap" in update["diagnosis"]
    assert update["causal_status"] == "non_causal"
    assert "do_not_add_broad_stage0_penalty" in update["hard_blocks"]


def test_stage7_score_calibration_plan_blocks_growth_when_score_scale_dominates(tmp_path):
    arbitration_path = tmp_path / "arbitration.json"
    arbitration_path.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "state_id": "state.ff",
                        "family_id": "family.ff",
                        "normal_selected": {
                            "skill_id": "krk.stage0_basin",
                            "score": 33.0,
                        },
                        "provider_arbitration": [
                            {
                                "provider": "krk.drive_to_edge",
                                "forced_known_outcome": "mate",
                                "forced_known_plies": 7,
                                "forced_best": {"move": "e4h4", "score": 0.2},
                                "required_support_to_overtake_selected": 32.8,
                                "adapter_support_amount": 0.05,
                                "adapter_fired_under_forced_provider": True,
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    payload = _stage7_score_calibration.plan_stage7_score_calibration(
        arbitration_path=arbitration_path,
        max_additive_support=1.0,
    )

    assert payload["schema_version"] == "stage7_score_calibration_plan.v1"
    assert payload["next_phase"] == "bounded_score_normalization_probe"
    assert payload["growth_governor"]["growth_status"] == (
        "growth_blocked_by_weight_vs_topology_diagnosis"
    )
    candidate = payload["calibration_candidates"][0]
    assert candidate["status"] == "score_scale_normalization_probe_ready"
    assert "provider_scores_not_comparable_across_skills" in candidate["diagnosis"]
    assert "new_post_box_topology_before_calibration_probe" in payload["growth_governor"][
        "blocked_actions"
    ]


def test_stage7_score_normalization_probe_marks_role_owned_arbitration_candidate(tmp_path):
    arbitration_path = tmp_path / "arbitration.json"
    arbitration_path.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "state_id": "state.ff",
                        "family_id": "family.ff",
                        "normal_selected": {
                            "skill_id": "krk.stage0_basin",
                            "move": "e4e8",
                            "score": 33.0,
                        },
                        "provider_arbitration": [
                            {
                                "provider": "krk.drive_to_edge",
                                "forced_known_outcome": "mate",
                                "forced_known_plies": 7,
                                "forced_best": {"move": "e4h4", "score": 0.2},
                                "adapter_fired_under_forced_provider": True,
                                "required_support_to_overtake_selected": 32.8,
                                "adapter_support_amount": 0.05,
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    payload = _stage7_score_normalization.probe_stage7_score_normalization(
        arbitration_path=arbitration_path
    )

    assert payload["schema_version"] == "stage7_score_normalization_probe.v1"
    assert payload["adapter_role_mate_count"] == 1
    assert payload["candidate_update"]["status"] == (
        "role_owned_score_normalization_sandbox_candidate"
    )
    assert payload["records"][0]["adapter_role_changes_provider"] is True
    assert "do_not_make_oracle_choice_causal" in payload["candidate_update"]["hard_blocks"]


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
