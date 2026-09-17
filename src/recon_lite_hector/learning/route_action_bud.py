"""A state route can grow an action-sensitive contributor without owner fission.

This bounded pilot keeps the existing formal scorer and selected-action reward law.
The only new authority is to compose two *observed terminal* predicates: a
state-only route from the owner's local pool and an action-varying reader. The
new SUR weight is zero at birth, so construction itself changes no decision.
"""
import copy
from dataclasses import dataclass, field, replace

from recon_lite.graph import Node, NodeState, NodeType

from .fresh_owner import FreshOwnerDevelopment
from .recursive_context import Expression, combine
from .terminal_development import Condition, PlasticWeight


@dataclass
class RouteActionEvidence:
    """Actual-action residual interaction, never alternative-action rewards."""

    counts: dict = field(default_factory=dict)
    sums: dict = field(default_factory=dict)
    variable: int = 0

    def add(self, route, reader, variable, residual):
        key = (bool(route), bool(reader))
        self.counts[key] = self.counts.get(key, 0) + 1
        self.sums[key] = self.sums.get(key, 0.0) + residual
        self.variable += bool(variable)

    def score(self, minimum):
        keys = ((False, False), (False, True), (True, False), (True, True))
        if self.variable < minimum or min(self.counts.get(key, 0) for key in keys) < minimum:
            return None
        mean = {key: self.sums[key] / self.counts[key] for key in keys}
        contrast = ((mean[True, True] - mean[True, False])
                    - (mean[False, True] - mean[False, False]))
        return contrast * contrast / sum(1 / self.counts[key] for key in keys)


class RouteActionBudDevelopment(FreshOwnerDevelopment):
    """Add a zero-weight route×affordance gate to its current scorer.

    No child owner is created. At each ordinary owner development opportunity,
    a supported interaction takes the same one birth slot as a normal birth.
    If none qualifies, the existing local birth search remains available.
    """

    @classmethod
    def from_actor(cls, source, **kwargs):
        actor = super().from_actor(source, **kwargs)
        actor.action_readers = tuple(Expression('read', atom=(i, value))
            for i, coordinate in enumerate(actor.schema)
            if i not in actor.state_coordinates for value in coordinate.values)
        if not actor.action_readers:
            raise ValueError('route-action budding needs a declared action-varying coordinate')
        actor.action_probe_nodes = {}
        actor.action_bud_pending = None
        actor.action_bud_evidence = {owner: {} for owner in actor.leaves}
        actor.action_bud_history = []
        actor._rebuild(actor.slots)
        return actor

    def __getstate__(self):
        if getattr(self, 'action_bud_pending', None) is not None:
            raise RuntimeError('checkpoint requires completed action-bud evidence')
        return super().__getstate__()

    def _ensure_slots(self, count):
        if not hasattr(self, 'action_readers') or count <= self.slots:
            return super()._ensure_slots(count)
        old_graph, old_slots = self.graph, self.slots
        backup = copy.deepcopy(old_graph)
        definitions, probes = dict(self.expression_ids), dict(self.action_probe_nodes)
        try:
            super()._ensure_slots(count)
            for slot in range(self.slots):
                root = f'action-probe:{slot}'
                if root in self.graph.nodes:
                    continue
                self.graph.add_node(Node(root, NodeType.SCRIPT,
                    meta={'confirm_policy': 'weighted_evidence'}))
                nodes = []
                for expression in self.action_readers:
                    child = self._expression_node(expression, slot, root)
                    nodes.append(child)
                    self.graph.add_hierarchy_pair(root, child)
                self.action_probe_nodes[slot] = tuple(nodes)
            self.validate_ownership()
        except Exception:
            old_graph.__dict__ = backup.__dict__
            self.graph, self.slots = old_graph, old_slots
            self.expression_ids, self.action_probe_nodes = definitions, probes
            from recon_lite.graph import LinkType
            for slot in range(old_slots):
                self.graph.edge_by_key[(f'bias:{slot}', f'option:{slot}', LinkType.SUR)].w = self.bias
                for cid, condition in self.conditions.items():
                    self.graph.edge_by_key[(f'gate:{slot}:{cid}', f'option:{slot}', LinkType.SUR)].w = condition.weight
            raise

    def _before_execute(self, engine, env, *, event_id, slot, prediction, learn):
        super()._before_execute(engine, env, event_id=event_id, slot=slot,
                                prediction=prediction, learn=learn)
        if not learn:
            return
        observations = []
        for binding_slot in range(len(env['bindings'])):
            root = f'action-probe:{binding_slot}'
            engine.request(root)
            engine.run(max_ticks=40, env=env,
                until=lambda e: self.graph.nodes[root].state
                in (NodeState.CONFIRMED, NodeState.FAILED))
            states = tuple(self.graph.nodes[n].state for n in self.action_probe_nodes[binding_slot])
            if any(s not in (NodeState.CONFIRMED, NodeState.FAILED) for s in states):
                raise RuntimeError('action reader observations did not settle')
            observations.append(tuple(s == NodeState.CONFIRMED for s in states))
        selected = observations[slot]
        variable = tuple(len({values[i] for values in observations}) > 1
                         for i in range(len(self.action_readers)))
        self.action_bud_pending = (event_id, env['bindings'][slot], self.owner_pending[2],
                                   self.candidate_pending[4], selected, variable)

    def _record_nomination_outcome(self, owner, action, residual, observations):
        pending = self.action_bud_pending
        if (pending is None or pending[1:3] != (action, owner)
                or pending[3] != observations):
            raise RuntimeError('action-bud evidence crossed actual action or owner')
        for route_index, side in enumerate(observations):
            for reader_index, active in enumerate(pending[4]):
                self.action_bud_evidence[owner].setdefault(
                    (route_index, reader_index), RouteActionEvidence()).add(
                    side, active, pending[5][reader_index], residual)
        self.action_bud_pending = None

    def split_decision(self, owner, route):
        # Manual splitting remains mechanically valid, although this pilot never
        # schedules it. New owners must not inherit another route's evidence.
        children = super().split_decision(owner, route)
        for child in children:
            self.action_bud_evidence[child] = {}
        return children

    def _run_development(self, owner):
        retired = self._retire_local(owner)
        event = {'episode': self.completed, 'owner': owner,
                 'local_visit': self.owner_visits[owner], 'retired': retired,
                 'split': None, 'birth': None, 'bud': None,
                 'budget_rejections': []}
        choices = []
        for (route_index, reader_index), evidence in self.action_bud_evidence[owner].items():
            expression = combine('and', (self.owner_candidates[route_index],
                                         self.action_readers[reader_index]))
            if expression in self.owner_seen[owner]:
                continue
            if self._compatibility(owner, expression)[0].status == 'impossible':
                continue
            score = evidence.score(self.development_config.min_support)
            if score is not None and score > 0:
                choices.append((score, route_index, reader_index, expression))
        for score, route_index, reader_index, expression in sorted(
                choices, key=lambda x: (-x[0], x[1], x[2])):
            if len(self.conditions) >= self.ownership_limits.max_parameters:
                event['budget_rejections'].append('parameter budget')
                break
            trial = copy.deepcopy(self)
            cid = trial.next_condition
            trial.next_condition += 1
            trial.conditions[cid] = Condition(cid, (), 'and', trial.completed,
                                               weight=PlasticWeight())
            trial.base_expressions[cid] = expression
            trial.birth_visits[cid] = trial.owner_visits[owner]
            trial.owner_seen[owner].add(expression)
            trial.leaves[owner] = replace(trial.leaves[owner], contributions=(
                *trial.leaves[owner].contributions, cid))
            try:
                trial._rebuild(self.slots)
            except (ValueError, RuntimeError) as error:
                if 'budget' not in str(error):
                    raise
                event['budget_rejections'].append(str(error))
                continue
            event['birth'] = cid
            event['bud'] = {'condition': cid, 'route_index': route_index,
                            'reader_index': reader_index, 'expression': expression,
                            'score': score, 'evidence': copy.deepcopy(
                                self.action_bud_evidence[owner][(route_index, reader_index)])}
            trial.action_bud_history.append(event['bud'] | {
                'episode': self.completed, 'owner': owner})
            trial.development_history.append(event)
            self.__dict__ = trial.__dict__
            return
        event['birth'] = self._birth_local(owner)
        self.development_history.append(event)
