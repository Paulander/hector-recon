from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, script: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / script)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ownership_module = _load_module(
    "build_krk_ownership_selection_label_dataset_v0",
    "build_krk_ownership_selection_label_dataset_v0.py",
)
split_v1_module = _load_module(
    "build_krk_split_selector_objective_dataset_v1",
    "build_krk_split_selector_objective_dataset_v1.py",
)
probe_module = _load_module(
    "probe_krk_ownership_selection_features_v0",
    "probe_krk_ownership_selection_features_v0.py",
)
readiness_module = _load_module(
    "review_krk_split_selector_objective_readiness_v1",
    "review_krk_split_selector_objective_readiness_v1.py",
)
ownership_v1_module = _load_module(
    "build_krk_ownership_selection_label_dataset_v1",
    "build_krk_ownership_selection_label_dataset_v1.py",
)
selected_diversity_labels_module = _load_module(
    "run_krk_selected_provider_diversity_ownership_labels_v0",
    "run_krk_selected_provider_diversity_ownership_labels_v0.py",
)
context_dataset_module = _load_module(
    "build_krk_ownership_selection_context_dataset_v0",
    "build_krk_ownership_selection_context_dataset_v0.py",
)
context_probe_module = _load_module(
    "probe_krk_ownership_selection_context_features_v0",
    "probe_krk_ownership_selection_context_features_v0.py",
)
context_review_module = _load_module(
    "review_krk_ownership_context_feature_results_v0",
    "review_krk_ownership_context_feature_results_v0.py",
)
ownership_v3_module = _load_module(
    "build_krk_ownership_selection_label_dataset_v3",
    "build_krk_ownership_selection_label_dataset_v3.py",
)
targeted_manifest_module = _load_module(
    "generate_krk_targeted_non_stage0_ownership_manifest_v0",
    "generate_krk_targeted_non_stage0_ownership_manifest_v0.py",
)
targeted_labels_module = _load_module(
    "run_krk_targeted_non_stage0_ownership_labels_v0",
    "run_krk_targeted_non_stage0_ownership_labels_v0.py",
)
targeted_review_module = _load_module(
    "review_krk_targeted_non_stage0_ownership_v0",
    "review_krk_targeted_non_stage0_ownership_v0.py",
)
ownership_v4_module = _load_module(
    "build_krk_ownership_selection_label_dataset_v4",
    "build_krk_ownership_selection_label_dataset_v4.py",
)
targeted_negative_manifest_module = _load_module(
    "generate_krk_targeted_ownership_negative_manifest_v0",
    "generate_krk_targeted_ownership_negative_manifest_v0.py",
)
targeted_negative_labels_module = _load_module(
    "run_krk_targeted_ownership_negative_labels_v0",
    "run_krk_targeted_ownership_negative_labels_v0.py",
)
ownership_v5_module = _load_module(
    "build_krk_ownership_selection_label_dataset_v5",
    "build_krk_ownership_selection_label_dataset_v5.py",
)
paired_inventory_v1_module = _load_module(
    "build_krk_state_local_paired_ownership_inventory_v1",
    "build_krk_state_local_paired_ownership_inventory_v1.py",
)
paired_probe_module = _load_module(
    "probe_krk_state_local_paired_ownership_objective_v0",
    "probe_krk_state_local_paired_ownership_objective_v0.py",
)
paired_review_module = _load_module(
    "review_krk_state_local_paired_ownership_objective_v0",
    "review_krk_state_local_paired_ownership_objective_v0.py",
)
paired_probe_v1_module = _load_module(
    "probe_krk_state_local_paired_ownership_objective_v1",
    "probe_krk_state_local_paired_ownership_objective_v1.py",
)
paired_packet_module = _load_module(
    "summarize_krk_state_local_paired_selector_runtime_review_packet_v0",
    "summarize_krk_state_local_paired_selector_runtime_review_packet_v0.py",
)
runtime_proxy_module = _load_module(
    "design_krk_state_local_paired_runtime_proxies_v0",
    "design_krk_state_local_paired_runtime_proxies_v0.py",
)
failure_risk_terms_module = _load_module(
    "extract_krk_selected_owner_failure_risk_terms_v0",
    "extract_krk_selected_owner_failure_risk_terms_v0.py",
)
failure_risk_validation_module = _load_module(
    "validate_krk_selected_owner_failure_risk_proxy_v0",
    "validate_krk_selected_owner_failure_risk_proxy_v0.py",
)


def _write_json(root: Path, relative: Path, payload: dict) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_ownership_selection_recovery_uses_only_normal_selected_provider(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(ownership_module, "ROOT", root)
    _write_json(
        root,
        ownership_module.SELECTOR_FEATURES,
        {
            "causal_status": "non_causal_feature_dataset",
            "rows": [
                {
                    "target_kind": "selected_playout_success",
                    "usable_for_training": True,
                    "source_stage": "stage5",
                    "state_id": "s1",
                    "frame_id": "f1",
                    "active_landmark_label": "fence_established",
                    "provider_id": "krk.stage0_basin",
                    "move_uci": "a1a2",
                    "label": "positive",
                    "selected_provider_before_observation": "krk.stage0_basin",
                    "selected_provider_matches_target": True,
                    "target_provider_best_rank": 1,
                    "target_provider_best_raw_score": 3.0,
                    "target_provider_summary_count": 1,
                    "unique_provider_count": 2,
                    "all_suggestion_count": 4,
                    "source_terms": ["fence_exists"],
                    "source_term_count": 1,
                },
                {
                    "target_kind": "selected_playout_success",
                    "usable_for_training": True,
                    "source_stage": "stage5",
                    "state_id": "s1",
                    "frame_id": "f1",
                    "provider_id": "krk.edge_trap_close",
                    "label": "positive",
                    "selected_provider_before_observation": "krk.stage0_basin",
                    "selected_provider_matches_target": False,
                },
                {
                    "target_kind": "selected_playout_success",
                    "usable_for_training": True,
                    "source_stage": "stage7",
                    "state_id": "s7",
                    "frame_id": "f7",
                    "provider_id": "krk.stage0_basin",
                    "label": "negative",
                    "selected_provider_before_observation": "krk.stage0_basin",
                    "selected_provider_matches_target": True,
                },
            ],
        },
    )
    _write_json(root, ownership_module.SPLIT_READINESS, {"causal_status": "non_causal_readiness_review"})

    dataset = ownership_module.build_dataset()

    assert dataset["causal_status"] == "non_causal_ownership_label_dataset"
    assert dataset["summary"]["deduplicated_row_count"] == 1
    assert dataset["summary"]["target_label_counts"] == {"selected_owner_converted": 1}
    assert dataset["summary"]["stage7_row_count"] == 0
    assert dataset["decision"]["selector_training_allowed"] is False


def test_split_v1_replaces_missing_ownership_channel(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(split_v1_module, "ROOT", root)
    _write_json(
        root,
        split_v1_module.SPLIT_V0,
        {
            "causal_status": "non_causal_split_objective_dataset",
            "rows": [
                {
                    "causal_status": "non_causal_objective_row",
                    "objective_channel": "capacity_risk",
                    "target_label": "risk_path_failed_h40",
                    "usable_for_offline_probe": True,
                    "usable_for_selector_training": False,
                },
                {
                    "causal_status": "non_causal_objective_row",
                    "objective_channel": "ownership_selection",
                    "target_label": "missing_runtime_ownership_label",
                    "usable_for_offline_probe": False,
                    "usable_for_selector_training": False,
                },
            ],
        },
    )
    _write_json(
        root,
        split_v1_module.OWNERSHIP,
        {
            "causal_status": "non_causal_ownership_label_dataset",
            "rows": [
                {
                    "causal_status": "non_causal_ownership_label",
                    "objective_channel": "ownership_selection",
                    "target_label": "selected_owner_failed",
                    "source_stage": "stage5",
                    "usable_for_offline_probe": True,
                    "usable_for_selector_training": False,
                }
            ],
        },
    )

    dataset = split_v1_module.build_dataset()

    assert dataset["summary"]["ownership_selection_available"] is True
    assert dataset["summary"]["ownership_selection_row_count"] == 1
    assert dataset["summary"]["selector_training_row_count"] == 0
    assert dataset["decision"]["selector_training_allowed"] is False


def test_ownership_probe_and_readiness_remain_non_causal(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(probe_module, "ROOT", root)
    monkeypatch.setattr(readiness_module, "ROOT", root)
    ownership_rows = [
        {
            "causal_status": "non_causal_ownership_label",
            "target_label": "selected_owner_converted",
            "owner_positive": True,
            "state_id": "s1",
            "source_stage": "stage5",
            "provider_id": "krk.stage0_basin",
            "provider_family": "stage0_basin",
            "target_provider_best_raw_score": 3.0,
            "target_provider_summary_count": 1,
            "unique_provider_count": 2,
            "source_terms": ["fence_exists"],
        },
        {
            "causal_status": "non_causal_ownership_label",
            "target_label": "selected_owner_failed",
            "owner_positive": False,
            "state_id": "s2",
            "source_stage": "stage5",
            "provider_id": "krk.edge_trap_close",
            "provider_family": "edge_trap",
            "target_provider_best_raw_score": -1.0,
            "target_provider_summary_count": 1,
            "unique_provider_count": 2,
            "source_terms": [],
        },
    ]
    _write_json(
        root,
        probe_module.OWNERSHIP,
        {
            "causal_status": "non_causal_ownership_label_dataset",
            "rows": ownership_rows,
        },
    )
    probe = probe_module.build_probe()
    _write_json(
        root,
        readiness_module.SPLIT,
        {
            "causal_status": "non_causal_split_objective_dataset",
            "summary": {"ownership_selection_available": True, "ownership_selection_row_count": 2},
            "rows": [
                {
                    "objective_channel": "ownership_selection",
                    "target_label": "selected_owner_converted",
                    "source_stage": "stage5",
                    "usable_for_selector_training": False,
                }
            ],
        },
    )
    _write_json(root, readiness_module.OWNERSHIP_PROBE, probe)
    _write_json(
        root,
        readiness_module.CAPACITY_FEATURE_REVIEW,
        {
            "causal_status": "non_causal_feature_review",
            "best_result": {"negative_suppression": 0.7, "positive_recall": 0.9},
        },
    )
    readiness = readiness_module.build_review()

    assert probe["causal_status"] == "non_causal_offline_probe"
    assert probe["runtime_selector_implemented"] is False
    assert probe["decision"]["selector_training_allowed"] is False
    assert readiness["causal_status"] == "non_causal_readiness_review"
    assert readiness["summary"]["ownership_selection_available"] is True
    assert readiness["decision"]["selector_training_allowed"] is False


def test_selected_provider_diversity_label_validation_blocks_runtime_flags():
    payload = {
        "causal_status": "non_causal_label_run",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "summary": {"stage7_training_rows": 0},
        "labels": [
            {
                "causal_status": "non_causal_ownership_outcome_label",
                "source_stage": "stage5",
            }
        ],
    }

    selected_diversity_labels_module.validate_payload(payload)
    payload["runtime_selector_implemented"] = True
    try:
        selected_diversity_labels_module.validate_payload(payload)
    except ValueError as exc:
        assert "runtime_selector_implemented" in str(exc)
    else:
        raise AssertionError("runtime selector flag should be rejected")


def test_ownership_v1_merges_diversity_negatives_without_training_rows(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(ownership_v1_module, "ROOT", root)
    _write_json(
        root,
        ownership_v1_module.OWNERSHIP_V0,
        {
            "causal_status": "non_causal_ownership_label_dataset",
            "rows": [
                {
                    "causal_status": "non_causal_ownership_label",
                    "state_id": "s1",
                    "provider_id": "krk.stage0_basin",
                    "source_stage": "stage5",
                    "target_label": "selected_owner_converted",
                    "owner_positive": True,
                    "label_source": "normal_selected_playout",
                }
            ],
        },
    )
    _write_json(
        root,
        ownership_v1_module.DIVERSITY_LABELS,
        {
            "causal_status": "non_causal_label_run",
            "labels": [
                {
                    "causal_status": "non_causal_ownership_outcome_label",
                    "state_id": "s2",
                    "frame_id": "f2",
                    "source_stage": "stage6",
                    "active_landmark_label": "drive_to_edge",
                    "selected_provider": "krk.stage0_basin",
                    "selected_move": "a1a8",
                    "initial_provider_count": 1,
                    "initial_same_move_providers": [
                        {
                            "provider_id": "krk.stage0_basin",
                            "score": 12.0,
                        }
                    ],
                    "selected_playout_success": {"result": "max_plies", "plies": 40},
                }
            ],
        },
    )

    dataset = ownership_v1_module.build_dataset()

    assert dataset["summary"]["merged_row_count"] == 2
    assert dataset["summary"]["target_label_counts"] == {
        "selected_owner_converted": 1,
        "selected_owner_failed": 1,
    }
    assert dataset["summary"]["selector_training_row_count"] == 0
    assert dataset["decision"]["selector_training_allowed"] is False


def test_ownership_context_dataset_and_probe_are_non_causal(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(context_dataset_module, "ROOT", root)
    monkeypatch.setattr(context_probe_module, "ROOT", root)
    monkeypatch.setattr(context_review_module, "ROOT", root)
    reports = root / "reports"
    reports.mkdir()
    _write_json(
        root,
        context_dataset_module.OWNERSHIP,
        {
            "causal_status": "non_causal_ownership_label_dataset",
            "rows": [
                {
                    "causal_status": "non_causal_ownership_label",
                    "state_id": "state.a",
                    "frame_id": "cp.krk.state.a",
                    "source_stage": "stage5",
                    "active_landmark_label": "fence_established",
                    "provider_id": "krk.stage0_basin",
                    "provider_family": "stage0_basin",
                    "move_uci": "h7h8",
                    "target_label": "selected_owner_converted",
                    "owner_positive": True,
                    "target_provider_best_raw_score": 12.0,
                    "unique_provider_count": 1,
                    "target_provider_summary_count": 1,
                    "source_terms": [],
                    "usable_for_selector_training": False,
                },
                {
                    "causal_status": "non_causal_ownership_label",
                    "state_id": "state.b",
                    "frame_id": "cp.krk.state.b",
                    "source_stage": "stage6",
                    "active_landmark_label": "drive_to_edge",
                    "provider_id": "krk.stage0_basin",
                    "provider_family": "stage0_basin",
                    "move_uci": "a4a8",
                    "target_label": "selected_owner_failed",
                    "owner_positive": False,
                    "target_provider_best_raw_score": 8.0,
                    "unique_provider_count": 1,
                    "target_provider_summary_count": 1,
                    "source_terms": [],
                    "usable_for_selector_training": False,
                },
            ],
        },
    )
    for source in context_dataset_module.LABEL_SOURCES:
        _write_json(root, source, {"causal_status": "non_causal_label_run", "labels": []})
    for source in context_dataset_module.FRAME_SOURCES:
        _write_json(
            root,
            source,
            {
                "causal_status": "non_causal_frame_export",
                "frames": [
                    {
                        "state_id": "state.a",
                        "fen": "5k2/7R/1K6/8/8/8/8/8 w - - 2 2",
                    },
                    {
                        "state_id": "state.b",
                        "fen": "8/8/8/8/R7/2k5/4K3/8 w - - 2 2",
                    },
                ],
            },
        )

    dataset = context_dataset_module.build_dataset()
    (reports / "krk_ownership_selection_context_dataset_v0.json").write_text(
        json.dumps(dataset),
        encoding="utf-8",
    )
    probe = context_probe_module.build_probe()
    (reports / "krk_ownership_selection_context_feature_probe_v0.json").write_text(
        json.dumps(probe),
        encoding="utf-8",
    )
    _write_json(
        root,
        context_review_module.BASE_PROBE,
        {
            "causal_status": "non_causal_offline_probe",
            "best_result": {"negative_suppression": 0.0, "positive_recall": 0.0},
        },
    )
    review = context_review_module.build_review()

    assert dataset["summary"]["fen_join_count"] == 2
    assert dataset["summary"]["selector_training_row_count"] == 0
    assert probe["causal_status"] == "non_causal_offline_probe"
    assert probe["decision"]["selector_training_allowed"] is False
    assert "best_balanced_result" in probe
    assert review["runtime_selector_implemented"] is False
    assert review["decision"]["runtime_work_allowed"] is False


def test_ownership_v3_recovers_selected_provider_group_label(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(ownership_v3_module, "ROOT", root)
    _write_json(
        root,
        ownership_v3_module.OWNERSHIP_V2,
        {
            "causal_status": "non_causal_ownership_label_dataset",
            "rows": [],
        },
    )
    _write_json(
        root,
        ownership_v3_module.SELECTOR_FEATURES,
        {
            "causal_status": "non_causal_feature_dataset",
            "rows": [
                {
                    "target_kind": "selected_playout_success",
                    "usable_for_training": True,
                    "source_stage": "stage5",
                    "state_id": "state.fence",
                    "frame_id": "cp.krk.state.fence",
                    "active_landmark_label": "fence_established",
                    "provider_id": "krk.edge_trap_close",
                    "selected_provider_before_observation": "krk.fence_established",
                    "selected_provider_matches_target": False,
                    "move_uci": "h7c7",
                    "label": "negative",
                    "provider_summary": {"krk.fence_established": 1},
                    "unique_provider_count": 2,
                    "all_suggestion_count": 3,
                    "source_terms": ["fence_needs_repair"],
                    "source_term_count": 1,
                }
            ],
        },
    )

    dataset = ownership_v3_module.build_dataset()

    assert dataset["summary"]["supplemental_row_count"] == 1
    assert dataset["summary"]["provider_family_counts"] == {"fence_established": 1}
    assert dataset["rows"][0]["target_label"] == "selected_owner_failed"
    assert dataset["rows"][0]["usable_for_selector_training"] is False
    assert dataset["decision"]["runtime_work_allowed"] is False


def test_targeted_non_stage0_manifest_excludes_stage7_and_stage0(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(targeted_manifest_module, "ROOT", root)
    monkeypatch.setattr(
        targeted_manifest_module,
        "STAGE_CONFIGS",
        {
            "stage5": {
                "label": "fence_established",
                "stage_role": "stage5_fence_handoff",
            },
            "stage6": {
                "label": "drive_to_edge",
                "stage_role": "stage6_drive_to_edge",
            },
        },
    )
    monkeypatch.setattr(
        targeted_manifest_module,
        "_binding_for_stage",
        lambda stage: {
            "topology_path": "topology.json",
            "source_checkpoint": "checkpoint.pkl",
            "composition_profile": "handoff_composition_v1",
            "topology_version": "stage6_overlay_composed_v1",
        },
    )
    (root / "topology.json").write_text("{}", encoding="utf-8")
    (root / "checkpoint.pkl").write_text("checkpoint", encoding="utf-8")
    _write_json(
        root,
        targeted_manifest_module.SOURCE,
        {
            "causal_status": "non_causal_labeled_observation_controls",
            "records": [
                {
                    "state_id": "state.edge",
                    "frame_id": "cp.krk.state.edge",
                    "source_stage": "stage5",
                    "active_landmark_label": "fence_established",
                    "fen": "6k1/4R3/6K1/8/8/8/8/8 w - - 2 2",
                    "observation": {"selected_provider": "krk.edge_trap_close"},
                },
                {
                    "state_id": "state.stage0",
                    "source_stage": "stage5",
                    "fen": "6k1/4R3/6K1/8/8/8/8/8 w - - 2 2",
                    "observation": {"selected_provider": "krk.stage0_basin"},
                },
                {
                    "state_id": "state.stage7",
                    "source_stage": "stage7",
                    "fen": "6k1/4R3/6K1/8/8/8/8/8 w - - 2 2",
                    "observation": {"selected_provider": "krk.edge_trap_close"},
                },
            ],
        },
    )

    manifest = targeted_manifest_module.build_manifest(root)

    assert manifest["causal_status"] == "non_causal_execution_manifest"
    assert manifest["binding_summary"]["job_count"] == 1
    assert manifest["binding_summary"]["stage7_job_count"] == 0
    assert manifest["jobs"][0]["historical_selected_provider"] == "krk.edge_trap_close"
    assert manifest["decision"]["selector_training_allowed"] is False
    assert manifest["runtime_behavior_changed"] is False


def test_targeted_non_stage0_label_and_review_validation_blocks_runtime_flags(tmp_path, monkeypatch):
    label_payload = {
        "causal_status": "non_causal_label_run",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "selector_training_allowed": False,
        "labels": [
            {
                "causal_status": "non_causal_outcome_label",
                "source_stage": "stage5",
                "selected_playout_success": {"result": "mate"},
            }
        ],
    }
    targeted_labels_module.validate_payload(label_payload)
    label_payload["selector_training_allowed"] = True
    try:
        targeted_labels_module.validate_payload(label_payload)
    except ValueError as exc:
        assert "selector_training_allowed" in str(exc)
    else:
        raise AssertionError("selector training flag should be rejected")

    review_payload = {
        "causal_status": "non_causal_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "selector_training_allowed": False,
    }
    targeted_review_module.validate_review(review_payload)
    review_payload["runtime_arbiter_implemented"] = True
    try:
        targeted_review_module.validate_review(review_payload)
    except ValueError as exc:
        assert "runtime_arbiter_implemented" in str(exc)
    else:
        raise AssertionError("runtime arbiter flag should be rejected")


def test_ownership_v4_targeted_labels_supersede_stale_nonstage0_labels(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(ownership_v4_module, "ROOT", root)
    _write_json(
        root,
        ownership_v4_module.OWNERSHIP_V3,
        {
            "causal_status": "non_causal_ownership_label_dataset",
            "rows": [
                {
                    "causal_status": "non_causal_ownership_label",
                    "state_id": "state.edge",
                    "frame_id": "cp.krk.state.edge",
                    "source_stage": "stage5",
                    "active_landmark_label": "fence_established",
                    "provider_id": "krk.edge_trap_close",
                    "provider_family": "edge_trap",
                    "move_uci": "h7c7",
                    "target_label": "selected_owner_failed",
                    "owner_positive": False,
                    "label_source": "normal_selected_playout",
                    "usable_for_selector_training": False,
                }
            ],
        },
    )
    _write_json(
        root,
        ownership_v4_module.TARGETED_LABELS,
        {
            "causal_status": "non_causal_label_run",
            "labels": [
                {
                    "causal_status": "non_causal_outcome_label",
                    "state_id": "state.edge",
                    "frame_id": "cp.krk.state.edge",
                    "source_stage": "stage5",
                    "active_landmark_label": "fence_established",
                    "current_profile_selected_provider": "krk.edge_trap_close",
                    "current_profile_selected_move": "h7c7",
                    "historical_selected_provider": "krk.edge_trap_close",
                    "historical_selection_preserved": True,
                    "initial_provider_count": 1,
                    "initial_same_move_providers": [
                        {"provider_id": "krk.edge_trap_close", "score": 3.0}
                    ],
                    "selected_playout_success": {"result": "mate", "plies": 3},
                    "forced_provider_conversion_for_selected_provider": {"result": "mate"},
                }
            ],
        },
    )
    _write_json(
        root,
        ownership_v4_module.TARGETED_REVIEW,
        {"causal_status": "non_causal_review"},
    )

    dataset = ownership_v4_module.build_dataset()

    assert dataset["summary"]["merged_row_count"] == 1
    assert dataset["summary"]["targeted_label_change_count"] == 1
    assert dataset["rows"][0]["target_label"] == "selected_owner_converted"
    assert dataset["rows"][0]["prior_target_label"] == "selected_owner_failed"
    assert dataset["rows"][0]["usable_for_selector_training"] is False
    assert dataset["decision"]["selector_training_allowed"] is False


def test_targeted_negative_manifest_and_labels_remain_non_causal():
    manifest = {
        "causal_status": "non_causal_execution_manifest",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "labels_generated_in_this_slice": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "jobs": [
            {
                "causal_status": "non_causal_label_job",
                "source_stage": "stage5",
            }
        ],
    }
    targeted_negative_manifest_module.validate_manifest(manifest)
    manifest["runtime_selector_implemented"] = True
    try:
        targeted_negative_manifest_module.validate_manifest(manifest)
    except ValueError as exc:
        assert "runtime_selector_implemented" in str(exc)
    else:
        raise AssertionError("runtime selector flag should be rejected")

    labels = {
        "causal_status": "non_causal_label_run",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "selector_training_allowed": False,
        "labels": [
            {
                "causal_status": "non_causal_outcome_label",
                "source_stage": "stage5",
            }
        ],
    }
    targeted_negative_labels_module.validate_payload(labels)
    labels["stage8_training_allowed"] = True
    try:
        targeted_negative_labels_module.validate_payload(labels)
    except ValueError as exc:
        assert "stage8_training_allowed" in str(exc)
    else:
        raise AssertionError("stage8 training flag should be rejected")


def test_ownership_v5_merges_targeted_negative_labels_without_training_rows(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(ownership_v5_module, "ROOT", root)
    _write_json(
        root,
        ownership_v5_module.OWNERSHIP_V4,
        {
            "causal_status": "non_causal_ownership_label_dataset",
            "rows": [],
        },
    )
    _write_json(
        root,
        ownership_v5_module.TARGETED_NEGATIVE_LABELS,
        {
            "causal_status": "non_causal_label_run",
            "labels": [
                {
                    "causal_status": "non_causal_outcome_label",
                    "state_id": "state.neg",
                    "frame_id": "cp.krk.state.neg",
                    "source_stage": "stage4",
                    "active_landmark_label": "edge_trap_wrong_tempo",
                    "selected_provider": "krk.stage0_basin",
                    "selected_move": "a1a8",
                    "initial_provider_count": 1,
                    "target_cell_id": "stage4_stage0_wrong_tempo_like",
                    "target_cell_reason": "test",
                    "label_semantics": "current_profile_selected_owner_outcome_in_false_positive_risk_cell",
                    "selected_playout_success": {"result": "max_plies"},
                }
            ],
        },
    )

    dataset = ownership_v5_module.build_dataset()

    assert dataset["summary"]["targeted_added_row_count"] == 1
    assert dataset["summary"]["target_label_counts"] == {"selected_owner_failed": 1}
    assert dataset["rows"][0]["usable_for_selector_training"] is False
    assert dataset["decision"]["selector_training_allowed"] is False


def test_paired_ownership_label_ordering():
    selected_failed = {"target_label": "selected_owner_failed", "owner_positive": False}
    selected_mate = {"target_label": "selected_owner_converted", "owner_positive": True}
    capacity_mate = {"capacity_label": "positive_capacity"}
    capacity_failed = {"capacity_label": "negative_capacity"}

    assert paired_inventory_v1_module._comparison_label(selected_failed, capacity_mate) == (
        "prefer_capacity_alternative",
        "strong_same_state_conflict",
    )
    assert paired_inventory_v1_module._comparison_label(selected_mate, capacity_failed) == (
        "prefer_selected_owner",
        "strong_same_state_conflict",
    )
    assert paired_inventory_v1_module._comparison_label(selected_mate, capacity_mate) == (
        "equivalent_positive_or_preserve_selected",
        "safe_preservation",
    )


def test_paired_inventory_validation_blocks_runtime_flags():
    payload = {
        "causal_status": "non_causal_pair_inventory",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "selector_training_allowed": False,
        "summary": {"stage7_row_count": 0},
        "rows": [
            {
                "causal_status": "non_causal_pair_label",
                "usable_for_selector_training": False,
            }
        ],
    }
    paired_inventory_v1_module.validate_inventory(payload)
    payload["runtime_selector_implemented"] = True
    try:
        paired_inventory_v1_module.validate_inventory(payload)
    except ValueError as exc:
        assert "runtime_selector_implemented" in str(exc)
    else:
        raise AssertionError("runtime selector flag should be rejected")


def test_paired_probe_and_review_validation_blocks_causal_flags():
    probe = {
        "causal_status": "non_causal_offline_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "selector_training_allowed": False,
        "summary": {"stage7_row_count": 0},
    }
    paired_probe_module.validate_probe(probe)
    probe["selector_training_allowed"] = True
    try:
        paired_probe_module.validate_probe(probe)
    except ValueError as exc:
        assert "selector_training_allowed" in str(exc)
    else:
        raise AssertionError("selector training flag should be rejected")

    review = {
        "causal_status": "non_causal_architecture_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "selector_training_allowed": False,
    }
    paired_review_module.validate_review(review)
    review["stage7_promotion_allowed"] = True
    try:
        paired_review_module.validate_review(review)
    except ValueError as exc:
        assert "stage7_promotion_allowed" in str(exc)
    else:
        raise AssertionError("Stage 7 promotion flag should be rejected")


def test_safe_preservation_gate_preserves_selected_mate_and_prefers_failed_selected():
    selected_mate_forced_mate = {
        "owner_a_positive": True,
        "owner_b_positive": True,
        "evidence_channel": "safe_preservation",
    }
    selected_failed_forced_mate = {
        "owner_a_positive": False,
        "owner_b_positive": True,
        "evidence_channel": "strong_same_state_conflict",
    }
    selected_mate_forced_failed = {
        "owner_a_positive": True,
        "owner_b_positive": False,
        "evidence_channel": "strong_same_state_conflict",
    }

    assert paired_probe_v1_module.safe_preservation_gate_predict(selected_mate_forced_mate) is False
    assert paired_probe_v1_module.conflict_only_predict(selected_mate_forced_mate) is False
    assert paired_probe_v1_module.safe_preservation_gate_predict(selected_failed_forced_mate) is True
    assert paired_probe_v1_module.conflict_only_predict(selected_failed_forced_mate) is True
    assert paired_probe_v1_module.safe_preservation_gate_predict(selected_mate_forced_failed) is False
    assert paired_probe_v1_module.conflict_only_predict(selected_mate_forced_failed) is False


def test_runtime_review_packet_does_not_authorize_implementation():
    packet = {
        "causal_status": "non_causal_runtime_review_packet",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "selector_training_allowed": False,
        "implementation_allowed_by_this_packet": False,
    }
    paired_packet_module.validate_packet(packet)
    packet["implementation_allowed_by_this_packet"] = True
    try:
        paired_packet_module.validate_packet(packet)
    except ValueError as exc:
        assert "implementation_allowed_by_this_packet" in str(exc)
    else:
        raise AssertionError("runtime review packet must not authorize implementation")


def test_runtime_proxy_design_dataset_and_probe_remain_non_causal(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(runtime_proxy_module, "ROOT", root)
    reports = root / "reports"
    reports.mkdir()
    _write_json(
        root,
        runtime_proxy_module.RUNTIME_PACKET,
        {
            "causal_status": "non_causal_runtime_review_packet",
            "runtime_behavior_changed": False,
            "runtime_defaults_changed": False,
            "runtime_selector_implemented": False,
            "runtime_candidate_generator_implemented": False,
            "runtime_terminals_added": False,
            "runtime_dtm_or_tablebase_lookup": False,
            "gameplay_topology_mutation": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "selector_training_allowed": False,
            "implementation_allowed_by_this_packet": False,
        },
    )
    _write_json(root, runtime_proxy_module.PROBE_V1, {"causal_status": "non_causal_offline_probe"})
    _write_json(root, runtime_proxy_module.ERROR_AUDIT, {"causal_status": "non_causal_error_audit"})
    _write_json(
        root,
        runtime_proxy_module.INVENTORY,
        {
            "causal_status": "non_causal_pair_inventory",
            "rows": [
                {
                    "causal_status": "non_causal_pair_label",
                    "source_stage": "stage5",
                    "state_id": "state.safe",
                    "frame_id": "cp.safe",
                    "active_landmark_label": "fence_established",
                    "owner_a": "krk.fence_established",
                    "owner_a_family": "fence_established",
                    "owner_a_evidence_channel": "normal_selected_playout",
                    "owner_a_positive": True,
                    "owner_a_outcome": "selected_owner_converted",
                    "owner_b": "krk.edge_trap_close",
                    "owner_b_family": "edge_trap",
                    "owner_b_evidence_channel": "forced_capacity",
                    "owner_b_role": "forced_capacity_alternative",
                    "owner_b_positive": True,
                    "owner_b_outcome": "positive_capacity",
                    "comparison_label": "equivalent_positive_or_preserve_selected",
                    "safe_preservation_pair": True,
                    "context_terms": ["selected_piece:rook", "box_area_delta:same"],
                    "terminal_space_context": {
                        "black_king_edge_bucket": "edge",
                        "box_area_relevance": "low",
                        "white_king_support_bucket": "close",
                        "rook_safe_proxy": True,
                    },
                },
                {
                    "causal_status": "non_causal_pair_label",
                    "source_stage": "stage5",
                    "state_id": "state.risk",
                    "frame_id": "cp.risk",
                    "active_landmark_label": "fence_established",
                    "owner_a": "krk.stage0_basin",
                    "owner_a_family": "stage0_basin",
                    "owner_a_evidence_channel": "normal_selected_playout",
                    "owner_a_positive": False,
                    "owner_a_outcome": "selected_owner_failed",
                    "owner_b": "krk.edge_trap_close",
                    "owner_b_family": "edge_trap",
                    "owner_b_evidence_channel": "forced_capacity",
                    "owner_b_role": "forced_capacity_alternative",
                    "owner_b_positive": True,
                    "owner_b_outcome": "positive_capacity",
                    "comparison_label": "prefer_capacity_alternative",
                    "safe_preservation_pair": False,
                    "context_terms": ["selected_piece:king", "box_area_delta:same"],
                    "terminal_space_context": {
                        "black_king_edge_bucket": "edge",
                        "box_area_relevance": "low",
                        "white_king_support_bucket": "medium",
                        "rook_safe_proxy": True,
                    },
                },
                {
                    "causal_status": "non_causal_pair_label",
                    "source_stage": "stage7",
                    "state_id": "state.stage7",
                    "owner_a": "krk.box_shrink",
                    "owner_b": "krk.edge_trap_close",
                    "comparison_label": "prefer_capacity_alternative",
                },
            ],
        },
    )

    design, dataset, probe, review = runtime_proxy_module.build_all()

    assert design["causal_status"] == "non_causal_proxy_design"
    assert dataset["summary"]["stage7_row_count"] == 0
    assert dataset["summary"]["selector_training_row_count"] == 0
    assert probe["causal_status"] == "non_causal_proxy_probe"
    assert review["causal_status"] == "non_causal_architecture_review"
    assert review["implementation_allowed_by_this_review"] is False
    assert review["runtime_selector_implemented"] is False
    assert all(row["usable_for_selector_training"] is False for row in dataset["rows"])


def test_runtime_proxy_forbidden_outcome_features_are_not_runtime_eligible():
    row = {
        "runtime_visible_candidate_features": {
            "selected_owner_family": "stage0_basin",
            "alternative_owner_family": "edge_trap",
            "source_stage": "stage5",
        },
        "offline_outcome_forbidden_features": {
            "owner_a_positive": False,
            "owner_b_positive": True,
        },
    }

    offline_model = runtime_proxy_module._rule_model(
        [row],
        model_id="offline_semantic_selected_failed_alt_positive",
        target_name="selected_owner_failure_risk_target",
        runtime_feature_eligible=False,
        notes="test",
    )

    assert offline_model["runtime_feature_eligible"] is False
    assert offline_model["predictions"][0]["predicted_positive"] is True


def test_selected_owner_failure_risk_terms_identify_visible_proxy_without_causal_flags(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(failure_risk_terms_module, "ROOT", root)
    reports = root / "reports"
    reports.mkdir()
    _write_json(
        root,
        failure_risk_terms_module.CONTEXT_DATASET,
        {
            "causal_status": "non_causal_context_feature_dataset",
            "rows": [
                {
                    "source_stage": "stage5",
                    "state_id": "state.risk",
                    "provider_id": "krk.stage0_basin",
                    "source_terms": ["edge_trap_shape_available"],
                },
                {
                    "source_stage": "stage5",
                    "state_id": "state.safe",
                    "provider_id": "krk.fence_established",
                    "source_terms": [],
                },
            ],
        },
    )
    _write_json(
        root,
        failure_risk_terms_module.PROXY_DATASET,
        {
            "causal_status": "non_causal_proxy_validation_dataset",
            "rows": [
                {
                    "source_stage": "stage5",
                    "state_id": "state.risk",
                    "owner_a": "krk.stage0_basin",
                    "owner_b": "krk.edge_trap_close",
                    "comparison_label": "prefer_capacity_alternative",
                    "selected_owner_failure_risk_target": True,
                    "safe_preservation_confidence_target": False,
                    "runtime_visible_candidate_features": {
                        "family_pair": "stage0_basin->edge_trap",
                        "selected_piece": "king",
                        "box_area_delta": "same",
                        "rook_distance_delta": "worsens",
                        "active_landmark_label": "fence_established",
                    },
                },
                {
                    "source_stage": "stage5",
                    "state_id": "state.safe",
                    "owner_a": "krk.fence_established",
                    "owner_b": "krk.edge_trap_close",
                    "comparison_label": "equivalent_positive_or_preserve_selected",
                    "selected_owner_failure_risk_target": False,
                    "safe_preservation_confidence_target": True,
                    "runtime_visible_candidate_features": {
                        "family_pair": "fence_established->edge_trap",
                        "selected_piece": "rook",
                        "box_area_delta": "same",
                        "rook_distance_delta": "improves",
                        "active_landmark_label": "fence_established",
                    },
                },
            ],
        },
    )

    terms, probe, review = failure_risk_terms_module.build_all()

    assert terms["summary"]["stage7_row_count"] == 0
    assert terms["summary"]["selector_training_row_count"] == 0
    assert probe["candidate_proxy"]["true_positive"] == 1
    assert probe["candidate_proxy"]["false_positive"] == 0
    assert probe["decision"]["runtime_work_allowed"] is False
    assert review["implementation_allowed_by_this_review"] is False
    assert review["runtime_selector_implemented"] is False


def test_failure_risk_terms_validation_rejects_runtime_behavior():
    payload = {
        "causal_status": "non_causal_architecture_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "selector_training_allowed": False,
        "implementation_allowed_by_this_review": False,
        "summary": {"stage7_row_count": 0, "selector_training_row_count": 0},
    }
    failure_risk_terms_module._validate_non_causal(payload)
    payload["runtime_terminals_added"] = True
    try:
        failure_risk_terms_module._validate_non_causal(payload)
    except ValueError as exc:
        assert "runtime_terminals_added" in str(exc)
    else:
        raise AssertionError("runtime terminal flag should be rejected")


def test_independent_failure_risk_validation_builds_packet_only_on_pass():
    labels = {
        "summary": {"stage7_training_rows": 0, "manifest_selected_provider_preserved_count": 2, "manifest_proxy_firing_preserved_count": 2},
        "labels": [
            {
                "proxy_fires": True,
                "selected_owner_failure_risk_target": True,
            },
            {
                "proxy_fires": False,
                "selected_owner_failure_risk_target": False,
            },
        ],
    }

    validation = failure_risk_validation_module.build_validation(labels)
    packet = failure_risk_validation_module.build_packet(validation)

    assert validation["decision"]["status"] == "independent_proxy_validation_passed"
    assert packet is not None
    assert packet["implementation_allowed_by_this_packet"] is False
    assert packet["runtime_selector_implemented"] is False

    failed_labels = {
        "summary": {"stage7_training_rows": 0, "manifest_selected_provider_preserved_count": 2, "manifest_proxy_firing_preserved_count": 2},
        "labels": [
            {
                "proxy_fires": True,
                "selected_owner_failure_risk_target": False,
            },
            {
                "proxy_fires": False,
                "selected_owner_failure_risk_target": True,
            },
        ],
    }
    failed_validation = failure_risk_validation_module.build_validation(failed_labels)

    assert failed_validation["decision"]["status"] == "independent_proxy_validation_failed_or_underpowered"
    assert failure_risk_validation_module.build_packet(failed_validation) is None


def test_independent_failure_risk_validation_rejects_causal_flags():
    payload = {
        "causal_status": "non_causal_proxy_validation",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "selector_training_allowed": False,
        "implementation_allowed_by_this_validation": False,
        "summary": {"stage7_row_count": 0},
    }
    failure_risk_validation_module._validate_non_causal(payload)
    payload["runtime_selector_implemented"] = True
    try:
        failure_risk_validation_module._validate_non_causal(payload)
    except ValueError as exc:
        assert "runtime_selector_implemented" in str(exc)
    else:
        raise AssertionError("runtime selector flag should be rejected")
