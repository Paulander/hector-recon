"""Content-blind lifetime evidence for role-blind topology metabolism."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import random
from typing import Literal

RentProposalMode = Literal["residual_ranked", "rank_shuffled"]


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

    def __post_init__(self) -> None:
        for name in (
            "global_capacity",
            "temporary_challenger_allowance",
            "review_interval_episodes",
            "proposal_interval_episodes",
            "min_eligible_support",
            "consecutive_negative_reviews",
            "max_uncertain_reviews",
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
class CandidateRentStats:
    support: int
    predictive_benefit: float | None
    rent: float | None
    margin_utility: float | None


class LifetimeDecisionReservoir:
    """Uniform Algorithm-R sample over an anonymous decision lifetime."""

    def __init__(self, *, capacity: int, random_seed: int) -> None:
        self.config = ExperienceReservoirConfig(capacity=capacity)
        self._rng = random.Random(random_seed)
        self.records: list[LifetimeDecisionRecord] = []
        self.seen_count = 0
        self.replacement_count = 0
        self.rng_call_count = 0

    def add(self, record: LifetimeDecisionRecord) -> None:
        if record.sequence != self.seen_count:
            raise ValueError("reservoir sequence must be monotonic")
        self.seen_count += 1
        if len(self.records) < self.config.capacity:
            self.records.append(record)
            return
        index = self._rng.randrange(self.seen_count)
        self.rng_call_count += 1
        if index < self.config.capacity:
            self.records[index] = record
            self.replacement_count += 1

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
