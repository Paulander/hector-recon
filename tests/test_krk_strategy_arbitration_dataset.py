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
