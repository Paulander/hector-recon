"""Bounded owner-local nomination from terminal observations and real residuals.

Fixed candidate-pool factorial control; not an open-ended developmental policy.
Existing ownership, compatibility and action-credit implementations are unchanged.
"""
import copy
import math
import random
from dataclasses import dataclass, replace

from recon_lite.graph import Node, NodeState, NodeType
from .compatible_owner import CompatibleOwnerDevelopment
from .recursive_context import Expression, SplitEvidence, combine
from .residual_shadow import random_definitions
from .terminal_development import Condition, PlasticWeight


@dataclass(frozen=True)
class BirthSearchConfig:
    mode: str = "random"
    extra_after_split: bool = False
    candidates: int = 24
    min_support: int = 4
    random_fraction: float = 0.25

    def __post_init__(self):
        if self.mode not in ("random", "residual"):
            raise ValueError("unknown birth selection mode")
        if type(self.extra_after_split) is not bool:
            raise ValueError("extra_after_split must be Boolean")
        if any(type(v) is not int or v < 1 for v in (self.candidates, self.min_support)):
            raise ValueError("positive candidate and support budgets required")
        if not math.isfinite(self.random_fraction) or not 0 < self.random_fraction <= 1:
            raise ValueError("a nonzero random eligibility path is required")


class BirthSearchOwnerDevelopment(CompatibleOwnerDevelopment):
    @classmethod
    def from_actor(cls, source, *, search=None, search_seed=0, **kwargs):
        actor = super().from_actor(source, **kwargs)
        actor.birth_search_config = search or BirthSearchConfig()
        actor.birth_definitions = random_definitions(
            actor.schema, seed=f"owner-birth-pool:{search_seed}",
            count=actor.birth_search_config.candidates)
        actor.birth_expressions = tuple(combine(d.operator, tuple(
            Expression("read", atom=a) for a in d.atoms)) for d in actor.birth_definitions)
        actor.birth_selection_rng = random.Random(f"owner-birth-selection:{search_seed}")
        actor.birth_evidence = {owner: [SplitEvidence() for _ in actor.birth_definitions]
                                for owner in actor.leaves}
        actor.birth_search_pending = None
        actor.birth_probe_nodes = {}
        actor.birth_nominations = []
        actor.deferred_development = None
        actor.last_route_observations = {}
        actor._rebuild(actor.slots)
        return actor

    def __getstate__(self):
        if (getattr(self, "birth_search_pending", None) is not None
                or getattr(self, "deferred_development", None) is not None):
            raise RuntimeError("checkpoint requires completed birth evidence")
        return super().__getstate__()

    def _ensure_slots(self, count):
        if not hasattr(self, "birth_definitions") or count <= self.slots:
            return super()._ensure_slots(count)
        old_graph, old_slots = self.graph, self.slots
        graph_backup = copy.deepcopy(old_graph)
        definitions = dict(self.expression_ids)
        probes, owner_probes = dict(self.birth_probe_nodes), dict(self.probe_nodes)
        try:
            super()._ensure_slots(count)
            for slot in range(self.slots):
                root = f"birth-probe:{slot}"
                if root in self.graph.nodes:
                    continue
                self.graph.add_node(Node(root, NodeType.SCRIPT,
                    meta={"confirm_policy": "weighted_evidence"}))
                nodes = []
                for expression in self.birth_expressions:
                    nid = self._expression_node(expression, slot, root)
                    nodes.append(nid)
                    self.graph.add_hierarchy_pair(root, nid)
                self.birth_probe_nodes[slot] = tuple(nodes)
            self.validate_ownership()
        except Exception:
            old_graph.__dict__ = graph_backup.__dict__
            self.graph, self.slots = old_graph, old_slots
            self.expression_ids, self.birth_probe_nodes = definitions, probes
            self.probe_nodes = owner_probes
            from recon_lite.graph import LinkType
            for slot in range(old_slots):
                self.graph.edge_by_key[(f"bias:{slot}", f"option:{slot}", LinkType.SUR)].w = self.bias
                for cid, condition in self.conditions.items():
                    self.graph.edge_by_key[(f"gate:{slot}:{cid}", f"option:{slot}", LinkType.SUR)].w = condition.weight
            raise

    def _before_execute(self, engine, env, *, event_id, slot, prediction, learn):
        super()._before_execute(engine, env, event_id=event_id, slot=slot,
                                prediction=prediction, learn=learn)
        if not learn:
            return
        root = f"birth-probe:{slot}"
        engine.request(root)
        engine.run(max_ticks=40, env=env, until=lambda e: self.graph.nodes[root].state
                   in (NodeState.CONFIRMED, NodeState.FAILED))
        states = tuple(self.graph.nodes[nid].state for nid in self.birth_probe_nodes[slot])
        if any(s not in (NodeState.CONFIRMED, NodeState.FAILED) for s in states):
            raise RuntimeError("birth candidate observations did not settle")
        self.birth_search_pending = (event_id, env["bindings"][slot], self.owner_pending[2],
                                      prediction, tuple(s == NodeState.CONFIRMED for s in states))

    def observe(self, feedback):
        pending = self.birth_search_pending
        if (pending is None or self.candidate_pending is None or self.owner_pending is None
                or len(self.pending) != 1
                or any((feedback.event_id, feedback.action) != p[:2]
                       for p in (pending, self.candidate_pending, self.owner_pending, self.pending[-1]))):
            raise ValueError("birth evidence requires the matching actual action")
        reward = float(feedback.reward)
        if not math.isfinite(reward):
            raise ValueError("reward must be finite")
        owner = pending[2]
        if owner != self.owner_pending[2] or owner != self.candidate_pending[2]:
            raise RuntimeError("birth evidence crossed ownership")
        route_values = self.candidate_pending[4]
        # Base applies actual credit and schedules (but defers) development.
        self.birth_search_pending = None
        super().observe(feedback)
        for evidence, active in zip(self.birth_evidence[owner], pending[4]):
            evidence.add(active, reward - pending[3])
        self.last_route_observations[owner] = route_values
        deferred = self.deferred_development
        self.deferred_development = None
        if deferred is not None:
            self._run_development(deferred)

    def _develop_owner(self, owner):
        if self.deferred_development is not None:
            raise RuntimeError("only one development opportunity per action")
        self.deferred_development = owner

    def _run_development(self, owner):
        super()._develop_owner(owner)
        split = self.development_history[-1]["split"]
        if split is not None and self.birth_search_config.extra_after_split:
            # Uses the formal state-only confirmation collected before execution.
            active = self.last_route_observations[owner][split["candidate"]]
            child = split["children"][int(active)]
            cid = self._birth_local(child)
            self.development_history[-1]["extra_birth"] = {"owner": child, "birth": cid}

    def split_decision(self, owner, route):
        children = super().split_decision(owner, route)
        for child in children:
            self.birth_evidence[child] = [SplitEvidence() for _ in self.birth_definitions]
        return children

    def _birth_local(self, owner):
        config = self.birth_search_config
        record = {"episode": self.completed, "owner": owner,
                  "local_visit": self.owner_visits[owner], "mode": config.mode,
                  "eligible": [], "scores": {}, "selected": None, "birth": None}
        self.birth_nominations.append(record)
        if len(self.conditions) >= self.ownership_limits.max_parameters:
            record["outcome"] = "parameter budget: no draw"
            return None
        for index, expression in enumerate(self.birth_expressions):
            if expression in self.owner_seen[owner]:
                continue
            verdict, _ = self._compatibility(owner, expression)
            if verdict.status == "impossible":
                continue
            record["eligible"].append(index)
            score = self.birth_evidence[owner][index].score(config.min_support)
            if score is not None and score > 0:
                record["scores"][index] = score
        if not record["eligible"]:
            record["outcome"] = "no eligible pool candidate"
            return None
        lottery = self.birth_selection_rng.random()
        fallback = self.birth_selection_rng.choice(record["eligible"])
        ranked = (config.mode == "residual" and lottery >= config.random_fraction
                  and bool(record["scores"]))
        selected = (max(record["scores"], key=lambda i: (record["scores"][i], -i))
                    if ranked else fallback)
        record.update(selected=selected, selection="residual" if ranked else "random",
                      lottery=lottery, evidence=copy.deepcopy(self.birth_evidence[owner][selected]))
        trial = copy.deepcopy(self)
        definition, expression = trial.birth_definitions[selected], trial.birth_expressions[selected]
        cid = trial.next_condition
        trial.next_condition += 1
        trial.conditions[cid] = Condition(cid, definition.atoms, definition.operator,
                                         trial.completed, weight=PlasticWeight())
        trial.base_expressions[cid] = expression
        trial.birth_visits[cid] = trial.owner_visits[owner]
        trial.owner_seen[owner].add(expression)
        trial.leaves[owner] = replace(trial.leaves[owner],
            contributions=(*trial.leaves[owner].contributions, cid))
        try:
            trial._rebuild(self.slots)
        except (ValueError, RuntimeError) as error:
            if "budget" not in str(error):
                raise
            record["outcome"] = "graph budget"
            return None
        trial.birth_nominations[-1].update(outcome="born", birth=cid)
        self.__dict__ = trial.__dict__
        return cid
