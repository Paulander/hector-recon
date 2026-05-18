#!/usr/bin/env python3
"""Tests for the non-causal Stage 7 plan capsule artifact helpers."""

import importlib.util
import json
from pathlib import Path

from recon_lite_chess.routing import PlanCapsuleSpec, StructuralCandidate


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "audit_stage7_post_box_plan_capsule.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("audit_stage7_post_box_plan_capsule", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_plan_capsule_candidate_export_is_non_causal():
    module = _load_script_module()
    payload = module.build_plan_capsule_candidate(evidence_artifacts=["stage7.json"])

    assert payload["schema_version"] == "plan_capsule_candidate.v1"
    assert payload["causal_status"] == "non_causal"
    assert payload["promotion_status"] == "proposed"
    assert payload["candidate_id"] == "cand.krk.box_shrink.post_box_continuation_capsule.v1"

    capsule = PlanCapsuleSpec.from_dict(json.loads(json.dumps(payload["plan_capsule"])))
    candidate = StructuralCandidate.from_dict(json.loads(json.dumps(payload["structural_candidate"])))

    assert capsule.schema_version == "plan_capsule_spec.v1"
    assert capsule.capsule_id == "krk.post_box_shrink_continuation"
    assert capsule.causal_status == "non_causal"
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
