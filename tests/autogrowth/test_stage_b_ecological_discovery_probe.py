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
    run_phase36_yardstick_sovereignty_probe,
    run_phase37_recent_curriculum_black_resistance_probe,
    run_phase38_persistent_staged_ladder_probe,
    run_phase39_stable_plasticity_probe,
    run_phase40_stratified_acceptance_probe,
    run_phase41_credit_precision_paired_gates_probe,
    run_phase42_standing_ladder_ecology_probe,
    run_phase43_discriminative_cell_economy_probe,
    run_phase44_audition_cell_economy_probe,
    run_phase45_scheduled_audition_economy_probe,
    run_phase46_homeostatic_audition_economy_probe,
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


def test_phase36_yardstick_sovereignty_writes_executable_manifest(tmp_path: Path) -> None:
    summary = run_phase36_yardstick_sovereignty_probe(
        config=StageBEcologicalDiscoveryConfig(
            output_dir=str(tmp_path / "phase3_6_yardstick_probe"),
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

    assert summary["schema_version"] == "phase3_6_yardstick_sovereignty.v0"
    assert summary["historical_provenance"]["classification"] == "non_replayable_count_only_yardstick"
    assert "full_row_traces" in summary["historical_provenance"]["missing_replay_fields"]
    assert summary["decision"]["ecology_ran"] is False
    assert summary["decision"]["executable_host_equivalence_passed"] is True
    row = summary["per_flat_seed"][0]
    assert row["full_trace_equivalence"]["passed"] is True
    assert row["full_trace_equivalence"]["mismatch_count"] == 0
    assert row["evaluation_contract"]["black_reply_policy"].startswith("_edge_mate_fixed_seed_black_reply")
    assert row["baseline_manifest"]["current_executable_success_by_row"]
    assert row["baseline_manifest"]["current_executable_trace_digest_by_row"]
    assert row["baseline_manifest"]["initial_score_vector_mismatch_count"] == 0


def test_phase37_recent_curriculum_black_resistance_uses_recent_stage_ab_only(tmp_path: Path) -> None:
    summary = run_phase37_recent_curriculum_black_resistance_probe(
        config=StageBEcologicalDiscoveryConfig(
            output_dir=str(tmp_path / "phase3_7_recent_curriculum_probe"),
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

    assert summary["schema_version"] == "phase3_7_recent_curriculum_black_resistance.v0"
    assert summary["dataset"]["recent_curriculum_only"] is True
    assert summary["dataset"]["old_krk_curriculum_imported"] is False
    assert summary["black_reply_policies"]["runtime_tablebase_or_dtm_move_source"] is False
    assert summary["black_reply_policies"]["white_oracle_move_provider"] is False
    row = summary["per_flat_seed"][0]
    assert set(row["stage_a"]) == {"fixed_seed", "exact_adversarial"}
    assert set(row["stage_b"]) == {"fixed_seed", "exact_adversarial"}
    assert "stage_a_fixed_wins" in summary["tables"]["phase3_7_headline"][0]


def test_phase38_persistent_staged_ladder_records_provenance_and_gates(tmp_path: Path) -> None:
    summary = run_phase38_persistent_staged_ladder_probe(
        config=StageBEcologicalDiscoveryConfig(
            output_dir=str(tmp_path / "phase3_8_ladder_probe"),
            seeds=(20272931,),
            flat_baseline_seeds=(20272911,),
            stage_a_train_row_limit=1,
            train_row_limit=1,
            heldout_row_limit=1,
            max_samples=1,
            max_guided_births=0,
            ecology_mode="stem_cell_graph",
            native_foundation_train_repetitions=1,
            native_foundation_continuation_repetitions=1,
            native_foundation_max_mate1_positions=2,
            native_foundation_max_mate2_positions=1,
            native_foundation_prototype_scan_triplets=32,
            native_foundation_key_mode="coarse",
            real_native_engine_max_ticks=80,
        )
    )

    assert summary["schema_version"] == "phase3_8_persistent_staged_ladder.v0"
    assert summary["provenance_law"]["default_tick_budget"] == 80
    assert summary["decision"]["ecology_deferred"] is True
    assert summary["dataset"]["recent_curriculum_only_for_stage_a_b"] is True
    assert summary["dataset"]["old_krk_curriculum_imported_for_stage_a_b"] is False
    assert "phase3_8_gate_matrix" in summary["tables"]
    row = summary["per_seed"][0]
    assert row["baselines"]["stage_a_exact_adversarial_flat"]["runner_config"]["black_reply_policy"] == "exact_adversarial"
    assert row["baselines"]["stage_b_exact_adversarial_flat"]["success_by_row"]


def test_phase39_stable_plasticity_records_split_law_and_consolidation(tmp_path: Path) -> None:
    summary = run_phase39_stable_plasticity_probe(
        config=StageBEcologicalDiscoveryConfig(
            output_dir=str(tmp_path / "phase3_9_stable_probe"),
            seeds=(20272931,),
            flat_baseline_seeds=(20272911,),
            stage_a_train_row_limit=2,
            train_row_limit=2,
            heldout_row_limit=1,
            max_samples=1,
            max_guided_births=0,
            ecology_mode="stem_cell_graph",
            native_foundation_train_repetitions=1,
            native_foundation_continuation_repetitions=1,
            native_foundation_max_mate1_positions=2,
            native_foundation_max_mate2_positions=1,
            native_foundation_prototype_scan_triplets=32,
            native_foundation_key_mode="coarse",
            real_native_engine_max_ticks=80,
        )
    )

    assert summary["schema_version"] == "phase3_9_stable_plasticity.v0"
    assert summary["split_law"]["gate_void_if_consulted"] is True
    assert summary["dataset"]["gate_rows_consulted_by_update_decisions"] is False
    assert "phase3_9_consolidation" in summary["tables"]
    row = summary["per_seed"][0]
    assert row["split_manifest"]["stage_a"]["gate_rows_consulted_by_update_decisions"] is False
    if "stage_a" in row:
        training = row["stage_a"]["training"]
        assert training["m3_m4_restored"] is True
        assert training["gate_heldout_consulted"] is False
        assert "chunks_consolidated" in training


def test_phase40_stratified_acceptance_records_endpoint_non_regression(tmp_path: Path) -> None:
    summary = run_phase40_stratified_acceptance_probe(
        config=StageBEcologicalDiscoveryConfig(
            output_dir=str(tmp_path / "phase3_10_stratified_probe"),
            seeds=(20272931,),
            flat_baseline_seeds=(20272911,),
            stage_a_train_row_limit=2,
            train_row_limit=2,
            heldout_row_limit=1,
            max_samples=1,
            max_guided_births=0,
            ecology_mode="stem_cell_graph",
            native_foundation_train_repetitions=1,
            native_foundation_continuation_repetitions=1,
            native_foundation_max_mate1_positions=2,
            native_foundation_max_mate2_positions=1,
            native_foundation_prototype_scan_triplets=32,
            native_foundation_key_mode="coarse",
            real_native_engine_max_ticks=80,
        )
    )

    assert summary["schema_version"] == "phase3_10_stratified_acceptance.v0"
    assert summary["consolidation"]["endpoint_non_regression"] is True
    assert summary["dataset"]["gate_rows_consulted_by_update_decisions"] is False
    assert "phase3_10_consolidation" in summary["tables"]
    row = summary["per_seed"][0]
    assert row["split_manifest"]["stage_a"]["split_strategy"] == "stratified_by_train_pool_initial_endpoint"
    if "stage_a" in row:
        training = row["stage_a"]["training"]
        assert training["endpoint_non_regression_required"] is True
        assert "fence_broken" in training["acceptance_endpoint_keys"]


def test_phase41_credit_precision_records_paired_gates_and_flip_stats(tmp_path: Path) -> None:
    summary = run_phase41_credit_precision_paired_gates_probe(
        config=StageBEcologicalDiscoveryConfig(
            output_dir=str(tmp_path / "phase3_11_credit_probe"),
            seeds=(20272931,),
            flat_baseline_seeds=(20272911,),
            stage_a_train_row_limit=2,
            train_row_limit=2,
            heldout_row_limit=1,
            max_samples=1,
            max_guided_births=0,
            ecology_mode="stem_cell_graph",
            native_foundation_train_repetitions=1,
            native_foundation_continuation_repetitions=1,
            native_foundation_max_mate1_positions=2,
            native_foundation_max_mate2_positions=1,
            native_foundation_prototype_scan_triplets=32,
            native_foundation_key_mode="coarse",
            real_native_engine_max_ticks=80,
        )
    )

    assert summary["schema_version"] == "phase3_11_credit_precision_paired_gates.v0"
    assert summary["paired_gate_spec"]["paired_rows"] is True
    assert summary["credit_precision"]["features_changed"] is False
    assert "phase3_11_paired_gates" in summary["tables"]
    assert "phase3_11_flip_ply" in summary["tables"]
    assert summary["phase3_10_paired_gate_calibration"]["enabled"] in {True, False}
    row = summary["per_seed"][0]
    if "stage_a" in row:
        training = row["stage_a"]["training"]
        assert training["fresh_validation_fold_per_chunk"] is True
        assert training["paired_acceptance"] is True
        assert "flip_ply_identification_rate" in training
        assert "paired_gate" in row["stage_a"]["gate"]


def test_phase42_standing_ladder_ecology_records_lifecycle_summary(tmp_path: Path) -> None:
    summary = run_phase42_standing_ladder_ecology_probe(
        config=StageBEcologicalDiscoveryConfig(
            output_dir=str(tmp_path / "phase3_12_ecology_probe"),
            seeds=(20272931,),
            flat_baseline_seeds=(20272911,),
            stage_a_train_row_limit=2,
            train_row_limit=2,
            heldout_row_limit=1,
            max_samples=1,
            max_guided_births=0,
            ecology_mode="stem_cell_graph",
            native_foundation_train_repetitions=1,
            native_foundation_continuation_repetitions=1,
            native_foundation_max_mate1_positions=2,
            native_foundation_max_mate2_positions=1,
            native_foundation_prototype_scan_triplets=32,
            native_foundation_key_mode="coarse",
            real_native_engine_max_ticks=80,
            real_native_foundation_row_limit=1,
            real_native_critical_period_exposures=2,
            real_native_critical_period_credit_multiplier=1.5,
            real_native_critical_period_optimism=0.01,
            real_native_positive_flip_credit=0.02,
            real_native_positive_flip_window=1,
        )
    )

    assert summary["schema_version"] == "phase3_12_standing_ladder_ecology.v0"
    assert summary["ecology"]["cells_carried_across_rungs"] is True
    assert summary["ecology"]["guided_birth_budget"] == 0
    assert "phase3_12_headline" in summary["tables"]
    assert "phase3_12_acceptance_margins" in summary["tables"]
    row = summary["per_seed"][0]
    assert "acceptance_check" in row
    if "population" in row:
        assert "mature_count" in row["population"]


def test_phase43_discriminative_cell_economy_records_choice_signal(tmp_path: Path) -> None:
    summary = run_phase43_discriminative_cell_economy_probe(
        config=StageBEcologicalDiscoveryConfig(
            output_dir=str(tmp_path / "phase3_13_discriminative_probe"),
            seeds=(20272931,),
            flat_baseline_seeds=(20272911,),
            stage_a_train_row_limit=2,
            train_row_limit=2,
            heldout_row_limit=1,
            max_samples=1,
            max_guided_births=0,
            ecology_mode="stem_cell_graph",
            native_foundation_train_repetitions=1,
            native_foundation_continuation_repetitions=1,
            native_foundation_max_mate1_positions=2,
            native_foundation_max_mate2_positions=1,
            native_foundation_prototype_scan_triplets=32,
            native_foundation_key_mode="coarse",
            real_native_engine_max_ticks=80,
            real_native_foundation_row_limit=1,
            real_native_max_live_composites=4,
            real_native_max_live_siblings_per_parent=2,
            real_native_trial_grace_exposures=1,
            real_native_critical_period_exposures=2,
            real_native_critical_period_credit_multiplier=1.5,
            real_native_critical_period_optimism=0.01,
            real_native_positive_flip_credit=0.02,
            real_native_positive_flip_window=1,
            real_native_choice_change_mature_events=1,
            real_native_choice_change_neutral_rent=0.001,
            real_native_near_zero_choice_change_rate=0.0,
            real_native_stability_band_multiplier=5,
        )
    )

    assert summary["schema_version"] == "phase3_13_discriminative_cell_economy.v0"
    assert summary["ecology"]["same_choice_credit"].startswith("zero")
    assert summary["ecology"]["birth_throttle"]["per_parent_live_capacity"] == 2
    assert "phase3_13_headline" in summary["tables"]
    assert "phase3_13_choice_change_signal" in summary["tables"]
    row = summary["per_seed"][0]
    assert "acceptance_check" in row
    if "stage_a" in row and "ecology_training" in row["stage_a"]:
        assert "choice_changed_ply_rate" in row["stage_a"]["ecology_training"]


def test_phase44_audition_cell_economy_records_verdicts(tmp_path: Path) -> None:
    summary = run_phase44_audition_cell_economy_probe(
        config=StageBEcologicalDiscoveryConfig(
            output_dir=str(tmp_path / "phase3_14_audition_probe"),
            seeds=(20272931,),
            flat_baseline_seeds=(20272911,),
            stage_a_train_row_limit=2,
            train_row_limit=2,
            heldout_row_limit=1,
            max_samples=1,
            max_guided_births=0,
            ecology_mode="stem_cell_graph",
            native_foundation_train_repetitions=1,
            native_foundation_continuation_repetitions=1,
            native_foundation_max_mate1_positions=2,
            native_foundation_max_mate2_positions=1,
            native_foundation_prototype_scan_triplets=32,
            native_foundation_key_mode="coarse",
            real_native_engine_max_ticks=80,
            real_native_foundation_row_limit=1,
            real_native_max_live_composites=4,
            real_native_max_live_siblings_per_parent=2,
            real_native_trial_grace_exposures=1,
            real_native_critical_period_exposures=2,
            real_native_critical_period_credit_multiplier=1.5,
            real_native_critical_period_optimism=0.01,
            real_native_positive_flip_credit=0.02,
            real_native_positive_flip_window=1,
            real_native_choice_change_mature_events=1,
            real_native_choice_change_neutral_rent=0.001,
            real_native_near_zero_choice_change_rate=0.0,
            real_native_stability_band_multiplier=5,
            real_native_audition_budget_per_cell=2,
            real_native_audition_per_ply_cap=1,
            real_native_audition_horizon_plies=2,
            real_native_audition_mature_better_events=1,
            real_native_audition_neutral_rent=0.001,
            real_native_audition_debt_threshold=1,
            real_native_audition_starvation_min_per_cell=0.0,
        )
    )

    assert summary["schema_version"] == "phase3_14_audition_cell_economy.v0"
    assert summary["ecology"]["audition_economy"]["per_cell_budget"] == 2
    assert summary["ecology"]["audition_economy"]["per_ply_cap"] == 1
    assert "phase3_14_headline" in summary["tables"]
    assert "phase3_14_audition_signal" in summary["tables"]
    row = summary["per_seed"][0]
    assert "acceptance_check" in row
    if "stage_a" in row and "ecology_training" in row["stage_a"]:
        assert "auditions_per_cell_distribution" in row["stage_a"]["ecology_training"]


def test_phase45_scheduled_audition_economy_records_coverage(tmp_path: Path) -> None:
    summary = run_phase45_scheduled_audition_economy_probe(
        config=StageBEcologicalDiscoveryConfig(
            output_dir=str(tmp_path / "phase3_15_scheduled_probe"),
            seeds=(20272931,),
            flat_baseline_seeds=(20272911,),
            stage_a_train_row_limit=2,
            train_row_limit=2,
            heldout_row_limit=1,
            max_samples=1,
            max_guided_births=0,
            ecology_mode="stem_cell_graph",
            native_foundation_train_repetitions=1,
            native_foundation_continuation_repetitions=1,
            native_foundation_max_mate1_positions=2,
            native_foundation_max_mate2_positions=1,
            native_foundation_prototype_scan_triplets=32,
            native_foundation_key_mode="coarse",
            real_native_engine_max_ticks=80,
            real_native_foundation_row_limit=1,
            real_native_max_live_composites=4,
            real_native_max_live_siblings_per_parent=2,
            real_native_trial_grace_exposures=1,
            real_native_critical_period_exposures=2,
            real_native_critical_period_credit_multiplier=1.5,
            real_native_critical_period_optimism=0.01,
            real_native_positive_flip_credit=0.02,
            real_native_positive_flip_window=1,
            real_native_choice_change_mature_events=1,
            real_native_choice_change_neutral_rent=0.001,
            real_native_near_zero_choice_change_rate=0.0,
            real_native_stability_band_multiplier=5,
            real_native_audition_budget_per_cell=2,
            real_native_audition_per_ply_cap=1,
            real_native_audition_horizon_plies=2,
            real_native_audition_mature_better_events=1,
            real_native_audition_neutral_rent=0.001,
            real_native_audition_debt_threshold=1,
            real_native_audition_starvation_min_per_cell=0.0,
            real_native_scheduled_audition_chunk_size=1,
            real_native_scheduled_unjudged_fraction_stop=1.0,
        )
    )

    assert summary["schema_version"] == "phase3_15_scheduled_audition_economy.v0"
    assert summary["ecology"]["scheduled_auditions"]["enabled"] is True
    assert summary["cross_experiment_composite_correspondence"]
    assert "phase3_15_headline" in summary["tables"]
    assert "phase3_15_audition_signal" in summary["tables"]
    row = summary["per_seed"][0]
    assert row["schema_version"] == "phase3_15_scheduled_audition_economy_seed.v0"
    if "stage_a" in row and "ecology_training" in row["stage_a"]:
        assert "scheduled_coverage" in row["stage_a"]["ecology_training"]


def test_phase46_homeostatic_audition_economy_records_flush_and_families(tmp_path: Path) -> None:
    summary = run_phase46_homeostatic_audition_economy_probe(
        config=StageBEcologicalDiscoveryConfig(
            output_dir=str(tmp_path / "phase3_16_homeostatic_probe"),
            seeds=(20272931,),
            flat_baseline_seeds=(20272911,),
            stage_a_train_row_limit=2,
            train_row_limit=2,
            heldout_row_limit=1,
            max_samples=1,
            max_guided_births=0,
            ecology_mode="stem_cell_graph",
            native_foundation_train_repetitions=1,
            native_foundation_continuation_repetitions=1,
            native_foundation_max_mate1_positions=2,
            native_foundation_max_mate2_positions=1,
            native_foundation_prototype_scan_triplets=32,
            native_foundation_key_mode="coarse",
            real_native_engine_max_ticks=80,
            real_native_foundation_row_limit=1,
            real_native_max_live_composites=4,
            real_native_max_live_siblings_per_parent=2,
            real_native_trial_grace_exposures=1,
            real_native_critical_period_exposures=2,
            real_native_critical_period_credit_multiplier=1.5,
            real_native_critical_period_optimism=0.01,
            real_native_positive_flip_credit=0.02,
            real_native_positive_flip_window=1,
            real_native_choice_change_mature_events=1,
            real_native_choice_change_neutral_rent=0.001,
            real_native_near_zero_choice_change_rate=0.0,
            real_native_stability_band_multiplier=5,
            real_native_audition_budget_per_cell=2,
            real_native_audition_per_ply_cap=1,
            real_native_audition_horizon_plies=2,
            real_native_audition_mature_better_events=1,
            real_native_audition_neutral_rent=0.001,
            real_native_audition_debt_threshold=1,
            real_native_audition_starvation_min_per_cell=0.0,
            real_native_scheduled_audition_chunk_size=1,
            real_native_scheduled_unjudged_fraction_stop=1.0,
            real_native_scheduled_complete_flush=True,
            real_native_homeostatic_backlog_threshold=0.30,
            real_native_continue_after_seed_stop=True,
        )
    )

    assert summary["schema_version"] == "phase3_16_homeostatic_audition_economy.v0"
    assert summary["ecology"]["scheduled_auditions"]["complete_end_of_stage_flush"] is True
    assert summary["ecology"]["homeostatic_birth_gate"]["backlog_threshold"] == 0.30
    assert "phase3_16_mature_recurrence_by_family" in summary["tables"]
    assert "phase3_16_phase3_15_under_k_diagnosis" in summary["tables"]
    row = summary["per_seed"][0]
    assert row["schema_version"] == "phase3_16_homeostatic_audition_economy_seed.v0"
    if "stage_a" in row and "ecology_training" in row["stage_a"]:
        training = row["stage_a"]["ecology_training"]
        assert "complete_flush" in training
        assert "backlog_curve" in training
