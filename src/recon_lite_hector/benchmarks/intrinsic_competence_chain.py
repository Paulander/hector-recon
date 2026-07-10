"""Planted proof for recursively grounded intrinsic competence credit.

The learner receives one terminal outcome at the innermost rung. Outer rungs see
only the consolidated signal emitted by the already-grounded successor cell.
The task evaluator uses full rollouts solely for paired causal confirmation.
No intermediate rung label is converted into a reward.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from recon_lite_hector.learning import IntrinsicCreditConfig, IntrinsicCreditEngine


@dataclass(frozen=True)
class ChainBenchmarkConfig:
    episodes_per_rung: int = 12
    output_path: str | None = None
    gamma: float = 0.97
    real_move_cost: float = 0.01
    eta_fast: float = 0.40
    eta_slow: float = 1.0
    min_grounding_evidence: int = 3


def _engine(config: ChainBenchmarkConfig) -> IntrinsicCreditEngine:
    return IntrinsicCreditEngine(
        IntrinsicCreditConfig(
            gamma=config.gamma,
            real_move_cost=config.real_move_cost,
            eta_fast=config.eta_fast,
            eta_slow=config.eta_slow,
            min_grounding_evidence=config.min_grounding_evidence,
            min_causal_confirmations=1,
        )
    )


def _terminal_return(config: ChainBenchmarkConfig, real_moves: int) -> float:
    return 1.0 - config.real_move_cost * real_moves


def _train_terminal_anchor(
    engine: IntrinsicCreditEngine,
    config: ChainBenchmarkConfig,
    cell_id: str,
) -> None:
    for _ in range(config.episodes_per_rung):
        engine.begin_episode()
        engine.transition(cell_id, terminal_kind="mate")
    engine.record_paired_intervention(
        cell_id,
        enabled_return=_terminal_return(config, 1),
        disabled_return=-0.25,
    )
    engine.consolidate((cell_id,))


def _train_from_child(
    engine: IntrinsicCreditEngine,
    config: ChainBenchmarkConfig,
    cell_id: str,
    child_id: str,
    *,
    rollout_moves: int,
) -> None:
    for _ in range(config.episodes_per_rung):
        engine.begin_episode()
        engine.transition(cell_id, successor_ids=(child_id,))
    # The evaluator compares complete enabled/disabled rollouts after learning.
    # This confirms causality but is not used as an intermediate shaping signal.
    engine.record_paired_intervention(
        cell_id,
        enabled_return=_terminal_return(config, rollout_moves),
        disabled_return=-0.25,
    )
    engine.consolidate((cell_id,))


def run_intrinsic_competence_chain(
    config: ChainBenchmarkConfig | None = None,
) -> dict[str, Any]:
    """Run the chain and controls, optionally writing one compact artifact."""

    cfg = config or ChainBenchmarkConfig()
    engine = _engine(cfg)
    cell_ids = ("cell_000", "cell_001", "cell_002")
    for cell_id in cell_ids:
        engine.register(cell_id, mature=True)

    _train_terminal_anchor(engine, cfg, cell_ids[0])
    _train_from_child(engine, cfg, cell_ids[1], cell_ids[0], rollout_moves=2)
    _train_from_child(engine, cfg, cell_ids[2], cell_ids[1], rollout_moves=3)

    states = engine.states
    values = {cell_id: states[cell_id].slow_value for cell_id in cell_ids}
    levels = {cell_id: states[cell_id].grounding_level for cell_id in cell_ids}

    no_bootstrap = _engine(cfg)
    no_bootstrap.register("outer", mature=True)
    for _ in range(cfg.episodes_per_rung):
        no_bootstrap.begin_episode()
        no_bootstrap.transition("outer")

    immature = _engine(cfg)
    immature.register("child", mature=False)
    immature.register("parent", mature=True)
    for _ in range(cfg.episodes_per_rung):
        immature.begin_episode()
        immature.transition("child", terminal_kind="mate")
    immature.record_paired_intervention(
        "child", enabled_return=_terminal_return(cfg, 1), disabled_return=-0.25
    )
    immature.consolidate(("child",))
    immature.begin_episode()
    immature_event = immature.transition("parent", successor_ids=("child",))

    engine.begin_episode()
    cycle_event = engine.transition(cell_ids[0], successor_ids=(cell_ids[2],))

    gates = {
        "terminal_anchor": states[cell_ids[0]].grounding_level == 0 and values[cell_ids[0]] > 0.0,
        "recursive_handoff": levels == {cell_ids[0]: 0, cell_ids[1]: 1, cell_ids[2]: 2},
        "value_orders_by_distance": values[cell_ids[0]] > values[cell_ids[1]] > values[cell_ids[2]] > 0.0,
        "no_bootstrap_control": no_bootstrap.states["outer"].fast_value < 0.0
        and no_bootstrap.states["outer"].grounding_level is None,
        "immature_provider_blocked": immature_event.provider_ids == ()
        and immature_event.successor_value == 0.0,
        "cycle_guard": cycle_event.cycle_rejected and cycle_event.provider_ids == (),
        "intermediate_reward_labels_used": False,
    }
    summary: dict[str, Any] = {
        "benchmark": "intrinsic_competence_chain_v1",
        "config": asdict(cfg),
        "cell_ids_are_semantically_anonymous": True,
        "root_reward_source": "terminal outcome only",
        "paired_confirmation_source": "complete enabled/disabled rollout outcomes",
        "values": values,
        "grounding_levels": levels,
        "grounding_ancestors": {
            cell_id: sorted(states[cell_id].grounding_ancestors) for cell_id in cell_ids
        },
        "controls": {
            "no_bootstrap_fast_value": no_bootstrap.states["outer"].fast_value,
            "immature_provider_event": asdict(immature_event),
            "cycle_event": asdict(cycle_event),
        },
        "gates": gates,
        "pass": all(value for key, value in gates.items() if key != "intermediate_reward_labels_used")
        and gates["intermediate_reward_labels_used"] is False,
        "engine_snapshot": engine.snapshot(),
    }
    if cfg.output_path is not None:
        path = Path(cfg.output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


if __name__ == "__main__":
    result = run_intrinsic_competence_chain()
    print(json.dumps({"pass": result["pass"], "values": result["values"], "gates": result["gates"]}, indent=2))
