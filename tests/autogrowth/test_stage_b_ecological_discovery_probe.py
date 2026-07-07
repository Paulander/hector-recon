from pathlib import Path

from recon_lite_chess.autogrowth.stage_b_ecological_discovery_probe import (
    StageBEcologicalDiscoveryConfig,
    _fast_enter_mate2_audit,
    run_stage_ab_graph_native_carryover_probe,
    run_stage_ab_native_foundation_ecology_probe,
    run_phase32_real_native_graph_ecology_probe,
    run_phase33_migrated_flat_native_ecology_probe,
    run_phase34_host_tiebreak_alignment_probe,
    run_phase35_equivalence_forensics_probe,
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


def test_phase31_stage_ab_carryover_reuses_same_population(tmp_path: Path) -> None:
    summary = run_stage_ab_graph_native_carryover_probe(
        config=StageBEcologicalDiscoveryConfig(
            output_dir=str(tmp_path / "phase3_1_probe"),
            seeds=(20272931,),
            stage_a_train_row_limit=2,
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

    assert summary["schema_version"] == "phase3_1_stage_ab_graph_native_carryover.v0"
    assert summary["dataset"]["same_population_across_stage_a_b"] is True
    assert summary["dataset"]["full_foundation_curriculum"] is False
    assert "phase3_1_headline" in summary["tables"]
    arm1 = summary["seed_results"]["20272931"]["arm1_unguided_ecological"]
    assert arm1["curriculum_carryover"]["same_population_across_segments"] is True
    assert [item["name"] for item in arm1["curriculum_carryover"]["segments"]] == [
        "stage_a_approach_warmup",
        "stage_b_true_middle_chase",
    ]
    assert "births_by_segment" in arm1["structure"]["curriculum_carryover"]


def test_phase32_native_foundation_ecology_reports_coverage(tmp_path: Path) -> None:
    summary = run_stage_ab_native_foundation_ecology_probe(
        config=StageBEcologicalDiscoveryConfig(
            output_dir=str(tmp_path / "phase3_2_probe"),
            seeds=(20272931,),
            stage_a_train_row_limit=2,
            train_row_limit=2,
            heldout_row_limit=2,
            max_population_per_habitat=1,
            max_guided_births=0,
            max_births_per_decision=1,
            max_samples=2,
            pruned_rescue_audit_limit=1,
            ecology_mode="stem_cell_graph",
            native_foundation_train_repetitions=1,
            native_foundation_continuation_repetitions=1,
            native_foundation_max_mate1_positions=4,
            native_foundation_max_mate2_positions=2,
            native_foundation_key_mode="coarse",
        )
    )

    assert summary["schema_version"] == "phase3_2_native_foundation_ecology.v0"
    assert summary["dataset"]["same_native_foundation_graph_across_stage_a_b"] is True
    assert summary["dataset"]["same_ecological_population_across_stage_a_b"] is True
    assert "phase3_2_headline" in summary["tables"]
    assert "native_foundation_coverage" in summary
    assert "native_foundation_base" in summary["reference_baselines"]
    arm1 = summary["seed_results"]["20272931"]["arm1_unguided_ecological"]
    assert arm1["autogrowth_evidence"] is True
    assert arm1["uses_oracle_birth"] is False


def test_phase32_real_native_graph_ecology_acceptance_path(tmp_path: Path) -> None:
    summary = run_phase32_real_native_graph_ecology_probe(
        config=StageBEcologicalDiscoveryConfig(
            output_dir=str(tmp_path / "phase3_2_real_native_probe"),
            seeds=(20272931,),
            real_native_foundation_row_limit=1,
            train_row_limit=1,
            heldout_row_limit=1,
            max_samples=2,
            max_guided_births=0,
            ecology_mode="stem_cell_graph",
            native_foundation_train_repetitions=1,
            native_foundation_continuation_repetitions=1,
            native_foundation_max_mate1_positions=2,
            native_foundation_max_mate2_positions=1,
            native_foundation_prototype_scan_triplets=32,
            native_foundation_key_mode="coarse",
            real_native_max_live_composites=4,
            real_native_max_live_siblings_per_parent=2,
            real_native_engine_max_ticks=80,
        )
    )

    assert summary["schema_version"] == "phase3_2_real_native_graph_ecology.v0"
    assert summary["dataset"]["one_persistent_graph_per_seed_foundation_then_chase"] is True
    assert "FormalReConEngine.run(active_nodes={ROOT_ID,parent_script,composite_terminal})" in summary["acceptance_spec"]["call_chain"]

    result = summary["seed_results"]["20272931"]
    acceptance = result["acceptance_check"]
    proof = acceptance["dynamic_proof"]
    assert acceptance["passed"] is True
    assert proof["request_sub_message_to_composite_seen"] is True
    assert proof["predicate_evaluated"] is True
    assert proof["terminal_requested"] is True
    assert proof["formal_engine_eval_count_after"] > proof["formal_engine_eval_count_before"]
    assert proof["formal_ticks_run"] <= 80

    instrumentation = result["runtime_instrumentation"]
    assert instrumentation["formal_engine_composite_call_count"] >= instrumentation["formal_engine_composite_eval_count"] > 0
    assert instrumentation["engine_tick_samples"]


def test_phase33_migrated_flat_host_equivalence_gate(tmp_path: Path) -> None:
    summary = run_phase33_migrated_flat_native_ecology_probe(
        config=StageBEcologicalDiscoveryConfig(
            output_dir=str(tmp_path / "phase3_3_migrated_flat_probe"),
            seeds=(20272931,),
            flat_baseline_seeds=(20272911,),
            real_native_foundation_row_limit=1,
            train_row_limit=1,
            heldout_row_limit=2,
            max_samples=2,
            max_guided_births=0,
            ecology_mode="stem_cell_graph",
            native_foundation_train_repetitions=1,
            native_foundation_continuation_repetitions=1,
            native_foundation_max_mate1_positions=2,
            native_foundation_max_mate2_positions=1,
            native_foundation_prototype_scan_triplets=32,
            native_foundation_key_mode="coarse",
            real_native_max_live_composites=4,
            real_native_max_live_siblings_per_parent=2,
            real_native_engine_max_ticks=80,
        )
    )

    assert summary["schema_version"] == "phase3_3_migrated_flat_native_ecology.v0"
    equivalence = summary["host_equivalence"]
    assert equivalence["all_passed"] is True
    row = equivalence["per_flat_seed"][0]
    proof = row["acceptance_check"]["dynamic_proof"]
    assert row["migrated_wins"] == row["sealed_wins"]
    assert proof["request_sub_message_to_atom_seen"] is True
    assert proof["formal_engine_eval_count_after"] > proof["formal_engine_eval_count_before"]
    assert "FormalReConEngine.run(active_nodes={ROOT_ID,stage_b_policy_parent,active_atom_terminals})" in row["acceptance_check"]["call_chain"]

    result = summary["seed_results"]["20272931"]
    assert result["host_instrumentation"]["formal_engine_atom_eval_count"] > 0
    assert "host_plus_minus_host_wins" in result["evaluations"]


def test_phase34_host_tiebreak_alignment_uses_deterministic_contract(tmp_path: Path) -> None:
    summary = run_phase34_host_tiebreak_alignment_probe(
        config=StageBEcologicalDiscoveryConfig(
            output_dir=str(tmp_path / "phase3_4_tiebreak_probe"),
            seeds=(20272931,),
            flat_baseline_seeds=(20272911,),
            real_native_foundation_row_limit=1,
            train_row_limit=1,
            heldout_row_limit=2,
            max_samples=2,
            max_guided_births=0,
            ecology_mode="stem_cell_graph",
            native_foundation_train_repetitions=1,
            native_foundation_continuation_repetitions=1,
            native_foundation_max_mate1_positions=2,
            native_foundation_max_mate2_positions=1,
            native_foundation_prototype_scan_triplets=32,
            native_foundation_key_mode="coarse",
            real_native_max_live_composites=4,
            real_native_max_live_siblings_per_parent=2,
            real_native_engine_max_ticks=80,
        )
    )

    assert summary["schema_version"] == "phase3_4_host_tiebreak_alignment.v0"
    assert summary["tiebreak_repair"]["migrated_host_tiebreak"] == "(score, uci)"
    assert "phase3_4_headline" in summary["tables"]
    assert summary["host_equivalence"]["tiebreak_alignment"]["same_repetition_guard"] is True
    assert summary["host_equivalence"]["tiebreak_alignment"]["same_sealed_action_key_scales"] is True
    assert summary["host_equivalence"]["residual_diagnostic_source"] == (
        "current_executable_official_terminal_sum_vs_migrated_host"
    )
    row = summary["host_equivalence"]["per_flat_seed"][0]
    assert row["tiebreak_alignment"]["official_executable_replay"] == "(score, uci)"
    assert row["migrated_wins"] == row["sealed_wins"]


def test_phase35_equivalence_forensics_records_predicates_without_ecology(tmp_path: Path) -> None:
    summary = run_phase35_equivalence_forensics_probe(
        config=StageBEcologicalDiscoveryConfig(
            output_dir=str(tmp_path / "phase3_5_forensics_probe"),
            seeds=(20272931,),
            flat_baseline_seeds=(20272911,),
            real_native_foundation_row_limit=1,
            train_row_limit=1,
            heldout_row_limit=2,
            max_samples=2,
            max_guided_births=0,
            ecology_mode="stem_cell_graph",
            native_foundation_train_repetitions=1,
            native_foundation_continuation_repetitions=1,
            native_foundation_max_mate1_positions=2,
            native_foundation_max_mate2_positions=1,
            native_foundation_prototype_scan_triplets=32,
            native_foundation_key_mode="coarse",
            real_native_max_live_composites=4,
            real_native_max_live_siblings_per_parent=2,
            real_native_engine_max_ticks=80,
        )
    )

    assert summary["schema_version"] == "phase3_5_equivalence_forensics.v0"
    assert summary["success_predicates"]["official_stage_b_artifact"]["horizon_white_moves"] == 16
    assert summary["success_predicates"]["phase3_5_migrated_equivalence_check"]["function"].endswith(
        "_rollout_policy"
    )
    assert summary["decision"]["ecology_ran"] is False
    row = summary["per_flat_seed"][0]
    assert row["current_executable_replay_wins"] == row["migrated_host_wins"]
