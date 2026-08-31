from __future__ import annotations

from itertools import permutations
import json

import pytest

from recon_lite import NodeState

from recon_lite_chess.autogrowth.native_all_reply_envelope import (
    AvailabilityState,
    CounterexampleChallengeSelector,
    ReplyAuthority,
    SELECTION_READ_FIELDS,
    evaluate_all_reply_envelope,
    rank_counterexample_challenges,
    replay_all_reply_envelope,
)


def _reply(
    reply_id: str,
    state: AvailabilityState,
    *,
    confidence: float = 0.9,
    value: float = 0.8,
    exposure_count: int = 0,
    grounded: bool = True,
) -> ReplyAuthority:
    return ReplyAuthority(
        reply_id,
        state=state,
        confidence=confidence,
        value=value,
        exposure_count=exposure_count,
        grounded=grounded,
    )


def test_conservative_envelope_uses_minimum_not_average() -> None:
    result = evaluate_all_reply_envelope([
        _reply("reply:a", AvailabilityState.AVAILABLE, value=0.92),
        _reply("reply:b", AvailabilityState.AVAILABLE, value=0.18),
    ], generic_seed=17)

    assert result.state is AvailabilityState.AVAILABLE
    assert result.value == 0.18
    assert result.value != (0.92 + 0.18) / 2.0
    assert result.positive_gate is True
    assert result.all_available_root_state is NodeState.CONFIRMED
    assert result.any_refuted_root_state is NodeState.FAILED


def test_envelope_is_permutation_invariant() -> None:
    rows = (
        _reply("reply:c", AvailabilityState.AVAILABLE, value=0.64),
        _reply("reply:a", AvailabilityState.UNKNOWN, confidence=0.2),
        _reply("reply:b", AvailabilityState.REFUTED, confidence=0.7),
    )
    manifests = {
        json.dumps(evaluate_all_reply_envelope(
            ordering,
            envelope_id="permutation-check",
            generic_seed=99,
        ).to_manifest(), sort_keys=True)
        for ordering in permutations(rows)
    }

    assert len(manifests) == 1


def test_snapshot_resume_preserves_deterministic_counterexample_selection() -> None:
    rows = (
        _reply("available:high", AvailabilityState.AVAILABLE, confidence=0.95, exposure_count=1),
        _reply("available:low", AvailabilityState.AVAILABLE, confidence=0.25, exposure_count=5),
        _reply("unknown:one", AvailabilityState.UNKNOWN, confidence=0.1, exposure_count=4),
        _reply("refuted:one", AvailabilityState.REFUTED, confidence=0.99, exposure_count=100),
    )
    result = evaluate_all_reply_envelope(rows, envelope_id="resume-check", generic_seed=1234)
    resumed = replay_all_reply_envelope(result.snapshot())

    assert result.counterexample_reply_id == "refuted:one"
    assert result.selection["ranked_reply_ids"] == resumed.selection["ranked_reply_ids"]
    assert result.selection["selection_digest"] == resumed.selection["selection_digest"]
    assert resumed.to_manifest() == result.to_manifest()
    selector = CounterexampleChallengeSelector(result.selection["generic_seed"])
    assert selector.select(tuple(reversed(rows))).reply_id == "refuted:one"


def test_unknown_reply_never_opens_positive_gate() -> None:
    result = evaluate_all_reply_envelope([
        _reply("known", AvailabilityState.AVAILABLE, value=0.81),
        _reply("pending", AvailabilityState.UNKNOWN, value=0.77),
    ])

    assert result.state is AvailabilityState.UNKNOWN
    assert result.value == 0.0
    assert result.partial_value == 0.81
    assert result.positive_gate is False
    assert result.can_emit_positive is False
    assert result.all_available_root_state is NodeState.FAILED
    assert result.any_refuted_root_state is NodeState.FAILED


def test_ungrounded_available_reply_never_opens_positive_gate() -> None:
    result = evaluate_all_reply_envelope([
        _reply("known-but-ungrounded", AvailabilityState.AVAILABLE, grounded=False),
    ])

    assert result.state is AvailabilityState.UNKNOWN
    assert result.value == 0.0
    assert result.positive_gate is False
    assert result.all_available_root_state is NodeState.FAILED
    assert result.any_refuted_root_state is NodeState.FAILED


def test_ungrounded_reply_is_ranked_as_an_unknown_challenge() -> None:
    ranked = rank_counterexample_challenges([
        _reply("grounded-available", AvailabilityState.AVAILABLE, grounded=True),
        _reply("ungrounded-available", AvailabilityState.AVAILABLE, grounded=False),
    ])

    assert tuple(item.reply_id for item in ranked) == (
        "ungrounded-available",
        "grounded-available",
    )


def test_ungrounded_refutation_is_not_a_global_veto() -> None:
    result = evaluate_all_reply_envelope([
        _reply("untrusted-refutation", AvailabilityState.REFUTED, grounded=False),
    ])

    assert result.state is AvailabilityState.UNKNOWN
    assert result.value == 0.0
    assert result.positive_gate is False
    assert result.all_available_root_state is NodeState.FAILED
    assert result.any_refuted_root_state is NodeState.FAILED


def test_manifest_requires_explicit_grounding_and_preserves_false() -> None:
    row = _reply("explicit-false", AvailabilityState.AVAILABLE, grounded=False).to_manifest()
    restored = ReplyAuthority.from_manifest(row)
    assert restored.grounded is False

    row.pop("grounded")
    with pytest.raises(ValueError, match="requires explicit grounded"):
        ReplyAuthority.from_manifest(row)


def test_omitted_constructor_grounding_fails_closed() -> None:
    reply = ReplyAuthority(
        "implicit-grounding", AvailabilityState.AVAILABLE, 0.9, 0.8
    )
    assert reply.grounded is False
    assert evaluate_all_reply_envelope([reply]).state is AvailabilityState.UNKNOWN


def test_one_refuted_reply_vetoes_the_all_reply_envelope() -> None:
    result = evaluate_all_reply_envelope([
        _reply("good", AvailabilityState.AVAILABLE, value=0.9),
        _reply("counterexample", AvailabilityState.REFUTED, value=0.1),
    ])

    assert result.state is AvailabilityState.REFUTED
    assert result.value == 0.0
    assert result.partial_value == 0.9
    assert result.positive_gate is False
    assert result.counterexample_reply_id == "counterexample"
    assert result.all_available_root_state is NodeState.FAILED
    assert result.any_refuted_root_state is NodeState.CONFIRMED


def test_empty_reply_set_is_unknown_and_fails_closed() -> None:
    result = evaluate_all_reply_envelope([])

    assert result.state is AvailabilityState.UNKNOWN
    assert result.value == 0.0
    assert result.positive_gate is False
    assert result.counterexample is None
    assert result.all_available_root_state is NodeState.FAILED
    assert result.any_refuted_root_state is NodeState.FAILED


def test_challenge_ranking_is_state_first_and_content_blind() -> None:
    rows = (
        _reply("available:least-exposed", AvailabilityState.AVAILABLE, confidence=0.4, exposure_count=0),
        _reply("available:low-confidence", AvailabilityState.AVAILABLE, confidence=0.1, exposure_count=50),
        _reply("unknown", AvailabilityState.UNKNOWN, confidence=0.99, exposure_count=999),
        _reply("refuted", AvailabilityState.REFUTED, confidence=0.99, exposure_count=999),
    )

    ranked = rank_counterexample_challenges(rows, generic_seed=7)
    assert tuple(item.reply_id for item in ranked) == (
        "refuted",
        "unknown",
        "available:low-confidence",
        "available:least-exposed",
    )
    assert ranked[0].state is AvailabilityState.REFUTED
    assert ranked[2].confidence < ranked[3].confidence
    assert {
        "fen", "mate_label", "outcome", "terminal_kind"
    }.isdisjoint(ReplyAuthority.__dataclass_fields__)
    assert SELECTION_READ_FIELDS == (
        "reply_id", "authority_state", "confidence", "value",
        "grounded", "exposure_count", "generic_seed",
    )


def test_available_challenge_uses_worst_value_before_uncertainty() -> None:
    rows = (
        _reply(
            "available:lower-confidence",
            AvailabilityState.AVAILABLE,
            confidence=0.1,
            value=0.8,
            exposure_count=0,
        ),
        _reply(
            "available:worst-value",
            AvailabilityState.AVAILABLE,
            confidence=0.9,
            value=0.2,
            exposure_count=99,
        ),
    )

    ranked = rank_counterexample_challenges(rows, generic_seed=7)

    assert tuple(item.reply_id for item in ranked) == (
        "available:worst-value",
        "available:lower-confidence",
    )
