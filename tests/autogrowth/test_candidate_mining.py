import json

from recon_lite_chess.autogrowth import (
    CandidateMiningConfig,
    FORBIDDEN_LEARNER_TERMS,
    TraceCollectionConfig,
    collect_trace_records,
    mine_triplet_candidates_from_records,
    validate_learner_record,
)


def _small_mining_payload():
    trace = collect_trace_records(
        config=TraceCollectionConfig(
            seed=202,
            train_count=12,
            horizon=14,
        )
    )
    return mine_triplet_candidates_from_records(
        records=trace.records,
        trace_schema_version="test_trace_schema",
        trace_digest="test_digest",
        source_summary=trace.summary,
        config=CandidateMiningConfig(
            min_support=2,
            max_candidates=5,
            source_trace_path="memory",
        ),
    ).to_dict()


def test_m4_candidate_mining_outputs_firewall_clean_records() -> None:
    payload = _small_mining_payload()

    assert payload["schema_version"] == "krk_autogrowth_m4_candidates.v0"
    assert payload["summary"]["candidate_count"] > 0
    assert payload["summary"]["behavior_change_applied"] is False
    assert payload["summary"]["candidate_spawned"] is False
    assert payload["summary"]["candidate_active_in_runtime"] is False
    assert payload["summary"]["ready_for_m5_sandbox"] is True

    serialized = json.dumps(payload["candidates"], sort_keys=True).lower()
    for term in FORBIDDEN_LEARNER_TERMS:
        assert term not in serialized
    validate_learner_record(payload["candidates"])


def test_m4_top_candidate_is_recon_topology_plan_not_action_override() -> None:
    payload = _small_mining_payload()
    top = payload["candidates"][0]

    assert top["rank"] == 1
    assert top["selected_for_m5"] is True
    assert top["status"] == "m4_mined_not_spawned"
    assert top["behavior_change_applied"] is False
    assert top["candidate_active_in_runtime"] is False
    assert top["recon_topology_plan"]["node_types"] == ["TERMINAL", "ACTION", "TERMINAL", "SCRIPT"]
    assert top["recon_topology_plan"]["relation_types"] == ["SUB", "SUR", "POR", "RET"]
    assert top["recon_topology_plan"]["spawned_now"] is False
    assert top["recon_topology_plan"]["m3_update_count"] == 0
    assert top["recon_topology_plan"]["m4_event_count"] == 0
    assert top["evidence"]["support_count"] >= 2
    assert top["evidence"]["position_count"] >= 1
    assert top["before_cluster"]["prototype"]
    assert top["after_delta_cluster"]["prototype"]
    assert set(top["action_schema"]) == {
        "piece_type",
        "file_delta_sign",
        "rank_delta_sign",
        "file_delta_magnitude",
        "rank_delta_magnitude",
        "gives_check",
        "is_capture",
    }


def test_m4_candidate_artifact_writes_json(tmp_path) -> None:
    trace = collect_trace_records(
        config=TraceCollectionConfig(
            seed=303,
            train_count=8,
            horizon=12,
        )
    )
    result = mine_triplet_candidates_from_records(
        records=trace.records,
        trace_schema_version="test_trace_schema",
        trace_digest="test_digest",
        source_summary=trace.summary,
        config=CandidateMiningConfig(
            min_support=2,
            max_candidates=3,
            source_trace_path="memory",
        ),
    )
    output = result.write_json(tmp_path / "candidates.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["summary"]["candidate_count"] == len(payload["candidates"])
    assert payload["summary"]["selected_candidate_key"] == payload["candidates"][0]["candidate_key"]
