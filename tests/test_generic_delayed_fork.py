from __future__ import annotations

import random

from recon_lite_hector.learning import (
    IntrinsicCreditConfig,
    IntrinsicCreditEngine,
    Responsibility,
)


def _run_delayed_episode(
    *,
    early_id: str,
    filler_ids: tuple[str, ...],
    reset_each_step: bool,
) -> tuple[float, float]:
    engine = IntrinsicCreditEngine(
        IntrinsicCreditConfig(
            gamma=1.0,
            real_move_cost=0.0,
            eligibility_decay=0.8,
            eta_fast=0.5,
            parent_learning_decay=1.0,
        )
    )
    engine.register(early_id)
    for filler_id in filler_ids:
        engine.register(filler_id)
    terminal_id = f"terminal_{early_id}"
    engine.register(terminal_id)

    engine.begin_episode()
    engine.transition(
        early_id,
        responsibilities=(Responsibility(early_id),),
        prediction_override=0.0,
    )
    for filler_id in filler_ids:
        if reset_each_step:
            engine.begin_episode()
        engine.transition(
            filler_id,
            responsibilities=(Responsibility(filler_id),),
            prediction_override=0.0,
        )
    if reset_each_step:
        engine.begin_episode()
    terminal = engine.transition(
        terminal_id,
        responsibilities=(Responsibility(terminal_id),),
        terminal_value=1.0,
        prediction_override=0.0,
    )
    return engine.states[early_id].fast_value, terminal.td_error


def test_delayed_fork_requires_one_episode_boundary_not_per_step_reset() -> None:
    for seed in range(20):
        rng = random.Random(20260712 + seed)
        delay = rng.choice((4, 5, 6))
        anonymous = [f"cell_{seed}_{index}" for index in range(delay)]
        rng.shuffle(anonymous)
        early_id = anonymous[0]
        filler_ids = tuple(anonymous[1:-1])

        persistent_value, persistent_delta = _run_delayed_episode(
            early_id=early_id,
            filler_ids=filler_ids,
            reset_each_step=False,
        )
        reset_value, reset_delta = _run_delayed_episode(
            early_id=early_id,
            filler_ids=filler_ids,
            reset_each_step=True,
        )

        assert persistent_delta == reset_delta == 1.0
        assert persistent_value > 0.0
        assert reset_value == 0.0
