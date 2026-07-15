"""Content-blind lifetime evidence for role-blind topology metabolism."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import random
from typing import Literal

RentProposalMode = Literal["residual_ranked", "rank_shuffled"]
LifecycleGraceMode = Literal[
    "two_review",
    "fixed_six",
    "support_conditioned_six",
]
ExplorationRequestMode = Literal[
    "ordinary_random",
    "support_directed",
    "support_shuffled",
    "exact_support_directed",
    "exact_support_shuffled",
]


@dataclass(frozen=True)
class ExperienceReservoirConfig:
    capacity: int = 2048

    def __post_init__(self) -> None:
        if self.capacity < 1:
            raise ValueError("reservoir capacity must be positive")


@dataclass(frozen=True)
class CausalRentConfig:
    global_capacity: int = 32
    temporary_challenger_allowance: int = 1
    review_interval_episodes: int = 512
    proposal_interval_episodes: int = 128
    min_eligible_support: int = 32
    resource_cost: float = 0.002
    promotion_margin: float = 0.01
    retirement_margin: float = 0.01
    replacement_margin: float = 0.01
    consecutive_negative_reviews: int = 2
    max_uncertain_reviews: int = 2
    proposal_mode: RentProposalMode = "residual_ranked"
    exploration_request_mode: ExplorationRequestMode = "ordinary_random"
    lifecycle_grace_mode: LifecycleGraceMode = "two_review"
    grace_max_trial_reviews: int = 6
    grace_progress_window_reviews: int = 2

    def __post_init__(self) -> None:
        for name in (
            "global_capacity",
            "temporary_challenger_allowance",
            "review_interval_episodes",
            "proposal_interval_episodes",
            "min_eligible_support",
            "consecutive_negative_reviews",
            "max_uncertain_reviews",
            "grace_max_trial_reviews",
            "grace_progress_window_reviews",
        ):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be positive")
        for name in (
            "resource_cost",
            "promotion_margin",
            "retirement_margin",
            "replacement_margin",
        ):
            value = getattr(self, name)
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative")
        if self.proposal_mode not in {
            "residual_ranked", "rank_shuffled",
        }:
            raise ValueError("unsupported causal-rent proposal mode")
        if self.lifecycle_grace_mode not in {
            "two_review",
            "fixed_six",
            "support_conditioned_six",
        }:
            raise ValueError("unsupported lifecycle grace mode")
        if self.grace_max_trial_reviews != 6:
            raise ValueError("lifecycle grace review cap is frozen at six")
        if self.grace_progress_window_reviews != 2:
            raise ValueError("lifecycle grace progress window is frozen at two")
        if self.exploration_request_mode not in {
            "ordinary_random",
            "support_directed",
            "support_shuffled",
            "exact_support_directed",
            "exact_support_shuffled",
        }:
            raise ValueError(
                "unsupported causal-rent exploration request mode"
            )

    @property
    def safety_ceiling(self) -> int:
        return self.global_capacity + self.temporary_challenger_allowance


@dataclass(frozen=True)
class LifetimeDecisionRecord:
    sequence: int
    action_id: str
    active_atom_ids: tuple[str, ...]
    legal_action_ids: tuple[str, ...]
    decision_scores: tuple[tuple[str, float], ...]
    target: float
    discount: float
    elapsed_steps: int


@dataclass(frozen=True)
class LifetimeReservoirMutation:
    """Unambiguous result of one Algorithm-R insertion attempt."""

    attempted_record: LifetimeDecisionRecord
    retained: bool
    inserted_record: LifetimeDecisionRecord | None
    evicted_record: LifetimeDecisionRecord | None
    retained_index: int | None


def record_supports_candidate(
    record: LifetimeDecisionRecord,
    action_id: str,
    immutable_members: tuple[str, ...],
) -> bool:
    """Return exact anonymous support eligibility used by causal-rent review."""
    return (
        record.action_id == action_id
        and len(record.legal_action_ids) >= 2
        and set(immutable_members) <= set(record.active_atom_ids)
    )


@dataclass(frozen=True)
class CandidateRentStats:
    support: int
    predictive_benefit: float | None
    rent: float | None
    margin_utility: float | None
    mean_margin_with: float | None
    mean_margin_without: float | None
    margin_sign_flip_rate: float | None


class LifetimeDecisionReservoir:
    """Uniform Algorithm-R sample over an anonymous decision lifetime."""

    def __init__(self, *, capacity: int, random_seed: int) -> None:
        self.config = ExperienceReservoirConfig(capacity=capacity)
        self._rng = random.Random(random_seed)
        self.records: list[LifetimeDecisionRecord] = []
        self.seen_count = 0
        self.replacement_count = 0
        self.rng_call_count = 0

    def add(
        self, record: LifetimeDecisionRecord
    ) -> LifetimeReservoirMutation:
        if record.sequence != self.seen_count:
            raise ValueError("reservoir sequence must be monotonic")
        self.seen_count += 1
        if len(self.records) < self.config.capacity:
            retained_index = len(self.records)
            self.records.append(record)
            return LifetimeReservoirMutation(
                attempted_record=record,
                retained=True,
                inserted_record=record,
                evicted_record=None,
                retained_index=retained_index,
            )
        index = self._rng.randrange(self.seen_count)
        self.rng_call_count += 1
        if index >= self.config.capacity:
            return LifetimeReservoirMutation(
                attempted_record=record,
                retained=False,
                inserted_record=None,
                evicted_record=None,
                retained_index=None,
            )
        evicted = self.records[index]
        self.records[index] = record
        self.replacement_count += 1
        return LifetimeReservoirMutation(
            attempted_record=record,
            retained=True,
            inserted_record=record,
            evicted_record=evicted,
            retained_index=index,
        )

    def snapshot(self) -> dict[str, object]:
        serialized = [asdict(record) for record in self.records]
        encoded = json.dumps(
            serialized, sort_keys=True, separators=(",", ":")
        ).encode()
        return {
            "schema_version": "recon_lifetime_decision_reservoir.v1",
            "capacity": self.config.capacity,
            "seen_count": self.seen_count,
            "retained_count": len(self.records),
            "replacement_count": self.replacement_count,
            "rng_call_count": self.rng_call_count,
            "records_sha256": hashlib.sha256(encoded).hexdigest(),
        }
