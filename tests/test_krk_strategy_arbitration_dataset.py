import importlib.util
import json
from pathlib import Path


_dataset_spec = importlib.util.spec_from_file_location(
    "build_krk_strategy_arbitration_dataset",
    Path(__file__).resolve().parents[1] / "scripts" / "build_krk_strategy_arbitration_dataset.py",
)
assert _dataset_spec is not None
assert _dataset_spec.loader is not None
_dataset = importlib.util.module_from_spec(_dataset_spec)
_dataset_spec.loader.exec_module(_dataset)

_probe_spec = importlib.util.spec_from_file_location(
    "probe_krk_strategy_arbitration",
    Path(__file__).resolve().parents[1] / "scripts" / "probe_krk_strategy_arbitration.py",
)
assert _probe_spec is not None
assert _probe_spec.loader is not None
_probe = importlib.util.module_from_spec(_probe_spec)
_probe_spec.loader.exec_module(_probe)

_challenge_manifest_spec = importlib.util.spec_from_file_location(
    "summarize_stage7_challenge_set_manifest",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_stage7_challenge_set_manifest.py",
)
assert _challenge_manifest_spec is not None
assert _challenge_manifest_spec.loader is not None
_challenge_manifest = importlib.util.module_from_spec(_challenge_manifest_spec)
_challenge_manifest_spec.loader.exec_module(_challenge_manifest)

_decision_gate_spec = importlib.util.spec_from_file_location(
    "summarize_krk_strategy_arbitration_decision_gate",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_strategy_arbitration_decision_gate.py",
)
assert _decision_gate_spec is not None
assert _decision_gate_spec.loader is not None
_decision_gate = importlib.util.module_from_spec(_decision_gate_spec)
_decision_gate_spec.loader.exec_module(_decision_gate)

_missing_feature_audit_spec = importlib.util.spec_from_file_location(
    "audit_krk_strategy_missing_features",
    Path(__file__).resolve().parents[1] / "scripts" / "audit_krk_strategy_missing_features.py",
)
assert _missing_feature_audit_spec is not None
assert _missing_feature_audit_spec.loader is not None
_missing_feature_audit = importlib.util.module_from_spec(_missing_feature_audit_spec)
_missing_feature_audit_spec.loader.exec_module(_missing_feature_audit)

_feature_validation_spec = importlib.util.spec_from_file_location(
    "validate_krk_feature_candidates",
    Path(__file__).resolve().parents[1] / "scripts" / "validate_krk_feature_candidates.py",
)
assert _feature_validation_spec is not None
assert _feature_validation_spec.loader is not None
_feature_validation = importlib.util.module_from_spec(_feature_validation_spec)
_feature_validation_spec.loader.exec_module(_feature_validation)

_monitor_records_spec = importlib.util.spec_from_file_location(
    "extract_krk_strategy_monitor_records",
    Path(__file__).resolve().parents[1] / "scripts" / "extract_krk_strategy_monitor_records.py",
)
assert _monitor_records_spec is not None
assert _monitor_records_spec.loader is not None
_monitor_records = importlib.util.module_from_spec(_monitor_records_spec)
_monitor_records_spec.loader.exec_module(_monitor_records)

_companion_audit_spec = importlib.util.spec_from_file_location(
    "audit_krk_strategy_monitor_companion_terms",
    Path(__file__).resolve().parents[1] / "scripts" / "audit_krk_strategy_monitor_companion_terms.py",
)
assert _companion_audit_spec is not None
assert _companion_audit_spec.loader is not None
_companion_audit = importlib.util.module_from_spec(_companion_audit_spec)
_companion_audit_spec.loader.exec_module(_companion_audit)

_visible_monitor_terms_spec = importlib.util.spec_from_file_location(
    "extract_krk_visible_monitor_terms",
    Path(__file__).resolve().parents[1] / "scripts" / "extract_krk_visible_monitor_terms.py",
)
assert _visible_monitor_terms_spec is not None
assert _visible_monitor_terms_spec.loader is not None
_visible_monitor_terms = importlib.util.module_from_spec(_visible_monitor_terms_spec)
_visible_monitor_terms_spec.loader.exec_module(_visible_monitor_terms)

_maturity_gate_spec = importlib.util.spec_from_file_location(
    "summarize_krk_strategy_monitor_maturity_gate",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_strategy_monitor_maturity_gate.py",
)
assert _maturity_gate_spec is not None
assert _maturity_gate_spec.loader is not None
_maturity_gate = importlib.util.module_from_spec(_maturity_gate_spec)
_maturity_gate_spec.loader.exec_module(_maturity_gate)

_internal_terminal_spec = importlib.util.spec_from_file_location(
    "summarize_krk_internal_terminal_candidates",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_internal_terminal_candidates.py",
)
assert _internal_terminal_spec is not None
assert _internal_terminal_spec.loader is not None
_internal_terminal = importlib.util.module_from_spec(_internal_terminal_spec)
_internal_terminal_spec.loader.exec_module(_internal_terminal)

_internal_terminal_evidence_spec = importlib.util.spec_from_file_location(
    "summarize_krk_internal_terminal_evidence",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_internal_terminal_evidence.py",
)
assert _internal_terminal_evidence_spec is not None
assert _internal_terminal_evidence_spec.loader is not None
_internal_terminal_evidence = importlib.util.module_from_spec(_internal_terminal_evidence_spec)
_internal_terminal_evidence_spec.loader.exec_module(_internal_terminal_evidence)

_protected_stage_status_spec = importlib.util.spec_from_file_location(
    "summarize_krk_protected_stage_status",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_protected_stage_status.py",
)
assert _protected_stage_status_spec is not None
assert _protected_stage_status_spec.loader is not None
_protected_stage_status = importlib.util.module_from_spec(_protected_stage_status_spec)
_protected_stage_status_spec.loader.exec_module(_protected_stage_status)

_self_expansion_gate_spec = importlib.util.spec_from_file_location(
    "summarize_krk_self_expansion_architecture_gate",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_self_expansion_architecture_gate.py",
)
assert _self_expansion_gate_spec is not None
assert _self_expansion_gate_spec.loader is not None
_self_expansion_gate = importlib.util.module_from_spec(_self_expansion_gate_spec)
_self_expansion_gate_spec.loader.exec_module(_self_expansion_gate)

_control_plane_contract_spec = importlib.util.spec_from_file_location(
    "summarize_krk_control_plane_contract",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_control_plane_contract.py",
)
assert _control_plane_contract_spec is not None
assert _control_plane_contract_spec.loader is not None
_control_plane_contract = importlib.util.module_from_spec(_control_plane_contract_spec)
_control_plane_contract_spec.loader.exec_module(_control_plane_contract)

_control_plane_manifest_spec = importlib.util.spec_from_file_location(
    "build_krk_control_plane_manifest",
    Path(__file__).resolve().parents[1] / "scripts" / "build_krk_control_plane_manifest.py",
)
assert _control_plane_manifest_spec is not None
assert _control_plane_manifest_spec.loader is not None
_control_plane_manifest = importlib.util.module_from_spec(_control_plane_manifest_spec)
_control_plane_manifest_spec.loader.exec_module(_control_plane_manifest)

_control_plane_gap_spec = importlib.util.spec_from_file_location(
    "summarize_krk_control_plane_gap_report",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_control_plane_gap_report.py",
)
assert _control_plane_gap_spec is not None
assert _control_plane_gap_spec.loader is not None
_control_plane_gap = importlib.util.module_from_spec(_control_plane_gap_spec)
_control_plane_gap_spec.loader.exec_module(_control_plane_gap)

_control_plane_frames_spec = importlib.util.spec_from_file_location(
    "export_krk_control_plane_frames",
    Path(__file__).resolve().parents[1] / "scripts" / "export_krk_control_plane_frames.py",
)
assert _control_plane_frames_spec is not None
assert _control_plane_frames_spec.loader is not None
_control_plane_frames = importlib.util.module_from_spec(_control_plane_frames_spec)
_control_plane_frames_spec.loader.exec_module(_control_plane_frames)

_control_plane_quality_spec = importlib.util.spec_from_file_location(
    "summarize_krk_control_plane_frame_quality",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_control_plane_frame_quality.py",
)
assert _control_plane_quality_spec is not None
assert _control_plane_quality_spec.loader is not None
_control_plane_quality = importlib.util.module_from_spec(_control_plane_quality_spec)
_control_plane_quality_spec.loader.exec_module(_control_plane_quality)

_control_plane_filter_spec = importlib.util.spec_from_file_location(
    "filter_krk_control_plane_frames",
    Path(__file__).resolve().parents[1] / "scripts" / "filter_krk_control_plane_frames.py",
)
assert _control_plane_filter_spec is not None
assert _control_plane_filter_spec.loader is not None
_control_plane_filter = importlib.util.module_from_spec(_control_plane_filter_spec)
_control_plane_filter_spec.loader.exec_module(_control_plane_filter)

_control_plane_strategy_probe_spec = importlib.util.spec_from_file_location(
    "probe_krk_control_plane_strategy_arbitration",
    Path(__file__).resolve().parents[1] / "scripts" / "probe_krk_control_plane_strategy_arbitration.py",
)
assert _control_plane_strategy_probe_spec is not None
assert _control_plane_strategy_probe_spec.loader is not None
_control_plane_strategy_probe = importlib.util.module_from_spec(_control_plane_strategy_probe_spec)
_control_plane_strategy_probe_spec.loader.exec_module(_control_plane_strategy_probe)

_control_plane_strategy_baseline_spec = importlib.util.spec_from_file_location(
    "probe_krk_control_plane_strategy_arbitration_baseline",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "probe_krk_control_plane_strategy_arbitration_baseline.py",
)
assert _control_plane_strategy_baseline_spec is not None
assert _control_plane_strategy_baseline_spec.loader is not None
_control_plane_strategy_baseline = importlib.util.module_from_spec(
    _control_plane_strategy_baseline_spec
)
_control_plane_strategy_baseline_spec.loader.exec_module(_control_plane_strategy_baseline)

_control_plane_stage7_boundary_refresh_spec = importlib.util.spec_from_file_location(
    "summarize_krk_control_plane_stage7_boundary_refresh",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "summarize_krk_control_plane_stage7_boundary_refresh.py",
)
assert _control_plane_stage7_boundary_refresh_spec is not None
assert _control_plane_stage7_boundary_refresh_spec.loader is not None
_control_plane_stage7_boundary_refresh = importlib.util.module_from_spec(
    _control_plane_stage7_boundary_refresh_spec
)
_control_plane_stage7_boundary_refresh_spec.loader.exec_module(_control_plane_stage7_boundary_refresh)

_protected_max_only_review_spec = importlib.util.spec_from_file_location(
    "summarize_krk_protected_max_only_frame_review",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "summarize_krk_protected_max_only_frame_review.py",
)
assert _protected_max_only_review_spec is not None
assert _protected_max_only_review_spec.loader is not None
_protected_max_only_review = importlib.util.module_from_spec(_protected_max_only_review_spec)
_protected_max_only_review_spec.loader.exec_module(_protected_max_only_review)

_protected_missing_provider_plan_spec = importlib.util.spec_from_file_location(
    "summarize_krk_protected_missing_provider_capacity_audit_plan",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "summarize_krk_protected_missing_provider_capacity_audit_plan.py",
)
assert _protected_missing_provider_plan_spec is not None
assert _protected_missing_provider_plan_spec.loader is not None
_protected_missing_provider_plan = importlib.util.module_from_spec(_protected_missing_provider_plan_spec)
_protected_missing_provider_plan_spec.loader.exec_module(_protected_missing_provider_plan)

_protected_missing_provider_manifest_spec = importlib.util.spec_from_file_location(
    "build_krk_protected_missing_provider_capacity_execution_manifest",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_krk_protected_missing_provider_capacity_execution_manifest.py",
)
assert _protected_missing_provider_manifest_spec is not None
assert _protected_missing_provider_manifest_spec.loader is not None
_protected_missing_provider_manifest = importlib.util.module_from_spec(
    _protected_missing_provider_manifest_spec
)
_protected_missing_provider_manifest_spec.loader.exec_module(_protected_missing_provider_manifest)

_protected_missing_provider_manifest_review_spec = importlib.util.spec_from_file_location(
    "review_krk_protected_missing_provider_capacity_execution_manifest",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_protected_missing_provider_capacity_execution_manifest.py",
)
assert _protected_missing_provider_manifest_review_spec is not None
assert _protected_missing_provider_manifest_review_spec.loader is not None
_protected_missing_provider_manifest_review = importlib.util.module_from_spec(
    _protected_missing_provider_manifest_review_spec
)
_protected_missing_provider_manifest_review_spec.loader.exec_module(_protected_missing_provider_manifest_review)

_protected_missing_provider_label_run_spec = importlib.util.spec_from_file_location(
    "run_krk_protected_missing_provider_capacity_labels",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_krk_protected_missing_provider_capacity_labels.py",
)
assert _protected_missing_provider_label_run_spec is not None
assert _protected_missing_provider_label_run_spec.loader is not None
_protected_missing_provider_label_run = importlib.util.module_from_spec(
    _protected_missing_provider_label_run_spec
)
_protected_missing_provider_label_run_spec.loader.exec_module(_protected_missing_provider_label_run)

_strategy_arbiter_risk_review_spec = importlib.util.spec_from_file_location(
    "review_krk_strategy_arbiter_evidence_risks",
    Path(__file__).resolve().parents[1] / "scripts" / "review_krk_strategy_arbiter_evidence_risks.py",
)
assert _strategy_arbiter_risk_review_spec is not None
assert _strategy_arbiter_risk_review_spec.loader is not None
_strategy_arbiter_risk_review = importlib.util.module_from_spec(
    _strategy_arbiter_risk_review_spec
)
_strategy_arbiter_risk_review_spec.loader.exec_module(_strategy_arbiter_risk_review)

_strategy_arbiter_stratified_spec = importlib.util.spec_from_file_location(
    "probe_krk_strategy_arbiter_stratified_v2",
    Path(__file__).resolve().parents[1] / "scripts" / "probe_krk_strategy_arbiter_stratified_v2.py",
)
assert _strategy_arbiter_stratified_spec is not None
assert _strategy_arbiter_stratified_spec.loader is not None
_strategy_arbiter_stratified = importlib.util.module_from_spec(
    _strategy_arbiter_stratified_spec
)
_strategy_arbiter_stratified_spec.loader.exec_module(_strategy_arbiter_stratified)

_forced_provider_control_plan_spec = importlib.util.spec_from_file_location(
    "plan_krk_forced_provider_control_labels",
    Path(__file__).resolve().parents[1] / "scripts" / "plan_krk_forced_provider_control_labels.py",
)
assert _forced_provider_control_plan_spec is not None
assert _forced_provider_control_plan_spec.loader is not None
_forced_provider_control_plan = importlib.util.module_from_spec(
    _forced_provider_control_plan_spec
)
_forced_provider_control_plan_spec.loader.exec_module(_forced_provider_control_plan)

_forced_provider_binding_spec = importlib.util.spec_from_file_location(
    "bind_krk_forced_provider_control_labels",
    Path(__file__).resolve().parents[1] / "scripts" / "bind_krk_forced_provider_control_labels.py",
)
assert _forced_provider_binding_spec is not None
assert _forced_provider_binding_spec.loader is not None
_forced_provider_binding = importlib.util.module_from_spec(_forced_provider_binding_spec)
_forced_provider_binding_spec.loader.exec_module(_forced_provider_binding)

_out_of_sample_manifest_spec = importlib.util.spec_from_file_location(
    "generate_krk_strategy_arbiter_out_of_sample_execution_manifest",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "generate_krk_strategy_arbiter_out_of_sample_execution_manifest.py",
)
assert _out_of_sample_manifest_spec is not None
assert _out_of_sample_manifest_spec.loader is not None
_out_of_sample_manifest = importlib.util.module_from_spec(_out_of_sample_manifest_spec)
_out_of_sample_manifest_spec.loader.exec_module(_out_of_sample_manifest)

_out_of_sample_manifest_review_spec = importlib.util.spec_from_file_location(
    "review_krk_strategy_arbiter_out_of_sample_execution_manifest",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_strategy_arbiter_out_of_sample_execution_manifest.py",
)
assert _out_of_sample_manifest_review_spec is not None
assert _out_of_sample_manifest_review_spec.loader is not None
_out_of_sample_manifest_review = importlib.util.module_from_spec(_out_of_sample_manifest_review_spec)
_out_of_sample_manifest_review_spec.loader.exec_module(_out_of_sample_manifest_review)

_out_of_sample_label_run_spec = importlib.util.spec_from_file_location(
    "run_krk_strategy_arbiter_out_of_sample_control_labels",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_krk_strategy_arbiter_out_of_sample_control_labels.py",
)
assert _out_of_sample_label_run_spec is not None
assert _out_of_sample_label_run_spec.loader is not None
_out_of_sample_label_run = importlib.util.module_from_spec(_out_of_sample_label_run_spec)
_out_of_sample_label_run_spec.loader.exec_module(_out_of_sample_label_run)

_out_of_sample_probe_spec = importlib.util.spec_from_file_location(
    "probe_krk_strategy_arbiter_out_of_sample_controls",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "probe_krk_strategy_arbiter_out_of_sample_controls.py",
)
assert _out_of_sample_probe_spec is not None
assert _out_of_sample_probe_spec.loader is not None
_out_of_sample_probe = importlib.util.module_from_spec(_out_of_sample_probe_spec)
_out_of_sample_probe_spec.loader.exec_module(_out_of_sample_probe)

_out_of_sample_arch_review_spec = importlib.util.spec_from_file_location(
    "summarize_krk_strategy_arbiter_out_of_sample_architecture_review",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "summarize_krk_strategy_arbiter_out_of_sample_architecture_review.py",
)
assert _out_of_sample_arch_review_spec is not None
assert _out_of_sample_arch_review_spec.loader is not None
_out_of_sample_arch_review = importlib.util.module_from_spec(_out_of_sample_arch_review_spec)
_out_of_sample_arch_review_spec.loader.exec_module(_out_of_sample_arch_review)

_selector_readiness_v2_spec = importlib.util.spec_from_file_location(
    "summarize_krk_selector_readiness_v2_plan",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_selector_readiness_v2_plan.py",
)
assert _selector_readiness_v2_spec is not None
assert _selector_readiness_v2_spec.loader is not None
_selector_readiness_v2 = importlib.util.module_from_spec(_selector_readiness_v2_spec)
_selector_readiness_v2_spec.loader.exec_module(_selector_readiness_v2)

_strategy_owner_contrast_spec = importlib.util.spec_from_file_location(
    "build_krk_strategy_owner_contrast_dataset",
    Path(__file__).resolve().parents[1] / "scripts" / "build_krk_strategy_owner_contrast_dataset.py",
)
assert _strategy_owner_contrast_spec is not None
assert _strategy_owner_contrast_spec.loader is not None
_strategy_owner_contrast = importlib.util.module_from_spec(_strategy_owner_contrast_spec)
_strategy_owner_contrast_spec.loader.exec_module(_strategy_owner_contrast)

_strategy_owner_label_plan_spec = importlib.util.spec_from_file_location(
    "plan_krk_strategy_owner_contrast_labels",
    Path(__file__).resolve().parents[1] / "scripts" / "plan_krk_strategy_owner_contrast_labels.py",
)
assert _strategy_owner_label_plan_spec is not None
assert _strategy_owner_label_plan_spec.loader is not None
_strategy_owner_label_plan = importlib.util.module_from_spec(_strategy_owner_label_plan_spec)
_strategy_owner_label_plan_spec.loader.exec_module(_strategy_owner_label_plan)

_strategy_owner_label_plan_review_spec = importlib.util.spec_from_file_location(
    "review_krk_strategy_owner_contrast_label_plan",
    Path(__file__).resolve().parents[1] / "scripts" / "review_krk_strategy_owner_contrast_label_plan.py",
)
assert _strategy_owner_label_plan_review_spec is not None
assert _strategy_owner_label_plan_review_spec.loader is not None
_strategy_owner_label_plan_review = importlib.util.module_from_spec(_strategy_owner_label_plan_review_spec)
_strategy_owner_label_plan_review_spec.loader.exec_module(_strategy_owner_label_plan_review)

_strategy_owner_bind_spec = importlib.util.spec_from_file_location(
    "bind_krk_strategy_owner_contrast_labels",
    Path(__file__).resolve().parents[1] / "scripts" / "bind_krk_strategy_owner_contrast_labels.py",
)
assert _strategy_owner_bind_spec is not None
assert _strategy_owner_bind_spec.loader is not None
_strategy_owner_bind = importlib.util.module_from_spec(_strategy_owner_bind_spec)
_strategy_owner_bind_spec.loader.exec_module(_strategy_owner_bind)

_strategy_owner_manifest_review_spec = importlib.util.spec_from_file_location(
    "review_krk_strategy_owner_contrast_execution_manifest",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_strategy_owner_contrast_execution_manifest.py",
)
assert _strategy_owner_manifest_review_spec is not None
assert _strategy_owner_manifest_review_spec.loader is not None
_strategy_owner_manifest_review = importlib.util.module_from_spec(_strategy_owner_manifest_review_spec)
_strategy_owner_manifest_review_spec.loader.exec_module(_strategy_owner_manifest_review)

_strategy_owner_label_run_spec = importlib.util.spec_from_file_location(
    "run_krk_strategy_owner_contrast_control_labels",
    Path(__file__).resolve().parents[1] / "scripts" / "run_krk_strategy_owner_contrast_control_labels.py",
)
assert _strategy_owner_label_run_spec is not None
assert _strategy_owner_label_run_spec.loader is not None
_strategy_owner_label_run = importlib.util.module_from_spec(_strategy_owner_label_run_spec)
_strategy_owner_label_run_spec.loader.exec_module(_strategy_owner_label_run)

_strategy_owner_probe_spec = importlib.util.spec_from_file_location(
    "probe_krk_strategy_owner_contrast_dataset",
    Path(__file__).resolve().parents[1] / "scripts" / "probe_krk_strategy_owner_contrast_dataset.py",
)
assert _strategy_owner_probe_spec is not None
assert _strategy_owner_probe_spec.loader is not None
_strategy_owner_probe = importlib.util.module_from_spec(_strategy_owner_probe_spec)
_strategy_owner_probe_spec.loader.exec_module(_strategy_owner_probe)

_selector_after_contrast_review_spec = importlib.util.spec_from_file_location(
    "summarize_krk_selector_readiness_after_contrast_probe",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "summarize_krk_selector_readiness_after_contrast_probe.py",
)
assert _selector_after_contrast_review_spec is not None
assert _selector_after_contrast_review_spec.loader is not None
_selector_after_contrast_review = importlib.util.module_from_spec(_selector_after_contrast_review_spec)
_selector_after_contrast_review_spec.loader.exec_module(_selector_after_contrast_review)

_selected_provider_diversity_plan_spec = importlib.util.spec_from_file_location(
    "plan_krk_selected_provider_diversity_evidence",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "plan_krk_selected_provider_diversity_evidence.py",
)
assert _selected_provider_diversity_plan_spec is not None
assert _selected_provider_diversity_plan_spec.loader is not None
_selected_provider_diversity_plan = importlib.util.module_from_spec(_selected_provider_diversity_plan_spec)
_selected_provider_diversity_plan_spec.loader.exec_module(_selected_provider_diversity_plan)

_selected_provider_scan_spec = importlib.util.spec_from_file_location(
    "scan_krk_selected_provider_diversity_replay_free",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "scan_krk_selected_provider_diversity_replay_free.py",
)
assert _selected_provider_scan_spec is not None
assert _selected_provider_scan_spec.loader is not None
_selected_provider_scan = importlib.util.module_from_spec(_selected_provider_scan_spec)
_selected_provider_scan_spec.loader.exec_module(_selected_provider_scan)

_selected_provider_sampling_manifest_spec = importlib.util.spec_from_file_location(
    "generate_krk_selected_provider_diversity_sampling_manifest",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "generate_krk_selected_provider_diversity_sampling_manifest.py",
)
assert _selected_provider_sampling_manifest_spec is not None
assert _selected_provider_sampling_manifest_spec.loader is not None
_selected_provider_sampling_manifest = importlib.util.module_from_spec(
    _selected_provider_sampling_manifest_spec
)
_selected_provider_sampling_manifest_spec.loader.exec_module(_selected_provider_sampling_manifest)

_selected_provider_sampling_review_spec = importlib.util.spec_from_file_location(
    "review_krk_selected_provider_diversity_sampling_manifest",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_selected_provider_diversity_sampling_manifest.py",
)
assert _selected_provider_sampling_review_spec is not None
assert _selected_provider_sampling_review_spec.loader is not None
_selected_provider_sampling_review = importlib.util.module_from_spec(
    _selected_provider_sampling_review_spec
)
_selected_provider_sampling_review_spec.loader.exec_module(_selected_provider_sampling_review)

_selected_provider_observation_scan_spec = importlib.util.spec_from_file_location(
    "run_krk_selected_provider_diversity_observation_scan",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_krk_selected_provider_diversity_observation_scan.py",
)
assert _selected_provider_observation_scan_spec is not None
assert _selected_provider_observation_scan_spec.loader is not None
_selected_provider_observation_scan = importlib.util.module_from_spec(
    _selected_provider_observation_scan_spec
)
_selected_provider_observation_scan_spec.loader.exec_module(_selected_provider_observation_scan)

_selected_provider_arch_review_spec = importlib.util.spec_from_file_location(
    "summarize_krk_selected_provider_diversity_architecture_review",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "summarize_krk_selected_provider_diversity_architecture_review.py",
)
assert _selected_provider_arch_review_spec is not None
assert _selected_provider_arch_review_spec.loader is not None
_selected_provider_arch_review = importlib.util.module_from_spec(_selected_provider_arch_review_spec)
_selected_provider_arch_review_spec.loader.exec_module(_selected_provider_arch_review)

_selector_readiness_v3_spec = importlib.util.spec_from_file_location(
    "summarize_krk_selector_readiness_v3_plan",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_selector_readiness_v3_plan.py",
)
assert _selector_readiness_v3_spec is not None
assert _selector_readiness_v3_spec.loader is not None
_selector_readiness_v3 = importlib.util.module_from_spec(_selector_readiness_v3_spec)
_selector_readiness_v3_spec.loader.exec_module(_selector_readiness_v3)

_default_off_design_review_spec = importlib.util.spec_from_file_location(
    "summarize_krk_strategy_arbiter_default_off_design_review_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "summarize_krk_strategy_arbiter_default_off_design_review_v1.py",
)
assert _default_off_design_review_spec is not None
assert _default_off_design_review_spec.loader is not None
_default_off_design_review = importlib.util.module_from_spec(_default_off_design_review_spec)
_default_off_design_review_spec.loader.exec_module(_default_off_design_review)

_runtime_review_packet_spec = importlib.util.spec_from_file_location(
    "summarize_krk_strategy_arbiter_runtime_review_packet_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "summarize_krk_strategy_arbiter_runtime_review_packet_v1.py",
)
assert _runtime_review_packet_spec is not None
assert _runtime_review_packet_spec.loader is not None
_runtime_review_packet = importlib.util.module_from_spec(_runtime_review_packet_spec)
_runtime_review_packet_spec.loader.exec_module(_runtime_review_packet)

_provider_label_plan_spec = importlib.util.spec_from_file_location(
    "summarize_krk_provider_label_coverage_plan",
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_provider_label_coverage_plan.py",
)
assert _provider_label_plan_spec is not None
assert _provider_label_plan_spec.loader is not None
_provider_label_plan = importlib.util.module_from_spec(_provider_label_plan_spec)
_provider_label_plan_spec.loader.exec_module(_provider_label_plan)


def test_strategy_proposal_frame_validation_roundtrip():
    frame = {
        "schema_version": "strategy_proposal_frame.v1",
        "state_id": "state.test",
        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
        "active_landmark_label": "box_shrink",
        "provider_id": "krk.box_shrink",
        "skill_id": "krk.box_shrink",
        "provider_version": "test",
        "move_uci": "a1a2",
        "raw_score": 0.5,
        "provider_local_rank": 1,
        "normalized_score": 1.0,
        "source_terms": ["box_area_relevance"],
        "role_licenses": [],
        "plan_capsule_context": {},
        "move_shape_terms": ["candidate_is_rook_move"],
        "post_move_terms": ["rook_safe_after_move"],
        "safety_terms": ["rook_safe_after_move"],
        "known_outcome_label": {"result": "mate"},
        "shadow_failure_labels": [],
        "causal_status": "non_causal",
    }

    _dataset.validate_strategy_proposal_frame(json.loads(json.dumps(frame)))


def test_krk_strategy_arbitration_dataset_v0_from_stage7_merge(tmp_path):
    root = tmp_path
    structural = root / "reports" / "structural_candidates"
    structural.mkdir(parents=True)
    (structural / "stage7_evidence_merge_table.json").write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "state_identity": {
                            "state_signature": "state.sample",
                            "post_reply_fen": "8/8/8/R7/4k3/8/3K4/8 w - - 2 2",
                            "source_artifacts": ["stage7_sample.json"],
                            "sample_support_count": 1,
                        },
                        "terminal_space_context": {
                            "black_king_edge_distance": 3,
                            "black_king_edge_bucket": "central_or_midboard",
                            "box_area": 28,
                            "box_area_relevance": "high",
                            "rook_safe": True,
                            "fence_cut_status": "fence_or_cut_not_preserved",
                            "king_support_status": "support_can_improve",
                            "mate_in_one_available": False,
                            "active_terminal_terms": ["rook_safe"],
                        },
                        "strategy_provider_evidence": {
                            "provider_local_rank_info": [
                                {
                                    "provider_id": "krk.stage0_basin",
                                    "move": "a5h5",
                                    "raw_score": 13.0,
                                    "provider_local_rank": 1,
                                    "provider_local_normalized_score": 1.0,
                                }
                            ],
                            "forced_provider_results": {
                                "krk.drive_to_edge": {
                                    "first_move": "a5b5",
                                    "result": "mate",
                                    "plies": 9,
                                    "horizon": 40,
                                }
                            },
                        },
                        "continuation_evidence": {"current_graph_result_h40": "max_plies"},
                        "hypothesis_labels": ["strategy_arbitration_candidate"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    dataset = _dataset.build_dataset(root)

    assert dataset["schema_version"] == "krk_strategy_arbitration_dataset.v0"
    assert dataset["causal_status"] == "non_causal_dataset"
    assert dataset["runtime_behavior_changed"] is False
    assert dataset["stage7_promotion_allowed"] is False
    assert dataset["stage8_training_allowed"] is False
    assert dataset["summary"]["records_by_source_stage"] == {"stage7": 1}
    record = dataset["records"][0]
    assert record["causal_status"] == "non_causal"
    assert len(record["strategy_proposals"]) == 2
    assert {frame["causal_status"] for frame in record["strategy_proposals"]} == {"non_causal"}


def test_krk_strategy_arbitration_probe_v0_is_non_causal(tmp_path):
    dataset = {
        "schema_version": "krk_strategy_arbitration_dataset.v0",
        "causal_status": "non_causal_dataset",
        "runtime_behavior_changed": False,
        "summary": {"record_count": 1, "proposal_count": 2},
        "records": [
            {
                "state_id": "state.test",
                "source_stage": "stage7",
                "result_label": {"current_graph_h40": "max_plies"},
                "terminal_space_context": {
                    "black_king_edge_bucket": "central_or_midboard",
                    "box_area_relevance": "high",
                    "white_king_can_improve_support": True,
                    "active_terminal_terms": ["rook_safe"],
                },
                "strategy_proposals": [
                    {
                        "schema_version": "strategy_proposal_frame.v1",
                        "state_id": "state.test",
                        "provider_id": "krk.stage0_basin",
                        "move_uci": "a5a8",
                        "raw_score": 10.0,
                        "provider_local_rank": 1,
                        "normalized_score": 1.0,
                        "known_outcome_label": {"result": "max_plies"},
                        "causal_status": "non_causal",
                    },
                    {
                        "schema_version": "strategy_proposal_frame.v1",
                        "state_id": "state.test",
                        "provider_id": "krk.drive_to_edge",
                        "move_uci": "a5h5",
                        "raw_score": 0.1,
                        "provider_local_rank": 1,
                        "normalized_score": 1.0,
                        "known_outcome_label": {"result": "mate"},
                        "causal_status": "non_causal",
                    },
                ],
            }
        ],
    }
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps(dataset), encoding="utf-8")

    probe = _probe.build_probe(path)

    assert probe["schema_version"] == "krk_strategy_arbitration_probe.v0"
    assert probe["causal_status"] == "non_causal_probe"
    assert probe["runtime_behavior_changed"] is False
    assert probe["stage7_promotion_allowed"] is False
    assert probe["stage8_training_allowed"] is False
    assert probe["metrics"]["raw_global_provider_score"]["hit_rate"] == 0.0
    assert probe["metrics"]["provider_local_rank1_coverage"]["coverage_rate"] == 1.0


def test_stage7_challenge_set_manifest_is_non_causal(tmp_path, monkeypatch):
    artifact_root = tmp_path / "reports" / "structural_candidates"
    strategy_root = tmp_path / "reports" / "strategy_arbitration"
    artifact_root.mkdir(parents=True)
    strategy_root.mkdir(parents=True)
    (artifact_root / "stage7_evidence_merge_table.json").write_text(
        json.dumps({"rows": [{"hypothesis_labels": ["strategy_arbitration_candidate"]}]}),
        encoding="utf-8",
    )
    (artifact_root / "stage7_0926_move_shape_role_candidate_audit.json").write_text(
        json.dumps({"schema_version": "x"}), encoding="utf-8"
    )
    (strategy_root / "krk_strategy_arbitration_dataset_v0.json").write_text(
        json.dumps({"records": [{"state_id": "state.test"}]}), encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    manifest = _challenge_manifest.build_manifest(artifact_root)

    assert manifest["schema_version"] == "stage7_challenge_set_manifest.v1"
    assert manifest["causal_status"] == "non_causal_manifest"
    assert manifest["runtime_behavior_changed"] is False
    assert manifest["stage7_promotion_allowed"] is False
    assert manifest["stage8_training_allowed"] is False
    assert manifest["summary"]["challenge_family_count"] >= 6
    assert all(family["held_out_challenge_case"] for family in manifest["families"])


def test_krk_strategy_arbitration_decision_gate_selects_missing_feature(tmp_path):
    report_root = tmp_path / "reports" / "strategy_arbitration"
    report_root.mkdir(parents=True)
    (report_root / "krk_strategy_arbitration_dataset_v0.json").write_text(
        json.dumps({"summary": {"record_count": 3, "proposal_count": 5}}), encoding="utf-8"
    )
    (report_root / "krk_strategy_arbitration_probe_v0.json").write_text(
        json.dumps(
            {
                "decision": {"status": "missing_feature_first"},
                "metrics": {
                    "raw_global_provider_score": {"hit_rate": 0.9},
                    "provider_local_rank1_coverage": {"coverage_rate": 1.0},
                    "visible_heuristic_arbiter": {"hit_rate": 0.1},
                },
            }
        ),
        encoding="utf-8",
    )
    (report_root / "stage7_challenge_set_manifest.json").write_text(
        json.dumps({"summary": {"challenge_family_count": 6}}), encoding="utf-8"
    )

    gate = _decision_gate.build_gate(report_root)

    assert gate["schema_version"] == "krk_strategy_arbitration_decision_gate.v0"
    assert gate["causal_status"] == "non_causal_decision_gate"
    assert gate["runtime_behavior_changed"] is False
    assert gate["stage7_promotion_allowed"] is False
    assert gate["stage8_training_allowed"] is False
    assert gate["selected_status"] == "missing_feature_first"
    assert gate["recommendation"]["next_class"] == "non_causal_terminal_affordance_candidate_audit"


def test_krk_strategy_missing_feature_audit_proposes_non_causal_candidates(tmp_path):
    report_root = tmp_path / "reports" / "strategy_arbitration"
    report_root.mkdir(parents=True)
    (report_root / "krk_strategy_arbitration_dataset_v0.json").write_text(
        json.dumps(
            {
                "summary": {"record_count": 1, "proposal_count": 1},
                "records": [
                    {
                        "state_id": "state.edge",
                        "source_stage": "stage7",
                        "result_label": {"current_graph_h40": "max_plies"},
                        "terminal_space_context": {
                            "black_king_edge_bucket": "at_edge",
                            "box_area_relevance": "low",
                            "edge_net_pressure_proxy": True,
                            "white_king_can_improve_support": True,
                        },
                        "strategy_proposals": [{"provider_id": "krk.stage0_basin"}],
                        "hypothesis_labels": ["missing_feature_candidate"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (report_root / "krk_strategy_arbitration_probe_v0.json").write_text(
        json.dumps({"decision": {"status": "missing_feature_first"}}), encoding="utf-8"
    )
    (report_root / "stage7_challenge_set_manifest.json").write_text(
        json.dumps({"summary": {"challenge_family_count": 6}}), encoding="utf-8"
    )

    audit = _missing_feature_audit.build_audit(report_root)

    assert audit["schema_version"] == "krk_strategy_missing_feature_audit.v0"
    assert audit["causal_status"] == "non_causal_audit"
    assert audit["runtime_behavior_changed"] is False
    assert audit["stage7_promotion_allowed"] is False
    assert audit["stage8_training_allowed"] is False
    assert audit["recommended_next_step"] == (
        "stop_for_architecture_review_before_any_terminal_or_affordance_runtime_sandbox"
    )
    assert {candidate["causal_status"] for candidate in audit["candidates"]} == {"non_causal"}
    assert {candidate["promotion_status"] for candidate in audit["candidates"]} == {"proposed"}


def test_krk_feature_candidate_validation_types_candidates_without_runtime_effects(tmp_path):
    report_root = tmp_path / "reports" / "strategy_arbitration"
    report_root.mkdir(parents=True)
    (report_root / "krk_strategy_missing_feature_candidates.json").write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "candidate_id": "cand.krk.strategy.edge_net_affordance.v0",
                        "candidate_type": "terminal_affordance_refinement",
                        "proposed_change": {"target_concept": "edge_net_affordance"},
                    },
                    {
                        "candidate_id": "cand.krk.strategy.plan_selection_needed.v0",
                        "candidate_type": "terminal_affordance_refinement",
                        "proposed_change": {"target_concept": "plan_selection_needed"},
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    (report_root / "krk_strategy_arbitration_dataset_v0.json").write_text(
        json.dumps(
            {
                "summary": {"record_count": 3, "proposal_count": 3},
                "records": [
                    {
                        "state_id": "state.edge.mate",
                        "source_stage": "stage5",
                        "result_label": {"playout_result": "mate"},
                        "terminal_space_context": {
                            "black_king_edge_bucket": "at_edge",
                            "edge_net_pressure_proxy": True,
                            "box_area_relevance": "low",
                        },
                    },
                    {
                        "state_id": "state.edge.fail",
                        "source_stage": "stage7",
                        "result_label": {"current_graph_h40": "max_plies"},
                        "terminal_space_context": {
                            "black_king_edge_bucket": "at_edge",
                            "edge_net_pressure_proxy": True,
                            "box_area_relevance": "low",
                        },
                    },
                    {
                        "state_id": "state.stage7.unknown",
                        "source_stage": "stage7",
                        "result_label": {"current_graph_h40": None},
                        "terminal_space_context": {
                            "black_king_edge_bucket": "central_or_midboard",
                            "box_area_relevance": "high",
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (report_root / "krk_strategy_arbitration_probe_v0.json").write_text(
        json.dumps({"decision": {"status": "missing_feature_first"}}), encoding="utf-8"
    )

    validation = _feature_validation.build_validation(report_root)

    assert validation["schema_version"] == "krk_feature_candidate_validation.v0"
    assert validation["causal_status"] == "non_causal_validation"
    assert validation["runtime_behavior_changed"] is False
    assert validation["runtime_defaults_changed"] is False
    assert validation["stage7_promotion_allowed"] is False
    assert validation["stage8_training_allowed"] is False
    assert validation["summary"]["all_candidates_remain_non_causal"] is True
    assert validation["summary"]["sandbox_ready_candidate_ids"] == []
    assert {
        item["target_concept"]: item["causal_recommendation"]
        for item in validation["candidate_validations"]
    } == {
        "edge_net_affordance": "sandbox-blocked",
        "plan_selection_needed": "non-causal only",
    }


def test_strategy_monitor_record_validation_roundtrip():
    record = {
        "schema_version": "strategy_monitor_record.v1",
        "monitor_id": "monitor.krk.phase.state.test.0",
        "monitor_type": "PhaseBoundaryMonitor",
        "source_candidate_id": "cand.krk.strategy.phase_boundary_near_edge.v0",
        "active_landmark_label": "box_shrink",
        "state_id": "state.test",
        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
        "source_terms": ["black_king_edge_bucket in {at_edge, near_edge}"],
        "missing_terms": ["successful_next_provider"],
        "confidence": 0.5,
        "associated_outcome": "max_plies",
        "suggested_action_class": "audit_owner_phase",
        "causal_status": "non_causal",
        "promotion_status": "proposed",
        "notes": "roundtrip",
    }

    _monitor_records.validate_strategy_monitor_record(json.loads(json.dumps(record)))


def test_krk_strategy_monitor_record_extraction_is_non_causal(tmp_path):
    report_root = tmp_path / "reports" / "strategy_arbitration"
    report_root.mkdir(parents=True)
    (report_root / "krk_strategy_arbitration_dataset_v0.json").write_text(
        json.dumps(
            {
                "records": [
                    {
                        "state_id": "state.edge.fail",
                        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                        "active_landmark_label": "box_shrink",
                        "source_stage": "stage7",
                        "result_label": {"current_graph_h40": "max_plies"},
                        "terminal_space_context": {
                            "black_king_edge_bucket": "at_edge",
                            "box_area_relevance": "low",
                            "edge_net_pressure_proxy": True,
                            "fence_exists": True,
                            "fence_stable": False,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (report_root / "krk_feature_candidate_validation_v0.json").write_text(
        json.dumps(
            {
                "candidate_validations": [
                    {
                        "candidate_id": "cand.krk.strategy.phase_boundary_near_edge.v0",
                        "target_concept": "phase_boundary_near_edge",
                        "typed_as": "needs refinement / companion terms",
                        "mate_precision": 0.48,
                        "max_plies_failure_precision": 0.52,
                        "required_scope_or_companion_terms": ["successful_next_provider"],
                        "typing_rationale": "mixed",
                    },
                    {
                        "candidate_id": "cand.krk.strategy.king_support_conversion_affordance.v0",
                        "target_concept": "king_support_conversion_affordance",
                        "typed_as": "too broad / reject",
                        "mate_precision": 0.4,
                        "max_plies_failure_precision": 0.6,
                        "required_scope_or_companion_terms": ["king_support_improvement_move_exists"],
                        "typing_rationale": "too broad",
                    },
                    {
                        "candidate_id": "cand.krk.strategy.plan_selection_needed.v0",
                        "target_concept": "plan_selection_needed",
                        "typed_as": "growth-pressure/internal monitor",
                        "mate_precision": 0.0,
                        "max_plies_failure_precision": 1.0,
                        "required_scope_or_companion_terms": ["plan_capsule_context"],
                        "typing_rationale": "stage7 only",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    (report_root / "krk_strategy_missing_feature_candidates.json").write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "candidate_id": "cand.krk.strategy.phase_boundary_near_edge.v0",
                        "proposed_change": {"target_concept": "phase_boundary_near_edge"},
                        "source_terms": ["black_king_edge_bucket in {at_edge, near_edge}"],
                    },
                    {
                        "candidate_id": "cand.krk.strategy.king_support_conversion_affordance.v0",
                        "proposed_change": {"target_concept": "king_support_conversion_affordance"},
                        "source_terms": ["white_king_support_available"],
                    },
                    {
                        "candidate_id": "cand.krk.strategy.plan_selection_needed.v0",
                        "proposed_change": {"target_concept": "plan_selection_needed"},
                        "source_terms": ["stage7 residual"],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    payload = _monitor_records.build_monitor_records(report_root)

    assert payload["schema_version"] == "krk_strategy_monitor_records.v0"
    assert payload["causal_status"] == "non_causal_monitor_extraction"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["rejected_definition_count"] == 1
    assert {record["causal_status"] for record in payload["records"]} == {"non_causal"}
    assert "RejectedFeatureDefinition" not in {record["monitor_type"] for record in payload["records"]}


def test_krk_strategy_monitor_companion_audit_is_replay_free_and_non_causal(tmp_path):
    report_root = tmp_path / "reports" / "strategy_arbitration"
    report_root.mkdir(parents=True)
    (report_root / "krk_strategy_monitor_companion_terms_v0.json").write_text(
        json.dumps(
            {
                "companion_sets": [
                    {
                        "set_id": "phase_boundary_companions",
                        "target_monitor_types": ["PhaseBoundaryMonitor"],
                        "source_concepts": ["phase_boundary_near_edge"],
                        "candidate_terms": [
                            "current_owner",
                            "safe_edge_net_tighten_move_exists",
                            "active_landmark_label == box_shrink",
                        ],
                    }
                ],
                "blocked_next_steps": ["runtime_arbiter"],
            }
        ),
        encoding="utf-8",
    )
    (report_root / "krk_strategy_arbitration_dataset_v0.json").write_text(
        json.dumps(
            {
                "records": [
                    {
                        "state_id": "state.test",
                        "active_landmark_label": "box_shrink",
                        "terminal_space_context": {
                            "active_terminal_terms": ["safe_check_available"],
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    payload = _companion_audit.build_audit(report_root)

    assert payload["schema_version"] == "krk_strategy_monitor_companion_audit.v0"
    assert payload["causal_status"] == "non_causal_audit"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    statuses = {
        term["term"]: term["availability_status"]
        for companion_set in payload["companion_sets"]
        for term in companion_set["terms"]
    }
    assert statuses["current_owner"] == "proxy_available"
    assert statuses["active_landmark_label == box_shrink"] == "available_expression"
    assert statuses["safe_edge_net_tighten_move_exists"] == "missing_requires_visible_extraction"


def test_krk_visible_monitor_terms_are_diagnostic_only(tmp_path):
    report_root = tmp_path / "reports" / "strategy_arbitration"
    report_root.mkdir(parents=True)
    (report_root / "krk_strategy_arbitration_dataset_v0.json").write_text(
        json.dumps(
            {
                "records": [
                    {
                        "state_id": "state.test",
                        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                        "source_stage": "stage7",
                        "active_landmark_label": "box_shrink",
                        "result_label": {"current_graph_h40": "max_plies"},
                        "hypothesis_labels": ["strategy_arbitration_candidate"],
                        "terminal_space_context": {
                            "black_king_edge_bucket": "at_edge",
                            "box_area_relevance": "low",
                            "edge_net_pressure_proxy": True,
                            "mate_basin_readiness": False,
                            "rook_safe": True,
                            "stalemate_or_draw_risk": False,
                            "active_terminal_terms": [
                                "repair_or_reestablish_cut_available",
                                "king_support_improvement_move_exists",
                            ],
                        },
                        "strategy_proposals": [
                            {
                                "known_outcome_label": {"result": "mate"},
                                "post_move_terms": ["cut_restored_after_move"],
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    payload = _visible_monitor_terms.build_visible_terms(report_root)

    assert payload["schema_version"] == "krk_visible_monitor_terms.v0"
    assert payload["causal_status"] == "non_causal_diagnostic_terms"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    terms = payload["records"][0]["terms"]
    assert terms["king_support_improves_after_move"]["value"] is True
    assert terms["cut_or_fence_restored_after_move"]["value"] is True
    assert terms["safe_repair_move_exists"]["value"] is True
    assert terms["box_area_no_longer_decision_relevant"]["value"] is True
    assert terms["local_provider_competition_failed"]["value"] is True
    assert {term_payload["causal_status"] for term_payload in terms.values()} == {"non_causal"}


def test_krk_strategy_monitor_companion_audit_v1_uses_visible_terms(tmp_path):
    report_root = tmp_path / "reports" / "strategy_arbitration"
    report_root.mkdir(parents=True)
    (report_root / "krk_strategy_monitor_companion_terms_v0.json").write_text(
        json.dumps(
            {
                "companion_sets": [
                    {
                        "set_id": "repair_needed_companions",
                        "target_monitor_types": ["RepairNeededMonitor"],
                        "source_concepts": ["fence_or_cut_repair_affordance"],
                        "candidate_terms": ["safe_repair_move_exists", "cut_or_fence_restored_after_move"],
                    }
                ],
                "blocked_next_steps": ["runtime_arbiter"],
            }
        ),
        encoding="utf-8",
    )
    (report_root / "krk_strategy_arbitration_dataset_v0.json").write_text(
        json.dumps({"records": [{"state_id": "state.test", "terminal_space_context": {}}]}),
        encoding="utf-8",
    )
    visible_path = report_root / "krk_visible_monitor_terms_v0.json"
    visible_path.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "state_id": "state.test",
                        "terms": {
                            "safe_repair_move_exists": {
                                "value": True,
                                "confidence": "expression_from_current_state_terms",
                            },
                            "cut_or_fence_restored_after_move": {
                                "value": False,
                                "confidence": "not_observed",
                            },
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    payload = _companion_audit.build_audit(
        report_root,
        visible_terms_path=visible_path,
        schema_version="krk_strategy_monitor_companion_audit.v1",
    )

    assert payload["schema_version"] == "krk_strategy_monitor_companion_audit.v1"
    assert payload["summary"]["visible_terms_applied"] is True
    assert payload["summary"]["visible_term_count"] == 2
    assert payload["summary"]["terms_moved_to_extracted"] == [
        "safe_repair_move_exists",
        "cut_or_fence_restored_after_move",
    ]
    assert payload["companion_sets"][0]["set_availability_status"] == "improved_by_visible_extraction"
    assert {term["availability_status"] for term in payload["companion_sets"][0]["terms"]} == {
        "available_extracted"
    }


def test_krk_strategy_monitor_maturity_gate_blocks_causal_use(tmp_path):
    report_root = tmp_path / "reports" / "strategy_arbitration"
    report_root.mkdir(parents=True)
    (report_root / "krk_visible_monitor_terms_v0.json").write_text(
        json.dumps(
            {
                "summary": {
                    "term_names": [
                        "king_support_improves_after_move",
                        "cut_or_fence_restored_after_move",
                        "safe_repair_move_exists",
                        "box_area_no_longer_decision_relevant",
                        "post_plan_stagnation",
                        "local_provider_competition_failed",
                    ]
                },
                "records": [
                    {
                        "state_id": "state.fail",
                        "source_stage": "stage7",
                        "associated_outcome": "max_plies",
                        "terms": {
                            "king_support_improves_after_move": {"value": True},
                            "cut_or_fence_restored_after_move": {"value": True},
                            "safe_repair_move_exists": {"value": True},
                            "box_area_no_longer_decision_relevant": {"value": True},
                            "post_plan_stagnation": {"value": True},
                            "local_provider_competition_failed": {"value": True},
                        },
                    },
                    {
                        "state_id": "state.mate",
                        "source_stage": "stage5",
                        "associated_outcome": "mate",
                        "terms": {
                            "king_support_improves_after_move": {"value": True},
                            "cut_or_fence_restored_after_move": {"value": False},
                            "safe_repair_move_exists": {"value": True},
                            "box_area_no_longer_decision_relevant": {"value": True},
                            "post_plan_stagnation": {"value": False},
                            "local_provider_competition_failed": {"value": False},
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (report_root / "krk_strategy_monitor_records_v0.json").write_text(
        json.dumps(
            {
                "summary": {
                    "outcomes_by_monitor_type": {
                        "PlanSelectionNeededMonitor": {"max_plies": 1},
                        "OwnerExitMonitor": {"mate": 1, "max_plies": 1},
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    (report_root / "krk_strategy_monitor_companion_audit_v1.json").write_text(
        json.dumps(
            {
                "summary": {
                    "still_missing_terms": [
                        "safe_edge_net_tighten_move_exists",
                        "king_support_improves_after_reply",
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    gate = _maturity_gate.build_gate(report_root)

    assert gate["schema_version"] == "krk_strategy_monitor_maturity_gate.v0"
    assert gate["causal_status"] == "non_causal_maturity_gate"
    assert gate["runtime_behavior_changed"] is False
    assert gate["runtime_defaults_changed"] is False
    assert gate["stage7_promotion_allowed"] is False
    assert gate["stage8_training_allowed"] is False
    assert gate["summary"]["causal_ready_terms"] == []
    assert gate["summary"]["strongest_internal_terminal_candidates"] == [
        "post_plan_stagnation",
        "local_provider_competition_failed",
    ]
    assert all(item["causal_use_blocked"] is True for item in gate["term_maturity"])
    assert {
        item["term"]: item["maturity_status"] for item in gate["term_maturity"]
    }["post_plan_stagnation"] == "internal_terminal_candidate"


def test_internal_terminal_spec_validation_roundtrip():
    spec = {
        "schema_version": "internal_terminal_spec.v1",
        "terminal_id": "terminal.krk.test_monitor",
        "monitor_type": "internal_control_test_monitor",
        "source_monitor_candidates": ["test_monitor"],
        "source_terms": ["test_term"],
        "missing_terms": ["missing_term"],
        "intended_scope": "diagnostic only",
        "forbidden_causal_uses": ["choose_provider"],
        "potential_future_consumers": ["GrowthMonitor"],
        "validation_requirements": ["broader evidence"],
        "maturity_status": "internal_terminal_candidate",
        "causal_status": "non_causal",
        "promotion_status": "monitoring_only",
    }

    _internal_terminal.validate_internal_terminal_spec(json.loads(json.dumps(spec)))


def test_internal_terminal_validation_record_roundtrip():
    record = {
        "schema_version": "internal_terminal_validation_record.v1",
        "terminal_id": "terminal.krk.test_monitor",
        "state_id": "state.test",
        "family_id": "state.test",
        "active_landmark_label": "box_shrink",
        "source_terms_met": ["local_provider_competition_failed"],
        "missing_terms": ["route_conflict"],
        "associated_outcome": "max_plies",
        "stage": "stage7",
        "confidence": "replay_free_existing_artifact",
        "false_positive_risk": "unknown",
        "false_negative_risk": "unknown",
        "notes": "roundtrip",
    }

    _internal_terminal.validate_internal_terminal_validation_record(json.loads(json.dumps(record)))


def test_krk_internal_terminal_candidates_and_validation_are_non_causal(tmp_path):
    report_root = tmp_path / "reports" / "strategy_arbitration"
    report_root.mkdir(parents=True)
    (report_root / "krk_visible_monitor_terms_v0.json").write_text(
        json.dumps(
            {
                "records": [
                    {
                        "state_id": "state.fail",
                        "source_stage": "stage7",
                        "active_landmark_label": "box_shrink",
                        "associated_outcome": "max_plies",
                        "terms": {
                            "local_provider_competition_failed": {"value": True},
                            "post_plan_stagnation": {"value": True},
                            "box_area_no_longer_decision_relevant": {"value": True},
                            "cut_or_fence_restored_after_move": {"value": True},
                            "safe_repair_move_exists": {"value": True},
                        },
                    },
                    {
                        "state_id": "state.mate",
                        "source_stage": "stage5",
                        "active_landmark_label": "fence_established",
                        "associated_outcome": "mate",
                        "terms": {
                            "local_provider_competition_failed": {"value": False},
                            "post_plan_stagnation": {"value": False},
                            "box_area_no_longer_decision_relevant": {"value": False},
                            "cut_or_fence_restored_after_move": {"value": False},
                            "safe_repair_move_exists": {"value": True},
                        },
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    candidates = _internal_terminal.build_candidates(report_root)
    validation = _internal_terminal.build_validation(report_root, candidates)

    assert candidates["schema_version"] == "krk_internal_terminal_candidates.v0"
    assert candidates["causal_status"] == "non_causal_design"
    assert validation["schema_version"] == "krk_internal_terminal_validation.v0"
    assert validation["causal_status"] == "non_causal_validation"
    assert validation["runtime_behavior_changed"] is False
    assert validation["stage7_promotion_allowed"] is False
    assert validation["stage8_training_allowed"] is False
    assert validation["summary"]["causal_ready_terminals"] == []
    assert validation["summary"]["strongest_internal_terminal_candidates"] == [
        "terminal.krk.local_provider_competition_failed",
        "terminal.krk.post_plan_stagnation",
    ]
    assert all(item["causal_use_blocked"] is True for item in validation["terminal_validations"])


def test_krk_internal_terminal_evidence_and_review_are_non_causal(tmp_path):
    report_root = tmp_path / "reports" / "strategy_arbitration"
    structural_root = tmp_path / "reports" / "structural_candidates"
    report_root.mkdir(parents=True)
    structural_root.mkdir(parents=True)
    candidates = _internal_terminal.build_candidates(report_root)
    (report_root / "krk_internal_terminal_candidates_v0.json").write_text(
        json.dumps(candidates), encoding="utf-8"
    )
    (report_root / "krk_visible_monitor_terms_v0.json").write_text(
        json.dumps(
            {
                "records": [
                    {
                        "state_id": "state.fail",
                        "source_stage": "stage7",
                        "active_landmark_label": "box_shrink",
                        "associated_outcome": "max_plies",
                        "terms": {
                            "local_provider_competition_failed": {"value": True},
                            "post_plan_stagnation": {"value": True},
                            "box_area_no_longer_decision_relevant": {"value": True},
                            "cut_or_fence_restored_after_move": {"value": True},
                            "safe_repair_move_exists": {"value": True},
                        },
                    },
                    {
                        "state_id": "state.mate",
                        "source_stage": "stage5",
                        "active_landmark_label": "fence_established",
                        "associated_outcome": "mate",
                        "terms": {
                            "local_provider_competition_failed": {"value": False},
                            "post_plan_stagnation": {"value": False},
                            "box_area_no_longer_decision_relevant": {"value": False},
                            "cut_or_fence_restored_after_move": {"value": False},
                            "safe_repair_move_exists": {"value": True},
                        },
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    validation = _internal_terminal.build_validation(report_root, candidates)
    (report_root / "krk_internal_terminal_validation_v0.json").write_text(
        json.dumps(validation), encoding="utf-8"
    )
    (report_root / "krk_strategy_arbitration_dataset_v0.json").write_text(
        json.dumps(
            {
                "records": [
                    {
                        "state_id": "state.fail",
                        "source_stage": "stage7",
                        "active_landmark_label": "box_shrink",
                        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                        "result_label": {"current_graph_h40": "max_plies"},
                        "hypothesis_labels": ["strategy_arbitration_candidate"],
                        "terminal_space_context": {"fence_stable": False},
                        "strategy_proposals": [
                            {
                                "provider_id": "krk.stage0_basin",
                                "move_uci": "a1a2",
                                "raw_score": 10.0,
                            },
                            {
                                "provider_id": "krk.drive_to_edge",
                                "move_uci": "a1a3",
                                "raw_score": 0.2,
                            },
                        ],
                    },
                    {
                        "state_id": "state.mate",
                        "source_stage": "stage5",
                        "active_landmark_label": "fence_established",
                        "result_label": {"playout_result": "mate"},
                        "hypothesis_labels": [],
                        "terminal_space_context": {"fence_stable": True},
                        "strategy_proposals": [],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    (report_root / "krk_strategy_monitor_records_v0.json").write_text(
        json.dumps(
            {
                "summary": {
                    "outcomes_by_monitor_type": {
                        "PlanSelectionNeededMonitor": {"max_plies": 1},
                        "RepairNeededMonitor": {"mate": 1, "max_plies": 1},
                    },
                    "records_by_monitor_type": {
                        "PlanSelectionNeededMonitor": 1,
                        "RepairNeededMonitor": 2,
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (structural_root / "stage7_evidence_merge_table.json").write_text(
        json.dumps({"rows": []}), encoding="utf-8"
    )

    evidence = _internal_terminal_evidence.build_evidence(report_root, structural_root)
    review = _internal_terminal_evidence.build_design_review(evidence)

    assert evidence["schema_version"] == "krk_internal_terminal_evidence.v1"
    assert evidence["causal_status"] == "non_causal_evidence"
    assert evidence["runtime_behavior_changed"] is False
    assert evidence["runtime_defaults_changed"] is False
    assert evidence["stage7_promotion_allowed"] is False
    assert evidence["stage8_training_allowed"] is False
    assert evidence["summary"]["causal_ready_terminals"] == []
    assert all(item["causal_ready"] is False for item in evidence["terminal_evidence"])
    assert any(
        item["terminal_id"] == "terminal.krk.local_provider_competition_failed"
        and item["associated_provider_strategy_patterns"]["raw_top_provider_counts"]["krk.stage0_basin"] == 1
        for item in evidence["terminal_evidence"]
    )

    assert review["schema_version"] == "krk_internal_terminal_design_review.v1"
    assert review["causal_status"] == "non_causal_design_review"
    assert review["runtime_behavior_changed"] is False
    assert review["runtime_defaults_changed"] is False
    assert review["summary"]["causal_ready_terminals"] == []
    assert all(item["causal_ready"] is False for item in review["terminal_readiness"])
    assert "no_hidden_controller" in review["runtime_promotion_readiness_checklist"]
    assert "no_topology_mutation_during_gameplay" in review["runtime_promotion_readiness_checklist"]


def test_krk_protected_stage_status_preserves_stage4_caveat(tmp_path):
    root = tmp_path

    def write_json(relative_path, payload):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    validation_profile = {
        "schema_version": "composition_profile.v1",
        "profile_id": "handoff_composition_v1",
    }
    write_json(
        _protected_stage_status.STAGE1_MANIFEST,
        {
            "formal_validation": {
                "mode": "strict_pairs",
                "validated": True,
                "nodes": 257,
                "edges": 796,
            },
            "evaluation": {"stage1_eval_samples": 50},
            "learner_readiness": {"ready": True},
        },
    )
    write_json(
        _protected_stage_status.STAGE4_PROFILE,
        {
            "total": 500,
            "improved": 500,
            "optimal": 500,
            "worsened": 0,
            "no_move": 0,
            "playouts": {"mate": 500},
            "conversion_status_counts": {"passed": 500},
            "one_ply_status_counts": {"passed": 500},
            "shadow_candidates": [],
            "composition_profile": validation_profile,
        },
    )
    write_json(
        _protected_stage_status.STAGE5_PROFILE,
        {
            "total": 1000,
            "improved": 1000,
            "optimal": 1000,
            "worsened": 0,
            "no_move": 0,
            "playouts": {"mate": 1000},
            "conversion_status_counts": {"passed": 1000},
            "one_ply_status_counts": {"passed": 1000},
            "shadow_candidates": [],
            "composition_profile": validation_profile,
        },
    )
    write_json(
        _protected_stage_status.STAGE6_CANDIDATE,
        {
            "total": 300,
            "improved": 300,
            "optimal": 217,
            "worsened": 0,
            "no_move": 0,
            "playouts": {"mate": 300},
            "conversion_status_counts": {"passed": 300},
            "one_ply_status_counts": {"passed": 217, "failed": 83},
            "shadow_candidates": [],
            "composition_profile": validation_profile,
        },
    )
    write_json(
        _protected_stage_status.STAGE5_OVERLAY_GUARD,
        {
            "total": 300,
            "improved": 300,
            "optimal": 300,
            "worsened": 0,
            "no_move": 0,
            "playouts": {"mate": 300},
            "conversion_status_counts": {"passed": 300},
            "one_ply_status_counts": {"passed": 300},
            "shadow_candidates": [],
            "composition_profile": validation_profile,
        },
    )
    stage4_caveat_payload = {
        "total": 300,
        "improved": 300,
        "optimal": 300,
        "worsened": 0,
        "no_move": 0,
        "playouts": {"mate": 247, "max_plies": 53},
        "conversion_status_counts": {"passed": 247, "failed": 53},
        "one_ply_status_counts": {"passed": 300},
        "shadow_candidates": [{}] * 106,
        "composition_profile": validation_profile,
    }
    write_json(_protected_stage_status.STAGE4_OVERLAY_PROBE, stage4_caveat_payload)
    write_json(_protected_stage_status.STAGE4_BASE_CONTROL, stage4_caveat_payload)
    write_json(
        _protected_stage_status.STAGE6_PROMOTION,
        {
            "promotion_status": "promoted",
            "stage": {"mate_rate": 1.0, "passed": True},
            "guardrails": [{"label": "fence_established", "mate_rate": 1.0, "passed": True}],
        },
    )
    notes = root / _protected_stage_status.HANDOFF_NOTES
    notes.parent.mkdir(parents=True, exist_ok=True)
    notes.write_text(
        "Stage 1 regression:\n\n"
        "```text\n"
        "samples: 500\n"
        "result: 500/500 improved, 500/500 optimal, 0 worsened, 0 no-move\n"
        "```\n",
        encoding="utf-8",
    )

    status = _protected_stage_status.build_status(root)

    assert status["schema_version"] == "krk_protected_stage_status.v1"
    assert status["causal_status"] == "non_causal_status_audit"
    assert status["runtime_behavior_changed"] is False
    assert status["runtime_defaults_changed"] is False
    assert status["stage7_promotion_allowed"] is False
    assert status["stage8_training_allowed"] is False

    stages = {item["stage"]: item for item in status["stage_statuses"]}
    assert stages["stage1_backchain"]["evidence"]["documented_500_sample_regression"] is True
    assert stages["stage5_fence"]["evidence"]["profile_1000_seed7_h40"]["playouts"] == {
        "mate": 1000
    }
    assert (
        stages["stage6_drive_overlay"]["evidence"]["promotion_eval"]["promotion_status"]
        == "promoted"
    )
    assert stages["stage4_wrong_tempo"]["evidence"][
        "overlay_caveat_reproduces_on_base_control"
    ] is True
    assert stages["stage4_wrong_tempo"]["evidence"]["overlay_probe_300_seed7_h40"][
        "playouts"
    ] == {"mate": 247, "max_plies": 53}


def test_krk_protected_stage_status_uses_active_retry1_manifest(tmp_path):
    root = tmp_path

    def write_json(relative_path, payload):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    validation_profile = {
        "schema_version": "composition_profile.v1",
        "profile_id": "handoff_composition_v1",
    }
    write_json(
        _protected_stage_status.STAGE1_MANIFEST,
        {
            "formal_validation": {
                "mode": "strict_pairs",
                "validated": True,
                "nodes": 257,
                "edges": 796,
            }
        },
    )
    write_json(
        _protected_stage_status.STAGE4_PROFILE,
        {
            "total": 500,
            "playouts": {"mate": 500},
            "shadow_candidates": [],
            "composition_profile": validation_profile,
        },
    )
    write_json(
        _protected_stage_status.STAGE5_PROFILE,
        {
            "total": 1000,
            "playouts": {"mate": 1000},
            "shadow_candidates": [],
            "composition_profile": validation_profile,
        },
    )
    retry_root = Path("snapshots/retry1")
    stage6_validation = retry_root / "stage6.json"
    stage5_guardrail = retry_root / "stage5_guardrail.json"
    stage4_overlay = retry_root / "stage4_overlay.json"
    stage4_base = retry_root / "stage4_base.json"
    promotion_eval = retry_root / "promotion.json"
    stage6_payload = {
        "total": 300,
        "improved": 300,
        "optimal": 217,
        "worsened": 0,
        "playouts": {"mate": 300},
        "shadow_candidates": [],
        "composition_profile": validation_profile,
    }
    stage5_payload = {
        "total": 300,
        "improved": 144,
        "optimal": 144,
        "worsened": 156,
        "playouts": {"mate": 300},
        "shadow_candidates": [],
        "composition_profile": validation_profile,
    }
    stage4_payload = {
        "total": 300,
        "improved": 238,
        "optimal": 238,
        "worsened": 62,
        "playouts": {"mate": 268, "max_plies": 32},
        "shadow_candidates": [],
        "composition_profile": validation_profile,
    }
    write_json(stage6_validation, stage6_payload)
    write_json(stage5_guardrail, stage5_payload)
    write_json(stage4_overlay, stage4_payload)
    write_json(stage4_base, stage4_payload)
    write_json(
        promotion_eval,
        {
            "promotion_status": "overlay_only",
            "promotion_status_semantics": "overlay_only_due_to_guardrail_control_debt",
            "stage": {"passed": True, "mate_rate": 1.0},
            "guardrail_semantics": {
                "conversion_preservation": [{"passed": True}],
                "local_reward_contract_debt": [{"status": "control_debt"}],
            },
            "guardrails": [],
        },
    )
    write_json(
        _protected_stage_status.RETRY1_STAGE4_REVIEW,
        {"source_artifacts": {"stage4_overlay": str(stage4_overlay)}},
    )
    write_json(
        _protected_stage_status.ACTIVE_STACK,
        {
            "status": "retry1_protected_stage5_6_stack_adopted_manifest_only",
            "active_protected_stack": {
                "stage6_drive_overlay": {
                    "stage6_validation": str(stage6_validation),
                    "stage5_guardrail": str(stage5_guardrail),
                    "stage4_caveat_control": str(stage4_base),
                    "promotion_eval": str(promotion_eval),
                }
            },
        },
    )

    status = _protected_stage_status.build_status(root)

    assert status["protected_stack_reference_mode"] == "retry1_manifest_active"
    assert status["active_stack_status"] == "retry1_protected_stage5_6_stack_adopted_manifest_only"
    stages = {item["stage"]: item for item in status["stage_statuses"]}
    assert stages["stage6_drive_overlay"]["status"] == (
        "active_retry1_overlay_solved_with_guardrail_control_debt"
    )
    assert stages["stage6_drive_overlay"]["evidence"]["promotion_eval"][
        "promotion_status_semantics"
    ] == "overlay_only_due_to_guardrail_control_debt"
    assert stages["stage4_wrong_tempo"]["evidence"]["overlay_probe_300_seed7_h40"][
        "playouts"
    ] == {"mate": 268, "max_plies": 32}


def test_krk_self_expansion_architecture_gate_selects_non_causal_contract(tmp_path):
    root = tmp_path

    def write_json(relative_path, payload):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    non_causal_flags = {
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
    }
    write_json(
        _self_expansion_gate.PROTECTED_STAGE_STATUS,
        {
            "causal_status": "non_causal_status_audit",
            **non_causal_flags,
            "stage7_status": "local_valid_composition_quarantined",
            "summary": {
                "current_architecture_profile": "handoff_composition_v1",
                "yes_protected_or_promoted": [
                    "stage1_backchain",
                    "stage4_wrong_tempo",
                    "stage5_fence",
                    "stage6_drive_overlay",
                ],
                "cleanest_solved_components": [
                    "stage1_backchain",
                    "stage5_fence",
                    "stage6_drive_overlay",
                ],
                "solved_with_caveat": ["stage4_wrong_tempo"],
                "stage6_overlay_status": "promoted",
            },
        },
    )
    write_json(
        _self_expansion_gate.STRATEGY_ARBITRATION_GATE,
        {
            "causal_status": "non_causal_decision_gate",
            **non_causal_flags,
            "selected_status": "missing_feature_first",
            "missing_evidence": ["more stratified records"],
        },
    )
    write_json(
        _self_expansion_gate.INTERNAL_TERMINAL_REVIEW,
        {
            "causal_status": "non_causal_design_review",
            **non_causal_flags,
            "summary": {
                "main_conclusion": "Internal terminals are useful monitor/evidence objects.",
                "causal_ready_terminals": [],
            },
            "answers": {"safest_next_evidence_step": "broader replay-free evidence"},
        },
    )
    write_json(
        _self_expansion_gate.TRAINING_OBJECTIVE_GATE,
        {
            "causal_status": "non_causal_decision_gate",
            **non_causal_flags,
            "selected_outcome": "model_expression_gap_persists_stage7_micro_work_stops",
        },
    )
    write_json(
        _self_expansion_gate.SEQUENCE_POLICY_NOTE,
        {
            "causal_status": "non_causal_design_note",
            **non_causal_flags,
            "minimum_future_data_requirements": ["family held-out trajectories"],
        },
    )
    brief = root / _self_expansion_gate.CURRENT_BRIEF
    brief.parent.mkdir(parents=True, exist_ok=True)
    brief.write_text("# brief\n", encoding="utf-8")

    gate = _self_expansion_gate.build_gate(root)

    assert gate["schema_version"] == "krk_self_expansion_architecture_gate.v0"
    assert gate["causal_status"] == "non_causal_architecture_review"
    assert gate["runtime_behavior_changed"] is False
    assert gate["runtime_arbiter_added"] is False
    assert gate["runtime_terminals_added"] is False
    assert gate["stage7_promotion_allowed"] is False
    assert gate["stage8_training_allowed"] is False
    assert gate["selected_next_architecture_goal"]["goal_id"] == (
        "krk_control_plane_evidence_contract_v0"
    )
    assert gate["selected_next_architecture_goal"]["must_remain_non_causal"] is True
    assert "stage7_runtime_repair" in gate["forbidden_next_steps"]
    assert "control_plane_schema_design_v0" in {
        item["slice_id"] for item in gate["allowed_next_slices"]
    }


def test_krk_control_plane_contract_is_non_causal_schema(tmp_path):
    root = tmp_path
    report_path = root / _control_plane_contract.ARCHITECTURE_GATE
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "causal_status": "non_causal_architecture_review",
                "runtime_behavior_changed": False,
                "runtime_defaults_changed": False,
                "runtime_dtm_or_tablebase_lookup": False,
                "gameplay_topology_mutation": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
                "selected_next_architecture_goal": {
                    "goal_id": "krk_control_plane_evidence_contract_v0"
                },
                "forbidden_next_steps": ["stage7_runtime_repair", "runtime_arbiter"],
            }
        ),
        encoding="utf-8",
    )

    contract = _control_plane_contract.build_contract(root)

    assert contract["schema_version"] == "krk_control_plane_evidence_contract.v0"
    assert contract["causal_status"] == "non_causal_schema_contract"
    assert contract["runtime_behavior_changed"] is False
    assert contract["runtime_arbiter_added"] is False
    assert contract["runtime_terminals_added"] is False
    assert contract["stage7_promotion_allowed"] is False
    assert contract["stage8_training_allowed"] is False
    assert contract["primary_frame"]["schema_version"] == "control_plane_evidence_frame.v1"
    assert "runtime_move_override" in contract["primary_frame"]["forbidden_fields"]
    assert "runtime_move_selector" in contract["forbidden_consumers"]
    assert "offline_sequence_policy_benchmark" in contract["allowed_consumers"]
    assert contract["first_manifest_scope"]["records_from_existing_artifacts_only"] is True
    assert contract["first_manifest_scope"]["new_playouts_allowed"] is False
    assert contract["recommended_next_slice"] == (
        "control_plane_manifest_from_existing_artifacts_v0"
    )

    subschemas = {item["name"] for item in contract["subschemas"]}
    assert {
        "ProtectedProviderProvenance",
        "StrategyProposalFrame",
        "InternalMonitorEvidence",
        "PlanCapsuleWindowEvidence",
        "SequenceTrainingExample",
        "GuardrailResultSummary",
        "GrowthGovernorStatus",
        "PromotionGateStatus",
    } == subschemas


def test_krk_control_plane_manifest_maps_existing_artifacts_without_playouts(tmp_path):
    root = tmp_path

    def write_json(relative_path, payload):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def write_text(relative_path, text):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    write_json(
        _control_plane_manifest.CONTRACT,
        {
            "causal_status": "non_causal_schema_contract",
            "primary_frame": {
                "required_fields": [
                    "frame_id",
                    "domain",
                    "state_id",
                    "fen",
                    "source_stage",
                    "active_landmark_label",
                    "protected_provider_provenance",
                    "strategy_proposal_frames",
                    "internal_monitor_records",
                    "plan_capsule_window_records",
                    "sequence_training_examples",
                    "outcome_labels",
                    "guardrail_result_summaries",
                    "growth_governor_status",
                    "promotion_gate_status",
                    "source_artifacts",
                    "causal_status",
                ]
            },
            "blocked_next_steps": ["stage7_runtime_repair"],
        },
    )
    write_json(
        _control_plane_manifest.PROTECTED_STATUS,
        {
            "stage7_status": "local_valid_composition_quarantined",
            "summary": {
                "yes_protected_or_promoted": ["stage1_backchain", "stage5_fence"],
                "cleanest_solved_components": ["stage1_backchain", "stage5_fence"],
                "solved_with_caveat": ["stage4_wrong_tempo"],
            },
        },
    )
    write_text(_control_plane_manifest.STAGE6_MANIFEST, "# manifest\n")
    write_json(
        _control_plane_manifest.STRATEGY_DATASET,
        {
            "summary": {
                "record_count": 2,
                "proposal_count": 3,
                "records_by_source_stage": {"stage5": 1, "stage7": 1},
            }
        },
    )
    write_json(
        _control_plane_manifest.MONITOR_RECORDS,
        {"summary": {"monitor_record_count": 4}},
    )
    write_json(
        _control_plane_manifest.INTERNAL_TERMINAL_EVIDENCE,
        {
            "summary": {
                "terminal_count": 2,
                "causal_ready_terminals": [],
                "strongest_internal_terminal_candidates": [
                    "terminal.krk.local_provider_competition_failed"
                ],
            }
        },
    )
    write_json(_control_plane_manifest.PLAN_WINDOW, {"windows": [{}, {}]})
    write_json(_control_plane_manifest.PLAN_AUDIT, {"schema_version": "audit.v1"})
    write_json(_control_plane_manifest.DTM_TRAJECTORY_SEED, {"trajectories": [{}, {}]})
    write_text(_control_plane_manifest.DTM_TRAJECTORY_SEED_JSONL, "{}\n{}\n")
    write_json(_control_plane_manifest.DTM_TRAJECTORY_EXPANDED, {"trajectories": [{}]})
    write_text(_control_plane_manifest.DTM_TRAJECTORY_EXPANDED_JSONL, "{}\n")
    write_json(
        _control_plane_manifest.TRAINING_OBJECTIVE_BENCHMARK,
        {"final_decision": "model_expression_gap_persists"},
    )
    write_json(
        _control_plane_manifest.TRAINING_OBJECTIVE_GATE,
        {"selected_outcome": "model_expression_gap_persists_stage7_micro_work_stops"},
    )
    write_json(_control_plane_manifest.GROWTH_GOVERNOR_PLAN, {"schema_version": "plan.v1"})
    write_json(_control_plane_manifest.STAGE6_PROMOTION, {"promotion_status": "promoted"})
    write_json(_control_plane_manifest.STAGE7_CLOSURE, {"decision": "stopped"})

    manifest = _control_plane_manifest.build_manifest(root)

    assert manifest["schema_version"] == "krk_control_plane_manifest.v0"
    assert manifest["causal_status"] == "non_causal_manifest"
    assert manifest["runtime_behavior_changed"] is False
    assert manifest["runtime_arbiter_added"] is False
    assert manifest["runtime_terminals_added"] is False
    assert manifest["stage7_promotion_allowed"] is False
    assert manifest["stage8_training_allowed"] is False
    assert manifest["summary"]["new_playouts_added"] == 0
    assert manifest["summary"]["records_from_existing_artifacts_only"] is True
    assert manifest["summary"]["strategy_record_count"] == 2
    assert manifest["summary"]["strategy_proposal_count"] == 3
    assert manifest["summary"]["monitor_record_count"] == 4
    assert manifest["summary"]["sequence_seed_step_count"] == 2
    assert manifest["summary"]["sequence_expanded_step_count"] == 1
    assert "strategy_proposal_frames" in manifest["summary"]["covered_contract_fields"]
    assert "internal_monitor_records" in manifest["summary"]["covered_contract_fields"]
    assert "unified_frame_export_missing" in {gap["gap_id"] for gap in manifest["gaps"]}


def test_krk_control_plane_gap_report_recommends_replay_free_frame_export(tmp_path):
    root = tmp_path
    manifest_path = root / _control_plane_gap.MANIFEST
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "causal_status": "non_causal_manifest",
                "runtime_behavior_changed": False,
                "runtime_defaults_changed": False,
                "runtime_dtm_or_tablebase_lookup": False,
                "gameplay_topology_mutation": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
                "summary": {
                    "strategy_record_count": 2,
                    "strategy_proposal_count": 3,
                    "monitor_record_count": 4,
                    "plan_window_count": 1,
                    "sequence_seed_step_count": 2,
                    "sequence_expanded_step_count": 5,
                    "new_playouts_added": 0,
                },
                "field_coverage": [
                    {
                        "field": "strategy_proposal_frames",
                        "summary": {"records_by_source_stage": {"stage5": 1, "stage7": 1}},
                    }
                ],
                "blocked_next_steps": ["stage7_runtime_repair", "runtime_arbiter"],
            }
        ),
        encoding="utf-8",
    )

    report = _control_plane_gap.build_gap_report(root)

    assert report["schema_version"] == "krk_control_plane_gap_report.v0"
    assert report["causal_status"] == "non_causal_gap_report"
    assert report["runtime_behavior_changed"] is False
    assert report["runtime_arbiter_added"] is False
    assert report["runtime_terminals_added"] is False
    assert report["stage7_promotion_allowed"] is False
    assert report["stage8_training_allowed"] is False
    assert report["recommended_next_slice"]["slice_id"] == (
        "export_replay_free_control_plane_frames_v0"
    )
    assert report["recommended_next_slice"]["causal"] is False
    assert report["recommended_next_slice"]["new_playouts_allowed"] is False
    assert "no_unified_control_plane_frames" in {
        gap["gap_id"] for gap in report["stratified_gaps"]
    }
    assert "stage8_training" in report["deferred_until_after_frame_export"]


def test_krk_control_plane_frame_export_is_replay_free_and_non_causal(tmp_path):
    root = tmp_path

    def write_json(relative_path, payload):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def write_text(relative_path, text):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    write_json(_control_plane_frames.CONTRACT, {"causal_status": "non_causal_schema_contract"})
    write_json(
        _control_plane_frames.GAP_REPORT,
        {"recommended_next_slice": {"slice_id": "export_replay_free_control_plane_frames_v0"}},
    )
    write_json(
        _control_plane_frames.PROTECTED_STATUS,
        {
            "stage_statuses": [
                {
                    "stage": "stage5_fence",
                    "evidence": {
                        "profile": {
                            "total": 1,
                            "playouts": {"mate": 1},
                            "shadow_candidate_count": 0,
                        }
                    },
                }
            ]
        },
    )
    write_json(
        _control_plane_frames.STRATEGY_DATASET,
        {
            "records": [
                {
                    "state_id": "state.test",
                    "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                    "source_stage": "stage7",
                    "active_landmark_label": "box_shrink",
                    "strategy_proposals": [
                        {
                            "provider_id": "krk.box_shrink",
                            "move_uci": "a1a2",
                            "raw_score": 1.0,
                            "provider_local_rank": 1,
                        }
                    ],
                    "result_label": {"current_graph_h40": "max_plies"},
                    "hypothesis_labels": ["training_objective_model_expression_candidate"],
                    "source_artifacts": ["fixture.json"],
                }
            ]
        },
    )
    write_json(
        _control_plane_frames.MONITOR_RECORDS,
        {
            "records": [
                {
                    "state_id": "state.test",
                    "monitor_id": "monitor.test",
                    "monitor_type": "PlanSelectionNeededMonitor",
                    "source_terms": ["local_provider_competition_failed"],
                    "missing_terms": [],
                    "confidence": 1.0,
                    "associated_outcome": "max_plies",
                    "promotion_status": "proposed",
                }
            ]
        },
    )
    write_json(
        _control_plane_frames.PLAN_WINDOWS,
        {
            "windows": [
                {
                    "start_fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                    "ttl_white_moves": 3,
                    "owned_white_move_count": 3,
                    "entry_confirmed": True,
                    "progress_terms": ["box_area_preserved"],
                    "result": "max_plies",
                }
            ]
        },
    )
    write_text(
        _control_plane_frames.DTM_SEED_JSONL,
        json.dumps(
            {
                "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                "ply_index": 0,
                "target_skill": "krk.post_box_shrink_continuation",
                "legal_move_labels": [
                    {"move": "a1a2", "label": 1, "target_class": "optimal_dtm_move"},
                    {"move": "a1a3", "label": 0, "target_class": "winning_nonoptimal_move"},
                ],
            }
        )
        + "\n",
    )
    write_text(_control_plane_frames.DTM_EXPANDED_JSONL, "")
    write_json(_control_plane_frames.STAGE6_PROMOTION, {"promotion_status": "promoted"})
    write_json(
        _control_plane_frames.STAGE7_CLOSURE,
        {"decision": {"benchmark_status": "model_expression_gap_persists"}},
    )

    export = _control_plane_frames.build_frames(root)

    assert export["schema_version"] == "krk_control_plane_frames_export.v0"
    assert export["causal_status"] == "non_causal_frame_export"
    assert export["runtime_behavior_changed"] is False
    assert export["runtime_arbiter_added"] is False
    assert export["runtime_terminals_added"] is False
    assert export["stage7_promotion_allowed"] is False
    assert export["stage8_training_allowed"] is False
    assert export["summary"]["frame_count"] == 1
    assert export["summary"]["strategy_proposal_frame_count"] == 1
    assert export["summary"]["internal_monitor_record_count"] == 1
    assert export["summary"]["plan_capsule_window_record_count"] == 1
    assert export["summary"]["sequence_training_example_count"] == 1
    assert export["summary"]["new_playouts_added"] == 0

    frame = export["frames"][0]
    assert frame["causal_status"] == "non_causal"
    assert frame["promotion_gate_status"]["promotion_status"] == "quarantined"
    assert frame["strategy_proposal_frames"][0]["causal_status"] == "non_causal"
    assert frame["internal_monitor_records"][0]["causal_ready"] is False
    assert frame["sequence_training_examples"][0]["offline_only"] is True


def test_krk_control_plane_frame_quality_blocks_runtime_and_recommends_filters(tmp_path):
    root = tmp_path
    frames_path = root / _control_plane_quality.FRAMES
    frames_path.parent.mkdir(parents=True, exist_ok=True)
    frames_path.write_text(
        json.dumps(
            {
                "causal_status": "non_causal_frame_export",
                "frames": [
                    {
                        "frame_id": "cp.a",
                        "source_stage": "stage7",
                        "outcome_labels": {"result_label": {"current_graph_h40": "max_plies"}},
                        "strategy_proposal_frames": [],
                        "internal_monitor_records": [
                            {"monitor_id": "m1"},
                            {"monitor_id": "m1"},
                        ],
                        "plan_capsule_window_records": [
                            {
                                "progress_terms_confirmed": ["p"],
                                "window_outcome": "max_plies",
                            }
                        ],
                        "sequence_training_examples": [{"offline_only": True}],
                    },
                    {
                        "frame_id": "cp.b",
                        "source_stage": "stage5",
                        "outcome_labels": {"result_label": {"current_graph_h40": "mate"}},
                        "strategy_proposal_frames": [{"move_uci": "a1a2"}],
                        "internal_monitor_records": [],
                        "plan_capsule_window_records": [],
                        "sequence_training_examples": [],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    report = _control_plane_quality.build_quality_report(root)

    assert report["schema_version"] == "krk_control_plane_frame_quality_report.v0"
    assert report["causal_status"] == "non_causal_quality_report"
    assert report["runtime_behavior_changed"] is False
    assert report["runtime_arbiter_added"] is False
    assert report["runtime_terminals_added"] is False
    assert report["stage7_promotion_allowed"] is False
    assert report["stage8_training_allowed"] is False
    assert report["readiness"]["runtime_sandbox"] == "blocked"
    assert report["readiness"]["stage8_training"] == "blocked"
    assert report["recommended_next_slice"]["slice_id"] == (
        "control_plane_frame_dedupe_and_quality_filters_v0"
    )
    assert report["recommended_next_slice"]["causal"] is False
    assert any(
        flag["flag_id"] == "some_frames_lack_strategy_proposals" and flag["count"] == 1
        for flag in report["quality_flags"]
    )


def test_krk_control_plane_filter_marks_strategy_ready_and_dedupes(tmp_path):
    root = tmp_path

    def write_json(relative_path, payload):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    write_json(
        _control_plane_filter.FRAMES,
        {
            "causal_status": "non_causal_frame_export",
            "frames": [
                {
                    "frame_id": "cp.a",
                    "state_id": "state.a",
                    "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                    "source_stage": "stage5",
                    "active_landmark_label": "fence_established",
                    "outcome_labels": {"result_label": {"current_graph_h40": "mate"}},
                    "strategy_proposal_frames": [{"move_uci": "a1a2"}],
                    "internal_monitor_records": [
                        {"monitor_id": "m1", "terminal_id": "t", "monitor_type": "T"},
                        {"monitor_id": "m1", "terminal_id": "t", "monitor_type": "T"},
                    ],
                    "plan_capsule_window_records": [
                        {
                            "plan_id": "p",
                            "progress_terms_confirmed": ["x"],
                            "window_outcome": "mate",
                            "ttl_white_moves": 3,
                            "owned_white_move_count": 3,
                        },
                        {
                            "plan_id": "p",
                            "progress_terms_confirmed": ["x"],
                            "window_outcome": "mate",
                            "ttl_white_moves": 3,
                            "owned_white_move_count": 3,
                        },
                    ],
                    "sequence_training_examples": [],
                    "protected_provider_provenance": [],
                    "growth_governor_status": {},
                    "promotion_gate_status": {},
                },
                {
                    "frame_id": "cp.b",
                    "state_id": "state.b",
                    "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                    "source_stage": "stage7",
                    "active_landmark_label": "box_shrink",
                    "outcome_labels": {"result_label": {"current_graph_h40": "max_plies"}},
                    "strategy_proposal_frames": [{"move_uci": "a1a2"}],
                    "internal_monitor_records": [],
                    "plan_capsule_window_records": [],
                    "sequence_training_examples": [{"offline_only": True}],
                    "protected_provider_provenance": [],
                    "growth_governor_status": {},
                    "promotion_gate_status": {},
                },
            ],
        },
    )
    write_json(_control_plane_filter.QUALITY, {"causal_status": "non_causal_quality_report"})

    result = _control_plane_filter.build_filtered_export(root)

    assert result["schema_version"] == "krk_control_plane_filtered_frames.v0"
    assert result["causal_status"] == "non_causal_filtered_frame_export"
    assert result["runtime_behavior_changed"] is False
    assert result["runtime_arbiter_added"] is False
    assert result["runtime_terminals_added"] is False
    assert result["stage7_promotion_allowed"] is False
    assert result["stage8_training_allowed"] is False
    assert result["summary"]["strategy_ready_frame_count"] == 1
    assert result["summary"]["stage7_boundary_heldout_frame_count"] == 1
    assert result["summary"]["context_only_frame_count"] == 0
    assert result["summary"]["dropped_duplicate_monitor_count"] == 1
    assert result["summary"]["dropped_duplicate_plan_window_count"] == 1
    assert result["summary"]["new_playouts_added"] == 0
    assert result["readiness"]["runtime_sandbox"] == "blocked"
    assert result["recommended_next_slice"] == "offline_strategy_arbitration_probe_filtered_v0"

    first = result["frames"][0]
    assert "strategy_arbitration_benchmark" in first["filter_metadata"]["benchmark_roles"]
    assert first["filter_metadata"]["causal_status"] == "non_causal"
    assert len(first["internal_monitor_records"]) == 1
    assert len(first["plan_capsule_window_records"]) == 1
    second = result["frames"][1]
    assert "stage7_boundary_heldout_challenge" in second["filter_metadata"]["benchmark_roles"]
    assert "strategy_arbitration_benchmark" not in second["filter_metadata"]["benchmark_roles"]


def test_krk_control_plane_strategy_probe_stays_non_causal_and_reports_label_gap(tmp_path):
    root = tmp_path
    filtered_path = root / _control_plane_strategy_probe.FILTERED_FRAMES
    filtered_path.parent.mkdir(parents=True, exist_ok=True)
    filtered_path.write_text(
        json.dumps(
            {
                "causal_status": "non_causal_filtered_frame_export",
                "frames": [
                    {
                        "frame_id": "cp.a",
                        "filter_metadata": {
                            "benchmark_roles": ["strategy_arbitration_benchmark"]
                        },
                        "strategy_proposal_frames": [
                            {
                                "provider_id": "krk.a",
                                "move_uci": "a1a2",
                                "raw_score": 2.0,
                                "normalized_score": 1.0,
                                "provider_local_rank": 1,
                                "known_outcome_label": {"playout_result": "mate"},
                            },
                            {
                                "provider_id": "krk.b",
                                "move_uci": "a1a3",
                                "raw_score": 3.0,
                                "normalized_score": 0.5,
                                "provider_local_rank": 2,
                                "known_outcome_label": {"result": "max_plies"},
                            },
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    probe = _control_plane_strategy_probe.build_probe(root)

    assert probe["schema_version"] == "krk_control_plane_strategy_arbitration_probe.v0"
    assert probe["causal_status"] == "non_causal_probe"
    assert probe["runtime_behavior_changed"] is False
    assert probe["runtime_arbiter_added"] is False
    assert probe["runtime_terminals_added"] is False
    assert probe["stage7_promotion_allowed"] is False
    assert probe["stage8_training_allowed"] is False
    assert probe["label_coverage"]["strategy_benchmark_frame_count"] == 1
    assert probe["label_coverage"]["provider_labeled_frame_count"] == 1
    assert probe["label_coverage"]["frames_with_known_provider_mate"] == 1
    assert probe["decision"]["selected_status"] == "provider_labels_underpowered"
    assert probe["decision"]["causal_next_step_allowed"] is False
    raw = next(item for item in probe["selector_results"] if item["selector"] == "raw_global_score")
    assert raw["selected_max_plies_count"] == 1
    normalized = next(
        item for item in probe["selector_results"] if item["selector"] == "normalized_score"
    )
    assert normalized["selected_mate_count"] == 1


def test_krk_provider_label_coverage_plan_is_bounded_and_non_causal(tmp_path):
    root = tmp_path

    def write_json(relative_path, payload):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    write_json(
        _provider_label_plan.FILTERED_FRAMES,
        {
            "causal_status": "non_causal_filtered_frame_export",
            "frames": [
                {
                    "frame_id": "cp.stage5",
                    "source_stage": "stage5",
                    "filter_metadata": {
                        "benchmark_roles": ["strategy_arbitration_benchmark"]
                    },
                    "strategy_proposal_frames": [
                        {
                            "provider_id": "krk.fence",
                            "move_uci": "a1a2",
                            "known_outcome_label": {"playout_result": "max_plies"},
                        }
                    ],
                },
                {
                    "frame_id": "cp.stage7",
                    "source_stage": "stage7",
                    "filter_metadata": {
                        "benchmark_roles": ["strategy_arbitration_benchmark"]
                    },
                    "strategy_proposal_frames": [
                        {
                            "provider_id": "krk.drive",
                            "move_uci": "a1a3",
                            "known_outcome_label": {"result": "mate"},
                        }
                    ],
                },
            ],
        },
    )
    write_json(
        _provider_label_plan.STRATEGY_PROBE,
        {
            "causal_status": "non_causal_probe",
            "label_coverage": {
                "provider_labeled_frame_count": 2,
                "frames_with_known_provider_mate": 1,
                "label_status": "provider_labels_sufficient_for_small_probe",
            },
        },
    )

    plan = _provider_label_plan.build_plan(root)

    assert plan["schema_version"] == "krk_provider_label_coverage_plan.v0"
    assert plan["causal_status"] == "non_causal_label_plan"
    assert plan["runtime_behavior_changed"] is False
    assert plan["labels_generated_in_this_slice"] is False
    assert plan["runtime_arbiter_added"] is False
    assert plan["stage7_promotion_allowed"] is False
    assert plan["stage8_training_allowed"] is False
    assert plan["current_label_coverage"]["unknown_provider_label_count_by_stage"] == {}
    assert plan["current_label_coverage"]["known_provider_label_count_by_stage"] == {
        "stage5": 1,
        "stage7": 1
    }
    assert plan["current_label_coverage"]["coverage_status"] == "sufficient_for_current_small_probe"
    assert plan["bounded_labeling_plan"][0]["phase"] == "p0_protected_success_controls"
    assert plan["bounded_labeling_plan"][0]["new_runtime_behavior"] is False
    assert plan["recommended_next_slice"] == "offline_strategy_arbitration_baseline_v1"


def test_krk_control_plane_strategy_baseline_is_non_causal_and_reads_labels(tmp_path):
    root = tmp_path
    filtered_path = root / _control_plane_strategy_baseline.FILTERED_FRAMES
    filtered_path.parent.mkdir(parents=True, exist_ok=True)
    filtered_path.write_text(
        json.dumps(
            {
                "causal_status": "non_causal_filtered_frame_export",
                "frames": [
                    {
                        "frame_id": "cp.test",
                        "state_id": "state.test",
                        "source_stage": "stage5",
                        "active_landmark_label": "fence_established",
                        "fen": "6k1/R7/8/8/8/8/5K2/8 w - - 2 2",
                        "outcome": "mate",
                        "filter_metadata": {
                            "benchmark_roles": ["strategy_arbitration_benchmark"]
                        },
                        "strategy_proposal_frames": [
                            {
                                "provider_id": "krk.stage0_basin",
                                "move_uci": "f2g3",
                                "raw_score": 1.0,
                                "normalized_score": 1.0,
                                "provider_local_rank": 1,
                                "known_outcome_label": {"playout_result": "mate"},
                            },
                            {
                                "provider_id": "krk.edge_trap_close",
                                "move_uci": "a7a8",
                                "raw_score": 2.0,
                                "normalized_score": 0.5,
                                "provider_local_rank": 2,
                                "known_outcome_label": {"result": "max_plies"},
                            },
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    baseline = _control_plane_strategy_baseline.build_baseline(root)

    assert baseline["schema_version"] == "krk_control_plane_strategy_arbitration_baseline.v1"
    assert baseline["causal_status"] == "non_causal_probe"
    assert baseline["runtime_behavior_changed"] is False
    assert baseline["runtime_arbiter_added"] is False
    assert baseline["runtime_terminals_added"] is False
    assert baseline["stage7_promotion_allowed"] is False
    assert baseline["stage8_training_allowed"] is False
    assert baseline["frame_summary"]["proposal_label_counts"] == {
        "mate": 1,
        "max_plies": 1,
    }
    raw = next(item for item in baseline["selector_results"] if item["selector"] == "raw_global_score")
    assert raw["selected_label_counts"]["max_plies"] == 1
    normalized = next(
        item for item in baseline["selector_results"] if item["selector"] == "normalized_score"
    )
    assert normalized["selected_label_counts"]["mate"] == 1
    assert baseline["decision"]["causal_next_step_allowed"] is False


def test_krk_control_plane_stage7_boundary_refresh_keeps_stage7_heldout(tmp_path, monkeypatch):
    root = tmp_path
    reports = root / "reports"
    structural = reports / "structural_candidates"
    structural.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    (structural / "stage7_curriculum_boundary_decision_v0.json").write_text(
        json.dumps(
            {
                "decision": {
                    "status": "box_shrink_reclassified_as_local_evidence_handoff_trigger"
                }
            }
        ),
        encoding="utf-8",
    )
    (reports / "krk_control_plane_filtered_frames_v0.json").write_text(
        json.dumps(
            {
                "summary": {
                    "strategy_ready_frame_count": 1,
                    "strategy_ready_by_stage": {"stage5": 1},
                    "stage7_boundary_heldout_frame_count": 1,
                    "benchmark_role_counts": {
                        "strategy_arbitration_benchmark": 1,
                        "stage7_boundary_heldout_challenge": 1,
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (reports / "krk_control_plane_strategy_arbitration_probe_v0.json").write_text(
        json.dumps(
            {
                "label_coverage": {
                    "strategy_benchmark_frame_count": 1,
                    "label_status": "provider_labels_underpowered",
                },
                "decision": {"selected_status": "provider_labels_underpowered"},
            }
        ),
        encoding="utf-8",
    )
    (reports / "krk_control_plane_strategy_arbitration_baseline_v1.json").write_text(
        json.dumps(
            {
                "frame_summary": {
                    "strategy_benchmark_frame_count": 1,
                    "stage_counts": {"stage5": 1},
                },
                "decision": {"selected_status": "inconclusive_need_more_stratified_data"},
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(_control_plane_stage7_boundary_refresh, "ROOT", root)
    review = _control_plane_stage7_boundary_refresh.build_review()

    assert review["schema_version"] == "krk_control_plane_stage7_boundary_refresh.v0"
    assert review["causal_status"] == "non_causal_artifact_review"
    assert review["runtime_behavior_changed"] is False
    assert review["runtime_selector_implemented"] is False
    assert review["stage7_promotion_allowed"] is False
    assert review["stage8_training_allowed"] is False
    assert review["decision"]["status"] == "control_plane_respects_stage7_boundary"
    assert (
        review["decision"]["recommended_next_step"]
        == "continue_broader_krk_strategy_sequence_work_with_stage7_heldout"
    )
    assert review["filtered_frame_summary"]["strategy_ready_by_stage"] == {"stage5": 1}
    assert review["filtered_frame_summary"]["stage7_boundary_heldout_frame_count"] == 1


def test_krk_protected_max_only_review_identifies_capacity_gap(tmp_path, monkeypatch):
    root = tmp_path
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "krk_control_plane_filtered_frames_v0.json").write_text(
        json.dumps(
            {
                "frames": [
                    {
                        "frame_id": "cp.mate",
                        "state_id": "state.mate",
                        "source_stage": "stage5",
                        "active_landmark_label": "fence_established",
                        "outcome": "mate",
                        "filter_metadata": {"benchmark_roles": ["strategy_arbitration_benchmark"]},
                        "strategy_proposal_frames": [
                            {"provider_id": "krk.edge_trap_close", "known_outcome_label": {"result": "mate"}}
                        ],
                    },
                    {
                        "frame_id": "cp.max",
                        "state_id": "state.max",
                        "source_stage": "stage6",
                        "active_landmark_label": "drive_to_edge",
                        "outcome": "max_plies",
                        "filter_metadata": {"benchmark_roles": ["strategy_arbitration_benchmark"]},
                        "strategy_proposal_frames": [
                            {
                                "provider_id": "krk.stage0_basin",
                                "known_outcome_label": {"result": "max_plies"},
                            }
                        ],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    (reports / "krk_control_plane_strategy_arbitration_baseline_v1.json").write_text(
        json.dumps({"decision": {"selected_status": "strategy_arbitration_promising"}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(_protected_max_only_review, "ROOT", root)

    review = _protected_max_only_review.build_review()

    assert review["schema_version"] == "krk_protected_max_only_frame_review.v0"
    assert review["causal_status"] == "non_causal_artifact_review"
    assert review["runtime_behavior_changed"] is False
    assert review["stage7_promotion_allowed"] is False
    assert review["stage8_training_allowed"] is False
    assert review["summary"]["frames_with_labeled_mate_provider"] == 1
    assert review["summary"]["frames_with_only_labeled_max_plies_providers"] == 1
    assert review["decision"]["status"] == "protected_max_only_frames_block_runtime_selector"


def test_krk_protected_missing_provider_capacity_plan_is_bounded(tmp_path, monkeypatch):
    root = tmp_path
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "krk_protected_max_only_frame_review_v0.json").write_text(
        json.dumps(
            {
                "max_only_frames": [
                    {
                        "frame_id": "cp.max",
                        "state_id": "state.max",
                        "source_stage": "stage6",
                        "active_landmark_label": "drive_to_edge",
                        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                        "max_only_provider_counts": {"krk.stage0_basin": 1},
                    },
                    {
                        "frame_id": "cp.max",
                        "state_id": "state.max",
                        "source_stage": "stage6",
                        "active_landmark_label": "drive_to_edge",
                        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                        "max_only_provider_counts": {"krk.stage0_basin": 1},
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(_protected_missing_provider_plan, "ROOT", root)

    plan = _protected_missing_provider_plan.build_plan()

    assert plan["schema_version"] == "krk_protected_missing_provider_capacity_audit_plan.v0"
    assert plan["causal_status"] == "non_causal_label_plan"
    assert plan["runtime_behavior_changed"] is False
    assert plan["runtime_selector_implemented"] is False
    assert plan["stage7_promotion_allowed"] is False
    assert plan["stage8_training_allowed"] is False
    assert plan["label_budget"]["stage7_jobs"] == 0
    assert plan["summary"]["job_count"] == 3
    assert plan["decision"]["status"] == "protected_missing_provider_capacity_audit_plan_ready"
    assert len({job["job_id"] for job in plan["jobs"]}) == len(plan["jobs"])


def test_krk_protected_missing_provider_capacity_manifest_review_allows_labels(tmp_path, monkeypatch):
    root = tmp_path
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    topology = root / _protected_missing_provider_manifest.TOPOLOGY
    topology.parent.mkdir(parents=True, exist_ok=True)
    topology.write_text(json.dumps({"nodes": {"x": {"meta": {"skill": "krk.drive_to_edge"}}}}), encoding="utf-8")
    (reports / "krk_protected_missing_provider_capacity_audit_plan_v0.json").write_text(
        json.dumps(
            {
                "jobs": [
                    {
                        "job_id": "job.a",
                        "frame_id": "cp.a",
                        "state_id": "state.a",
                        "source_stage": "stage6",
                        "active_landmark_label": "drive_to_edge",
                        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                        "provider_id": "krk.drive_to_edge",
                        "horizon": 40,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(_protected_missing_provider_manifest, "ROOT", root)
    manifest = _protected_missing_provider_manifest.build_manifest()
    (reports / "krk_protected_missing_provider_capacity_execution_manifest_v0.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )
    monkeypatch.setattr(_protected_missing_provider_manifest_review, "ROOT", root)

    review = _protected_missing_provider_manifest_review.build_review()

    assert manifest["schema_version"] == "krk_protected_missing_provider_capacity_execution_manifest.v0"
    assert manifest["causal_status"] == "non_causal_execution_manifest"
    assert manifest["binding_summary"]["all_bindings_valid"] is True
    assert manifest["decision"]["labels_allowed_now"] is False
    assert review["schema_version"] == "krk_protected_missing_provider_capacity_execution_manifest_review.v0"
    assert review["causal_status"] == "non_causal_manifest_review"
    assert review["runtime_behavior_changed"] is False
    assert review["stage7_promotion_allowed"] is False
    assert review["stage8_training_allowed"] is False
    assert review["review_summary"]["violation_count"] == 0
    assert review["decision"]["labels_allowed"] is True
    assert review["decision"]["runtime_work_allowed"] is False


def test_krk_protected_missing_provider_capacity_labels_are_non_causal(tmp_path, monkeypatch):
    root = tmp_path
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "krk_protected_missing_provider_capacity_execution_manifest_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_execution_manifest",
                "binding_summary": {"all_bindings_valid": True},
                "jobs": [
                    {
                        "job_id": "job.stage6",
                        "frame_id": "cp.stage6",
                        "state_id": "state.stage6",
                        "source_stage": "stage6",
                        "active_landmark_label": "drive_to_edge",
                        "provider_id": "krk.drive_to_edge",
                        "stage7_training_row": False,
                        "execution_binding": {"provider_version": "stage6_overlay_v1"},
                    },
                    {
                        "job_id": "job.stage4",
                        "frame_id": "cp.stage4",
                        "state_id": "state.stage4",
                        "source_stage": "stage4",
                        "active_landmark_label": "wrong_tempo_control",
                        "provider_id": "krk.edge_trap_wrong_tempo",
                        "stage7_training_row": False,
                        "execution_binding": {"provider_version": "stage5_validated_v1"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (reports / "krk_protected_missing_provider_capacity_execution_manifest_review_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_manifest_review",
                "decision": {"labels_allowed": True},
            }
        ),
        encoding="utf-8",
    )

    def fake_run_job(repo_root, job, cache):
        return {
            "schema_version": "krk_forced_provider_control_label.v0",
            "causal_status": "non_causal_outcome_label",
            "job_id": job["job_id"],
            "source_stage": job["source_stage"],
            "provider_id": job["provider_id"],
            "forced_first_move": "a1a2",
            "result": "max_plies",
            "plies": 40,
            "trace": [{"fen": "start"}, {"fen": "end"}],
            "stagnation_summary": {"no_progress_plies": 4},
        }

    monkeypatch.setattr(_protected_missing_provider_label_run, "ROOT", root)
    monkeypatch.setattr(_protected_missing_provider_label_run.forced_labels, "_run_job", fake_run_job)

    payload = _protected_missing_provider_label_run.run_labels()

    assert payload["schema_version"] == "krk_protected_missing_provider_capacity_labels.v0"
    assert payload["causal_status"] == "non_causal_label_run"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_terminals_added"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["label_count"] == 2
    assert payload["summary"]["stage7_labels"] == 0
    assert payload["summary"]["stage7_training_labels"] == 0
    label = payload["labels"][0]
    assert label["label_channel"] == "protected_missing_provider_capacity"
    assert label["full_trace_elided"] is True
    assert "trace" not in label
    assert label["provider_version"] == "stage6_overlay_v1"
    assert payload["labels"][1]["source_active_landmark_label"] == "wrong_tempo_control"
    assert payload["labels"][1]["execution_landmark_label"] == "edge_trap_wrong_tempo"
    assert payload["decision"]["runtime_work_allowed"] is False


def test_krk_strategy_arbiter_risk_review_separates_label_semantics(tmp_path):
    root = tmp_path

    def write_json(relative_path, payload):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    write_json(
        _strategy_arbiter_risk_review.FILTERED_FRAMES,
        {
            "causal_status": "non_causal_filtered_frame_export",
            "frames": [
                {
                    "frame_id": "cp.forced",
                    "state_id": "state.forced",
                    "source_stage": "stage7",
                    "active_landmark_label": "box_shrink",
                    "outcome": "max_plies",
                    "filter_metadata": {
                        "benchmark_roles": ["strategy_arbitration_benchmark"]
                    },
                    "strategy_proposal_frames": [
                        {
                            "provider_id": "krk.drive_to_edge",
                            "known_outcome_label": {
                                "result": "mate",
                                "source": "forced_provider_result",
                            },
                        },
                    ],
                },
                {
                    "frame_id": "cp.selected",
                    "state_id": "state.selected",
                    "source_stage": "stage5",
                    "active_landmark_label": "fence_established",
                    "outcome": "max_plies",
                    "filter_metadata": {
                        "benchmark_roles": ["strategy_arbitration_benchmark"]
                    },
                    "strategy_proposal_frames": [
                        {
                            "provider_id": "krk.edge_trap_close",
                            "known_outcome_label": {
                                "playout_result": "max_plies",
                                "selected": True,
                            },
                        },
                        {
                            "provider_id": "krk.edge_trap_enemy_between",
                            "known_outcome_label": {
                                "playout_result": "max_plies",
                                "selected": False,
                            },
                        },
                    ],
                },
            ],
        },
    )
    write_json(
        _strategy_arbiter_risk_review.BASELINE,
        {"causal_status": "non_causal_probe"},
    )
    write_json(
        _strategy_arbiter_risk_review.DESIGN,
        {"causal_status": "non_causal_design"},
    )

    review = _strategy_arbiter_risk_review.build_review(root)

    assert review["schema_version"] == "krk_strategy_arbiter_evidence_risk_review.v0"
    assert review["causal_status"] == "non_causal_review"
    assert review["runtime_behavior_changed"] is False
    assert review["runtime_arbiter_implemented"] is False
    assert review["stage7_promotion_allowed"] is False
    assert review["stage8_training_allowed"] is False
    assert review["summary"]["label_semantic_counts"] == {
        "forced_provider_outcome": 1,
        "selected_provider_playout": 1,
        "same_move_unselected_provider_playout": 1,
    }
    assert review["summary"]["max_only_classification_counts"] == {
        "selected_playout_guardrail_or_horizon_caveat": 1
    }
    assert review["decision"]["runtime_sandbox_allowed"] is False


def test_krk_strategy_arbiter_stratified_probe_blocks_runtime_sandbox(tmp_path):
    root = tmp_path

    def write_json(relative_path, payload):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    write_json(
        _strategy_arbiter_stratified.FILTERED_FRAMES,
        {
            "causal_status": "non_causal_filtered_frame_export",
            "frames": [
                {
                    "frame_id": "cp.selected",
                    "source_stage": "stage5",
                    "active_landmark_label": "fence_established",
                    "filter_metadata": {
                        "benchmark_roles": ["strategy_arbitration_benchmark"]
                    },
                    "strategy_proposal_frames": [
                        {
                            "provider_id": "krk.stage0_basin",
                            "normalized_score": 1.0,
                            "provider_local_rank": 1,
                            "known_outcome_label": {
                                "playout_result": "mate",
                                "selected": True,
                            },
                        }
                    ],
                },
                {
                    "frame_id": "cp.forced",
                    "source_stage": "stage7",
                    "active_landmark_label": "box_shrink",
                    "filter_metadata": {
                        "benchmark_roles": ["strategy_arbitration_benchmark"]
                    },
                    "strategy_proposal_frames": [
                        {
                            "provider_id": "krk.drive_to_edge",
                            "normalized_score": 1.0,
                            "provider_local_rank": 1,
                            "known_outcome_label": {
                                "result": "max_plies",
                                "source": "forced_provider_result",
                            },
                        },
                        {
                            "provider_id": "krk.fence_established",
                            "normalized_score": 0.5,
                            "provider_local_rank": 2,
                            "known_outcome_label": {
                                "result": "mate",
                                "source": "forced_provider_result",
                            },
                        },
                    ],
                },
            ],
        },
    )
    write_json(
        _strategy_arbiter_stratified.RISK_REVIEW,
        {"causal_status": "non_causal_review"},
    )
    write_json(
        _strategy_arbiter_stratified.BASELINE,
        {"causal_status": "non_causal_probe"},
    )

    probe = _strategy_arbiter_stratified.build_probe(root)

    assert probe["schema_version"] == "krk_strategy_arbiter_stratified_probe.v2"
    assert probe["causal_status"] == "non_causal_probe"
    assert probe["runtime_behavior_changed"] is False
    assert probe["runtime_arbiter_implemented"] is False
    assert probe["runtime_terminals_added"] is False
    assert probe["stage7_promotion_allowed"] is False
    assert probe["stage8_training_allowed"] is False
    assert probe["summary"]["best_selected_provider_positive_hit_rate"] == 1.0
    assert probe["summary"]["best_forced_provider_positive_hit_rate"] == 0.0
    assert probe["decision"]["runtime_sandbox_allowed"] is False


def test_krk_forced_provider_control_label_plan_is_bounded_and_non_causal(tmp_path):
    root = tmp_path

    def write_json(relative_path, payload):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    write_json(
        _forced_provider_control_plan.FILTERED_FRAMES,
        {
            "causal_status": "non_causal_filtered_frame_export",
            "frames": [
                {
                    "frame_id": "cp.stage5",
                    "state_id": "state.stage5",
                    "source_stage": "stage5",
                    "active_landmark_label": "fence_established",
                    "fen": "6k1/R7/8/8/8/8/5K2/8 w - - 2 2",
                    "filter_metadata": {
                        "benchmark_roles": ["strategy_arbitration_benchmark"]
                    },
                    "strategy_proposal_frames": [
                        {
                            "provider_id": "krk.stage0_basin",
                            "move_uci": "f2g3",
                            "known_outcome_label": {
                                "playout_result": "mate",
                                "selected": True,
                            },
                        },
                    ],
                },
                {
                    "frame_id": "cp.stage7",
                    "state_id": "state.stage7",
                    "source_stage": "stage7",
                    "active_landmark_label": "box_shrink",
                    "fen": "8/8/8/8/4K3/4R3/3k4/8 w - - 2 2",
                    "filter_metadata": {
                        "benchmark_roles": ["strategy_arbitration_benchmark"]
                    },
                    "strategy_proposal_frames": [
                        {
                            "provider_id": "krk.drive_to_edge",
                            "move_uci": "e3a3",
                            "known_outcome_label": {
                                "result": "max_plies",
                                "source": "forced_provider_result",
                            },
                        },
                    ],
                },
            ],
        },
    )
    write_json(
        _forced_provider_control_plan.STRATIFIED_PROBE,
        {"causal_status": "non_causal_probe"},
    )

    plan = _forced_provider_control_plan.build_plan(root, max_jobs=4, max_jobs_per_stage=2)

    assert plan["schema_version"] == "krk_forced_provider_control_label_plan.v0"
    assert plan["causal_status"] == "non_causal_label_plan"
    assert plan["runtime_behavior_changed"] is False
    assert plan["runtime_arbiter_implemented"] is False
    assert plan["stage7_promotion_allowed"] is False
    assert plan["stage8_training_allowed"] is False
    assert plan["labels_generated_in_this_slice"] is False
    assert plan["job_selection"]["selected_job_count"] == 1
    assert plan["jobs"][0]["source_stage"] == "stage5"
    assert plan["jobs"][0]["target_label_semantics"] == "forced_provider_outcome"
    assert plan["jobs"][0]["labels_generated"] is False


def test_krk_forced_provider_execution_manifest_binds_topologies(tmp_path, monkeypatch):
    root = tmp_path
    plan_path = root / _forced_provider_binding.PLAN
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        json.dumps(
            {
                "causal_status": "non_causal_label_plan",
                "jobs": [
                    {
                        "job_id": "job.stage5",
                        "causal_status": "non_causal_label_job",
                        "source_stage": "stage5",
                        "provider_id": "krk.stage0_basin",
                    },
                    {
                        "job_id": "job.stage6",
                        "causal_status": "non_causal_label_job",
                        "source_stage": "stage6",
                        "provider_id": "krk.drive_to_edge",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    stage5_topology = Path("stage5/topology.json")
    stage6_topology = Path("stage6/topology.json")
    stage5_checkpoint = Path("stage5/checkpoint.pkl")
    stage6_checkpoint = Path("stage6/checkpoint.pkl")
    for path in (stage5_topology, stage6_topology, stage5_checkpoint, stage6_checkpoint):
        full = root / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(_forced_provider_binding, "STAGE5_TOPOLOGY", stage5_topology)
    monkeypatch.setattr(_forced_provider_binding, "STAGE6_TOPOLOGY", stage6_topology)
    monkeypatch.setattr(_forced_provider_binding, "STAGE5_CHECKPOINT", stage5_checkpoint)
    monkeypatch.setattr(_forced_provider_binding, "STAGE6_CHECKPOINT", stage6_checkpoint)

    manifest = _forced_provider_binding.build_manifest(root)

    assert manifest["schema_version"] == "krk_forced_provider_label_execution_manifest.v0"
    assert manifest["causal_status"] == "non_causal_execution_manifest"
    assert manifest["runtime_behavior_changed"] is False
    assert manifest["labels_generated_in_this_slice"] is False
    assert manifest["stage7_promotion_allowed"] is False
    assert manifest["stage8_training_allowed"] is False
    assert manifest["binding_summary"]["all_bindings_valid"] is True
    assert manifest["jobs"][0]["execution_binding"]["topology_version"] == "stage6_overlay_composed_v1"
    assert (
        manifest["jobs"][0]["execution_binding"]["topology_component"]
        == "stage5_frozen_base_provider_pack_with_skill_ids"
    )
    assert manifest["jobs"][1]["execution_binding"]["topology_version"] == "stage6_overlay_composed_v1"
    assert manifest["recommended_next_step"] == "run_bounded_forced_provider_control_labels"


def test_krk_out_of_sample_execution_manifest_is_bounded_and_non_causal(tmp_path, monkeypatch):
    root = tmp_path

    def write_json(relative_path, payload):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    write_json(
        _out_of_sample_manifest.PLAN,
        {
            "causal_status": "non_causal_collection_plan",
            "collection_bounds": {"max_states": 6, "per_stage_max": 2, "horizon": 40},
        },
    )
    write_json(
        _out_of_sample_manifest.PLAN_REVIEW,
        {"causal_status": "non_causal_plan_review"},
    )
    write_json(
        _out_of_sample_manifest.BALANCED,
        {"rows": [{"state_id": "state.used"}]},
    )
    write_json(
        _out_of_sample_manifest.FRAMES_WITH_FORCED,
        {
            "causal_status": "non_causal_augmented_frame_export",
            "frames": [
                {
                    "frame_id": "cp.stage5",
                    "state_id": "state.stage5.existing",
                    "source_stage": "stage5",
                    "active_landmark_label": "fence_established",
                    "fen": "1k6/7R/2K5/8/8/8/8/8 w - - 2 2",
                    "strategy_proposal_frames": [
                        {
                            "provider_id": "krk.stage0_basin",
                            "move_uci": "c6b6",
                            "known_outcome_label": {"result": "max_plies"},
                        }
                    ],
                },
                {
                    "frame_id": "cp.used",
                    "state_id": "state.used",
                    "source_stage": "stage6",
                    "active_landmark_label": "drive_to_edge",
                    "fen": "2k5/8/1K6/8/8/8/8/R7 w - - 2 2",
                    "strategy_proposal_frames": [
                        {
                            "provider_id": "krk.stage0_basin",
                            "move_uci": "a1d1",
                            "known_outcome_label": {"result": "mate"},
                        }
                    ],
                },
            ],
        },
    )
    topology = Path("topology/krk_entry_topology.json")
    stage4_checkpoint = Path("stage4.pkl")
    stage5_checkpoint = Path("stage5.pkl")
    stage6_checkpoint = Path("stage6.pkl")
    for path in (topology, stage4_checkpoint, stage5_checkpoint, stage6_checkpoint):
        full = root / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(_out_of_sample_manifest, "STAGE6_COMPOSED_TOPOLOGY", topology)
    monkeypatch.setitem(
        _out_of_sample_manifest.STAGE_CONFIGS["stage4"],
        "source_checkpoint",
        stage4_checkpoint,
    )
    monkeypatch.setitem(
        _out_of_sample_manifest.STAGE_CONFIGS["stage5"],
        "source_checkpoint",
        stage5_checkpoint,
    )
    monkeypatch.setitem(
        _out_of_sample_manifest.STAGE_CONFIGS["stage6"],
        "source_checkpoint",
        stage6_checkpoint,
    )

    monkeypatch.setattr(
        _out_of_sample_manifest,
        "_generated_candidates",
        lambda **_: [
            {
                "source_kind": "deterministic_curriculum_sample",
                "state_id": "state.stage4.generated",
                "frame_id": "cp.stage4",
                "source_stage": "stage4",
                "active_landmark_label": "edge_trap_wrong_tempo",
                "fen": "1R6/2K5/k7/8/8/8/8/8 w - - 0 1",
                "generation": {"sample_index": 0},
                "prior_label": None,
            },
            {
                "source_kind": "deterministic_curriculum_sample",
                "state_id": "state.stage6.generated",
                "frame_id": "cp.stage6",
                "source_stage": "stage6",
                "active_landmark_label": "drive_to_edge",
                "fen": "4k3/8/3K4/8/8/8/8/R7 w - - 0 1",
                "generation": {"sample_index": 0},
                "prior_label": None,
            },
        ],
    )

    manifest = _out_of_sample_manifest.build_manifest(root)

    assert manifest["schema_version"] == "krk_strategy_arbiter_out_of_sample_execution_manifest.v0"
    assert manifest["causal_status"] == "non_causal_execution_manifest"
    assert manifest["runtime_behavior_changed"] is False
    assert manifest["runtime_arbiter_implemented"] is False
    assert manifest["labels_generated_in_this_slice"] is False
    assert manifest["stage7_promotion_allowed"] is False
    assert manifest["stage8_training_allowed"] is False
    assert manifest["binding_summary"]["all_bindings_valid"] is True
    assert manifest["binding_summary"]["job_count_by_stage"] == {
        "stage4": 1,
        "stage5": 1,
        "stage6": 1,
    }
    assert all(job["source_stage"] != "stage7" for job in manifest["jobs"])
    assert all(job["execution_binding"]["composition_profile"] == "handoff_composition_v1" for job in manifest["jobs"])
    assert manifest["decision"]["execute_labels_now"] is False
    assert manifest["decision"]["recommended_next_step"] == "review_execution_manifest_before_any_h40_label_run"


def test_krk_out_of_sample_execution_manifest_review_allows_only_bounded_labels(tmp_path, monkeypatch):
    root = tmp_path
    manifest_path = root / _out_of_sample_manifest_review.MANIFEST
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    topology = Path("topology/krk_entry_topology.json")
    checkpoint = Path("checkpoint.pkl")
    for path in (topology, checkpoint):
        full = root / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text("{}", encoding="utf-8")
    manifest_path.write_text(
        json.dumps(
            {
                "causal_status": "non_causal_execution_manifest",
                "runtime_behavior_changed": False,
                "runtime_defaults_changed": False,
                "runtime_arbiter_implemented": False,
                "runtime_terminals_added": False,
                "runtime_dtm_or_tablebase_lookup": False,
                "gameplay_topology_mutation": False,
                "labels_generated_in_this_slice": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
                "binding_summary": {"all_bindings_valid": True},
                "jobs": [
                    {
                        "job_id": f"job.{stage}",
                        "state_id": f"state.{stage}",
                        "source_stage": stage,
                        "causal_status": "non_causal_label_job",
                        "labels_generated": False,
                        "stage7_training_row": False,
                        "target_label_semantics": [
                            "selected_playout_success",
                            "forced_provider_conversion_for_selected_provider",
                            "same_move_provider_compatibility_when_available",
                            "guardrail_safe_ownership",
                            "shadow_candidate_delta",
                        ],
                        "execution_binding": {
                            "topology_path": str(topology),
                            "source_checkpoint": str(checkpoint),
                            "composition_profile": "handoff_composition_v1",
                            "selected_provider_resolved_at_execution": True,
                        },
                    }
                    for stage in ("stage4", "stage5", "stage6")
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(_out_of_sample_manifest_review, "ROOT", root)

    review = _out_of_sample_manifest_review.build_review()

    assert review["schema_version"] == "krk_strategy_arbiter_out_of_sample_execution_manifest_review.v0"
    assert review["causal_status"] == "non_causal_manifest_review"
    assert review["runtime_behavior_changed"] is False
    assert review["labels_generated_in_this_slice"] is False
    assert review["stage7_promotion_allowed"] is False
    assert review["stage8_training_allowed"] is False
    assert review["summary"]["missing_stage_coverage"] == []
    assert review["summary"]["missing_target_semantics"] == []
    assert review["summary"]["invalid_job_count"] == 0
    assert review["summary"]["stage7_training_rows"] == 0
    assert review["decision"]["bounded_label_run_allowed_after_review"] is True
    assert review["decision"]["runtime_arbiter_allowed"] is False
    assert review["decision"]["selector_sandbox_ready"] is False


def test_krk_out_of_sample_control_label_run_is_non_causal(tmp_path, monkeypatch):
    root = tmp_path
    manifest_path = root / _out_of_sample_label_run.MANIFEST
    review_path = root / _out_of_sample_label_run.REVIEW
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    job = {
        "job_id": "job.stage5",
        "frame_id": "cp.stage5",
        "state_id": "state.stage5",
        "source_stage": "stage5",
        "active_landmark_label": "fence_established",
        "fen": "1k6/7R/2K5/8/8/8/8/8 w - - 2 2",
        "horizon": 40,
        "execution_binding": {"topology_path": "topology.json"},
    }
    manifest_path.write_text(
        json.dumps(
            {
                "causal_status": "non_causal_execution_manifest",
                "binding_summary": {"all_bindings_valid": True},
                "jobs": [job],
            }
        ),
        encoding="utf-8",
    )
    review_path.write_text(
        json.dumps(
            {
                "decision": {
                    "bounded_label_run_allowed_after_review": True,
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(_out_of_sample_label_run, "_run_job", lambda repo_root, job, cache: {
        "schema_version": "krk_strategy_arbiter_out_of_sample_control_label.v0",
        "causal_status": "non_causal_outcome_label",
        "job_id": job["job_id"],
        "state_id": job["state_id"],
        "source_stage": job["source_stage"],
        "selected_provider": "krk.stage0_basin",
        "selected_move": "c6b6",
        "selected_playout_success": {"result": "mate"},
        "forced_provider_conversion_for_selected_provider": {"result": "mate"},
        "labels_generated": True,
        "runtime_behavior_changed": False,
    })

    payload = _out_of_sample_label_run.run_labels(root)

    assert payload["schema_version"] == "krk_strategy_arbiter_out_of_sample_control_labels.v0"
    assert payload["causal_status"] == "non_causal_label_run"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_arbiter_implemented"] is False
    assert payload["runtime_terminals_added"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["label_count"] == 1
    assert payload["summary"]["selected_result_counts"] == {"mate": 1}
    assert payload["recommended_next_step"] == "probe_out_of_sample_control_labels_before_any_selector_sandbox"


def test_krk_out_of_sample_control_probe_blocks_selector_when_provider_dominates(tmp_path, monkeypatch):
    root = tmp_path
    labels_path = root / _out_of_sample_probe.LABELS
    labels_path.parent.mkdir(parents=True, exist_ok=True)
    labels_path.write_text(
        json.dumps(
            {
                "causal_status": "non_causal_label_run",
                "labels": [
                    {
                        "source_stage": "stage4",
                        "selected_provider": "krk.stage0_basin",
                        "selected_playout_success": {"result": "mate"},
                        "forced_provider_conversion_for_selected_provider": {"result": "mate"},
                    },
                    {
                        "source_stage": "stage5",
                        "selected_provider": "krk.stage0_basin",
                        "selected_playout_success": {"result": "mate"},
                        "forced_provider_conversion_for_selected_provider": {"result": "mate"},
                    },
                    {
                        "source_stage": "stage6",
                        "selected_provider": "krk.stage0_basin",
                        "selected_playout_success": {"result": "max_plies"},
                        "forced_provider_conversion_for_selected_provider": {"result": "max_plies"},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(_out_of_sample_probe, "ROOT", root)

    probe = _out_of_sample_probe.build_probe()

    assert probe["schema_version"] == "krk_strategy_arbiter_out_of_sample_control_probe.v0"
    assert probe["causal_status"] == "non_causal_probe"
    assert probe["runtime_behavior_changed"] is False
    assert probe["runtime_arbiter_implemented"] is False
    assert probe["stage7_promotion_allowed"] is False
    assert probe["stage8_training_allowed"] is False
    assert probe["metrics"]["selected_provider_dominance"] == 1.0
    assert "selected_provider_dominance" in probe["decision"]["sandbox_blockers"]
    assert probe["decision"]["runtime_arbiter_allowed"] is False
    assert probe["decision"]["selector_sandbox_ready"] is False


def test_krk_out_of_sample_architecture_review_blocks_runtime_selector(tmp_path, monkeypatch):
    root = tmp_path

    def write_json(relative_path, payload):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    write_json(
        _out_of_sample_arch_review.PROBE,
        {
            "metrics": {
                "label_count": 12,
                "selected_result_counts": {"mate": 11, "max_plies": 1},
                "forced_selected_provider_result_counts": {"mate": 11, "max_plies": 1},
                "selected_provider_counts": {"krk.stage0_basin": 12},
                "stage_result_counts": {"stage4:max_plies": 1, "stage5:mate": 4},
            },
            "decision": {
                "status": "out_of_sample_controls_guardrail_positive_selector_sandbox_blocked",
                "sandbox_blockers": ["class_imbalance", "selected_provider_dominance"],
            },
        },
    )
    write_json(
        _out_of_sample_arch_review.READINESS,
        {"decision": {"status": "readiness_criteria_defined_sandbox_still_blocked"}},
    )
    write_json(
        _out_of_sample_arch_review.BALANCED_REVIEW,
        {"decision": {"status": "selector_signal_promising_sandbox_blocked_pending_readiness_criteria"}},
    )
    monkeypatch.setattr(_out_of_sample_arch_review, "ROOT", root)

    review = _out_of_sample_arch_review.build_review()

    assert review["schema_version"] == "krk_strategy_arbiter_out_of_sample_architecture_review.v0"
    assert review["causal_status"] == "non_causal_architecture_review"
    assert review["runtime_behavior_changed"] is False
    assert review["runtime_arbiter_implemented"] is False
    assert review["stage7_promotion_allowed"] is False
    assert review["stage8_training_allowed"] is False
    assert review["decision"]["status"] == "selector_sandbox_blocked_out_of_sample_controls_not_selector_diverse"
    assert review["decision"]["runtime_arbiter_allowed"] is False
    assert review["decision"]["selector_sandbox_ready"] is False
    assert review["decision"]["recommended_next_step"] == (
        "design_selector_readiness_v2_or_strategy_owner_contrast_dataset"
    )


def test_krk_selector_readiness_v2_plan_requires_provider_diversity(tmp_path, monkeypatch):
    root = tmp_path
    review_path = root / _selector_readiness_v2.ARCH_REVIEW
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(
        json.dumps({"causal_status": "non_causal_architecture_review"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(_selector_readiness_v2, "ROOT", root)

    plan = _selector_readiness_v2.build_plan()

    assert plan["schema_version"] == "krk_selector_readiness_v2_plan.v0"
    assert plan["causal_status"] == "non_causal_design_plan"
    assert plan["runtime_behavior_changed"] is False
    assert plan["runtime_arbiter_implemented"] is False
    assert plan["stage7_promotion_allowed"] is False
    assert plan["stage8_training_allowed"] is False
    requirements = {item["requirement_id"]: item for item in plan["readiness_requirements_v2"]}
    assert requirements["provider_diversity"]["minimum"]["distinct_selected_provider_families"] == 3
    assert requirements["held_out_challenge_boundary"]["minimum"]["stage7_training_rows"] == 0
    assert plan["decision"]["selector_sandbox_ready"] is False
    assert plan["decision"]["recommended_next_step"] == "build_non_causal_strategy_owner_contrast_dataset_v0"


def test_krk_strategy_owner_contrast_dataset_preserves_stage7_holdout(tmp_path, monkeypatch):
    root = tmp_path
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "krk_selector_readiness_v2_plan.json").write_text(
        json.dumps({"causal_status": "non_causal_design_plan"}),
        encoding="utf-8",
    )
    (reports / "krk_control_plane_filtered_frames_with_forced_controls_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_augmented_frame_export",
                "frames": [
                    {
                        "state_id": "state.stage5_positive",
                        "frame_id": "cp.krk.state.stage5_positive",
                        "source_stage": "stage5",
                        "active_landmark_label": "fence_established",
                        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                        "strategy_proposal_frames": [
                            {
                                "provider_id": "krk.edge_trap_close",
                                "move_uci": "a1a2",
                                "known_outcome_label": {
                                    "playout_result": "mate",
                                    "selected": True,
                                },
                            },
                            {
                                "provider_id": "krk.stage0_basin",
                                "move_uci": "a1a2",
                                "known_outcome_label": {
                                    "playout_result": "max_plies",
                                    "selected": False,
                                },
                            },
                        ],
                    },
                    {
                        "state_id": "state.stage7_heldout",
                        "frame_id": "cp.krk.state.stage7_heldout",
                        "source_stage": "stage7",
                        "active_landmark_label": "box_shrink",
                        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                        "strategy_proposal_frames": [
                            {
                                "provider_id": "krk.drive_to_edge",
                                "move_uci": "a1a2",
                                "known_outcome_label": {
                                    "source": "forced_provider_result",
                                    "result": "mate",
                                },
                            },
                            {
                                "provider_id": "krk.stage0_basin",
                                "move_uci": "a1a3",
                                "known_outcome_label": {
                                    "source": "forced_provider_result",
                                    "result": "max_plies",
                                },
                            },
                        ],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(_strategy_owner_contrast, "ROOT", root)

    dataset = _strategy_owner_contrast.build_dataset()

    assert dataset["schema_version"] == "krk_strategy_owner_contrast_dataset.v0"
    assert dataset["causal_status"] == "non_causal_dataset"
    assert dataset["runtime_behavior_changed"] is False
    assert dataset["runtime_arbiter_implemented"] is False
    assert dataset["stage7_promotion_allowed"] is False
    assert dataset["stage8_training_allowed"] is False
    assert dataset["summary"]["stage7_training_rows"] == 0
    assert dataset["summary"]["training_non_stage0_positive_rows"] == 1
    assert dataset["summary"]["heldout_non_stage0_positive_rows"] == 1
    rows_by_state = {row["state_id"]: row for row in dataset["rows"]}
    assert rows_by_state["state.stage7_heldout"]["held_out_challenge"] is True
    assert rows_by_state["state.stage7_heldout"]["training_eligible"] is False
    assert dataset["readiness_v2_assessment"]["selector_sandbox_ready"] is False
    assert "insufficient_protected_non_stage0_positive_rows" in dataset["readiness_v2_assessment"]["blockers"]
    assert dataset["decision"]["status"] == "strategy_owner_contrast_dataset_underpowered_no_selector_sandbox"


def test_krk_strategy_owner_contrast_label_plan_excludes_stage7(tmp_path, monkeypatch):
    root = tmp_path
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "krk_strategy_owner_contrast_dataset_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_dataset",
                "rows": [
                    {
                        "state_id": "state.stage5_existing",
                        "provider_labels": [{"provider_id": "krk.edge_trap_close"}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (reports / "krk_selector_readiness_v2_plan.json").write_text(
        json.dumps({"causal_status": "non_causal_design_plan"}),
        encoding="utf-8",
    )
    frames = []
    balanced_rows = []
    for stage, state_id, landmark in (
        ("stage4", "state.stage4_a", "wrong_tempo_control"),
        ("stage5", "state.stage5_existing", "fence_established"),
        ("stage6", "state.stage6_a", "drive_to_edge"),
        ("stage7", "state.stage7_a", "box_shrink"),
    ):
        frames.append(
            {
                "state_id": state_id,
                "frame_id": f"cp.krk.{state_id}",
                "source_stage": stage,
                "active_landmark_label": landmark,
                "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
            }
        )
        balanced_rows.append(
            {
                "state_id": state_id,
                "source_stage": stage,
                "provider_id": "krk.stage0_basin",
                "target_kind": "guardrail_safe_selected_playout",
                "label": "positive",
            }
        )
    (reports / "krk_control_plane_filtered_frames_with_forced_controls_v0.json").write_text(
        json.dumps({"causal_status": "non_causal_augmented_frame_export", "frames": frames}),
        encoding="utf-8",
    )
    (reports / "krk_selector_balanced_label_dataset_v1.json").write_text(
        json.dumps({"causal_status": "non_causal_balanced_label_dataset", "rows": balanced_rows}),
        encoding="utf-8",
    )
    monkeypatch.setattr(_strategy_owner_label_plan, "ROOT", root)

    plan = _strategy_owner_label_plan.build_plan(max_jobs=8, max_jobs_per_stage=3)

    assert plan["schema_version"] == "krk_strategy_owner_contrast_label_plan.v0"
    assert plan["causal_status"] == "non_causal_label_plan"
    assert plan["runtime_behavior_changed"] is False
    assert plan["runtime_arbiter_implemented"] is False
    assert plan["stage7_promotion_allowed"] is False
    assert plan["stage8_training_allowed"] is False
    assert plan["job_selection"]["stage7_jobs"] == 0
    assert all(job["source_stage"] != "stage7" for job in plan["jobs"])
    assert all(job["labels_generated"] is False for job in plan["jobs"])
    assert all(job["provider_id"] != "krk.edge_trap_close" for job in plan["jobs"] if job["state_id"] == "state.stage5_existing")
    assert plan["decision"]["selector_sandbox_ready"] is False
    assert plan["decision"]["recommended_next_step"] == "review_and_bind_bounded_contrast_label_plan_before_execution"


def test_krk_strategy_owner_contrast_label_plan_review_blocks_label_run(tmp_path, monkeypatch):
    root = tmp_path
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "krk_strategy_owner_contrast_label_plan_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_label_plan",
                "labels_generated_in_this_slice": False,
                "jobs": [
                    {
                        "job_id": "job.stage4",
                        "causal_status": "non_causal_label_job",
                        "labels_generated": False,
                        "source_stage": "stage4",
                        "provider_id": "krk.edge_trap_wrong_tempo",
                        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                        "horizon": 40,
                        "trace_mode": "failures_only",
                        "diagnostic_caches_required": True,
                    },
                    {
                        "job_id": "job.stage5",
                        "causal_status": "non_causal_label_job",
                        "labels_generated": False,
                        "source_stage": "stage5",
                        "provider_id": "krk.edge_trap_close",
                        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                        "horizon": 40,
                        "trace_mode": "failures_only",
                        "diagnostic_caches_required": True,
                    },
                    {
                        "job_id": "job.stage6",
                        "causal_status": "non_causal_label_job",
                        "labels_generated": False,
                        "source_stage": "stage6",
                        "provider_id": "krk.drive_to_edge",
                        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                        "horizon": 40,
                        "trace_mode": "failures_only",
                        "diagnostic_caches_required": True,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(_strategy_owner_label_plan_review, "ROOT", root)

    review = _strategy_owner_label_plan_review.build_review()

    assert review["schema_version"] == "krk_strategy_owner_contrast_label_plan_review.v0"
    assert review["causal_status"] == "non_causal_plan_review"
    assert review["runtime_behavior_changed"] is False
    assert review["runtime_arbiter_implemented"] is False
    assert review["stage7_promotion_allowed"] is False
    assert review["stage8_training_allowed"] is False
    assert review["review_summary"]["violations"] == []
    assert review["review_summary"]["allowed_to_bind_execution_manifest"] is True
    assert review["review_summary"]["allowed_to_run_labels"] is False
    assert review["decision"]["labels_allowed_now"] is False
    assert review["decision"]["recommended_next_step"] == "bind_contrast_label_jobs_to_explicit_topologies"


def test_krk_strategy_owner_contrast_binding_manifest_is_non_causal(tmp_path, monkeypatch):
    root = tmp_path
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    topology = (
        root
        / "snapshots"
        / "krk_triplet_pipeline"
        / "adaptive_krk_stage6_drive_overlay_composed"
        / "topology"
        / "krk_entry_topology.json"
    )
    stage5_checkpoint = (
        root
        / "snapshots"
        / "krk_triplet_pipeline"
        / "adaptive_krk_stage5_fence_clean"
        / "baseline"
        / "best_by_stage"
        / "fence_established.pkl"
    )
    stage6_checkpoint = (
        root
        / "snapshots"
        / "krk_triplet_pipeline"
        / "adaptive_krk_stage6_drive_profile_king_support"
        / "baseline"
        / "best_by_stage"
        / "drive_to_edge.pkl"
    )
    topology.parent.mkdir(parents=True, exist_ok=True)
    stage5_checkpoint.parent.mkdir(parents=True, exist_ok=True)
    stage6_checkpoint.parent.mkdir(parents=True, exist_ok=True)
    topology.write_text(
        json.dumps({"skills": ["krk.edge_trap_wrong_tempo", "krk.drive_to_edge"]}),
        encoding="utf-8",
    )
    stage5_checkpoint.write_text("stage5", encoding="utf-8")
    stage6_checkpoint.write_text("stage6", encoding="utf-8")
    (reports / "krk_strategy_owner_contrast_label_plan_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_label_plan",
                "jobs": [
                    {
                        "job_id": "job.stage4",
                        "causal_status": "non_causal_label_job",
                        "labels_generated": False,
                        "source_stage": "stage4",
                        "provider_id": "krk.edge_trap_wrong_tempo",
                        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                        "horizon": 40,
                    },
                    {
                        "job_id": "job.stage6",
                        "causal_status": "non_causal_label_job",
                        "labels_generated": False,
                        "source_stage": "stage6",
                        "provider_id": "krk.drive_to_edge",
                        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                        "horizon": 40,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (reports / "krk_strategy_owner_contrast_label_plan_review_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_plan_review",
                "review_summary": {"allowed_to_bind_execution_manifest": True},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(_strategy_owner_bind, "ROOT", root)

    manifest = _strategy_owner_bind.build_manifest()

    assert manifest["schema_version"] == "krk_strategy_owner_contrast_execution_manifest.v0"
    assert manifest["causal_status"] == "non_causal_execution_manifest"
    assert manifest["runtime_behavior_changed"] is False
    assert manifest["runtime_arbiter_implemented"] is False
    assert manifest["stage7_promotion_allowed"] is False
    assert manifest["stage8_training_allowed"] is False
    assert manifest["binding_summary"]["all_bindings_valid"] is True
    assert manifest["binding_summary"]["stage7_jobs"] == 0
    assert manifest["decision"]["labels_allowed_now"] is False
    bound = {job["provider_id"]: job["execution_binding"] for job in manifest["jobs"]}
    assert bound["krk.edge_trap_wrong_tempo"]["provider_version"] == "stage5_validated_v1"
    assert bound["krk.drive_to_edge"]["provider_version"] == "stage6_overlay_v1"


def test_krk_strategy_owner_contrast_manifest_review_allows_only_labels(tmp_path, monkeypatch):
    root = tmp_path
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    job = {
        "job_id": "job.stage4",
        "source_stage": "stage4",
        "provider_id": "krk.edge_trap_wrong_tempo",
        "horizon": 40,
        "trace_mode": "failures_only",
        "diagnostic_caches_required": True,
        "execution_binding": {
            "composition_profile": "handoff_composition_v1",
            "execution_mode": "force_provider_first_white_move_then_release",
            "enable_diagnostic_caches": True,
            "topology_version": "stage6_overlay_composed_v1",
            "provider_version": "stage5_validated_v1",
            "source_checkpoint": "checkpoint.pkl",
        },
    }
    (reports / "krk_strategy_owner_contrast_execution_manifest_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_execution_manifest",
                "binding_summary": {"all_bindings_valid": True},
                "jobs": [
                    job,
                    {**job, "job_id": "job.stage5", "source_stage": "stage5"},
                    {
                        **job,
                        "job_id": "job.stage6",
                        "source_stage": "stage6",
                        "provider_id": "krk.drive_to_edge",
                        "execution_binding": {
                            **job["execution_binding"],
                            "provider_version": "stage6_overlay_v1",
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(_strategy_owner_manifest_review, "ROOT", root)

    review = _strategy_owner_manifest_review.build_review()

    assert review["schema_version"] == "krk_strategy_owner_contrast_execution_manifest_review.v0"
    assert review["causal_status"] == "non_causal_manifest_review"
    assert review["runtime_behavior_changed"] is False
    assert review["runtime_arbiter_implemented"] is False
    assert review["stage7_promotion_allowed"] is False
    assert review["stage8_training_allowed"] is False
    assert review["review_summary"]["labels_allowed"] is False
    assert "stage4_job_count_not_4" in review["review_summary"]["violations"]
    assert review["decision"]["runtime_arbiter_allowed"] is False
    assert review["decision"]["selector_sandbox_ready"] is False


def test_krk_strategy_owner_contrast_label_run_is_non_causal(tmp_path, monkeypatch):
    root = tmp_path
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "krk_strategy_owner_contrast_execution_manifest_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_execution_manifest",
                "jobs": [
                    {
                        "job_id": "job.stage4",
                        "source_stage": "stage4",
                        "provider_id": "krk.edge_trap_wrong_tempo",
                    },
                    {
                        "job_id": "job.stage6",
                        "source_stage": "stage6",
                        "provider_id": "krk.drive_to_edge",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (reports / "krk_strategy_owner_contrast_execution_manifest_review_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_manifest_review",
                "decision": {"labels_allowed": True},
            }
        ),
        encoding="utf-8",
    )

    def fake_run_job(repo_root, job, cache):
        return {
            "schema_version": "krk_forced_provider_control_label.v0",
            "causal_status": "non_causal_outcome_label",
            "job_id": job["job_id"],
            "source_stage": job["source_stage"],
            "provider_id": job["provider_id"],
            "forced_first_move": "a1a2",
            "result": "mate",
            "plies": 3,
        }

    monkeypatch.setattr(_strategy_owner_label_run, "ROOT", root)
    monkeypatch.setattr(_strategy_owner_label_run.forced_labels, "_run_job", fake_run_job)

    payload = _strategy_owner_label_run.run_labels()

    assert payload["schema_version"] == "krk_strategy_owner_contrast_control_labels.v0"
    assert payload["causal_status"] == "non_causal_label_run"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_arbiter_implemented"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["label_count"] == 2
    assert payload["summary"]["stage7_labels"] == 0
    assert payload["summary"]["result_counts"] == {"mate": 2}
    assert payload["recommended_next_step"] == "merge_contrast_labels_and_rebuild_strategy_owner_contrast_dataset"


def test_krk_strategy_owner_contrast_probe_blocks_selector_sandbox(tmp_path, monkeypatch):
    root = tmp_path
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "state_id": "state.stage4",
            "source_stage": "stage4",
            "training_eligible": True,
            "held_out_challenge": False,
            "contrast_summary": {"provider_count": 2, "has_non_stage0_positive": True},
            "provider_labels": [
                {"provider_family": "edge_trap", "provider_id": "krk.edge_trap_close", "positive": True},
                {"provider_family": "edge_trap", "provider_id": "krk.edge_trap_wrong_tempo", "positive": False},
            ],
        },
        {
            "state_id": "state.stage5",
            "source_stage": "stage5",
            "training_eligible": True,
            "held_out_challenge": False,
            "contrast_summary": {"provider_count": 2, "has_non_stage0_positive": True},
            "provider_labels": [
                {"provider_family": "fence_established", "provider_id": "krk.fence_established", "positive": True},
                {"provider_family": "edge_trap", "provider_id": "krk.edge_trap_close", "positive": False},
            ],
        },
        {
            "state_id": "state.stage6",
            "source_stage": "stage6",
            "training_eligible": True,
            "held_out_challenge": False,
            "contrast_summary": {"provider_count": 2, "has_non_stage0_positive": True},
            "provider_labels": [
                {"provider_family": "drive_to_edge", "provider_id": "krk.drive_to_edge", "positive": True},
                {"provider_family": "edge_trap", "provider_id": "krk.edge_trap_close", "positive": False},
            ],
        },
        {
            "state_id": "state.stage7",
            "source_stage": "stage7",
            "training_eligible": False,
            "held_out_challenge": True,
            "contrast_summary": {"provider_count": 2, "has_non_stage0_positive": False},
            "provider_labels": [
                {"provider_family": "drive_to_edge", "provider_id": "krk.drive_to_edge", "positive": False},
                {"provider_family": "stage0_basin", "provider_id": "krk.stage0_basin", "positive": False},
            ],
        },
    ]
    # Duplicate rows provide enough labels for the probe-ready threshold while
    # keeping selected-provider evidence absent.
    expanded_rows = rows[:3] + [{**row, "state_id": row["state_id"] + ".b"} for row in rows[:3]] + [rows[3]]
    (reports / "krk_strategy_owner_contrast_dataset_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_dataset",
                "readiness_v2_assessment": {
                    "blockers": ["insufficient_selected_provider_family_diversity"]
                },
                "rows": expanded_rows,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(_strategy_owner_probe, "ROOT", root)

    probe = _strategy_owner_probe.build_probe()

    assert probe["schema_version"] == "krk_strategy_owner_contrast_probe.v0"
    assert probe["causal_status"] == "non_causal_probe"
    assert probe["runtime_behavior_changed"] is False
    assert probe["runtime_arbiter_implemented"] is False
    assert probe["stage7_promotion_allowed"] is False
    assert probe["stage8_training_allowed"] is False
    assert probe["decision"]["status"] == "strategy_owner_contrast_signal_present_selector_sandbox_blocked"
    assert probe["decision"]["selector_sandbox_ready"] is False
    assert "heldout_stage7_contains_unresolved_all_negative_rows" in probe["findings"]


def test_krk_selector_readiness_after_contrast_probe_review_blocks_sandbox(tmp_path, monkeypatch):
    root = tmp_path
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "krk_strategy_owner_contrast_dataset_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_dataset",
                "decision": {
                    "status": "strategy_owner_contrast_dataset_ready_for_non_causal_probe_selector_sandbox_blocked"
                },
                "readiness_v2_assessment": {
                    "blockers": ["insufficient_selected_provider_family_diversity"],
                    "contrast_probe_ready": True,
                },
            }
        ),
        encoding="utf-8",
    )
    (reports / "krk_strategy_owner_contrast_probe_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_probe",
                "decision": {
                    "status": "strategy_owner_contrast_signal_present_selector_sandbox_blocked"
                },
                "findings": [
                    "protected_conversion_positive_provider_diversity_present",
                    "protected_label_balance_present",
                    "selected_provider_family_diversity_still_missing",
                ],
                "metrics": {
                    "training_row_count": 9,
                    "heldout_row_count": 4,
                    "training_positive_label_count": 13,
                    "training_negative_label_count": 11,
                    "selected_training_provider_families": ["edge_trap"],
                    "readiness_blockers": ["insufficient_selected_provider_family_diversity"],
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(_selector_after_contrast_review, "ROOT", root)

    review = _selector_after_contrast_review.build_review()

    assert review["schema_version"] == "krk_selector_readiness_after_contrast_probe_review.v0"
    assert review["causal_status"] == "non_causal_architecture_review"
    assert review["runtime_behavior_changed"] is False
    assert review["runtime_arbiter_implemented"] is False
    assert review["stage7_promotion_allowed"] is False
    assert review["stage8_training_allowed"] is False
    assert review["decision"]["status"] == "selector_sandbox_blocked_selected_provider_evidence_missing"
    assert review["decision"]["selector_sandbox_ready"] is False
    assert review["decision"]["recommended_next_step"] == "design_non_causal_selected_provider_diversity_evidence_plan"


def test_krk_selected_provider_diversity_evidence_plan_is_design_only(tmp_path, monkeypatch):
    root = tmp_path
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "krk_selector_readiness_after_contrast_probe_review_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_architecture_review",
                "evidence": {"selected_training_provider_families": ["edge_trap"]},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(_selected_provider_diversity_plan, "ROOT", root)

    plan = _selected_provider_diversity_plan.build_plan()

    assert plan["schema_version"] == "krk_selected_provider_diversity_evidence_plan.v0"
    assert plan["causal_status"] == "non_causal_design_plan"
    assert plan["runtime_behavior_changed"] is False
    assert plan["runtime_arbiter_implemented"] is False
    assert plan["stage7_promotion_allowed"] is False
    assert plan["stage8_training_allowed"] is False
    assert plan["labels_generated_in_this_slice"] is False
    assert plan["evidence_gap"]["current_selected_training_provider_families"] == ["edge_trap"]
    assert plan["minimum_future_evidence"]["stage7_training_rows"] == 0
    assert plan["decision"]["selector_sandbox_ready"] is False
    assert plan["decision"]["recommended_next_step"] == "run_replay_free_selected_provider_diversity_scan"


def test_krk_selected_provider_diversity_scan_is_replay_free_and_non_causal(tmp_path, monkeypatch):
    root = tmp_path
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "krk_selected_provider_diversity_evidence_plan_v0.json").write_text(
        json.dumps({"causal_status": "non_causal_design_plan"}),
        encoding="utf-8",
    )
    (reports / "krk_control_plane_filtered_frames_with_forced_controls_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_augmented_frame_export",
                "frames": [
                    {
                        "state_id": "state.stage4",
                        "source_stage": "stage4",
                        "active_landmark_label": "edge_trap_wrong_tempo",
                        "strategy_proposal_frames": [
                            {
                                "provider_id": "krk.edge_trap_close",
                                "move_uci": "a1a2",
                                "known_outcome_label": {
                                    "playout_result": "mate",
                                    "selected": True,
                                },
                            }
                        ],
                    },
                    {
                        "state_id": "state.stage7",
                        "source_stage": "stage7",
                        "active_landmark_label": "box_shrink",
                        "strategy_proposal_frames": [
                            {
                                "provider_id": "krk.drive_to_edge",
                                "move_uci": "a1a2",
                                "known_outcome_label": {
                                    "playout_result": "mate",
                                    "selected": True,
                                },
                            }
                        ],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (reports / "krk_selector_balanced_label_dataset_v1.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_balanced_label_dataset",
                "rows": [
                    {
                        "state_id": "state.stage5",
                        "source_stage": "stage5",
                        "provider_id": "krk.stage0_basin",
                        "target_kind": "guardrail_safe_selected_playout",
                        "label": "positive",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(_selected_provider_scan, "ROOT", root)

    scan = _selected_provider_scan.build_scan()

    assert scan["schema_version"] == "krk_selected_provider_diversity_replay_free_scan.v0"
    assert scan["causal_status"] == "non_causal_scan"
    assert scan["runtime_behavior_changed"] is False
    assert scan["runtime_arbiter_implemented"] is False
    assert scan["stage7_promotion_allowed"] is False
    assert scan["stage8_training_allowed"] is False
    assert scan["labels_generated_in_this_slice"] is False
    assert scan["summary"]["stage7_records"] == 0
    assert scan["summary"]["selected_provider_family_counts"] == {
        "edge_trap": 1,
        "stage0_basin": 1,
    }
    assert scan["decision"]["selector_sandbox_ready"] is False


def test_krk_selected_provider_diversity_sampling_manifest_is_selection_only(tmp_path, monkeypatch):
    root = tmp_path
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    topology = (
        root
        / "snapshots"
        / "krk_triplet_pipeline"
        / "adaptive_krk_stage6_drive_overlay_composed"
        / "topology"
        / "krk_entry_topology.json"
    )
    stage5_checkpoint = (
        root
        / "snapshots"
        / "krk_triplet_pipeline"
        / "adaptive_krk_stage5_fence_clean"
        / "baseline"
        / "best_by_stage"
        / "fence_established.pkl"
    )
    stage6_checkpoint = (
        root
        / "snapshots"
        / "krk_triplet_pipeline"
        / "adaptive_krk_stage6_drive_profile_king_support"
        / "baseline"
        / "best_by_stage"
        / "drive_to_edge.pkl"
    )
    topology.parent.mkdir(parents=True, exist_ok=True)
    stage5_checkpoint.parent.mkdir(parents=True, exist_ok=True)
    stage6_checkpoint.parent.mkdir(parents=True, exist_ok=True)
    topology.write_text("{}", encoding="utf-8")
    stage5_checkpoint.write_text("stage5", encoding="utf-8")
    stage6_checkpoint.write_text("stage6", encoding="utf-8")
    (reports / "krk_selected_provider_diversity_evidence_plan_v0.json").write_text(
        json.dumps({"causal_status": "non_causal_design_plan"}),
        encoding="utf-8",
    )
    (reports / "krk_selected_provider_diversity_replay_free_scan_v0.json").write_text(
        json.dumps({"causal_status": "non_causal_scan"}),
        encoding="utf-8",
    )

    class FakeBoard:
        turn = True

        def __init__(self, name):
            self.name = name

        def board_fen(self):
            return f"8/8/8/8/8/8/8/{self.name}"

        def fen(self):
            return f"8/8/8/8/8/8/8/{self.name} w - - 0 1"

    def fake_select_eval_position(sample_rng, label, position_mode, source_names):
        return FakeBoard(label[0])

    monkeypatch.setattr(_selected_provider_sampling_manifest, "ROOT", root)
    monkeypatch.setattr(
        _selected_provider_sampling_manifest.diag,
        "source_stage_names_for_label",
        lambda label: (label,),
    )
    monkeypatch.setattr(
        _selected_provider_sampling_manifest.diag,
        "select_eval_position",
        fake_select_eval_position,
    )

    manifest = _selected_provider_sampling_manifest.build_manifest(
        max_jobs=3,
        per_stage_max=1,
        max_sample_index=1,
    )

    assert manifest["schema_version"] == "krk_selected_provider_diversity_sampling_manifest.v0"
    assert manifest["causal_status"] == "non_causal_sampling_manifest"
    assert manifest["runtime_behavior_changed"] is False
    assert manifest["runtime_arbiter_implemented"] is False
    assert manifest["stage7_promotion_allowed"] is False
    assert manifest["stage8_training_allowed"] is False
    assert manifest["binding_summary"]["job_count"] == 3
    assert manifest["selection_policy"]["playout_labels"] is False
    assert all(job["source_stage"] != "stage7" for job in manifest["jobs"])
    assert all(
        job["execution_binding"]["execution_mode"] == "observe_selected_provider_only"
        for job in manifest["jobs"]
    )


def test_krk_selected_provider_diversity_sampling_manifest_review_allows_observation_only(tmp_path, monkeypatch):
    root = tmp_path
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    base_job = {
        "causal_status": "non_causal_selection_observation_job",
        "source_stage": "stage4",
        "execution_binding": {
            "execution_mode": "observe_selected_provider_only",
            "composition_profile": "handoff_composition_v1",
            "enable_diagnostic_caches": True,
        },
    }
    (reports / "krk_selected_provider_diversity_sampling_manifest_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_sampling_manifest",
                "binding_summary": {"all_bindings_valid": True},
                "jobs": [
                    {**base_job, "job_id": "job.stage4", "source_stage": "stage4"},
                    {**base_job, "job_id": "job.stage5", "source_stage": "stage5"},
                    {**base_job, "job_id": "job.stage6", "source_stage": "stage6"},
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(_selected_provider_sampling_review, "ROOT", root)

    review = _selected_provider_sampling_review.build_review()

    assert review["schema_version"] == "krk_selected_provider_diversity_sampling_manifest_review.v0"
    assert review["causal_status"] == "non_causal_manifest_review"
    assert review["runtime_behavior_changed"] is False
    assert review["runtime_arbiter_implemented"] is False
    assert review["stage7_promotion_allowed"] is False
    assert review["stage8_training_allowed"] is False
    assert review["review_summary"]["observations_allowed"] is True
    assert review["decision"]["recommended_next_step"] == "run_bounded_selected_provider_observation_scan"


def test_krk_selected_provider_diversity_observation_scan_is_non_causal(tmp_path, monkeypatch):
    root = tmp_path
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "krk_selected_provider_diversity_sampling_manifest_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_sampling_manifest",
                "jobs": [
                    {
                        "job_id": "job.stage4",
                        "source_stage": "stage4",
                        "state_id": "state.stage4",
                        "active_landmark_label": "edge_trap_wrong_tempo",
                        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                        "execution_binding": {"topology_path": "topology.json"},
                    },
                    {
                        "job_id": "job.stage5",
                        "source_stage": "stage5",
                        "state_id": "state.stage5",
                        "active_landmark_label": "fence_established",
                        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                        "execution_binding": {"topology_path": "topology.json"},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (reports / "krk_selected_provider_diversity_sampling_manifest_review_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_manifest_review",
                "decision": {"observations_allowed": True},
            }
        ),
        encoding="utf-8",
    )
    observations = {
        "job.stage4": {
            "schema_version": "krk_selected_provider_observation.v0",
            "causal_status": "non_causal_selected_provider_observation",
            "job_id": "job.stage4",
            "source_stage": "stage4",
            "selected_provider_family": "edge_trap",
        },
        "job.stage5": {
            "schema_version": "krk_selected_provider_observation.v0",
            "causal_status": "non_causal_selected_provider_observation",
            "job_id": "job.stage5",
            "source_stage": "stage5",
            "selected_provider_family": "fence_established",
        },
    }

    def fake_observe_job(job, cache):
        return observations[job["job_id"]]

    monkeypatch.setattr(_selected_provider_observation_scan, "ROOT", root)
    monkeypatch.setattr(_selected_provider_observation_scan, "_observe_job", fake_observe_job)

    payload = _selected_provider_observation_scan.run_observations()

    assert payload["schema_version"] == "krk_selected_provider_diversity_observation_scan.v0"
    assert payload["causal_status"] == "non_causal_observation_scan"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_arbiter_implemented"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["labels_generated_in_this_slice"] is False
    assert payload["summary"]["stage7_observations"] == 0
    assert payload["summary"]["selected_provider_family_counts"] == {
        "edge_trap": 1,
        "fence_established": 1,
    }
    assert payload["decision"]["selector_sandbox_ready"] is False


def test_krk_selected_provider_diversity_architecture_review_reframes_requirement(tmp_path, monkeypatch):
    root = tmp_path
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "krk_selected_provider_diversity_replay_free_scan_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_scan",
                "summary": {
                    "selected_provider_family_counts": {"stage0_basin": 4, "edge_trap": 1},
                    "distinct_selected_provider_families": 2,
                    "max_selected_provider_family_dominance": 0.8,
                },
            }
        ),
        encoding="utf-8",
    )
    (reports / "krk_selected_provider_diversity_observation_scan_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_observation_scan",
                "summary": {
                    "selected_provider_family_counts": {"stage0_basin": 20},
                    "distinct_selected_provider_families": 1,
                    "max_selected_provider_family_dominance": 1.0,
                },
            }
        ),
        encoding="utf-8",
    )
    (reports / "krk_strategy_owner_contrast_probe_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_probe",
                "metrics": {"training_provider_family_rates": {}},
                "findings": ["protected_conversion_positive_provider_diversity_present"],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(_selected_provider_arch_review, "ROOT", root)

    review = _selected_provider_arch_review.build_review()

    assert review["schema_version"] == "krk_selected_provider_diversity_architecture_review.v0"
    assert review["causal_status"] == "non_causal_architecture_review"
    assert review["runtime_behavior_changed"] is False
    assert review["runtime_arbiter_implemented"] is False
    assert review["stage7_promotion_allowed"] is False
    assert review["stage8_training_allowed"] is False
    assert review["decision"]["status"] == "selected_provider_diversity_requirement_should_be_reframed"
    assert review["decision"]["selector_sandbox_ready"] is False
    assert review["proposed_readiness_v3_direction"]["replace_hard_requirement"] == "distinct_current_selected_provider_families"


def test_krk_selector_readiness_v3_allows_design_review_not_runtime(tmp_path, monkeypatch):
    root = tmp_path
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "krk_selected_provider_diversity_architecture_review_v0.json").write_text(
        json.dumps({"causal_status": "non_causal_architecture_review"}),
        encoding="utf-8",
    )
    (reports / "krk_strategy_owner_contrast_dataset_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_dataset",
                "summary": {
                    "training_positive_provider_label_count": 6,
                    "training_negative_provider_label_count": 6,
                    "row_count_by_stage": {"stage4": 1, "stage5": 1, "stage6": 1},
                    "stage7_training_rows": 0,
                },
                "readiness_v2_assessment": {
                    "blockers": ["insufficient_selected_provider_family_diversity"]
                },
            }
        ),
        encoding="utf-8",
    )
    (reports / "krk_strategy_owner_contrast_probe_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_probe",
                "metrics": {
                    "training_provider_family_rates": {
                        "drive_to_edge": {"positive": 1},
                        "edge_trap": {"positive": 1},
                        "fence_established": {"positive": 1},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(_selector_readiness_v3, "ROOT", root)

    plan = _selector_readiness_v3.build_plan()

    assert plan["schema_version"] == "krk_selector_readiness_v3_plan.v0"
    assert plan["causal_status"] == "non_causal_design_plan"
    assert plan["runtime_behavior_changed"] is False
    assert plan["runtime_arbiter_implemented"] is False
    assert plan["stage7_promotion_allowed"] is False
    assert plan["stage8_training_allowed"] is False
    assert plan["decision"]["status"] == "selector_readiness_v3_sandbox_design_review_allowed"
    assert plan["decision"]["runtime_arbiter_allowed"] is False
    assert plan["decision"]["selector_sandbox_ready"] is False
    assert plan["decision"]["recommended_next_step"] == "design_default_off_strategy_arbiter_sandbox_for_review"


def test_krk_strategy_arbiter_default_off_design_review_blocks_implementation(tmp_path, monkeypatch):
    root = tmp_path
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "krk_selector_readiness_v3_plan.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_design_plan",
                "reason": "test",
                "readiness_checks_v3": [
                    {"requirement_id": "proposal_family_diversity", "status": "passed"},
                    {
                        "requirement_id": "current_selected_provider_diversity",
                        "status": "diagnostic_only_not_sandbox_blocker",
                    },
                ],
                "decision": {
                    "hard_blockers": [],
                    "runtime_arbiter_allowed": False,
                    "selector_sandbox_ready": False,
                },
            }
        ),
        encoding="utf-8",
    )
    (reports / "krk_strategy_owner_contrast_probe_v0.json").write_text(
        json.dumps({"causal_status": "non_causal_probe"}),
        encoding="utf-8",
    )
    (reports / "krk_selected_provider_diversity_architecture_review_v0.json").write_text(
        json.dumps({"causal_status": "non_causal_architecture_review"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(_default_off_design_review, "ROOT", root)

    review = _default_off_design_review.build_review()

    assert review["schema_version"] == "krk_strategy_arbiter_default_off_design_review.v1"
    assert review["causal_status"] == "non_causal_design_review"
    assert review["runtime_behavior_changed"] is False
    assert review["runtime_arbiter_implemented"] is False
    assert review["selector_sandbox_implemented"] is False
    assert review["runtime_terminals_added"] is False
    assert review["stage7_promotion_allowed"] is False
    assert review["stage8_training_allowed"] is False
    assert review["decision"]["status"] == "default_off_strategy_arbiter_design_ready_for_external_review"
    assert review["decision"]["runtime_arbiter_allowed"] is False
    assert review["decision"]["selector_sandbox_ready"] is False
    assert review["decision"]["implementation_allowed"] is False


def test_krk_strategy_arbiter_runtime_review_packet_keeps_implementation_blocked(tmp_path, monkeypatch):
    root = tmp_path
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "krk_protected_stage_status.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_status_audit",
                "stage7_status": "local_valid_composition_quarantined",
                "summary": {"current_architecture_profile": "handoff_composition_v1"},
                "stage_statuses": [
                    {
                        "stage": "stage5_fence",
                        "status": "protected_solved_conversion_profile",
                        "solved_under_current_architecture": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (reports / "krk_selector_readiness_v3_plan.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_design_plan",
                "decision": {"runtime_arbiter_allowed": False},
            }
        ),
        encoding="utf-8",
    )
    (reports / "krk_strategy_arbiter_default_off_design_review_v1.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_design_review",
                "decision": {"implementation_allowed": False},
            }
        ),
        encoding="utf-8",
    )
    (reports / "krk_strategy_owner_contrast_probe_v0.json").write_text(
        json.dumps(
            {
                "causal_status": "non_causal_probe",
                "metrics": {
                    "training_provider_family_rates": {
                        "drive_to_edge": {"positive": 1},
                        "edge_trap": {"positive": 1},
                    },
                    "training_positive_label_count": 2,
                    "training_negative_label_count": 1,
                    "heldout_row_count": 0,
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(_runtime_review_packet, "ROOT", root)

    packet = _runtime_review_packet.build_packet()

    assert packet["schema_version"] == "krk_strategy_arbiter_runtime_review_packet.v1"
    assert packet["causal_status"] == "non_causal_review_packet"
    assert packet["runtime_behavior_changed"] is False
    assert packet["runtime_arbiter_implemented"] is False
    assert packet["selector_sandbox_implemented"] is False
    assert packet["stage7_promotion_allowed"] is False
    assert packet["stage8_training_allowed"] is False
    assert packet["implementation_blocked_until_review"] is True
    assert packet["decision"]["status"] == "runtime_review_packet_ready"
    assert packet["decision"]["implementation_allowed"] is False
    assert packet["decision"]["runtime_arbiter_allowed"] is False
    assert packet["decision"]["recommended_next_step"] == "external_architecture_review_decision"
