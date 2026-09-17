"""Owner-local refinement of an action-sensitive contribution.

An active contributor f may become f AND g and f AND NOT g, where g is a
formally observed state reader. Both children inherit f's weight, so the
mutation is prediction-preserving; later actual-action reward separates them.
No alternative-action reward, task label, or whole-owner copy enters growth.
"""
import copy
from dataclasses import dataclass, field, replace
import math

from recon_lite.graph import NodeState

from .recursive_context import SplitEvidence, combine, negate
from .route_action_bud import RouteActionBudDevelopment
from .terminal_development import Condition, PlasticWeight


class RefiningRouteActionDevelopment(RouteActionBudDevelopment):
    @classmethod
    def from_actor(cls, source, *, minimum_refinement_score=0.0,
                   reclosure_enabled=False, **kwargs):
        if (not math.isfinite(minimum_refinement_score)
                or minimum_refinement_score < 0):
            raise ValueError('refinement score floor must be finite and nonnegative')
        if type(reclosure_enabled) is not bool:
            raise ValueError('reclosure_enabled must be Boolean')
        actor = super().from_actor(source, **kwargs)
        actor.minimum_refinement_score = float(minimum_refinement_score)
        actor.reclosure_enabled = reclosure_enabled
        actor.refinable = set()
        actor.refinement_evidence = {}
        actor.refinement_history = []
        actor.reclosure_history = []
        return actor

    def _before_execute(self, engine, env, *, event_id, slot, prediction, learn):
        super()._before_execute(engine, env, event_id=event_id, slot=slot,
                                prediction=prediction, learn=learn)
        if learn:
            active = tuple(sorted(cid for cid in self.refinable
                if self.graph.nodes[f'gate:{slot}:{cid}'].state == NodeState.CONFIRMED))
            self.action_bud_pending += (active,)

    def _record_nomination_outcome(self, owner, action, residual, observations):
        pending = self.action_bud_pending
        if pending is None or len(pending) != 7:
            raise RuntimeError('refinement needs the actual formal activation frame')
        active = pending[6]
        super()._record_nomination_outcome(owner, action, residual, observations)
        for cid in active:
            evidence = self.refinement_evidence[cid]
            for index, side in enumerate(observations):
                evidence.setdefault(index, SplitEvidence()).add(side, residual)

    def _retire_local(self, owner):
        retired = super()._retire_local(owner)
        for cid in retired:
            self.refinable.discard(cid)
            self.refinement_evidence.pop(cid, None)
        return retired

    def _children(self, cid, predicate):
        source = self.base_expressions[cid]
        return (combine('and', (source, negate(predicate))),
                combine('and', (source, predicate)))

    def _eligible_refinement(self, owner, cid, predicate):
        if cid not in self.refinable or cid not in self.leaves[owner].contributions:
            return None
        children = self._children(cid, predicate)
        if (max(x.depth for x in children) > self.ownership_limits.max_depth
                or any(x in self.owner_seen[owner] for x in children)):
            return None
        if any(self._compatibility(owner, x)[0].status == 'impossible' for x in children):
            return None
        return children

    def _refine_local(self, owner, cid, predicate, *, evidence_score=None):
        if self.pending or self.owner_pending is not None:
            raise RuntimeError('refinement requires completed actual feedback')
        children = self._eligible_refinement(owner, cid, predicate)
        if children is None:
            raise ValueError('refinement is duplicate, impossible or out of depth')
        if len(self.conditions) + 1 > self.ownership_limits.max_parameters:
            raise ValueError('ownership parameter budget exhausted')
        trial = copy.deepcopy(self)
        parent = trial.conditions.pop(cid)
        contributions = list(trial.leaves[owner].contributions)
        position = contributions.index(cid)
        born = []
        for expression in children:
            child = trial.next_condition
            trial.next_condition += 1
            trial.conditions[child] = Condition(child, (), 'and', trial.completed,
                                                weight=copy.copy(parent.weight))
            trial.base_expressions[child] = expression
            trial.birth_visits[child] = trial.owner_visits[owner]
            trial.owner_seen[owner].add(expression)
            trial.refinable.add(child)
            trial.refinement_evidence[child] = {}
            born.append(child)
        contributions[position:position+1] = born
        trial.leaves[owner] = replace(trial.leaves[owner], contributions=tuple(contributions))
        trial.refinable.remove(cid)
        trial.refinement_evidence.pop(cid)
        event = {'episode': trial.completed, 'owner': owner, 'parent': cid,
                 'children': tuple(born), 'predicate': predicate,
                 'expressions': children, 'inherited_weight': float(parent.weight),
                 'score': evidence_score}
        trial.refinement_history.append(event)
        trial._rebuild(self.slots)
        self.__dict__ = trial.__dict__
        return event

    def _eligible_reclosure(self, owner, split):
        """Use only post-birth, selected-action evidence to veto a stale split.

        A small learned weight gap alone is not evidence of irrelevance: credit
        might simply have failed to separate useful children. The residual
        comparison is conservative, not proof that future contexts need no split.
        Retained owner_seen tombstones intentionally prohibit this exact split
        from being born again after reclosure.
        """
        if split['owner'] != owner or owner not in self.leaves:
            return None
        low, high = split['children']
        leaf = self.leaves[owner]
        positions = {cid: i for i, cid in enumerate(leaf.contributions)}
        if (low not in positions or high not in positions
                or positions[high] != positions[low] + 1
                or low not in self.refinable or high not in self.refinable):
            return None
        if (self.base_expressions.get(low) != split['expressions'][0]
                or self.base_expressions.get(high) != split['expressions'][1]
                or self.base_expressions.get(split['parent']) is None
                or self._children(split['parent'], split['predicate'])
                != split['expressions']):
            return None
        visit = self.owner_visits[owner]
        minimum = self.development_config.min_support
        counts = tuple(self.conditions[cid].stats.relevance_stats.confirm_count
                       for cid in (low, high))
        if (any(visit - self.birth_visits[cid] < self.config.grace_episodes
                for cid in (low, high)) or min(counts) < minimum):
            return None
        gap = abs(float(self.conditions[low].weight)
                  - float(self.conditions[high].weight))
        if not math.isfinite(gap) or gap > self.config.prune_weight:
            return None
        try:
            index = self.owner_candidates.index(split['predicate'])
        except ValueError:
            return None
        low_evidence = self.refinement_evidence.get(low, {}).get(index)
        high_evidence = self.refinement_evidence.get(high, {}).get(index)
        if (low_evidence is None or high_evidence is None
                or (low_evidence.n0, low_evidence.n1) != (counts[0], 0)
                or (high_evidence.n0, high_evidence.n1) != (0, counts[1])):
            return None
        residual_gap = abs(low_evidence.sum0 / counts[0]
                           - high_evidence.sum1 / counts[1])
        if not math.isfinite(residual_gap) or residual_gap > self.config.prune_weight:
            return None
        return gap, residual_gap, counts

    def _reclose_local(self, owner, split):
        if (self.pending or self.owner_pending is not None
                or self.candidate_pending is not None
                or self.action_bud_pending is not None
                or self.birth_search_pending is not None):
            raise RuntimeError('reclosure requires completed actual feedback')
        evidence = self._eligible_reclosure(owner, split)
        if evidence is None:
            raise ValueError('reclosure needs live, supported, locally redundant siblings')
        gap, residual_gap, counts = evidence
        trial = copy.deepcopy(self)
        low, high = split['children']
        leaf = trial.leaves[owner]
        contributions = list(leaf.contributions)
        position = contributions.index(low)
        retired = tuple(trial.conditions.pop(cid) for cid in (low, high))
        retired_evidence = tuple(trial.refinement_evidence.pop(cid)
                                 for cid in (low, high))
        for cid in (low, high):
            trial.refinable.remove(cid)
        identity = trial.next_condition
        trial.next_condition += 1
        parent_expression = trial.base_expressions[split['parent']]
        weight = PlasticWeight(
            fast=(retired[0].weight.fast + retired[1].weight.fast) / 2,
            slow=(retired[0].weight.slow + retired[1].weight.slow) / 2)
        trial.conditions[identity] = Condition(identity, (), 'and', trial.completed,
                                               weight=weight)
        trial.base_expressions[identity] = parent_expression
        trial.birth_visits[identity] = trial.owner_visits[owner]
        trial.owner_seen[owner].add(parent_expression)
        trial.refinable.add(identity)
        trial.refinement_evidence[identity] = {}
        contributions[position:position + 2] = [identity]
        trial.leaves[owner] = replace(leaf, contributions=tuple(contributions))
        event = {'episode': trial.completed, 'owner': owner,
                 'parent': split['parent'], 'children': (low, high),
                 'condition': identity, 'predicate': split['predicate'],
                 'expression': parent_expression, 'gap': gap,
                 'maximum_option_score_change': gap / 2,
                 'residual_gap': residual_gap, 'post_birth_confirms': counts}
        trial.reclosure_history.append({**event, 'retired_conditions': retired,
                                        'retired_evidence': retired_evidence})
        trial._rebuild(self.slots)
        self.__dict__ = trial.__dict__
        return event

    def _reclose_after_development(self, owner):
        """Reclaim at most one redundant pair without spending a growth turn."""
        if not getattr(self, 'reclosure_enabled', False):
            return
        latest = self.development_history[-1]
        latest['reclosure'] = None
        choices = []
        for split in self.refinement_history:
            evidence = self._eligible_reclosure(owner, split)
            if evidence is not None:
                choices.append((evidence[0], split['parent'], split))
        if choices:
            _, _, split = min(choices, key=lambda x: (x[0], x[1]))
            event = self._reclose_local(owner, split)
            # _reclose_local commits a deep copy, so latest above is stale.
            self.development_history[-1]['reclosure'] = event

    def _run_development(self, owner):
        retired = self._retire_local(owner)
        choices = []
        for cid in sorted(self.refinable & set(self.leaves[owner].contributions)):
            for index, evidence in self.refinement_evidence[cid].items():
                score = evidence.score(self.development_config.min_support)
                if (score is not None and score > 0
                        and score >= self.minimum_refinement_score):
                    predicate = self.owner_candidates[index]
                    if self._eligible_refinement(owner, cid, predicate) is not None:
                        choices.append((score, cid, index, predicate))
        rejections = []
        for score, cid, index, predicate in sorted(
                choices, key=lambda x: (-x[0], x[1], x[2])):
            try:
                event = self._refine_local(owner, cid, predicate, evidence_score=score)
            except (ValueError, RuntimeError) as error:
                if 'budget' not in str(error):
                    raise
                rejections.append(str(error))
                continue
            self.development_history.append({
                'episode': self.completed, 'owner': owner,
                'local_visit': self.owner_visits[owner], 'retired': retired,
                'split': None, 'birth': None, 'bud': None,
                'refinement': event, 'budget_rejections': rejections})
            self._reclose_after_development(owner)
            return
        # The unchanged bud/ordinary-birth opportunity is the fallback.
        super()._run_development(owner)
        latest = self.development_history[-1]
        latest['retired'] = retired
        latest['refinement'] = None
        latest['budget_rejections'].extend(rejections)
        if latest['bud'] is not None:
            cid = latest['bud']['condition']
            self.refinable.add(cid)
            self.refinement_evidence[cid] = {}
        self._reclose_after_development(owner)


@dataclass
class ProspectiveRefinementNomination:
    """A frozen local proposal, assessed only on later real-action receipts."""

    index: int
    discovery: SplitEvidence
    discovery_score: float
    nominated_visit: int
    validation: SplitEvidence = field(default_factory=SplitEvidence)

    def validation_gain(self, minimum):
        if min(self.validation.n0, self.validation.n1) < minimum:
            return None
        first = self.discovery
        pooled = (first.sum0 + first.sum1) / (first.n0 + first.n1)
        means = (first.sum0 / first.n0, first.sum1 / first.n1)
        # Difference between prospective squared residual errors from one
        # pooled prediction and two discovery-fitted side predictions. The
        # sum of residual squares cancels; counts and sums are sufficient.
        return sum(2 * (mean - pooled) * total - count * (mean * mean - pooled * pooled)
                   for mean, count, total in zip(means,
                       (self.validation.n0, self.validation.n1),
                       (self.validation.sum0, self.validation.sum1)))


class ProspectiveRefiningRouteActionDevelopment(RefiningRouteActionDevelopment):
    """Require disjoint future evidence before a local action-bud refinement.

    The ordinary graph, reward update, zero-output-change mutation and bud
    fallback are unchanged. Every active contribution may nominate one state
    predicate from at most four local development intervals. Its predicate and
    fitted residual means then freeze; later selected-action receipts alone
    determine whether the split pays a fixed one-parameter resource cost.
    """

    @classmethod
    def from_actor(cls, source, *, prospective_resource_cost=1.0, **kwargs):
        if kwargs.get('reclosure_enabled', False):
            raise ValueError('prospective refinement does not support reclosure')
        if (not math.isfinite(prospective_resource_cost)
                or prospective_resource_cost <= 0):
            raise ValueError('prospective resource cost must be finite and positive')
        actor = super().from_actor(source, **kwargs)
        actor.prospective_resource_cost = float(prospective_resource_cost)
        actor.prospective_discovery = {}
        actor.prospective_started = {}
        actor.prospective_nominations = {}
        actor.prospective_history = []
        return actor

    def _record_nomination_outcome(self, owner, action, residual, observations):
        pending = self.action_bud_pending
        if pending is None or len(pending) != 7:
            raise RuntimeError('prospective evidence requires a formal activation frame')
        active = pending[6]
        super()._record_nomination_outcome(owner, action, residual, observations)
        for cid in active:
            nomination = self.prospective_nominations.get(cid)
            if nomination is not None:
                nomination.validation.add(observations[nomination.index], residual)
            else:
                self.prospective_started.setdefault(cid, self.owner_visits[owner])
                evidence = self.prospective_discovery.setdefault(cid, {})
                for index, side in enumerate(observations):
                    evidence.setdefault(index, SplitEvidence()).add(side, residual)

    def _retire_local(self, owner):
        retired = super()._retire_local(owner)
        for cid in retired:
            self.prospective_discovery.pop(cid, None)
            self.prospective_started.pop(cid, None)
            self.prospective_nominations.pop(cid, None)
        return retired

    def _refine_local(self, owner, cid, predicate, *, evidence_score=None):
        event = super()._refine_local(owner, cid, predicate,
                                      evidence_score=evidence_score)
        visit = self.owner_visits[owner]
        deferred = []
        for other, nomination in sorted(self.prospective_nominations.items()):
            if other == cid or other not in self.leaves[owner].contributions:
                continue
            # The mutation leaves every option score unchanged at this instant,
            # so a different contribution's frozen discovery remains valid.
            # Later plasticity can alter residuals: require fresh two-sided
            # validation before this proposal may spend a mutation slot.
            deferred.append({'condition': other, 'candidate': nomination.index,
                             'prior_validation': copy.deepcopy(nomination.validation),
                             'prior_gain': nomination.validation_gain(
                                 self.development_config.min_support),
                             'prior_nominated_visit': nomination.nominated_visit,
                             'reset_visit': visit})
            nomination.validation = SplitEvidence()
            nomination.nominated_visit = visit
        for child in event['children']:
            self.prospective_discovery[child] = {}
            self.prospective_started[child] = visit
        self.prospective_discovery.pop(cid, None)
        self.prospective_started.pop(cid, None)
        self.prospective_nominations.pop(cid, None)
        event['deferred_revalidation'] = deferred
        return event

    def _run_development(self, owner):
        retired = self._retire_local(owner)
        visit = self.owner_visits[owner]
        interval = self.development_config.develop_every
        maximum_age = 4 * interval
        candidates = []
        reviews = []
        live = self.refinable & set(self.leaves[owner].contributions)

        # Review only nominations frozen before the current evidence window.
        for cid in sorted(live & set(self.prospective_nominations)):
            nomination = self.prospective_nominations[cid]
            predicate = self.owner_candidates[nomination.index]
            gain = nomination.validation_gain(self.development_config.min_support)
            age = visit - nomination.nominated_visit
            if self._eligible_refinement(owner, cid, predicate) is None:
                decision = 'ineligible'
            elif gain is not None:
                decision = ('approved' if gain > self.prospective_resource_cost
                            else 'rejected')
            elif age >= maximum_age:
                decision = 'unsupported'
            else:
                continue
            review = {'episode': self.completed, 'owner': owner, 'condition': cid,
                      'candidate': nomination.index, 'decision': decision,
                      'discovery': copy.deepcopy(nomination.discovery),
                      'validation': copy.deepcopy(nomination.validation),
                      'discovery_score': nomination.discovery_score,
                      'prospective_gain': gain, 'age': age}
            reviews.append(review)
            self.prospective_history.append(review)
            if decision == 'approved':
                candidates.append((gain, cid, nomination.index, predicate))
            else:
                self.prospective_nominations.pop(cid)
                self.prospective_discovery[cid] = {}
                self.prospective_started[cid] = visit

        rejections = []
        for gain, cid, index, predicate in sorted(candidates,
                                                  key=lambda x: (-x[0], x[1], x[2])):
            try:
                event = self._refine_local(owner, cid, predicate, evidence_score=gain)
            except (ValueError, RuntimeError) as error:
                if 'budget' not in str(error):
                    raise
                rejections.append(str(error))
                self.prospective_nominations.pop(cid)
                self.prospective_discovery[cid] = {}
                self.prospective_started[cid] = visit
                continue
            self.development_history.append({
                'episode': self.completed, 'owner': owner,
                'local_visit': visit, 'retired': retired,
                'split': None, 'birth': None, 'bud': None,
                'refinement': event, 'prospective_reviews': reviews,
                'prospective_nominations': [], 'budget_rejections': rejections})
            return

        nominated = []
        for cid in sorted(live - set(self.prospective_nominations)):
            choices = []
            for index, evidence in self.prospective_discovery.get(cid, {}).items():
                score = evidence.score(self.development_config.min_support)
                if (score is not None and score > 0
                        and score >= self.minimum_refinement_score):
                    predicate = self.owner_candidates[index]
                    if self._eligible_refinement(owner, cid, predicate) is not None:
                        choices.append((score, index, predicate))
            if choices:
                score, index, predicate = min(choices, key=lambda x: (-x[0], x[1]))
                discovery = copy.deepcopy(self.prospective_discovery[cid][index])
                self.prospective_nominations[cid] = ProspectiveRefinementNomination(
                    index, discovery, score, visit)
                nominated.append({'condition': cid, 'candidate': index,
                                  'predicate': predicate, 'score': score,
                                  'discovery': discovery, 'visit': visit})
                self.prospective_discovery[cid] = {}
                self.prospective_started.pop(cid, None)
            elif visit - self.prospective_started.get(cid, visit) >= maximum_age:
                self.prospective_discovery[cid] = {}
                self.prospective_started[cid] = visit

        # Keep the prior bud/ordinary-birth opportunity while proposals wait.
        RouteActionBudDevelopment._run_development(self, owner)
        latest = self.development_history[-1]
        latest['retired'] = retired
        latest['refinement'] = None
        latest['prospective_reviews'] = reviews
        latest['prospective_nominations'] = nominated
        latest['budget_rejections'].extend(rejections)
        if latest['bud'] is not None:
            cid = latest['bud']['condition']
            self.refinable.add(cid)
            self.refinement_evidence[cid] = {}
            self.prospective_discovery[cid] = {}
            self.prospective_started[cid] = visit
