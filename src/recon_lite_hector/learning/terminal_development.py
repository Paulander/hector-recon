"""Finite typed terminals and reward-driven development, independent of chess.

The persistent formal graph computes action support. The runtime binds primitive
actuators, proposes generic readers/gates and updates participating SUR weights.
It never receives a feature vector, a board, or alternative-action rewards.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import random
from typing import Protocol

from recon_lite.formal_engine import FormalReConEngine
from recon_lite.graph import Graph, LinkType, Node, NodeState, NodeType
from recon_lite_hector.nodes.stem_cell import CandidateLocalStats, StemCellState


@dataclass(frozen=True)
class Coordinate:
    name: str
    values: tuple[bool | int, ...]

    def __post_init__(self):
        if not self.name or not self.values or len(set(self.values)) != len(self.values):
            raise ValueError("coordinate requires a name and distinct finite values")
        if any(type(value) not in (bool, int) for value in self.values):
            raise ValueError("this initial reader grammar supports boolean/integer domains")
        if len({type(value) for value in self.values}) != 1:
            raise ValueError("each coordinate has one declared scalar type")

    def validate(self, value):
        if type(value) is not type(self.values[0]) or value not in self.values:
            raise ValueError(f"measurement outside typed domain: {self.name}")
        return value


class FeaturePort(Protocol):
    schema: tuple[Coordinate, ...]

    def bindings(self) -> tuple[str, ...]: ...
    def measure(self, coordinate: int, binding: str) -> bool | int: ...
    def execute(self, binding: str) -> None: ...


@dataclass
class PlasticWeight:
    fast: float = 0.0
    slow: float = 0.0

    def __float__(self):
        return self.fast + self.slow

    def consolidate(self, rate: float):
        # Transfer, rather than duplicate, credit. Slow weights affect policy
        # immediately; fast plasticity remains available after consolidation.
        transfer = rate * self.fast
        self.fast -= transfer
        self.slow += transfer


@dataclass
class Condition:
    identity: int
    atoms: tuple[tuple[int, bool | int], ...]
    operator: str
    born: int
    weight: PlasticWeight = field(default_factory=PlasticWeight)
    stats: CandidateLocalStats = field(default_factory=CandidateLocalStats)
    state: StemCellState = StemCellState.TRIAL


@dataclass(frozen=True)
class DevelopmentConfig:
    max_conditions: int = 96
    births_per_episode: int = 2
    learning_rate: float = 0.3
    exploration: float = 0.25
    grace_episodes: int = 256
    prune_weight: float = 0.02
    consolidate_every: int = 32
    consolidation_rate: float = 0.1
    eligibility_decay: float = 0.8

    def __post_init__(self):
        if min(self.max_conditions, self.births_per_episode, self.grace_episodes,
               self.consolidate_every) < 1:
            raise ValueError("development budgets must be positive")
        if not 0 < self.learning_rate <= 1 or not 0 <= self.exploration <= 1:
            raise ValueError("invalid learning/exploration rate")
        if not 0 <= self.consolidation_rate <= 1 or not 0 <= self.eligibility_decay <= 1:
            raise ValueError("invalid consolidation/eligibility rate")
        if not math.isfinite(self.prune_weight) or self.prune_weight < 0:
            raise ValueError("pruning threshold must be finite and nonnegative")


# Picklable terminal implementations: only these functions call the port.
def _catalog(node, env):
    bindings = tuple(env["port"].bindings())
    if len(set(bindings)) != len(bindings) or any(not isinstance(x, str) or not x for x in bindings):
        raise ValueError("actuator bindings must be unique nonempty opaque tokens")
    node.meta["reading"] = bindings
    return True, True


def _reader(node, env):
    index, expected = node.meta["atom"]
    binding = env["bindings"][node.meta["slot"]]
    actual = env["schema"][index].validate(env["port"].measure(index, binding))
    node.meta["reading"] = actual
    matches = actual == expected
    node.activation.value = float(matches)
    return True, matches


def _constant(node, env):
    node.activation.value = 1.0
    return True, True


def _exploration(node, env):
    node.activation.value = float(env["exploration"].get(node.meta["slot"], 0.0))
    return True, True


def _actuator(node, env):
    # This terminal is requested only after the formal choice root confirms.
    graph = env["__graph__"]
    root = graph.nodes["goal"]
    if root.state != NodeState.CONFIRMED:
        return True, False
    token = root.meta["emitted_actuator_identity"]
    env["port"].execute(token)
    node.meta["emitted"] = token
    return True, True


class TerminalDevelopment:
    """Persistent bound SCRIPT topology, scalar episodic feedback, local credit.

    Binding slots instantiate the same learned condition parameters. Each slot
    has distinct terminal nodes, so concurrent requests cannot share mutable
    readings. Slot identity/action spelling is never a learned feature.
    """

    def __init__(self, *, seed=1, config: DevelopmentConfig | None = None):
        self.config = config or DevelopmentConfig()
        self.rng = random.Random(seed)
        self.schema: tuple[Coordinate, ...] | None = None
        self.graph = Graph()
        self.graph.add_node(Node("goal", NodeType.SCRIPT, meta={"confirm_policy": "choice"}))
        self.graph.add_node(Node("catalog_root", NodeType.SCRIPT, meta={"confirm_policy": "and"}))
        self.graph.add_node(Node("catalog", NodeType.TERMINAL, predicate=_catalog))
        self.graph.add_hierarchy_pair("catalog_root", "catalog")
        self.graph.add_node(Node("execute", NodeType.SCRIPT, meta={"confirm_policy": "and"}))
        self.graph.add_node(Node("actuator", NodeType.TERMINAL, predicate=_actuator))
        self.graph.add_hierarchy_pair("execute", "actuator")
        self.conditions: dict[int, Condition] = {}
        self.bias = PlasticWeight()
        self.slots = 0
        self.completed = 0
        self.next_condition = 0
        self.pruned = 0
        self.pending: list[tuple[int, str, float, tuple[int, ...]]] = []
        self.last_event = -1

    def __getstate__(self):
        if self.pending:
            raise RuntimeError("checkpoint requires completed outcome feedback")
        return self.__dict__.copy()

    def _add_condition_slot(self, condition, slot):
        option = f"option:{slot}"
        gate = f"gate:{slot}:{condition.identity}"
        self.graph.add_node(Node(gate, NodeType.SCRIPT, meta={
            "confirm_policy": condition.operator, "condition_id": condition.identity,
        }))
        self.graph.nodes[gate].activation.value = 1.0
        self.graph.add_hierarchy_pair(option, gate)
        self.graph.edge_by_key[(gate, option, LinkType.SUR)].w = condition.weight
        for index, expected in condition.atoms:
            terminal = f"read:{slot}:{index}:{int(expected)}"
            if terminal not in self.graph.nodes:
                self.graph.add_node(Node(terminal, NodeType.TERMINAL, predicate=_reader,
                                         meta={"slot": slot, "atom": (index, expected)}))
            self.graph.add_hierarchy_pair(gate, terminal)

    def _ensure_slots(self, count):
        while self.slots < count:
            slot = self.slots
            option = f"option:{slot}"
            self.graph.add_node(Node(option, NodeType.SCRIPT, meta={
                "confirm_policy": "weighted_evidence", "actuator_identity": "unbound",
            }))
            self.graph.add_hierarchy_pair("goal", option)
            for kind, predicate, weight in (("bias", _constant, self.bias),
                                             ("explore", _exploration, 1.0)):
                nid = f"{kind}:{slot}"
                self.graph.add_node(Node(nid, NodeType.TERMINAL, predicate=predicate,
                                         meta={"slot": slot}))
                self.graph.add_hierarchy_pair(option, nid)
                self.graph.edge_by_key[(nid, option, LinkType.SUR)].w = weight
            for condition in self.conditions.values():
                self._add_condition_slot(condition, slot)
            self.slots += 1

    def _birth(self):
        if self.schema is None:
            return
        keys = {(c.operator, c.atoms) for c in self.conditions.values()}
        for _ in range(self.config.births_per_episode):
            if len(self.conditions) >= self.config.max_conditions:
                break
            indices = self.rng.sample(range(len(self.schema)), self.rng.randint(1, min(3, len(self.schema))))
            atoms = tuple(sorted((i, self.rng.choice(self.schema[i].values)) for i in indices))
            operator = self.rng.choices(("and", "or", "xor"), weights=(8, 1, 1))[0]
            if len(atoms) == 1:
                operator = "and"
            if (operator, atoms) in keys:
                continue
            condition = Condition(self.next_condition, atoms, operator, self.completed)
            self.next_condition += 1
            self.conditions[condition.identity] = condition
            keys.add((operator, atoms))
            for slot in range(self.slots):
                self._add_condition_slot(condition, slot)

    def _reset(self):
        for node in self.graph.nodes.values():
            node.state = NodeState.INACTIVE
            if "condition_id" not in node.meta:
                node.activation.value = 0.0
            node.meta.pop("choice_selected", None)
            node.meta.pop("choice_selected_child", None)
            node.meta.pop("emitted_actuator_identity", None)
            node.meta.pop("reading", None)
            node.meta.pop("emitted", None)

    def act(self, port: FeaturePort, *, event_id: int, learn: bool) -> str | None:
        if learn and event_id <= self.last_event:
            raise ValueError("action event must increase; cannot duplicate credit")
        if not learn and self.pending:
            raise RuntimeError("cannot evaluate during an unfinished episode")
        schema = tuple(port.schema)
        if not schema or not all(isinstance(c, Coordinate) for c in schema):
            raise ValueError("a fixed typed coordinate schema is required")
        if self.schema is not None and self.schema != schema:
            raise ValueError("feature schema changed; use a new organism")
        if self.schema is None:
            self.schema = schema
        self._reset()
        # The goal may have no options until the catalog terminal has read the
        # current legal bindings. Validate the complete graph after binding.
        engine = FormalReConEngine(self.graph, validate_pairs=False, record_trace=False)
        env = {"port": port, "schema": schema, "raise_terminal_errors": True}
        engine.request("catalog_root")
        engine.run(max_ticks=16, env=env,
                   until=lambda e: e.g.nodes["catalog_root"].state in (NodeState.CONFIRMED, NodeState.FAILED))
        catalog = self.graph.nodes["catalog"]
        if catalog.state != NodeState.CONFIRMED:
            raise RuntimeError("actuator catalog terminal failed")
        bindings = catalog.meta["reading"]
        if not bindings:
            raise ValueError("action request requires at least one available actuator binding")
        self._ensure_slots(len(bindings))
        self.graph.validate_formal_pairs()
        for slot in range(self.slots):
            node = self.graph.nodes[f"option:{slot}"]
            node.meta["actuator_identity"] = bindings[slot] if slot < len(bindings) else "unbound"
            if slot >= len(bindings):
                node.state = NodeState.FAILED
        exploration = {}
        if learn and self.rng.random() < self.config.exploration:
            # A bounded internal stochastic signal; no environment measurements
            # or outcome labels determine which legal binding is explored.
            bound = 1.0 + 2.0 * (abs(float(self.bias)) + sum(abs(float(c.weight)) for c in self.conditions.values()))
            exploration[self.rng.randrange(len(bindings))] = bound
        env.update(bindings=bindings, exploration=exploration)
        engine.request("goal")
        engine.run(max_ticks=40, env=env,
                   until=lambda e: e.g.nodes["goal"].state in (NodeState.CONFIRMED, NodeState.FAILED))
        token = engine.emit_exactly_one_actuator("goal")
        selected = self.graph.nodes["goal"].meta["choice_selected_child"]
        slot = int(selected.split(":")[1])
        active = tuple(cid for cid in self.conditions
                       if self.graph.nodes[f"gate:{slot}:{cid}"].state == NodeState.CONFIRMED)
        prediction = self.graph.nodes[selected].activation.value - exploration.get(slot, 0.0)
        engine.request("execute")
        engine.run(max_ticks=16, env=env,
                   until=lambda e: e.g.nodes["execute"].state in (NodeState.CONFIRMED, NodeState.FAILED))
        if self.graph.nodes["execute"].state != NodeState.CONFIRMED:
            raise RuntimeError("requested actuator failed")
        if learn:
            self.last_event = event_id
            self.pending.append((event_id, token, prediction, active))
        return token

    def observe(self, feedback):
        if not self.pending:
            raise RuntimeError("no episode awaiting outcome")
        if (feedback.event_id, feedback.action) != self.pending[-1][:2]:
            raise ValueError("outcome does not bind to the latest submitted action")
        reward = float(feedback.reward)
        if not math.isfinite(reward):
            raise ValueError("reward must be finite")
        # Eligibility carries final feedback backwards only along actions that
        # actually occurred. Unselected alternatives receive no weight update.
        length = len(self.pending)
        for step, (_, _, prediction, active) in enumerate(self.pending):
            eligibility = self.config.eligibility_decay ** (length - step - 1)
            delta = self.config.learning_rate * eligibility * (reward - prediction) / (1 + len(active))
            self.bias.fast += delta
            for cid in active:
                condition = self.conditions[cid]
                condition.weight.fast += delta
                condition.stats.record_activation("goal")
                condition.stats.record_confirm(self.completed, "goal")
                condition.stats.record_correlation("positive" if reward > 0 else "negative" if reward < 0 else "neutral")
            for condition in self.conditions.values():
                condition.stats.record_request("goal")
        for condition in self.conditions.values():
            if condition.stats.relevance_stats.activation_count >= 32:
                # Outcome correlation supports operational consolidation. It is
                # deliberately NOT counterfactual causal MATURE certification.
                condition.state = StemCellState.PROBATION
        self.pending.clear()
        self.completed += 1
        if self.completed % self.config.consolidate_every == 0:
            self.bias.consolidate(self.config.consolidation_rate)
            for condition in self.conditions.values():
                if condition.state == StemCellState.PROBATION:
                    condition.weight.consolidate(self.config.consolidation_rate)
            self._prune()
        self._birth()

    def _prune(self):
        # Terminal marginal usefulness is irrelevant: live compositions protect
        # all of their readers. Only aged, weak whole conditions are retired.
        doomed = {cid for cid, c in self.conditions.items()
                  if self.completed - c.born >= self.config.grace_episodes
                  and abs(float(c.weight)) < self.config.prune_weight}
        if not doomed:
            return
        remove = {f"gate:{slot}:{cid}" for slot in range(self.slots) for cid in doomed}
        for cid in doomed:
            self.conditions[cid].state = StemCellState.PRUNED
            del self.conditions[cid]
        for nid, node in self.graph.nodes.items():
            if node.predicate is _reader and all(parent in remove for parent in self.graph.all_parents(nid)):
                remove.add(nid)
        # Reindex without replacing surviving nodes/edges or their shared weight
        # objects. Graph currently has no complete remove-node API.
        survivors = [node for nid, node in self.graph.nodes.items() if nid not in remove]
        edges = [edge for edge in self.graph.edges if edge.src not in remove and edge.dst not in remove]
        graph = self.graph
        graph.__init__()
        for node in survivors:
            graph.add_node(node)
        for edge in edges:
            graph.add_edge(edge.src, edge.dst, edge.ltype)
            replacement = graph.edge_by_key[(edge.src, edge.dst, edge.ltype)]
            replacement.w, replacement.meta = edge.w, edge.meta
        self.pruned += len(doomed)
        graph.validate_formal_pairs()
