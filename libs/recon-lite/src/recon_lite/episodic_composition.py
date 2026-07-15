"""Graph-backed action values with terminal-only episodic responsibility."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import random
from typing import Iterable

from .causal_rent import (
    CandidateRentStats,
    CausalRentConfig,
    ExperienceReservoirConfig,
    LifetimeDecisionRecord,
    LifetimeDecisionReservoir,
    LifetimeReservoirMutation,
    record_supports_candidate,
)
from .graph import Graph, LinkType, Node, NodeType
from .online_composition import (
    OnlineCompositionConfig,
    OnlinePairCompositionLearner,
)


@dataclass(frozen=True)
class EpisodicCompositionConfig:
    exploration_rate: float = 0.15
    discount: float = 0.97

    def __post_init__(self) -> None:
        if not 0.0 <= self.exploration_rate <= 1.0:
            raise ValueError("exploration_rate must be in [0, 1]")
        if not 0.0 <= self.discount <= 1.0:
            raise ValueError("discount must be in [0, 1]")


@dataclass
class DecisionTrace:
    action_id: str
    active_atom_ids: tuple[str, ...]
    graph_prediction: float
    active_graph_nodes: tuple[str, ...]
    component_importance: tuple[tuple[str, float], ...] = ()
    raw_component_contributions: tuple[tuple[str, float], ...] = ()
    component_states: tuple[tuple[str, str], ...] = ()
    legal_action_ids: tuple[str, ...] = ()
    decision_scores: tuple[tuple[str, float], ...] = ()
    elapsed_steps: int = 0


class GraphBackedCompositionChannel:
    """Expose an online composition learner through real graph activations."""

    ROOT_ID = "action_score"
    BIAS_ID = "bias_terminal"
    EVIDENCE_DEFICIT_PREFIX = "evidence_deficit_"
    EVIDENCE_REQUEST_PREFIX = "evidence_request_"
    GRACE_TERMINAL_PREFIXES = {
        "evidence_deficit": "grace_evidence_deficit_",
        "evidence_progress": "grace_evidence_progress_",
        "request_active": "grace_request_active_",
        "grace_budget_remaining": "grace_budget_remaining_",
    }
    DEFER_PRUNING_REQUEST_PREFIX = "defer_pruning_request_"

    def __init__(
        self,
        *,
        random_seed: int,
        composition_config: OnlineCompositionConfig | None = None,
    ) -> None:
        self.learner = OnlinePairCompositionLearner(
            proposal_mode="residual_ranked",
            random_seed=random_seed,
            config=composition_config,
        )
        self.graph = Graph()
        self.graph.add_node(Node(self.ROOT_ID, NodeType.SCRIPT))
        self.graph.add_node(Node(self.BIAS_ID, NodeType.TERMINAL))
        self.graph.add_hierarchy_pair(self.ROOT_ID, self.BIAS_ID)
        self.primitive_node_ids: set[str] = set()
        self.candidate_node_ids: dict[int, str] = {}
        self.evidence_deficit_node_ids: dict[int, str] = {}
        self.evidence_request_node_ids: dict[int, str] = {}
        self.lifecycle_grace_mode = "two_review"
        self.grace_terminal_node_ids: dict[int, dict[str, str]] = {}
        self.defer_pruning_request_node_ids: dict[int, str] = {}
        self.graph_prediction_count = 0
        self.graph_prediction_mismatch_count = 0
        self.trial_root_edge_count = 0
        self._sync_weights()

    def predict(
        self,
        active_atom_ids: Iterable[str],
        *,
        include_mature_composites: bool = True,
        disabled_candidate_indices: frozenset[int] = frozenset(),
    ) -> float:
        atoms = self._normalize(active_atom_ids)
        for atom in atoms:
            self._ensure_primitive(atom)
        self._set_activations(atoms)
        raw = 0.0
        for child_id, weight in self.graph.get_sub_children(self.ROOT_ID):
            if not include_mature_composites and child_id.startswith("composite_"):
                continue
            if (
                child_id.startswith("composite_")
                and int(child_id.removeprefix("composite_"))
                in disabled_candidate_indices
            ):
                continue
            raw += weight * self.graph.nodes[child_id].activation.value
        prediction = self._clip(raw)
        if include_mature_composites and not disabled_candidate_indices:
            self.graph_prediction_count += 1
            if not math.isclose(
                prediction,
                self.learner.predict(atoms),
                rel_tol=0.0,
                abs_tol=1e-12,
            ):
                self.graph_prediction_mismatch_count += 1
        return prediction

    def observe(
        self,
        active_atom_ids: Iterable[str],
        target: float,
        *,
        decision_component_ids: Iterable[str] | None = None,
        decision_component_importance: dict[str, float] | None = None,
    ) -> float:
        atoms = self._normalize(active_atom_ids)
        graph_prediction = self.predict(atoms)
        learner_prediction = self.learner.observe(
            atoms,
            target,
            decision_component_ids=decision_component_ids,
            decision_component_importance=decision_component_importance,
        )
        if not math.isclose(
            graph_prediction, learner_prediction, rel_tol=0.0, abs_tol=1e-12
        ):
            self.graph_prediction_mismatch_count += 1
        self._sync_topology()
        self._sync_weights()
        return graph_prediction

    def active_responsibility(
        self, active_atom_ids: Iterable[str]
    ) -> tuple[str, ...]:
        atoms = self._normalize(active_atom_ids)
        self.predict(atoms)
        return tuple(
            sorted(
                node_id
                for node_id, node in self.graph.nodes.items()
                if node_id != self.ROOT_ID and node.activation.value > 0.5
            )
        )

    def decision_responsibility(
        self, active_atom_ids: Iterable[str]
    ) -> dict[str, tuple[tuple[str, object], ...]]:
        atoms = self._normalize(active_atom_ids)
        active_nodes = self.active_responsibility(atoms)
        importance = self.learner.active_component_importance(atoms)
        contributions = self.learner.component_contributions(atoms)
        states = self.learner.component_states(atoms)
        return {
            "active_graph_nodes": tuple(
                (node_id, True) for node_id in active_nodes
            ),
            "component_importance": tuple(
                (node_id, importance[node_id])
                for node_id in active_nodes
            ),
            "raw_component_contributions": tuple(
                (node_id, contributions[node_id])
                for node_id in active_nodes
            ),
            "component_states": tuple(
                (node_id, states[node_id])
                for node_id in active_nodes
            ),
        }

    def score_decomposition(
        self, active_atom_ids: Iterable[str]
    ) -> dict[str, object]:
        atoms = self._normalize(active_atom_ids)
        contributions = self.learner.component_contributions(atoms)
        states = self.learner.component_states(atoms)
        behavioral = {
            component_id: value
            for component_id, value in contributions.items()
            if states[component_id] != "trial"
        }
        raw = sum(behavioral.values())
        clipped = self._clip(raw)
        return {
            "raw_score": raw,
            "clipped_score": clipped,
            "output_clipped": raw != clipped,
            "contributions": dict(sorted(behavioral.items())),
            "shadow_trial_contributions": dict(sorted(
                (component_id, value)
                for component_id, value in contributions.items()
                if states[component_id] == "trial"
            )),
            "component_states": dict(sorted(states.items())),
        }

    def snapshot(self) -> dict[str, object]:
        state_counts = {"trial": 0, "mature": 0, "pruned": 0}
        for candidate in self.learner.candidates:
            state_counts[candidate.state] += 1
        return {
            "schema_version": "recon_graph_backed_composition.v1",
            "learner": self.learner.snapshot(),
            "graph": self.graph.to_snapshot(),
            "candidate_state_counts": state_counts,
            "graph_prediction_count": self.graph_prediction_count,
            "graph_prediction_mismatch_count": self.graph_prediction_mismatch_count,
            "trial_root_edge_count": self.trial_root_edge_count,
            "evidence_deficit_node_ids": dict(
                sorted(self.evidence_deficit_node_ids.items())
            ),
            "evidence_request_node_ids": dict(
                sorted(self.evidence_request_node_ids.items())
            ),
            "lifecycle_grace_mode": self.lifecycle_grace_mode,
            "grace_terminal_node_ids": {
                index: dict(sorted(node_ids.items()))
                for index, node_ids in sorted(
                    self.grace_terminal_node_ids.items()
                )
            },
            "defer_pruning_request_node_ids": dict(
                sorted(self.defer_pruning_request_node_ids.items())
            ),
        }

    def configure_lifecycle_grace(self, mode: str) -> None:
        if mode not in {
            "two_review",
            "fixed_six",
            "support_conditioned_six",
        }:
            raise ValueError("unsupported lifecycle grace mode")
        self.lifecycle_grace_mode = mode
        self._sync_topology()

    def sync_external_lifecycle(self) -> None:
        """Reflect externally reviewed candidate state in the real graph."""
        self._sync_topology()
        self._sync_weights()

    def emit_evidence_requests(
        self,
        active_atom_ids: Iterable[str],
        *,
        action_id: str,
        measurement_source: str,
        min_eligible_support: int,
        terminals_enabled: bool = True,
    ) -> tuple[dict[str, object], ...]:
        """Measure local state and return only graph-emitted request strengths."""
        if measurement_source not in {"activation", "exact_reservoir"}:
            raise ValueError("unsupported evidence measurement source")
        if min_eligible_support < 1:
            raise ValueError("min_eligible_support must be positive")
        self._sync_topology()
        normalized_deficits: dict[int, float] = {}
        for candidate_index, terminal_id in sorted(
            self.evidence_deficit_node_ids.items()
        ):
            candidate = self.learner.candidates[candidate_index]
            measured_support = (
                candidate.activation_count
                if measurement_source == "activation"
                else candidate.rent_evidence_support
            )
            deficit = max(0, min_eligible_support - measured_support)
            terminal = self.graph.nodes[terminal_id]
            terminal.meta["measurement_source"] = measurement_source
            terminal.meta["measured_support"] = measured_support
            terminal.meta["evidence_deficit"] = deficit
            normalized_deficits[candidate_index] = (
                deficit / min_eligible_support
                if terminals_enabled
                else 0.0
            )
        self._set_activations(
            self._normalize(active_atom_ids),
            evidence_deficits=normalized_deficits,
        )
        emissions = []
        for candidate_index, request_id in sorted(
            self.evidence_request_node_ids.items()
        ):
            strength = int(round(
                self.graph.nodes[request_id].activation.value
                * min_eligible_support
            ))
            if strength <= 0:
                continue
            terminal_id = self.evidence_deficit_node_ids[candidate_index]
            terminal = self.graph.nodes[terminal_id]
            request = self.graph.nodes[request_id]
            emissions.append({
                "action_id": action_id,
                "candidate_index": candidate_index,
                "candidate_node_id": request.meta["candidate_node_id"],
                "request_node_id": request_id,
                "terminal_node_id": terminal_id,
                "request_strength": strength,
                "measured_support": terminal.meta["measured_support"],
                "measurement_source": measurement_source,
            })
        return tuple(emissions)

    def record_evidence_request(self, request_node_id: str) -> None:
        """Record an emitted graph request without exposing fields to the bus."""
        candidate_index = int(
            self.graph.nodes[request_node_id].meta["candidate_index"]
        )
        self.learner.candidates[
            candidate_index
        ].exploration_request_count += 1

    def record_evidence_probe_benefit(self, request_node_id: str) -> None:
        """Record that the emitted request shared the selected action."""
        candidate_index = int(
            self.graph.nodes[request_node_id].meta["candidate_index"]
        )
        self.learner.candidates[
            candidate_index
        ].exploration_probe_benefit_count += 1

    def evidence_request_topology_signature(self) -> dict[str, object]:
        """Return measurement-independent request node and edge identities."""
        node_ids = tuple(sorted(
            (*self.evidence_deficit_node_ids.values(),
             *self.evidence_request_node_ids.values())
        ))
        node_set = set(node_ids)
        edges = tuple(sorted(
            (edge.src, edge.dst, edge.ltype.value)
            for edge in self.graph.edges
            if edge.src in node_set or edge.dst in node_set
        ))
        return {"node_ids": node_ids, "edges": edges}

    def _ensure_primitive(self, atom_id: str) -> None:
        if atom_id in self.primitive_node_ids:
            return
        if (
            atom_id in {self.ROOT_ID, self.BIAS_ID}
            or atom_id.startswith("composite_")
            or atom_id.startswith(self.EVIDENCE_DEFICIT_PREFIX)
            or atom_id.startswith(self.EVIDENCE_REQUEST_PREFIX)
            or atom_id.startswith(self.DEFER_PRUNING_REQUEST_PREFIX)
            or any(
                atom_id.startswith(prefix)
                for prefix in self.GRACE_TERMINAL_PREFIXES.values()
            )
        ):
            raise ValueError("atom ID collides with reserved graph namespace")
        self.graph.add_node(Node(atom_id, NodeType.TERMINAL))
        self.graph.add_hierarchy_pair(self.ROOT_ID, atom_id)
        self.primitive_node_ids.add(atom_id)
        self._sync_weights()

    def _sync_topology(self) -> None:
        for index, candidate in enumerate(self.learner.candidates):
            node_id = self.candidate_node_ids.get(index)
            if candidate.state == "pruned":
                self._remove_evidence_request_topology(index)
                self._remove_lifecycle_grace_topology(index)
                if node_id is not None:
                    self.graph.remove_node(node_id)
                    del self.candidate_node_ids[index]
                continue
            for member in candidate.members:
                self._ensure_primitive(member)
            if node_id is None:
                node_id = f"composite_{index}"
                self.graph.add_node(
                    Node(
                        node_id,
                        NodeType.SCRIPT,
                        meta={
                            "aggregation": "and",
                            "candidate_index": index,
                            "candidate_state": candidate.state,
                            "members": candidate.members,
                        },
                    )
                )
                for member in candidate.members:
                    self.graph.add_hierarchy_pair(node_id, member)
                self.candidate_node_ids[index] = node_id
            self.graph.nodes[node_id].meta["candidate_state"] = candidate.state
            if candidate.state == "trial":
                self._ensure_evidence_request_topology(index)
                if self.lifecycle_grace_mode == "two_review":
                    self._remove_lifecycle_grace_topology(index)
                else:
                    self._ensure_lifecycle_grace_topology(index)
            else:
                self._remove_evidence_request_topology(index)
                self._remove_lifecycle_grace_topology(index)
                if self.graph.parent_of(node_id) is None:
                    self.graph.add_hierarchy_pair(self.ROOT_ID, node_id)

        for index, node_id in self.candidate_node_ids.items():
            candidate = self.learner.candidates[index]
            if candidate.state == "trial" and self.graph.parent_of(node_id) is not None:
                self.trial_root_edge_count += 1

    def _ensure_evidence_request_topology(self, candidate_index: int) -> None:
        if candidate_index in self.evidence_request_node_ids:
            return
        candidate = self.learner.candidates[candidate_index]
        candidate_node_id = self.candidate_node_ids[candidate_index]
        terminal_id = f"{self.EVIDENCE_DEFICIT_PREFIX}{candidate_index}"
        request_id = f"{self.EVIDENCE_REQUEST_PREFIX}{candidate_index}"
        self.graph.add_node(Node(
            terminal_id,
            NodeType.TERMINAL,
            meta={
                "internal_terminal": "EVIDENCE_DEFICIT",
                "frame_scope": "persistent_internal_real",
                "candidate_index": candidate_index,
                "candidate_node_id": candidate_node_id,
            },
        ))
        self.graph.add_node(Node(
            request_id,
            NodeType.SCRIPT,
            meta={
                "aggregation": "and",
                "request_kind": "exploration",
                "candidate_index": candidate_index,
                "candidate_node_id": candidate_node_id,
            },
        ))
        self.graph.add_hierarchy_pair(request_id, terminal_id)
        for member in candidate.members:
            self.graph.add_hierarchy_pair(request_id, member)
        self.evidence_deficit_node_ids[candidate_index] = terminal_id
        self.evidence_request_node_ids[candidate_index] = request_id

    def _ensure_lifecycle_grace_topology(self, candidate_index: int) -> None:
        if candidate_index in self.defer_pruning_request_node_ids:
            return
        candidate_node_id = self.candidate_node_ids[candidate_index]
        terminal_ids = {
            name: f"{prefix}{candidate_index}"
            for name, prefix in self.GRACE_TERMINAL_PREFIXES.items()
        }
        request_id = (
            f"{self.DEFER_PRUNING_REQUEST_PREFIX}{candidate_index}"
        )
        for name, terminal_id in terminal_ids.items():
            self.graph.add_node(Node(
                terminal_id,
                NodeType.TERMINAL,
                meta={
                    "internal_terminal": name.upper(),
                    "frame_scope": "persistent_internal_real",
                    "candidate_index": candidate_index,
                    "candidate_node_id": candidate_node_id,
                },
            ))
        self.graph.add_node(Node(
            request_id,
            NodeType.SCRIPT,
            meta={
                "aggregation": "and",
                "request_kind": "defer_pruning",
                "candidate_index": candidate_index,
                "candidate_node_id": candidate_node_id,
            },
        ))
        for terminal_id in terminal_ids.values():
            self.graph.add_hierarchy_pair(request_id, terminal_id)
        self.grace_terminal_node_ids[candidate_index] = terminal_ids
        self.defer_pruning_request_node_ids[candidate_index] = request_id

    def _remove_lifecycle_grace_topology(
        self, candidate_index: int
    ) -> None:
        request_id = self.defer_pruning_request_node_ids.pop(
            candidate_index, None
        )
        terminal_ids = self.grace_terminal_node_ids.pop(
            candidate_index, {}
        )
        if request_id is not None:
            self.graph.remove_node(request_id)
        for terminal_id in terminal_ids.values():
            self.graph.remove_node(terminal_id)

    def emit_defer_pruning_request(
        self,
        candidate_index: int,
        *,
        min_eligible_support: int,
        max_trial_reviews: int,
    ) -> tuple[dict[str, object] | None, dict[str, object]]:
        """Measure candidate-local grace state and return graph emission only."""
        if self.lifecycle_grace_mode == "two_review":
            raise RuntimeError("two-review mode has no grace topology")
        self._sync_topology()
        candidate = self.learner.candidates[candidate_index]
        if candidate.state != "trial":
            raise RuntimeError("only trials can emit defer-pruning requests")
        terminal_ids = self.grace_terminal_node_ids[candidate_index]
        request_id = self.defer_pruning_request_node_ids[candidate_index]
        deficit = max(
            0, min_eligible_support - candidate.rent_evidence_support
        )
        history = candidate.rent_review_support_high_waters
        comparison_high_water = (
            history[-2]
            if candidate.rent_review_count >= 2 and len(history) >= 2
            else candidate.rent_birth_support
        )
        measured_progress = bool(
            candidate.rent_review_count == 1
            or candidate.rent_interval_support_high_water
            > comparison_high_water
        )
        measured_request_active = bool(
            candidate.exploration_request_count
            > candidate.rent_request_count_at_last_review
        )
        budget_remaining = max(
            0, max_trial_reviews - candidate.rent_review_count
        )
        fixed = self.lifecycle_grace_mode == "fixed_six"
        measurements = {
            "evidence_deficit": (
                deficit / min_eligible_support
                if min_eligible_support else 0.0
            ),
            "evidence_progress": 1.0 if fixed or measured_progress else 0.0,
            "request_active": (
                1.0 if fixed or measured_request_active else 0.0
            ),
            "grace_budget_remaining": (
                budget_remaining / max_trial_reviews
                if max_trial_reviews else 0.0
            ),
        }
        request = self.graph.nodes[request_id]
        request.activation.reset(0.0)
        for name, terminal_id in terminal_ids.items():
            terminal = self.graph.nodes[terminal_id]
            terminal.activation.reset(measurements[name])
            terminal.meta.update({
                "measurement": measurements[name],
                "measurement_backend": (
                    "fixed_active"
                    if fixed and name in {
                        "evidence_progress", "request_active"
                    }
                    else "candidate_local"
                ),
            })
        self.graph.propagate_activation(eta=1.0)
        emitted = request.activation.value > 0.0
        inactive = [
            name for name, value in measurements.items() if value <= 0.0
        ]
        if "grace_budget_remaining" in inactive:
            reason = (
                "fixed_grace_budget_exhausted"
                if fixed else "conditioned_grace_budget_exhausted"
            )
        elif "evidence_progress" in inactive:
            reason = "conditioned_grace_no_progress"
        elif "request_active" in inactive:
            reason = "conditioned_grace_request_inactive"
        elif "evidence_deficit" in inactive:
            reason = "grace_not_needed"
        else:
            reason = None
        audit = {
            "mode": self.lifecycle_grace_mode,
            "candidate_index": candidate_index,
            "candidate_node_id": self.candidate_node_ids[candidate_index],
            "request_node_id": request_id,
            "terminal_node_ids": dict(sorted(terminal_ids.items())),
            "terminal_measurements": dict(sorted(measurements.items())),
            "terminal_backends": {
                name: self.graph.nodes[terminal_id].meta[
                    "measurement_backend"
                ]
                for name, terminal_id in sorted(terminal_ids.items())
            },
            "request_activation": request.activation.value,
            "emitted": emitted,
            "non_emission_reason": reason,
            "support": candidate.rent_evidence_support,
            "interval_support_high_water": (
                candidate.rent_interval_support_high_water
            ),
            "comparison_support_high_water": comparison_high_water,
            "measured_progress": measured_progress,
            "measured_request_active": measured_request_active,
            "request_count_at_interval_start": (
                candidate.rent_request_count_at_last_review
            ),
            "request_count_at_interval_end": (
                candidate.exploration_request_count
            ),
            "review_count": candidate.rent_review_count,
            "budget_remaining": budget_remaining,
        }
        emission = None
        if emitted:
            emission = {
                "candidate_index": candidate_index,
                "candidate_node_id": self.candidate_node_ids[candidate_index],
                "request_node_id": request_id,
                "request_activation": request.activation.value,
            }
        return emission, audit

    def lifecycle_grace_topology_signature(self) -> dict[str, object]:
        node_ids = tuple(sorted((
            *self.defer_pruning_request_node_ids.values(),
            *(
                terminal_id
                for terminal_ids in self.grace_terminal_node_ids.values()
                for terminal_id in terminal_ids.values()
            ),
        )))
        node_set = set(node_ids)
        edges = tuple(sorted(
            (edge.src, edge.dst, edge.ltype.value)
            for edge in self.graph.edges
            if edge.src in node_set or edge.dst in node_set
        ))
        return {"node_ids": node_ids, "edges": edges}

    def _remove_evidence_request_topology(self, candidate_index: int) -> None:
        request_id = self.evidence_request_node_ids.pop(candidate_index, None)
        terminal_id = self.evidence_deficit_node_ids.pop(candidate_index, None)
        if request_id is not None:
            self.graph.remove_node(request_id)
        if terminal_id is not None:
            self.graph.remove_node(terminal_id)

    def _sync_weights(self) -> None:
        bias_edge = self.graph.get_edge(self.ROOT_ID, self.BIAS_ID, LinkType.SUB)
        if bias_edge is not None:
            bias_edge.w = self.learner.bias
        for atom_id in self.primitive_node_ids:
            edge = self.graph.get_edge(self.ROOT_ID, atom_id, LinkType.SUB)
            if edge is not None:
                edge.w = self.learner.primitive_weights.get(atom_id, 0.0)
        for index, node_id in self.candidate_node_ids.items():
            edge = self.graph.get_edge(self.ROOT_ID, node_id, LinkType.SUB)
            if edge is not None:
                edge.w = self.learner.candidates[index].shadow_weight

    def _set_activations(
        self,
        atoms: tuple[str, ...],
        *,
        evidence_deficits: dict[int, float] | None = None,
    ) -> None:
        active = set(atoms)
        self.graph.reset_activations()
        self.graph.nodes[self.BIAS_ID].activation.reset(1.0)
        for atom_id in self.primitive_node_ids:
            self.graph.nodes[atom_id].activation.reset(float(atom_id in active))
        normalized = evidence_deficits or {}
        for candidate_index, terminal_id in self.evidence_deficit_node_ids.items():
            self.graph.nodes[terminal_id].activation.reset(
                normalized.get(candidate_index, 0.0)
            )
        self.graph.propagate_activation(eta=1.0)

    def _clip(self, value: float) -> float:
        config = self.learner.config
        return min(config.prediction_max, max(config.prediction_min, value))

    @staticmethod
    def _normalize(active_atom_ids: Iterable[str]) -> tuple[str, ...]:
        return tuple(sorted(set(map(str, active_atom_ids))))


class EpisodicCompositionPolicy:
    """Choose actions from graph outputs and credit retained decision traces."""

    def __init__(
        self,
        action_ids: Iterable[str],
        *,
        random_seed: int,
        config: EpisodicCompositionConfig | None = None,
        composition_config: OnlineCompositionConfig | None = None,
        reservoir_config: ExperienceReservoirConfig | None = None,
    ) -> None:
        actions = tuple(sorted(set(map(str, action_ids))))
        if len(actions) < 2:
            raise ValueError("at least two legal actions are required")
        self.action_ids = actions
        self.config = config or EpisodicCompositionConfig()
        self._rng = random.Random(random_seed)
        self.channels = {
            action_id: GraphBackedCompositionChannel(
                random_seed=random_seed + index + 1,
                composition_config=composition_config,
            )
            for index, action_id in enumerate(actions)
        }
        self.episode_trace: list[DecisionTrace] = []
        self.selection_count = {action_id: 0 for action_id in actions}
        self.terminal_return_sum = 0.0
        self.terminal_count = 0
        self.credited_decision_count = 0
        self.selection_update_mismatch_count = 0
        self.terminal_trace_lengths: list[int] = []
        self.rng_call_count = 0
        self.decision_count = 0
        self.experience_reservoir = (
            LifetimeDecisionReservoir(
                capacity=reservoir_config.capacity,
                random_seed=random_seed + 20_000_003,
            )
            if reservoir_config is not None
            else None
        )
        self._topology_rng = random.Random(random_seed + 30_000_007)
        self.causal_rent_config: CausalRentConfig | None = None
        self.causal_rent_start_terminal_count: int | None = None
        self.causal_rent_start_decision_count: int | None = None
        self.causal_rent_start_exploration_event_count: int | None = None
        self.causal_rent_events: list[dict[str, object]] = []
        self.causal_rent_review_count = 0
        self.causal_rent_proposal_opportunity_count = 0
        self.causal_rent_proposal_count = 0
        self.causal_rent_topology_rng_call_count = 0
        self.causal_rent_challenger_block_count = 0
        self.causal_rent_safety_ceiling_bind_count = 0
        self.maximum_global_live_candidate_count = self._global_live_count()
        self.causal_rent_occupancy_observation_count = 0
        self.causal_rent_live_trial_occupancy_sum = 0
        self.causal_rent_live_global_occupancy_sum = 0
        self.causal_rent_displaced_proposal_opportunity_count = 0
        self.causal_rent_displaced_eligible_proposal_count = 0
        self.causal_rent_right_censored_count = 0
        self.causal_rent_phase_finalized = False
        self._support_exploration_rng = random.Random(
            random_seed + 40_000_009
        )
        self.exploration_event_count = 0
        self.exploration_event_decision_indices: list[int] = []
        self.support_exploration_rng_call_count = 0
        self.support_request_opportunity_count = 0
        self.support_zero_request_opportunity_count = 0
        self.support_one_request_opportunity_count = 0
        self.support_multi_request_opportunity_count = 0
        self.support_unequal_strength_opportunity_count = 0
        self.support_allocator_could_differ_count = 0
        self.support_probe_action_count = 0
        self.support_exploration_fallback_count = 0
        self.support_exploration_events: list[dict[str, object]] = []
        self.evidence_request_terminals_enabled = True

    def begin_episode(self) -> None:
        self.episode_trace.clear()

    def choose(
        self,
        active_atom_ids: Iterable[str],
        *,
        explore: bool = True,
        legal_action_ids: Iterable[str] | None = None,
    ) -> str:
        atoms = tuple(sorted(set(map(str, active_atom_ids))))
        legal_actions = self._legal_actions(legal_action_ids)
        scores = {
            action_id: channel.predict(atoms)
            for action_id, channel in self.channels.items()
            if action_id in legal_actions
        }
        explore_draw = self._rng.random()
        random_action = legal_actions[self._rng.randrange(len(legal_actions))]
        tie_draw = self._rng.random()
        self.rng_call_count += 3
        best_score = max(scores.values())
        best_actions = [
            action_id for action_id in legal_actions
            if math.isclose(scores[action_id], best_score, rel_tol=0.0, abs_tol=1e-12)
        ]
        tie_index = min(len(best_actions) - 1, int(tie_draw * len(best_actions)))
        greedy_action = best_actions[tie_index]
        self.decision_count += 1
        exploration_event = bool(
            explore and explore_draw < self.config.exploration_rate
        )
        if exploration_event:
            self.exploration_event_count += 1
            self.exploration_event_decision_indices.append(
                self.decision_count
            )
        action_id = random_action if exploration_event else greedy_action
        rent_config = self.causal_rent_config
        if (
            exploration_event
            and rent_config is not None
            and rent_config.exploration_request_mode
            != "ordinary_random"
        ):
            action_id = self._graph_requested_exploration_action(
                atoms, legal_actions, random_action
            )
        responsibility = self.channels[action_id].decision_responsibility(atoms)
        active_graph_nodes = tuple(
            node_id
            for node_id, _ in responsibility["active_graph_nodes"]
        )
        self.episode_trace.append(
            DecisionTrace(
                action_id=action_id,
                active_atom_ids=atoms,
                graph_prediction=scores[action_id],
                active_graph_nodes=active_graph_nodes,
                component_importance=responsibility[
                    "component_importance"
                ],
                raw_component_contributions=responsibility[
                    "raw_component_contributions"
                ],
                component_states=responsibility["component_states"],
                legal_action_ids=legal_actions,
                decision_scores=tuple(sorted(scores.items())),
            )
        )
        self.selection_count[action_id] += 1
        return action_id

    def _graph_requested_exploration_action(
        self,
        atoms: tuple[str, ...],
        legal_actions: tuple[str, ...],
        ordinary_random_action: str,
    ) -> str:
        """Actuate graph emissions without inspecting candidate state."""
        config = self.causal_rent_config
        assert config is not None
        mode = config.exploration_request_mode
        if mode not in {
            "support_directed",
            "support_shuffled",
            "exact_support_directed",
            "exact_support_shuffled",
        }:
            raise RuntimeError("evidence exploration called in ordinary mode")

        draw = self._support_exploration_rng.random()
        self.support_exploration_rng_call_count += 1
        measurement_source = (
            "exact_reservoir"
            if mode.startswith("exact_support_")
            else "activation"
        )
        directed = mode.endswith("_directed")
        emissions: list[dict[str, object]] = []
        for action_id in legal_actions:
            channel_emissions = self.channels[action_id].emit_evidence_requests(
                atoms,
                action_id=action_id,
                measurement_source=measurement_source,
                min_eligible_support=config.min_eligible_support,
                terminals_enabled=self.evidence_request_terminals_enabled,
            )
            for emission in channel_emissions:
                self.channels[action_id].record_evidence_request(
                    str(emission["request_node_id"])
                )
            emissions.extend(channel_emissions)
        emissions.sort(key=lambda item: (
            str(item["action_id"]), int(item["candidate_index"])
        ))

        request_count = len(emissions)
        strengths = tuple(
            int(emission["request_strength"])
            for emission in emissions
        )
        if request_count == 0:
            self.support_zero_request_opportunity_count += 1
        elif request_count == 1:
            self.support_one_request_opportunity_count += 1
        else:
            self.support_multi_request_opportunity_count += 1
        unequal_strengths = len(set(strengths)) > 1
        if unequal_strengths:
            self.support_unequal_strength_opportunity_count += 1
        allocator_could_differ = bool(
            request_count > 1
            and any(strength < max(strengths) for strength in strengths)
        )
        if allocator_could_differ:
            self.support_allocator_could_differ_count += 1
        request_rows = tuple({
            "requester": (
                f'{emission["action_id"]}:'
                f'{emission["candidate_node_id"]}'
            ),
            "request_node_id": emission["request_node_id"],
            "terminal_node_id": emission["terminal_node_id"],
            "action_id": emission["action_id"],
            "measured_support": emission["measured_support"],
            "request_strength": emission["request_strength"],
            "measurement_source": emission["measurement_source"],
        } for emission in emissions)

        if not emissions:
            self.support_exploration_fallback_count += 1
            self.support_exploration_events.append({
                "decision_index": self.decision_count,
                "terminal_count": self.terminal_count,
                "mode": mode,
                "cumulative_terminal_return": self.terminal_return_sum,
                "active_request_count": 0,
                "selected_requester": None,
                "selected_action_id": ordinary_random_action,
                "ordinary_random_action_id": ordinary_random_action,
                "beneficiary_candidate_ids": (),
                "requesters": request_rows,
                "unequal_request_strengths": False,
                "allocators_could_differ": False,
                "fallback": True,
            })
            return ordinary_random_action

        self.support_request_opportunity_count += 1
        request_pool = emissions
        if directed:
            maximum_deficit = max(strengths)
            request_pool = [
                emission for emission in emissions
                if int(emission["request_strength"]) == maximum_deficit
            ]
        selected_index = min(
            len(request_pool) - 1,
            int(draw * len(request_pool)),
        )
        selected = request_pool[selected_index]
        action_id = str(selected["action_id"])
        beneficiaries = []
        for emission in emissions:
            if emission["action_id"] != action_id:
                continue
            self.channels[action_id].record_evidence_probe_benefit(
                str(emission["request_node_id"])
            )
            beneficiaries.append(
                f'{action_id}:{emission["candidate_node_id"]}'
            )
        self.support_probe_action_count += 1
        self.support_exploration_events.append({
            "decision_index": self.decision_count,
            "terminal_count": self.terminal_count,
            "mode": mode,
            "cumulative_terminal_return": self.terminal_return_sum,
            "active_request_count": request_count,
            "selected_requester": (
                f'{action_id}:{selected["candidate_node_id"]}'
            ),
            "selected_request_graph_node": selected["request_node_id"],
            "selected_request_support": selected["measured_support"],
            "selected_request_deficit": selected["request_strength"],
            "selected_action_id": action_id,
            "ordinary_random_action_id": ordinary_random_action,
            "beneficiary_candidate_ids": tuple(sorted(beneficiaries)),
            "requesters": request_rows,
            "unequal_request_strengths": unequal_strengths,
            "allocators_could_differ": allocator_could_differ,
            "fallback": False,
        })
        return action_id

    def greedy_action(
        self,
        active_atom_ids: Iterable[str],
        *,
        include_mature_composites: bool = True,
        legal_action_ids: Iterable[str] | None = None,
        disabled_candidates_by_action: (
            dict[str, frozenset[int]] | None
        ) = None,
    ) -> str:
        atoms = tuple(sorted(set(map(str, active_atom_ids))))
        legal_actions = self._legal_actions(legal_action_ids)
        scores = {
            action_id: channel.predict(
                atoms,
                include_mature_composites=include_mature_composites,
                disabled_candidate_indices=(
                    disabled_candidates_by_action.get(
                        action_id, frozenset()
                    )
                    if disabled_candidates_by_action
                    else frozenset()
                ),
            )
            for action_id, channel in self.channels.items()
            if action_id in legal_actions
        }
        return max(legal_actions, key=lambda action_id: (scores[action_id], action_id))

    def real_step(self, *, clear_trace: bool = False) -> None:
        for decision in self.episode_trace:
            decision.elapsed_steps += 1
        if clear_trace:
            self.episode_trace.clear()

    def observe_terminal(self, terminal_return: float) -> int:
        value = float(terminal_return)
        if not math.isfinite(value):
            raise ValueError("terminal_return must be finite")
        value = min(1.0, max(-1.0, value))
        self.terminal_return_sum += value
        self.terminal_count += 1
        self.terminal_trace_lengths.append(len(self.episode_trace))
        credited = 0
        for decision in self.episode_trace:
            target = value * (self.config.discount ** decision.elapsed_steps)
            if self.experience_reservoir is not None:
                mutation = self.experience_reservoir.add(
                    LifetimeDecisionRecord(
                        sequence=self.experience_reservoir.seen_count,
                        action_id=decision.action_id,
                        active_atom_ids=decision.active_atom_ids,
                        legal_action_ids=decision.legal_action_ids,
                        decision_scores=decision.decision_scores,
                        target=target,
                        discount=self.config.discount,
                        elapsed_steps=decision.elapsed_steps,
                    )
                )
                self._apply_reservoir_mutation(mutation)
            current_prediction = self.channels[decision.action_id].predict(
                decision.active_atom_ids
            )
            if not math.isclose(
                current_prediction,
                decision.graph_prediction,
                rel_tol=0.0,
                abs_tol=1e-12,
            ):
                self.selection_update_mismatch_count += 1
            self.channels[decision.action_id].observe(
                decision.active_atom_ids,
                target,
                decision_component_ids=decision.active_graph_nodes,
                decision_component_importance=dict(
                    decision.component_importance
                ),
            )
            credited += 1
        self.credited_decision_count += credited
        self.episode_trace.clear()
        self._causal_rent_tick()
        return credited

    def snapshot(self) -> dict[str, object]:
        if self.causal_rent_config is not None:
            self.assert_rent_evidence_support_parity()
        return {
            "schema_version": "recon_episodic_composition_policy.v1",
            "config": asdict(self.config),
            "action_ids": self.action_ids,
            "selection_count": dict(self.selection_count),
            "terminal_return_sum": self.terminal_return_sum,
            "terminal_count": self.terminal_count,
            "credited_decision_count": self.credited_decision_count,
            "rng_call_count": self.rng_call_count,
            "exploration": {
                "decision_count": self.decision_count,
                "event_count": self.exploration_event_count,
                "event_decision_indices": list(
                    self.exploration_event_decision_indices
                ),
                "support_rng_call_count": (
                    self.support_exploration_rng_call_count
                ),
                "request_opportunity_count": self.support_request_opportunity_count,
                "zero_request_opportunity_count": (
                    self.support_zero_request_opportunity_count
                ),
                "one_request_opportunity_count": (
                    self.support_one_request_opportunity_count
                ),
                "multi_request_opportunity_count": (
                    self.support_multi_request_opportunity_count
                ),
                "unequal_strength_opportunity_count": (
                    self.support_unequal_strength_opportunity_count
                ),
                "allocator_could_differ_count": (
                    self.support_allocator_could_differ_count
                ),
                "terminals_enabled": self.evidence_request_terminals_enabled,
                "probe_action_count": self.support_probe_action_count,
                "fallback_count": self.support_exploration_fallback_count,
                "events": list(self.support_exploration_events),
                "rent_enabled_decision_count": (
                    self.decision_count - self.causal_rent_start_decision_count
                    if self.causal_rent_start_decision_count is not None
                    else None
                ),
                "rent_enabled_event_count": (
                    self.exploration_event_count
                    - self.causal_rent_start_exploration_event_count
                    if self.causal_rent_start_exploration_event_count is not None
                    else None
                ),
                "rent_enabled_event_decision_indices": (
                    [
                        index for index in self.exploration_event_decision_indices
                        if index > self.causal_rent_start_decision_count
                    ]
                    if self.causal_rent_start_decision_count is not None
                    else None
                ),
            },
            "selection_update_mismatch_count": self.selection_update_mismatch_count,
            "terminal_trace_lengths": list(self.terminal_trace_lengths),
            "experience_reservoir": (
                self.experience_reservoir.snapshot()
                if self.experience_reservoir is not None
                else None
            ),
            "causal_rent": self._causal_rent_snapshot(),
            "channels": {
                action_id: channel.snapshot()
                for action_id, channel in self.channels.items()
            },
        }

    def enable_causal_rent(self, config: CausalRentConfig) -> None:
        """Enable role-blind global lifecycle review from this checkpoint."""
        if self.experience_reservoir is None:
            raise RuntimeError("causal rent requires a lifetime reservoir")
        if self.causal_rent_config is not None:
            raise RuntimeError("causal rent is already enabled")
        trials = self._trial_candidates()
        if len(trials) > config.temporary_challenger_allowance:
            raise RuntimeError(
                "checkpoint has too many live trials for challenger allowance"
            )
        if self._mature_count() > config.global_capacity:
            raise RuntimeError("checkpoint exceeds global mature capacity")
        if (
            config.lifecycle_grace_mode != "two_review"
            and config.exploration_request_mode != "exact_support_directed"
        ):
            raise ValueError(
                "lifecycle grace requires exact directed evidence requests"
            )
        self.causal_rent_config = config
        self.causal_rent_start_terminal_count = self.terminal_count
        self.causal_rent_start_decision_count = self.decision_count
        self.causal_rent_start_exploration_event_count = (
            self.exploration_event_count
        )
        for action_id, channel in self.channels.items():
            channel.configure_lifecycle_grace(
                config.lifecycle_grace_mode
            )
            channel.learner.external_lifecycle = True
            for candidate_index, candidate in enumerate(
                channel.learner.candidates
            ):
                if candidate.state in {"trial", "mature"}:
                    self._initialize_candidate_rent_evidence_support(
                        action_id, candidate_index
                    )
            channel.sync_external_lifecycle()
        self.assert_rent_evidence_support_parity()
        self.maximum_global_live_candidate_count = max(
            self.maximum_global_live_candidate_count,
            self._global_live_count(),
        )
        self._record_rent_event("enabled")

    def candidate_rent_stats(
        self, action_id: str, candidate_index: int
    ) -> CandidateRentStats:
        """Evaluate one candidate on the anonymous lifetime reservoir."""
        if self.experience_reservoir is None:
            raise RuntimeError("candidate rent requires a lifetime reservoir")
        if action_id not in self.channels:
            raise KeyError(action_id)
        learner = self.channels[action_id].learner
        candidate = learner.candidates[candidate_index]
        predictive_benefits = []
        margin_utilities = []
        margins_with = []
        margins_without = []
        margin_sign_flips = []
        for record in self.experience_reservoir.records:
            if not record_supports_candidate(
                record, action_id, candidate.members
            ):
                continue
            with_candidate, without_candidate = (
                learner.candidate_prediction_pair(
                    record.active_atom_ids, candidate_index
                )
            )
            other_scores = [
                self.channels[other_action].learner.predict(
                    record.active_atom_ids
                )
                for other_action in record.legal_action_ids
                if other_action != action_id
            ]
            if not other_scores:
                continue
            best_other = max(other_scores)
            margin_with = with_candidate - best_other
            margin_without = without_candidate - best_other
            margins_with.append(margin_with)
            margins_without.append(margin_without)
            margin_sign_flips.append((margin_with > 0.0) != (margin_without > 0.0))
            predictive_benefits.append(
                (record.target - without_candidate) ** 2
                - (record.target - with_candidate) ** 2
            )
            margin_utilities.append(
                record.target
                * (
                    (with_candidate - best_other)
                    - (without_candidate - best_other)
                )
            )
        support = len(predictive_benefits)
        if (
            self.causal_rent_config is not None
            and candidate.state in {"trial", "mature"}
            and support != candidate.rent_evidence_support
        ):
            raise RuntimeError(
                "incremental rent evidence support disagrees with full scan: "
                f"{action_id}:composite_{candidate_index} "
                f"incremental={candidate.rent_evidence_support} full={support}"
            )
        mean_margin_with = (
            sum(margins_with) / support if support else None
        )
        mean_margin_without = (
            sum(margins_without) / support if support else None
        )
        margin_sign_flip_rate = (
            sum(margin_sign_flips) / support if support else None
        )
        rent_config = self.causal_rent_config or CausalRentConfig()
        if support < rent_config.min_eligible_support:
            return CandidateRentStats(
                support, None, None, None,
                mean_margin_with, mean_margin_without,
                margin_sign_flip_rate,
            )
        benefit = sum(predictive_benefits) / support
        return CandidateRentStats(
            support=support,
            predictive_benefit=benefit,
            rent=benefit - rent_config.resource_cost,
            margin_utility=sum(margin_utilities) / support,
            mean_margin_with=mean_margin_with,
            mean_margin_without=mean_margin_without,
            margin_sign_flip_rate=margin_sign_flip_rate,
        )

    def review_causal_rent(self) -> None:
        """Run one explicit review over live anonymous candidates."""
        self.assert_rent_evidence_support_parity()
        config = self.causal_rent_config
        if config is None:
            raise RuntimeError("causal rent is not enabled")
        if self.causal_rent_phase_finalized:
            raise RuntimeError("causal-rent phase is already finalized")
        self.causal_rent_review_count += 1
        live = [
            (action_id, index, candidate)
            for action_id, channel in self.channels.items()
            for index, candidate in enumerate(channel.learner.candidates)
            if candidate.state in {"trial", "mature"}
        ]
        stats_by_id: dict[tuple[str, int], CandidateRentStats] = {}
        grace_emissions: dict[
            tuple[str, int], dict[str, object] | None
        ] = {}
        grace_audits: dict[tuple[str, int], dict[str, object]] = {}
        for action_id, index, candidate in live:
            stats = self.candidate_rent_stats(action_id, index)
            stats_by_id[(action_id, index)] = stats
            candidate.rent_review_count += 1
            candidate.last_rent = stats.rent
            candidate.last_margin_utility = stats.margin_utility
            if stats.rent is not None:
                candidate.rent_adequate_review_count += 1
            candidate.rent_evidence_support_high_water = max(
                candidate.rent_evidence_support_high_water, stats.support
            )
            candidate.rent_interval_support_high_water = max(
                candidate.rent_interval_support_high_water, stats.support
            )
            interval_high_water = (
                candidate.rent_interval_support_high_water
            )
            if (
                candidate.state == "trial"
                and config.lifecycle_grace_mode != "two_review"
            ):
                emission, grace_audit = self.channels[
                    action_id
                ].emit_defer_pruning_request(
                    index,
                    min_eligible_support=config.min_eligible_support,
                    max_trial_reviews=config.grace_max_trial_reviews,
                )
                grace_emissions[(action_id, index)] = emission
                grace_audits[(action_id, index)] = grace_audit
            else:
                grace_audit = {
                    "mode": config.lifecycle_grace_mode,
                    "emitted": False,
                    "non_emission_reason": (
                        "two_review_lifecycle"
                        if candidate.state == "trial"
                        else "not_trial"
                    ),
                }
                grace_audits[(action_id, index)] = grace_audit
            self._record_rent_event(
                "review",
                action_id=action_id,
                candidate_index=index,
                candidate_state=candidate.state,
                candidate_birth_observation=candidate.born_observation,
                candidate_birth_terminal_count=(
                    candidate.rent_birth_terminal_count
                ),
                candidate_birth_review_count=(
                    candidate.rent_birth_review_count
                ),
                candidate_birth_support=candidate.rent_birth_support,
                candidate_review_count=candidate.rent_review_count,
                support=stats.support,
                support_high_water=(
                    candidate.rent_evidence_support_high_water
                ),
                interval_support_high_water=interval_high_water,
                review_support_high_water_history=list(
                    candidate.rent_review_support_high_waters
                ),
                request_count_at_interval_start=(
                    candidate.rent_request_count_at_last_review
                ),
                request_count_at_interval_end=(
                    candidate.exploration_request_count
                ),
                grace_extension_count=candidate.grace_extension_count,
                grace_audit=grace_audit,
                rent=stats.rent,
                margin_utility=stats.margin_utility,
                mean_margin_with=stats.mean_margin_with,
                mean_margin_without=stats.mean_margin_without,
                margin_sign_flip_rate=stats.margin_sign_flip_rate,
            )
            candidate.rent_review_support_high_waters.append(
                interval_high_water
            )
            candidate.rent_request_count_at_last_review = (
                candidate.exploration_request_count
            )
            candidate.rent_interval_support_high_water = stats.support

        for action_id, index, candidate in live:
            if candidate.state != "mature":
                continue
            stats = stats_by_id[(action_id, index)]
            if stats.rent is None:
                continue
            negative = (
                stats.rent < -config.retirement_margin
                or stats.margin_utility is not None
                and stats.margin_utility < 0.0
            )
            candidate.negative_review_streak = (
                candidate.negative_review_streak + 1 if negative else 0
            )
            if (
                candidate.negative_review_streak
                >= config.consecutive_negative_reviews
            ):
                self._transition_candidate(
                    action_id, index, "pruned", "retired"
                )

        trials = [
            (action_id, index, candidate)
            for action_id, index, candidate in live
            if candidate.state == "trial"
        ]
        trials.sort(key=lambda item: (
            stats_by_id[(item[0], item[1])].rent is None,
            -(
                stats_by_id[(item[0], item[1])].rent
                if stats_by_id[(item[0], item[1])].rent is not None
                else 0.0
            ),
            item[0],
            item[1],
        ))
        for action_id, index, candidate in trials:
            if candidate.state != "trial":
                continue
            stats = stats_by_id[(action_id, index)]
            if stats.rent is None:
                candidate.uncertainty_review_streak += 1
                if config.lifecycle_grace_mode == "two_review":
                    if (
                        candidate.uncertainty_review_streak
                        >= config.max_uncertain_reviews
                    ):
                        self._transition_candidate(
                            action_id,
                            index,
                            "pruned",
                            "unsupported_pruned",
                        )
                    continue
                emission = grace_emissions[(action_id, index)]
                grace_audit = grace_audits[(action_id, index)]
                if emission is not None:
                    candidate.grace_extension_count += 1
                    self._record_rent_event(
                        "unsupported_deferred",
                        action_id=action_id,
                        candidate_index=index,
                        candidate_review_count=candidate.rent_review_count,
                        support=stats.support,
                        grace_extension_count=(
                            candidate.grace_extension_count
                        ),
                        defer_request=emission,
                        grace_audit=grace_audit,
                    )
                    continue
                reason = str(grace_audit["non_emission_reason"])
                self._transition_candidate(
                    action_id, index, "pruned", reason
                )
                continue
            promotes = (
                stats.rent > config.promotion_margin
                and stats.margin_utility is not None
                and stats.margin_utility > 0.0
            )
            if promotes:
                self._promote_or_replace(
                    action_id, index, stats, stats_by_id
                )
                continue
            clearly_negative = (
                stats.rent < -config.promotion_margin
                or stats.margin_utility is not None
                and stats.margin_utility < 0.0
            )
            if clearly_negative:
                self._transition_candidate(
                    action_id, index, "pruned", "challenger_rejected"
                )
                continue
            candidate.uncertainty_review_streak += 1
            if (
                candidate.uncertainty_review_streak
                >= config.max_uncertain_reviews
            ):
                self._transition_candidate(
                    action_id, index, "pruned", "uncertain_pruned"
                )

        self._sync_all_channels()
        self._assert_rent_bounds()
        self.assert_rent_evidence_support_parity()

    def _promote_or_replace(
        self,
        action_id: str,
        candidate_index: int,
        challenger_stats: CandidateRentStats,
        stats_by_id: dict[tuple[str, int], CandidateRentStats],
    ) -> None:
        config = self.causal_rent_config
        assert config is not None and challenger_stats.rent is not None
        if self._mature_count() < config.global_capacity:
            self._transition_candidate(
                action_id, candidate_index, "mature", "promoted"
            )
            return
        eligible_incumbents = []
        for other_action, channel in self.channels.items():
            for other_index, other in enumerate(channel.learner.candidates):
                if other.state != "mature":
                    continue
                stats = stats_by_id.get((other_action, other_index))
                if stats is not None and stats.rent is not None:
                    eligible_incumbents.append(
                        (stats.rent, other_action, other_index)
                    )
        if not eligible_incumbents:
            self._transition_candidate(
                action_id, candidate_index, "pruned", "capacity_rejected"
            )
            return
        incumbent_rent, incumbent_action, incumbent_index = min(
            eligible_incumbents
        )
        if (
            challenger_stats.rent
            <= incumbent_rent + config.replacement_margin
        ):
            self._transition_candidate(
                action_id, candidate_index, "pruned", "capacity_rejected"
            )
            return
        self._transition_candidate(
            incumbent_action, incumbent_index, "pruned", "replaced"
        )
        self._transition_candidate(
            action_id, candidate_index, "mature", "promoted_replacement"
        )

    def _causal_rent_tick(self) -> None:
        config = self.causal_rent_config
        if config is None:
            return
        assert self.causal_rent_start_terminal_count is not None
        elapsed = self.terminal_count - self.causal_rent_start_terminal_count
        if elapsed <= 0:
            return
        self.causal_rent_occupancy_observation_count += 1
        self.causal_rent_live_trial_occupancy_sum += len(
            self._trial_candidates()
        )
        self.causal_rent_live_global_occupancy_sum += (
            self._global_live_count()
        )
        if elapsed % config.review_interval_episodes == 0:
            self.review_causal_rent()
        if elapsed % config.proposal_interval_episodes == 0:
            self._causal_rent_proposal_opportunity()

    def _eligible_causal_rent_proposal_options(
        self,
    ) -> list[tuple[float, str, tuple[str, str]]]:
        options = []
        for action_id, channel in self.channels.items():
            learner = channel.learner
            if len(learner.candidates) >= learner._total_proposal_limit():
                continue
            options.extend(
                (score, action_id, pair)
                for pair, score in learner.proposal_options()
            )
        options.sort(key=lambda item: (item[0], item[1], item[2]))
        return options

    def _causal_rent_proposal_opportunity(self) -> None:
        config = self.causal_rent_config
        assert config is not None
        self.causal_rent_proposal_opportunity_count += 1
        options = self._eligible_causal_rent_proposal_options()
        trial_count = len(self._trial_candidates())
        if trial_count >= config.temporary_challenger_allowance:
            self.causal_rent_challenger_block_count += 1
            displaced = bool(options)
            if displaced:
                self.causal_rent_displaced_proposal_opportunity_count += 1
                self.causal_rent_displaced_eligible_proposal_count += len(
                    options
                )
            self._record_rent_event(
                "proposal_blocked_by_challenger",
                temporary_challenger_count=trial_count,
                temporary_challenger_allowance=(
                    config.temporary_challenger_allowance
                ),
                eligible_proposal_count=len(options),
                proposal_opportunity_displaced=displaced,
            )
            return
        if self._global_live_count() >= config.safety_ceiling:
            self.causal_rent_safety_ceiling_bind_count += 1
            self._record_rent_event(
                "safety_ceiling_bind",
                eligible_proposal_count=len(options),
            )
            return
        if not options:
            self._record_rent_event("no_eligible_proposal")
            return
        if config.proposal_mode == "residual_ranked":
            score, action_id, pair = options[-1]
        else:
            choice = self._topology_rng.randrange(len(options))
            self.causal_rent_topology_rng_call_count += 1
            score, action_id, pair = options[choice]
        learner = self.channels[action_id].learner
        candidate_index = learner.propose_pair(pair)
        self._initialize_candidate_rent_evidence_support(
            action_id, candidate_index
        )
        self.channels[action_id].sync_external_lifecycle()
        self.assert_rent_evidence_support_parity()
        self.causal_rent_proposal_count += 1
        self.maximum_global_live_candidate_count = max(
            self.maximum_global_live_candidate_count,
            self._global_live_count(),
        )
        candidate = learner.candidates[candidate_index]
        self._record_rent_event(
            "proposed",
            action_id=action_id,
            candidate_index=candidate_index,
            proposal_score=score,
            candidate_birth_observation=candidate.born_observation,
            candidate_birth_terminal_count=(
                candidate.rent_birth_terminal_count
            ),
            candidate_birth_review_count=candidate.rent_birth_review_count,
            candidate_birth_support=candidate.rent_birth_support,
        )
        self._assert_rent_bounds()

    def _initialize_candidate_rent_evidence_support(
        self, action_id: str, candidate_index: int
    ) -> None:
        if self.experience_reservoir is None:
            raise RuntimeError("candidate evidence requires a lifetime reservoir")
        candidate = self.channels[action_id].learner.candidates[candidate_index]
        candidate.rent_evidence_support = sum(
            record_supports_candidate(record, action_id, candidate.members)
            for record in self.experience_reservoir.records
        )
        if candidate.rent_birth_terminal_count is None:
            candidate.rent_birth_terminal_count = self.terminal_count
            candidate.rent_birth_review_count = self.causal_rent_review_count
            candidate.rent_birth_support = candidate.rent_evidence_support
            candidate.rent_evidence_support_high_water = (
                candidate.rent_evidence_support
            )
            candidate.rent_interval_support_high_water = (
                candidate.rent_evidence_support
            )
            candidate.rent_review_support_high_waters = [
                candidate.rent_evidence_support
            ]
            candidate.rent_request_count_at_last_review = (
                candidate.exploration_request_count
            )

    def _apply_reservoir_mutation(
        self, mutation: LifetimeReservoirMutation
    ) -> None:
        if self.causal_rent_config is None:
            return
        if not mutation.retained:
            if any((
                mutation.inserted_record is not None,
                mutation.evicted_record is not None,
                mutation.retained_index is not None,
            )):
                raise RuntimeError("rejected reservoir mutation is ambiguous")
            return
        inserted = mutation.inserted_record
        if inserted is None or mutation.retained_index is None:
            raise RuntimeError("retained reservoir mutation lacks insertion")
        for action_id, channel in self.channels.items():
            for candidate in channel.learner.candidates:
                if candidate.state not in {"trial", "mature"}:
                    continue
                if record_supports_candidate(
                    inserted, action_id, candidate.members
                ):
                    candidate.rent_evidence_support += 1
                evicted = mutation.evicted_record
                if (
                    evicted is not None
                    and record_supports_candidate(
                        evicted, action_id, candidate.members
                    )
                ):
                    candidate.rent_evidence_support -= 1
                if candidate.rent_evidence_support < 0:
                    raise RuntimeError(
                        "candidate rent evidence support became negative"
                    )
                candidate.rent_evidence_support_high_water = max(
                    candidate.rent_evidence_support_high_water,
                    candidate.rent_evidence_support,
                )
                candidate.rent_interval_support_high_water = max(
                    candidate.rent_interval_support_high_water,
                    candidate.rent_evidence_support,
                )

    def assert_rent_evidence_support_parity(self) -> None:
        """Hard-fail if any live candidate counter differs from a fresh scan."""
        if self.experience_reservoir is None:
            raise RuntimeError("candidate evidence requires a lifetime reservoir")
        for action_id, channel in self.channels.items():
            for candidate_index, candidate in enumerate(
                channel.learner.candidates
            ):
                if candidate.state not in {"trial", "mature"}:
                    continue
                full_support = sum(
                    record_supports_candidate(
                        record, action_id, candidate.members
                    )
                    for record in self.experience_reservoir.records
                )
                if full_support != candidate.rent_evidence_support:
                    raise RuntimeError(
                        "incremental rent evidence support disagrees with "
                        f"full scan: {action_id}:composite_{candidate_index} "
                        f"incremental={candidate.rent_evidence_support} "
                        f"full={full_support}"
                    )

    def _transition_candidate(
        self,
        action_id: str,
        candidate_index: int,
        state: str,
        event: str,
    ) -> None:
        channel = self.channels[action_id]
        candidate = channel.learner.candidates[candidate_index]
        channel.learner.transition_candidate(candidate_index, state)
        channel.sync_external_lifecycle()
        self._record_rent_event(
            event,
            action_id=action_id,
            candidate_index=candidate_index,
            candidate_review_count=candidate.rent_review_count,
            support=candidate.rent_evidence_support,
            support_high_water=candidate.rent_evidence_support_high_water,
            interval_support_high_water=(
                candidate.rent_interval_support_high_water
            ),
            grace_extension_count=candidate.grace_extension_count,
            pruning_reason=event if state == "pruned" else None,
        )

    def finalize_causal_rent_phase(self) -> None:
        """Record end-of-phase right censoring without changing behavior."""
        config = self.causal_rent_config
        if config is None:
            raise RuntimeError("causal rent is not enabled")
        if self.causal_rent_phase_finalized:
            raise RuntimeError("causal-rent phase is already finalized")
        self.assert_rent_evidence_support_parity()
        applicable_cap = (
            config.max_uncertain_reviews
            if config.lifecycle_grace_mode == "two_review"
            else config.grace_max_trial_reviews
        )
        for action_id, channel in self.channels.items():
            for index, candidate in enumerate(channel.learner.candidates):
                if candidate.state != "trial":
                    continue
                if candidate.rent_review_count >= applicable_cap:
                    raise RuntimeError(
                        "live trial reached lifecycle cap without adjudication"
                    )
                candidate.rent_right_censored = True
                self.causal_rent_right_censored_count += 1
                self._record_rent_event(
                    "right_censored",
                    action_id=action_id,
                    candidate_index=index,
                    candidate_review_count=candidate.rent_review_count,
                    applicable_review_cap=applicable_cap,
                    support=candidate.rent_evidence_support,
                    support_high_water=(
                        candidate.rent_evidence_support_high_water
                    ),
                    interval_support_high_water=(
                        candidate.rent_interval_support_high_water
                    ),
                    grace_extension_count=candidate.grace_extension_count,
                )
        self.causal_rent_phase_finalized = True

    def _sync_all_channels(self) -> None:
        for channel in self.channels.values():
            channel.sync_external_lifecycle()

    def _record_rent_event(self, event: str, **fields: object) -> None:
        self.causal_rent_events.append({
            "event": event,
            "terminal_count": self.terminal_count,
            "global_live_count": self._global_live_count(),
            "global_trial_count": len(self._trial_candidates()),
            "global_mature_count": self._mature_count(),
            **fields,
        })

    def _global_live_count(self) -> int:
        return sum(
            candidate.state in {"trial", "mature"}
            for channel in self.channels.values()
            for candidate in channel.learner.candidates
        )

    def _mature_count(self) -> int:
        return sum(
            candidate.state == "mature"
            for channel in self.channels.values()
            for candidate in channel.learner.candidates
        )

    def _trial_candidates(self) -> list[tuple[str, int]]:
        return [
            (action_id, index)
            for action_id, channel in self.channels.items()
            for index, candidate in enumerate(channel.learner.candidates)
            if candidate.state == "trial"
        ]

    def _assert_rent_bounds(self) -> None:
        config = self.causal_rent_config
        assert config is not None
        if self._mature_count() > config.global_capacity:
            raise RuntimeError("causal-rent mature capacity exceeded")
        if self._global_live_count() > config.safety_ceiling:
            raise RuntimeError("causal-rent safety ceiling exceeded")
        if len(self._trial_candidates()) > config.temporary_challenger_allowance:
            raise RuntimeError("causal-rent challenger allowance exceeded")

    def _causal_rent_snapshot(self) -> dict[str, object] | None:
        config = self.causal_rent_config
        if config is None:
            return None
        return {
            "schema_version": "recon_role_blind_causal_rent.v2",
            "config": asdict(config),
            "start_terminal_count": self.causal_rent_start_terminal_count,
            "final_terminal_return_sum": self.terminal_return_sum,
            "review_count": self.causal_rent_review_count,
            "proposal_opportunity_count": (
                self.causal_rent_proposal_opportunity_count
            ),
            "proposal_count": self.causal_rent_proposal_count,
            "topology_rng_call_count": (
                self.causal_rent_topology_rng_call_count
            ),
            "challenger_block_count": (
                self.causal_rent_challenger_block_count
            ),
            "safety_ceiling_bind_count": (
                self.causal_rent_safety_ceiling_bind_count
            ),
            "global_live_count": self._global_live_count(),
            "global_mature_count": self._mature_count(),
            "maximum_global_live_candidate_count": (
                self.maximum_global_live_candidate_count
            ),
            "occupancy_observation_count": (
                self.causal_rent_occupancy_observation_count
            ),
            "mean_live_trial_occupancy": (
                self.causal_rent_live_trial_occupancy_sum
                / self.causal_rent_occupancy_observation_count
                if self.causal_rent_occupancy_observation_count
                else 0.0
            ),
            "mean_live_global_occupancy": (
                self.causal_rent_live_global_occupancy_sum
                / self.causal_rent_occupancy_observation_count
                if self.causal_rent_occupancy_observation_count
                else 0.0
            ),
            "displaced_proposal_opportunity_count": (
                self.causal_rent_displaced_proposal_opportunity_count
            ),
            "displaced_eligible_proposal_count": (
                self.causal_rent_displaced_eligible_proposal_count
            ),
            "right_censored_count": self.causal_rent_right_censored_count,
            "phase_finalized": self.causal_rent_phase_finalized,
            "events": list(self.causal_rent_events),
        }

    def _legal_actions(
        self, legal_action_ids: Iterable[str] | None
    ) -> tuple[str, ...]:
        if legal_action_ids is None:
            return self.action_ids
        legal = tuple(sorted(set(map(str, legal_action_ids))))
        if not legal:
            raise ValueError("at least one legal action is required")
        unknown = set(legal) - set(self.action_ids)
        if unknown:
            raise KeyError(f"unknown legal actions: {sorted(unknown)}")
        return legal
