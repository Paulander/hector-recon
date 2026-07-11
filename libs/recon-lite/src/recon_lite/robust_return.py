"""Graph-local empirical return distributions and lower-tail estimates.

The mechanism is domain agnostic. It receives only a cell identity and an
observed scalar return. It does not know what constitutes a chess reply, trap,
failure, or correct action.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
from typing import Iterable, Literal


@dataclass(frozen=True)
class RobustReturnConfig:
    capacity: int = 256
    lower_quantile: float = 0.10
    min_observations: int = 2
    confidence_prior: float = 3.0
    prior_return: float = 0.0
    return_min: float = -1.0
    return_max: float = 1.0

    def __post_init__(self) -> None:
        if self.capacity < 2:
            raise ValueError("capacity must be at least two")
        if not 0.0 < self.lower_quantile <= 0.5:
            raise ValueError("lower_quantile must be in (0, 0.5]")
        if self.min_observations < 1:
            raise ValueError("min_observations must be positive")
        if self.confidence_prior <= 0.0:
            raise ValueError("confidence_prior must be positive")
        if self.return_min >= self.return_max:
            raise ValueError("return_min must be smaller than return_max")


@dataclass(frozen=True)
class ReturnEstimate:
    cell_id: str
    observation_count: int
    retained_count: int
    mean: float
    lower_quantile: float
    minimum: float
    maximum: float
    confidence: float
    lower_tail_gap: float
    mean_score: float
    robust_score: float


@dataclass
class ReturnDistributionState:
    cell_id: str
    returns: list[float] = field(default_factory=list)
    observation_count: int = 0


class RobustReturnMemory:
    """Bounded return memory owned by learner cell identities."""

    def __init__(self, config: RobustReturnConfig | None = None) -> None:
        self.config = config or RobustReturnConfig()
        self.states: dict[str, ReturnDistributionState] = {}

    def observe(self, cell_id: str, observed_return: float) -> ReturnEstimate:
        value = float(observed_return)
        if not math.isfinite(value):
            raise ValueError("observed return must be finite")
        value = min(self.config.return_max, max(self.config.return_min, value))
        state = self.states.setdefault(
            str(cell_id), ReturnDistributionState(cell_id=str(cell_id))
        )
        state.observation_count += 1
        state.returns.append(value)
        if len(state.returns) > self.config.capacity:
            self._compress(state)
        return self.estimate(cell_id)

    def estimate(self, cell_id: str) -> ReturnEstimate:
        normalized = str(cell_id)
        state = self.states.get(normalized)
        values = () if state is None else tuple(state.returns)
        observation_count = 0 if state is None else state.observation_count
        if not values:
            prior = float(self.config.prior_return)
            return ReturnEstimate(
                cell_id=normalized,
                observation_count=observation_count,
                retained_count=0,
                mean=prior,
                lower_quantile=prior,
                minimum=prior,
                maximum=prior,
                confidence=0.0,
                lower_tail_gap=0.0,
                mean_score=prior,
                robust_score=prior,
            )
        ordered = sorted(values)
        mean = sum(ordered) / len(ordered)
        rank = max(0, math.ceil(self.config.lower_quantile * len(ordered)) - 1)
        lower = ordered[rank]
        confidence = observation_count / (
            observation_count + self.config.confidence_prior
        )
        if observation_count < self.config.min_observations:
            confidence *= observation_count / self.config.min_observations
        prior = float(self.config.prior_return)
        return ReturnEstimate(
            cell_id=normalized,
            observation_count=observation_count,
            retained_count=len(ordered),
            mean=mean,
            lower_quantile=lower,
            minimum=ordered[0],
            maximum=ordered[-1],
            confidence=confidence,
            lower_tail_gap=mean - lower,
            mean_score=confidence * mean + (1.0 - confidence) * prior,
            robust_score=confidence * lower + (1.0 - confidence) * prior,
        )

    def select(
        self,
        cell_ids: Iterable[str],
        *,
        objective: Literal["mean", "lower_tail"] = "lower_tail",
    ) -> str | None:
        ids = tuple(dict.fromkeys(map(str, cell_ids)))
        if not ids:
            return None
        if objective not in {"mean", "lower_tail"}:
            raise ValueError("objective must be mean or lower_tail")
        estimates = [self.estimate(cell_id) for cell_id in ids]
        return max(
            estimates,
            key=lambda estimate: (
                estimate.mean_score
                if objective == "mean"
                else estimate.robust_score,
                estimate.confidence,
                -estimate.lower_tail_gap,
                estimate.cell_id,
            ),
        ).cell_id

    def snapshot(self) -> dict[str, object]:
        return {
            "schema_version": "recon_robust_return.v1",
            "config": asdict(self.config),
            "states": {
                cell_id: {
                    "observation_count": state.observation_count,
                    "returns": list(state.returns),
                    "estimate": asdict(self.estimate(cell_id)),
                }
                for cell_id, state in sorted(self.states.items())
            },
        }

    def _compress(self, state: ReturnDistributionState) -> None:
        """Retain the lower tail plus deterministic coverage of other returns."""

        ordered = sorted(state.returns)
        tail_count = max(1, math.ceil(self.config.lower_quantile * self.config.capacity))
        tail = ordered[:tail_count]
        remainder = ordered[tail_count:]
        slots = self.config.capacity - len(tail)
        if len(remainder) <= slots:
            state.returns = tail + remainder
            return
        stride = len(remainder) / slots
        coverage = [remainder[min(len(remainder) - 1, int(index * stride))] for index in range(slots)]
        state.returns = tail + coverage
