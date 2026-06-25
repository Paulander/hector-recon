from pathlib import Path

from recon_lite_chess.autogrowth import ContinuationCandidateRetrievalRepairConfig, run_continuation_candidate_retrieval_repair


def test_tg29r_baseline_only_keeps_retrieval_labels_trainer_side(tmp_path: Path) -> None:
    result = run_continuation_candidate_retrieval_repair(
        config=ContinuationCandidateRetrievalRepairConfig(
            run_real_context=False,
            max_blocked_turns=0,
            base=ContinuationCandidateRetrievalRepairConfig().base.__class__(
                progress_output=str(tmp_path / "progress.json"),
            ),
        )
    )

    output = result.write_json(tmp_path / "tg29r.json")
    decision = result.decision
    assert output.exists()
    assert Path(result.config.base.progress_output).exists()
    assert decision["checkpoint_pass"] is False
    assert decision["repair_applied"] is False
    assert decision["blocked_turn_count"] == 0
    assert decision["continuation_positive_candidate_count"] == 0
    assert decision["foundation_frozen"] is True
    assert decision["continuation_labels_learner_visible"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["direct_provider_override"] is False
