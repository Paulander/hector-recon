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

_trajectory_provider_spec = importlib.util.spec_from_file_location(
    "train_stage7_post_box_trajectory_provider",
    Path(__file__).resolve().parents[1] / "scripts" / "train_stage7_post_box_trajectory_provider.py",
)
assert _trajectory_provider_spec is not None
assert _trajectory_provider_spec.loader is not None
_trajectory_provider = importlib.util.module_from_spec(_trajectory_provider_spec)
_trajectory_provider_spec.loader.exec_module(_trajectory_provider)

_trajectory_expansion_spec = importlib.util.spec_from_file_location(
    "expand_stage7_post_box_dtm_trajectory_seed",
    Path(__file__).resolve().parents[1] / "scripts" / "expand_stage7_post_box_dtm_trajectory_seed.py",
)
assert _trajectory_expansion_spec is not None
assert _trajectory_expansion_spec.loader is not None
_trajectory_expansion = importlib.util.module_from_spec(_trajectory_expansion_spec)
_trajectory_expansion_spec.loader.exec_module(_trajectory_expansion)

_overlay_learner_spec = importlib.util.spec_from_file_location(
    "train_stage7_post_box_overlay_learner",
    Path(__file__).resolve().parents[1] / "scripts" / "train_stage7_post_box_overlay_learner.py",
)
assert _overlay_learner_spec is not None
assert _overlay_learner_spec.loader is not None
_overlay_learner = importlib.util.module_from_spec(_overlay_learner_spec)
_overlay_learner_spec.loader.exec_module(_overlay_learner)

_learnable_capsule_provider_spec = importlib.util.spec_from_file_location(
    "plan_stage7_post_box_learnable_capsule_provider",
    Path(__file__).resolve().parents[1] / "scripts" / "plan_stage7_post_box_learnable_capsule_provider.py",
)
assert _learnable_capsule_provider_spec is not None
assert _learnable_capsule_provider_spec.loader is not None
_learnable_capsule_provider = importlib.util.module_from_spec(_learnable_capsule_provider_spec)
_learnable_capsule_provider_spec.loader.exec_module(_learnable_capsule_provider)

_learnable_capsule_replay_spec = importlib.util.spec_from_file_location(
    "replay_stage7_learnable_capsule_provider",
    Path(__file__).resolve().parents[1] / "scripts" / "replay_stage7_learnable_capsule_provider.py",
)
assert _learnable_capsule_replay_spec is not None
assert _learnable_capsule_replay_spec.loader is not None
_learnable_capsule_replay = importlib.util.module_from_spec(_learnable_capsule_replay_spec)
_learnable_capsule_replay_spec.loader.exec_module(_learnable_capsule_replay)

_capsule_fidelity_spec = importlib.util.spec_from_file_location(
    "audit_stage7_capsule_trajectory_fidelity",
    Path(__file__).resolve().parents[1] / "scripts" / "audit_stage7_capsule_trajectory_fidelity.py",
)
assert _capsule_fidelity_spec is not None
assert _capsule_fidelity_spec.loader is not None
_capsule_fidelity = importlib.util.module_from_spec(_capsule_fidelity_spec)
_capsule_fidelity_spec.loader.exec_module(_capsule_fidelity)

_strategy_arbitration_spec = importlib.util.spec_from_file_location(
    "build_stage7_unified_strategy_arbitration_dataset",
    Path(__file__).resolve().parents[1] / "scripts" / "build_stage7_unified_strategy_arbitration_dataset.py",
)
assert _strategy_arbitration_spec is not None
assert _strategy_arbitration_spec.loader is not None
_strategy_arbitration = importlib.util.module_from_spec(_strategy_arbitration_spec)
_strategy_arbitration_spec.loader.exec_module(_strategy_arbitration)

_neutral_matrix_spec = importlib.util.spec_from_file_location(
    "summarize_stage7_neutral_diagnostic_matrix",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_stage7_neutral_diagnostic_matrix.py",
)
assert _neutral_matrix_spec is not None
assert _neutral_matrix_spec.loader is not None
_neutral_matrix = importlib.util.module_from_spec(_neutral_matrix_spec)
_neutral_matrix_spec.loader.exec_module(_neutral_matrix)

_evidence_merge_spec = importlib.util.spec_from_file_location(
    "summarize_stage7_evidence_merge_table",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_stage7_evidence_merge_table.py",
)
assert _evidence_merge_spec is not None
assert _evidence_merge_spec.loader is not None
_evidence_merge = importlib.util.module_from_spec(_evidence_merge_spec)
_evidence_merge_spec.loader.exec_module(_evidence_merge)

_training_benchmark_spec = importlib.util.spec_from_file_location(
    "benchmark_stage7_training_objectives",
    Path(__file__).resolve().parents[1] / "scripts" / "benchmark_stage7_training_objectives.py",
)
assert _training_benchmark_spec is not None
assert _training_benchmark_spec.loader is not None
_training_benchmark = importlib.util.module_from_spec(_training_benchmark_spec)
_training_benchmark_spec.loader.exec_module(_training_benchmark)


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
        index={},
        dtm=[],
    )

    assert step["schema_version"] == "stage7_post_box_dtm_trajectory_step.v1"
    assert step["target_skill"] == "krk.post_box_shrink_continuation"
    assert step["target_class"] == "dtm_trajectory_white_move"
    assert step["move"] == "a6a5"
    assert step["label"] == 1
    assert "dtm_oracle_move_selection" in step["runtime_forbidden_terms"]
    assert "state_hash_exception" in step["runtime_forbidden_terms"]


def test_stage7_post_box_trajectory_provider_model_is_sandbox_non_promoted(tmp_path):
    seed = {
        "schema_version": "stage7_post_box_dtm_trajectory_seed.v1",
        "trajectories": [
            {
                "white_training_steps": [
                    {
                        "fen": "8/8/R7/8/2k5/8/8/3K4 w - - 2 2",
                        "legal_move_labels": [
                            {
                                "move": "a6d6",
                                "label": 1,
                                "piece": "R",
                                "is_rook_move": True,
                                "coordinate_terms": ["piece.R", "delta_file_abs.3"],
                                "move_shape_terms": ["candidate_is_rook_move"],
                                "post_move_terms": ["box_area_decreases_after_move"],
                            },
                            {
                                "move": "a6a1",
                                "label": 0,
                                "piece": "R",
                                "is_rook_move": True,
                                "coordinate_terms": ["piece.R", "delta_rank_abs.5"],
                                "move_shape_terms": ["candidate_is_rook_move"],
                                "post_move_terms": [],
                            },
                        ],
                    }
                ]
            }
        ],
    }
    path = tmp_path / "seed.json"
    path.write_text(json.dumps(seed), encoding="utf-8")

    payload = _trajectory_provider.train_model(seed_path=path)

    assert payload["schema_version"] == "stage7_post_box_trajectory_provider_model.v1"
    assert payload["causal_status"] == "sandbox_model_non_promoted"
    assert payload["provider_skill_id"] == "krk.stage7_post_box_learned_continuation"
    assert payload["provider_version"] == "stage7_post_box_continuation_overlay_v1"
    assert payload["plan_capsule_id"] == "krk.post_box_shrink_continuation"
    assert payload["default_enabled"] is False
    assert payload["can_m4_consolidate"] is False
    assert "do_not_enable_by_default" in payload["constraints"]
    assert "dtm_oracle_move_selection" in payload["runtime_forbidden_terms"]
    assert payload["positive_count"] == 1
    assert payload["negative_count"] == 1


def test_stage7_dagger_seed_expansion_collects_failed_rollout_white_fens(monkeypatch):
    monkeypatch.setattr(_trajectory_expansion, "build_krk_dtm", lambda: (None, {}, []))
    monkeypatch.setattr(_trajectory_expansion, "_dtm_for_fen", lambda fen, index, dtm: 27)
    payloads = [
        {
            "schema_version": "stage7_learnable_capsule_provider_replay.v1",
            "records": [
                {
                    "result": "max_plies",
                    "trace": [
                        {
                            "ply": 0,
                            "turn": "white",
                            "fen": "8/8/R7/8/2k5/8/8/3K4 w - - 2 2",
                            "move": "a6a8",
                        },
                        {
                            "ply": 1,
                            "turn": "black",
                            "fen": "R7/8/8/8/2k5/8/8/3K4 b - - 3 2",
                            "move": "c4c3",
                        },
                    ],
                }
            ],
        }
    ]

    rows = _trajectory_expansion.collect_rollout_fens(
        replay_payloads=payloads,
        exclude_fens=set(),
        max_new_starts=4,
        max_start_dtm=40,
    )

    assert rows[0]["fen"] == "8/8/R7/8/2k5/8/8/3K4 w - - 2 2"
    assert rows[0]["source_result"] == "max_plies"
    assert rows[0]["state_dtm"] > 0


def test_stage7_overlay_learner_dtm_margin_reward_penalizes_dtm_gap():
    seed = {
        "trajectories": [
            {
                "white_training_steps": [
                    {
                        "fen": "8/8/R7/8/2k5/8/8/3K4 w - - 2 2",
                        "legal_move_labels": [
                            {
                                "move": "a6a5",
                                "label": 1,
                                "target_class": "optimal_dtm_move",
                                "child_dtm": 26,
                            },
                            {
                                "move": "a6a8",
                                "label": 0,
                                "target_class": "winning_nonoptimal_move",
                                "child_dtm": 30,
                            },
                        ],
                    }
                ]
            }
        ]
    }

    rows = _overlay_learner._transitions(
        seed,
        include_nonoptimal_winning_negatives=True,
        positive_reward=1.0,
        winning_nonoptimal_negative_reward=-0.35,
        non_winning_negative_reward=-1.0,
        reward_mode="dtm_margin",
        dtm_gap_scale=0.25,
    )
    rewards = {item.action: item.reward for item in rows}

    assert rewards["a6a5"] == 1.0
    assert rewards["a6a8"] == -1.0


def test_stage7_post_box_learnable_capsule_provider_plan_is_bounded_and_default_off(tmp_path):
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(
        json.dumps(
            {
                "schema_version": "stage7_post_box_dtm_trajectory_seed.v1",
                "trajectories": [
                    {
                        "white_training_steps": [
                            {"fen": "8/8/R7/8/2k5/8/8/3K4 w - - 2 2"},
                            {"fen": "8/8/8/R7/2k5/8/8/3K4 w - - 4 3"},
                        ]
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    summary_path = tmp_path / "training.json"
    summary_path.write_text(
        json.dumps(
            {
                "schema_version": "stage7_post_box_overlay_learner_training.v1",
                "causal_status": "offline_training_non_promoted",
                "provider_version": "stage7_post_box_continuation_overlay_v1",
                "plan_capsule_id": "krk.post_box_shrink_continuation",
                "transition_count": 12,
                "overlay_actuator_count": 4,
            }
        ),
        encoding="utf-8",
    )

    payload = _learnable_capsule_provider.build_plan(
        trajectory_seed_path=seed_path,
        overlay_training_summary_path=summary_path,
    )

    assert payload["schema_version"] == "stage7_post_box_learnable_capsule_provider_plan.v1"
    assert payload["causal_status"] == "non_causal"
    assert payload["runtime_behavior_changed"] is False
    provider = payload["provider"]
    assert provider["provider_skill_id"] == "krk.post_box_shrink_continuation"
    assert provider["provider_version"] == "stage7_post_box_continuation_overlay_v1"
    assert provider["plan_capsule_id"] == "krk.post_box_shrink_continuation"
    assert provider["default_enabled"] is False
    assert provider["causal_status"] == "sandbox_opt_in"
    assert provider["can_m3_update"] is True
    assert provider["can_m4_consolidate"] is False
    assert provider["ttl_white_moves"] == 4
    assert "learned_scoring_head" in provider["trainable_internal_components"]
    assert payload["candidate_local_training_protocol"]["m4_consolidation_enabled"] is False
    assert payload["candidate_local_training_protocol"]["runtime_dtm_or_tablebase_lookup"] is False
    assert "do_not_train_stage8" in payload["hard_constraints"]


def test_stage7_learnable_capsule_replay_extracts_unique_seed_start_fens():
    payload = {
        "trajectories": [
            {
                "white_training_steps": [
                    {
                        "fen": "8/8/R7/8/2k5/8/8/3K4 w - - 2 2",
                        "move": "a6a5",
                        "child_dtm": 26,
                    },
                    {
                        "fen": "8/8/8/R7/2k5/8/8/3K4 w - - 4 3",
                        "move": "d1e2",
                    },
                ]
            },
            {
                "white_training_steps": [
                    {
                        "fen": "8/8/R7/8/2k5/8/8/3K4 w - - 2 2",
                        "move": "a6d6",
                    }
                ]
            },
        ]
    }

    rows = _learnable_capsule_replay._seed_start_fens(payload)

    assert rows == [
        {
            "trajectory_index": 0,
            "fen": "8/8/R7/8/2k5/8/8/3K4 w - - 2 2",
            "dtm_step_count": 2,
            "first_dtm_move": "a6a5",
            "first_child_dtm": 26,
        }
    ]


def test_stage7_plan_capsule_default_state_owns_learnable_provider():
    state = _learnable_capsule_replay.diag._stage7_plan_capsule_default_state(ttl=4)

    assert "krk.post_box_shrink_continuation" in state["owned_providers"]
    assert state["ttl_white_moves"] == 4


def test_stage7_capsule_fidelity_closed_loop_diagnosis_splits_ranking_and_followup():
    step_by_fen = {
        "fen.bad": {
            "teacher_move": "a6a5",
            "positive_moves": ["a6a5"],
            "optimal_moves": ["a6a5"],
            "label_by_move": {
                "a6a8": {"target_class": "winning_nonoptimal_move", "label": 0, "child_dtm": 28}
            },
        },
        "fen.goodfirst": {
            "teacher_move": "d2c3",
            "positive_moves": ["a5h5"],
            "optimal_moves": ["d2c3", "a5h5"],
            "label_by_move": {
                "a5h5": {"target_class": "optimal_dtm_move", "label": 1, "child_dtm": 24}
            },
        },
    }
    records = _capsule_fidelity._closed_loop_records(
        replay_payloads=[
            {
                "schema_version": "stage7_learnable_capsule_provider_replay.v1",
                "records": [
                    {"start_fen": "fen.bad", "selected_move": "a6a8", "result": "max_plies"},
                    {"start_fen": "fen.goodfirst", "selected_move": "a5h5", "result": "max_plies"},
                ],
            }
        ],
        step_by_fen=step_by_fen,
    )

    diagnoses = _capsule_fidelity._diagnosis_by_family(records)

    assert diagnoses[0]["diagnosis"] == "teacher_fidelity_ranking_gap"
    assert diagnoses[1]["diagnosis"] == "closed_loop_compounding_or_followup_policy_gap"


def test_stage7_capsule_fidelity_top_level_flags_top1_ranking_gap_before_compounding():
    diagnosis, next_action = _capsule_fidelity._top_level_diagnosis(
        accuracy={
            "dtm_positive_top1_rate": 0.28,
            "dtm_positive_top3_rate": 0.80,
        },
        closed_loop=[
            {"result": "max_plies", "selected_is_dtm_positive": False},
            {"result": "max_plies", "selected_is_dtm_positive": False},
        ],
    )

    assert diagnosis == "trajectory_ranking_and_closed_loop_gap"
    assert "ranked_imitation" in next_action


def test_stage7_unified_strategy_arbitration_provider_ranks_and_relevance():
    rows = _strategy_arbitration._provider_ranked_suggestions(
        [
            {"skill_id": "krk.stage0_basin", "move": "a1a2", "score": 10.0},
            {"skill_id": "krk.stage0_basin", "move": "a1a3", "score": 5.0},
            {"skill_id": "krk.drive_to_edge", "move": "d1d2", "score": 0.2},
        ],
        {"krk.stage0_basin", "krk.drive_to_edge"},
    )

    by_move = {item["move"]: item for item in rows}
    assert by_move["a1a2"]["provider_local_rank"] == 1
    assert by_move["a1a3"]["provider_local_rank"] == 2
    assert by_move["a1a2"]["provider_local_normalized_score"] == 1.0
    assert by_move["a1a3"]["provider_local_normalized_score"] == 0.0
    assert _strategy_arbitration._box_area_relevance({"enemy_edge_distance": 0, "box_area": 30}) == "low"
    assert _strategy_arbitration._box_area_relevance({"enemy_edge_distance": 2, "box_area": 20}) == "high"


def test_stage7_unified_strategy_arbitration_probe_detects_normalized_shortlist_advantage():
    dataset = {
        "state_count": 1,
        "records": [
            {
                "state_id": "state.demo",
                "board_features": {
                    "box_area_relevance": "low",
                    "black_king_edge_distance": 0,
                    "fence_exists": False,
                    "king_support": True,
                },
                "suggestions": [
                    {
                        "provider_id": "krk.stage0_basin",
                        "move": "a1a2",
                        "raw_score": 10.0,
                        "provider_local_rank": 1,
                        "playout_label": {"result": "max_plies"},
                    },
                    {
                        "provider_id": "krk.edge_trap_close",
                        "move": "h7h8",
                        "raw_score": 0.1,
                        "provider_local_rank": 1,
                        "playout_label": {"result": "mate"},
                    },
                ],
            }
        ],
    }

    probe = _strategy_arbitration.run_probe(dataset)

    assert probe["raw_global_top_conversion_rate"] == 0.0
    assert probe["provider_local_rank1_oracle_coverage"] == 1.0
    assert probe["answers"]["provider_local_normalization_outperforms_raw_global_score"] is True
    assert probe["answers"]["failures_suggest_box_or_stage0_over_ownership"] is True


def test_stage7_neutral_diagnostic_matrix_keeps_all_hypotheses_non_causal(tmp_path):
    (tmp_path / "stage7_post_box_family_diagnosis.json").write_text(
        json.dumps(
            {
                "family_diagnosis_counts": {
                    "existing_provider_can_convert_if_family_role_selects_it": 2,
                    "unresolved_by_existing_forced_providers_at_h80": 2,
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "stage7_expanded_ranked_capsule_trajectory_fidelity_audit.json").write_text(
        json.dumps(
            {
                "teacher_forced_accuracy": {
                    "dtm_positive_top1_rate": 0.36,
                    "dtm_positive_top3_rate": 0.80,
                },
                "top_level_diagnosis": "trajectory_ranking_and_closed_loop_gap",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "stage7_unified_strategy_arbitration_probe.json").write_text(
        json.dumps(
            {
                "dataset_state_count": 3,
                "labeled_state_count": 3,
                "raw_global_top_conversion_rate": 0.0,
                "provider_local_rank1_oracle_coverage": 0.0,
                "box_area_relevance_outcome_counts": {"high:any_mate=False": 3},
                "answers": {
                    "provider_selection_model_predicts_converting_provider": False,
                    "provider_local_normalization_outperforms_raw_global_score": False,
                    "box_area_relevance_explains_some_failures": False,
                    "failures_suggest_box_or_stage0_over_ownership": False,
                },
            }
        ),
        encoding="utf-8",
    )

    matrix = _neutral_matrix.build_matrix(tmp_path)

    assert matrix["schema_version"] == "stage7_neutral_diagnostic_matrix.v1"
    assert matrix["causal_status"] == "non_causal"
    assert matrix["runtime_behavior_changed"] is False
    assert matrix["stage7_status"] == "local_valid_composition_quarantined"
    assert len(matrix["hypotheses"]) == 5
    assert all(item["next_test_causal_status"] == "non_causal" for item in matrix["hypotheses"])
    assert {item["confidence"] for item in matrix["hypotheses"]} <= {"low", "medium", "high"}
    assert "repair" not in matrix["current_best_interpretation"]["next_proposed_step"].lower()


def test_stage7_neutral_diagnostic_markdown_names_current_best_interpretation(tmp_path):
    matrix = _neutral_matrix.build_matrix(tmp_path)
    markdown = _neutral_matrix.render_markdown(matrix)

    assert "# Stage 7 Neutral Diagnostic Matrix" in markdown
    assert "## Current Best Interpretation" in markdown
    assert "Training-objective / model-expression issue" in markdown
    assert "No runtime behavior" not in markdown


def test_stage7_evidence_merge_table_combines_family_dtm_and_fidelity_rows(tmp_path):
    (tmp_path / "stage7_post_box_family_diagnosis.json").write_text(
        json.dumps(
            {
                "families": [
                    {
                        "family_id": "stage7.post_box.family_ff",
                        "state_id": "state.ff",
                        "post_reply_fen": "8/8/8/8/4R3/2k5/4K3/8 w - - 2 2",
                        "selected_successor": "krk.stage0_basin",
                        "selected_move": "e4e8",
                        "conversion_result": "max_plies",
                        "failure_classes": ["selected_successor_miscalibrated"],
                        "visible_terms": {"current_terms": ["rook_safe", "box_area_large"]},
                        "forced_provider_results": {
                            "krk.drive_to_edge": {
                                "result": "mate",
                                "plies": 7,
                                "first_move": "e4h4",
                                "horizon": 40,
                            },
                            "krk.stage0_basin": {
                                "result": "max_plies",
                                "plies": 40,
                                "first_move": "e4e8",
                                "horizon": 40,
                            },
                        },
                        "diagnosis": "existing_provider_can_convert_if_family_role_selects_it",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "stage7_remaining_dtm_candidate_summary.json").write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "candidate_id": "cand.demo",
                        "state_id": "state.dtm",
                        "post_reply_fen": "8/8/R7/8/2k5/8/8/3K4 w - - 2 2",
                        "diagnosis": "dtm_won_within_validation_horizon_but_current_continuation_failed",
                        "dtm": {
                            "state_dtm": 27,
                            "best_dtm_plies": 27,
                            "winning_move_count": 19,
                            "legal_move_count": 19,
                            "best_moves": [{"move": "a6a5"}],
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "stage7_expanded_ranked_capsule_trajectory_fidelity_audit.json").write_text(
        json.dumps(
            {
                "teacher_forced_accuracy": {
                    "teacher_move_top1_rate": 0.2,
                    "dtm_positive_top1_rate": 0.36,
                    "dtm_positive_top3_rate": 0.8,
                },
                "top_level_diagnosis": "trajectory_ranking_and_closed_loop_gap",
                "closed_loop_records": [
                    {
                        "start_fen": "8/8/R7/8/2k5/8/8/3K4 w - - 2 2",
                        "result": "max_plies",
                        "plies": 40,
                        "selected_skill": "krk.post_box_shrink_continuation",
                        "selected_move": "a6a8",
                        "selected_is_dtm_positive": False,
                        "teacher_move": "a6a5",
                        "first_divergence": {"ply": 0},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    merge = _evidence_merge.build_evidence_merge(tmp_path)

    assert merge["schema_version"] == "stage7_evidence_merge_table.v1"
    assert merge["causal_status"] == "non_causal"
    assert merge["runtime_behavior_changed"] is False
    assert merge["stage7_promotion_allowed"] is False
    assert merge["stage8_training_allowed"] is False
    assert merge["summary"]["row_count"] == 2
    label_counts = merge["summary"]["hypothesis_label_counts"]
    assert label_counts["already_solved_by_existing_provider_if_arbitrated"] == 1
    assert label_counts["training_objective_model_expression_candidate"] == 1
    assert any(
        row["strategy_provider_evidence"]["best_forced_provider"]
        and row["strategy_provider_evidence"]["best_forced_provider"]["provider"] == "krk.drive_to_edge"
        for row in merge["rows"]
    )


def test_stage7_decision_gate_prefers_training_objective_benchmark_for_current_evidence(tmp_path):
    merge = {
        "schema_version": "stage7_evidence_merge_table.v1",
        "causal_status": "non_causal",
        "runtime_behavior_changed": False,
        "stage7_status": "local_valid_composition_quarantined",
        "stage8_training_allowed": False,
        "stage7_promotion_allowed": False,
        "rows": [],
        "summary": {
            "row_count": 5,
            "hypothesis_label_counts": {
                "training_objective_model_expression_candidate": 3,
                "continuation_capacity_candidate": 2,
                "missing_feature_candidate": 1,
            },
            "m3_trainability_summary": {
                "probe_result": "scripted_provider_selected_but_not_trainable_for_move_policy"
            },
            "arbitration_probe_answers": {
                "provider_local_normalization_outperforms_raw_global_score": False
            },
        },
    }

    gate = _evidence_merge.build_decision_gate(merge)

    assert gate["schema_version"] == "stage7_decision_gate.v1"
    assert gate["causal_status"] == "non_causal"
    assert gate["selected_status"] == "proceed_to_training_objective_benchmark"
    assert gate["stage7_promotion_allowed"] is False
    assert gate["stage8_training_allowed"] is False
    assert "offline-only" in gate["minimum_next_step"].lower()
    assert "do not compile a runtime repair" in gate["minimum_next_step"].lower()
    assert "train_stage8" in gate["blocked_next_steps"]


def test_stage7_training_objective_benchmark_is_non_causal_and_compares_required_models(tmp_path):
    seed = {
        "schema_version": "stage7_post_box_dtm_trajectory_seed.v1",
        "trajectory_count": 2,
        "trajectories": [
            {
                "white_training_steps": [
                    {
                        "fen": "8/8/R7/8/2k5/8/8/3K4 w - - 2 2",
                        "move": "a6a5",
                        "legal_move_labels": [
                            {
                                "move": "a6a5",
                                "label": 1,
                                "target_class": "optimal_dtm_move",
                                "child_dtm": 26,
                                "piece": "R",
                                "move_shape_terms": ["candidate_is_rook_move"],
                                "post_move_terms": ["box_area_decreases_after_move", "rook_safe_after_move"],
                            },
                            {
                                "move": "a6a8",
                                "label": 0,
                                "target_class": "winning_nonoptimal_move",
                                "child_dtm": 28,
                                "piece": "R",
                                "move_shape_terms": ["candidate_is_rook_move"],
                                "post_move_terms": ["rook_safe_after_move"],
                            },
                        ],
                    }
                ]
            },
            {
                "white_training_steps": [
                    {
                        "fen": "8/8/8/R7/4k3/8/3K4/8 w - - 2 2",
                        "move": "d2c3",
                        "legal_move_labels": [
                            {
                                "move": "d2c3",
                                "label": 1,
                                "target_class": "optimal_dtm_move",
                                "child_dtm": 20,
                                "piece": "K",
                                "move_shape_terms": ["candidate_is_king_move", "king_moves_toward_enemy"],
                                "post_move_terms": ["white_king_distance_to_enemy_decreases", "rook_safe_after_move"],
                            },
                            {
                                "move": "a5h5",
                                "label": 0,
                                "target_class": "winning_nonoptimal_move",
                                "child_dtm": 24,
                                "piece": "R",
                                "move_shape_terms": ["candidate_is_rook_move"],
                                "post_move_terms": ["rook_safe_after_move"],
                            },
                            {
                                "move": "a5a1",
                                "label": 0,
                                "target_class": "non_winning_move",
                                "child_dtm": -1,
                                "piece": "R",
                                "move_shape_terms": ["candidate_is_rook_move"],
                                "post_move_terms": ["rook_safe_after_move"],
                            },
                        ],
                    }
                ]
            },
        ],
    }
    fidelity = {
        "teacher_forced_records": [
            {
                "trajectory_index": 0,
                "step_index": 0,
                "fen": "8/8/R7/8/2k5/8/8/3K4 w - - 2 2",
                "top_moves": [
                    {"move": "a6a8", "label": 0, "target_class": "winning_nonoptimal_move", "score": 1.0},
                    {"move": "a6a5", "label": 1, "target_class": "optimal_dtm_move", "score": 0.5},
                ],
                "positive_move_rank": 2,
                "optimal_move_rank": 2,
            },
            {
                "trajectory_index": 1,
                "step_index": 0,
                "fen": "8/8/8/R7/4k3/8/3K4/8 w - - 2 2",
                "top_moves": [
                    {"move": "d2c3", "label": 1, "target_class": "optimal_dtm_move", "score": 1.0},
                    {"move": "a5h5", "label": 0, "target_class": "winning_nonoptimal_move", "score": 0.5},
                ],
                "positive_move_rank": 1,
                "optimal_move_rank": 1,
            },
        ]
    }
    (tmp_path / "stage7_post_box_dtm_trajectory_seed_expanded_h40.json").write_text(
        json.dumps(seed), encoding="utf-8"
    )
    (tmp_path / "stage7_expanded_ranked_capsule_trajectory_fidelity_audit.json").write_text(
        json.dumps(fidelity), encoding="utf-8"
    )

    benchmark = _training_benchmark.build_benchmark(tmp_path)

    assert benchmark["schema_version"] == "stage7_training_objective_benchmark.v1"
    assert benchmark["causal_status"] == "non_causal_offline_benchmark"
    assert benchmark["runtime_behavior_changed"] is False
    assert benchmark["runtime_dtm_or_tablebase_lookup"] is False
    assert benchmark["stage7_promotion_allowed"] is False
    assert benchmark["stage8_training_allowed"] is False
    model_ids = {model["model_id"] for model in benchmark["models"]}
    assert "current_learned_post_box_scorer" in model_ids
    assert "visible_term_log_odds_scorer" in model_ids
    assert "pairwise_ranked_preference_scorer" in model_ids
    assert "heuristic_safety_non_draw_rook_safe" in model_ids
    assert "oracle_dtm_positive_topk_ceiling" in model_ids
    assert benchmark["decision"]["candidate_status"] in {
        "training_objective_benchmark_supports_ranked_sequence_policy",
        "model_expression_gap_not_solved_by_simple_ranking",
        "missing_feature_or_ontology_candidate",
        "ranking_calibration_gap",
        "continuation_capacity_or_harness_gap",
    }


def test_stage7_training_benchmark_tie_breaks_without_label_leakage():
    labels = [
        {"move": "b1b2", "label": 1, "target_class": "optimal_dtm_move"},
        {"move": "a1a2", "label": 0, "target_class": "winning_nonoptimal_move"},
    ]

    ranked = _training_benchmark._rank_labels(labels, lambda _label: 0.0)

    assert [item["move"] for item in ranked] == ["a1a2", "b1b2"]
