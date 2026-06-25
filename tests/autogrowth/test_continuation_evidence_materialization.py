from pathlib import Path

from recon_lite_chess.autogrowth import ContinuationEvidenceMaterializationConfig, run_continuation_evidence_materialization


def test_tg29s_tiers_continuation_positive_without_learner_label_leak(tmp_path: Path) -> None:
    result = run_continuation_evidence_materialization(
        config=ContinuationEvidenceMaterializationConfig(
            base=ContinuationEvidenceMaterializationConfig().base.__class__(
                progress_output=str(tmp_path / "progress.json"),
            )
        )
    )

    output = result.write_json(tmp_path / "tg29s.json")
    decision = result.decision
    assert output.exists()
    assert Path(result.config.base.progress_output).exists()
    assert decision["checkpoint_pass"] is True
    assert decision["repair_applied"] is False
    assert decision["continuation_positive_candidate_count"] == 81
    assert decision["continuation_label_too_broad"] is True
    assert (
        decision["strong_continuation_positive_count"] + decision["partial_continuation_positive_count"]
        < decision["continuation_positive_candidate_count"]
    )
    assert decision["continuation_labels_learner_visible"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["direct_provider_override"] is False
