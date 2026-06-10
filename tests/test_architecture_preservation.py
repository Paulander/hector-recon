"""
Architecture preservation checks for handoff diagnostics and M3-M5 learning.

These tests guard the intended separation:
- handoff/contract/shadow records are diagnostic evidence,
- M4 consolidation consumes ordinary episode edge deltas,
- shadow growth proposals do not mutate topology during gameplay.
"""

import ast
from pathlib import Path

from recon_lite.graph import Graph, LinkType, Node, NodeState, NodeType
from recon_lite.trace_db import EpisodeSummary
from recon_lite_chess.routing.contracts import (
    HandoffPacket,
    PlanCapsuleSpec,
    ShadowStemCandidate,
    SkillContractStats,
    StructuralCandidate,
    record_handoff_composition_event,
    record_plan_capsule_event,
    record_provider_promotion_event,
    record_structural_candidate_event,
)
from recon_lite_chess.routing.shadow_queue import build_shadow_stem_queue
from recon_lite_hector.plasticity.consolidate import (
    ConsolidationConfig,
    EdgeConsolidationState,
    ConsolidationEngine,
)


ROOT = Path(__file__).resolve().parents[1]


def _make_graph() -> Graph:
    graph = Graph()
    graph.add_node(Node("phase1", NodeType.SCRIPT, state=NodeState.INACTIVE))
    graph.add_node(Node("phase2", NodeType.SCRIPT, state=NodeState.INACTIVE))
    graph.add_edge("phase1", "phase2", LinkType.POR)
    return graph


def test_krk_runtime_source_has_no_tablebase_or_hidden_controller_imports():
    runtime_root = ROOT / "src" / "recon_lite_chess"
    forbidden_imports = {
        "chess.syzygy",
        "subprocess",
    }
    forbidden_call_names = {
        "SimpleEngine",
        "open_tablebase",
        "popen_uci",
    }
    violations = []

    for path in sorted(runtime_root.rglob("*.py")):
        relative = path.relative_to(runtime_root)
        if "/scripts/" in path.as_posix():
            continue
        if not (
            path.name.startswith("krk_")
            or relative.parts[:1] in {("graph",), ("routing",)}
        ):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported = alias.name
                    if imported in forbidden_imports:
                        violations.append((path.relative_to(ROOT).as_posix(), imported))
            elif isinstance(node, ast.ImportFrom) and node.module:
                module = node.module
                if module in forbidden_imports:
                    violations.append((path.relative_to(ROOT).as_posix(), module))
            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr in forbidden_call_names:
                    violations.append((path.relative_to(ROOT).as_posix(), func.attr))
                elif isinstance(func, ast.Name) and func.id in forbidden_call_names:
                    violations.append((path.relative_to(ROOT).as_posix(), func.id))

    assert violations == []


def test_handoff_diagnostics_round_trip_without_becoming_m4_inputs():
    packet = HandoffPacket.create(
        from_skill="krk.fence_established",
        phase="post_opponent_reply",
        status="confirmed",
        evidence_terms={
            "visible_fence_exists": True,
            "fence_survived_reply": True,
            "stagnation_loop": False,
        },
        continuation_exports={"krk.edge_trap_close": 0.31},
        observed_outcome="mate",
    )
    stats = SkillContractStats(
        skill_id="krk.fence_established",
        context_bucket="stage5.visible_fence_survived",
        attempts=3,
        confirmations=3,
        conversions_passed=2,
        conversions_failed=1,
    )
    candidate = ShadowStemCandidate(
        trigger="reward_contract_mismatch",
        owner_router="krk.successor_hub",
        scope="stage5",
        parent_skill="krk.fence_established",
        state_signature="state.visible-alignment-smoke",
        route_scores={"krk.edge_trap_close": 0.31},
        packet_id=packet.packet_id,
        observed_outcome="max_plies",
    )

    summary = EpisodeSummary(
        edge_delta_sums={"phase1->phase2:POR": 0.25},
        avg_reward_tick=1.0,
        outcome_score=1.0,
    )
    summary.record_learning_event(
        tick=12,
        event_type="handoff_diagnostic",
        subject_id=packet.packet_id,
        parent_id="krk.fence_established",
        credit=0.0,
        meta={
            "handoff_packet": packet.to_dict(),
            "skill_contract_stats": stats.to_dict(),
            "shadow_candidate": candidate.to_dict(),
        },
    )

    restored = EpisodeSummary.from_dict(summary.to_dict())
    event = restored.learning_events[0]
    assert restored.edge_delta_sums == {"phase1->phase2:POR": 0.25}
    assert event.meta["handoff_packet"]["schema_version"] == "handoff_packet.v1"
    assert event.meta["skill_contract_stats"]["schema_version"] == "skill_contract_stats.v1"
    assert event.meta["shadow_candidate"]["promotion_status"] == "shadow"

    engine = ConsolidationEngine(
        ConsolidationConfig(min_episodes=1, outcome_weight=0.5)
    )
    engine.edge_states["phase1->phase2:POR"] = EdgeConsolidationState(
        edge_key="phase1->phase2:POR",
        w_base=1.0,
    )
    engine.accumulate_episode(restored)

    assert set(engine.edge_states) == {"phase1->phase2:POR"}
    state = engine.edge_states["phase1->phase2:POR"]
    assert state.episode_count == 1
    assert state.accumulated_weighted_delta == 0.25


def test_shadow_candidates_queue_without_live_topology_mutation():
    graph = _make_graph()
    before_nodes = set(graph.nodes)
    before_edge_count = len(graph.edges)

    candidate = ShadowStemCandidate(
        trigger="handoff_gap",
        owner_router="krk.successor_hub",
        scope="stage5",
        parent_skill="krk.fence_established",
        state_signature="state.shadow-only",
        route_scores={"krk.stage0_basin": 0.5},
        observed_outcome="max_plies",
    )
    queue = build_shadow_stem_queue([candidate.to_dict()])

    assert len(queue.queue) == 1
    assert queue.queue[0].promotion_status == "shadow"
    assert queue.queue[0].trigger == "handoff_gap"
    assert set(graph.nodes) == before_nodes
    assert len(graph.edges) == before_edge_count
    assert graph.get_edge("phase1", "phase2", LinkType.POR) is not None


def test_handoff_composition_events_export_to_episode_summary_non_causally():
    packet = HandoffPacket.create(
        from_skill="krk.fence_established",
        to_skill="krk.edge_trap_close",
        phase="post_opponent_reply",
        status="confirmed",
        evidence_terms={"visible_role": "krk.post_fence_edge_trap_recovery"},
        observed_outcome="mate",
    )
    summary = EpisodeSummary(
        edge_delta_sums={"phase1->phase2:POR": 0.4},
        avg_reward_tick=1.0,
        outcome_score=1.0,
    )

    record_handoff_composition_event(
        summary,
        tick=18,
        from_skill="krk.fence_established",
        to_skill="krk.edge_trap_close",
        role="krk.post_fence_edge_trap_recovery",
        move_shape="krk.move_shape.rook_transfer_to_cut",
        status="conversion_success",
        handoff_packet=packet,
        plies_to_mate=12,
    )

    restored = EpisodeSummary.from_dict(summary.to_dict())
    assert restored.edge_delta_sums == {"phase1->phase2:POR": 0.4}
    assert len(restored.learning_events) == 1
    event = restored.learning_events[0]
    assert event.event_type == "handoff_composition_event"
    assert event.credit == 0.0
    assert event.meta["schema_version"] == "handoff_composition_event.v1"
    assert event.meta["handoff_packet"]["schema_version"] == "handoff_packet.v1"

    engine = ConsolidationEngine(
        ConsolidationConfig(min_episodes=1, outcome_weight=0.5)
    )
    engine.edge_states["phase1->phase2:POR"] = EdgeConsolidationState(
        edge_key="phase1->phase2:POR",
        w_base=1.0,
    )
    engine.accumulate_episode(restored)

    assert set(engine.edge_states) == {"phase1->phase2:POR"}
    assert engine.edge_states["phase1->phase2:POR"].accumulated_weighted_delta == 0.4


def test_provider_promotion_events_export_to_episode_summary_non_causally():
    summary = EpisodeSummary(
        edge_delta_sums={"phase1->phase2:POR": 0.35},
        avg_reward_tick=1.0,
        outcome_score=1.0,
    )

    record_provider_promotion_event(
        summary,
        tick=21,
        skill_id="krk.drive_to_edge",
        provider_version="stage6_overlay_v1",
        promotion_status="promoted",
        source_checkpoint="snapshots/.../drive_to_edge.pkl",
        base_provider_version="stage5_validated_v1",
        overlay_provider_version="stage6_overlay_v1",
        validated_profile="handoff_composition_v1",
        stage_artifact="stage6_drive_overlay_300_seed7_h40.json",
        guardrail_artifacts=["stage5_fence_overlay_300_seed7_h40.json"],
        promotion_eval={"schema_version": "provider_promotion_eval.v1"},
    )

    restored = EpisodeSummary.from_dict(summary.to_dict())
    assert restored.edge_delta_sums == {"phase1->phase2:POR": 0.35}
    assert len(restored.learning_events) == 1
    event = restored.learning_events[0]
    assert event.event_type == "provider_promotion_event"
    assert event.credit == 0.0
    assert event.parent_id == "krk.drive_to_edge"
    assert event.meta["schema_version"] == "provider_promotion_event.v1"
    assert event.meta["promotion_status"] == "promoted"
    assert event.meta["promotion_eval"]["schema_version"] == "provider_promotion_eval.v1"

    engine = ConsolidationEngine(
        ConsolidationConfig(min_episodes=1, outcome_weight=0.5)
    )
    engine.edge_states["phase1->phase2:POR"] = EdgeConsolidationState(
        edge_key="phase1->phase2:POR",
        w_base=1.0,
    )
    engine.accumulate_episode(restored)

    assert set(engine.edge_states) == {"phase1->phase2:POR"}
    assert engine.edge_states["phase1->phase2:POR"].accumulated_weighted_delta == 0.35


def test_structural_candidate_round_trips_and_remains_non_causal():
    candidate = StructuralCandidate(
        candidate_type="contract_refinement",
        source_monitor_script="growth.monitor.reward_contract_mismatch",
        source_terms=["reward_confirmed", "visible_contract_not_confirmed"],
        trigger_failure_classes=["reward_contract_mismatch"],
        target_skill="krk.box_shrink",
        parent_skill="krk.drive_to_edge",
        proposed_change={"kind": "visible_contract_audit"},
        evidence_artifacts=["stage7.json"],
    )

    restored = StructuralCandidate.from_dict(candidate.to_dict())

    assert restored.schema_version == "structural_candidate.v1"
    assert restored.causal_status == "non_causal"
    assert restored.credit == 0.0
    assert restored.promotion_status == "proposed"
    assert restored.governor_status == "settling"
    assert restored.governor_metadata == {}
    assert restored.topology_weight_diagnosis == {}
    assert restored.candidate_diagnostic_labels == []


def test_structural_candidate_event_exports_without_m4_or_topology_effect():
    graph = _make_graph()
    before_nodes = set(graph.nodes)
    before_edges = len(graph.edges)
    candidate = StructuralCandidate(
        candidate_type="successor_contract_refinement",
        source_monitor_script="growth.monitor.successor_miscalibration",
        source_terms=["selected_successor_miscalibrated", "repeated_conversion_failure"],
        trigger_failure_classes=["selected_successor_miscalibrated", "repeated_conversion_failure"],
        target_skill="krk.box_shrink",
        parent_skill="krk.drive_to_edge",
        proposed_change={"kind": "handoff_role_audit"},
        evidence_artifacts=["stage7.json", "stage7.md"],
    )
    summary = EpisodeSummary(
        edge_delta_sums={"phase1->phase2:POR": 0.45},
        avg_reward_tick=1.0,
        outcome_score=1.0,
    )

    record_structural_candidate_event(summary, tick=33, candidate=candidate)

    restored = EpisodeSummary.from_dict(summary.to_dict())
    event = restored.learning_events[0]
    assert event.event_type == "structural_candidate_event"
    assert event.credit == 0.0
    assert event.meta["schema_version"] == "structural_candidate_event.v1"
    assert event.meta["structural_candidate"]["schema_version"] == "structural_candidate.v1"
    assert event.meta["structural_candidate"]["causal_status"] == "non_causal"

    engine = ConsolidationEngine(
        ConsolidationConfig(min_episodes=1, outcome_weight=0.5)
    )
    engine.edge_states["phase1->phase2:POR"] = EdgeConsolidationState(
        edge_key="phase1->phase2:POR",
        w_base=1.0,
    )
    engine.accumulate_episode(restored)

    assert set(graph.nodes) == before_nodes
    assert len(graph.edges) == before_edges
    assert set(engine.edge_states) == {"phase1->phase2:POR"}
    assert engine.edge_states["phase1->phase2:POR"].accumulated_weighted_delta == 0.45


def test_plan_capsule_event_exports_without_m4_or_topology_effect():
    graph = _make_graph()
    before_nodes = set(graph.nodes)
    before_edges = len(graph.edges)
    capsule = PlanCapsuleSpec(
        capsule_id="krk.post_box_shrink_continuation",
        source_candidate_id="cand.krk.box_shrink.post_box_continuation_capsule.v1",
        source_monitor_script="growth.monitor.stage7_post_box_continuation_gap",
        source_terms=["local_valid_composition_quarantined", "single_move_repairs_exhausted"],
        domain="krk",
        target_skill="krk.box_shrink",
        entry_terms=["active_landmark_label.box_shrink", "post_reply_state_reached"],
        progress_terms=["box_area_decreases_or_does_not_expand"],
        exit_terms=["edge_trap_role_confirmed", "drive_to_edge_role_confirmed"],
        abort_terms=["rook_unsafe", "no_progress_after_owned_moves"],
        ttl_white_moves=3,
        owned_roles=["krk.post_box_shrink_continuation"],
        owned_providers=["krk.drive_to_edge", "krk.edge_trap_close"],
        handoff_exports={"krk.edge_trap_close": 0.4, "krk.drive_to_edge": 0.3},
        training_source="reports/structural_candidates/stage7_post_box_dtm_trajectory_seed_h40.json",
        validation_protocol={"target": "Stage 7 h40", "default": "disabled"},
        guardrails=["stage6_drive_to_edge", "stage5_fence_established"],
        notes=["not a fixed Stage 7.5 curriculum stage"],
    )
    summary = EpisodeSummary(
        edge_delta_sums={"phase1->phase2:POR": 0.55},
        avg_reward_tick=1.0,
        outcome_score=1.0,
    )

    record_plan_capsule_event(summary, tick=44, capsule=capsule)

    restored = EpisodeSummary.from_dict(summary.to_dict())
    event = restored.learning_events[0]
    assert event.event_type == "plan_capsule_event"
    assert event.credit == 0.0
    assert event.meta["schema_version"] == "plan_capsule_event.v1"
    assert event.meta["plan_capsule"]["schema_version"] == "plan_capsule_spec.v1"
    assert event.meta["plan_capsule"]["causal_status"] == "non_causal"

    engine = ConsolidationEngine(
        ConsolidationConfig(min_episodes=1, outcome_weight=0.5)
    )
    engine.edge_states["phase1->phase2:POR"] = EdgeConsolidationState(
        edge_key="phase1->phase2:POR",
        w_base=1.0,
    )
    engine.accumulate_episode(restored)

    assert set(graph.nodes) == before_nodes
    assert len(graph.edges) == before_edges
    assert set(engine.edge_states) == {"phase1->phase2:POR"}
    assert engine.edge_states["phase1->phase2:POR"].accumulated_weighted_delta == 0.55
