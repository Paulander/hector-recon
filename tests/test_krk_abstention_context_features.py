from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_script(name: str, script: str):
    spec = importlib.util.spec_from_file_location(
        name,
        Path(__file__).resolve().parents[1] / "scripts" / script,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_dataset = _load_script(
    "build_krk_abstention_context_feature_dataset_v0",
    "build_krk_abstention_context_feature_dataset_v0.py",
)
_probe = _load_script(
    "probe_krk_abstention_context_feature_dataset_v0",
    "probe_krk_abstention_context_feature_dataset_v0.py",
)
_error_audit = _load_script(
    "summarize_krk_abstention_context_error_audit_v0",
    "summarize_krk_abstention_context_error_audit_v0.py",
)


def _write_fixture(root: Path) -> None:
    reports = root / "reports"
    reports.mkdir()
    (reports / "krk_abstention_training_dataset_v1.json").write_text(
        json.dumps(
            {
                "schema_version": "krk_abstention_training_dataset.v1",
                "causal_status": "non_causal_abstention_dataset",
                "rows": [
                    {
                        "state_id": "state.a",
                        "frame_id": "cp.krk.state.a",
                        "source_stage": "stage5",
                        "active_landmark_label": "fence_established",
                        "provider_id": "krk.stage0_basin",
                        "provider_family": "stage0_basin",
                        "provider_maturity": "foundation_frozen",
                        "provider_version": "stage5_validated_v1",
                        "forced_first_move": "h7h8",
                        "forced_result": "mate",
                        "forced_plies": 9,
                        "label_source_artifact": "fixture",
                        "abstention_label": "safe_owner",
                        "usable_for_training": True,
                    },
                    {
                        "state_id": "state.b",
                        "frame_id": "cp.krk.state.b",
                        "source_stage": "stage6",
                        "active_landmark_label": "drive_to_edge",
                        "provider_id": "krk.drive_to_edge",
                        "provider_family": "drive_to_edge",
                        "provider_maturity": "settling_medium_plasticity",
                        "provider_version": "stage6_overlay_v1",
                        "forced_first_move": "a4a8",
                        "forced_result": "max_plies",
                        "forced_plies": 40,
                        "label_source_artifact": "fixture",
                        "abstention_label": "unsafe_owner",
                        "usable_for_training": True,
                    },
                ],
            }
        )
    )
    (reports / "krk_control_plane_filtered_frames_with_forced_controls_v0.json").write_text(
        json.dumps(
            {
                "schema_version": "krk_control_plane_filtered_frames.v0",
                "causal_status": "non_causal_augmented_frame_export",
                "frames": [
                    {
                        "state_id": "state.a",
                        "frame_id": "cp.krk.state.a",
                        "fen": "5k2/7R/1K6/8/8/8/8/8 w - - 2 2",
                        "source_stage": "stage5",
                        "active_landmark_label": "fence_established",
                        "outcome": "mate",
                        "filter_metadata": {"strategy_proposal_count": 1},
                        "strategy_proposal_frames": [
                            {
                                "provider_id": "krk.stage0_basin",
                                "move_uci": "h7h8",
                                "raw_score": 12.0,
                                "normalized_score": 1.0,
                                "provider_local_rank": 1,
                            }
                        ],
                        "internal_monitor_records": [
                            {
                                "monitor_type": "OwnerExitMonitor",
                                "terminal_id": "cand.krk.strategy.box_shrink_exit_condition.v0",
                                "source_terms_met": ["rook_safe"],
                                "confidence": 0.8,
                            }
                        ],
                    },
                    {
                        "state_id": "state.b",
                        "frame_id": "cp.krk.state.b",
                        "fen": "8/8/8/8/R7/2k5/4K3/8 w - - 2 2",
                        "source_stage": "stage6",
                        "active_landmark_label": "drive_to_edge",
                        "outcome": "max_plies",
                        "filter_metadata": {"strategy_proposal_count": 1},
                        "strategy_proposal_frames": [
                            {
                                "provider_id": "krk.drive_to_edge",
                                "move_uci": "a4a8",
                                "raw_score": 0.2,
                                "normalized_score": 1.0,
                                "provider_local_rank": 1,
                            }
                        ],
                        "internal_monitor_records": [
                            {
                                "monitor_type": "RepairNeededMonitor",
                                "terminal_id": "cand.krk.strategy.fence_or_cut_repair_affordance.v0",
                                "source_terms_met": ["not fence_stable", "rook_safe"],
                                "confidence": 1.0,
                            }
                        ],
                    },
                ],
            }
        )
    )


def test_abstention_context_feature_dataset_is_non_causal(tmp_path):
    _write_fixture(tmp_path)
    payload = _dataset.build_dataset(tmp_path)

    assert payload["schema_version"] == "krk_abstention_context_feature_dataset.v0"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["summary"]["row_count"] == 2
    assert payload["summary"]["matched_proposal_count"] == 2
    row = payload["rows"][0]
    assert row["causal_status"] == "non_causal_context_feature_example"
    assert row["terminal_space_context"]["feature_source_status"] == "fen_proxy"
    assert row["proposal_context"]["matched_proposal"] is True
    assert row["monitor_context"]["monitor_count"] == 1


def test_abstention_context_feature_probe_blocks_runtime(tmp_path):
    _write_fixture(tmp_path)
    dataset = _dataset.build_dataset(tmp_path)
    (tmp_path / "reports" / "krk_abstention_context_feature_dataset_v0.json").write_text(
        json.dumps(dataset)
    )

    probe = _probe.build_probe(tmp_path)

    assert probe["schema_version"] == "krk_abstention_context_feature_probe.v0"
    assert probe["runtime_selector_implemented"] is False
    assert probe["decision"]["runtime_test_allowed_next"] is False
    assert "king_support_provider_family" in probe["results"]
    assert probe["decision"]["stage7_promotion_allowed"] is False


def test_abstention_context_error_audit_blocks_runtime(tmp_path):
    _write_fixture(tmp_path)
    dataset = _dataset.build_dataset(tmp_path)
    (tmp_path / "reports" / "krk_abstention_context_feature_dataset_v0.json").write_text(
        json.dumps(dataset)
    )
    probe = _probe.build_probe(tmp_path)
    (tmp_path / "reports" / "krk_abstention_context_feature_probe_v0.json").write_text(
        json.dumps(probe)
    )

    audit = _error_audit.build_audit(tmp_path)

    assert audit["schema_version"] == "krk_abstention_context_error_audit.v0"
    assert audit["runtime_selector_implemented"] is False
    assert audit["decision"]["runtime_test_allowed_next"] is False
    assert audit["summary"]["row_count"] == 2
    assert audit["summary"]["false_positive_count"] + audit["summary"]["false_negative_count"] >= 0
