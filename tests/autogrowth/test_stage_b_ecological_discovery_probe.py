from pathlib import Path

from recon_lite_chess.autogrowth.stage_b_ecological_discovery_probe import (
    StageBEcologicalDiscoveryConfig,
    run_stage_b_ecological_discovery_probe,
)


def test_phase29e_stage_b_ecological_probe_keeps_arms_quarantined(tmp_path: Path) -> None:
    summary = run_stage_b_ecological_discovery_probe(
        config=StageBEcologicalDiscoveryConfig(
            output_dir=str(tmp_path / "phase2_9e_probe"),
            seeds=(20272931,),
            train_row_limit=2,
            heldout_row_limit=2,
            max_population=4,
            max_guided_births=4,
            max_births_per_decision=1,
            max_samples=2,
        )
    )

    assert (tmp_path / "phase2_9e_probe" / "design_spec.json").exists()
    assert (tmp_path / "phase2_9e_probe" / "summary.json").exists()
    assert summary["decision"]["all_arm1_load_bearing_zero"] in {True, False}

    result = summary["seed_results"]["20272931"]
    arm1 = result["arm1_unguided_ecological"]
    arm2 = result["arm2_guided_residual_control"]

    assert arm1["autogrowth_evidence"] is True
    assert arm1["uses_oracle_birth"] is False
    assert arm1["structure"]["oracle_targeted_birth_count"] == 0
    assert "oracle_atom_failure_residual" not in arm1["structure"]["trigger_distribution"]
    assert arm1["structure"]["leak_count"] == 0
    assert arm1["birth_death_curve"]
    assert {"load_bearing_count", "inert_count", "harmful_count"} <= set(arm1["post_hoc_ablation"])

    assert arm2["autogrowth_evidence"] is False
    assert arm2["uses_oracle_birth"] is True
    assert "error_set_targeted_birth_count" in arm2["structure"]
    assert {"survivor_trial", "promoted_positive_only", "atom_only_replay"} <= set(arm2["evaluations"])
