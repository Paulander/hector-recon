import importlib.util
import json
from pathlib import Path


_summary_spec = importlib.util.spec_from_file_location(
    "summarize_stage7_unresolved_legal_first",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_stage7_unresolved_legal_first.py",
)
assert _summary_spec is not None
assert _summary_spec.loader is not None
_summary = importlib.util.module_from_spec(_summary_spec)
_summary_spec.loader.exec_module(_summary)

_dtm_summary_spec = importlib.util.spec_from_file_location(
    "summarize_stage7_dtm_oracle",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_stage7_dtm_oracle.py",
)
assert _dtm_summary_spec is not None
assert _dtm_summary_spec.loader is not None
_dtm_summary = importlib.util.module_from_spec(_dtm_summary_spec)
_dtm_summary_spec.loader.exec_module(_dtm_summary)

_training_seed_spec = importlib.util.spec_from_file_location(
    "build_stage7_post_box_training_seed",
    Path(__file__).resolve().parents[1] / "scripts" / "build_stage7_post_box_training_seed.py",
)
assert _training_seed_spec is not None
assert _training_seed_spec.loader is not None
_training_seed = importlib.util.module_from_spec(_training_seed_spec)
_training_seed_spec.loader.exec_module(_training_seed)

_m3_trainability_spec = importlib.util.spec_from_file_location(
    "assess_stage7_post_box_m3_trainability",
    Path(__file__).resolve().parents[1] / "scripts" / "assess_stage7_post_box_m3_trainability.py",
)
assert _m3_trainability_spec is not None
assert _m3_trainability_spec.loader is not None
_m3_trainability = importlib.util.module_from_spec(_m3_trainability_spec)
_m3_trainability_spec.loader.exec_module(_m3_trainability)

_trajectory_seed_spec = importlib.util.spec_from_file_location(
    "build_stage7_post_box_dtm_trajectory_seed",
    Path(__file__).resolve().parents[1] / "scripts" / "build_stage7_post_box_dtm_trajectory_seed.py",
)
assert _trajectory_seed_spec is not None
assert _trajectory_seed_spec.loader is not None
_trajectory_seed = importlib.util.module_from_spec(_trajectory_seed_spec)
_trajectory_seed_spec.loader.exec_module(_trajectory_seed)


def test_stage7_unresolved_legal_first_summary_marks_selection_gap_and_capacity_probe(tmp_path):
    probe = {
        "records": [
            {
                "state_id": "state.actiongap",
                "post_reply_fen": "8/8/8/8/4K3/4R3/3k4/8 w - - 2 2",
                "diagnosis": "unresolved_by_existing_forced_providers_at_h80",
                "legal_first_probes": [
                    {
                        "move": "e4d4",
                        "horizon": 40,
                        "result": "mate",
                        "plies": 5,
                        "move_shape_audit": {
                            "move_shape_terms": ["candidate_is_king_move"],
                            "post_move_terms": ["rook_safe_after_move"],
                            "current_terms": ["rook_safe"],
                        },
                    }
                ],
            },
            {
                "state_id": "state.capacity",
                "post_reply_fen": "8/8/8/R7/4k3/8/8/3K4 w - - 2 2",
                "diagnosis": "unresolved_by_existing_forced_providers_at_h80",
                "legal_first_probes": [
                    {"move": "a5a1", "horizon": 50, "result": "max_plies", "plies": 50}
                ],
            },
        ]
    }
    path = tmp_path / "probe.json"
    path.write_text(json.dumps(probe), encoding="utf-8")

    payload = _summary.summarize([path])

    assert payload["causal_status"] == "non_causal"
    assert payload["diagnosis_counts"] == {
        "legal_first_action_selection_gap": 1,
        "no_legal_first_conversion_under_current_graph": 1,
    }
    candidates = {item["state_id"]: item for item in payload["candidates"]}
    assert candidates["state.actiongap"]["promotion_status"] == "sandbox_ready_if_terms_separate"
    assert candidates["state.actiongap"]["proposed_change"]["kind"] == "visible_move_shape_role_candidate"
    assert candidates["state.actiongap"]["legal_first_mating_moves"][0]["move"] == "e4d4"
    assert candidates["state.capacity"]["promotion_status"] == "needs_longer_horizon_or_new_provider_probe"
    assert candidates["state.capacity"]["proposed_change"]["max_tested_horizon"] == 50


def test_stage7_dtm_oracle_summary_marks_won_unresolved_family_as_overlay_probe(tmp_path):
    oracle = {
        "schema_version": "krk_dtm_oracle_probe.v1",
        "causal_status": "non_causal_diagnostic",
        "records": [
            {
                "fen": "8/8/8/R7/4k3/8/3K4/8 w - - 2 2",
                "state_dtm": 21,
                "winning_move_count": 17,
                "legal_move_count": 20,
                "best_winning_moves": [
                    {
                        "move": "d2c3",
                        "plies_to_mate_if_chosen": 21,
                        "is_check": False,
                    }
                ],
            }
        ],
    }
    path = tmp_path / "dtm.json"
    path.write_text(json.dumps(oracle), encoding="utf-8")

    payload = _dtm_summary.summarize_dtm_oracle(
        oracle_path=path,
        validation_horizon=40,
        evidence_artifacts=["stage7_unresolved_legal_first_summary.json"],
    )

    assert payload["causal_status"] == "non_causal"
    assert payload["diagnosis_counts"] == {
        "dtm_won_within_validation_horizon_but_current_continuation_failed": 1
    }
    candidate = payload["candidates"][0]
    assert candidate["schema_version"] == "structural_candidate.v1"
    assert candidate["causal_status"] == "non_causal"
    assert candidate["credit"] == 0.0
    assert candidate["governor_status"] == "growth_allowed"
    assert candidate["promotion_status"] == "proposed"
    assert candidate["candidate_type"] == "post_box_continuation_overlay_probe"
    assert candidate["proposed_change"]["do_not_use_tablebase_at_runtime"] is True
    assert candidate["dtm"]["best_moves"][0]["move"] == "d2c3"


def test_stage7_post_box_training_seed_is_non_causal_offline_supervision(tmp_path):
    oracle = {
        "schema_version": "krk_dtm_oracle_probe.v1",
        "causal_status": "non_causal_diagnostic",
        "records": [
            {
                "fen": "8/8/8/R7/4k3/8/3K4/8 w - - 2 2",
                "state_dtm": 21,
                "best_winning_moves": [
                    {
                        "move": "d2c3",
                        "plies_to_mate_if_chosen": 21,
                        "is_check": False,
                    }
                ],
                "legal_moves": [
                    {
                        "move": "d2c3",
                        "forces_mate": True,
                        "plies_to_mate_if_chosen": 21,
                        "is_check": False,
                    },
                    {
                        "move": "a5a4",
                        "forces_mate": False,
                        "dtm_after_move": -1,
                        "is_check": False,
                    },
                ],
            }
        ],
    }
    path = tmp_path / "dtm.json"
    path.write_text(json.dumps(oracle), encoding="utf-8")

    payload = _training_seed.build_training_seed(oracle_path=path, horizon=40)

    assert payload["schema_version"] == "stage7_post_box_training_seed.v1"
    assert payload["causal_status"] == "non_causal_training_evidence"
    assert "do_not_use_dtm_or_tablebase_at_runtime" in payload["constraints"]
    example = payload["examples"][0]
    assert example["target_skill"] == "krk.post_box_shrink_continuation"
    assert example["positive_moves"][0]["move"] == "d2c3"
    assert example["positive_moves"][0]["target_class"] == "optimal_dtm_move"
    labels = {item["move"]: item["label"] for item in example["legal_move_labels"]}
    assert labels["d2c3"] == 1
    assert labels["a5a4"] == 0
    assert "tablebase_lookup" in example["runtime_forbidden_terms"]


def test_stage7_post_box_m3_trainability_blocks_scripted_provider_without_internal_edges(tmp_path):
    topology = {
        "nodes": {
            "krk_hub": {"id": "krk_hub", "type": "SCRIPT", "meta": {}},
            "terminal.krk.stage7_post_box_continuation": {
                "id": "terminal.krk.stage7_post_box_continuation",
                "type": "TERMINAL",
                "meta": {
                    "role_id": "krk.post_box_shrink_continuation",
                    "provider_skill_id": "krk.stage7_post_box_continuation",
                    "stage7_post_box_continuation_provider": True,
                    "overlay_provider": True,
                    "can_m3_update": True,
                },
            },
        },
        "edges": [
            {
                "src": "krk_hub",
                "dst": "terminal.krk.stage7_post_box_continuation",
                "type": "SUB",
                "weight": 1.0,
            }
        ],
    }
    diagnostic = {
        "handoff_packets": [
            {
                "phase": "post_opponent_reply",
                "packet_id": "packet.1",
                "evidence_terms": {
                    "post_reply_fen": "8/8/R7/8/2k5/8/8/3K4 w - - 2 2",
                    "post_reply_state_signature": "state.2cc0b3e1033a",
                    "successor_selected_skill": "krk.stage7_post_box_continuation",
                    "playout_result": "max_plies",
                    "successor_skills": {
                        "krk.stage7_post_box_continuation": {
                            "visible_stage7_post_box_continuation_license": {
                                "move": "a6d6",
                                "source_terms": ["box_area_decreases_after_move"],
                            }
                        }
                    },
                },
            }
        ]
    }
    topology_path = tmp_path / "topology.json"
    diagnostic_path = tmp_path / "diagnostic.json"
    topology_path.write_text(json.dumps(topology), encoding="utf-8")
    diagnostic_path.write_text(json.dumps(diagnostic), encoding="utf-8")

    payload = _m3_trainability.assess_stage7_post_box_m3_trainability(
        topology_path=topology_path,
        diagnostic_path=diagnostic_path,
    )

    assert payload["causal_status"] == "non_causal"
    assert payload["probe_result"] == "scripted_provider_selected_but_not_trainable_for_move_policy"
    assert payload["recommended_next_action"] == "train_or_compile_learned_candidate_provider_before_m3_warmup"
    assert payload["trainable_internal_edge_count"] == 0
    assert payload["activation_edge_count"] == 1
    assert "do_not_promote_stage7" in payload["safety"]["hard_blocks"]


def test_stage7_post_box_dtm_trajectory_step_is_non_causal_training_evidence():
    import chess

    board = chess.Board("8/8/R7/8/2k5/8/8/3K4 w - - 2 2")
    step = _trajectory_seed._white_training_step(
        board,
        chess.Move.from_uci("a6a5"),
        child_dtm=26,
        ply_index=0,
    )

    assert step["schema_version"] == "stage7_post_box_dtm_trajectory_step.v1"
    assert step["target_skill"] == "krk.post_box_shrink_continuation"
    assert step["target_class"] == "dtm_trajectory_white_move"
    assert step["move"] == "a6a5"
    assert step["label"] == 1
    assert "dtm_oracle_move_selection" in step["runtime_forbidden_terms"]
    assert "state_hash_exception" in step["runtime_forbidden_terms"]
