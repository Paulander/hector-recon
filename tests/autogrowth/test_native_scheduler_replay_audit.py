from recon_lite_chess.autogrowth import (
    NativeSchedulerReplayAuditConfig,
    run_native_scheduler_replay_audit,
)


def test_tg26q_smoke_replay_audit_reports_required_sections() -> None:
    result = run_native_scheduler_replay_audit(
        config=NativeSchedulerReplayAuditConfig(
            replay_repetitions=1,
            include_symmetries=False,
            generated_mate1_heldout_count=1,
            generated_mate2_heldout_count=0,
            equivalence_mate1_positions=1,
            equivalence_mate2_positions=0,
            max_samples=4,
        )
    )

    payload = result.to_dict()
    assert payload["checkpoint"] == "TG26q_native_scheduler_replay_heldout_equivalence_audit"
    assert payload["replay"]["repetition_count"] == 1
    assert payload["replay"]["rows"][0]["mate1_total"] == payload["dataset"]["curated_mate1_count"]
    assert "generated_heldout" in payload
    assert "scheduler_equivalence" in payload
    assert "ablations" in payload
    assert "graph_diagnostics" in payload
    assert payload["purity_boundary"]["direct_provider_override"] is False
    assert payload["purity_boundary"]["runtime_tablebase_or_dtm_move_source"] is False
    assert "random legal KRK generators" in payload["dataset"]["generated_source"]
    assert len(payload["generated_heldout"]["mate1_fens"]) == 1
    assert payload["generated_heldout"]["stage_labels_learner_visible"] is False
