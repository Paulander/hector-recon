"""Graph-backed action values with terminal-only episodic responsibility."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import random
from typing import Iterable

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
    elapsed_steps: int = 0


class GraphBackedCompositionChannel:
    """Expose an online composition learner through real graph activations."""

    ROOT_ID = "action_score"
    BIAS_ID = "bias_terminal"

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
        }

    def _ensure_primitive(self, atom_id: str) -> None:
        if atom_id in self.primitive_node_ids:
            return
        if atom_id in {self.ROOT_ID, self.BIAS_ID} or atom_id.startswith("composite_"):
            raise ValueError("atom ID collides with reserved graph namespace")
        self.graph.add_node(Node(atom_id, NodeType.TERMINAL))
        self.graph.add_hierarchy_pair(self.ROOT_ID, atom_id)
        self.primitive_node_ids.add(atom_id)
        self._sync_weights()

    def _sync_topology(self) -> None:
        for index, candidate in enumerate(self.learner.candidates):
            node_id = self.candidate_node_ids.get(index)
            if candidate.state == "pruned":
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
            if candidate.state == "mature" and self.graph.parent_of(node_id) is None:
                self.graph.add_hierarchy_pair(self.ROOT_ID, node_id)

        for index, node_id in self.candidate_node_ids.items():
            candidate = self.learner.candidates[index]
            if candidate.state == "trial" and self.graph.parent_of(node_id) is not None:
                self.trial_root_edge_count += 1

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

    def _set_activations(self, atoms: tuple[str, ...]) -> None:
        active = set(atoms)
        self.graph.reset_activations()
        self.graph.nodes[self.BIAS_ID].activation.reset(1.0)
        for atom_id in self.primitive_node_ids:
            self.graph.nodes[atom_id].activation.reset(float(atom_id in active))
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
        action_id = (
            random_action
            if explore and explore_draw < self.config.exploration_rate
            else greedy_action
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
            )
        )
        self.selection_count[action_id] += 1
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
        return credited

    def snapshot(self) -> dict[str, object]:
        return {
            "schema_version": "recon_episodic_composition_policy.v1",
            "config": asdict(self.config),
            "action_ids": self.action_ids,
            "selection_count": dict(self.selection_count),
            "terminal_return_sum": self.terminal_return_sum,
            "terminal_count": self.terminal_count,
            "credited_decision_count": self.credited_decision_count,
            "rng_call_count": self.rng_call_count,
            "selection_update_mismatch_count": self.selection_update_mismatch_count,
            "terminal_trace_lengths": list(self.terminal_trace_lengths),
            "channels": {
                action_id: channel.snapshot()
                for action_id, channel in self.channels.items()
            },
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
