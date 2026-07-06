from pathlib import Path

from recon_lite_chess.autogrowth.stage_b_ecological_discovery_probe import (
    StageBEcologicalDiscoveryConfig,
    _fast_enter_mate2_audit,
    run_stage_b_graph_native_ecology_probe,
    run_stage_b_ecological_habitat_probe,
    run_stage_b_ecological_discovery_probe,
    run_stage_b_ecological_discovery_scale_probe,
)
from recon_lite_chess.autogrowth.quorum_basin import (
    _edge_mate_enter_mate2_audit,
    load_canonical_mate2_first_scorer,
)
import chess


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


def test_phase29e_fast_enter_mate2_matches_slow_exact_audit() -> None:
    scorer = load_canonical_mate2_first_scorer()
    mate2_cache: dict[str, dict] = {}
    enter_cache: dict[str, dict] = {}
    fens = [
        "8/6R1/8/6K1/8/8/7k/8 w - - 0 1",
        "3k4/5R2/8/5K2/8/8/8/8 w - - 0 1",
        "8/8/8/K7/7k/8/6R1/8 w - - 0 1",
    ]

    for fen in fens:
        board = chess.Board(fen)
        slow = _edge_mate_enter_mate2_audit(
            board,
            scorer=scorer,
            mate2_cache=mate2_cache,
            enter_cache=enter_cache,
        )
        fast = _fast_enter_mate2_audit(board)
        assert fast["confirmed"] == slow["confirmed"]


def test_phase29f_scale_probe_writes_characterization_fields(tmp_path: Path) -> None:
    summary = run_stage_b_ecological_discovery_scale_probe(
        config=StageBEcologicalDiscoveryConfig(
            output_dir=str(tmp_path / "phase2_9f_probe"),
            seeds=(20272931,),
            train_row_limit=2,
            heldout_row_limit=2,
            max_population=4,
            max_guided_births=4,
            max_births_per_decision=1,
            max_samples=2,
        )
    )

    assert summary["schema_version"] == "phase2_9f_stage_b_ecological_scale.v0"
    assert "cross_seed_composite_analysis" in summary
    assert "enrichment_summary" in summary
    assert "phase2_9f_headline" in summary["tables"]
    arm1 = summary["seed_results"]["20272931"]["arm1_unguided_ecological"]
    assert "survivor_composite_dumps" in arm1


def test_phase29g_habitat_probe_uses_local_ecology(tmp_path: Path) -> None:
    summary = run_stage_b_ecological_habitat_probe(
        config=StageBEcologicalDiscoveryConfig(
            output_dir=str(tmp_path / "phase2_9g_probe"),
            seeds=(20272931,),
            train_row_limit=2,
            heldout_row_limit=2,
            max_population=4,
            max_total_population=4,
            max_population_per_habitat=1,
            max_guided_births=4,
            max_births_per_decision=1,
            max_samples=2,
            ecology_mode="habitat_local",
        )
    )

    assert summary["schema_version"] == "phase2_9g_stage_b_habitat_ecology.v0"
    assert "phase2_9g_headline" in summary["tables"]
    arm1 = summary["seed_results"]["20272931"]["arm1_unguided_ecological"]
    assert arm1["structure"]["leak_count"] == 0
    assert "habitat_cap_pruned_count" in arm1["structure"]
    assert "alive_habitat_count" in arm1["birth_death_curve"][-1]


def test_phase30_graph_native_probe_records_stem_cell_fates(tmp_path: Path) -> None:
    summary = run_stage_b_graph_native_ecology_probe(
        config=StageBEcologicalDiscoveryConfig(
            output_dir=str(tmp_path / "phase3_0_probe"),
            seeds=(20272931,),
            train_row_limit=2,
            heldout_row_limit=2,
            max_population_per_habitat=1,
            max_guided_births=2,
            max_births_per_decision=1,
            max_samples=2,
            pruned_rescue_audit_limit=1,
            ecology_mode="stem_cell_graph",
        )
    )

    assert summary["schema_version"] == "phase3_0_stage_b_graph_native_ecology.v0"
    assert "phase3_0_headline" in summary["tables"]
    assert "maturity_summary" in summary
    arm1 = summary["seed_results"]["20272931"]["arm1_unguided_ecological"]
    assert arm1["structure"]["leak_count"] == 0
    assert "parent_budget_pruned_count" in arm1["structure"]
    assert "candidate_fate_log" in arm1
    assert arm1["pruned_rescue_audit"]["enabled"] is True
