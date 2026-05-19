import importlib.util
import json
from pathlib import Path


_dataset_spec = importlib.util.spec_from_file_location(
    "build_krk_strategy_arbitration_dataset",
    Path(__file__).resolve().parents[1] / "scripts" / "build_krk_strategy_arbitration_dataset.py",
)
assert _dataset_spec is not None
assert _dataset_spec.loader is not None
_dataset = importlib.util.module_from_spec(_dataset_spec)
_dataset_spec.loader.exec_module(_dataset)

_probe_spec = importlib.util.spec_from_file_location(
    "probe_krk_strategy_arbitration",
    Path(__file__).resolve().parents[1] / "scripts" / "probe_krk_strategy_arbitration.py",
)
assert _probe_spec is not None
assert _probe_spec.loader is not None
_probe = importlib.util.module_from_spec(_probe_spec)
_probe_spec.loader.exec_module(_probe)

_challenge_manifest_spec = importlib.util.spec_from_file_location(
    "summarize_stage7_challenge_set_manifest",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_stage7_challenge_set_manifest.py",
)
assert _challenge_manifest_spec is not None
assert _challenge_manifest_spec.loader is not None
_challenge_manifest = importlib.util.module_from_spec(_challenge_manifest_spec)
_challenge_manifest_spec.loader.exec_module(_challenge_manifest)

_decision_gate_spec = importlib.util.spec_from_file_location(
    "summarize_krk_strategy_arbitration_decision_gate",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_strategy_arbitration_decision_gate.py",
)
assert _decision_gate_spec is not None
assert _decision_gate_spec.loader is not None
_decision_gate = importlib.util.module_from_spec(_decision_gate_spec)
_decision_gate_spec.loader.exec_module(_decision_gate)

_missing_feature_audit_spec = importlib.util.spec_from_file_location(
    "audit_krk_strategy_missing_features",
    Path(__file__).resolve().parents[1] / "scripts" / "audit_krk_strategy_missing_features.py",
)
assert _missing_feature_audit_spec is not None
assert _missing_feature_audit_spec.loader is not None
_missing_feature_audit = importlib.util.module_from_spec(_missing_feature_audit_spec)
_missing_feature_audit_spec.loader.exec_module(_missing_feature_audit)

_feature_validation_spec = importlib.util.spec_from_file_location(
    "validate_krk_feature_candidates",
    Path(__file__).resolve().parents[1] / "scripts" / "validate_krk_feature_candidates.py",
)
assert _feature_validation_spec is not None
assert _feature_validation_spec.loader is not None
_feature_validation = importlib.util.module_from_spec(_feature_validation_spec)
_feature_validation_spec.loader.exec_module(_feature_validation)

_monitor_records_spec = importlib.util.spec_from_file_location(
    "extract_krk_strategy_monitor_records",
    Path(__file__).resolve().parents[1] / "scripts" / "extract_krk_strategy_monitor_records.py",
)
assert _monitor_records_spec is not None
assert _monitor_records_spec.loader is not None
_monitor_records = importlib.util.module_from_spec(_monitor_records_spec)
_monitor_records_spec.loader.exec_module(_monitor_records)

_companion_audit_spec = importlib.util.spec_from_file_location(
    "audit_krk_strategy_monitor_companion_terms",
    Path(__file__).resolve().parents[1] / "scripts" / "audit_krk_strategy_monitor_companion_terms.py",
)
assert _companion_audit_spec is not None
assert _companion_audit_spec.loader is not None
_companion_audit = importlib.util.module_from_spec(_companion_audit_spec)
_companion_audit_spec.loader.exec_module(_companion_audit)

_visible_monitor_terms_spec = importlib.util.spec_from_file_location(
    "extract_krk_visible_monitor_terms",
    Path(__file__).resolve().parents[1] / "scripts" / "extract_krk_visible_monitor_terms.py",
)
assert _visible_monitor_terms_spec is not None
assert _visible_monitor_terms_spec.loader is not None
_visible_monitor_terms = importlib.util.module_from_spec(_visible_monitor_terms_spec)
_visible_monitor_terms_spec.loader.exec_module(_visible_monitor_terms)


def test_strategy_proposal_frame_validation_roundtrip():
    frame = {
        "schema_version": "strategy_proposal_frame.v1",
        "state_id": "state.test",
        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
        "active_landmark_label": "box_shrink",
        "provider_id": "krk.box_shrink",
        "skill_id": "krk.box_shrink",
        "provider_version": "test",
        "move_uci": "a1a2",
        "raw_score": 0.5,
        "provider_local_rank": 1,
        "normalized_score": 1.0,
        "source_terms": ["box_area_relevance"],
        "role_licenses": [],
        "plan_capsule_context": {},
        "move_shape_terms": ["candidate_is_rook_move"],
        "post_move_terms": ["rook_safe_after_move"],
        "safety_terms": ["rook_safe_after_move"],
        "known_outcome_label": {"result": "mate"},
        "shadow_failure_labels": [],
        "causal_status": "non_causal",
    }

    _dataset.validate_strategy_proposal_frame(json.loads(json.dumps(frame)))


def test_krk_strategy_arbitration_dataset_v0_from_stage7_merge(tmp_path):
    root = tmp_path
    structural = root / "reports" / "structural_candidates"
    structural.mkdir(parents=True)
    (structural / "stage7_evidence_merge_table.json").write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "state_identity": {
                            "state_signature": "state.sample",
                            "post_reply_fen": "8/8/8/R7/4k3/8/3K4/8 w - - 2 2",
                            "source_artifacts": ["stage7_sample.json"],
                            "sample_support_count": 1,
                        },
                        "terminal_space_context": {
                            "black_king_edge_distance": 3,
                            "black_king_edge_bucket": "central_or_midboard",
                            "box_area": 28,
                            "box_area_relevance": "high",
                            "rook_safe": True,
                            "fence_cut_status": "fence_or_cut_not_preserved",
                            "king_support_status": "support_can_improve",
                            "mate_in_one_available": False,
                            "active_terminal_terms": ["rook_safe"],
                        },
                        "strategy_provider_evidence": {
                            "provider_local_rank_info": [
                                {
                                    "provider_id": "krk.stage0_basin",
                                    "move": "a5h5",
                                    "raw_score": 13.0,
                                    "provider_local_rank": 1,
                                    "provider_local_normalized_score": 1.0,
                                }
                            ],
                            "forced_provider_results": {
                                "krk.drive_to_edge": {
                                    "first_move": "a5b5",
                                    "result": "mate",
                                    "plies": 9,
                                    "horizon": 40,
                                }
                            },
                        },
                        "continuation_evidence": {"current_graph_result_h40": "max_plies"},
                        "hypothesis_labels": ["strategy_arbitration_candidate"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    dataset = _dataset.build_dataset(root)

    assert dataset["schema_version"] == "krk_strategy_arbitration_dataset.v0"
    assert dataset["causal_status"] == "non_causal_dataset"
    assert dataset["runtime_behavior_changed"] is False
    assert dataset["stage7_promotion_allowed"] is False
    assert dataset["stage8_training_allowed"] is False
    assert dataset["summary"]["records_by_source_stage"] == {"stage7": 1}
    record = dataset["records"][0]
    assert record["causal_status"] == "non_causal"
    assert len(record["strategy_proposals"]) == 2
    assert {frame["causal_status"] for frame in record["strategy_proposals"]} == {"non_causal"}


def test_krk_strategy_arbitration_probe_v0_is_non_causal(tmp_path):
    dataset = {
        "schema_version": "krk_strategy_arbitration_dataset.v0",
        "causal_status": "non_causal_dataset",
        "runtime_behavior_changed": False,
        "summary": {"record_count": 1, "proposal_count": 2},
        "records": [
            {
                "state_id": "state.test",
                "source_stage": "stage7",
                "result_label": {"current_graph_h40": "max_plies"},
                "terminal_space_context": {
                    "black_king_edge_bucket": "central_or_midboard",
                    "box_area_relevance": "high",
                    "white_king_can_improve_support": True,
                    "active_terminal_terms": ["rook_safe"],
                },
                "strategy_proposals": [
                    {
                        "schema_version": "strategy_proposal_frame.v1",
                        "state_id": "state.test",
                        "provider_id": "krk.stage0_basin",
                        "move_uci": "a5a8",
                        "raw_score": 10.0,
                        "provider_local_rank": 1,
                        "normalized_score": 1.0,
                        "known_outcome_label": {"result": "max_plies"},
                        "causal_status": "non_causal",
                    },
                    {
                        "schema_version": "strategy_proposal_frame.v1",
                        "state_id": "state.test",
                        "provider_id": "krk.drive_to_edge",
                        "move_uci": "a5h5",
                        "raw_score": 0.1,
                        "provider_local_rank": 1,
                        "normalized_score": 1.0,
                        "known_outcome_label": {"result": "mate"},
                        "causal_status": "non_causal",
                    },
                ],
            }
        ],
    }
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps(dataset), encoding="utf-8")

    probe = _probe.build_probe(path)

    assert probe["schema_version"] == "krk_strategy_arbitration_probe.v0"
    assert probe["causal_status"] == "non_causal_probe"
    assert probe["runtime_behavior_changed"] is False
    assert probe["stage7_promotion_allowed"] is False
    assert probe["stage8_training_allowed"] is False
    assert probe["metrics"]["raw_global_provider_score"]["hit_rate"] == 0.0
    assert probe["metrics"]["provider_local_rank1_coverage"]["coverage_rate"] == 1.0


def test_stage7_challenge_set_manifest_is_non_causal(tmp_path, monkeypatch):
    artifact_root = tmp_path / "reports" / "structural_candidates"
    strategy_root = tmp_path / "reports" / "strategy_arbitration"
    artifact_root.mkdir(parents=True)
    strategy_root.mkdir(parents=True)
    (artifact_root / "stage7_evidence_merge_table.json").write_text(
        json.dumps({"rows": [{"hypothesis_labels": ["strategy_arbitration_candidate"]}]}),
        encoding="utf-8",
    )
    (artifact_root / "stage7_0926_move_shape_role_candidate_audit.json").write_text(
        json.dumps({"schema_version": "x"}), encoding="utf-8"
    )
    (strategy_root / "krk_strategy_arbitration_dataset_v0.json").write_text(
        json.dumps({"records": [{"state_id": "state.test"}]}), encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    manifest = _challenge_manifest.build_manifest(artifact_root)

    assert manifest["schema_version"] == "stage7_challenge_set_manifest.v1"
    assert manifest["causal_status"] == "non_causal_manifest"
    assert manifest["runtime_behavior_changed"] is False
    assert manifest["stage7_promotion_allowed"] is False
    assert manifest["stage8_training_allowed"] is False
    assert manifest["summary"]["challenge_family_count"] >= 6
    assert all(family["held_out_challenge_case"] for family in manifest["families"])


def test_krk_strategy_arbitration_decision_gate_selects_missing_feature(tmp_path):
    report_root = tmp_path / "reports" / "strategy_arbitration"
    report_root.mkdir(parents=True)
    (report_root / "krk_strategy_arbitration_dataset_v0.json").write_text(
        json.dumps({"summary": {"record_count": 3, "proposal_count": 5}}), encoding="utf-8"
    )
    (report_root / "krk_strategy_arbitration_probe_v0.json").write_text(
        json.dumps(
            {
                "decision": {"status": "missing_feature_first"},
                "metrics": {
                    "raw_global_provider_score": {"hit_rate": 0.9},
                    "provider_local_rank1_coverage": {"coverage_rate": 1.0},
                    "visible_heuristic_arbiter": {"hit_rate": 0.1},
                },
            }
        ),
        encoding="utf-8",
    )
    (report_root / "stage7_challenge_set_manifest.json").write_text(
        json.dumps({"summary": {"challenge_family_count": 6}}), encoding="utf-8"
    )

    gate = _decision_gate.build_gate(report_root)

    assert gate["schema_version"] == "krk_strategy_arbitration_decision_gate.v0"
    assert gate["causal_status"] == "non_causal_decision_gate"
    assert gate["runtime_behavior_changed"] is False
    assert gate["stage7_promotion_allowed"] is False
    assert gate["stage8_training_allowed"] is False
    assert gate["selected_status"] == "missing_feature_first"
    assert gate["recommendation"]["next_class"] == "non_causal_terminal_affordance_candidate_audit"


def test_krk_strategy_missing_feature_audit_proposes_non_causal_candidates(tmp_path):
    report_root = tmp_path / "reports" / "strategy_arbitration"
    report_root.mkdir(parents=True)
    (report_root / "krk_strategy_arbitration_dataset_v0.json").write_text(
        json.dumps(
            {
                "summary": {"record_count": 1, "proposal_count": 1},
                "records": [
                    {
                        "state_id": "state.edge",
                        "source_stage": "stage7",
                        "result_label": {"current_graph_h40": "max_plies"},
                        "terminal_space_context": {
                            "black_king_edge_bucket": "at_edge",
                            "box_area_relevance": "low",
                            "edge_net_pressure_proxy": True,
                            "white_king_can_improve_support": True,
                        },
                        "strategy_proposals": [{"provider_id": "krk.stage0_basin"}],
                        "hypothesis_labels": ["missing_feature_candidate"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (report_root / "krk_strategy_arbitration_probe_v0.json").write_text(
        json.dumps({"decision": {"status": "missing_feature_first"}}), encoding="utf-8"
    )
    (report_root / "stage7_challenge_set_manifest.json").write_text(
        json.dumps({"summary": {"challenge_family_count": 6}}), encoding="utf-8"
    )

    audit = _missing_feature_audit.build_audit(report_root)

    assert audit["schema_version"] == "krk_strategy_missing_feature_audit.v0"
    assert audit["causal_status"] == "non_causal_audit"
    assert audit["runtime_behavior_changed"] is False
    assert audit["stage7_promotion_allowed"] is False
    assert audit["stage8_training_allowed"] is False
    assert audit["recommended_next_step"] == (
        "stop_for_architecture_review_before_any_terminal_or_affordance_runtime_sandbox"
    )
    assert {candidate["causal_status"] for candidate in audit["candidates"]} == {"non_causal"}
    assert {candidate["promotion_status"] for candidate in audit["candidates"]} == {"proposed"}


def test_krk_feature_candidate_validation_types_candidates_without_runtime_effects(tmp_path):
    report_root = tmp_path / "reports" / "strategy_arbitration"
    report_root.mkdir(parents=True)
    (report_root / "krk_strategy_missing_feature_candidates.json").write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "candidate_id": "cand.krk.strategy.edge_net_affordance.v0",
                        "candidate_type": "terminal_affordance_refinement",
                        "proposed_change": {"target_concept": "edge_net_affordance"},
                    },
                    {
                        "candidate_id": "cand.krk.strategy.plan_selection_needed.v0",
                        "candidate_type": "terminal_affordance_refinement",
                        "proposed_change": {"target_concept": "plan_selection_needed"},
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    (report_root / "krk_strategy_arbitration_dataset_v0.json").write_text(
        json.dumps(
            {
                "summary": {"record_count": 3, "proposal_count": 3},
                "records": [
                    {
                        "state_id": "state.edge.mate",
                        "source_stage": "stage5",
                        "result_label": {"playout_result": "mate"},
                        "terminal_space_context": {
                            "black_king_edge_bucket": "at_edge",
                            "edge_net_pressure_proxy": True,
                            "box_area_relevance": "low",
                        },
                    },
                    {
                        "state_id": "state.edge.fail",
                        "source_stage": "stage7",
                        "result_label": {"current_graph_h40": "max_plies"},
                        "terminal_space_context": {
                            "black_king_edge_bucket": "at_edge",
                            "edge_net_pressure_proxy": True,
                            "box_area_relevance": "low",
                        },
                    },
                    {
                        "state_id": "state.stage7.unknown",
                        "source_stage": "stage7",
                        "result_label": {"current_graph_h40": None},
                        "terminal_space_context": {
                            "black_king_edge_bucket": "central_or_midboard",
                            "box_area_relevance": "high",
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (report_root / "krk_strategy_arbitration_probe_v0.json").write_text(
        json.dumps({"decision": {"status": "missing_feature_first"}}), encoding="utf-8"
    )

    validation = _feature_validation.build_validation(report_root)

    assert validation["schema_version"] == "krk_feature_candidate_validation.v0"
    assert validation["causal_status"] == "non_causal_validation"
    assert validation["runtime_behavior_changed"] is False
    assert validation["runtime_defaults_changed"] is False
    assert validation["stage7_promotion_allowed"] is False
    assert validation["stage8_training_allowed"] is False
    assert validation["summary"]["all_candidates_remain_non_causal"] is True
    assert validation["summary"]["sandbox_ready_candidate_ids"] == []
    assert {
        item["target_concept"]: item["causal_recommendation"]
        for item in validation["candidate_validations"]
    } == {
        "edge_net_affordance": "sandbox-blocked",
        "plan_selection_needed": "non-causal only",
    }


def test_strategy_monitor_record_validation_roundtrip():
    record = {
        "schema_version": "strategy_monitor_record.v1",
        "monitor_id": "monitor.krk.phase.state.test.0",
        "monitor_type": "PhaseBoundaryMonitor",
        "source_candidate_id": "cand.krk.strategy.phase_boundary_near_edge.v0",
        "active_landmark_label": "box_shrink",
        "state_id": "state.test",
        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
        "source_terms": ["black_king_edge_bucket in {at_edge, near_edge}"],
        "missing_terms": ["successful_next_provider"],
        "confidence": 0.5,
        "associated_outcome": "max_plies",
        "suggested_action_class": "audit_owner_phase",
        "causal_status": "non_causal",
        "promotion_status": "proposed",
        "notes": "roundtrip",
    }

    _monitor_records.validate_strategy_monitor_record(json.loads(json.dumps(record)))


def test_krk_strategy_monitor_record_extraction_is_non_causal(tmp_path):
    report_root = tmp_path / "reports" / "strategy_arbitration"
    report_root.mkdir(parents=True)
    (report_root / "krk_strategy_arbitration_dataset_v0.json").write_text(
        json.dumps(
            {
                "records": [
                    {
                        "state_id": "state.edge.fail",
                        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                        "active_landmark_label": "box_shrink",
                        "source_stage": "stage7",
                        "result_label": {"current_graph_h40": "max_plies"},
                        "terminal_space_context": {
                            "black_king_edge_bucket": "at_edge",
                            "box_area_relevance": "low",
                            "edge_net_pressure_proxy": True,
                            "fence_exists": True,
                            "fence_stable": False,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (report_root / "krk_feature_candidate_validation_v0.json").write_text(
        json.dumps(
            {
                "candidate_validations": [
                    {
                        "candidate_id": "cand.krk.strategy.phase_boundary_near_edge.v0",
                        "target_concept": "phase_boundary_near_edge",
                        "typed_as": "needs refinement / companion terms",
                        "mate_precision": 0.48,
                        "max_plies_failure_precision": 0.52,
                        "required_scope_or_companion_terms": ["successful_next_provider"],
                        "typing_rationale": "mixed",
                    },
                    {
                        "candidate_id": "cand.krk.strategy.king_support_conversion_affordance.v0",
                        "target_concept": "king_support_conversion_affordance",
                        "typed_as": "too broad / reject",
                        "mate_precision": 0.4,
                        "max_plies_failure_precision": 0.6,
                        "required_scope_or_companion_terms": ["king_support_improvement_move_exists"],
                        "typing_rationale": "too broad",
                    },
                    {
                        "candidate_id": "cand.krk.strategy.plan_selection_needed.v0",
                        "target_concept": "plan_selection_needed",
                        "typed_as": "growth-pressure/internal monitor",
                        "mate_precision": 0.0,
                        "max_plies_failure_precision": 1.0,
                        "required_scope_or_companion_terms": ["plan_capsule_context"],
                        "typing_rationale": "stage7 only",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    (report_root / "krk_strategy_missing_feature_candidates.json").write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "candidate_id": "cand.krk.strategy.phase_boundary_near_edge.v0",
                        "proposed_change": {"target_concept": "phase_boundary_near_edge"},
                        "source_terms": ["black_king_edge_bucket in {at_edge, near_edge}"],
                    },
                    {
                        "candidate_id": "cand.krk.strategy.king_support_conversion_affordance.v0",
                        "proposed_change": {"target_concept": "king_support_conversion_affordance"},
                        "source_terms": ["white_king_support_available"],
                    },
                    {
                        "candidate_id": "cand.krk.strategy.plan_selection_needed.v0",
                        "proposed_change": {"target_concept": "plan_selection_needed"},
                        "source_terms": ["stage7 residual"],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    payload = _monitor_records.build_monitor_records(report_root)

    assert payload["schema_version"] == "krk_strategy_monitor_records.v0"
    assert payload["causal_status"] == "non_causal_monitor_extraction"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["rejected_definition_count"] == 1
    assert {record["causal_status"] for record in payload["records"]} == {"non_causal"}
    assert "RejectedFeatureDefinition" not in {record["monitor_type"] for record in payload["records"]}


def test_krk_strategy_monitor_companion_audit_is_replay_free_and_non_causal(tmp_path):
    report_root = tmp_path / "reports" / "strategy_arbitration"
    report_root.mkdir(parents=True)
    (report_root / "krk_strategy_monitor_companion_terms_v0.json").write_text(
        json.dumps(
            {
                "companion_sets": [
                    {
                        "set_id": "phase_boundary_companions",
                        "target_monitor_types": ["PhaseBoundaryMonitor"],
                        "source_concepts": ["phase_boundary_near_edge"],
                        "candidate_terms": [
                            "current_owner",
                            "safe_edge_net_tighten_move_exists",
                            "active_landmark_label == box_shrink",
                        ],
                    }
                ],
                "blocked_next_steps": ["runtime_arbiter"],
            }
        ),
        encoding="utf-8",
    )
    (report_root / "krk_strategy_arbitration_dataset_v0.json").write_text(
        json.dumps(
            {
                "records": [
                    {
                        "state_id": "state.test",
                        "active_landmark_label": "box_shrink",
                        "terminal_space_context": {
                            "active_terminal_terms": ["safe_check_available"],
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    payload = _companion_audit.build_audit(report_root)

    assert payload["schema_version"] == "krk_strategy_monitor_companion_audit.v0"
    assert payload["causal_status"] == "non_causal_audit"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    statuses = {
        term["term"]: term["availability_status"]
        for companion_set in payload["companion_sets"]
        for term in companion_set["terms"]
    }
    assert statuses["current_owner"] == "proxy_available"
    assert statuses["active_landmark_label == box_shrink"] == "available_expression"
    assert statuses["safe_edge_net_tighten_move_exists"] == "missing_requires_visible_extraction"


def test_krk_visible_monitor_terms_are_diagnostic_only(tmp_path):
    report_root = tmp_path / "reports" / "strategy_arbitration"
    report_root.mkdir(parents=True)
    (report_root / "krk_strategy_arbitration_dataset_v0.json").write_text(
        json.dumps(
            {
                "records": [
                    {
                        "state_id": "state.test",
                        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                        "source_stage": "stage7",
                        "active_landmark_label": "box_shrink",
                        "result_label": {"current_graph_h40": "max_plies"},
                        "hypothesis_labels": ["strategy_arbitration_candidate"],
                        "terminal_space_context": {
                            "black_king_edge_bucket": "at_edge",
                            "box_area_relevance": "low",
                            "edge_net_pressure_proxy": True,
                            "mate_basin_readiness": False,
                            "rook_safe": True,
                            "stalemate_or_draw_risk": False,
                            "active_terminal_terms": [
                                "repair_or_reestablish_cut_available",
                                "king_support_improvement_move_exists",
                            ],
                        },
                        "strategy_proposals": [
                            {
                                "known_outcome_label": {"result": "mate"},
                                "post_move_terms": ["cut_restored_after_move"],
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    payload = _visible_monitor_terms.build_visible_terms(report_root)

    assert payload["schema_version"] == "krk_visible_monitor_terms.v0"
    assert payload["causal_status"] == "non_causal_diagnostic_terms"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    terms = payload["records"][0]["terms"]
    assert terms["king_support_improves_after_move"]["value"] is True
    assert terms["cut_or_fence_restored_after_move"]["value"] is True
    assert terms["safe_repair_move_exists"]["value"] is True
    assert terms["box_area_no_longer_decision_relevant"]["value"] is True
    assert terms["local_provider_competition_failed"]["value"] is True
    assert {term_payload["causal_status"] for term_payload in terms.values()} == {"non_causal"}


def test_krk_strategy_monitor_companion_audit_v1_uses_visible_terms(tmp_path):
    report_root = tmp_path / "reports" / "strategy_arbitration"
    report_root.mkdir(parents=True)
    (report_root / "krk_strategy_monitor_companion_terms_v0.json").write_text(
        json.dumps(
            {
                "companion_sets": [
                    {
                        "set_id": "repair_needed_companions",
                        "target_monitor_types": ["RepairNeededMonitor"],
                        "source_concepts": ["fence_or_cut_repair_affordance"],
                        "candidate_terms": ["safe_repair_move_exists", "cut_or_fence_restored_after_move"],
                    }
                ],
                "blocked_next_steps": ["runtime_arbiter"],
            }
        ),
        encoding="utf-8",
    )
    (report_root / "krk_strategy_arbitration_dataset_v0.json").write_text(
        json.dumps({"records": [{"state_id": "state.test", "terminal_space_context": {}}]}),
        encoding="utf-8",
    )
    visible_path = report_root / "krk_visible_monitor_terms_v0.json"
    visible_path.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "state_id": "state.test",
                        "terms": {
                            "safe_repair_move_exists": {
                                "value": True,
                                "confidence": "expression_from_current_state_terms",
                            },
                            "cut_or_fence_restored_after_move": {
                                "value": False,
                                "confidence": "not_observed",
                            },
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    payload = _companion_audit.build_audit(
        report_root,
        visible_terms_path=visible_path,
        schema_version="krk_strategy_monitor_companion_audit.v1",
    )

    assert payload["schema_version"] == "krk_strategy_monitor_companion_audit.v1"
    assert payload["summary"]["visible_terms_applied"] is True
    assert payload["summary"]["visible_term_count"] == 2
    assert payload["summary"]["terms_moved_to_extracted"] == [
        "safe_repair_move_exists",
        "cut_or_fence_restored_after_move",
    ]
    assert payload["companion_sets"][0]["set_availability_status"] == "improved_by_visible_extraction"
    assert {term["availability_status"] for term in payload["companion_sets"][0]["terms"]} == {
        "available_extracted"
    }
