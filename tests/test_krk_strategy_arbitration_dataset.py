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

_maturity_gate_spec = importlib.util.spec_from_file_location(
    "summarize_krk_strategy_monitor_maturity_gate",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_strategy_monitor_maturity_gate.py",
)
assert _maturity_gate_spec is not None
assert _maturity_gate_spec.loader is not None
_maturity_gate = importlib.util.module_from_spec(_maturity_gate_spec)
_maturity_gate_spec.loader.exec_module(_maturity_gate)

_internal_terminal_spec = importlib.util.spec_from_file_location(
    "summarize_krk_internal_terminal_candidates",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_internal_terminal_candidates.py",
)
assert _internal_terminal_spec is not None
assert _internal_terminal_spec.loader is not None
_internal_terminal = importlib.util.module_from_spec(_internal_terminal_spec)
_internal_terminal_spec.loader.exec_module(_internal_terminal)

_internal_terminal_evidence_spec = importlib.util.spec_from_file_location(
    "summarize_krk_internal_terminal_evidence",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_internal_terminal_evidence.py",
)
assert _internal_terminal_evidence_spec is not None
assert _internal_terminal_evidence_spec.loader is not None
_internal_terminal_evidence = importlib.util.module_from_spec(_internal_terminal_evidence_spec)
_internal_terminal_evidence_spec.loader.exec_module(_internal_terminal_evidence)

_protected_stage_status_spec = importlib.util.spec_from_file_location(
    "summarize_krk_protected_stage_status",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_protected_stage_status.py",
)
assert _protected_stage_status_spec is not None
assert _protected_stage_status_spec.loader is not None
_protected_stage_status = importlib.util.module_from_spec(_protected_stage_status_spec)
_protected_stage_status_spec.loader.exec_module(_protected_stage_status)

_self_expansion_gate_spec = importlib.util.spec_from_file_location(
    "summarize_krk_self_expansion_architecture_gate",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_self_expansion_architecture_gate.py",
)
assert _self_expansion_gate_spec is not None
assert _self_expansion_gate_spec.loader is not None
_self_expansion_gate = importlib.util.module_from_spec(_self_expansion_gate_spec)
_self_expansion_gate_spec.loader.exec_module(_self_expansion_gate)

_control_plane_contract_spec = importlib.util.spec_from_file_location(
    "summarize_krk_control_plane_contract",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_control_plane_contract.py",
)
assert _control_plane_contract_spec is not None
assert _control_plane_contract_spec.loader is not None
_control_plane_contract = importlib.util.module_from_spec(_control_plane_contract_spec)
_control_plane_contract_spec.loader.exec_module(_control_plane_contract)

_control_plane_manifest_spec = importlib.util.spec_from_file_location(
    "build_krk_control_plane_manifest",
    Path(__file__).resolve().parents[1] / "scripts" / "build_krk_control_plane_manifest.py",
)
assert _control_plane_manifest_spec is not None
assert _control_plane_manifest_spec.loader is not None
_control_plane_manifest = importlib.util.module_from_spec(_control_plane_manifest_spec)
_control_plane_manifest_spec.loader.exec_module(_control_plane_manifest)

_control_plane_gap_spec = importlib.util.spec_from_file_location(
    "summarize_krk_control_plane_gap_report",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_control_plane_gap_report.py",
)
assert _control_plane_gap_spec is not None
assert _control_plane_gap_spec.loader is not None
_control_plane_gap = importlib.util.module_from_spec(_control_plane_gap_spec)
_control_plane_gap_spec.loader.exec_module(_control_plane_gap)

_control_plane_frames_spec = importlib.util.spec_from_file_location(
    "export_krk_control_plane_frames",
    Path(__file__).resolve().parents[1] / "scripts" / "export_krk_control_plane_frames.py",
)
assert _control_plane_frames_spec is not None
assert _control_plane_frames_spec.loader is not None
_control_plane_frames = importlib.util.module_from_spec(_control_plane_frames_spec)
_control_plane_frames_spec.loader.exec_module(_control_plane_frames)

_control_plane_quality_spec = importlib.util.spec_from_file_location(
    "summarize_krk_control_plane_frame_quality",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_control_plane_frame_quality.py",
)
assert _control_plane_quality_spec is not None
assert _control_plane_quality_spec.loader is not None
_control_plane_quality = importlib.util.module_from_spec(_control_plane_quality_spec)
_control_plane_quality_spec.loader.exec_module(_control_plane_quality)

_control_plane_filter_spec = importlib.util.spec_from_file_location(
    "filter_krk_control_plane_frames",
    Path(__file__).resolve().parents[1] / "scripts" / "filter_krk_control_plane_frames.py",
)
assert _control_plane_filter_spec is not None
assert _control_plane_filter_spec.loader is not None
_control_plane_filter = importlib.util.module_from_spec(_control_plane_filter_spec)
_control_plane_filter_spec.loader.exec_module(_control_plane_filter)

_control_plane_strategy_probe_spec = importlib.util.spec_from_file_location(
    "probe_krk_control_plane_strategy_arbitration",
    Path(__file__).resolve().parents[1] / "scripts" / "probe_krk_control_plane_strategy_arbitration.py",
)
assert _control_plane_strategy_probe_spec is not None
assert _control_plane_strategy_probe_spec.loader is not None
_control_plane_strategy_probe = importlib.util.module_from_spec(_control_plane_strategy_probe_spec)
_control_plane_strategy_probe_spec.loader.exec_module(_control_plane_strategy_probe)

_provider_label_plan_spec = importlib.util.spec_from_file_location(
    "summarize_krk_provider_label_coverage_plan",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_provider_label_coverage_plan.py",
)
assert _provider_label_plan_spec is not None
assert _provider_label_plan_spec.loader is not None
_provider_label_plan = importlib.util.module_from_spec(_provider_label_plan_spec)
_provider_label_plan_spec.loader.exec_module(_provider_label_plan)


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


def test_krk_strategy_monitor_maturity_gate_blocks_causal_use(tmp_path):
    report_root = tmp_path / "reports" / "strategy_arbitration"
    report_root.mkdir(parents=True)
    (report_root / "krk_visible_monitor_terms_v0.json").write_text(
        json.dumps(
            {
                "summary": {
                    "term_names": [
                        "king_support_improves_after_move",
                        "cut_or_fence_restored_after_move",
                        "safe_repair_move_exists",
                        "box_area_no_longer_decision_relevant",
                        "post_plan_stagnation",
                        "local_provider_competition_failed",
                    ]
                },
                "records": [
                    {
                        "state_id": "state.fail",
                        "source_stage": "stage7",
                        "associated_outcome": "max_plies",
                        "terms": {
                            "king_support_improves_after_move": {"value": True},
                            "cut_or_fence_restored_after_move": {"value": True},
                            "safe_repair_move_exists": {"value": True},
                            "box_area_no_longer_decision_relevant": {"value": True},
                            "post_plan_stagnation": {"value": True},
                            "local_provider_competition_failed": {"value": True},
                        },
                    },
                    {
                        "state_id": "state.mate",
                        "source_stage": "stage5",
                        "associated_outcome": "mate",
                        "terms": {
                            "king_support_improves_after_move": {"value": True},
                            "cut_or_fence_restored_after_move": {"value": False},
                            "safe_repair_move_exists": {"value": True},
                            "box_area_no_longer_decision_relevant": {"value": True},
                            "post_plan_stagnation": {"value": False},
                            "local_provider_competition_failed": {"value": False},
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (report_root / "krk_strategy_monitor_records_v0.json").write_text(
        json.dumps(
            {
                "summary": {
                    "outcomes_by_monitor_type": {
                        "PlanSelectionNeededMonitor": {"max_plies": 1},
                        "OwnerExitMonitor": {"mate": 1, "max_plies": 1},
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    (report_root / "krk_strategy_monitor_companion_audit_v1.json").write_text(
        json.dumps(
            {
                "summary": {
                    "still_missing_terms": [
                        "safe_edge_net_tighten_move_exists",
                        "king_support_improves_after_reply",
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    gate = _maturity_gate.build_gate(report_root)

    assert gate["schema_version"] == "krk_strategy_monitor_maturity_gate.v0"
    assert gate["causal_status"] == "non_causal_maturity_gate"
    assert gate["runtime_behavior_changed"] is False
    assert gate["runtime_defaults_changed"] is False
    assert gate["stage7_promotion_allowed"] is False
    assert gate["stage8_training_allowed"] is False
    assert gate["summary"]["causal_ready_terms"] == []
    assert gate["summary"]["strongest_internal_terminal_candidates"] == [
        "post_plan_stagnation",
        "local_provider_competition_failed",
    ]
    assert all(item["causal_use_blocked"] is True for item in gate["term_maturity"])
    assert {
        item["term"]: item["maturity_status"] for item in gate["term_maturity"]
    }["post_plan_stagnation"] == "internal_terminal_candidate"


def test_internal_terminal_spec_validation_roundtrip():
    spec = {
        "schema_version": "internal_terminal_spec.v1",
        "terminal_id": "terminal.krk.test_monitor",
        "monitor_type": "internal_control_test_monitor",
        "source_monitor_candidates": ["test_monitor"],
        "source_terms": ["test_term"],
        "missing_terms": ["missing_term"],
        "intended_scope": "diagnostic only",
        "forbidden_causal_uses": ["choose_provider"],
        "potential_future_consumers": ["GrowthMonitor"],
        "validation_requirements": ["broader evidence"],
        "maturity_status": "internal_terminal_candidate",
        "causal_status": "non_causal",
        "promotion_status": "monitoring_only",
    }

    _internal_terminal.validate_internal_terminal_spec(json.loads(json.dumps(spec)))


def test_internal_terminal_validation_record_roundtrip():
    record = {
        "schema_version": "internal_terminal_validation_record.v1",
        "terminal_id": "terminal.krk.test_monitor",
        "state_id": "state.test",
        "family_id": "state.test",
        "active_landmark_label": "box_shrink",
        "source_terms_met": ["local_provider_competition_failed"],
        "missing_terms": ["route_conflict"],
        "associated_outcome": "max_plies",
        "stage": "stage7",
        "confidence": "replay_free_existing_artifact",
        "false_positive_risk": "unknown",
        "false_negative_risk": "unknown",
        "notes": "roundtrip",
    }

    _internal_terminal.validate_internal_terminal_validation_record(json.loads(json.dumps(record)))


def test_krk_internal_terminal_candidates_and_validation_are_non_causal(tmp_path):
    report_root = tmp_path / "reports" / "strategy_arbitration"
    report_root.mkdir(parents=True)
    (report_root / "krk_visible_monitor_terms_v0.json").write_text(
        json.dumps(
            {
                "records": [
                    {
                        "state_id": "state.fail",
                        "source_stage": "stage7",
                        "active_landmark_label": "box_shrink",
                        "associated_outcome": "max_plies",
                        "terms": {
                            "local_provider_competition_failed": {"value": True},
                            "post_plan_stagnation": {"value": True},
                            "box_area_no_longer_decision_relevant": {"value": True},
                            "cut_or_fence_restored_after_move": {"value": True},
                            "safe_repair_move_exists": {"value": True},
                        },
                    },
                    {
                        "state_id": "state.mate",
                        "source_stage": "stage5",
                        "active_landmark_label": "fence_established",
                        "associated_outcome": "mate",
                        "terms": {
                            "local_provider_competition_failed": {"value": False},
                            "post_plan_stagnation": {"value": False},
                            "box_area_no_longer_decision_relevant": {"value": False},
                            "cut_or_fence_restored_after_move": {"value": False},
                            "safe_repair_move_exists": {"value": True},
                        },
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    candidates = _internal_terminal.build_candidates(report_root)
    validation = _internal_terminal.build_validation(report_root, candidates)

    assert candidates["schema_version"] == "krk_internal_terminal_candidates.v0"
    assert candidates["causal_status"] == "non_causal_design"
    assert validation["schema_version"] == "krk_internal_terminal_validation.v0"
    assert validation["causal_status"] == "non_causal_validation"
    assert validation["runtime_behavior_changed"] is False
    assert validation["stage7_promotion_allowed"] is False
    assert validation["stage8_training_allowed"] is False
    assert validation["summary"]["causal_ready_terminals"] == []
    assert validation["summary"]["strongest_internal_terminal_candidates"] == [
        "terminal.krk.local_provider_competition_failed",
        "terminal.krk.post_plan_stagnation",
    ]
    assert all(item["causal_use_blocked"] is True for item in validation["terminal_validations"])


def test_krk_internal_terminal_evidence_and_review_are_non_causal(tmp_path):
    report_root = tmp_path / "reports" / "strategy_arbitration"
    structural_root = tmp_path / "reports" / "structural_candidates"
    report_root.mkdir(parents=True)
    structural_root.mkdir(parents=True)
    candidates = _internal_terminal.build_candidates(report_root)
    (report_root / "krk_internal_terminal_candidates_v0.json").write_text(
        json.dumps(candidates), encoding="utf-8"
    )
    (report_root / "krk_visible_monitor_terms_v0.json").write_text(
        json.dumps(
            {
                "records": [
                    {
                        "state_id": "state.fail",
                        "source_stage": "stage7",
                        "active_landmark_label": "box_shrink",
                        "associated_outcome": "max_plies",
                        "terms": {
                            "local_provider_competition_failed": {"value": True},
                            "post_plan_stagnation": {"value": True},
                            "box_area_no_longer_decision_relevant": {"value": True},
                            "cut_or_fence_restored_after_move": {"value": True},
                            "safe_repair_move_exists": {"value": True},
                        },
                    },
                    {
                        "state_id": "state.mate",
                        "source_stage": "stage5",
                        "active_landmark_label": "fence_established",
                        "associated_outcome": "mate",
                        "terms": {
                            "local_provider_competition_failed": {"value": False},
                            "post_plan_stagnation": {"value": False},
                            "box_area_no_longer_decision_relevant": {"value": False},
                            "cut_or_fence_restored_after_move": {"value": False},
                            "safe_repair_move_exists": {"value": True},
                        },
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    validation = _internal_terminal.build_validation(report_root, candidates)
    (report_root / "krk_internal_terminal_validation_v0.json").write_text(
        json.dumps(validation), encoding="utf-8"
    )
    (report_root / "krk_strategy_arbitration_dataset_v0.json").write_text(
        json.dumps(
            {
                "records": [
                    {
                        "state_id": "state.fail",
                        "source_stage": "stage7",
                        "active_landmark_label": "box_shrink",
                        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                        "result_label": {"current_graph_h40": "max_plies"},
                        "hypothesis_labels": ["strategy_arbitration_candidate"],
                        "terminal_space_context": {"fence_stable": False},
                        "strategy_proposals": [
                            {
                                "provider_id": "krk.stage0_basin",
                                "move_uci": "a1a2",
                                "raw_score": 10.0,
                            },
                            {
                                "provider_id": "krk.drive_to_edge",
                                "move_uci": "a1a3",
                                "raw_score": 0.2,
                            },
                        ],
                    },
                    {
                        "state_id": "state.mate",
                        "source_stage": "stage5",
                        "active_landmark_label": "fence_established",
                        "result_label": {"playout_result": "mate"},
                        "hypothesis_labels": [],
                        "terminal_space_context": {"fence_stable": True},
                        "strategy_proposals": [],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    (report_root / "krk_strategy_monitor_records_v0.json").write_text(
        json.dumps(
            {
                "summary": {
                    "outcomes_by_monitor_type": {
                        "PlanSelectionNeededMonitor": {"max_plies": 1},
                        "RepairNeededMonitor": {"mate": 1, "max_plies": 1},
                    },
                    "records_by_monitor_type": {
                        "PlanSelectionNeededMonitor": 1,
                        "RepairNeededMonitor": 2,
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (structural_root / "stage7_evidence_merge_table.json").write_text(
        json.dumps({"rows": []}), encoding="utf-8"
    )

    evidence = _internal_terminal_evidence.build_evidence(report_root, structural_root)
    review = _internal_terminal_evidence.build_design_review(evidence)

    assert evidence["schema_version"] == "krk_internal_terminal_evidence.v1"
    assert evidence["causal_status"] == "non_causal_evidence"
    assert evidence["runtime_behavior_changed"] is False
    assert evidence["runtime_defaults_changed"] is False
    assert evidence["stage7_promotion_allowed"] is False
    assert evidence["stage8_training_allowed"] is False
    assert evidence["summary"]["causal_ready_terminals"] == []
    assert all(item["causal_ready"] is False for item in evidence["terminal_evidence"])
    assert any(
        item["terminal_id"] == "terminal.krk.local_provider_competition_failed"
        and item["associated_provider_strategy_patterns"]["raw_top_provider_counts"]["krk.stage0_basin"] == 1
        for item in evidence["terminal_evidence"]
    )

    assert review["schema_version"] == "krk_internal_terminal_design_review.v1"
    assert review["causal_status"] == "non_causal_design_review"
    assert review["runtime_behavior_changed"] is False
    assert review["runtime_defaults_changed"] is False
    assert review["summary"]["causal_ready_terminals"] == []
    assert all(item["causal_ready"] is False for item in review["terminal_readiness"])
    assert "no_hidden_controller" in review["runtime_promotion_readiness_checklist"]
    assert "no_topology_mutation_during_gameplay" in review["runtime_promotion_readiness_checklist"]


def test_krk_protected_stage_status_preserves_stage4_caveat(tmp_path):
    root = tmp_path

    def write_json(relative_path, payload):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    validation_profile = {
        "schema_version": "composition_profile.v1",
        "profile_id": "handoff_composition_v1",
    }
    write_json(
        _protected_stage_status.STAGE1_MANIFEST,
        {
            "formal_validation": {
                "mode": "strict_pairs",
                "validated": True,
                "nodes": 257,
                "edges": 796,
            },
            "evaluation": {"stage1_eval_samples": 50},
            "learner_readiness": {"ready": True},
        },
    )
    write_json(
        _protected_stage_status.STAGE4_PROFILE,
        {
            "total": 500,
            "improved": 500,
            "optimal": 500,
            "worsened": 0,
            "no_move": 0,
            "playouts": {"mate": 500},
            "conversion_status_counts": {"passed": 500},
            "one_ply_status_counts": {"passed": 500},
            "shadow_candidates": [],
            "composition_profile": validation_profile,
        },
    )
    write_json(
        _protected_stage_status.STAGE5_PROFILE,
        {
            "total": 1000,
            "improved": 1000,
            "optimal": 1000,
            "worsened": 0,
            "no_move": 0,
            "playouts": {"mate": 1000},
            "conversion_status_counts": {"passed": 1000},
            "one_ply_status_counts": {"passed": 1000},
            "shadow_candidates": [],
            "composition_profile": validation_profile,
        },
    )
    write_json(
        _protected_stage_status.STAGE6_CANDIDATE,
        {
            "total": 300,
            "improved": 300,
            "optimal": 217,
            "worsened": 0,
            "no_move": 0,
            "playouts": {"mate": 300},
            "conversion_status_counts": {"passed": 300},
            "one_ply_status_counts": {"passed": 217, "failed": 83},
            "shadow_candidates": [],
            "composition_profile": validation_profile,
        },
    )
    write_json(
        _protected_stage_status.STAGE5_OVERLAY_GUARD,
        {
            "total": 300,
            "improved": 300,
            "optimal": 300,
            "worsened": 0,
            "no_move": 0,
            "playouts": {"mate": 300},
            "conversion_status_counts": {"passed": 300},
            "one_ply_status_counts": {"passed": 300},
            "shadow_candidates": [],
            "composition_profile": validation_profile,
        },
    )
    stage4_caveat_payload = {
        "total": 300,
        "improved": 300,
        "optimal": 300,
        "worsened": 0,
        "no_move": 0,
        "playouts": {"mate": 247, "max_plies": 53},
        "conversion_status_counts": {"passed": 247, "failed": 53},
        "one_ply_status_counts": {"passed": 300},
        "shadow_candidates": [{}] * 106,
        "composition_profile": validation_profile,
    }
    write_json(_protected_stage_status.STAGE4_OVERLAY_PROBE, stage4_caveat_payload)
    write_json(_protected_stage_status.STAGE4_BASE_CONTROL, stage4_caveat_payload)
    write_json(
        _protected_stage_status.STAGE6_PROMOTION,
        {
            "promotion_status": "promoted",
            "stage": {"mate_rate": 1.0, "passed": True},
            "guardrails": [{"label": "fence_established", "mate_rate": 1.0, "passed": True}],
        },
    )
    notes = root / _protected_stage_status.HANDOFF_NOTES
    notes.parent.mkdir(parents=True, exist_ok=True)
    notes.write_text(
        "Stage 1 regression:\n\n"
        "```text\n"
        "samples: 500\n"
        "result: 500/500 improved, 500/500 optimal, 0 worsened, 0 no-move\n"
        "```\n",
        encoding="utf-8",
    )

    status = _protected_stage_status.build_status(root)

    assert status["schema_version"] == "krk_protected_stage_status.v1"
    assert status["causal_status"] == "non_causal_status_audit"
    assert status["runtime_behavior_changed"] is False
    assert status["runtime_defaults_changed"] is False
    assert status["stage7_promotion_allowed"] is False
    assert status["stage8_training_allowed"] is False

    stages = {item["stage"]: item for item in status["stage_statuses"]}
    assert stages["stage1_backchain"]["evidence"]["documented_500_sample_regression"] is True
    assert stages["stage5_fence"]["evidence"]["profile_1000_seed7_h40"]["playouts"] == {
        "mate": 1000
    }
    assert (
        stages["stage6_drive_overlay"]["evidence"]["promotion_eval"]["promotion_status"]
        == "promoted"
    )
    assert stages["stage4_wrong_tempo"]["evidence"][
        "overlay_caveat_reproduces_on_base_control"
    ] is True
    assert stages["stage4_wrong_tempo"]["evidence"]["overlay_probe_300_seed7_h40"][
        "playouts"
    ] == {"mate": 247, "max_plies": 53}


def test_krk_self_expansion_architecture_gate_selects_non_causal_contract(tmp_path):
    root = tmp_path

    def write_json(relative_path, payload):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    non_causal_flags = {
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
    }
    write_json(
        _self_expansion_gate.PROTECTED_STAGE_STATUS,
        {
            "causal_status": "non_causal_status_audit",
            **non_causal_flags,
            "stage7_status": "local_valid_composition_quarantined",
            "summary": {
                "current_architecture_profile": "handoff_composition_v1",
                "yes_protected_or_promoted": [
                    "stage1_backchain",
                    "stage4_wrong_tempo",
                    "stage5_fence",
                    "stage6_drive_overlay",
                ],
                "cleanest_solved_components": [
                    "stage1_backchain",
                    "stage5_fence",
                    "stage6_drive_overlay",
                ],
                "solved_with_caveat": ["stage4_wrong_tempo"],
                "stage6_overlay_status": "promoted",
            },
        },
    )
    write_json(
        _self_expansion_gate.STRATEGY_ARBITRATION_GATE,
        {
            "causal_status": "non_causal_decision_gate",
            **non_causal_flags,
            "selected_status": "missing_feature_first",
            "missing_evidence": ["more stratified records"],
        },
    )
    write_json(
        _self_expansion_gate.INTERNAL_TERMINAL_REVIEW,
        {
            "causal_status": "non_causal_design_review",
            **non_causal_flags,
            "summary": {
                "main_conclusion": "Internal terminals are useful monitor/evidence objects.",
                "causal_ready_terminals": [],
            },
            "answers": {"safest_next_evidence_step": "broader replay-free evidence"},
        },
    )
    write_json(
        _self_expansion_gate.TRAINING_OBJECTIVE_GATE,
        {
            "causal_status": "non_causal_decision_gate",
            **non_causal_flags,
            "selected_outcome": "model_expression_gap_persists_stage7_micro_work_stops",
        },
    )
    write_json(
        _self_expansion_gate.SEQUENCE_POLICY_NOTE,
        {
            "causal_status": "non_causal_design_note",
            **non_causal_flags,
            "minimum_future_data_requirements": ["family held-out trajectories"],
        },
    )
    brief = root / _self_expansion_gate.CURRENT_BRIEF
    brief.parent.mkdir(parents=True, exist_ok=True)
    brief.write_text("# brief\n", encoding="utf-8")

    gate = _self_expansion_gate.build_gate(root)

    assert gate["schema_version"] == "krk_self_expansion_architecture_gate.v0"
    assert gate["causal_status"] == "non_causal_architecture_review"
    assert gate["runtime_behavior_changed"] is False
    assert gate["runtime_arbiter_added"] is False
    assert gate["runtime_terminals_added"] is False
    assert gate["stage7_promotion_allowed"] is False
    assert gate["stage8_training_allowed"] is False
    assert gate["selected_next_architecture_goal"]["goal_id"] == (
        "krk_control_plane_evidence_contract_v0"
    )
    assert gate["selected_next_architecture_goal"]["must_remain_non_causal"] is True
    assert "stage7_runtime_repair" in gate["forbidden_next_steps"]
    assert "control_plane_schema_design_v0" in {
        item["slice_id"] for item in gate["allowed_next_slices"]
    }


def test_krk_control_plane_contract_is_non_causal_schema(tmp_path):
    root = tmp_path
    report_path = root / _control_plane_contract.ARCHITECTURE_GATE
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "causal_status": "non_causal_architecture_review",
                "runtime_behavior_changed": False,
                "runtime_defaults_changed": False,
                "runtime_dtm_or_tablebase_lookup": False,
                "gameplay_topology_mutation": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
                "selected_next_architecture_goal": {
                    "goal_id": "krk_control_plane_evidence_contract_v0"
                },
                "forbidden_next_steps": ["stage7_runtime_repair", "runtime_arbiter"],
            }
        ),
        encoding="utf-8",
    )

    contract = _control_plane_contract.build_contract(root)

    assert contract["schema_version"] == "krk_control_plane_evidence_contract.v0"
    assert contract["causal_status"] == "non_causal_schema_contract"
    assert contract["runtime_behavior_changed"] is False
    assert contract["runtime_arbiter_added"] is False
    assert contract["runtime_terminals_added"] is False
    assert contract["stage7_promotion_allowed"] is False
    assert contract["stage8_training_allowed"] is False
    assert contract["primary_frame"]["schema_version"] == "control_plane_evidence_frame.v1"
    assert "runtime_move_override" in contract["primary_frame"]["forbidden_fields"]
    assert "runtime_move_selector" in contract["forbidden_consumers"]
    assert "offline_sequence_policy_benchmark" in contract["allowed_consumers"]
    assert contract["first_manifest_scope"]["records_from_existing_artifacts_only"] is True
    assert contract["first_manifest_scope"]["new_playouts_allowed"] is False
    assert contract["recommended_next_slice"] == (
        "control_plane_manifest_from_existing_artifacts_v0"
    )

    subschemas = {item["name"] for item in contract["subschemas"]}
    assert {
        "ProtectedProviderProvenance",
        "StrategyProposalFrame",
        "InternalMonitorEvidence",
        "PlanCapsuleWindowEvidence",
        "SequenceTrainingExample",
        "GuardrailResultSummary",
        "GrowthGovernorStatus",
        "PromotionGateStatus",
    } == subschemas


def test_krk_control_plane_manifest_maps_existing_artifacts_without_playouts(tmp_path):
    root = tmp_path

    def write_json(relative_path, payload):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def write_text(relative_path, text):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    write_json(
        _control_plane_manifest.CONTRACT,
        {
            "causal_status": "non_causal_schema_contract",
            "primary_frame": {
                "required_fields": [
                    "frame_id",
                    "domain",
                    "state_id",
                    "fen",
                    "source_stage",
                    "active_landmark_label",
                    "protected_provider_provenance",
                    "strategy_proposal_frames",
                    "internal_monitor_records",
                    "plan_capsule_window_records",
                    "sequence_training_examples",
                    "outcome_labels",
                    "guardrail_result_summaries",
                    "growth_governor_status",
                    "promotion_gate_status",
                    "source_artifacts",
                    "causal_status",
                ]
            },
            "blocked_next_steps": ["stage7_runtime_repair"],
        },
    )
    write_json(
        _control_plane_manifest.PROTECTED_STATUS,
        {
            "stage7_status": "local_valid_composition_quarantined",
            "summary": {
                "yes_protected_or_promoted": ["stage1_backchain", "stage5_fence"],
                "cleanest_solved_components": ["stage1_backchain", "stage5_fence"],
                "solved_with_caveat": ["stage4_wrong_tempo"],
            },
        },
    )
    write_text(_control_plane_manifest.STAGE6_MANIFEST, "# manifest\n")
    write_json(
        _control_plane_manifest.STRATEGY_DATASET,
        {
            "summary": {
                "record_count": 2,
                "proposal_count": 3,
                "records_by_source_stage": {"stage5": 1, "stage7": 1},
            }
        },
    )
    write_json(
        _control_plane_manifest.MONITOR_RECORDS,
        {"summary": {"monitor_record_count": 4}},
    )
    write_json(
        _control_plane_manifest.INTERNAL_TERMINAL_EVIDENCE,
        {
            "summary": {
                "terminal_count": 2,
                "causal_ready_terminals": [],
                "strongest_internal_terminal_candidates": [
                    "terminal.krk.local_provider_competition_failed"
                ],
            }
        },
    )
    write_json(_control_plane_manifest.PLAN_WINDOW, {"windows": [{}, {}]})
    write_json(_control_plane_manifest.PLAN_AUDIT, {"schema_version": "audit.v1"})
    write_json(_control_plane_manifest.DTM_TRAJECTORY_SEED, {"trajectories": [{}, {}]})
    write_text(_control_plane_manifest.DTM_TRAJECTORY_SEED_JSONL, "{}\n{}\n")
    write_json(_control_plane_manifest.DTM_TRAJECTORY_EXPANDED, {"trajectories": [{}]})
    write_text(_control_plane_manifest.DTM_TRAJECTORY_EXPANDED_JSONL, "{}\n")
    write_json(
        _control_plane_manifest.TRAINING_OBJECTIVE_BENCHMARK,
        {"final_decision": "model_expression_gap_persists"},
    )
    write_json(
        _control_plane_manifest.TRAINING_OBJECTIVE_GATE,
        {"selected_outcome": "model_expression_gap_persists_stage7_micro_work_stops"},
    )
    write_json(_control_plane_manifest.GROWTH_GOVERNOR_PLAN, {"schema_version": "plan.v1"})
    write_json(_control_plane_manifest.STAGE6_PROMOTION, {"promotion_status": "promoted"})
    write_json(_control_plane_manifest.STAGE7_CLOSURE, {"decision": "stopped"})

    manifest = _control_plane_manifest.build_manifest(root)

    assert manifest["schema_version"] == "krk_control_plane_manifest.v0"
    assert manifest["causal_status"] == "non_causal_manifest"
    assert manifest["runtime_behavior_changed"] is False
    assert manifest["runtime_arbiter_added"] is False
    assert manifest["runtime_terminals_added"] is False
    assert manifest["stage7_promotion_allowed"] is False
    assert manifest["stage8_training_allowed"] is False
    assert manifest["summary"]["new_playouts_added"] == 0
    assert manifest["summary"]["records_from_existing_artifacts_only"] is True
    assert manifest["summary"]["strategy_record_count"] == 2
    assert manifest["summary"]["strategy_proposal_count"] == 3
    assert manifest["summary"]["monitor_record_count"] == 4
    assert manifest["summary"]["sequence_seed_step_count"] == 2
    assert manifest["summary"]["sequence_expanded_step_count"] == 1
    assert "strategy_proposal_frames" in manifest["summary"]["covered_contract_fields"]
    assert "internal_monitor_records" in manifest["summary"]["covered_contract_fields"]
    assert "unified_frame_export_missing" in {gap["gap_id"] for gap in manifest["gaps"]}


def test_krk_control_plane_gap_report_recommends_replay_free_frame_export(tmp_path):
    root = tmp_path
    manifest_path = root / _control_plane_gap.MANIFEST
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "causal_status": "non_causal_manifest",
                "runtime_behavior_changed": False,
                "runtime_defaults_changed": False,
                "runtime_dtm_or_tablebase_lookup": False,
                "gameplay_topology_mutation": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
                "summary": {
                    "strategy_record_count": 2,
                    "strategy_proposal_count": 3,
                    "monitor_record_count": 4,
                    "plan_window_count": 1,
                    "sequence_seed_step_count": 2,
                    "sequence_expanded_step_count": 5,
                    "new_playouts_added": 0,
                },
                "field_coverage": [
                    {
                        "field": "strategy_proposal_frames",
                        "summary": {"records_by_source_stage": {"stage5": 1, "stage7": 1}},
                    }
                ],
                "blocked_next_steps": ["stage7_runtime_repair", "runtime_arbiter"],
            }
        ),
        encoding="utf-8",
    )

    report = _control_plane_gap.build_gap_report(root)

    assert report["schema_version"] == "krk_control_plane_gap_report.v0"
    assert report["causal_status"] == "non_causal_gap_report"
    assert report["runtime_behavior_changed"] is False
    assert report["runtime_arbiter_added"] is False
    assert report["runtime_terminals_added"] is False
    assert report["stage7_promotion_allowed"] is False
    assert report["stage8_training_allowed"] is False
    assert report["recommended_next_slice"]["slice_id"] == (
        "export_replay_free_control_plane_frames_v0"
    )
    assert report["recommended_next_slice"]["causal"] is False
    assert report["recommended_next_slice"]["new_playouts_allowed"] is False
    assert "no_unified_control_plane_frames" in {
        gap["gap_id"] for gap in report["stratified_gaps"]
    }
    assert "stage8_training" in report["deferred_until_after_frame_export"]


def test_krk_control_plane_frame_export_is_replay_free_and_non_causal(tmp_path):
    root = tmp_path

    def write_json(relative_path, payload):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def write_text(relative_path, text):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    write_json(_control_plane_frames.CONTRACT, {"causal_status": "non_causal_schema_contract"})
    write_json(
        _control_plane_frames.GAP_REPORT,
        {"recommended_next_slice": {"slice_id": "export_replay_free_control_plane_frames_v0"}},
    )
    write_json(
        _control_plane_frames.PROTECTED_STATUS,
        {
            "stage_statuses": [
                {
                    "stage": "stage5_fence",
                    "evidence": {
                        "profile": {
                            "total": 1,
                            "playouts": {"mate": 1},
                            "shadow_candidate_count": 0,
                        }
                    },
                }
            ]
        },
    )
    write_json(
        _control_plane_frames.STRATEGY_DATASET,
        {
            "records": [
                {
                    "state_id": "state.test",
                    "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                    "source_stage": "stage7",
                    "active_landmark_label": "box_shrink",
                    "strategy_proposals": [
                        {
                            "provider_id": "krk.box_shrink",
                            "move_uci": "a1a2",
                            "raw_score": 1.0,
                            "provider_local_rank": 1,
                        }
                    ],
                    "result_label": {"current_graph_h40": "max_plies"},
                    "hypothesis_labels": ["training_objective_model_expression_candidate"],
                    "source_artifacts": ["fixture.json"],
                }
            ]
        },
    )
    write_json(
        _control_plane_frames.MONITOR_RECORDS,
        {
            "records": [
                {
                    "state_id": "state.test",
                    "monitor_id": "monitor.test",
                    "monitor_type": "PlanSelectionNeededMonitor",
                    "source_terms": ["local_provider_competition_failed"],
                    "missing_terms": [],
                    "confidence": 1.0,
                    "associated_outcome": "max_plies",
                    "promotion_status": "proposed",
                }
            ]
        },
    )
    write_json(
        _control_plane_frames.PLAN_WINDOWS,
        {
            "windows": [
                {
                    "start_fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                    "ttl_white_moves": 3,
                    "owned_white_move_count": 3,
                    "entry_confirmed": True,
                    "progress_terms": ["box_area_preserved"],
                    "result": "max_plies",
                }
            ]
        },
    )
    write_text(
        _control_plane_frames.DTM_SEED_JSONL,
        json.dumps(
            {
                "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                "ply_index": 0,
                "target_skill": "krk.post_box_shrink_continuation",
                "legal_move_labels": [
                    {"move": "a1a2", "label": 1, "target_class": "optimal_dtm_move"},
                    {"move": "a1a3", "label": 0, "target_class": "winning_nonoptimal_move"},
                ],
            }
        )
        + "\n",
    )
    write_text(_control_plane_frames.DTM_EXPANDED_JSONL, "")
    write_json(_control_plane_frames.STAGE6_PROMOTION, {"promotion_status": "promoted"})
    write_json(
        _control_plane_frames.STAGE7_CLOSURE,
        {"decision": {"benchmark_status": "model_expression_gap_persists"}},
    )

    export = _control_plane_frames.build_frames(root)

    assert export["schema_version"] == "krk_control_plane_frames_export.v0"
    assert export["causal_status"] == "non_causal_frame_export"
    assert export["runtime_behavior_changed"] is False
    assert export["runtime_arbiter_added"] is False
    assert export["runtime_terminals_added"] is False
    assert export["stage7_promotion_allowed"] is False
    assert export["stage8_training_allowed"] is False
    assert export["summary"]["frame_count"] == 1
    assert export["summary"]["strategy_proposal_frame_count"] == 1
    assert export["summary"]["internal_monitor_record_count"] == 1
    assert export["summary"]["plan_capsule_window_record_count"] == 1
    assert export["summary"]["sequence_training_example_count"] == 1
    assert export["summary"]["new_playouts_added"] == 0

    frame = export["frames"][0]
    assert frame["causal_status"] == "non_causal"
    assert frame["promotion_gate_status"]["promotion_status"] == "quarantined"
    assert frame["strategy_proposal_frames"][0]["causal_status"] == "non_causal"
    assert frame["internal_monitor_records"][0]["causal_ready"] is False
    assert frame["sequence_training_examples"][0]["offline_only"] is True


def test_krk_control_plane_frame_quality_blocks_runtime_and_recommends_filters(tmp_path):
    root = tmp_path
    frames_path = root / _control_plane_quality.FRAMES
    frames_path.parent.mkdir(parents=True, exist_ok=True)
    frames_path.write_text(
        json.dumps(
            {
                "causal_status": "non_causal_frame_export",
                "frames": [
                    {
                        "frame_id": "cp.a",
                        "source_stage": "stage7",
                        "outcome_labels": {"result_label": {"current_graph_h40": "max_plies"}},
                        "strategy_proposal_frames": [],
                        "internal_monitor_records": [
                            {"monitor_id": "m1"},
                            {"monitor_id": "m1"},
                        ],
                        "plan_capsule_window_records": [
                            {
                                "progress_terms_confirmed": ["p"],
                                "window_outcome": "max_plies",
                            }
                        ],
                        "sequence_training_examples": [{"offline_only": True}],
                    },
                    {
                        "frame_id": "cp.b",
                        "source_stage": "stage5",
                        "outcome_labels": {"result_label": {"current_graph_h40": "mate"}},
                        "strategy_proposal_frames": [{"move_uci": "a1a2"}],
                        "internal_monitor_records": [],
                        "plan_capsule_window_records": [],
                        "sequence_training_examples": [],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    report = _control_plane_quality.build_quality_report(root)

    assert report["schema_version"] == "krk_control_plane_frame_quality_report.v0"
    assert report["causal_status"] == "non_causal_quality_report"
    assert report["runtime_behavior_changed"] is False
    assert report["runtime_arbiter_added"] is False
    assert report["runtime_terminals_added"] is False
    assert report["stage7_promotion_allowed"] is False
    assert report["stage8_training_allowed"] is False
    assert report["readiness"]["runtime_sandbox"] == "blocked"
    assert report["readiness"]["stage8_training"] == "blocked"
    assert report["recommended_next_slice"]["slice_id"] == (
        "control_plane_frame_dedupe_and_quality_filters_v0"
    )
    assert report["recommended_next_slice"]["causal"] is False
    assert any(
        flag["flag_id"] == "some_frames_lack_strategy_proposals" and flag["count"] == 1
        for flag in report["quality_flags"]
    )


def test_krk_control_plane_filter_marks_strategy_ready_and_dedupes(tmp_path):
    root = tmp_path

    def write_json(relative_path, payload):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    write_json(
        _control_plane_filter.FRAMES,
        {
            "causal_status": "non_causal_frame_export",
            "frames": [
                {
                    "frame_id": "cp.a",
                    "state_id": "state.a",
                    "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                    "source_stage": "stage5",
                    "active_landmark_label": "fence_established",
                    "outcome_labels": {"result_label": {"current_graph_h40": "mate"}},
                    "strategy_proposal_frames": [{"move_uci": "a1a2"}],
                    "internal_monitor_records": [
                        {"monitor_id": "m1", "terminal_id": "t", "monitor_type": "T"},
                        {"monitor_id": "m1", "terminal_id": "t", "monitor_type": "T"},
                    ],
                    "plan_capsule_window_records": [
                        {
                            "plan_id": "p",
                            "progress_terms_confirmed": ["x"],
                            "window_outcome": "mate",
                            "ttl_white_moves": 3,
                            "owned_white_move_count": 3,
                        },
                        {
                            "plan_id": "p",
                            "progress_terms_confirmed": ["x"],
                            "window_outcome": "mate",
                            "ttl_white_moves": 3,
                            "owned_white_move_count": 3,
                        },
                    ],
                    "sequence_training_examples": [],
                    "protected_provider_provenance": [],
                    "growth_governor_status": {},
                    "promotion_gate_status": {},
                },
                {
                    "frame_id": "cp.b",
                    "state_id": "state.b",
                    "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                    "source_stage": "stage7",
                    "active_landmark_label": "box_shrink",
                    "outcome_labels": {"result_label": {}},
                    "strategy_proposal_frames": [],
                    "internal_monitor_records": [],
                    "plan_capsule_window_records": [],
                    "sequence_training_examples": [{"offline_only": True}],
                    "protected_provider_provenance": [],
                    "growth_governor_status": {},
                    "promotion_gate_status": {},
                },
            ],
        },
    )
    write_json(_control_plane_filter.QUALITY, {"causal_status": "non_causal_quality_report"})

    result = _control_plane_filter.build_filtered_export(root)

    assert result["schema_version"] == "krk_control_plane_filtered_frames.v0"
    assert result["causal_status"] == "non_causal_filtered_frame_export"
    assert result["runtime_behavior_changed"] is False
    assert result["runtime_arbiter_added"] is False
    assert result["runtime_terminals_added"] is False
    assert result["stage7_promotion_allowed"] is False
    assert result["stage8_training_allowed"] is False
    assert result["summary"]["strategy_ready_frame_count"] == 1
    assert result["summary"]["context_only_frame_count"] == 1
    assert result["summary"]["dropped_duplicate_monitor_count"] == 1
    assert result["summary"]["dropped_duplicate_plan_window_count"] == 1
    assert result["summary"]["new_playouts_added"] == 0
    assert result["readiness"]["runtime_sandbox"] == "blocked"
    assert result["recommended_next_slice"] == "offline_strategy_arbitration_probe_filtered_v0"

    first = result["frames"][0]
    assert "strategy_arbitration_benchmark" in first["filter_metadata"]["benchmark_roles"]
    assert first["filter_metadata"]["causal_status"] == "non_causal"
    assert len(first["internal_monitor_records"]) == 1
    assert len(first["plan_capsule_window_records"]) == 1


def test_krk_control_plane_strategy_probe_stays_non_causal_and_reports_label_gap(tmp_path):
    root = tmp_path
    filtered_path = root / _control_plane_strategy_probe.FILTERED_FRAMES
    filtered_path.parent.mkdir(parents=True, exist_ok=True)
    filtered_path.write_text(
        json.dumps(
            {
                "causal_status": "non_causal_filtered_frame_export",
                "frames": [
                    {
                        "frame_id": "cp.a",
                        "filter_metadata": {
                            "benchmark_roles": ["strategy_arbitration_benchmark"]
                        },
                        "strategy_proposal_frames": [
                            {
                                "provider_id": "krk.a",
                                "move_uci": "a1a2",
                                "raw_score": 2.0,
                                "normalized_score": 1.0,
                                "provider_local_rank": 1,
                                "known_outcome_label": {"playout_result": "mate"},
                            },
                            {
                                "provider_id": "krk.b",
                                "move_uci": "a1a3",
                                "raw_score": 3.0,
                                "normalized_score": 0.5,
                                "provider_local_rank": 2,
                                "known_outcome_label": {"result": "max_plies"},
                            },
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    probe = _control_plane_strategy_probe.build_probe(root)

    assert probe["schema_version"] == "krk_control_plane_strategy_arbitration_probe.v0"
    assert probe["causal_status"] == "non_causal_probe"
    assert probe["runtime_behavior_changed"] is False
    assert probe["runtime_arbiter_added"] is False
    assert probe["runtime_terminals_added"] is False
    assert probe["stage7_promotion_allowed"] is False
    assert probe["stage8_training_allowed"] is False
    assert probe["label_coverage"]["strategy_benchmark_frame_count"] == 1
    assert probe["label_coverage"]["provider_labeled_frame_count"] == 1
    assert probe["label_coverage"]["frames_with_known_provider_mate"] == 1
    assert probe["decision"]["selected_status"] == "provider_labels_underpowered"
    assert probe["decision"]["causal_next_step_allowed"] is False
    raw = next(item for item in probe["selector_results"] if item["selector"] == "raw_global_score")
    assert raw["selected_max_plies_count"] == 1
    normalized = next(
        item for item in probe["selector_results"] if item["selector"] == "normalized_score"
    )
    assert normalized["selected_mate_count"] == 1


def test_krk_provider_label_coverage_plan_is_bounded_and_non_causal(tmp_path):
    root = tmp_path

    def write_json(relative_path, payload):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    write_json(
        _provider_label_plan.FILTERED_FRAMES,
        {
            "causal_status": "non_causal_filtered_frame_export",
            "frames": [
                {
                    "frame_id": "cp.stage5",
                    "source_stage": "stage5",
                    "filter_metadata": {
                        "benchmark_roles": ["strategy_arbitration_benchmark"]
                    },
                    "strategy_proposal_frames": [
                        {
                            "provider_id": "krk.fence",
                            "move_uci": "a1a2",
                            "known_outcome_label": {"playout_result": "max_plies"},
                        }
                    ],
                },
                {
                    "frame_id": "cp.stage7",
                    "source_stage": "stage7",
                    "filter_metadata": {
                        "benchmark_roles": ["strategy_arbitration_benchmark"]
                    },
                    "strategy_proposal_frames": [
                        {
                            "provider_id": "krk.drive",
                            "move_uci": "a1a3",
                            "known_outcome_label": {"result": "mate"},
                        }
                    ],
                },
            ],
        },
    )
    write_json(
        _provider_label_plan.STRATEGY_PROBE,
        {
            "causal_status": "non_causal_probe",
            "label_coverage": {
                "provider_labeled_frame_count": 2,
                "frames_with_known_provider_mate": 1,
                "label_status": "provider_labels_sufficient_for_small_probe",
            },
        },
    )

    plan = _provider_label_plan.build_plan(root)

    assert plan["schema_version"] == "krk_provider_label_coverage_plan.v0"
    assert plan["causal_status"] == "non_causal_label_plan"
    assert plan["runtime_behavior_changed"] is False
    assert plan["labels_generated_in_this_slice"] is False
    assert plan["runtime_arbiter_added"] is False
    assert plan["stage7_promotion_allowed"] is False
    assert plan["stage8_training_allowed"] is False
    assert plan["current_label_coverage"]["unknown_provider_label_count_by_stage"] == {}
    assert plan["current_label_coverage"]["known_provider_label_count_by_stage"] == {
        "stage5": 1,
        "stage7": 1
    }
    assert plan["current_label_coverage"]["coverage_status"] == "sufficient_for_current_small_probe"
    assert plan["bounded_labeling_plan"][0]["phase"] == "p0_protected_success_controls"
    assert plan["bounded_labeling_plan"][0]["new_runtime_behavior"] is False
    assert plan["recommended_next_slice"] == "offline_strategy_arbitration_baseline_v1"
