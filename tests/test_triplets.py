from recon_lite_chess.triplets import (
    ActuatorIntent,
    AfterCondition,
    BeforeCondition,
    CreditPolicy,
    TripletGrowthMode,
    TripletGrowthProfile,
    terminal_delta,
)


def test_terminal_delta_uses_shared_sensor_ids():
    before = {"s1": 0.2, "s2": 0.5}
    after = {"s1": 0.8, "s3": 1.0}

    assert terminal_delta(before, after, ["s1", "s2", "s3"]) == {"s1": 0.6000000000000001}


def test_before_condition_matches_terminal_space_prototype():
    condition = BeforeCondition(
        sensor_ids=("s1", "s2"),
        prototype={"s1": 1.0, "s2": 0.0},
        max_distance=0.25,
    )

    match = condition.evaluate({"s1": 0.9, "s2": 0.1})

    assert match.matched is True
    assert match.score > 0.8
    assert match.details["distance"] < 0.25


def test_actuator_intent_scores_simulated_terminal_delta():
    intent = ActuatorIntent(
        targets=("s1", "s2"),
        goal_delta={"s1": 1.0, "s2": -1.0},
        min_similarity=0.99,
    )

    match = intent.score_transition(
        before={"s1": 0.0, "s2": 2.0},
        after={"s1": 1.0, "s2": 1.0},
    )

    assert match.matched is True
    assert match.score > 0.99


def test_after_condition_can_reject_wrong_delta_even_when_keys_exist():
    after = AfterCondition(
        targets=("s1", "s2"),
        goal_delta={"s1": 1.0, "s2": -1.0},
        min_similarity=0.9,
        max_error=0.25,
    )

    match = after.evaluate(
        before={"s1": 0.0, "s2": 2.0},
        after={"s1": -1.0, "s2": 3.0},
    )

    assert match.matched is False
    assert match.details["error"] > 0.25


def test_credit_policy_rewards_goal_distance_improvement():
    credit = CreditPolicy(progress_weight=2.0, success_reward=10.0)

    assert credit.score(before_goal_distance=0.8, after_goal_distance=0.3) == 1.0
    assert credit.score(before_goal_distance=0.8, after_goal_distance=0.3, success=True) == 10.0
    assert credit.score(before_goal_distance=0.3, after_goal_distance=0.8) < 0.0


def test_growth_profiles_separate_training_eval_and_observe_modes():
    training = TripletGrowthProfile.training()
    evaluation = TripletGrowthProfile.evaluation()
    observe = TripletGrowthProfile.full_game_observe()

    assert training.mode is TripletGrowthMode.TRAINING
    assert training.spawn_probability(active_trials=0, stagnant=True) > training.base_spawn_probability

    assert evaluation.spawn_probability(active_trials=0, stagnant=True) == 0.0
    assert evaluation.allow_promotion is False
    assert evaluation.allow_prune is False

    assert observe.allow_spawn is True
    assert observe.allow_promotion is False
    assert observe.allow_prune is False
    assert observe.spawn_probability(active_trials=0, stagnant=True) > 0.0
