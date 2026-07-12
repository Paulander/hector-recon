"""Anonymous online nomination and causal validation of pair composites."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import random
from typing import Iterable, Literal

CandidateState = Literal["trial", "mature", "pruned"]
ProposalMode = Literal["residual_ranked", "matched_random"]
SharedLearningSchedule = Literal["fixed", "mature_activation_decay"]
ResidualUpdateMode = Literal[
    "broadcast",
    "responsibility_conserving",
    "responsibility_shuffled",
    "shared_frozen",
]


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
    shared_learning_schedule: SharedLearningSchedule = "fixed"
    adaptive_shared_learning_floor: float = 0.10
    adaptive_consolidation_activations: int = 1024
    residual_update_mode: ResidualUpdateMode = "broadcast"
    allocation_importance_epsilon: float = 0.01
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
        if self.shared_learning_schedule not in {
            "fixed", "mature_activation_decay",
        }:
            raise ValueError("unsupported shared_learning_schedule")
        if not 0.0 <= self.adaptive_shared_learning_floor <= 1.0:
            raise ValueError(
                "adaptive_shared_learning_floor must be in [0, 1]"
            )
        if self.adaptive_consolidation_activations < 1:
            raise ValueError(
                "adaptive_consolidation_activations must be positive"
            )
        if self.residual_update_mode not in {
            "broadcast",
            "responsibility_conserving",
            "responsibility_shuffled",
            "shared_frozen",
        }:
            raise ValueError("unsupported residual_update_mode")
        if self.allocation_importance_epsilon <= 0.0:
            raise ValueError(
                "allocation_importance_epsilon must be positive"
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

    BIAS_COMPONENT_ID = "bias_terminal"

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
        self.mature_evidence_activation_count = 0
        self.current_shared_learning_scale = 1.0
        self.minimum_shared_learning_scale = 1.0
        self.shared_learning_scale_sum_after_maturity = 0.0
        self.shared_learning_scale_observations_after_maturity = 0
        self.component_importance: dict[str, float] = {
            self.BIAS_COMPONENT_ID: 0.0
        }
        self.parameter_clip_counts = {
            "bias": 0,
            "primitive": 0,
            "trial": 0,
            "mature": 0,
        }
        self.allocation_update_count = 0
        self.allocation_component_opportunity_count = 0
        self.allocation_rng_call_count = 0
        self.allocation_missing_responsibility_count = 0
        self.allocation_stale_component_count = 0
        self.allocation_requested_l1_sum = 0.0
        self.allocation_actual_l1_sum = 0.0
        self.allocation_max_budget_error = 0.0
        self.allocation_share_sum = {
            "bias": 0.0,
            "primitive": 0.0,
            "trial": 0.0,
            "mature": 0.0,
        }

    def predict(self, active_atom_ids: Iterable[str]) -> float:
        atoms = self._normalize_atoms(active_atom_ids)
        raw = self.bias + sum(self.primitive_weights.get(atom, 0.0) for atom in atoms)
        active = set(atoms)
        for candidate in self.candidates:
            if candidate.state == "mature" and set(candidate.members) <= active:
                raw += candidate.shadow_weight
        return self._clip(raw)

    def observe(
        self,
        active_atom_ids: Iterable[str],
        target: float,
        *,
        decision_component_ids: Iterable[str] | None = None,
        decision_component_importance: dict[str, float] | None = None,
    ) -> float:
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
        active_trials: list[tuple[int, CompositeCandidate]] = []
        for candidate_index, candidate in enumerate(self.candidates):
            if candidate.state != "trial" or not set(candidate.members) <= active:
                continue
            active_trials.append((candidate_index, candidate))
            candidate.activation_count += 1
            shadow_prediction = self._clip(prediction + candidate.shadow_weight)
            if candidate.activation_count > self.config.burn_in_activations:
                candidate.disabled_error_sum += (outcome - prediction) ** 2
                candidate.enabled_error_sum += (outcome - shadow_prediction) ** 2
                candidate.confirmation_count += 1
            if self.config.residual_update_mode not in {
                "responsibility_conserving",
                "responsibility_shuffled",
            }:
                requested = self.config.learning_rate * (
                    outcome - shadow_prediction
                )
                actual = self._apply_component_update(
                    self._candidate_component_id(candidate_index),
                    requested,
                    residual=residual,
                )
                if mature_before_update and actual != 0.0:
                    self.candidate_weight_updates_after_maturity += 1

        allocation_mode = self.config.residual_update_mode in {
            "responsibility_conserving",
            "responsibility_shuffled",
        }
        if not allocation_mode:
            for _, candidate in active_trials:
                if (
                    candidate.confirmation_count
                    >= self.config.confirmation_activations
                ):
                    self._decide(candidate)

        has_mature_candidate = any(
            candidate.state == "mature" for candidate in self.candidates
        )
        if has_mature_candidate and self.first_maturity_observation is None:
            self.first_maturity_observation = self.observation_count
        active_mature_candidate = any(
            candidate.state == "mature"
            and set(candidate.members) <= active
            for candidate in self.candidates
        )
        if (
            self.config.shared_learning_schedule
            == "mature_activation_decay"
            and active_mature_candidate
        ):
            self.mature_evidence_activation_count += 1
        shared_scale = self._shared_learning_scale(
            has_mature_candidate=has_mature_candidate
        )
        self.current_shared_learning_scale = shared_scale
        if has_mature_candidate:
            self.minimum_shared_learning_scale = min(
                self.minimum_shared_learning_scale,
                shared_scale,
            )
            self.shared_learning_scale_sum_after_maturity += shared_scale
            self.shared_learning_scale_observations_after_maturity += 1

        if allocation_mode:
            self._apply_conserved_update(
                active=active,
                residual=residual,
                decision_component_ids=decision_component_ids,
                decision_component_importance=decision_component_importance,
            )
            for _, candidate in active_trials:
                if (
                    candidate.confirmation_count
                    >= self.config.confirmation_activations
                ):
                    self._decide(candidate)
        else:
            self._apply_broadcast_update(
                atoms=atoms,
                active=active,
                residual=residual,
                has_mature_candidate=has_mature_candidate,
            )
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
            "mature_evidence_activation_count": (
                self.mature_evidence_activation_count
            ),
            "current_shared_learning_scale": (
                self.current_shared_learning_scale
            ),
            "minimum_shared_learning_scale": (
                self.minimum_shared_learning_scale
            ),
            "mean_shared_learning_scale_after_maturity": (
                self.shared_learning_scale_sum_after_maturity
                / self.shared_learning_scale_observations_after_maturity
                if self.shared_learning_scale_observations_after_maturity
                else 1.0
            ),
            "shared_learning_scale_observations_after_maturity": (
                self.shared_learning_scale_observations_after_maturity
            ),
            "component_importance": dict(sorted(self.component_importance.items())),
            "parameter_clip_counts": dict(self.parameter_clip_counts),
            "allocation_update_count": self.allocation_update_count,
            "allocation_component_opportunity_count": (
                self.allocation_component_opportunity_count
            ),
            "allocation_rng_call_count": self.allocation_rng_call_count,
            "allocation_missing_responsibility_count": (
                self.allocation_missing_responsibility_count
            ),
            "allocation_stale_component_count": (
                self.allocation_stale_component_count
            ),
            "allocation_requested_l1_sum": self.allocation_requested_l1_sum,
            "allocation_actual_l1_sum": self.allocation_actual_l1_sum,
            "allocation_max_budget_error": self.allocation_max_budget_error,
            "allocation_share_sum": dict(self.allocation_share_sum),
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

    def _shared_learning_scale(self, *, has_mature_candidate: bool) -> float:
        if not has_mature_candidate:
            return 1.0
        if self.config.shared_learning_schedule == "fixed":
            return self.config.shared_learning_after_maturity_scale
        progress = min(
            1.0,
            self.mature_evidence_activation_count
            / self.config.adaptive_consolidation_activations,
        )
        floor = self.config.adaptive_shared_learning_floor
        return 1.0 - (1.0 - floor) * progress

    def active_component_importance(
        self, active_atom_ids: Iterable[str]
    ) -> dict[str, float]:
        atoms = self._normalize_atoms(active_atom_ids)
        active = set(atoms)
        component_ids = [self.BIAS_COMPONENT_ID, *atoms]
        for index, candidate in enumerate(self.candidates):
            if (
                candidate.state in {"trial", "mature"}
                and set(candidate.members) <= active
            ):
                component_ids.append(self._candidate_component_id(index))
        return {
            component_id: self.component_importance.get(component_id, 0.0)
            for component_id in component_ids
        }

    def component_contributions(
        self, active_atom_ids: Iterable[str]
    ) -> dict[str, float]:
        atoms = self._normalize_atoms(active_atom_ids)
        active = set(atoms)
        contributions = {self.BIAS_COMPONENT_ID: self.bias}
        contributions.update({
            atom: self.primitive_weights.get(atom, 0.0)
            for atom in atoms
        })
        for index, candidate in enumerate(self.candidates):
            if (
                candidate.state in {"trial", "mature"}
                and set(candidate.members) <= active
            ):
                contributions[
                    self._candidate_component_id(index)
                ] = candidate.shadow_weight
        return contributions

    def component_states(
        self, active_atom_ids: Iterable[str]
    ) -> dict[str, str]:
        atoms = self._normalize_atoms(active_atom_ids)
        active = set(atoms)
        states = {self.BIAS_COMPONENT_ID: "bias"}
        states.update({atom: "primitive" for atom in atoms})
        for index, candidate in enumerate(self.candidates):
            if (
                candidate.state in {"trial", "mature"}
                and set(candidate.members) <= active
            ):
                states[
                    self._candidate_component_id(index)
                ] = candidate.state
        return states

    def _apply_broadcast_update(
        self,
        *,
        atoms: tuple[str, ...],
        active: set[str],
        residual: float,
        has_mature_candidate: bool,
    ) -> None:
        shared_scale = self._shared_learning_scale(
            has_mature_candidate=has_mature_candidate
        )
        if self.config.residual_update_mode == "shared_frozen":
            shared_scale = 0.0
        update = self.config.learning_rate * residual / max(1, len(atoms) + 1)
        update *= shared_scale
        if update != 0.0:
            if has_mature_candidate:
                self.shared_update_events_after_maturity += 1
            else:
                self.shared_update_events_before_maturity += 1
        self._apply_component_update(
            self.BIAS_COMPONENT_ID, update, residual=residual
        )
        for atom in atoms:
            self._apply_component_update(atom, update, residual=residual)
        for index, candidate in enumerate(self.candidates):
            if candidate.state == "mature" and set(candidate.members) <= active:
                actual = self._apply_component_update(
                    self._candidate_component_id(index),
                    self.config.learning_rate * residual,
                    residual=residual,
                )
                if actual != 0.0:
                    self.candidate_weight_updates_after_maturity += 1

    def _apply_conserved_update(
        self,
        *,
        active: set[str],
        residual: float,
        decision_component_ids: Iterable[str] | None,
        decision_component_importance: dict[str, float] | None,
    ) -> None:
        current = self.component_states(active)
        if decision_component_ids is None or decision_component_importance is None:
            self.allocation_missing_responsibility_count += 1
            component_ids = tuple(sorted(current))
            importance = {
                component_id: self.component_importance.get(component_id, 0.0)
                for component_id in component_ids
            }
        else:
            component_ids = tuple(sorted(set(decision_component_ids)))
            importance = dict(decision_component_importance)
        eligible = []
        for component_id in component_ids:
            if component_id not in current:
                self.allocation_stale_component_count += 1
                continue
            if component_id not in importance:
                self.allocation_missing_responsibility_count += 1
                continue
            eligible.append(component_id)
        if not eligible:
            self.allocation_missing_responsibility_count += 1
            return
        values = [max(0.0, float(importance[item])) for item in eligible]
        shuffled = list(values)
        for index in range(len(shuffled) - 1, 0, -1):
            swap = self._rng.randrange(index + 1)
            self.allocation_rng_call_count += 1
            shuffled[index], shuffled[swap] = shuffled[swap], shuffled[index]
        if self.config.residual_update_mode == "responsibility_shuffled":
            values = shuffled
        epsilon = self.config.allocation_importance_epsilon
        unnormalized = [1.0 / (epsilon + value) for value in values]
        total = sum(unnormalized)
        shares = [value / total for value in unnormalized]
        requested = [
            self.config.learning_rate * residual * share
            for share in shares
        ]
        expected = self.config.learning_rate * residual
        error = abs(sum(requested) - expected)
        self.allocation_max_budget_error = max(
            self.allocation_max_budget_error, error
        )
        self.allocation_update_count += 1
        self.allocation_component_opportunity_count += len(eligible)
        self.allocation_requested_l1_sum += sum(map(abs, requested))
        actual_l1 = 0.0
        for component_id, share, delta_weight in zip(
            eligible, shares, requested
        ):
            component_class = current[component_id]
            self.allocation_share_sum[component_class] += share
            actual = self._apply_component_update(
                component_id, delta_weight, residual=residual
            )
            actual_l1 += abs(actual)
            if component_class in {"trial", "mature"} and actual != 0.0:
                self.candidate_weight_updates_after_maturity += int(
                    any(
                        candidate.state == "mature"
                        for candidate in self.candidates
                    )
                )
        self.allocation_actual_l1_sum += actual_l1
        if requested and expected != 0.0:
            if any(candidate.state == "mature" for candidate in self.candidates):
                self.shared_update_events_after_maturity += 1
            else:
                self.shared_update_events_before_maturity += 1

    def _apply_component_update(
        self,
        component_id: str,
        requested: float,
        *,
        residual: float,
    ) -> float:
        if component_id == self.BIAS_COMPONENT_ID:
            before = self.bias
            raw = before + requested
            after = self._clip(raw)
            if after != raw:
                self.parameter_clip_counts["bias"] += 1
            self.bias = after
            component_class = "bias"
        elif component_id.startswith("composite_"):
            index = int(component_id.removeprefix("composite_"))
            if index >= len(self.candidates):
                self.allocation_stale_component_count += 1
                return 0.0
            candidate = self.candidates[index]
            before = candidate.shadow_weight
            raw = before + requested
            after = self._clip(raw)
            component_class = candidate.state
            if after != raw:
                self.parameter_clip_counts[component_class] += 1
            candidate.shadow_weight = after
        else:
            before = self.primitive_weights.get(component_id, 0.0)
            raw = before + requested
            after = self._clip(raw)
            if after != raw:
                self.parameter_clip_counts["primitive"] += 1
            self.primitive_weights[component_id] = after
            component_class = "primitive"
        actual = after - before
        self.component_importance[component_id] = (
            self.component_importance.get(component_id, 0.0)
            + abs(residual * actual)
        )
        return actual

    @staticmethod
    def _candidate_component_id(index: int) -> str:
        return f"composite_{index}"

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
