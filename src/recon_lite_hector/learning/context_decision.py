"""Mechanical prototype: whole-decision parameter ownership under Boolean routes.

The existing formal graph computes all predicates and action scores. This module
does not nominate routes, grow/prune automatically, or implement freezing. Tests
may plant splits to verify the operation before an autonomous development study.
"""
from dataclasses import dataclass
import copy
import math

from recon_lite.graph import LinkType, Node, NodeState, NodeType
from .recursive_context import Expression, RecursiveDevelopment, TRUE, combine, negate
from .terminal_development import ACTION_CHOICE, Condition, PlasticWeight, TerminalDevelopment


@dataclass(frozen=True)
class OwnershipLimits:
    max_leaves: int = 4
    max_parameters: int = 128  # Biases included; each has fast/slow storage.
    max_definitions: int = 160
    max_physical_nodes: int = 4096
    max_depth: int = 4

    def __post_init__(self):
        if any(type(v) is not int or v < 1 for v in vars(self).values()):
            raise ValueError("positive integer ownership budgets required")
        if self.max_depth > 4:
            raise ValueError("depth exceeds the unchanged formal tick budget")


@dataclass(frozen=True)
class DecisionLeaf:
    identity: int
    path: Expression
    contributions: tuple[int, ...]
    bias_id: int
    born: int
    parent: int | None = None


class ContextDecisionDevelopment(RecursiveDevelopment):
    """A local decision owns every weight that can affect its action ordering.

    Conversion and splitting operate on copies before committing. Child parameters
    inherit values, not aliased objects or invented context-specific observations.
    Immutable definitions may be shared; SCRIPT execution instances may not.
    """

    def __init__(self, *args, **kwargs):
        raise TypeError("use from_actor with an initialized recursive actor")

    def __getstate__(self):
        if self.owner_pending is not None:
            raise RuntimeError("checkpoint requires completed outcome feedback")
        return super().__getstate__()

    @classmethod
    def from_actor(cls, source, *, state_coordinates, limits=None):
        if type(source) is not RecursiveDevelopment or source.schema is None:
            raise ValueError("an initialized recursive actor is required")
        if source.pending or source.context_pending is not None:
            raise RuntimeError("conversion requires completed feedback")
        coordinates = tuple(state_coordinates)
        if (not coordinates or len(set(coordinates)) != len(coordinates)
                or any(type(i) is not int or not 0 <= i < len(source.schema)
                       for i in coordinates)):
            raise ValueError("declare distinct state coordinate indices")
        actor = cls.__new__(cls)
        actor.__dict__ = copy.deepcopy(source.__dict__)
        actor.ownership_limits = limits or OwnershipLimits()
        actor.state_coordinates = frozenset(coordinates)
        actor.base_expressions = dict(actor.expressions)
        actor.ownership_history = []
        actor.owner_pending = None
        actor.next_owner = 1
        actor.converted_at = source.completed
        # Preserve earlier nomination evidence as ancestry, not live owner data.
        actor.nomination_ancestry = {
            "contexts": actor.contexts, "evidence": actor.evidence,
            "source_splits": actor.splits,
        }
        actor.contexts, actor.evidence, actor.splits = None, {}, []
        bias_id = actor.next_condition
        actor.next_condition += 1
        actor.conditions[bias_id] = Condition(
            bias_id, (), "and", actor.completed, weight=actor.bias)
        actor.base_expressions[bias_id] = TRUE
        actor.bias = PlasticWeight()  # Fixed zero legacy bias/exploration bound.
        actor.leaves = {0: DecisionLeaf(
            0, TRUE, tuple(actor.conditions), bias_id, actor.completed)}
        actor._rebuild(source.slots)
        return actor

    def _check_route(self, route):
        if not isinstance(route, Expression):
            raise ValueError("route must be an immutable Boolean expression")
        readers = []
        stack = [route]
        while stack:
            expression = stack.pop()
            if expression.operator == "read":
                index, value = expression.atom
                if index not in self.state_coordinates:
                    raise ValueError("route may use only declared state coordinates")
                self.schema[index].validate(value)
                readers.append(expression)
            stack.extend(expression.children)
        if not readers or route.depth > self.ownership_limits.max_depth:
            raise ValueError("route requires readers within the depth budget")

    def _expression_node(self, expression, slot, owner=None):
        # The inherited compiler enforces the recursive actor's original limits;
        # ownership has independent whole-graph limits checked before allocation.
        if expression not in self.expression_ids:
            if len(self.expression_ids) >= self.ownership_limits.max_definitions:
                raise ValueError("ownership definition budget exhausted")
        if len(self.graph.nodes) >= self.ownership_limits.max_physical_nodes:
            raise ValueError("ownership physical node budget exhausted")
        return super()._expression_node(expression, slot, owner)

    def _add_condition_slot(self, condition, slot):
        # An owned bias is TRUE and has no atoms; the legacy compiler's eagerly
        # evaluated flat-expression default does not accept that representation.
        expression = self.expressions[condition.identity]
        gate, option = f"gate:{slot}:{condition.identity}", f"option:{slot}"
        node = Node(gate, NodeType.SCRIPT, meta={
            "confirm_policy": "and", "condition_id": condition.identity})
        node.activation.value = 1.0
        self.graph.add_node(node)
        self.graph.add_hierarchy_pair(option, gate)
        self.graph.edge_by_key[(gate, option, LinkType.SUR)].w = condition.weight
        self.graph.add_hierarchy_pair(gate, self._expression_node(expression, slot, gate))

    def _rebuild(self, slots):
        from dataclasses import replace

        limits = self.ownership_limits
        if len(self.leaves) > limits.max_leaves or len(self.conditions) > limits.max_parameters:
            raise ValueError("ownership parameter/leaf budget exhausted")
        for leaf in self.leaves.values():
            for cid in leaf.contributions:
                source = self.base_expressions[cid]
                expression = source if leaf.path == TRUE else combine("and", (source, leaf.path))
                if expression.depth > limits.max_depth:
                    raise ValueError("ownership expression depth budget exhausted")
                self.expressions[cid] = expression
        self.recursive_config = replace(
            self.recursive_config, max_definitions=limits.max_definitions,
            max_physical_nodes=limits.max_physical_nodes)
        # Recompile execution instances; historical definitions/evidence remain.
        self.graph = TerminalDevelopment(config=self.config).graph
        self.slots = 0
        self._ensure_slots(slots)
        self.validate_ownership()

    def _ensure_slots(self, count):
        if count <= self.slots:
            return
        # Slot expansion also commits atomically if it exceeds a physical budget.
        graph, slots, definitions = self.graph, self.slots, dict(self.expression_ids)
        self.graph = copy.deepcopy(graph)
        # Deepcopy clones old edge weights; restore their parameter ownership.
        for slot in range(slots):
            for cid, condition in self.conditions.items():
                self.graph.edge_by_key[(f"gate:{slot}:{cid}", f"option:{slot}", LinkType.SUR)].w = condition.weight
            self.graph.edge_by_key[(f"bias:{slot}", f"option:{slot}", LinkType.SUR)].w = self.bias
        try:
            super()._ensure_slots(count)
            if len(self.graph.nodes) > self.ownership_limits.max_physical_nodes:
                raise ValueError("ownership physical node budget exhausted")
        except Exception:
            self.graph, self.slots, self.expression_ids = graph, slots, definitions
            raise
        # An active FormalReConEngine can already hold this Graph reference.
        graph.__dict__ = self.graph.__dict__
        self.graph = graph

    def split_decision(self, owner, route):
        """Planted mechanical operation; no diagnostic route enters a training run."""
        if self.pending or self.owner_pending is not None:
            raise RuntimeError("split requires completed feedback")
        self._check_route(route)
        if owner not in self.leaves:
            raise ValueError("split requires a live decision owner")
        trial = copy.deepcopy(self)
        parent = trial.leaves.pop(owner)
        children = []
        for enabled in (False, True):
            branch = route if enabled else negate(route)
            path = branch if parent.path == TRUE else combine("and", (parent.path, branch))
            identities, bias_id = [], None
            for cid in parent.contributions:
                old = trial.conditions[cid]
                identity = trial.next_condition
                trial.next_condition += 1
                trial.conditions[identity] = Condition(
                    identity, old.atoms, old.operator, trial.completed,
                    weight=copy.copy(old.weight))
                trial.base_expressions[identity] = trial.base_expressions[cid]
                identities.append(identity)
                if cid == parent.bias_id:
                    bias_id = identity
            child = trial.next_owner
            trial.next_owner += 1
            trial.leaves[child] = DecisionLeaf(
                child, path, tuple(identities), bias_id, trial.completed, owner)
            children.append(child)
        trial.ownership_history.append({
            "episode": trial.completed, "parent": parent, "route": route,
            "children": tuple(children),
            "conditions": tuple(trial.conditions.pop(cid) for cid in parent.contributions),
        })
        trial._rebuild(self.slots)
        self.__dict__ = trial.__dict__
        return tuple(children)

    def _before_execute(self, engine, env, *, event_id, slot, prediction, learn):
        # Read graph confirmations only, never the port or a Python predicate.
        owners = []
        for binding_slot in range(len(env["bindings"])):
            matching = [leaf.identity for leaf in self.leaves.values()
                        if self.graph.nodes[f"gate:{binding_slot}:{leaf.bias_id}"].state
                        == NodeState.CONFIRMED]
            if len(matching) != 1:
                raise RuntimeError("routing must select exactly one decision owner")
            owners.append(matching[0])
        if len(set(owners)) != 1:
            raise RuntimeError("declared state route differs across action bindings")
        if learn:
            self.owner_pending = (event_id, env["bindings"][slot], owners[slot])

    def observe(self, feedback):
        if (not self.pending or self.owner_pending is None
                or (feedback.event_id, feedback.action) != self.pending[-1][:2]
                or (feedback.event_id, feedback.action) != self.owner_pending[:2]):
            raise ValueError("outcome must bind to the pending actual action")
        reward = float(feedback.reward)
        if not math.isfinite(reward):
            raise ValueError("reward must be finite")
        _, _, owner = self.owner_pending
        leaf = self.leaves[owner]
        _, _, prediction, active = self.pending[-1]
        if leaf.bias_id not in active or not set(active) <= set(leaf.contributions):
            raise RuntimeError("credit crossed decision ownership")
        # Bias is an explicit active contribution here: len(active) == 1+k.
        delta = self.config.learning_rate * (reward - prediction) / len(active)
        for cid in active:
            condition = self.conditions[cid]
            condition.weight.fast += delta
            condition.stats.record_activation(ACTION_CHOICE)
            condition.stats.record_confirm(self.completed, ACTION_CHOICE)
            condition.stats.record_correlation(
                "positive" if reward > 0 else "negative" if reward < 0 else "neutral")
        for cid in leaf.contributions:
            self.conditions[cid].stats.record_request(ACTION_CHOICE)
        self.pending.clear()
        self.owner_pending = None
        self.completed += 1
        if self.completed % self.config.consolidate_every == 0:
            self.conditions[leaf.bias_id].weight.consolidate(self.config.consolidation_rate)
        # No automatic lifecycle yet. This is explicitly a fixed-topology fixture.

    def validate_ownership(self):
        limits = self.ownership_limits
        all_ids = [cid for leaf in self.leaves.values() for cid in leaf.contributions]
        if len(all_ids) != len(set(all_ids)) or set(all_ids) != set(self.conditions):
            raise ValueError("a scoring parameter must have exactly one owner")
        if len({id(c.weight) for c in self.conditions.values()}) != len(all_ids):
            raise ValueError("scoring parameters alias across contributions")
        if (float(self.bias) != 0 or len(self.leaves) > limits.max_leaves
                or len(all_ids) > limits.max_parameters
                or len(self.expression_ids) > limits.max_definitions
                or len(self.graph.nodes) > limits.max_physical_nodes):
            raise ValueError("ownership or fixed-zero bias budget violated")
        self.graph.validate_formal_pairs()
        for nid, node in self.graph.nodes.items():
            parents = self.graph.all_parents(nid)
            if node.ntype == NodeType.TERMINAL and self.graph.children(nid):
                raise ValueError("terminals must remain leaves")
            if node.ntype == NodeType.SCRIPT and len(parents) > 1:
                raise ValueError("SCRIPT instances require one owning parent")
        for slot in range(self.slots):
            for cid, condition in self.conditions.items():
                edge = self.graph.edge_by_key[(f"gate:{slot}:{cid}", f"option:{slot}", LinkType.SUR)]
                if edge.w is not condition.weight:
                    raise ValueError("graph score disconnected from owned credit")

    def refine(self, *args, **kwargs):
        raise RuntimeError("use split_decision; contributor refinement is a separate control")

    def _birth(self):
        raise RuntimeError("automatic owner development is not implemented")

    def _prune(self):
        raise RuntimeError("automatic owner retirement is not implemented")
