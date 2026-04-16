"""Reusable terminal-space triplet primitives.

These classes keep the learned KRK triplet idea explicit and testable:

    before terminal state -> actuator intent(delta_s) -> after verification

They intentionally do not know about chess boards. Domain code supplies terminal
snapshots as ``{sensor_id: value}`` dictionaries and can then use these small
objects inside ReCoN predicates, training loops, or structural growth managers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping, Optional

import numpy as np


@dataclass(frozen=True)
class TripletMatch:
    """Result from matching a terminal-space condition."""

    matched: bool
    score: float
    observed: Dict[str, float] = field(default_factory=dict)
    target: Dict[str, float] = field(default_factory=dict)
    details: Dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class BeforeCondition:
    """Checks whether current terminal outputs match a learned precondition."""

    sensor_ids: tuple[str, ...]
    prototype: Optional[Dict[str, float]] = None
    max_distance: Optional[float] = None
    normalize: bool = False

    def evaluate(self, current: Mapping[str, float]) -> TripletMatch:
        observed = _subset(current, self.sensor_ids)
        if len(observed) != len(self.sensor_ids):
            return TripletMatch(False, 0.0, observed=observed)
        if self.prototype is None:
            return TripletMatch(True, 1.0, observed=observed)

        distance = terminal_distance(observed, self.prototype, normalize=self.normalize)
        matched = self.max_distance is None or distance <= self.max_distance
        return TripletMatch(
            matched=matched,
            score=1.0 / (1.0 + distance),
            observed=observed,
            target=dict(self.prototype),
            details={"distance": distance},
        )


@dataclass(frozen=True)
class ActuatorIntent:
    """Scores whether an observed or simulated terminal delta matches intent."""

    targets: tuple[str, ...]
    goal_delta: Dict[str, float]
    min_similarity: float = -1.0

    def score_delta(self, delta: Mapping[str, float]) -> TripletMatch:
        observed = _subset(delta, self.targets)
        target = _subset(self.goal_delta, self.targets)
        if len(observed) != len(target) or not observed:
            return TripletMatch(False, 0.0, observed=observed, target=target)

        similarity = cosine_similarity(
            [observed[sid] for sid in self.targets],
            [target[sid] for sid in self.targets],
        )
        return TripletMatch(
            matched=similarity >= self.min_similarity,
            score=similarity,
            observed=observed,
            target=target,
            details={"similarity": similarity},
        )

    def score_transition(
        self,
        before: Mapping[str, float],
        after: Mapping[str, float],
    ) -> TripletMatch:
        return self.score_delta(terminal_delta(before, after, self.targets))


@dataclass(frozen=True)
class AfterCondition:
    """Verifies that the actual after-state followed the learned delta."""

    targets: tuple[str, ...]
    goal_delta: Dict[str, float]
    min_similarity: float = 0.0
    max_error: Optional[float] = None

    def evaluate(
        self,
        before: Mapping[str, float],
        after: Mapping[str, float],
    ) -> TripletMatch:
        intent = ActuatorIntent(self.targets, self.goal_delta, self.min_similarity)
        match = intent.score_transition(before, after)
        if not match.observed or not match.target:
            return match

        error = terminal_distance(match.observed, match.target)
        matched = match.matched and (self.max_error is None or error <= self.max_error)
        details = dict(match.details)
        details["error"] = error
        return TripletMatch(
            matched=matched,
            score=match.score,
            observed=match.observed,
            target=match.target,
            details=details,
        )


@dataclass(frozen=True)
class CreditPolicy:
    """Small default credit rule for terminal-space goal progress."""

    progress_weight: float = 1.0
    success_reward: float = 1.0
    failure_penalty: float = -1.0

    def score(
        self,
        *,
        before_goal_distance: Optional[float],
        after_goal_distance: Optional[float],
        success: bool = False,
    ) -> float:
        if success:
            return self.success_reward
        if before_goal_distance is None or after_goal_distance is None:
            return 0.0
        progress = before_goal_distance - after_goal_distance
        if progress <= 0.0:
            return self.failure_penalty * abs(progress)
        return self.progress_weight * progress


@dataclass(frozen=True)
class TripletSpec:
    """Composable before/action/after/credit bundle for a learned leg."""

    before: BeforeCondition
    actuator: ActuatorIntent
    after: AfterCondition
    credit: CreditPolicy = field(default_factory=CreditPolicy)


def terminal_delta(
    before: Mapping[str, float],
    after: Mapping[str, float],
    sensor_ids: Iterable[str],
) -> Dict[str, float]:
    """Return ``after - before`` for sensor ids present in both snapshots."""
    delta: Dict[str, float] = {}
    for sid in sensor_ids:
        if sid in before and sid in after:
            delta[sid] = float(after[sid]) - float(before[sid])
    return delta


def terminal_distance(
    current: Mapping[str, float],
    target: Mapping[str, float],
    *,
    normalize: bool = False,
) -> float:
    """L2 distance over shared terminal ids."""
    keys = sorted(set(current) & set(target))
    if not keys:
        return float("inf")
    cur = np.array([float(current[k]) for k in keys], dtype=np.float32)
    tgt = np.array([float(target[k]) for k in keys], dtype=np.float32)
    if normalize:
        cur = cur / (np.linalg.norm(cur) + 1e-6)
        tgt = tgt / (np.linalg.norm(tgt) + 1e-6)
    return float(np.linalg.norm(cur - tgt))


def cosine_similarity(a: Iterable[float], b: Iterable[float]) -> float:
    """Compute padded cosine similarity for terminal-space vectors."""
    a_arr = np.array(list(a), dtype=np.float32)
    b_arr = np.array(list(b), dtype=np.float32)
    if a_arr.size == 0 or b_arr.size == 0:
        return 0.0
    if a_arr.size != b_arr.size:
        max_len = max(a_arr.size, b_arr.size)
        a_arr = np.pad(a_arr, (0, max_len - a_arr.size))
        b_arr = np.pad(b_arr, (0, max_len - b_arr.size))
    norm_a = float(np.linalg.norm(a_arr))
    norm_b = float(np.linalg.norm(b_arr))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / (norm_a * norm_b))


def _subset(values: Mapping[str, float], keys: Iterable[str]) -> Dict[str, float]:
    return {key: float(values[key]) for key in keys if key in values}
