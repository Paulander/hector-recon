"""M16 reusable subcondition fragments for local KRK SCRIPT candidates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import copy
import json
from pathlib import Path
from typing import Any

from .candidate_generation import RISK_BEFORE_FEATURES
from .evaluate import ArmMetrics, evaluate_arm
from .features import validate_learner_record
from .positions import KRKPositionSet, generate_position_sets
from .sandbox import _paired_delta, _safety_counts
from .script_candidates import (
    LocalScriptConfig,
    LocalScriptMetrics,
    build_local_script_nodes,
    evaluate_local_script_arm,
    generate_local_script_candidates,
)


@dataclass(frozen=True)
class ScriptFragmentConfig:
    seed: int = 20260610
    train_count: int = 200
    heldout_weakness_count: int = 100
    heldout_broader_count: int = 100
    min_support: int = 1
    max_candidates: int = 12
    horizon: int = 40
    min_sequence_credit: float = 0.10
    activation_max_distance: float = 0.5
    eta_m3: float = 0.08
    fragment_feature_names: tuple[str, ...] = RISK_BEFORE_FEATURES


@dataclass(frozen=True)
class ScriptFragmentResult:
    config: ScriptFragmentConfig
    positions: KRKPositionSet
    exact_candidates: list[dict[str, Any]]
    fragment_candidates: list[dict[str, Any]]
    script_nodes: list[dict[str, Any]]
    generation_summary: dict[str, Any]
    baseline_metrics: dict[str, ArmMetrics]
    fragment_metrics: dict[str, LocalScriptMetrics]
    paired_deltas: dict[str, dict[str, int]]
    safety: dict[str, dict[str, int]]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        validate_learner_record(self.fragment_candidates)
        return {
            "schema_version": "krk_autogrowth_m16_script_fragments.v0",
            "config": asdict(self.config),
            "dataset": {
                "seed": self.positions.seed,
                "digest": self.positions.digest(),
                "train_count": len(self.positions.train),
                "heldout_count": len(self.positions.heldout),
                "heldout_weakness_count": len(self.positions.heldout_weakness),
                "heldout_broader_count": len(self.positions.heldout_broader),
            },
            "generation_summary": self.generation_summary,
            "local_recon_structure": {
                "parent_node_type": "SCRIPT",
                "candidate_node_type": "SCRIPT",
                "fragment_node_type": "TERMINAL",
                "action_child_count_per_script": 2,
                "relation_types": ["SUB", "POR", "SUR", "RET"],
                "move_choice_mediated_by_local_script_nodes": True,
                "fragment_confirms_script_locally": True,
                "direct_move_override": False,
            },
            "fragment_candidates": self.fragment_candidates,
            "script_nodes": [
                {
                    "cell": node["cell"].to_dict(),
                    "local_weight": node["local_weight"],
                    "learner_visible": node["learner_visible"],
                    "diagnostics": node["diagnostics"],
                }
                for node in self.script_nodes
            ],
            "arms": {
                "baseline": {name: metric.to_dict() for name, metric in self.baseline_metrics.items()},
                "fragment_script": {name: metric.to_dict() for name, metric in self.fragment_metrics.items()},
            },
            "paired_deltas": self.paired_deltas,
            "safety": self.safety,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_script_fragment_experiment(
    *,
    config: ScriptFragmentConfig,
    positions: KRKPositionSet | None = None,
) -> ScriptFragmentResult:
    positions = positions or generate_position_sets(
        seed=config.seed,
        train_count=config.train_count,
        heldout_weakness_count=config.heldout_weakness_count,
        heldout_broader_count=config.heldout_broader_count,
    )
    exact_config = _as_local_script_config(config, activation_max_distance=0.0)
    exact_candidates, exact_summary = generate_local_script_candidates(positions.train, config=exact_config)
    fragment_candidates = generalize_script_candidates_to_fragments(
        exact_candidates,
        fragment_feature_names=config.fragment_feature_names,
    )
    fragment_config = _as_local_script_config(config, activation_max_distance=config.activation_max_distance)
    script_nodes = build_local_script_nodes(
        positions.train,
        candidates=fragment_candidates,
        config=fragment_config,
    )
    baseline_metrics, fragment_metrics, paired_deltas, safety = _evaluate_fragment_slices(
        positions,
        script_nodes=script_nodes,
        config=config,
    )
    generation_summary = {
        **exact_summary,
        "exact_candidate_count": len(exact_candidates),
        "fragment_candidate_count": len(fragment_candidates),
        "fragment_feature_names": list(config.fragment_feature_names),
        "behavior_change_applied": False,
        "candidate_active_in_runtime": False,
        "direct_move_override": False,
    }
    decision = _fragment_decision(
        baseline_metrics=baseline_metrics,
        fragment_metrics=fragment_metrics,
        safety=safety,
    )
    return ScriptFragmentResult(
        config=config,
        positions=positions,
        exact_candidates=exact_candidates,
        fragment_candidates=fragment_candidates,
        script_nodes=script_nodes,
        generation_summary=generation_summary,
        baseline_metrics=baseline_metrics,
        fragment_metrics=fragment_metrics,
        paired_deltas=paired_deltas,
        safety=safety,
        decision=decision,
    )


def generalize_script_candidates_to_fragments(
    candidates: list[dict[str, Any]],
    *,
    fragment_feature_names: tuple[str, ...] = RISK_BEFORE_FEATURES,
) -> list[dict[str, Any]]:
    fragment_candidates: list[dict[str, Any]] = []
    for candidate in candidates:
        fragment = copy.deepcopy(candidate)
        prototype = candidate["before_cluster"]["prototype"]
        fragment["candidate_key"] = f"m16_fragment_{candidate['candidate_key'].removeprefix('m15_script_')}"
        fragment["status"] = "m16_fragment_script_not_spawned"
        fragment["source_candidate_key"] = candidate["candidate_key"]
        fragment["before_cluster"] = {
            "feature_names": list(fragment_feature_names),
            "prototype": {
                name: prototype[name]
                for name in fragment_feature_names
            },
        }
        fragment["subcondition_fragment"] = {
            "node_type": "TERMINAL",
            "feature_names": list(fragment_feature_names),
            "relation_to_script": "SUR",
            "scope": "local_script_request",
            "chooses_move_directly": False,
        }
        fragment["recon_topology_plan"]["node_types"] = ["SCRIPT", "TERMINAL", "ACTION", "ACTION", "TERMINAL"]
        fragment["recon_topology_plan"]["relation_types"] = ["SUB", "POR", "SUR", "RET"]
        fragment["script_plan"]["relation_plan"]["fragment_confirmation_relation"] = "SUR"
        fragment["script_plan"]["relation_plan"]["chooses_move_directly"] = False
        validate_learner_record(fragment)
        fragment_candidates.append(fragment)
    return fragment_candidates


def _evaluate_fragment_slices(
    positions: KRKPositionSet,
    *,
    script_nodes: list[dict[str, Any]],
    config: ScriptFragmentConfig,
) -> tuple[
    dict[str, ArmMetrics],
    dict[str, LocalScriptMetrics],
    dict[str, dict[str, int]],
    dict[str, dict[str, int]],
]:
    slices = {
        "train_replay": list(positions.train),
        "heldout_weakness": list(positions.heldout_weakness),
        "heldout_broader": list(positions.heldout_broader),
        "heldout_all": list(positions.heldout),
    }
    baseline_metrics: dict[str, ArmMetrics] = {}
    fragment_metrics: dict[str, LocalScriptMetrics] = {}
    paired_deltas: dict[str, dict[str, int]] = {}
    safety: dict[str, dict[str, int]] = {}
    for name, fens in slices.items():
        baseline_metric, baseline_outcomes = evaluate_arm(fens, arm="baseline", horizon=config.horizon)
        fragment_metric, fragment_outcomes = evaluate_local_script_arm(
            fens,
            script_nodes=script_nodes,
            horizon=config.horizon,
            activation_max_distance=config.activation_max_distance,
        )
        baseline_metrics[name] = baseline_metric
        fragment_metrics[name] = fragment_metric
        paired_deltas[name] = _paired_delta(baseline_outcomes, fragment_outcomes)
        safety[name] = _safety_counts(baseline_outcomes, fragment_outcomes)
    return baseline_metrics, fragment_metrics, paired_deltas, safety


def _fragment_decision(
    *,
    baseline_metrics: dict[str, ArmMetrics],
    fragment_metrics: dict[str, LocalScriptMetrics],
    safety: dict[str, dict[str, int]],
) -> dict[str, Any]:
    baseline = baseline_metrics["heldout_all"]
    heldout = fragment_metrics["heldout_all"]
    train = fragment_metrics["train_replay"]
    heldout_safety = safety["heldout_all"]
    safety_ok = (
        heldout_safety["illegal_regression_count"] == 0
        and heldout_safety["stalemate_regression_count"] == 0
        and heldout_safety["rook_loss_regression_count"] == 0
    )
    heldout_activation = heldout.script_start_count > 0
    train_activation = train.script_start_count > 0
    conversion_gain = heldout.mates > baseline.mates
    partial_curriculum_ready = train_activation and safety_ok
    broad_curriculum_ready = heldout_activation and safety_ok and heldout.negative_credit_count == 0
    reasons: list[str] = []
    if not train_activation:
        reasons.append("no_train_replay_activation")
    if not heldout_activation:
        reasons.append("no_heldout_activation")
    if not safety_ok:
        reasons.append("heldout_safety_regression")
    if heldout.mates == 0:
        reasons.append("no_heldout_conversion")
    if broad_curriculum_ready:
        status = "script_fragment_broad_curriculum_ready"
    elif partial_curriculum_ready:
        status = "script_fragment_partial_curriculum_ready"
    else:
        status = "script_fragment_checkpoint_failed"
    return {
        "status": status,
        "passed": partial_curriculum_ready,
        "partial_curriculum_ready": partial_curriculum_ready,
        "broad_curriculum_ready": broad_curriculum_ready,
        "heldout_activation_found": heldout_activation,
        "train_replay_activation_found": train_activation,
        "safety_checkpoint_passed": safety_ok,
        "krk_competence_passed": conversion_gain and safety_ok,
        "move_choice_mediated_by_local_script_nodes": True,
        "direct_move_override": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "reasons": reasons,
    }


def _as_local_script_config(config: ScriptFragmentConfig, *, activation_max_distance: float) -> LocalScriptConfig:
    return LocalScriptConfig(
        seed=config.seed,
        train_count=config.train_count,
        heldout_weakness_count=config.heldout_weakness_count,
        heldout_broader_count=config.heldout_broader_count,
        min_support=config.min_support,
        max_candidates=config.max_candidates,
        horizon=config.horizon,
        min_sequence_credit=config.min_sequence_credit,
        activation_max_distance=activation_max_distance,
        eta_m3=config.eta_m3,
    )
