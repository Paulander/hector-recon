import json

from recon_lite_chess.autogrowth import (
    FORBIDDEN_LEARNER_TERMS,
    TraceCollectionConfig,
    collect_trace_records,
    validate_learner_record,
)


def test_m4_trace_collection_is_train_only_and_firewall_clean() -> None:
    result = collect_trace_records(
        config=TraceCollectionConfig(
            seed=42,
            train_count=4,
            horizon=8,
        )
    )
    payload = result.to_dict()

    assert payload["schema_version"] == "krk_autogrowth_m4_traces.v0"
    assert payload["dataset"]["source_split"] == "train"
    assert payload["dataset"]["heldout_used_for_trace"] is False
    assert payload["dataset"]["train_count"] == 4
    assert payload["summary"]["trace_record_count"] == len(payload["records"])
    assert payload["summary"]["behavior_change_applied"] is False
    assert payload["summary"]["candidate_behavior_enabled"] is False
    assert payload["summary"]["runtime_tablebase_or_dtm_move_source"] is False
    assert payload["summary"]["white_action_count"] >= len(payload["records"])
    assert payload["records"]

    serialized = json.dumps(payload["records"], sort_keys=True).lower()
    for term in FORBIDDEN_LEARNER_TERMS:
        assert term not in serialized
    validate_learner_record(payload["records"])


def test_m4_trace_records_are_terminal_action_terminal_inputs() -> None:
    result = collect_trace_records(
        config=TraceCollectionConfig(
            seed=11,
            train_count=2,
            horizon=6,
        )
    )

    for record in result.records:
        assert record["source_split"] == "train"
        assert record["before_features"]
        assert record["after_features"]
        assert record["action"]["uci"]
        assert set(record["progress_deltas"]) == set(record["before_features"])
        assert record["recon_growth_view"]["before_node_type"] == "TERMINAL"
        assert record["recon_growth_view"]["action_node_type"] == "ACTION"
        assert record["recon_growth_view"]["after_node_type"] == "TERMINAL"
        assert record["recon_growth_view"]["script_node_type"] == "SCRIPT"
        assert record["recon_growth_view"]["allowed_relation_types"] == ["SUB", "SUR", "POR", "RET"]
        assert record["recon_growth_view"]["behavior_change_applied"] is False
        assert record["recon_growth_view"]["external_action_ranking_applied"] is False
        assert record["candidate_mining_input"]["terminal_action_terminal"] is True
        assert record["candidate_mining_input"]["runtime_behavior_change"] is False
        assert record["candidate_mining_input"]["external_action_ranking"] is False
        assert record["rollout_credit"]["runtime_move_source"] is False


def test_m4_trace_artifact_writes_json(tmp_path) -> None:
    result = collect_trace_records(
        config=TraceCollectionConfig(
            seed=5,
            train_count=3,
            horizon=5,
        )
    )
    output = result.write_json(tmp_path / "traces.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_m4_traces.v0"
    assert payload["summary"]["trace_record_count"] == len(payload["records"])
    assert payload["summary"]["terminal_outcomes"]
