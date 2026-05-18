#!/usr/bin/env python3
"""Tests for the non-causal Stage 7 plan capsule artifact helpers."""

import importlib.util
import json
from pathlib import Path

import chess

from recon_lite_chess.routing import PlanCapsuleSpec, StructuralCandidate


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "audit_stage7_post_box_plan_capsule.py"
LANDMARK_SCRIPT = ROOT / "scripts" / "test_krk_landmark_progress.py"
FEN_069 = "8/8/8/8/7R/2k5/4K3/8 w - - 2 2"
FEN_0926 = "8/8/8/8/4K3/8/R7/4k3 w - - 2 2"
FEN_2CC = "8/8/R7/8/2k5/8/8/3K4 w - - 2 2"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("audit_stage7_post_box_plan_capsule", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_landmark_module():
    spec = importlib.util.spec_from_file_location("test_krk_landmark_progress", LANDMARK_SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _candidate_layer_blackboard() -> dict:
    return {
        "candidate_move_layer_enabled": True,
        "krk_visible_terms": {
            "active_landmark_label.box_shrink": True,
            "post_reply_state_reached": True,
            "rook_safe": True,
            "conversion_not_immediate": True,
            "no_mate_in_one_available": True,
        },
        "krk_dynamic_context_terms": {},
        "krk_plan_capsule_markers": {
            "krk.post_box_shrink_continuation": {
                "entry_confirmed": True,
            }
        },
    }


def test_plan_capsule_candidate_export_is_non_causal():
    module = _load_script_module()
    payload = module.build_plan_capsule_candidate(evidence_artifacts=["stage7.json"])

    assert payload["schema_version"] == "plan_capsule_candidate.v1"
    assert payload["causal_status"] == "non_causal"
    assert payload["promotion_status"] == "sandbox_ready"
    assert payload["candidate_id"] == "cand.krk.box_shrink.post_box_continuation_capsule.v1"

    capsule = PlanCapsuleSpec.from_dict(json.loads(json.dumps(payload["plan_capsule"])))
    candidate = StructuralCandidate.from_dict(json.loads(json.dumps(payload["structural_candidate"])))

    assert capsule.schema_version == "plan_capsule_spec.v1"
    assert capsule.capsule_id == "krk.post_box_shrink_continuation"
    assert capsule.causal_status == "non_causal"
    assert capsule.promotion_status == "sandbox_ready"
    assert capsule.self_model["causal_status"] == "trace_only"
    assert capsule.ttl_white_moves == 3
    assert "not a fixed Stage 7.5 curriculum stage" in " ".join(capsule.notes)
    assert candidate.schema_version == "structural_candidate.v1"
    assert candidate.candidate_type == "plan_capsule"
    assert candidate.causal_status == "non_causal"
    assert candidate.credit == 0.0
    assert candidate.proposed_change["kind"] == "plan_capsule_commitment_bias"


def test_plan_capsule_sandbox_protocol_is_non_causal_and_bounded():
    module = _load_script_module()
    sandbox_script = ROOT / "scripts" / "sandbox_stage7_post_box_plan_capsule.py"
    spec = importlib.util.spec_from_file_location("sandbox_stage7_post_box_plan_capsule", sandbox_script)
    assert spec is not None
    sandbox = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(sandbox)

    candidate = module.build_plan_capsule_candidate(evidence_artifacts=["stage7.json"])
    trajectory_seed = {
        "trajectories": [
            {
                "start_fen": "8/8/R7/8/2k5/8/8/3K4 w - - 2 2",
                "start_dtm": 5,
                "white_training_steps": [
                    {
                        "ply_index": 0,
                        "move": "a6a5",
                        "child_dtm": 4,
                        "move_shape_terms": ["candidate_is_rook_move"],
                        "post_move_terms": [
                            "box_area_not_increased_after_move",
                            "enemy_edge_distance_not_increased_after_move",
                            "rook_safe_after_move",
                        ],
                    },
                    {
                        "ply_index": 2,
                        "move": "d1e2",
                        "child_dtm": 2,
                        "move_shape_terms": ["candidate_is_king_move"],
                        "post_move_terms": [
                            "box_area_not_increased_after_move",
                            "white_king_distance_to_rook_decreases",
                            "rook_safe_after_move",
                        ],
                    },
                ],
            }
        ]
    }

    payload = sandbox.evaluate_capsule_protocol(
        candidate=candidate,
        trajectory_seed=trajectory_seed,
        ttl_white_moves=2,
    )

    assert payload["schema_version"] == "stage7_post_box_plan_capsule_sandbox_protocol.v1"
    assert payload["causal_status"] == "non_causal"
    assert payload["runtime_behavior_changed"] is False
    assert payload["ttl_white_moves"] == 2
    assert payload["reference_supported_count"] == 1
    assert payload["per_trajectory"][0]["protocol_supported_by_reference"] is True


def test_plan_capsule_sandbox_compiler_is_default_off_and_non_requesting(tmp_path):
    module = _load_script_module()
    compiler_script = ROOT / "scripts" / "compile_plan_capsule_sandbox.py"
    spec = importlib.util.spec_from_file_location("compile_plan_capsule_sandbox", compiler_script)
    assert spec is not None
    compiler = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(compiler)

    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text(
        json.dumps(module.build_plan_capsule_candidate(evidence_artifacts=["stage7.json"])),
        encoding="utf-8",
    )
    topology_path = tmp_path / "topology.json"
    topology_path.write_text(
        json.dumps(
            {
                "nodes": {"krk_hub": {"id": "krk_hub", "type": "SCRIPT", "meta": {}}},
                "edges": [],
                "meta": {},
            }
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "compiled.json"

    topology = compiler.compile_plan_capsule_sandbox(
        topology_path=topology_path,
        candidate_path=candidate_path,
        output_path=output_path,
    )

    sandbox = topology["meta"]["plan_capsule_sandbox"]
    node = topology["nodes"][sandbox["node_id"]]
    assert sandbox["enabled_by_default"] is False
    assert sandbox["direct_request"] is False
    assert sandbox["causal_status"] == "sandbox_opt_in_non_requesting"
    assert node["meta"]["enabled_by_default"] is False
    assert node["meta"]["direct_request"] is False
    assert node["meta"]["causal_status"] == "sandbox_opt_in_non_requesting"
    assert "plan_capsule_sandbox_enabled" not in topology["nodes"]["krk_hub"].get("meta", {})


def test_plan_capsule_marker_analysis_recommends_progress_monitor():
    analyzer_script = ROOT / "scripts" / "analyze_plan_capsule_markers.py"
    spec = importlib.util.spec_from_file_location("analyze_plan_capsule_markers", analyzer_script)
    assert spec is not None
    analyzer = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(analyzer)

    diagnostic = {
        "handoff_packets": [
            {
                "phase": "post_opponent_reply",
                "evidence_terms": {
                    "playout_result": "max_plies",
                    "plan_capsule_markers": {
                        "krk.post_box_shrink_continuation": {
                            "entry_confirmed": True,
                            "abort_confirmed": False,
                            "entry_terms_met": ["post_reply_state_reached"],
                            "progress_terms_met": ["box_area_decreases_or_does_not_expand"],
                            "exit_terms_met": [],
                            "abort_terms_met": [],
                        }
                    },
                },
            },
            {
                "phase": "post_opponent_reply",
                "evidence_terms": {
                    "playout_result": "mate",
                    "plan_capsule_markers": {
                        "krk.post_box_shrink_continuation": {
                            "entry_confirmed": False,
                            "abort_confirmed": False,
                            "entry_terms_met": ["post_reply_state_reached"],
                            "progress_terms_met": ["box_area_decreases_or_does_not_expand"],
                            "exit_terms_met": ["mate_in_one_available"],
                            "abort_terms_met": [],
                        }
                    },
                },
            },
        ]
    }

    payload = analyzer.analyze_markers(
        diagnostic,
        capsule_id="krk.post_box_shrink_continuation",
    )

    assert payload["schema_version"] == "plan_capsule_marker_analysis.v1"
    assert payload["causal_status"] == "non_causal"
    assert payload["diagnosis"]["entry_confirmed_max_plies_count"] == 1
    assert payload["diagnosis"]["mate_exit_count"] == 1
    assert "add_owned_move_progress_or_ttl_failure_monitor_before_causal_capsule" in payload["recommendations"]


def test_plan_capsule_owned_window_analysis_detects_ttl_failure():
    analyzer_script = ROOT / "scripts" / "analyze_plan_capsule_owned_window.py"
    spec = importlib.util.spec_from_file_location("analyze_plan_capsule_owned_window", analyzer_script)
    assert spec is not None
    analyzer = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(analyzer)

    diagnostic = {
        "handoff_packets": [
            {
                "evidence_terms": {
                    "post_reply_fen": "8/8/8/8/7R/2k5/4K3/8 w - - 2 2",
                    "plan_capsule_markers": {
                        "krk.post_box_shrink_continuation": {
                            "entry_confirmed": True,
                            "abort_terms_met": [],
                        }
                    },
                }
            }
        ],
        "debug_playouts": [
            {
                "sample": 1,
                "result": "max_plies",
                "trace": [
                    {
                        "turn": "white",
                        "fen": "8/8/8/8/7R/2k5/4K3/8 w - - 2 2",
                        "move": "e2d1",
                        "resulting_fen": "8/8/8/8/7R/2k5/8/3K4 b - - 3 2",
                    },
                    {"turn": "black", "fen": "8/8/8/8/7R/2k5/8/3K4 b - - 3 2", "move": "c3d3"},
                    {
                        "turn": "white",
                        "fen": "8/8/8/8/7R/3k4/8/3K4 w - - 4 3",
                        "move": "d1c1",
                        "resulting_fen": "8/8/8/8/7R/3k4/8/2K5 b - - 5 3",
                    },
                    {"turn": "black", "fen": "8/8/8/8/7R/3k4/8/2K5 b - - 5 3", "move": "d3e3"},
                    {
                        "turn": "white",
                        "fen": "8/8/8/8/7R/4k3/8/2K5 w - - 6 4",
                        "move": "c1c2",
                        "resulting_fen": "8/8/8/8/7R/4k3/2K5/8 b - - 7 4",
                    },
                ],
            }
        ],
    }

    payload = analyzer.analyze_owned_window(
        diagnostic,
        capsule_id="krk.post_box_shrink_continuation",
        ttl_white_moves=3,
    )

    assert payload["schema_version"] == "plan_capsule_owned_window_analysis.v1"
    assert payload["causal_status"] == "non_causal"
    assert payload["window_count"] == 1
    assert payload["ttl_failure_count"] == 1
    assert payload["windows"][0]["ttl_failure"] is True


def test_stage7_residual_repair_protocols_are_non_causal():
    script = ROOT / "scripts" / "plan_stage7_residual_repair_protocols.py"
    spec = importlib.util.spec_from_file_location("plan_stage7_residual_repair_protocols", script)
    assert spec is not None
    planner = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(planner)

    candidate_payload = {
        "schema_version": "stage7_plan_capsule_residual_candidate_updates.v1",
        "structural_candidates": [
            {
                "schema_version": "structural_candidate.v1",
                "candidate_id": "cand.krk.box_shrink.family_069.drive_role_refinement.v1",
                "candidate_type": "family_specific_role_refinement",
                "source_monitor_script": "growth.monitor.stage7_plan_capsule_residual_family_split",
                "source_terms": ["drive_to_edge_forced_mate_h40"],
                "trigger_failure_classes": ["wrong_owned_provider"],
                "target_skill": "krk.box_shrink",
                "parent_skill": "krk.post_box_shrink_continuation",
                "proposed_change": {"kind": "visible_role_boundary_refinement"},
                "promotion_status": "proposed",
                "causal_status": "non_causal",
                "credit": 0.0,
            },
            {
                "schema_version": "structural_candidate.v1",
                "candidate_id": "cand.krk.box_shrink.family_0926.king_support_fence_stabilizer.v1",
                "candidate_type": "move_shape_role_refinement",
                "source_monitor_script": "growth.monitor.stage7_plan_capsule_residual_family_split",
                "source_terms": ["legal_first_move_converts_h40"],
                "trigger_failure_classes": ["legal_first_action_selection_gap"],
                "target_skill": "krk.box_shrink",
                "parent_skill": "krk.post_box_shrink_continuation",
                "proposed_change": {"kind": "visible_move_shape_contract"},
                "promotion_status": "proposed",
                "causal_status": "non_causal",
                "credit": 0.0,
            },
            {
                "schema_version": "structural_candidate.v1",
                "candidate_id": "cand.krk.box_shrink.family_2cc.post_box_continuation_overlay.v1",
                "candidate_type": "narrow_overlay_training_candidate",
                "source_monitor_script": "growth.monitor.stage7_plan_capsule_residual_family_split",
                "source_terms": ["dtm_won_within_h40"],
                "trigger_failure_classes": ["provider_capacity_missing"],
                "target_skill": "krk.box_shrink",
                "parent_skill": "krk.post_box_shrink_continuation",
                "proposed_change": {"kind": "narrow_post_box_continuation_overlay_probe"},
                "promotion_status": "proposed",
                "causal_status": "non_causal",
                "credit": 0.0,
            },
        ],
    }

    payload = planner.build_residual_protocols(candidate_payload)

    assert payload["schema_version"] == "stage7_residual_repair_protocols.v1"
    assert payload["causal_status"] == "non_causal"
    assert payload["protocol_count"] == 3
    statuses = {item["source_candidate_id"]: item["status"] for item in payload["protocols"]}
    assert (
        statuses["cand.krk.box_shrink.family_069.drive_role_refinement.v1"]
        == "rejected_as_general_priority_rule"
    )
    assert (
        statuses["cand.krk.box_shrink.family_0926.king_support_fence_stabilizer.v1"]
        == "sandbox_design_ready"
    )
    assert "do_not_promote_stage7" in payload["global_boundaries"]


def test_stage7_0926_move_shape_role_export_is_non_causal():
    script = ROOT / "scripts" / "export_stage7_0926_move_shape_role.py"
    spec = importlib.util.spec_from_file_location("export_stage7_0926_move_shape_role", script)
    assert spec is not None
    exporter = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(exporter)

    candidate_payload = {
        "structural_candidates": [
            {
                "schema_version": "structural_candidate.v1",
                "candidate_id": "cand.krk.box_shrink.family_0926.king_support_fence_stabilizer.v1",
                "candidate_type": "move_shape_role_refinement",
                "source_monitor_script": "growth.monitor.stage7_plan_capsule_residual_family_split",
                "source_terms": ["legal_first_move_converts_h40"],
                "trigger_failure_classes": ["legal_first_action_selection_gap"],
                "target_skill": "krk.box_shrink",
                "parent_skill": "krk.post_box_shrink_continuation",
                "proposed_change": {"kind": "visible_move_shape_contract"},
                "promotion_status": "proposed",
                "causal_status": "non_causal",
                "credit": 0.0,
            }
        ]
    }

    payload = exporter.build_role_spec(candidate_payload)

    assert payload["schema_version"] == "stage7_0926_move_shape_role_export.v1"
    assert payload["causal_status"] == "non_causal"
    role = payload["move_shape_role"]
    assert role["schema_version"] == "move_shape_role_spec.v1"
    assert role["role_id"] == "krk.post_box.king_support_fence_stabilizer"
    assert role["causal_status"] == "non_causal"
    assert "candidate_is_king_move" in role["move_shape_required_terms"]
    assert "no_state_hash_exception" in role["guardrails"]


def test_move_shape_role_candidate_audit_matches_only_visible_terms():
    script = ROOT / "scripts" / "audit_move_shape_role_candidates.py"
    spec = importlib.util.spec_from_file_location("audit_move_shape_role_candidates", script)
    assert spec is not None
    auditor = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(auditor)

    role = auditor.MoveShapeRoleSpec(
        role_id="krk.post_box.king_support_fence_stabilizer",
        source_candidate_id="cand.krk.box_shrink.family_0926.king_support_fence_stabilizer.v1",
        source_monitor_script="growth.monitor.stage7_plan_capsule_residual_family_split",
        source_terms=["legal_first_move_converts_h40"],
        domain="krk",
        target_skill="krk.box_shrink",
        move_shape_required_terms=[
            "candidate_is_king_move",
            "king_moves_toward_enemy",
            "king_moves_toward_rook_support",
        ],
        post_move_required_terms=[
            "rook_safe_after_move",
            "box_area_not_increased_after_move",
            "fence_exists_after_move",
            "fence_stable_after_move",
            "cut_preserved_after_move",
            "white_king_distance_to_enemy_decreases",
            "white_king_distance_to_rook_decreases",
        ],
    )

    payload = auditor.build_audit(
        role,
        fens=[
            "8/8/8/8/7R/2k5/4K3/8 w - - 2 2",
            "8/8/8/8/4K3/8/R7/4k3 w - - 2 2",
            "8/8/R7/8/2k5/8/8/3K4 w - - 2 2",
        ],
    )

    assert payload["causal_status"] == "non_causal"
    assert payload["summary"]["states_with_matches"] == 1
    matches = [
        move["move"]
        for record in payload["records"]
        for move in record["matching_moves"]
    ]
    assert matches == ["e4d3"]


def test_candidate_move_enumerator_emits_ephemeral_legal_frames():
    module = _load_landmark_module()
    board = chess.Board(FEN_0926)
    blackboard = _candidate_layer_blackboard()

    frames = module._enumerate_candidate_move_frames(board, blackboard=blackboard)

    assert frames
    assert all(frame.schema_version == "candidate_move_frame.v1" for frame in frames)
    assert all(frame.legal for frame in frames)
    assert all(frame.causal_status == "non_causal" for frame in frames)
    assert blackboard["krk_candidate_move_enumerator"]["direct_request"] is False
    assert blackboard["krk_candidate_move_enumerator"]["source_terminal"] == (
        "terminal.krk.candidate_move_enumerator"
    )


def test_role_scoped_candidate_move_actuator_matches_0926_only():
    module = _load_landmark_module()

    env = {
        "board": chess.Board(FEN_0926),
        "blackboard": _candidate_layer_blackboard(),
        "actuator_suggestions": [],
    }
    module._apply_stage7_candidate_move_layer(
        env,
        role_enabled=True,
        support_amount=3.0,
    )

    suggestions = env["actuator_suggestions"]
    assert [item["move"].uci() for item in suggestions] == ["e4d3"]
    payload = suggestions[0]["meta"]["visible_role_scoped_candidate_move_actuator"]
    assert payload["role_id"] == "krk.post_box.king_support_fence_stabilizer"
    assert payload["direct_request"] is False
    assert payload["causal_status"] == "sandbox_opt_in"
    assert payload["support_amount"] == 3.0
    assert "candidate_is_king_move" in payload["matched_terms"]
    assert env["blackboard"]["krk_candidate_move_role_matches"]["match_count"] == 1

    for fen in (FEN_069, FEN_2CC):
        env = {
            "board": chess.Board(fen),
            "blackboard": _candidate_layer_blackboard(),
            "actuator_suggestions": [],
        }
        module._apply_stage7_candidate_move_layer(
            env,
            role_enabled=True,
            support_amount=3.0,
        )
        assert env["actuator_suggestions"] == []
        assert env["blackboard"]["krk_candidate_move_role_matches"]["match_count"] == 0


def test_candidate_move_layer_default_off_does_not_emit_suggestions():
    module = _load_landmark_module()
    env = {
        "board": chess.Board(FEN_0926),
        "blackboard": _candidate_layer_blackboard() | {"candidate_move_layer_enabled": False},
        "actuator_suggestions": [],
    }

    module._apply_stage7_candidate_move_layer(
        env,
        role_enabled=True,
        support_amount=3.0,
    )

    assert env["actuator_suggestions"] == []
    assert "krk_candidate_move_frames" not in env["blackboard"]


def test_candidate_move_frame_audit_is_non_causal():
    script = ROOT / "scripts" / "audit_candidate_move_frames.py"
    spec = importlib.util.spec_from_file_location("audit_candidate_move_frames", script)
    assert spec is not None
    auditor = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(auditor)

    payload = auditor.audit_fens([FEN_2CC])

    assert payload["schema_version"] == "candidate_move_frame_audit.v1"
    assert payload["causal_status"] == "non_causal"
    assert payload["direct_request"] is False
    assert payload["records"][0]["legal_move_count"] > 0
    frames = payload["records"][0]["candidate_move_frames"]
    assert all(frame["schema_version"] == "candidate_move_frame.v1" for frame in frames)
    assert all(frame["causal_status"] == "non_causal" for frame in frames)


def test_candidate_move_frame_dtm_alignment_classifies_multistep_gap(tmp_path):
    audit_script = ROOT / "scripts" / "audit_candidate_move_frames.py"
    audit_spec = importlib.util.spec_from_file_location("audit_candidate_move_frames", audit_script)
    assert audit_spec is not None
    auditor = importlib.util.module_from_spec(audit_spec)
    assert audit_spec.loader is not None
    audit_spec.loader.exec_module(auditor)

    align_script = ROOT / "scripts" / "diagnose_candidate_move_frame_dtm_alignment.py"
    align_spec = importlib.util.spec_from_file_location(
        "diagnose_candidate_move_frame_dtm_alignment",
        align_script,
    )
    assert align_spec is not None
    aligner = importlib.util.module_from_spec(align_spec)
    assert align_spec.loader is not None
    align_spec.loader.exec_module(aligner)

    frames_path = tmp_path / "frames.json"
    frames_path.write_text(json.dumps(auditor.audit_fens([FEN_2CC])), encoding="utf-8")
    dtm_path = tmp_path / "dtm.json"
    dtm_path.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "fen": FEN_2CC,
                        "state_dtm": 27,
                        "legal_move_count": 2,
                        "winning_move_count": 2,
                        "best_winning_moves": [
                            {"move": "a6a5", "child_dtm": 26},
                        ],
                        "legal_moves": [
                            {"move": "a6a5", "child_dtm": 26, "forces_mate": True},
                            {"move": "d1d2", "child_dtm": 26, "forces_mate": True},
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    legal_path = tmp_path / "legal.json"
    legal_path.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "post_reply_fen": FEN_2CC,
                        "legal_first_probes": [
                            {"move": "a6a5", "horizon": 40, "result": "max_plies"},
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    payload = aligner.diagnose_alignment(
        candidate_frames_path=frames_path,
        dtm_oracle_path=dtm_path,
        legal_first_path=legal_path,
    )

    assert payload["schema_version"] == "candidate_move_frame_dtm_alignment.v1"
    assert payload["causal_status"] == "non_causal"
    assert payload["candidate_update"]["causal_status"] == "non_causal"
    assert payload["candidate_update"]["diagnosis"] == (
        "multi_step_continuation_policy_gap_not_single_move_gap"
    )


def test_stage7_2cc_continuation_protocol_is_non_causal():
    script = ROOT / "scripts" / "plan_stage7_2cc_continuation_protocol.py"
    spec = importlib.util.spec_from_file_location("plan_stage7_2cc_continuation_protocol", script)
    assert spec is not None
    planner = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(planner)

    payload = planner.build_protocol(
        {
            "schema_version": "candidate_move_frame_dtm_alignment.v1",
            "candidate_update": {
                "diagnosis": "multi_step_continuation_policy_gap_not_single_move_gap",
            },
        }
    )

    assert payload["schema_version"] == "stage7_2cc_continuation_protocol.v1"
    assert payload["causal_status"] == "non_causal"
    candidate = payload["structural_candidate"]
    assert candidate["causal_status"] == "non_causal"
    assert candidate["promotion_status"] == "sandbox_training_protocol_ready"
    assert "do_not_train_stage8" in payload["hard_boundaries"]
    assert "tablebase_lookup" in candidate["proposed_change"]["runtime_forbidden_terms"]


def test_stage7_2cc_protocol_phase01_uses_frozen_visible_model(tmp_path):
    script = ROOT / "scripts" / "evaluate_stage7_2cc_protocol_phase01.py"
    spec = importlib.util.spec_from_file_location("evaluate_stage7_2cc_protocol_phase01", script)
    assert spec is not None
    evaluator = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(evaluator)

    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text(
        json.dumps(
            {
                "causal_status": "non_causal",
                "structural_candidate": {
                    "candidate_id": "cand.krk.box_shrink.family_2cc.post_box_continuation_overlay.v1",
                    "causal_status": "non_causal",
                    "promotion_status": "sandbox_training_protocol_ready",
                    "proposed_change": {
                        "runtime_forbidden_terms": [
                            "tablebase_lookup",
                            "dtm_oracle_move_selection",
                            "state_hash_exception",
                        ]
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    frames_path = tmp_path / "frames.json"
    frames_path.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "fen": FEN_2CC,
                        "candidate_move_frames": [
                            {
                                "move_uci": "d1e2",
                                "move_shape_terms": ["candidate_is_king_move"],
                                "post_move_terms": ["white_king_distance_to_enemy_decreases"],
                            },
                            {
                                "move_uci": "a6a5",
                                "move_shape_terms": ["candidate_is_rook_move"],
                                "post_move_terms": ["rook_safe_after_move"],
                            },
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    alignment_path = tmp_path / "alignment.json"
    alignment_path.write_text(
        json.dumps(
            {
                "labeled_candidate_frames": [
                    {
                        "move": "d1e2",
                        "child_dtm": 28,
                        "forces_mate": True,
                        "optimal_dtm_move": False,
                    },
                    {
                        "move": "a6a5",
                        "child_dtm": 26,
                        "forces_mate": True,
                        "optimal_dtm_move": True,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    model_path = tmp_path / "model.json"
    model_path.write_text(
        json.dumps(
            {
                "schema_version": "stage7_post_box_trajectory_provider_model.v1",
                "causal_status": "sandbox_model_non_promoted",
                "provider_skill_id": "krk.stage7_post_box_learned_continuation",
                "constraints": ["do_not_enable_by_default"],
                "runtime_forbidden_terms": [
                    "tablebase_lookup",
                    "dtm_oracle_move_selection",
                    "state_hash_exception",
                ],
                "bias": 0.0,
                "weights": {
                    "move_shape:candidate_is_king_move": 2.0,
                    "post_move:white_king_distance_to_enemy_decreases": 2.0,
                    "move_shape:candidate_is_rook_move": 0.5,
                },
            }
        ),
        encoding="utf-8",
    )

    payload = evaluator.evaluate_phase01(
        protocol_path=protocol_path,
        alignment_path=alignment_path,
        candidate_frames_path=frames_path,
        model_path=model_path,
    )

    assert payload["schema_version"] == "stage7_2cc_protocol_phase01_eval.v1"
    assert payload["causal_status"] == "non_causal"
    assert payload["runtime_behavior_changed"] is False
    assert payload["phase0_static_sanity"]["passed"] is True
    probe = payload["phase1_frozen_weight_probe"]
    assert probe["selected_move"] == "d1e2"
    assert probe["selected_forces_mate"] is True
    assert probe["selected_optimal_dtm_move"] is False
    assert probe["status"] == "frozen_model_selects_winning_nonoptimal_move"
    assert payload["candidate_status_update"]["promotion_status"] == (
        "sandbox_protocol_phase01_complete"
    )


def test_stage7_2cc_protocol_phase02_classifies_downstream_gap(tmp_path):
    script = ROOT / "scripts" / "evaluate_stage7_2cc_protocol_phase02.py"
    spec = importlib.util.spec_from_file_location("evaluate_stage7_2cc_protocol_phase02", script)
    assert spec is not None
    evaluator = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(evaluator)

    phase01_path = tmp_path / "phase01.json"
    phase01_path.write_text(
        json.dumps(
            {
                "phase1_frozen_weight_probe": {"selected_move": "d1e2"},
                "candidate_status_update": {
                    "candidate_id": "cand.krk.box_shrink.family_2cc.post_box_continuation_overlay.v1"
                },
            }
        ),
        encoding="utf-8",
    )
    alignment_path = tmp_path / "alignment.json"
    alignment_path.write_text(
        json.dumps(
            {
                "target_fen": FEN_2CC,
                "labeled_candidate_frames": [
                    {
                        "move": "d1e2",
                        "child_dtm": 28,
                        "forces_mate": True,
                        "optimal_dtm_move": False,
                    },
                    {
                        "move": "a6a5",
                        "child_dtm": 26,
                        "forces_mate": True,
                        "optimal_dtm_move": True,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    legal_first_path = tmp_path / "legal_first.json"
    legal_first_path.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "post_reply_fen": FEN_2CC,
                        "legal_first_probes": [
                            {"move": "d1e2", "horizon": 50, "result": "max_plies"},
                            {"move": "a6a5", "horizon": 50, "result": "max_plies"},
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    payload = evaluator.evaluate_phase02(
        phase01_path=phase01_path,
        alignment_path=alignment_path,
        legal_first_path=legal_first_path,
    )

    assert payload["schema_version"] == "stage7_2cc_protocol_phase02_replay_eval.v1"
    assert payload["causal_status"] == "non_causal"
    assert payload["runtime_behavior_changed"] is False
    assert payload["selected_move"] == "d1e2"
    assert payload["selected_move_dtm"]["forces_mate"] is True
    assert payload["selected_move_current_graph_replay"]["result"] == "max_plies"
    assert payload["diagnosis"] == (
        "visible_first_step_winning_but_current_graph_downstream_continuation_fails"
    )
    assert payload["candidate_status_update"]["promotion_status"] == (
        "sandbox_protocol_phase02_complete"
    )
