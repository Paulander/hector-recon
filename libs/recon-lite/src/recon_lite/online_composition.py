"""Anonymous online nomination and causal validation of pair composites."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import random
from typing import Iterable, Literal

CandidateState = Literal["trial", "mature", "pruned"]
ProposalMode = Literal["residual_ranked", "matched_random"]


@dataclass(frozen=True)
class OnlineCompositionConfig:
    learning_rate: float = 0.08
    proposal_interval: int = 128
    min_pair_support: int = 16
    max_candidates: int = 4
    max_total_proposals: int | None = None
    burn_in_activations: int = 8
    confirmation_activations: int = 32
    causal_margin: float = 0.01
    resource_cost: float = 0.002
    trial_max_age: int = 512
    shared_learning_after_maturity_scale: float = 1.0
    prediction_min: float = -1.0
    prediction_max: float = 1.0

    def __post_init__(self) -> None:
        if not 0.0 < self.learning_rate <= 1.0:
            raise ValueError("learning_rate must be in (0, 1]")
        for name in (
            "proposal_interval", "min_pair_support", "max_candidates",
            "confirmation_activations", "trial_max_age",
        ):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be positive")
        if self.burn_in_activations < 0:
            raise ValueError("burn_in_activations cannot be negative")
        if (
            self.max_total_proposals is not None
            and self.max_total_proposals < self.max_candidates
        ):
            raise ValueError(
                "max_total_proposals cannot be smaller than max_candidates"
            )
        if self.causal_margin < 0.0 or self.resource_cost < 0.0:
            raise ValueError("costs cannot be negative")
        if not 0.0 <= self.shared_learning_after_maturity_scale <= 1.0:
            raise ValueError(
                "shared_learning_after_maturity_scale must be in [0, 1]"
            )
        if self.prediction_min >= self.prediction_max:
            raise ValueError("prediction_min must be smaller than prediction_max")


@dataclass
class PairEvidence:
    support: int = 0
    residual_sum: float = 0.0


@dataclass
class CompositeCandidate:
    members: tuple[str, str]
    born_observation: int
    proposal_score: float
    support_at_proposal: int
    state: CandidateState = "trial"
    shadow_weight: float = 0.0
    activation_count: int = 0
    confirmation_count: int = 0
    disabled_error_sum: float = 0.0
    enabled_error_sum: float = 0.0
    paired_improvement: float | None = None
    net_improvement: float | None = None
    decision_observation: int | None = None


class OnlinePairCompositionLearner:
    """Additive atom learner whose trial composites remain shadow-only."""

    def __init__(
        self, *, proposal_mode: ProposalMode, random_seed: int,
        config: OnlineCompositionConfig | None = None,
    ) -> None:
        if proposal_mode not in {"residual_ranked", "matched_random"}:
            raise ValueError("unsupported proposal_mode")
        self.config = config or OnlineCompositionConfig()
        self.proposal_mode = proposal_mode
        self._rng = random.Random(random_seed)
        self.observation_count = 0
        self.bias = 0.0
        self.primitive_weights: dict[str, float] = {}
        self.pair_evidence: dict[tuple[str, str], PairEvidence] = {}
        self.candidates: list[CompositeCandidate] = []
        self._proposed_pairs: set[tuple[str, str]] = set()
        self.global_residual_sum = 0.0
        self.trial_prediction_influence_count = 0
        self.max_observed_live_candidate_count = 0
        self.first_maturity_observation: int | None = None
        self.shared_update_events_before_maturity = 0
        self.shared_update_events_after_maturity = 0
        self.candidate_weight_updates_after_maturity = 0

    def predict(self, active_atom_ids: Iterable[str]) -> float:
        atoms = self._normalize_atoms(active_atom_ids)
        raw = self.bias + sum(self.primitive_weights.get(atom, 0.0) for atom in atoms)
        active = set(atoms)
        for candidate in self.candidates:
            if candidate.state == "mature" and set(candidate.members) <= active:
                raw += candidate.shadow_weight
        return self._clip(raw)

    def observe(self, active_atom_ids: Iterable[str], target: float) -> float:
        atoms = self._normalize_atoms(active_atom_ids)
        outcome = float(target)
        if not math.isfinite(outcome):
            raise ValueError("target must be finite")
        outcome = self._clip(outcome)
        active = set(atoms)
        prediction = self.predict(atoms)
        residual = outcome - prediction
        self.observation_count += 1
        self.global_residual_sum += residual

        for index, left in enumerate(atoms):
            for right in atoms[index + 1:]:
                evidence = self.pair_evidence.setdefault((left, right), PairEvidence())
                evidence.support += 1
                evidence.residual_sum += residual

        mature_before_update = any(
            candidate.state == "mature" for candidate in self.candidates
        )
        for candidate in self.candidates:
            if candidate.state != "trial" or not set(candidate.members) <= active:
                continue
            candidate.activation_count += 1
            shadow_prediction = self._clip(prediction + candidate.shadow_weight)
            if candidate.activation_count > self.config.burn_in_activations:
                candidate.disabled_error_sum += (outcome - prediction) ** 2
                candidate.enabled_error_sum += (outcome - shadow_prediction) ** 2
                candidate.confirmation_count += 1
            candidate.shadow_weight = self._clip(
                candidate.shadow_weight
                + self.config.learning_rate * (outcome - shadow_prediction)
            )
            if mature_before_update:
                self.candidate_weight_updates_after_maturity += 1
            if candidate.confirmation_count >= self.config.confirmation_activations:
                self._decide(candidate)

        has_mature_candidate = any(
            candidate.state == "mature" for candidate in self.candidates
        )
        if has_mature_candidate and self.first_maturity_observation is None:
            self.first_maturity_observation = self.observation_count
        shared_scale = (
            self.config.shared_learning_after_maturity_scale
            if has_mature_candidate
            else 1.0
        )
        update = self.config.learning_rate * residual / max(1, len(atoms) + 1)
        update *= shared_scale
        if update != 0.0:
            if has_mature_candidate:
                self.shared_update_events_after_maturity += 1
            else:
                self.shared_update_events_before_maturity += 1
        self.bias = self._clip(self.bias + update)
        for atom in atoms:
            self.primitive_weights[atom] = self._clip(
                self.primitive_weights.get(atom, 0.0) + update
            )
        for candidate in self.candidates:
            if candidate.state == "mature" and set(candidate.members) <= active:
                candidate.shadow_weight = self._clip(
                    candidate.shadow_weight + self.config.learning_rate * residual
                )
                self.candidate_weight_updates_after_maturity += 1

        for candidate in self.candidates:
            if (
                candidate.state == "trial"
                and self.observation_count - candidate.born_observation
                >= self.config.trial_max_age
            ):
                candidate.state = "pruned"
                candidate.decision_observation = self.observation_count
        if (
            self.observation_count % self.config.proposal_interval == 0
            and self._live_candidate_count() < self.config.max_candidates
            and len(self.candidates) < self._total_proposal_limit()
        ):
            self._propose()
            self.max_observed_live_candidate_count = max(
                self.max_observed_live_candidate_count,
                self._live_candidate_count(),
            )
        return prediction

    def snapshot(self) -> dict[str, object]:
        return {
            "schema_version": "recon_online_pair_composition.v1",
            "config": asdict(self.config),
            "proposal_mode": self.proposal_mode,
            "observation_count": self.observation_count,
            "bias": self.bias,
            "primitive_weights": dict(sorted(self.primitive_weights.items())),
            "candidate_count": len(self.candidates),
            "candidate_state_counts": {
                state: sum(
                    candidate.state == state for candidate in self.candidates
                )
                for state in ("trial", "mature", "pruned")
            },
            "live_candidate_count": self._live_candidate_count(),
            "max_observed_live_candidate_count": (
                self.max_observed_live_candidate_count
            ),
            "first_maturity_observation": self.first_maturity_observation,
            "shared_update_events_before_maturity": (
                self.shared_update_events_before_maturity
            ),
            "shared_update_events_after_maturity": (
                self.shared_update_events_after_maturity
            ),
            "candidate_weight_updates_after_maturity": (
                self.candidate_weight_updates_after_maturity
            ),
            "total_proposal_limit": self._total_proposal_limit(),
            "trial_prediction_influence_count": self.trial_prediction_influence_count,
            "candidates": [asdict(candidate) for candidate in self.candidates],
        }

    def _propose(self) -> None:
        eligible = sorted(
            pair for pair, evidence in self.pair_evidence.items()
            if evidence.support >= self.config.min_pair_support
            and pair not in self._proposed_pairs
        )
        if not eligible:
            return
        global_mean = self.global_residual_sum / self.observation_count

        def score(pair: tuple[str, str]) -> float:
            evidence = self.pair_evidence[pair]
            pair_mean = evidence.residual_sum / evidence.support
            return abs(pair_mean - global_mean) * math.sqrt(evidence.support)

        pair = (
            max(eligible, key=lambda item: (score(item), item))
            if self.proposal_mode == "residual_ranked"
            else self._rng.choice(eligible)
        )
        evidence = self.pair_evidence[pair]
        self._proposed_pairs.add(pair)
        self.candidates.append(CompositeCandidate(
            members=pair,
            born_observation=self.observation_count,
            proposal_score=score(pair),
            support_at_proposal=evidence.support,
        ))

    def _decide(self, candidate: CompositeCandidate) -> None:
        disabled = candidate.disabled_error_sum / candidate.confirmation_count
        enabled = candidate.enabled_error_sum / candidate.confirmation_count
        improvement = disabled - enabled
        net = improvement - self.config.resource_cost
        candidate.paired_improvement = improvement
        candidate.net_improvement = net
        candidate.state = "mature" if net > self.config.causal_margin else "pruned"
        candidate.decision_observation = self.observation_count

    def _clip(self, value: float) -> float:
        return min(self.config.prediction_max, max(self.config.prediction_min, value))

    def _live_candidate_count(self) -> int:
        return sum(
            candidate.state in {"trial", "mature"}
            for candidate in self.candidates
        )

    def _total_proposal_limit(self) -> int:
        configured = self.config.max_total_proposals
        return (
            self.config.max_candidates
            if configured is None
            else configured
        )

    @staticmethod
    def _normalize_atoms(active_atom_ids: Iterable[str]) -> tuple[str, ...]:
        return tuple(sorted(set(map(str, active_atom_ids))))
