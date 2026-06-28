from recon_lite_chess.autogrowth.clean_edge_fence_stage import (
    CleanEdgeFenceStageConfig,
    _is_veto_terminal_key,
    _promote_edge_fence,
)
from recon_lite_chess.autogrowth.terminal_substrate import TerminalAffordanceLearner


def _terminal(learner: TerminalAffordanceLearner, key: str, *, weight: float, positive: int, negative: int) -> None:
    terminal = learner.get_terminal(key)
    terminal.local_weight = weight
    terminal.positive_credit = positive
    terminal.negative_credit = negative


def test_tg47_m4_promotes_repeated_affordance_and_explicit_veto_only() -> None:
    learner = TerminalAffordanceLearner.create(eta_m3=0.08)
    _terminal(
        learner,
        "action_pattern:gives_check=1",
        weight=0.80,
        positive=20,
        negative=4,
    )
    _terminal(
        learner,
        "action_pattern:black_reply_mobility_after=0",
        weight=0.20,
        positive=1,
        negative=0,
    )
    _terminal(
        learner,
        "action_pattern:rook_attacked_after=1",
        weight=-0.90,
        positive=2,
        negative=20,
    )
    _terminal(
        learner,
        "before_terminal:rook_present=1",
        weight=-1.10,
        positive=2,
        negative=20,
    )

    promoted, audit = _promote_edge_fence(
        learner,
        CleanEdgeFenceStageConfig(m4_precision_threshold=0.58, m4_min_positive_support=12, m4_min_negative_support=12),
    )

    promoted_keys = set(promoted.terminals)
    assert "action_pattern:gives_check=1" in promoted_keys
    assert "action_pattern:rook_attacked_after=1" in promoted_keys
    assert "action_pattern:black_reply_mobility_after=0" not in promoted_keys
    assert "before_terminal:rook_present=1" not in promoted_keys

    promoted_as = {row["terminal_key"]: row["promoted_as"] for row in audit["candidate_rows"] if row["promoted"]}
    assert promoted_as["action_pattern:gives_check=1"] == "affordance"
    assert promoted_as["action_pattern:rook_attacked_after=1"] == "veto"


def test_tg47_veto_terminal_key_is_explicit_not_broad_safety_context() -> None:
    assert _is_veto_terminal_key("action_pattern:rook_attacked_after=1")
    assert _is_veto_terminal_key("delta_terminal:confinement_area=positive")
    assert not _is_veto_terminal_key("action_pattern:rook_attacked_after=0")
    assert not _is_veto_terminal_key("before_terminal:rook_present=1")
