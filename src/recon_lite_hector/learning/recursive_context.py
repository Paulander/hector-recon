"""Experimental recursive evidence reuse and local context specialization.

Only ordinary input terminals read the environment. Formal SCRIPTs calculate
every expression and choose the action. Residual statistics concern the actual
selected binding, never alternative outcomes. This is not goal arbitration.
"""
from dataclasses import dataclass
import copy
import math
import random

from recon_lite.graph import LinkType, Node, NodeState, NodeType
from .terminal_development import (
    Condition, PlasticWeight, TerminalDevelopment, _constant, _reader,
)


@dataclass(frozen=True)
class Expression:
    operator: str
    children: tuple = ()
    atom: tuple | None = None

    def __post_init__(self):
        if self.operator == "read":
            if (self.children or self.atom is None or len(self.atom) != 2
                    or type(self.atom[0]) is not int or self.atom[0] < 0
                    or type(self.atom[1]) not in (bool, int)):
                raise ValueError("reader requires one typed equality atom")
        elif self.operator == "true":
            if self.children or self.atom is not None:
                raise ValueError("constant must be a leaf")
        elif (self.operator not in ("and", "or", "xor") or self.atom is not None
              or len(self.children) < 2 or any(not isinstance(c, Expression) for c in self.children)):
            raise ValueError("invalid recursive Boolean expression")

    @property
    def depth(self):
        return 0 if not self.children else 1 + max(x.depth for x in self.children)


TRUE = Expression("true")


def combine(operator, children):
    children = tuple(children)
    if operator == "xor" and len(set(children)) != len(children):
        raise ValueError("exactly-one requires distinct child identities")
    children = tuple(sorted(set(children), key=repr))
    if operator not in ("and", "or", "xor") or not children:
        raise ValueError("nonempty Boolean composition required")
    if len(children) == 1:
        return children[0]
    return Expression(operator, children)


def negate(expression):
    # Exactly-one of TRUE and X implements NOT X, including integer readers.
    return combine("xor", (TRUE, expression))


def flat_expression(condition):
    return combine(condition.operator,
                   [Expression("read", atom=atom) for atom in condition.atoms])


@dataclass(frozen=True)
class RecursiveConfig:
    role: str = "ranked"
    prefix: int = 256
    grow_every: int = 128
    candidates: int = 12
    min_support: int = 4
    max_depth: int = 4
    max_splits: int = 6
    max_definitions: int = 160
    max_physical_nodes: int = 4096

    def __post_init__(self):
        if self.role not in ("flat", "random", "ranked"):
            raise ValueError("role must be flat, random or ranked")
        if min(self.prefix, self.grow_every, self.candidates, self.min_support,
               self.max_splits, self.max_definitions, self.max_physical_nodes) < 1:
            raise ValueError("positive finite budgets required")
        if not 1 <= self.max_depth <= 4:
            raise ValueError("depth 1..4 fits the unchanged formal tick budget")


@dataclass
class SplitEvidence:
    n0: int = 0
    n1: int = 0
    sum0: float = 0.0
    sum1: float = 0.0

    def add(self, enabled, residual):
        if enabled:
            self.n1 += 1
            self.sum1 += residual
        else:
            self.n0 += 1
            self.sum0 += residual

    def score(self, minimum):
        if min(self.n0, self.n1) < minimum:
            return None
        difference = self.sum1 / self.n1 - self.sum0 / self.n0
        return self.n0 * self.n1 / (self.n0 + self.n1) * difference ** 2


class RecursiveDevelopment(TerminalDevelopment):
    """A contributor may be refined into two disjoint, independently plastic paths.

    w*f becomes w0*(f AND NOT g) + w1*(f AND g), initially w0=w1=w.
    Old expression structure and historical evidence remain. Its direct scoring
    edge is removed, so knowledge is inherited without double-counting support.
    Other contributors and the ordinary selected-action credit law stay plastic.
    """

    def __init__(self, *, seed=1, config=None, recursive_config=None):
        super().__init__(seed=seed, config=config)
        self.recursive_config = recursive_config or RecursiveConfig()
        self.proposal_rng = random.Random(f"recursive:{seed}")
        self.exploration_rng = random.Random(f"recursive-exploration:{seed}")
        self.expressions = {}
        self.expression_ids = {}
        self.seen = set()
        self.history = []
        self.splits = []
        self.contexts = None
        self.evidence = {}
        self.context_pending = None
        self.generation = {}

    def act(self, port, *, event_id, learn):
        if self.context_pending is not None or self.pending:
            raise RuntimeError("recursive prototype requires immediate actual feedback")
        if self.completed < self.recursive_config.prefix:
            return super().act(port, event_id=event_id, learn=learn)
        # All roles switch together after the common prefix. Growth no longer
        # consumes their matched exploration stream.
        birth_rng = self.rng
        self.rng = self.exploration_rng
        try:
            return super().act(port, event_id=event_id, learn=learn)
        finally:
            self.rng = birth_rng

    def _expression_node(self, expression, slot, owner=None):
        identity = self.expression_ids.setdefault(expression, len(self.expression_ids))
        nid = f"expr:{slot}:{identity}"
        if expression.children:
            if owner is None:
                raise ValueError("SCRIPT instances require an owning request site")
            nid += f":in:{owner}"
        if nid in self.graph.nodes:
            return nid
        if len(self.expression_ids) > self.recursive_config.max_definitions:
            raise RuntimeError("expression definition budget exhausted")
        if len(self.graph.nodes) >= self.recursive_config.max_physical_nodes:
            raise RuntimeError("physical graph budget exhausted")
        if expression.operator == "read":
            index, expected = expression.atom
            if index >= len(self.schema):
                raise ValueError("reader coordinate outside schema")
            self.schema[index].validate(expected)
            node = Node(nid, NodeType.TERMINAL, predicate=_reader,
                        meta={"slot": slot, "atom": expression.atom})
        elif expression.operator == "true":
            node = Node(nid, NodeType.TERMINAL, predicate=_constant)
        else:
            node = Node(nid, NodeType.SCRIPT,
                        meta={"confirm_policy": expression.operator,
                              "recursive_expression": True, "definition_id": identity})
            node.activation.value = 1.0
        self.graph.add_node(node)
        for child in expression.children:
            self.graph.add_hierarchy_pair(nid, self._expression_node(child, slot, nid))
        return nid

    def _add_condition_slot(self, condition, slot):
        expression = self.expressions.setdefault(condition.identity, flat_expression(condition))
        self.seen.add(expression)
        self.generation.setdefault(condition.identity, 0)
        gate, option = f"gate:{slot}:{condition.identity}", f"option:{slot}"
        self.graph.add_node(Node(gate, NodeType.SCRIPT, meta={
            "confirm_policy": "and", "condition_id": condition.identity}))
        self.graph.nodes[gate].activation.value = 1.0
        self.graph.add_hierarchy_pair(option, gate)
        self.graph.edge_by_key[(gate, option, LinkType.SUR)].w = condition.weight
        self.graph.add_hierarchy_pair(gate, self._expression_node(expression, slot, gate))

    def _reset(self):
        super()._reset()
        for node in self.graph.nodes.values():
            if node.meta.get("recursive_expression"):
                node.activation.value = 1.0

    def _remove_contributions(self, identities, reason):
        remove = {f"gate:{slot}:{cid}" for slot in range(self.slots) for cid in identities}
        todo = list(remove)
        while todo:
            for child in self.graph.children(todo.pop()):
                if self.graph.nodes[child].ntype == NodeType.SCRIPT and child not in remove:
                    remove.add(child)
                    todo.append(child)
        for cid in sorted(identities):
            condition = self.conditions.pop(cid)
            self.history.append({"reason": reason, "episode": self.completed,
                                 "condition": condition, "expression": self.expressions[cid]})
        # Reuse the surviving physical nodes/edges and shared expression nodes.
        nodes = [n for nid, n in self.graph.nodes.items() if nid not in remove]
        edges = [e for e in self.graph.edges if e.src not in remove and e.dst not in remove]
        self.graph.__init__()
        for n in nodes:
            self.graph.add_node(n)
        for e in edges:
            self.graph.add_edge(e.src, e.dst, e.ltype)
            edge = self.graph.edge_by_key[(e.src, e.dst, e.ltype)]
            edge.w, edge.meta = e.w, e.meta

    def _prune(self):
        doomed = {cid for cid, c in self.conditions.items()
                  if self.completed - c.born >= self.config.grace_episodes
                  and abs(float(c.weight)) < self.config.prune_weight}
        if doomed:
            self._remove_contributions(doomed, "weak")
            self.pruned += len(doomed)

    def _flat_birth(self, attempts):
        for _ in range(attempts):
            if len(self.conditions) >= self.config.max_conditions:
                return
            indices = self.rng.sample(range(len(self.schema)), self.rng.randint(1, min(3, len(self.schema))))
            atoms = tuple(sorted((i, self.rng.choice(self.schema[i].values)) for i in indices))
            operator = self.rng.choices(("and", "or", "xor"), weights=(8, 1, 1))[0]
            if len(atoms) == 1:
                operator = "and"
            c = Condition(self.next_condition, atoms, operator, self.completed)
            expression = flat_expression(c)
            if expression in self.seen:
                continue
            self.next_condition += 1
            self.conditions[c.identity] = c
            self.expressions[c.identity] = expression
            self.seen.add(expression)
            for slot in range(self.slots):
                self._add_condition_slot(c, slot)

    def _birth(self):
        if self.schema is None:
            return
        cfg = self.recursive_config
        if self.completed <= cfg.prefix:
            self._flat_birth(self.config.births_per_episode)
        elif (self.completed - cfg.prefix) % cfg.grow_every == 0:
            if (cfg.role != "flat" and len(self.splits) < cfg.max_splits
                    and len(self.conditions) < self.config.max_conditions):
                choices = []
                for (cid, index), evidence in self.evidence.items():
                    if cid not in self.conditions:
                        continue
                    score = evidence.score(cfg.min_support)
                    context = self.contexts[index]
                    children = self._split_expressions(cid, context)
                    if (score is not None and max(x.depth for x in children) <= cfg.max_depth
                            and all(x not in self.seen for x in children)):
                        choices.append((score, cid, index))
                if choices:
                    choice = (max(choices, key=lambda x: (x[0], -x[1], -x[2]))
                              if cfg.role == "ranked" else self.proposal_rng.choice(choices))
                    score, cid, index = choice
                    self.refine(cid, self.contexts[index], evidence_score=score)
                    return
            # A failed nomination gets the same bounded fresh-proposal opportunity.
            self._flat_birth(1)

    def _split_expressions(self, cid, context):
        source = self.expressions[cid]
        return (combine("and", (source, negate(context))),
                combine("and", (source, context)))

    def refine(self, cid, context, *, evidence_score=None):
        """Generic local mutation. Tests may call directly; training uses _birth."""
        if self.pending:
            raise RuntimeError("refinement requires completed action feedback")
        cfg = self.recursive_config
        expressions = self._split_expressions(cid, context)
        if (len(self.conditions) >= self.config.max_conditions
                or len(self.splits) >= cfg.max_splits
                or max(x.depth for x in expressions) > cfg.max_depth
                or any(x in self.seen for x in expressions)):
            raise ValueError("split exceeds budget or duplicates an existing hypothesis")
        parent = self.conditions[cid]
        inherited = float(parent.weight)
        children = []
        for expression in expressions:
            child = Condition(self.next_condition, parent.atoms, parent.operator,
                              self.completed, weight=copy.copy(parent.weight))
            self.next_condition += 1
            self.conditions[child.identity] = child
            self.expressions[child.identity] = expression
            self.generation[child.identity] = self.generation[cid] + 1
            self.seen.add(expression)
            children.append(child.identity)
            for slot in range(self.slots):
                self._add_condition_slot(child, slot)
        self._remove_contributions({cid}, "refined")
        self.splits.append({"episode": self.completed, "parent": cid,
                            "children": tuple(children), "context": context,
                            "inherited_weight": inherited, "score": evidence_score})
        self.graph.validate_formal_pairs()
        return tuple(children)

    def _init_contexts(self):
        # Reuse actual definitions plus raw equality readers. No coordinate name,
        # action spelling, task identity or marginal-usefulness filter is read.
        pool = {Expression("read", atom=(i, v)) for i, c in enumerate(self.schema) for v in c.values}
        pool.update(self.expressions[cid] for cid in self.conditions)
        pool = sorted((x for x in pool if x.depth <= 2), key=repr)
        self.contexts = tuple(self.proposal_rng.sample(pool, min(len(pool), self.recursive_config.candidates)))

    def _before_execute(self, engine, env, *, event_id, slot, prediction, learn):
        if not learn or self.completed < self.recursive_config.prefix:
            return
        if self.contexts is None:
            self._init_contexts()
        root = f"context-probe:{slot}"
        if root not in self.graph.nodes:
            self.graph.add_node(Node(root, NodeType.SCRIPT, meta={"confirm_policy": "weighted_evidence"}))
            for context in self.contexts:
                self.graph.add_hierarchy_pair(root, self._expression_node(context, slot, root))
        engine.request(root)
        engine.run(max_ticks=40, env=env, until=lambda e: self.graph.nodes[root].state == NodeState.CONFIRMED)
        states = tuple(self.graph.nodes[self._expression_node(c, slot, root)].state for c in self.contexts)
        if any(s not in (NodeState.CONFIRMED, NodeState.FAILED) for s in states):
            raise RuntimeError("context observation did not settle")
        self.context_pending = (event_id, env["bindings"][slot], prediction,
                                tuple(s == NodeState.CONFIRMED for s in states))

    def observe(self, feedback):
        if not self.pending or (feedback.event_id, feedback.action) != self.pending[-1][:2]:
            raise ValueError("outcome must bind to the pending actual action")
        reward = float(feedback.reward)
        if not math.isfinite(reward):
            raise ValueError("reward must be finite")
        if self.context_pending is not None:
            event, action, prediction, contexts = self.context_pending
            if (event, action) != (feedback.event_id, feedback.action):
                raise ValueError("context commitment does not match actual action")
            for cid in self.pending[-1][3]:
                for index, enabled in enumerate(contexts):
                    self.evidence.setdefault((cid, index), SplitEvidence()).add(enabled, reward - prediction)
        self.context_pending = None
        # Unchanged scalar error, active-participant normalization and learning.
        # _birth is called only after pending feedback has been consumed.
        super().observe(feedback)
