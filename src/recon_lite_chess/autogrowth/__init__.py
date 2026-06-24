"""Learning-first KRK autogrowth utilities."""

from .arbitration import (
    LocalArbitrationConfig,
    LocalArbitrationMetrics,
    LocalArbitrationResult,
    arbitrate_local_action,
    build_local_action_nodes,
    evaluate_local_arbitration_arm,
    run_local_arbitration_experiment,
)
from .candidate_generation import (
    CONTEXT_SPECIALIZED_FEATURES,
    ContextSpecializedCandidateConfig,
    ContextSpecializedCandidateResult,
    RiskAwareCandidateConfig,
    RiskAwareCandidateResult,
    generate_context_specialized_candidates,
    generate_risk_aware_candidates,
    run_context_specialized_candidate_experiment,
    run_risk_aware_candidate_experiment,
)
from .continuation_retry import (
    ContinuationRetryConfig,
    ContinuationRetryMetrics,
    ContinuationRetryResult,
    choose_continuation_retry_action,
    evaluate_continuation_retry_arm,
    run_continuation_retry_experiment,
)
from .context_gated_curriculum import (
    ContextGatedCurriculumConfig,
    ContextGatedFoundationBundle,
    ContextGatedCurriculumResult,
    context_terminal_keys,
    run_context_gated_curriculum,
    train_context_gated_foundation_bundle,
)
from .context_gated_edge_fence_validation import (
    ContextGatedEdgeFenceValidationConfig,
    ContextGatedEdgeFenceValidationResult,
    run_context_gated_edge_fence_validation,
)
from .curriculum_reward_recovery import (
    CurriculumRewardRecoveryConfig,
    CurriculumRewardRecoveryResult,
    run_curriculum_reward_recovery,
    score_non_terminal_progress,
)
from .curated_terminal_curriculum import (
    CuratedTerminalCurriculumConfig,
    CuratedTerminalCurriculumResult,
    curated_stage_entries,
    run_curated_terminal_curriculum,
    stage_inventory,
)
from .curated_replay_curriculum import (
    CuratedReplayCurriculumConfig,
    CuratedReplayCurriculumResult,
    run_curated_replay_curriculum,
)
from .evaluate import (
    ArmMetrics,
    EvaluationConfig,
    EvaluationResult,
    evaluate_arm,
    evaluate_baseline_and_sham,
)
from .fence_boundary_rehearsal import (
    FenceBoundaryRehearsalConfig,
    FenceBoundaryRehearsalResult,
    run_fence_boundary_rehearsal,
)
from .fence_boundary_signal import (
    FenceBoundarySignalConfig,
    FenceBoundarySignalResult,
    run_fence_boundary_signal,
)
from .edge_fence_curriculum import (
    EdgeFenceCurriculumConfig,
    EdgeFenceCurriculumResult,
    run_edge_fence_curriculum,
)
from .foundation_curriculum import (
    ActionRanker,
    FoundationCurriculumConfig,
    FoundationCurriculumResult,
    run_foundation_curriculum,
)
from .handoff_filter_validation import (
    HandoffFilterValidationConfig,
    HandoffFilterValidationResult,
    run_handoff_filter_validation,
)
from .experiment import (
    AutogrowthExperimentConfig,
    AutogrowthExperimentResult,
    run_autogrowth_experiment,
)
from .features import (
    FORBIDDEN_LEARNER_TERMS,
    extract_learner_features,
    make_trace_record,
    validate_learner_record,
)
from .fragment_chain_curriculum import (
    FragmentChainCurriculumConfig,
    FragmentChainCurriculumResult,
    evaluate_fragment_chain_arm,
    run_fragment_chain_curriculum,
)
from .lag_terminals import (
    LagFragmentChainMetrics,
    LagTerminalConfig,
    LagTerminalResult,
    choose_lag_fragment_chain_action,
    evaluate_lag_fragment_chain_arm,
    evaluate_lag_terminal,
    run_lag_terminal_experiment,
)
from .mining import (
    CandidateMiningConfig,
    CandidateMiningResult,
    mine_triplet_candidates_from_artifact,
    mine_triplet_candidates_from_records,
)
from .positions import (
    KRKPositionSet,
    can_mate_in_one,
    generate_position_sets,
    is_valid_krk_seed,
)
from .precision_gate import (
    LocalPrecisionGate,
    PrecisionGateConfig,
    PrecisionGateResult,
    audit_confinement_sign_semantics,
    derive_local_precision_gate,
    run_precision_gate_experiment,
)
from .persisted_pool_validation import (
    PersistedPoolValidationConfig,
    PersistedPoolValidationResult,
    run_persisted_pool_validation,
)
from .retry_edges import (
    RetryEdgeConfig,
    RetryEdgeResult,
    run_retry_edge_experiment,
)
from .retry_diagnostics import (
    RetryDiagnosticsConfig,
    RetryDiagnosticsResult,
    run_retry_diagnostics,
)
from .retry_candidate_expansion import (
    RetryCandidateExpansionConfig,
    RetryCandidateExpansionResult,
    mine_retry_expansion_candidates,
    run_retry_candidate_expansion,
)
from .script_candidates import (
    LocalScriptConfig,
    LocalScriptMetrics,
    LocalScriptResult,
    choose_local_script_action,
    generate_local_script_candidates,
    run_local_script_experiment,
)
from .script_fragments import (
    ScriptFragmentConfig,
    ScriptFragmentResult,
    generalize_script_candidates_to_fragments,
    run_script_fragment_experiment,
)
from .single_graph_curriculum import (
    SingleGraphCurriculumConfig,
    SingleGraphCurriculumResult,
    SingleGraphKRKNetwork,
    run_single_graph_curriculum,
)
from .native_single_graph_curriculum import (
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
    NativeSingleGraphResult,
    run_native_single_graph_curriculum,
)
from .native_scheduler_replay_audit import (
    NativeSchedulerReplayAuditConfig,
    NativeSchedulerReplayAuditResult,
    run_native_scheduler_replay_audit,
)
from .native_foundation_generalization import (
    NativeFoundationGeneralizationConfig,
    NativeFoundationGeneralizationResult,
    run_native_foundation_generalization,
)
from .shared_feature_atoms import (
    SharedFeatureAtomConfig,
    SharedFeatureAtomResult,
    run_shared_feature_atom_experiment,
)
from .shared_atom_utility_voting import (
    SharedAtomUtilityVotingConfig,
    SharedAtomUtilityVotingResult,
    run_shared_atom_utility_voting,
)
from .native_quorum_materialization import (
    NativeQuorumMaterializationConfig,
    NativeQuorumMaterializationResult,
    run_native_quorum_materialization,
)
from .native_quorum_mate2_chaining import (
    NativeQuorumMate2ChainingConfig,
    NativeQuorumMate2ChainingResult,
    run_native_quorum_mate2_chaining,
)
from .internal_handoff_affordance_guard_audit import (
    InternalHandoffAffordanceConfig,
    InternalHandoffAffordanceResult,
    run_internal_handoff_affordance_guard_audit,
)
from .terminal_lifecycle import (
    TERMINAL_LIFECYCLE_POLICY,
    classify_terminal_kind,
    apply_terminal_lifecycle,
)
from .terminal_lifecycle_modest_scale import (
    TerminalLifecycleModestScaleConfig,
    TerminalLifecycleModestScaleResult,
    run_terminal_lifecycle_modest_scale,
)
from .continuous_handoff_attention import (
    ContinuousHandoffAttentionConfig,
    ContinuousHandoffAttentionResult,
    run_continuous_handoff_attention,
)
from .forced_chain_decomposition import (
    ForcedChainDecompositionConfig,
    ForcedChainDecompositionResult,
    run_forced_chain_decomposition,
)
from .native_foundation_scale_replay import (
    NativeFoundationScaleReplayConfig,
    NativeFoundationScaleReplayResult,
    run_native_foundation_scale_replay,
)
from .single_miss_repair import (
    SingleMissRepairConfig,
    SingleMissRepairResult,
    run_single_miss_repair,
)
from .frozen_foundation_edge_fence_reentry import (
    FrozenFoundationEdgeFenceReentryConfig,
    FrozenFoundationEdgeFenceReentryResult,
    run_frozen_foundation_edge_fence_reentry,
)
from .frozen_foundation_bridge_pressure import (
    FrozenFoundationBridgePressureConfig,
    FrozenFoundationBridgePressureResult,
    run_frozen_foundation_bridge_pressure,
)
from .frozen_foundation_response_cache_bridge_retrieval import (
    FrozenFoundationResponseCacheBridgeRetrievalConfig,
    FrozenFoundationResponseCacheBridgeRetrievalResult,
    run_frozen_foundation_response_cache_bridge_retrieval,
)
from .foundation_backed_bridge_frontier import (
    FoundationBackedBridgeFrontierConfig,
    FoundationBackedBridgeFrontierResult,
    run_foundation_backed_bridge_frontier,
)
from .persisted_foundation_backed_frontier_pool import (
    PersistedFoundationBackedFrontierPoolConfig,
    PersistedFoundationBackedFrontierPoolResult,
    run_persisted_foundation_backed_frontier_pool,
)
from .full_foundation_frontier_pool_resume import (
    FullFoundationFrontierPoolResumeConfig,
    FullFoundationFrontierPoolResumeResult,
    run_full_foundation_frontier_pool_resume,
)
from .full_frontier_validation_near_miss import (
    FullFrontierValidationNearMissConfig,
    FullFrontierValidationNearMissResult,
    run_full_frontier_validation_near_miss,
)
from .controlled_mixed_frontier_edge_curriculum import (
    ControlledMixedFrontierEdgeCurriculumConfig,
    ControlledMixedFrontierEdgeCurriculumResult,
    run_controlled_mixed_frontier_edge_curriculum,
)
from .staged_edge_bridge_foundation_rollout import (
    StagedEdgeBridgeFoundationRolloutConfig,
    StagedEdgeBridgeFoundationRolloutResult,
    run_staged_edge_bridge_foundation_rollout,
)
from .persisted_staged_predecessor_pool import (
    PersistedStagedPredecessorPoolConfig,
    PersistedStagedPredecessorPoolResult,
    run_persisted_staged_predecessor_pool,
)
from .staged_near_miss_ablation_restoration import (
    StagedNearMissAblationRestorationConfig,
    StagedNearMissAblationRestorationResult,
    run_staged_near_miss_ablation_restoration,
)
from .staged_pool_integrity_modest_scale import (
    StagedPoolIntegrityModestScaleConfig,
    StagedPoolIntegrityModestScaleResult,
    run_staged_pool_integrity_modest_scale,
)
from .tiny_online_krk_episode_runner import (
    TinyOnlineKRKEpisodeRunnerConfig,
    TinyOnlineKRKEpisodeRunnerResult,
    run_tiny_online_krk_episode_runner,
)
from .online_failure_decomposition import (
    OnlineFailureDecompositionConfig,
    OnlineFailureDecompositionResult,
    run_online_failure_decomposition,
)
from .reply_robust_bridge_pressure import (
    ReplyRobustBridgePressureConfig,
    ReplyRobustBridgePressureResult,
    run_reply_robust_bridge_pressure,
)
from .online_low_progress_repair import (
    OnlineLowProgressRepairConfig,
    OnlineLowProgressRepairResult,
    run_online_low_progress_repair,
)
from .reply_robust_progress_pool import (
    ReplyRobustProgressPoolConfig,
    ReplyRobustProgressPoolResult,
    run_reply_robust_progress_pool,
)
from .progress_candidate_selection_repair import (
    ProgressCandidateSelectionRepairConfig,
    ProgressCandidateSelectionRepairResult,
    run_progress_candidate_selection_repair,
)
from .trajectory_positive_prefix_audit import (
    TrajectoryPositivePrefixAuditConfig,
    TrajectoryPositivePrefixAuditResult,
    run_trajectory_positive_prefix_audit,
)
from .cached_trajectory_selection_repair import (
    CachedTrajectorySelectionRepairConfig,
    CachedTrajectorySelectionRepairResult,
    run_cached_trajectory_selection_repair,
)
from .stable_trajectory_cache_selection_microprobe import (
    StableTrajectoryCacheSelectionMicroprobeConfig,
    StableTrajectoryCacheSelectionMicroprobeResult,
    run_stable_trajectory_cache_selection_microprobe,
)
from .d3c3_trajectory_evidence_repair import (
    D3C3TrajectoryEvidenceRepairConfig,
    D3C3TrajectoryEvidenceRepairResult,
    run_d3c3_trajectory_evidence_repair,
)
from .runtime_trajectory_repair_integration import (
    RuntimeTrajectoryRepairIntegrationConfig,
    RuntimeTrajectoryRepairIntegrationResult,
    run_runtime_trajectory_repair_integration,
)
from .real_context_runtime_trajectory_validation import (
    RealContextRuntimeTrajectoryValidationConfig,
    RealContextRuntimeTrajectoryValidationResult,
    run_real_context_runtime_trajectory_validation,
)
from .sandbox import (
    SandboxConfig,
    SandboxMetrics,
    SandboxResult,
    evaluate_candidate_sandbox,
    evaluate_sandbox_arm,
    load_selected_candidate,
)
from .suppressor import (
    LocalSuppressorConfig,
    LocalSuppressorMetrics,
    LocalSuppressorResult,
    derive_local_suppressor,
    evaluate_local_suppressor_arm,
    run_local_suppressor_experiment,
    suppressor_confirms,
)
from .terminal_substrate import (
    TerminalFoundationBundle,
    TerminalAffordanceLearner,
    TerminalSubstrateConfig,
    TerminalSubstrateResult,
    action_ranker_behavior_audit,
    extract_terminal_feature_vector,
    feature_substrate_coverage_sample,
    run_terminal_substrate_revival,
    terminal_action_feature_keys,
    train_terminal_foundation_bundle,
)
from .terminal_edge_fence_validation import (
    TerminalEdgeFenceValidationConfig,
    TerminalEdgeFenceValidationResult,
    run_terminal_edge_fence_validation,
)
from .traces import (
    TraceCollectionConfig,
    TraceCollectionResult,
    collect_trace_records,
)
from .training import (
    CandidateLifecycle,
    GrowthTrainingConfig,
    GrowthTrainingResult,
    load_candidate_pool,
    train_growth_candidates,
)
from .topological_growth import (
    TopologicalGrowthRunwayConfig,
    TopologicalGrowthRunwayResult,
    build_triplet_chain_view,
    inventory_legacy_predefined_topology_runs,
    run_topological_growth_runway,
)

__all__ = [
    "ArmMetrics",
    "AutogrowthExperimentConfig",
    "AutogrowthExperimentResult",
    "CandidateMiningConfig",
    "CandidateMiningResult",
    "CONTEXT_SPECIALIZED_FEATURES",
    "ContinuationRetryConfig",
    "ContinuationRetryMetrics",
    "ContinuationRetryResult",
    "ContextGatedCurriculumConfig",
    "ContextGatedEdgeFenceValidationConfig",
    "ContextGatedEdgeFenceValidationResult",
    "ContextGatedFoundationBundle",
    "ContextGatedCurriculumResult",
    "CurriculumRewardRecoveryConfig",
    "CurriculumRewardRecoveryResult",
    "CuratedTerminalCurriculumConfig",
    "CuratedTerminalCurriculumResult",
    "CuratedReplayCurriculumConfig",
    "CuratedReplayCurriculumResult",
    "EvaluationConfig",
    "EvaluationResult",
    "EdgeFenceCurriculumConfig",
    "EdgeFenceCurriculumResult",
    "FenceBoundaryRehearsalConfig",
    "FenceBoundaryRehearsalResult",
    "FenceBoundarySignalConfig",
    "FenceBoundarySignalResult",
    "FORBIDDEN_LEARNER_TERMS",
    "ActionRanker",
    "FoundationCurriculumConfig",
    "FoundationCurriculumResult",
    "FragmentChainCurriculumConfig",
    "FragmentChainCurriculumResult",
    "LagFragmentChainMetrics",
    "LagTerminalConfig",
    "LagTerminalResult",
    "CandidateLifecycle",
    "GrowthTrainingConfig",
    "GrowthTrainingResult",
    "HandoffFilterValidationConfig",
    "HandoffFilterValidationResult",
    "KRKPositionSet",
    "LocalArbitrationConfig",
    "LocalArbitrationMetrics",
    "LocalArbitrationResult",
    "LocalScriptConfig",
    "LocalScriptMetrics",
    "LocalScriptResult",
    "LocalSuppressorConfig",
    "LocalSuppressorMetrics",
    "LocalSuppressorResult",
    "LocalPrecisionGate",
    "PrecisionGateConfig",
    "PrecisionGateResult",
    "PersistedPoolValidationConfig",
    "PersistedPoolValidationResult",
    "ContextSpecializedCandidateConfig",
    "ContextSpecializedCandidateResult",
    "RiskAwareCandidateConfig",
    "RiskAwareCandidateResult",
    "RetryEdgeConfig",
    "RetryEdgeResult",
    "RetryDiagnosticsConfig",
    "RetryDiagnosticsResult",
    "RetryCandidateExpansionConfig",
    "RetryCandidateExpansionResult",
    "SandboxConfig",
    "SandboxMetrics",
    "SandboxResult",
    "ScriptFragmentConfig",
    "ScriptFragmentResult",
    "SharedFeatureAtomConfig",
    "SharedFeatureAtomResult",
    "SharedAtomUtilityVotingConfig",
    "SharedAtomUtilityVotingResult",
    "NativeQuorumMaterializationConfig",
    "NativeQuorumMaterializationResult",
    "NativeQuorumMate2ChainingConfig",
    "NativeQuorumMate2ChainingResult",
    "InternalHandoffAffordanceConfig",
    "InternalHandoffAffordanceResult",
    "TerminalLifecycleModestScaleConfig",
    "TerminalLifecycleModestScaleResult",
    "ContinuousHandoffAttentionConfig",
    "ContinuousHandoffAttentionResult",
    "ForcedChainDecompositionConfig",
    "ForcedChainDecompositionResult",
    "SingleGraphCurriculumConfig",
    "SingleGraphCurriculumResult",
    "SingleGraphKRKNetwork",
    "TerminalEdgeFenceValidationConfig",
    "TerminalEdgeFenceValidationResult",
    "TerminalFoundationBundle",
    "TerminalAffordanceLearner",
    "TerminalSubstrateConfig",
    "TerminalSubstrateResult",
    "TraceCollectionConfig",
    "TraceCollectionResult",
    "TopologicalGrowthRunwayConfig",
    "TopologicalGrowthRunwayResult",
    "arbitrate_local_action",
    "build_local_action_nodes",
    "build_triplet_chain_view",
    "can_mate_in_one",
    "collect_trace_records",
    "context_terminal_keys",
    "curated_stage_entries",
    "evaluate_arm",
    "evaluate_baseline_and_sham",
    "evaluate_candidate_sandbox",
    "evaluate_fragment_chain_arm",
    "evaluate_lag_fragment_chain_arm",
    "evaluate_continuation_retry_arm",
    "evaluate_lag_terminal",
    "evaluate_local_arbitration_arm",
    "evaluate_local_suppressor_arm",
    "evaluate_sandbox_arm",
    "extract_learner_features",
    "generate_context_specialized_candidates",
    "generate_local_script_candidates",
    "generalize_script_candidates_to_fragments",
    "generate_risk_aware_candidates",
    "generate_position_sets",
    "is_valid_krk_seed",
    "inventory_legacy_predefined_topology_runs",
    "load_selected_candidate",
    "load_candidate_pool",
    "make_trace_record",
    "mine_triplet_candidates_from_artifact",
    "mine_triplet_candidates_from_records",
    "derive_local_suppressor",
    "run_autogrowth_experiment",
    "run_local_arbitration_experiment",
    "run_local_script_experiment",
    "run_local_suppressor_experiment",
    "run_script_fragment_experiment",
    "run_shared_feature_atom_experiment",
    "run_shared_atom_utility_voting",
    "run_native_quorum_materialization",
    "run_native_quorum_mate2_chaining",
    "run_internal_handoff_affordance_guard_audit",
    "run_terminal_lifecycle_modest_scale",
    "run_continuous_handoff_attention",
    "run_forced_chain_decomposition",
    "NativeFoundationScaleReplayConfig",
    "NativeFoundationScaleReplayResult",
    "run_native_foundation_scale_replay",
    "SingleMissRepairConfig",
    "SingleMissRepairResult",
    "run_single_miss_repair",
    "FrozenFoundationEdgeFenceReentryConfig",
    "FrozenFoundationEdgeFenceReentryResult",
    "run_frozen_foundation_edge_fence_reentry",
    "FrozenFoundationBridgePressureConfig",
    "FrozenFoundationBridgePressureResult",
    "run_frozen_foundation_bridge_pressure",
    "FrozenFoundationResponseCacheBridgeRetrievalConfig",
    "FrozenFoundationResponseCacheBridgeRetrievalResult",
    "run_frozen_foundation_response_cache_bridge_retrieval",
    "FoundationBackedBridgeFrontierConfig",
    "FoundationBackedBridgeFrontierResult",
    "run_foundation_backed_bridge_frontier",
    "PersistedFoundationBackedFrontierPoolConfig",
    "PersistedFoundationBackedFrontierPoolResult",
    "FullFoundationFrontierPoolResumeConfig",
    "FullFoundationFrontierPoolResumeResult",
    "FullFrontierValidationNearMissConfig",
    "FullFrontierValidationNearMissResult",
    "ControlledMixedFrontierEdgeCurriculumConfig",
    "ControlledMixedFrontierEdgeCurriculumResult",
    "StagedEdgeBridgeFoundationRolloutConfig",
    "StagedEdgeBridgeFoundationRolloutResult",
    "PersistedStagedPredecessorPoolConfig",
    "PersistedStagedPredecessorPoolResult",
    "StagedNearMissAblationRestorationConfig",
    "StagedNearMissAblationRestorationResult",
    "StagedPoolIntegrityModestScaleConfig",
    "StagedPoolIntegrityModestScaleResult",
    "TinyOnlineKRKEpisodeRunnerConfig",
    "TinyOnlineKRKEpisodeRunnerResult",
    "OnlineFailureDecompositionConfig",
    "OnlineFailureDecompositionResult",
    "ReplyRobustBridgePressureConfig",
    "ReplyRobustBridgePressureResult",
    "OnlineLowProgressRepairConfig",
    "OnlineLowProgressRepairResult",
    "ReplyRobustProgressPoolConfig",
    "ReplyRobustProgressPoolResult",
    "ProgressCandidateSelectionRepairConfig",
    "ProgressCandidateSelectionRepairResult",
    "TrajectoryPositivePrefixAuditConfig",
    "TrajectoryPositivePrefixAuditResult",
    "CachedTrajectorySelectionRepairConfig",
    "CachedTrajectorySelectionRepairResult",
    "StableTrajectoryCacheSelectionMicroprobeConfig",
    "StableTrajectoryCacheSelectionMicroprobeResult",
    "D3C3TrajectoryEvidenceRepairConfig",
    "D3C3TrajectoryEvidenceRepairResult",
    "RuntimeTrajectoryRepairIntegrationConfig",
    "RuntimeTrajectoryRepairIntegrationResult",
    "RealContextRuntimeTrajectoryValidationConfig",
    "RealContextRuntimeTrajectoryValidationResult",
    "run_persisted_foundation_backed_frontier_pool",
    "run_full_foundation_frontier_pool_resume",
    "run_full_frontier_validation_near_miss",
    "run_controlled_mixed_frontier_edge_curriculum",
    "run_staged_edge_bridge_foundation_rollout",
    "run_persisted_staged_predecessor_pool",
    "run_staged_near_miss_ablation_restoration",
    "run_staged_pool_integrity_modest_scale",
    "run_tiny_online_krk_episode_runner",
    "run_online_failure_decomposition",
    "run_reply_robust_bridge_pressure",
    "run_online_low_progress_repair",
    "run_reply_robust_progress_pool",
    "run_progress_candidate_selection_repair",
    "run_trajectory_positive_prefix_audit",
    "run_cached_trajectory_selection_repair",
    "run_stable_trajectory_cache_selection_microprobe",
    "run_d3c3_trajectory_evidence_repair",
    "run_runtime_trajectory_repair_integration",
    "run_real_context_runtime_trajectory_validation",
    "TERMINAL_LIFECYCLE_POLICY",
    "apply_terminal_lifecycle",
    "classify_terminal_kind",
    "run_single_graph_curriculum",
    "run_topological_growth_runway",
    "run_context_specialized_candidate_experiment",
    "run_context_gated_curriculum",
    "run_context_gated_edge_fence_validation",
    "run_continuation_retry_experiment",
    "run_curriculum_reward_recovery",
    "run_curated_terminal_curriculum",
    "run_curated_replay_curriculum",
    "run_edge_fence_curriculum",
    "run_fence_boundary_rehearsal",
    "run_fence_boundary_signal",
    "run_fragment_chain_curriculum",
    "run_foundation_curriculum",
    "run_handoff_filter_validation",
    "run_lag_terminal_experiment",
    "run_risk_aware_candidate_experiment",
    "run_retry_edge_experiment",
    "run_retry_diagnostics",
    "run_retry_candidate_expansion",
    "run_precision_gate_experiment",
    "run_persisted_pool_validation",
    "mine_retry_expansion_candidates",
    "derive_local_precision_gate",
    "audit_confinement_sign_semantics",
    "action_ranker_behavior_audit",
    "suppressor_confirms",
    "choose_local_script_action",
    "choose_lag_fragment_chain_action",
    "choose_continuation_retry_action",
    "extract_terminal_feature_vector",
    "feature_substrate_coverage_sample",
    "score_non_terminal_progress",
    "stage_inventory",
    "run_terminal_substrate_revival",
    "run_terminal_edge_fence_validation",
    "terminal_action_feature_keys",
    "train_context_gated_foundation_bundle",
    "train_growth_candidates",
    "train_terminal_foundation_bundle",
    "validate_learner_record",
]
