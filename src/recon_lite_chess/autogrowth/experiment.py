"""Full KRK Autogrowth v0 three-arm experiment wrapper."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from .evaluate import EvaluationConfig, evaluate_baseline_and_sham
from .positions import KRKPositionSet, generate_position_sets
from .sandbox import SandboxConfig, evaluate_candidate_sandbox


@dataclass(frozen=True)
class AutogrowthExperimentConfig:
    seed: int = 20260610
    train_count: int = 200
    heldout_weakness_count: int = 100
    heldout_broader_count: int = 100
    horizons: tuple[int, ...] = (40, 80)
    candidate_path: str = "reports/autogrowth/krk_autogrowth_m4_candidates.json"
    activation_max_distance: float = 1.5


@dataclass(frozen=True)
class AutogrowthExperimentResult:
    config: AutogrowthExperimentConfig
    positions: KRKPositionSet
    baseline_payload: dict[str, Any]
    sandbox_payload: dict[str, Any]
    threshold_evaluation: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_v0_experiment.v0",
            "config": {
                **asdict(self.config),
                "horizons": list(self.config.horizons),
            },
            "dataset": {
                "seed": self.positions.seed,
                "digest": self.positions.digest(),
                "train_count": len(self.positions.train),
                "heldout_count": len(self.positions.heldout),
                "heldout_weakness_count": len(self.positions.heldout_weakness),
                "heldout_broader_count": len(self.positions.heldout_broader),
            },
            "candidate": self.sandbox_payload["candidate"],
            "arms": {
                "baseline": self.baseline_payload["arms"]["baseline"],
                "sham_growth": self.baseline_payload["arms"]["sham_growth"],
                "autogrowth_sandbox": self.sandbox_payload["arms"]["autogrowth_sandbox"],
            },
            "paired_deltas": {
                "baseline_vs_sham": self.baseline_payload["paired_deltas"],
                "baseline_vs_autogrowth_sandbox": self.sandbox_payload["paired_deltas"],
            },
            "safety": self.sandbox_payload["safety"],
            "learning_decisions": self.sandbox_payload["learning_decisions"],
            "threshold_evaluation": self.threshold_evaluation,
            "decision": {
                "status": (
                    "pass_promote_candidate"
                    if self.threshold_evaluation["passed"]
                    else "fail_quarantine_candidate"
                ),
                "candidate_promoted": self.threshold_evaluation["passed"],
                "candidate_nodes_spawned": self.sandbox_payload["decision"]["candidate_nodes_spawned"],
                "candidate_nodes_promoted": 1 if self.threshold_evaluation["passed"] else 0,
                "deleted_candidate_count": 0 if self.threshold_evaluation["passed"] else 1,
                "m3_update_count": self.sandbox_payload["decision"]["m3_update_count"],
                "m4_event_count": 1 if self.threshold_evaluation["passed"] else 0,
                "runtime_tablebase_or_dtm_move_source": False,
                "direct_move_override": False,
            },
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_autogrowth_experiment(
    *,
    config: AutogrowthExperimentConfig,
    positions: KRKPositionSet | None = None,
) -> AutogrowthExperimentResult:
    positions = positions or generate_position_sets(
        seed=config.seed,
        train_count=config.train_count,
        heldout_weakness_count=config.heldout_weakness_count,
        heldout_broader_count=config.heldout_broader_count,
    )
    baseline_result = evaluate_baseline_and_sham(
        config=EvaluationConfig(
            seed=config.seed,
            train_count=config.train_count,
            heldout_weakness_count=config.heldout_weakness_count,
            heldout_broader_count=config.heldout_broader_count,
            horizons=config.horizons,
        ),
        positions=positions,
    )
    sandbox_result = evaluate_candidate_sandbox(
        config=SandboxConfig(
            seed=config.seed,
            train_count=config.train_count,
            heldout_weakness_count=config.heldout_weakness_count,
            heldout_broader_count=config.heldout_broader_count,
            horizons=config.horizons,
            candidate_path=config.candidate_path,
            activation_max_distance=config.activation_max_distance,
        ),
        positions=positions,
    )
    baseline_payload = baseline_result.to_dict()
    sandbox_payload = sandbox_result.to_dict()
    thresholds = _threshold_evaluation(
        baseline_payload=baseline_payload,
        sandbox_payload=sandbox_payload,
    )
    return AutogrowthExperimentResult(
        config=config,
        positions=positions,
        baseline_payload=baseline_payload,
        sandbox_payload=sandbox_payload,
        threshold_evaluation=thresholds,
    )


def _threshold_evaluation(
    *,
    baseline_payload: dict[str, Any],
    sandbox_payload: dict[str, Any],
) -> dict[str, Any]:
    h40 = _horizon_thresholds("40", baseline_payload, sandbox_payload)
    h80 = _horizon_thresholds("80", baseline_payload, sandbox_payload)
    checks = {
        "h40_conversion_plus_10pp": h40["conversion_delta_pp"] >= 10.0,
        "h80_conversion_plus_5pp": h80["conversion_delta_pp"] >= 5.0,
        "h40_horizon_failures_drop_20pct": h40["horizon_failure_drop_pct"] >= 20.0,
        "protected_regressions_zero": all(
            item["protected_baseline_regression_count"] == 0
            for item in sandbox_payload["safety"].values()
        ),
        "illegal_regressions_zero": all(
            item["illegal_regression_count"] == 0 for item in sandbox_payload["safety"].values()
        ),
        "stalemate_blunder_regressions_zero": all(
            item["stalemate_regression_count"] == 0 and item["blunder_regression_count"] == 0
            for item in sandbox_payload["safety"].values()
        ),
        "candidate_activation_at_least_10pct": all(
            arm["candidate_activation_rate"] >= 0.10
            for arm in sandbox_payload["arms"]["autogrowth_sandbox"].values()
        ),
        "m3_updates_nonzero": sandbox_payload["decision"]["m3_update_count"] > 0,
        "m4_consolidation_persisted_candidate": sandbox_payload["decision"]["m4_event_count"] > 0,
        "sham_did_not_match_candidate_improvement": _sham_did_not_match_candidate(
            baseline_payload=baseline_payload,
            sandbox_payload=sandbox_payload,
        ),
    }
    failed = [name for name, passed in checks.items() if not passed]
    return {
        "passed": not failed,
        "failed_checks": failed,
        "checks": checks,
        "h40": h40,
        "h80": h80,
    }


def _horizon_thresholds(
    horizon: str,
    baseline_payload: dict[str, Any],
    sandbox_payload: dict[str, Any],
) -> dict[str, float]:
    baseline = baseline_payload["arms"]["baseline"][horizon]
    candidate = sandbox_payload["arms"]["autogrowth_sandbox"][horizon]
    conversion_delta_pp = 100.0 * (candidate["conversion_rate"] - baseline["conversion_rate"])
    baseline_failures = int(baseline["horizon_no_mate"])
    candidate_failures = int(candidate["horizon_no_mate"])
    if baseline_failures == 0:
        failure_drop_pct = 0.0
    else:
        failure_drop_pct = 100.0 * (baseline_failures - candidate_failures) / baseline_failures
    return {
        "baseline_conversion_rate": float(baseline["conversion_rate"]),
        "candidate_conversion_rate": float(candidate["conversion_rate"]),
        "conversion_delta_pp": conversion_delta_pp,
        "baseline_horizon_no_mate": float(baseline_failures),
        "candidate_horizon_no_mate": float(candidate_failures),
        "horizon_failure_drop_pct": failure_drop_pct,
    }


def _sham_did_not_match_candidate(
    *,
    baseline_payload: dict[str, Any],
    sandbox_payload: dict[str, Any],
) -> bool:
    for horizon, baseline in baseline_payload["arms"]["baseline"].items():
        sham = baseline_payload["arms"]["sham_growth"][horizon]
        candidate = sandbox_payload["arms"]["autogrowth_sandbox"][horizon]
        sham_delta = sham["conversion_rate"] - baseline["conversion_rate"]
        candidate_delta = candidate["conversion_rate"] - baseline["conversion_rate"]
        if candidate_delta > 0.0 and sham_delta >= candidate_delta:
            return False
    return True
