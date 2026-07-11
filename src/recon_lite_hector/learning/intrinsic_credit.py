"""Outcome-grounded, graph-local credit for hierarchical ReCoN competence.

The host supplies only observable transition facts (terminal outcome and whether a
real or imagined step elapsed). Mature ReCoN subgraphs may expose their
consolidated expected return as a successor-state signal. Upstream cells learn
from that signal through local eligibility traces.

Only mature, causally confirmed, grounded cells may emit value. Grounding
provenance is acyclic, so an ecology cannot reward itself by circular firing.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
from typing import Any, Iterable, Mapping, Optional, Sequence

from recon_lite_hector.nodes import StemCellState, StemCellTerminal
from recon_lite_hector.plasticity.fast import (
    EdgePlasticityState,
    PlasticityConfig,
    apply_fast_update,
    update_eligibility,
)
from recon_lite_hector.graph import Graph


@dataclass(frozen=True)
class IntrinsicCreditConfig:
    """Learning and grounding policy for intrinsic hierarchical credit."""

    gamma: float = 0.97
    real_move_cost: float = 0.01
    virtual_frame_cost: float = 0.001
    eligibility_decay: float = 0.80
    eta_fast: float = 0.20
    eta_slow: float = 0.10
    parent_learning_decay: float = 0.60
    value_min: float = -1.0
    value_max: float = 1.0
    terminal_win_value: float = 1.0
    terminal_draw_value: float = -0.25
    terminal_failure_value: float = -1.0
    min_grounding_evidence: int = 3
    min_causal_confirmations: int = 1
    confidence_prior: float = 3.0
    causal_epsilon: float = 0.01

    def __post_init__(self) -> None:
        if not 0.0 <= self.gamma <= 1.0:
            raise ValueError("gamma must be in [0, 1]")
        if not 0.0 <= self.eligibility_decay <= 1.0:
            raise ValueError("eligibility_decay must be in [0, 1]")
        if not 0.0 < self.parent_learning_decay <= 1.0:
            raise ValueError("parent_learning_decay must be in (0, 1]")
        if self.min_grounding_evidence < 1:
            raise ValueError("min_grounding_evidence must be positive")
        if self.min_causal_confirmations < 1:
            raise ValueError("min_causal_confirmations must be positive")


@dataclass
class CompetenceValueState:
    """Value, eligibility, and grounding owned by one graph competence."""

    cell_id: str
    hierarchy_depth: int = 0
    mature: bool = False
    fast_value: float = 0.0
    slow_value: float = 0.0
    eligibility: float = 0.0
    terminal_evidence: int = 0
    handoff_evidence: int = 0
    causal_confirmations: int = 0
    causal_failures: int = 0
    value_updates: int = 0
    grounding_level: Optional[int] = None
    grounding_ancestors: set[str] = field(default_factory=set)
    last_provider_ids: tuple[str, ...] = ()

    @property
    def grounding_evidence(self) -> int:
        return self.terminal_evidence + self.handoff_evidence

    def confidence(self, config: IntrinsicCreditConfig) -> float:
        evidence = float(self.grounding_evidence)
        return evidence / (evidence + config.confidence_prior)

    def can_emit(self, config: IntrinsicCreditConfig) -> bool:
        return (
            self.mature
            and self.grounding_level is not None
            and self.grounding_evidence >= config.min_grounding_evidence
            and (
                self.causal_confirmations + self.causal_failures
                >= config.min_causal_confirmations
            )
        )

    def to_dict(self, config: IntrinsicCreditConfig) -> dict[str, Any]:
        payload = asdict(self)
        payload["grounding_ancestors"] = sorted(self.grounding_ancestors)
        payload["grounding_evidence"] = self.grounding_evidence
        payload["confidence"] = self.confidence(config)
        payload["can_emit"] = self.can_emit(config)
        return payload


@dataclass(frozen=True)
class Responsibility:
    """A cell's normalized responsibility for the current decision."""

    cell_id: str
    weight: float = 1.0
    parent_distance: int = 0


@dataclass(frozen=True)
class CompetenceSignal:
    """Consolidated value emitted by grounded successor cells."""

    value: float
    confidence: float
    provider_ids: tuple[str, ...]
    grounding_level: int
    grounding_ancestors: tuple[str, ...]


@dataclass(frozen=True)
class CreditEvent:
    """Auditable result of one graph-local credit transition."""

    event_index: int
    decision_id: str
    real_step: bool
    immediate_reward: float
    successor_value: float
    predicted_value: float
    td_error: float
    provider_ids: tuple[str, ...]
    updated_values: Mapping[str, float]
    cycle_rejected: bool = False
    terminal_kind: Optional[str] = None


@dataclass(frozen=True)
class CausalCredit:
    """Paired enabled/disabled evidence used at the maturation boundary."""

    cell_id: str
    enabled_return: float
    disabled_return: float
    delta: float
    valence: str


@dataclass(frozen=True)
class CompetenceGateConfig:
    """Content-blind calibration policy for a child's AVAILABLE signal."""

    learning_rate: float = 0.20
    steps: int = 10_000
    l2: float = 0.001
    threshold: float = 0.50
    min_validation_true_positives: int = 10
    max_validation_false_positives: int = 0
    min_validation_precision: float = 0.95


@dataclass(frozen=True)
class CompetenceGateExample:
    features: tuple[float, ...]
    success: bool


@dataclass
class OutcomeCalibratedCompetenceGate:
    """A mature sigmoid gate trained only from child-policy outcomes.

    Feature meanings are supplied by the caller; this learner sees only bounded
    numeric graph-response statistics and a terminal success/failure bit.
    """

    feature_names: tuple[str, ...]
    scales: tuple[float, ...]
    weights: tuple[float, ...]
    threshold: float
    train_metrics: Mapping[str, Any]
    validation_metrics: Mapping[str, Any]
    mature: bool

    @classmethod
    def fit(
        cls,
        feature_names: Sequence[str],
        train: Sequence[CompetenceGateExample],
        validation: Sequence[CompetenceGateExample],
        config: Optional[CompetenceGateConfig] = None,
    ) -> "OutcomeCalibratedCompetenceGate":
        cfg = config or CompetenceGateConfig()
        names = tuple(map(str, feature_names))
        if not names or not train or not validation:
            raise ValueError("competence gate requires named train and validation examples")
        if any(len(example.features) != len(names) for example in (*train, *validation)):
            raise ValueError("competence gate feature width mismatch")
        positives = sum(int(example.success) for example in train)
        negatives = len(train) - positives
        if positives == 0 or negatives == 0:
            raise ValueError("competence gate training requires both outcome classes")
        scales = tuple(
            max(1.0, max(abs(float(example.features[index])) for example in train))
            for index in range(len(names))
        )
        vectors = [
            (1.0,) + tuple(float(value) / scales[index] for index, value in enumerate(example.features))
            for example in train
        ]
        weights = [0.0] * (len(names) + 1)
        for _step in range(max(1, int(cfg.steps))):
            gradient = [cfg.l2 * weight for weight in weights]
            for vector, example in zip(vectors, train):
                probability = _sigmoid(sum(weight * value for weight, value in zip(weights, vector)))
                class_weight = 0.5 / (positives if example.success else negatives)
                error = (probability - float(example.success)) * class_weight
                for index, value in enumerate(vector):
                    gradient[index] += error * value
            for index in range(len(weights)):
                weights[index] -= cfg.learning_rate * gradient[index]
        provisional = cls(
            feature_names=names,
            scales=scales,
            weights=tuple(weights),
            threshold=cfg.threshold,
            train_metrics={},
            validation_metrics={},
            mature=False,
        )
        provisional.train_metrics = provisional.evaluate(train)
        provisional.validation_metrics = provisional.evaluate(validation)
        validation_metrics = provisional.validation_metrics
        provisional.mature = bool(
            validation_metrics["true_positive"] >= cfg.min_validation_true_positives
            and validation_metrics["false_positive"] <= cfg.max_validation_false_positives
            and validation_metrics["precision"] >= cfg.min_validation_precision
        )
        return provisional

    def probability(self, features: Sequence[float]) -> float:
        if len(features) != len(self.feature_names):
            raise ValueError("competence gate feature width mismatch")
        vector = (1.0,) + tuple(
            float(value) / self.scales[index] for index, value in enumerate(features)
        )
        return _sigmoid(sum(weight * value for weight, value in zip(self.weights, vector)))

    def confirms(self, features: Sequence[float]) -> bool:
        return self.mature and self.probability(features) >= self.threshold

    def evaluate(self, examples: Sequence[CompetenceGateExample]) -> dict[str, Any]:
        true_positive = false_positive = true_negative = false_negative = 0
        for example in examples:
            predicted = self.probability(example.features) >= self.threshold
            true_positive += int(predicted and example.success)
            false_positive += int(predicted and not example.success)
            true_negative += int(not predicted and not example.success)
            false_negative += int(not predicted and example.success)
        predicted_positive = true_positive + false_positive
        actual_positive = true_positive + false_negative
        return {
            "count": len(examples),
            "true_positive": true_positive,
            "false_positive": false_positive,
            "true_negative": true_negative,
            "false_negative": false_negative,
            "precision": 0.0 if predicted_positive == 0 else true_positive / predicted_positive,
            "recall": 0.0 if actual_positive == 0 else true_positive / actual_positive,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature_names": list(self.feature_names),
            "scales": list(self.scales),
            "weights": list(self.weights),
            "threshold": self.threshold,
            "train_metrics": dict(self.train_metrics),
            "validation_metrics": dict(self.validation_metrics),
            "mature": self.mature,
            "learner_visible_labels": False,
        }


@dataclass(frozen=True)
class PrototypeCompetenceGateConfig:
    """Content-blind local voting for a nonlinear AVAILABLE boundary."""

    neighbors: int = 3
    threshold: float = 0.50
    min_validation_true_positives: int = 10
    max_validation_false_positives: int = 0
    min_validation_precision: float = 0.95


@dataclass
class OutcomeCalibratedPrototypeGate:
    """Outcome-grounded prototype cells with local inverse-distance voting."""

    feature_names: tuple[str, ...]
    offsets: tuple[float, ...]
    scales: tuple[float, ...]
    prototypes: tuple[tuple[float, ...], ...]
    outcomes: tuple[bool, ...]
    neighbors: int
    threshold: float
    train_metrics: Mapping[str, Any]
    validation_metrics: Mapping[str, Any]
    mature: bool

    @classmethod
    def fit(
        cls,
        feature_names: Sequence[str],
        train: Sequence[CompetenceGateExample],
        validation: Sequence[CompetenceGateExample],
        config: Optional[PrototypeCompetenceGateConfig] = None,
    ) -> "OutcomeCalibratedPrototypeGate":
        cfg = config or PrototypeCompetenceGateConfig()
        names = tuple(map(str, feature_names))
        if not names or not train or not validation:
            raise ValueError("prototype gate requires named train and validation examples")
        if any(len(example.features) != len(names) for example in (*train, *validation)):
            raise ValueError("prototype gate feature width mismatch")
        positives = sum(int(example.success) for example in train)
        if positives == 0 or positives == len(train):
            raise ValueError("prototype gate training requires both outcome classes")
        offsets = tuple(
            min(float(example.features[index]) for example in train)
            for index in range(len(names))
        )
        scales = tuple(
            max(
                1e-9,
                max(float(example.features[index]) for example in train)
                - offsets[index],
            )
            for index in range(len(names))
        )
        prototypes = tuple(
            tuple(
                (float(value) - offsets[index]) / scales[index]
                for index, value in enumerate(example.features)
            )
            for example in train
        )
        provisional = cls(
            feature_names=names,
            offsets=offsets,
            scales=scales,
            prototypes=prototypes,
            outcomes=tuple(bool(example.success) for example in train),
            neighbors=max(1, min(int(cfg.neighbors), len(train))),
            threshold=float(cfg.threshold),
            train_metrics={},
            validation_metrics={},
            mature=False,
        )
        provisional.train_metrics = provisional.evaluate(train)
        provisional.validation_metrics = provisional.evaluate(validation)
        metrics = provisional.validation_metrics
        provisional.mature = bool(
            metrics["true_positive"] >= cfg.min_validation_true_positives
            and metrics["false_positive"] <= cfg.max_validation_false_positives
            and metrics["precision"] >= cfg.min_validation_precision
        )
        return provisional

    def probability(self, features: Sequence[float]) -> float:
        if len(features) != len(self.feature_names):
            raise ValueError("prototype gate feature width mismatch")
        vector = tuple(
            (float(value) - self.offsets[index]) / self.scales[index]
            for index, value in enumerate(features)
        )
        distances = sorted(
            (
                sum((value - prototype[index]) ** 2 for index, value in enumerate(vector)),
                outcome,
                prototype_index,
            )
            for prototype_index, (prototype, outcome) in enumerate(
                zip(self.prototypes, self.outcomes)
            )
        )
        nearest = distances[: self.neighbors]
        exact = [outcome for distance, outcome, _index in nearest if distance <= 1e-15]
        if exact:
            return sum(float(outcome) for outcome in exact) / len(exact)
        weights = [1.0 / max(1e-12, distance**0.5) for distance, _outcome, _index in nearest]
        return sum(
            weight * float(outcome)
            for weight, (_distance, outcome, _index) in zip(weights, nearest)
        ) / sum(weights)

    def confirms(self, features: Sequence[float]) -> bool:
        return self.mature and self.probability(features) >= self.threshold

    def evaluate(self, examples: Sequence[CompetenceGateExample]) -> dict[str, Any]:
        true_positive = false_positive = true_negative = false_negative = 0
        for example in examples:
            predicted = self.probability(example.features) >= self.threshold
            true_positive += int(predicted and example.success)
            false_positive += int(predicted and not example.success)
            true_negative += int(not predicted and not example.success)
            false_negative += int(not predicted and example.success)
        predicted_positive = true_positive + false_positive
        actual_positive = true_positive + false_negative
        return {
            "count": len(examples),
            "true_positive": true_positive,
            "false_positive": false_positive,
            "true_negative": true_negative,
            "false_negative": false_negative,
            "precision": 0.0 if predicted_positive == 0 else true_positive / predicted_positive,
            "recall": 0.0 if actual_positive == 0 else true_positive / actual_positive,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_family": "outcome_calibrated_prototype_cells",
            "feature_names": list(self.feature_names),
            "offsets": list(self.offsets),
            "scales": list(self.scales),
            "neighbors": self.neighbors,
            "threshold": self.threshold,
            "prototype_count": len(self.prototypes),
            "positive_prototype_count": sum(map(int, self.outcomes)),
            "negative_prototype_count": len(self.outcomes) - sum(map(int, self.outcomes)),
            "prototype_sha256": _hash_prototypes(self.prototypes, self.outcomes),
            "train_metrics": dict(self.train_metrics),
            "validation_metrics": dict(self.validation_metrics),
            "mature": self.mature,
            "learner_visible_labels": False,
        }


class IntrinsicCreditEngine:
    """Local TD/eligibility engine with recursively grounded child value."""

    def __init__(self, config: Optional[IntrinsicCreditConfig] = None) -> None:
        self.config = config or IntrinsicCreditConfig()
        self.states: dict[str, CompetenceValueState] = {}
        self.event_index = 0
        self.events: list[CreditEvent] = []

    def register(
        self,
        cell_id: str,
        *,
        mature: bool = False,
        hierarchy_depth: int = 0,
        initial_fast_value: float = 0.0,
        initial_slow_value: float = 0.0,
    ) -> CompetenceValueState:
        """Register a graph competence without granting grounding evidence."""

        normalized = str(cell_id)
        if normalized in self.states:
            state = self.states[normalized]
            state.mature = bool(mature)
            state.hierarchy_depth = max(0, int(hierarchy_depth))
            return state
        state = CompetenceValueState(
            cell_id=normalized,
            mature=bool(mature),
            hierarchy_depth=max(0, int(hierarchy_depth)),
            fast_value=self._clip(initial_fast_value),
            slow_value=self._clip(initial_slow_value),
        )
        self.states[normalized] = state
        return state

    def register_stem_cell(
        self,
        cell: StemCellTerminal,
        *,
        hierarchy_depth: int = 0,
    ) -> CompetenceValueState:
        """Bind value state to the existing stem-cell lifecycle substrate."""

        mature = cell.state in {StemCellState.MATURE, StemCellState.SPECIALIZED}
        return self.register(cell.cell_id, mature=mature, hierarchy_depth=hierarchy_depth)

    def set_mature(self, cell_id: str, mature: bool = True) -> None:
        self._state(cell_id).mature = bool(mature)

    def begin_episode(self) -> None:
        """Clear transient responsibility while retaining learned values."""

        for state in self.states.values():
            state.eligibility = 0.0

    def observe_responsibility(self, responsibilities: Sequence[Responsibility]) -> None:
        """Decay all traces, then add a size-normalized decision trace."""

        for state in self.states.values():
            state.eligibility *= self.config.eligibility_decay
        total = sum(abs(float(item.weight)) for item in responsibilities)
        if total <= 0.0:
            return
        for item in responsibilities:
            state = self._state(item.cell_id)
            distance = max(0, int(item.parent_distance))
            local_weight = float(item.weight) / total
            local_weight *= self.config.parent_learning_decay**distance
            state.eligibility += local_weight

    def successor_signal(
        self,
        successor_ids: Iterable[str],
        *,
        recipient_id: Optional[str] = None,
    ) -> tuple[Optional[CompetenceSignal], bool]:
        """Aggregate mature grounded child values, rejecting circular provenance."""

        providers: list[CompetenceValueState] = []
        cycle_rejected = False
        for cell_id in dict.fromkeys(map(str, successor_ids)):
            state = self.states.get(cell_id)
            if state is None or not state.can_emit(self.config):
                continue
            if recipient_id is not None and (
                state.cell_id == recipient_id or recipient_id in state.grounding_ancestors
            ):
                cycle_rejected = True
                continue
            providers.append(state)
        if not providers:
            return None, cycle_rejected

        confidences = [provider.confidence(self.config) for provider in providers]
        total_confidence = sum(confidences)
        if total_confidence <= 0.0:
            return None, cycle_rejected
        value = sum(
            provider.slow_value * confidence
            for provider, confidence in zip(providers, confidences)
        ) / total_confidence
        ancestors: set[str] = set()
        for provider in providers:
            ancestors.add(provider.cell_id)
            ancestors.update(provider.grounding_ancestors)
        return (
            CompetenceSignal(
                value=self._clip(value),
                confidence=min(1.0, total_confidence / len(providers)),
                provider_ids=tuple(sorted(provider.cell_id for provider in providers)),
                grounding_level=1 + max(int(provider.grounding_level or 0) for provider in providers),
                grounding_ancestors=tuple(sorted(ancestors)),
            ),
            cycle_rejected,
        )

    def transition(
        self,
        decision_id: str,
        *,
        responsibilities: Optional[Sequence[Responsibility]] = None,
        successor_ids: Sequence[str] = (),
        terminal_kind: Optional[str] = None,
        terminal_value: Optional[float] = None,
        real_step: bool = True,
        prediction_override: Optional[float] = None,
    ) -> CreditEvent:
        """Apply one real/imagined transition and return its local TD signal."""

        decision = self._state(decision_id)
        if not real_step and (terminal_kind is not None or terminal_value is not None):
            raise ValueError("virtual frames cannot create terminal grounding evidence")
        if responsibilities is None:
            responsibilities = (Responsibility(decision_id),)
        self.observe_responsibility(responsibilities)

        signal: Optional[CompetenceSignal] = None
        cycle_rejected = False
        if terminal_kind is None and terminal_value is None:
            signal, cycle_rejected = self.successor_signal(successor_ids, recipient_id=decision_id)

        cost = self.config.real_move_cost if real_step else self.config.virtual_frame_cost
        immediate = -float(cost)
        if terminal_value is not None:
            immediate += self._clip(terminal_value)
        elif terminal_kind is not None:
            immediate += self._terminal_value(terminal_kind)

        successor_value = 0.0 if signal is None else signal.value
        predicted = (
            decision.fast_value
            if prediction_override is None
            else float(prediction_override)
        )
        if not math.isfinite(predicted):
            raise ValueError("prediction_override must be finite")
        td_error = self._clip(immediate + self.config.gamma * successor_value - predicted)

        updated: dict[str, float] = {}
        for state in self.states.values():
            if abs(state.eligibility) <= 1e-15:
                continue
            depth_rate = self.config.parent_learning_decay ** max(0, state.hierarchy_depth)
            state.fast_value = self._clip(
                state.fast_value + self.config.eta_fast * depth_rate * td_error * state.eligibility
            )
            state.value_updates += 1
            updated[state.cell_id] = state.fast_value

        credited_states = [state for state in self.states.values() if abs(state.eligibility) > 1e-15]
        if terminal_kind is not None or terminal_value is not None:
            for state in credited_states:
                state.terminal_evidence += 1
                state.grounding_level = 0
                state.grounding_ancestors.clear()
                state.last_provider_ids = ()
        elif signal is not None:
            for state in credited_states:
                if state.cell_id in signal.grounding_ancestors:
                    continue
                state.handoff_evidence += 1
                if state.grounding_level is None or signal.grounding_level < state.grounding_level:
                    state.grounding_level = signal.grounding_level
                    state.grounding_ancestors = set(signal.grounding_ancestors)
                state.last_provider_ids = signal.provider_ids

        self.event_index += 1
        event = CreditEvent(
            event_index=self.event_index,
            decision_id=decision_id,
            real_step=bool(real_step),
            immediate_reward=immediate,
            successor_value=successor_value,
            predicted_value=predicted,
            td_error=td_error,
            provider_ids=() if signal is None else signal.provider_ids,
            updated_values=updated,
            cycle_rejected=cycle_rejected,
            terminal_kind=terminal_kind,
        )
        self.events.append(event)
        return event

    def record_correlation(self, cell: StemCellTerminal, signal: float) -> str:
        """Record association without granting maturation XP."""

        valence = self._valence(signal)
        cell.record_candidate_correlation(valence)
        return valence

    def record_paired_intervention(
        self,
        cell_id: str,
        *,
        enabled_return: float,
        disabled_return: float,
        stem_cell: Optional[StemCellTerminal] = None,
        cycle: Optional[int] = None,
    ) -> CausalCredit:
        """Record the only credit that may satisfy the maturation boundary."""

        state = self._state(cell_id)
        delta = float(enabled_return) - float(disabled_return)
        valence = self._valence(delta)
        if valence == "positive":
            state.causal_confirmations += 1
        elif valence == "negative":
            state.causal_failures += 1
        if stem_cell is not None:
            if stem_cell.state == StemCellState.TRIAL:
                stem_cell.update_xp(delta)
            else:
                stem_cell.record_candidate_intervention(valence, cycle=cycle)
        return CausalCredit(
            cell_id=cell_id,
            enabled_return=float(enabled_return),
            disabled_return=float(disabled_return),
            delta=delta,
            valence=valence,
        )

    def consolidate(self, cell_ids: Optional[Iterable[str]] = None) -> dict[str, float]:
        """Move grounded, causally confirmed fast values into slow memory."""

        selected = self.states.values() if cell_ids is None else (self._state(cell_id) for cell_id in cell_ids)
        deltas: dict[str, float] = {}
        for state in selected:
            if not state.can_emit(self.config):
                continue
            delta = self.config.eta_slow * (state.fast_value - state.slow_value)
            state.slow_value = self._clip(state.slow_value + delta)
            deltas[state.cell_id] = delta
        return deltas

    def snapshot(self) -> dict[str, Any]:
        return {
            "config": asdict(self.config),
            "states": {cell_id: state.to_dict(self.config) for cell_id, state in sorted(self.states.items())},
            "event_count": len(self.events),
            "events": [asdict(event) for event in self.events],
        }

    def terminal_value(self, terminal_kind: str) -> float:
        """Map an observable terminal fact to the configured bounded anchor."""

        return self._terminal_value(terminal_kind)

    def _state(self, cell_id: str) -> CompetenceValueState:
        try:
            return self.states[str(cell_id)]
        except KeyError as exc:
            raise KeyError(f"unregistered competence: {cell_id}") from exc

    def _clip(self, value: float) -> float:
        return max(self.config.value_min, min(self.config.value_max, float(value)))

    def _valence(self, signal: float) -> str:
        if signal > self.config.causal_epsilon:
            return "positive"
        if signal < -self.config.causal_epsilon:
            return "negative"
        return "neutral"

    def _terminal_value(self, terminal_kind: str) -> float:
        normalized = str(terminal_kind).strip().lower()
        if normalized in {"win", "mate", "checkmate", "success"}:
            return self.config.terminal_win_value
        if normalized in {"draw", "horizon", "max_plies"}:
            return self.config.terminal_draw_value
        if normalized in {
            "failure",
            "loss",
            "rook_loss",
            "stalemate",
            "illegal",
            "illegal_move",
            "catastrophe",
        }:
            return self.config.terminal_failure_value
        raise ValueError(f"unknown terminal kind: {terminal_kind}")


def apply_credit_event_to_edges(
    event: CreditEvent,
    *,
    edge_state: dict[str, EdgePlasticityState],
    graph: Graph,
    fired_edges: Iterable[dict[str, str]],
    plasticity_config: PlasticityConfig,
    eta_eff: Optional[float] = None,
) -> dict[str, float]:
    """Feed intrinsic TD error into the existing M3 edge-plasticity substrate.

    The intrinsic engine does not own a second set of routing weights. It emits
    one bounded local error; established ReCoN edge traces decide where that
    error is applied.
    """

    update_eligibility(
        edge_state,
        fired_edges,
        lambda_decay=plasticity_config.lambda_decay,
    )
    return apply_fast_update(
        edge_state,
        graph,
        reward_tick=event.td_error,
        eta_eff=plasticity_config.eta_tick if eta_eff is None else float(eta_eff),
        config=plasticity_config,
    )


def _sigmoid(value: float) -> float:
    bounded = max(-30.0, min(30.0, float(value)))
    return 1.0 / (1.0 + math.exp(-bounded))


def _hash_prototypes(
    prototypes: Sequence[Sequence[float]],
    outcomes: Sequence[bool],
) -> str:
    import hashlib
    import json

    payload = {
        "prototypes": [list(map(float, row)) for row in prototypes],
        "outcomes": list(map(bool, outcomes)),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
