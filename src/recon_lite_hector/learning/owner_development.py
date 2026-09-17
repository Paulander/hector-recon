"""Experience-driven nomination and local lifecycle for context-owned decisions.

This is a supplied generic developmental law. It observes formal confirmations
and actual selected-action reward; it never receives task or curriculum labels.
"""
from dataclasses import dataclass, replace
import copy
import math

from recon_lite.graph import LinkType, Node, NodeState, NodeType
from .context_decision import ContextDecisionDevelopment
from .recursive_context import Expression, SplitEvidence, combine
from .terminal_development import Condition, PlasticWeight


@dataclass(frozen=True)
class OwnerDevelopmentConfig:
    split_enabled: bool = True
    develop_every: int = 64
    candidates: int = 12
    min_support: int = 4

    def __post_init__(self):
        if type(self.split_enabled) is not bool:
            raise ValueError("split_enabled must be Boolean")
        if any(type(v) is not int or v < 1 for v in
               (self.develop_every, self.candidates, self.min_support)):
            raise ValueError("positive owner development budgets required")


class AdaptiveOwnerDevelopment(ContextDecisionDevelopment):
    @classmethod
    def from_actor(cls, source, *, state_coordinates, limits=None, development=None):
        actor = super().from_actor(source, state_coordinates=state_coordinates, limits=limits)
        actor.development_config = development or OwnerDevelopmentConfig()
        pool = {Expression("read", atom=(i, value)) for i in actor.state_coordinates
                for value in actor.schema[i].values}
        for expression in actor.base_expressions.values():
            try:
                actor._check_route(expression)
            except ValueError:
                continue
            if expression.depth <= 2:
                pool.add(expression)
        actor.owner_candidates = tuple(actor.proposal_rng.sample(
            sorted(pool, key=repr), min(len(pool), actor.development_config.candidates)))
        actor.candidate_pending = None
        actor.owner_visits = {0: actor.completed}
        actor.owner_evidence = {0: {}}
        actor.birth_visits = {cid: c.born for cid, c in actor.conditions.items()}
        actor.owner_seen = {0: {actor.base_expressions[cid] for cid in actor.conditions}}
        actor.development_history = []
        actor.retirement_history = []
        actor.probe_nodes = {}
        actor._rebuild(actor.slots)
        return actor

    def __getstate__(self):
        if getattr(self, "candidate_pending", None) is not None:
            raise RuntimeError("checkpoint requires completed candidate feedback")
        return super().__getstate__()

    def _ensure_slots(self, count):
        if not hasattr(self, "owner_candidates"):
            return super()._ensure_slots(count)
        if count <= self.slots:
            return
        old_graph, old_slots = self.graph, self.slots
        backup = copy.deepcopy(old_graph)
        definitions, probes = dict(self.expression_ids), dict(self.probe_nodes)
        try:
            super()._ensure_slots(count)
            for slot in range(self.slots):
                root = f"owner-probe:{slot}"
                if root in self.graph.nodes:
                    continue
                self.graph.add_node(Node(root, NodeType.SCRIPT,
                                         meta={"confirm_policy": "weighted_evidence"}))
                nodes = []
                for candidate in self.owner_candidates:
                    nid = self._expression_node(candidate, slot, root)
                    nodes.append(nid)
                    self.graph.add_hierarchy_pair(root, nid)
                self.probe_nodes[slot] = tuple(nodes)
            self.validate_ownership()
        except Exception:
            old_graph.__dict__ = backup.__dict__
            self.graph, self.slots = old_graph, old_slots
            self.expression_ids, self.probe_nodes = definitions, probes
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
        root = f"owner-probe:{slot}"
        try:
            engine.request(root)
            engine.run(max_ticks=40, env=env,
                       until=lambda e: self.graph.nodes[root].state == NodeState.CONFIRMED)
            states = tuple(self.graph.nodes[nid].state for nid in self.probe_nodes[slot])
            if any(s not in (NodeState.CONFIRMED, NodeState.FAILED) for s in states):
                raise RuntimeError("candidate observations did not settle")
            self.candidate_pending = (event_id, env["bindings"][slot], self.owner_pending[2],
                                      prediction, tuple(s == NodeState.CONFIRMED for s in states))
        except Exception:
            self.owner_pending = None
            raise

    def observe(self, feedback):
        if (not self.pending or self.owner_pending is None or self.candidate_pending is None
                or (feedback.event_id, feedback.action) != self.pending[-1][:2]
                or (feedback.event_id, feedback.action) != self.owner_pending[:2]
                or (feedback.event_id, feedback.action) != self.candidate_pending[:2]):
            raise ValueError("outcome must bind to the pending actual action")
        reward = float(feedback.reward)
        if not math.isfinite(reward):
            raise ValueError("reward must be finite")
        _, _, owner, prediction, observations = self.candidate_pending
        if owner != self.owner_pending[2]:
            raise RuntimeError("candidate evidence crossed ownership")
        # Super consumes exactly the original action's credit, including bias.
        super().observe(feedback)
        evidence = self.owner_evidence[owner]
        for index, enabled in enumerate(observations):
            evidence.setdefault(index, SplitEvidence()).add(enabled, reward - prediction)
        self._record_nomination_outcome(owner, feedback.action, reward - prediction, observations)
        self.candidate_pending = None
        self.owner_visits[owner] += 1
        if self.owner_visits[owner] % self.development_config.develop_every == 0:
            self._develop_owner(owner)

    def _record_nomination_outcome(self, owner, action, residual, observations):
        """Extension point for owner-local evidence from the executed action only."""

    def split_decision(self, owner, route):
        children = super().split_decision(owner, route)
        for child in children:
            self.owner_visits[child] = 0
            self.owner_evidence[child] = {}
            self.owner_seen[child] = {self.base_expressions[cid]
                                      for cid in self.leaves[child].contributions}
            for cid in self.leaves[child].contributions:
                self.birth_visits[cid] = 0
        return children

    def _retire_local(self, owner):
        leaf = self.leaves[owner]
        doomed = [cid for cid in leaf.contributions if cid != leaf.bias_id
                  and self.owner_visits[owner] - self.birth_visits[cid] >= self.config.grace_episodes
                  and abs(float(self.conditions[cid].weight)) < self.config.prune_weight]
        if not doomed:
            return ()
        trial = copy.deepcopy(self)
        for cid in doomed:
            trial.retirement_history.append({
                "episode": trial.completed, "owner": owner, "path": leaf.path,
                "local_visit": trial.owner_visits[owner],
                "condition": trial.conditions.pop(cid), "expression": trial.base_expressions[cid]})
        trial.leaves[owner] = replace(leaf, contributions=tuple(
            cid for cid in leaf.contributions if cid not in doomed))
        trial.pruned += len(doomed)
        trial._rebuild(self.slots)
        self.__dict__ = trial.__dict__
        return tuple(doomed)

    def _birth_local(self, owner):
        if len(self.conditions) >= self.ownership_limits.max_parameters:
            return None
        rng = self.proposal_rng
        indices = rng.sample(range(len(self.schema)), rng.randint(1, min(3, len(self.schema))))
        atoms = tuple(sorted((i, rng.choice(self.schema[i].values)) for i in indices))
        operator = rng.choices(("and", "or", "xor"), weights=(8, 1, 1))[0] if len(atoms) > 1 else "and"
        expression = combine(operator, tuple(Expression("read", atom=atom) for atom in atoms))
        if expression in self.owner_seen[owner]:
            return None
        trial = copy.deepcopy(self)
        cid = trial.next_condition
        trial.next_condition += 1
        trial.conditions[cid] = Condition(cid, atoms, operator, trial.completed, weight=PlasticWeight())
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
            return None
        self.__dict__ = trial.__dict__
        return cid

    def _develop_owner(self, owner):
        retired = self._retire_local(owner)
        event = {"episode": self.completed, "owner": owner,
                 "local_visit": self.owner_visits[owner], "retired": retired,
                 "split": None, "birth": None, "budget_rejections": []}
        if (self.development_config.split_enabled
                and len(self.leaves) < self.ownership_limits.max_leaves):
            choices = []
            for index, evidence in self.owner_evidence[owner].items():
                score = evidence.score(self.development_config.min_support)
                if score is not None and score > 0:
                    choices.append((score, index))
            for score, index in sorted(choices, key=lambda pair: (-pair[0], pair[1])):
                evidence = copy.deepcopy(self.owner_evidence[owner][index])
                try:
                    children = self.split_decision(owner, self.owner_candidates[index])
                except (ValueError, RuntimeError) as error:
                    if "budget" not in str(error):
                        raise
                    event["budget_rejections"].append({"candidate": index, "reason": str(error)})
                    continue
                event["split"] = {"candidate": index, "route": self.owner_candidates[index],
                                  "score": score, "evidence": evidence, "children": children}
                break
        if event["split"] is None:
            event["birth"] = self._birth_local(owner)
        self.development_history.append(event)
