"""Graph-backed action choice from empirical return distributions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import random
from typing import Iterable, Literal

from .graph import Graph, LinkType, Node, NodeType
from .robust_return import RobustReturnConfig, RobustReturnMemory


RobustObjective = Literal["mean", "lower_tail"]


@dataclass(frozen=True)
class RobustActionPolicyConfig:
    exploration_rate: float = 0.15

    def __post_init__(self) -> None:
        if not 0.0 <= self.exploration_rate <= 1.0:
            raise ValueError("exploration_rate must be in [0, 1]")


class GraphBackedRobustActionPolicy:
    """Use the selected empirical statistic as each action graph's exact score."""

    ROOT_ID = "action_value"
    BIAS_ID = "return_estimate"

    def __init__(
        self,
        action_ids: Iterable[str],
        *,
        objective: RobustObjective,
        random_seed: int,
        config: RobustActionPolicyConfig | None = None,
        return_config: RobustReturnConfig | None = None,
    ) -> None:
        actions = tuple(sorted(set(map(str, action_ids))))
        if len(actions) < 2:
            raise ValueError("at least two legal actions are required")
        if objective not in {"mean", "lower_tail"}:
            raise ValueError("objective must be mean or lower_tail")
        self.action_ids = actions
        self.objective = objective
        self.config = config or RobustActionPolicyConfig()
        self.memory = RobustReturnMemory(return_config)
        self._rng = random.Random(random_seed)
        self.graphs = {
            action_id: self._make_action_graph() for action_id in actions
        }
        self.selection_count = {action_id: 0 for action_id in actions}
        self.observed_return_count = 0
        self.rng_call_count = 0
        self.graph_prediction_count = 0
        self.graph_prediction_mismatch_count = 0
        self._sync_all()

    def score(self, action_id: str) -> float:
        normalized = str(action_id)
        graph = self.graphs[normalized]
        graph.nodes[self.BIAS_ID].activation.reset(1.0)
        score = graph.compute_z_sur(self.ROOT_ID)
        estimate = self.memory.estimate(normalized)
        expected = (
            estimate.mean_score
            if self.objective == "mean"
            else estimate.robust_score
        )
        self.graph_prediction_count += 1
        if not math.isclose(score, expected, rel_tol=0.0, abs_tol=1e-12):
            self.graph_prediction_mismatch_count += 1
        return score

    def choose(self, *, explore: bool = True) -> str:
        scores = {
            action_id: self.score(action_id) for action_id in self.action_ids
        }
        explore_draw = self._rng.random()
        random_action = self.action_ids[self._rng.randrange(len(self.action_ids))]
        tie_draw = self._rng.random()
        self.rng_call_count += 3
        best_score = max(scores.values())
        best_actions = [
            action_id for action_id in self.action_ids
            if math.isclose(scores[action_id], best_score, rel_tol=0.0, abs_tol=1e-12)
        ]
        tie_index = min(len(best_actions) - 1, int(tie_draw * len(best_actions)))
        action_id = (
            random_action
            if explore and explore_draw < self.config.exploration_rate
            else best_actions[tie_index]
        )
        self.selection_count[action_id] += 1
        return action_id

    def greedy_action(self) -> str:
        return max(
            self.action_ids,
            key=lambda action_id: (self.score(action_id), action_id),
        )

    def observe(self, action_id: str, observed_return: float) -> None:
        normalized = str(action_id)
        if normalized not in self.graphs:
            raise KeyError(f"unknown action: {normalized}")
        self.memory.observe(normalized, observed_return)
        self.observed_return_count += 1
        self._sync_action(normalized)

    def snapshot(self) -> dict[str, object]:
        return {
            "schema_version": "recon_graph_backed_robust_policy.v1",
            "objective": self.objective,
            "config": asdict(self.config),
            "action_ids": self.action_ids,
            "selection_count": dict(self.selection_count),
            "observed_return_count": self.observed_return_count,
            "rng_call_count": self.rng_call_count,
            "graph_prediction_count": self.graph_prediction_count,
            "graph_prediction_mismatch_count": (
                self.graph_prediction_mismatch_count
            ),
            "return_memory": self.memory.snapshot(),
            "graphs": {
                action_id: graph.to_snapshot()
                for action_id, graph in self.graphs.items()
            },
        }

    def _sync_all(self) -> None:
        for action_id in self.action_ids:
            self._sync_action(action_id)

    def _sync_action(self, action_id: str) -> None:
        estimate = self.memory.estimate(action_id)
        value = (
            estimate.mean_score
            if self.objective == "mean"
            else estimate.robust_score
        )
        edge = self.graphs[action_id].get_edge(
            self.ROOT_ID, self.BIAS_ID, LinkType.SUB
        )
        if edge is None:
            raise RuntimeError("action graph is missing its value edge")
        edge.w = value

    @classmethod
    def _make_action_graph(cls) -> Graph:
        graph = Graph()
        graph.add_node(Node(cls.ROOT_ID, NodeType.SCRIPT))
        graph.add_node(Node(cls.BIAS_ID, NodeType.TERMINAL))
        graph.add_hierarchy_pair(cls.ROOT_ID, cls.BIAS_ID)
        return graph
