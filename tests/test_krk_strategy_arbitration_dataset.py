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
