"""Internal residual nomination through an isolated terminal/SCRIPT branch.

No chess imports, feature-vector access, alternative outcomes, or action scoring.
Random proposals acquire local outcome statistics; nomination uses only the past.
Subsequent committed predictions measure predictive value, not causal competence.
"""
from dataclasses import asdict, dataclass
import math
import random

from recon_lite.graph import Node, NodeState, NodeType
from .terminal_development import (
    DevelopmentConfig, TerminalDevelopment, _reader,
)

SHADOW_ROOT = "shadow:root"


@dataclass(frozen=True)
class ShadowConfig:
    candidates: int = 64
    discovery_episodes: int = 64
    min_support: int = 4
    support_bins: int = 4
    learning_rate: float = 0.3

    def __post_init__(self):
        if min(self.candidates, self.min_support, self.support_bins) < 1:
            raise ValueError("shadow budgets must be positive")
        if self.discovery_episodes < 2 * self.min_support:
            raise ValueError("discovery must allow active and inactive support")
        if not 0 < self.learning_rate <= 1:
            raise ValueError("invalid shadow learning rate")


@dataclass(frozen=True)
class Definition:
    operator: str
    atoms: tuple[tuple[int, bool | int], ...]

    def validate(self, schema):
        if self.operator not in ("and", "or", "xor") or not 1 <= len(self.atoms) <= 3:
            raise ValueError("invalid shadow grammar")
        if len({i for i, _ in self.atoms}) != len(self.atoms):
            raise ValueError("shadow coordinates must be distinct")
        if tuple(sorted(self.atoms)) != self.atoms:
            raise ValueError("shadow atoms must have canonical order")
        if len(self.atoms) == 1 and self.operator != "and":
            raise ValueError("single readers use canonical AND")
        for i, value in self.atoms:
            if not 0 <= i < len(schema):
                raise ValueError("shadow coordinate outside schema")
            schema[i].validate(value)


def random_definitions(schema, *, seed, count):
    """Reuse the live generic grammar, with its own RNG and a finite draw budget."""
    if not schema or count < 1:
        raise ValueError("nonempty schema and positive candidate budget required")
    generator = TerminalDevelopment(seed=f"shadow-proposals:{seed}",
                                    config=DevelopmentConfig(max_conditions=count))
    generator.schema = tuple(schema)
    for _ in range(32 * count):
        generator._birth()
        if len(generator.conditions) == count:
            return tuple(Definition(c.operator, c.atoms) for c in generator.conditions.values())
    raise ValueError("candidate budget exceeds the sampled grammar; no silent truncation")


@dataclass
class Evidence:
    support: int = 0
    residual_sum: float = 0.0
    weight: float = 0.0


@dataclass(frozen=True)
class Commitment:
    event_id: int
    action: str
    base: float
    active: tuple[bool, ...]
    predictions: tuple[float, ...]


class ResidualEvidence:
    """Statistics local to one action-choice site and its trial compositions."""

    def __init__(self, definitions, *, seed, config):
        if len(definitions) != config.candidates or len(set(definitions)) != len(definitions):
            raise ValueError("distinct definitions must fill the candidate budget")
        self.definitions = tuple(definitions)
        self.config = config
        self.rng = random.Random(f"shadow-control:{seed}")
        self.evidence = [Evidence() for _ in definitions]
        self.observations = 0
        self.residual_sum = 0.0
        self.nomination = None
        self.nomination_status = "collecting"
        self.prospective = {"count": 0, "base_squared_error": 0.0,
                            "ranked_squared_error": 0.0, "random_squared_error": 0.0,
                            "ranked_active": 0, "random_active": 0}

    def commit(self, event_id, action, base, active):
        if len(active) != len(self.definitions) or any(type(x) is not bool for x in active):
            raise ValueError("one terminal-derived Boolean per candidate required")
        return Commitment(event_id, action, base, tuple(active),
                          tuple(base + e.weight * x for e, x in zip(self.evidence, active)))

    def _nominate(self, live):
        n = self.observations
        groups = {}
        scores = {}
        for i, (definition, evidence) in enumerate(zip(self.definitions, self.evidence)):
            support = evidence.support
            if definition in live or min(support, n - support) < self.config.min_support:
                continue
            # The old generic online_composition score, without its external
            # active-atom input, automatic maturity, or action-value machinery.
            scores[i] = abs(evidence.residual_sum / support - self.residual_sum / n) * math.sqrt(support)
            group = (len(definition.atoms), definition.operator,
                     support * self.config.support_bins // n)
            groups.setdefault(group, []).append(i)
        eligible = [(i, group) for group, ids in groups.items() if len(ids) >= 2 for i in ids]
        if not eligible:
            self.nomination_status = "no_matched_pair"
            return
        ranked, group = max(eligible, key=lambda item: (scores[item[0]], -item[0]))
        # Include the winner: removing it would handicap the random null.
        control = self.rng.choice(groups[group])
        self.nomination = {"after_episode": n, "ranked": ranked, "random": control,
                           "matching_group": group, "eligible_count": len(eligible),
                           "random_pool": tuple(groups[group]),
                           "ranked_score": scores[ranked], "random_score": scores[control],
                           "ranked_support": self.evidence[ranked].support,
                           "random_support": self.evidence[control].support,
                           "ranked_initial_weight": self.evidence[ranked].weight,
                           "random_initial_weight": self.evidence[control].weight}
        self.nomination_status = "nominated"

    def observe(self, commitment, reward, *, live):
        # Called only after the organism validates actual action-bound feedback.
        if self.nomination is not None:
            self.prospective["count"] += 1
            self.prospective["base_squared_error"] += (reward - commitment.base) ** 2
            for role in ("ranked", "random"):
                i = self.nomination[role]
                self.prospective[f"{role}_squared_error"] += (reward - commitment.predictions[i]) ** 2
                self.prospective[f"{role}_active"] += int(commitment.active[i])
        residual = reward - commitment.base
        # Score the committed forecast BEFORE learning this outcome. Both the
        # actor and every shadow coefficient continue adapting; no frozen actor.
        for e, active, prediction in zip(self.evidence, commitment.active, commitment.predictions):
            if active:
                e.support += 1
                e.residual_sum += residual
                e.weight += self.config.learning_rate * (reward - prediction)
        self.observations += 1
        self.residual_sum += residual
        if self.observations == self.config.discovery_episodes:
            self._nominate(live)

    def report(self):
        # Offline serialization; never passed back to the coach as training input.
        return {"definitions": [asdict(d) for d in self.definitions],
                "config": asdict(self.config), "evidence": [asdict(e) for e in self.evidence],
                "observations": self.observations, "residual_sum": self.residual_sum,
                "nomination": self.nomination, "nomination_status": self.nomination_status,
                "prospective": dict(self.prospective), "control_rng": self.rng.getstate()}


class ShadowDevelopment(TerminalDevelopment):
    """Experimental one-action episodes; production action/credit/birth unchanged.

    The isolated branch reads only the selected binding before its actuator runs.
    It has no hierarchy or other links into action_choice or any live condition.
    Candidate history persists; this first experiment never promotes or retires it.
    """

    def __init__(self, *, seed=1, config=None, shadow_config=None, definitions=None):
        super().__init__(seed=seed, config=config)
        self.shadow_config = shadow_config or ShadowConfig()
        self.shadow_seed = seed
        self.shadow_definitions = None if definitions is None else tuple(definitions)
        self.shadow = None
        self.shadow_pending = None

    def __getstate__(self):
        if self.shadow_pending is not None:
            raise RuntimeError("checkpoint requires completed shadow outcome feedback")
        return super().__getstate__()

    def act(self, port, *, event_id, learn):
        if self.shadow_pending is not None or (learn and self.pending):
            raise RuntimeError("shadow experiment requires feedback after each actual action")
        return super().act(port, event_id=event_id, learn=learn)

    def _init_shadow(self):
        definitions = self.shadow_definitions
        if definitions is None:
            definitions = random_definitions(self.schema, seed=self.shadow_seed,
                                              count=self.shadow_config.candidates)
        for definition in definitions:
            definition.validate(self.schema)
        self.shadow = ResidualEvidence(definitions, seed=self.shadow_seed, config=self.shadow_config)
        self.graph.add_node(Node(SHADOW_ROOT, NodeType.SCRIPT, meta={"confirm_policy": "weighted_evidence"}))
        for i, definition in enumerate(definitions):
            gate = f"shadow:gate:{i}"
            self.graph.add_node(Node(gate, NodeType.SCRIPT, meta={
                "confirm_policy": definition.operator, "condition_id": f"shadow:{i}"}))
            self.graph.nodes[gate].activation.value = 1.0
            self.graph.add_hierarchy_pair(SHADOW_ROOT, gate)
            for index, value in definition.atoms:
                terminal = f"shadow:read:{index}:{int(value)}"
                if terminal not in self.graph.nodes:
                    self.graph.add_node(Node(terminal, NodeType.TERMINAL, predicate=_reader,
                                             meta={"slot": 0, "atom": (index, value)}))
                self.graph.add_hierarchy_pair(gate, terminal)
        self.graph.validate_formal_pairs()

    def _before_execute(self, engine, env, *, event_id, slot, prediction, learn):
        if not learn:
            return
        if self.shadow is None:
            self._init_shadow()
        for nid, node in self.graph.nodes.items():
            if nid.startswith("shadow:read:"):
                node.meta["slot"] = slot
        engine.request(SHADOW_ROOT)
        engine.run(max_ticks=40, env=env, until=lambda e: e.g.nodes[SHADOW_ROOT].state in
                   (NodeState.CONFIRMED, NodeState.FAILED))
        states = tuple(self.graph.nodes[f"shadow:gate:{i}"].state
                       for i in range(self.shadow_config.candidates))
        if any(state not in (NodeState.CONFIRMED, NodeState.FAILED) for state in states):
            raise RuntimeError("shadow terminal composition did not settle")
        self.shadow_pending = self.shadow.commit(
            event_id, env["bindings"][slot], prediction,
            tuple(state == NodeState.CONFIRMED for state in states))

    def observe(self, feedback):
        # Validate before either learner mutates. Do not turn stale, virtual or
        # mismatched action outcomes into nomination evidence.
        if self.shadow_pending is None or len(self.pending) != 1:
            raise RuntimeError("no single actual action awaiting shadow feedback")
        commitment = self.shadow_pending
        if (feedback.event_id, feedback.action) != (commitment.event_id, commitment.action):
            raise ValueError("outcome does not bind to the latest submitted action")
        reward = float(feedback.reward)
        if not math.isfinite(reward):
            raise ValueError("reward must be finite")
        super().observe(feedback)
        live = {Definition(c.operator, c.atoms) for c in self.conditions.values()}
        self.shadow.observe(commitment, reward, live=live)
        self.shadow_pending = None
