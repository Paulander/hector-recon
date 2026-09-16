"""Local provisional owner splits using actual randomized access outcomes.

Reuses the existing lifecycle enum/stats, permission terminal and UseOutcome.
No counterfactual action is executed or credited. MATURE here means accepted by
the declared finite experimental rule, not a permanent sensor or a guarantee.
"""
import copy
import math
import random
from dataclasses import dataclass, field

from recon_lite.graph import Node, NodeType
from recon_lite_hector.nodes.stem_cell import CandidateLocalStats, StemCellState
from .context_decision import DecisionLeaf
from .fresh_owner import FreshOwnerDevelopment
from .recursive_context import TRUE, combine, negate
from .terminal_development import Condition, PlasticWeight
from .trial_usefulness import UseOutcome, _permission


@dataclass(frozen=True)
class OwnerTrialConfig:
    window: int = 256
    min_arm: int = 48
    min_child: int = 16
    min_reward_gain: float = 0.1

    def __post_init__(self):
        if (any(type(v) is not int or v < 1 for v in
                (self.window, self.min_arm, self.min_child))
                or self.window % 2 or 2*self.min_arm > self.window
                or not math.isfinite(self.min_reward_gain) or self.min_reward_gain <= 0):
            raise ValueError("positive bounded trial settings required")


@dataclass
class OwnerSplitTrial:
    parent: int
    children: tuple[int, int]
    route: object
    born: int
    nomination: object
    inherited: tuple
    state: StemCellState = StemCellState.TRIAL
    stats: CandidateLocalStats = field(default_factory=CandidateLocalStats)
    outcomes: list = field(default_factory=list)
    child_exposures: dict = field(default_factory=dict)
    resolution: dict | None = None
    retired: tuple = ()


class TrialOwnerDevelopment(FreshOwnerDevelopment):
    @classmethod
    def from_actor(cls, source, *, trial_config=None, search_seed=0, **kwargs):
        actor = super().from_actor(source, search_seed=search_seed, **kwargs)
        actor.owner_trial_config = trial_config or OwnerTrialConfig()
        actor.split_trials = {}
        actor.split_trial_history = []
        actor.split_tried = {}
        actor.split_use_rng = random.Random(f"owner-split-use:{search_seed}")
        actor.split_enabled = {}
        actor.split_use_pending = None
        return actor

    def __getstate__(self):
        if getattr(self, "split_use_pending", None) is not None:
            raise RuntimeError("checkpoint requires completed split-use feedback")
        return super().__getstate__()

    def _leaf_budget_count(self):
        # Each trial reserves its possible +1 committed leaf. Its continuing
        # parent is extra storage, fully counted by parameter/node budgets.
        return len(self.leaves) - len(getattr(self, "split_trials", {}))

    def _trial_for(self, owner):
        return next((t for t in getattr(self, "split_trials", {}).values()
                     if owner == t.parent or owner in t.children), None)

    def _add_condition_slot(self, condition, slot):
        super()._add_condition_slot(condition, slot)
        owner = next(leaf.identity for leaf in self.leaves.values()
                     if condition.identity in leaf.contributions)
        trial = self._trial_for(owner)
        if trial is None:
            return
        enabled = self.split_enabled.get(trial.parent, False)
        permit = f"split-permit:{slot}:{condition.identity}"
        self.graph.add_node(Node(permit, NodeType.TERMINAL, predicate=_permission,
            meta={"enabled": enabled == (owner != trial.parent),
                  "split_parent": trial.parent, "split_child": owner != trial.parent}))
        self.graph.add_hierarchy_pair(f"gate:{slot}:{condition.identity}", permit)

    def _set_split_access(self, assignments):
        self.split_enabled = dict(assignments)
        for node in self.graph.nodes.values():
            if node.predicate is _permission and "split_parent" in node.meta:
                node.meta["enabled"] = (assignments.get(node.meta["split_parent"], False)
                                         == node.meta["split_child"])

    def act(self, port, *, event_id, learn):
        if self.pending or self.split_use_pending is not None:
            raise RuntimeError("split-use requires immediate matching feedback")
        if learn and event_id <= self.last_event:
            raise ValueError("action event must increase")
        state, assignments = self.split_use_rng.getstate(), dict(self.split_enabled)
        # Internal independent random assignments, before any environment read.
        # All regions are assigned; formal gates determine the active region.
        self._set_split_access({parent: learn and self.split_use_rng.random() < .5
                                for parent in sorted(self.split_trials)})
        try:
            return super().act(port, event_id=event_id, learn=learn)
        except Exception:
            self.split_use_rng.setstate(state)
            self._set_split_access(assignments)
            raise

    def _before_execute(self, engine, env, *, event_id, slot, prediction, learn):
        super()._before_execute(engine, env, event_id=event_id, slot=slot,
                                prediction=prediction, learn=learn)
        if learn:
            owner = self.owner_pending[2]
            trial = self._trial_for(owner)
            if trial is not None:
                enabled = self.split_enabled[trial.parent]
                if enabled != (owner in trial.children):
                    raise RuntimeError("split assignment crossed actual ownership")
                self.split_use_pending = (event_id, env["bindings"][slot],
                                           trial.parent, owner, enabled, trial.born)

    def observe(self, feedback):
        assignment = self.split_use_pending
        if assignment is not None:
            if ((feedback.event_id, feedback.action) != assignment[:2]
                    or not math.isfinite(float(feedback.reward))):
                raise ValueError("outcome must bind to the actual split-use assignment")
            if self.owner_pending is None or self.owner_pending[2] != assignment[3]:
                raise RuntimeError("split-use owner mismatch")
        # Existing feedback validation occurs before permitting transactional
        # development copies. No new trial evidence is recorded on invalid input.
        if (not self.pending or self.birth_search_pending is None
                or (feedback.event_id, feedback.action) != self.pending[-1][:2]
                or not math.isfinite(float(feedback.reward))):
            raise ValueError("outcome must bind to the pending actual action")
        self.split_use_pending = None
        super().observe(feedback)
        if assignment is None:
            return
        _, _, parent, owner, enabled, born = assignment
        trial = self.split_trials[parent]
        if trial.born != born:
            raise RuntimeError("split-use evidence crossed trial identity")
        trial.outcomes.append(UseOutcome(feedback.event_id, feedback.action,
                                        enabled, enabled, float(feedback.reward)))
        trial.stats.record_request(str(parent))
        if enabled:
            trial.child_exposures[owner] += 1
            trial.stats.record_activation(str(parent))
            trial.stats.record_confirm(self.completed, str(parent))
        trial.stats.record_correlation("positive" if feedback.reward > 0 else
                                       "negative" if feedback.reward < 0 else "neutral")
        if len(trial.outcomes) == self.owner_trial_config.window:
            self._resolve_trial(parent)

    def _split_key(self, route):
        # Boolean equality and its complement are one partition hypothesis.
        if route.operator == "read" and set(self.schema[route.atom[0]].values) == {False, True}:
            return ("boolean-coordinate", route.atom[0])
        return frozenset((route, negate(route)))

    def nominate_split(self, owner, route, nomination=None):
        if self.pending or self.owner_pending is not None or self.split_use_pending is not None:
            raise RuntimeError("nomination requires completed feedback")
        self._check_route(route)
        if owner not in self.leaves or self._trial_for(owner) is not None:
            raise ValueError("nomination requires an owner without a competing trial")
        key = self._split_key(route)
        if key in self.split_tried.get(owner, set()):
            raise ValueError("split hypothesis already tried; history is retained")
        trial_actor = copy.deepcopy(self)
        parent = trial_actor.leaves[owner]
        inherited = tuple(copy.deepcopy(trial_actor.conditions[cid]) for cid in parent.contributions)
        children = []
        for enabled in (False, True):
            branch = route if enabled else negate(route)
            path = branch if parent.path == TRUE else combine("and", (parent.path, branch))
            ids, bias_id = [], None
            for cid in parent.contributions:
                old = trial_actor.conditions[cid]
                identity = trial_actor.next_condition
                trial_actor.next_condition += 1
                trial_actor.conditions[identity] = Condition(identity, old.atoms, old.operator,
                    trial_actor.completed, weight=copy.copy(old.weight))
                trial_actor.base_expressions[identity] = trial_actor.base_expressions[cid]
                trial_actor.birth_visits[identity] = 0
                ids.append(identity)
                if cid == parent.bias_id:
                    bias_id = identity
            child = trial_actor.next_owner
            trial_actor.next_owner += 1
            trial_actor.leaves[child] = DecisionLeaf(child, path, tuple(ids), bias_id,
                                                   trial_actor.completed, owner)
            trial_actor.owner_visits[child] = 0
            trial_actor.owner_evidence[child] = {}
            trial_actor.owner_seen[child] = {trial_actor.base_expressions[cid] for cid in ids}
            from .recursive_context import SplitEvidence
            trial_actor.birth_evidence[child] = [SplitEvidence() for _ in trial_actor.birth_definitions]
            children.append(child)
        trial_actor.split_trials[owner] = OwnerSplitTrial(owner, tuple(children), route,
            self.completed, copy.deepcopy(nomination), inherited,
            child_exposures={child: 0 for child in children})
        trial_actor.split_tried.setdefault(owner, set()).add(key)
        trial_actor.split_enabled[owner] = False
        trial_actor._rebuild(self.slots)
        self.__dict__ = trial_actor.__dict__
        return tuple(children)

    def trial_summary(self, trial):
        config, rows = self.owner_trial_config, trial.outcomes
        def contrast(items):
            off = [r.reward for r in items if not r.enabled]
            on = [r.reward for r in items if r.enabled]
            return (sum(on)/len(on)-sum(off)/len(off)) if on and off else None
        counts = [sum(r.enabled == flag for r in rows) for flag in (False, True)]
        halves = [contrast(rows[:config.window//2]), contrast(rows[config.window//2:])]
        gain = contrast(rows)
        supported = (min(counts) >= config.min_arm
                     and min(trial.child_exposures.values()) >= config.min_child)
        accepted = (len(rows) == config.window and supported and gain >= config.min_reward_gain
                    and all(g is not None and g > 0 for g in halves))
        return {"assigned": len(rows), "arm_counts": counts, "mean_reward_gain": gain,
                "half_gains": halves, "child_exposures": dict(trial.child_exposures),
                "supported": supported, "accepted": accepted}

    def _resolve_trial(self, parent):
        actor = copy.deepcopy(self)
        trial = actor.split_trials.pop(parent)
        summary = actor.trial_summary(trial)
        if len(trial.outcomes) != actor.owner_trial_config.window:
            raise RuntimeError("resolve only at the declared fixed local window")
        accepted = summary["accepted"]
        trial.state = StemCellState.MATURE if accepted else StemCellState.PRUNED
        trial.resolution = dict(summary, episode=actor.completed,
            reason="accepted empirical access benefit" if accepted else "unproven at window end")
        # A single prospective comparison enters intervention statistics. Individual
        # favorable rewards are not mislabeled as causal split evidence.
        trial.stats.record_intervention("positive" if accepted else "neutral")
        removed = (parent,) if accepted else trial.children
        retired = []
        for owner in removed:
            leaf = actor.leaves.pop(owner)
            conditions = tuple(actor.conditions.pop(cid) for cid in leaf.contributions)
            retired.append((leaf, conditions))
        trial.retired = tuple(retired)
        if accepted:
            actor.ownership_history.append({"episode": actor.completed, "parent": retired[0][0],
                "route": trial.route, "children": trial.children, "conditions": retired[0][1],
                "trial_born": trial.born, "acceptance": trial.resolution})
        actor.split_trial_history.append(trial)
        actor.split_enabled.pop(parent, None)
        actor._rebuild(self.slots)
        self.__dict__ = actor.__dict__

    def split_decision(self, owner, route):
        raise RuntimeError("provisional law requires nominate_split and actual outcome acceptance")

    def _nomination_score(self, owner, index, evidence):
        return evidence.score(self.development_config.min_support)

    def _run_development(self, owner):
        retired = self._retire_local(owner)
        # Continue the ordinary local opportunity even when nomination succeeds.
        # Birth precedes cloning so both alternatives start with identical scores
        # and the same feature set. Pending alternatives learn/grow on own visits.
        birth = self._birth_local(owner)
        event = {"episode": self.completed, "owner": owner,
            "local_visit": self.owner_visits[owner], "retired": retired, "birth": birth,
            "split": None, "trial_nomination": None, "budget_rejections": []}
        if (self.development_config.split_enabled and self._trial_for(owner) is None
                and self._leaf_budget_count() < self.ownership_limits.max_leaves):
            choices = []
            for index, evidence in self.owner_evidence[owner].items():
                score = self._nomination_score(owner, index, evidence)
                key = self._split_key(self.owner_candidates[index])
                if score is not None and score > 0 and key not in self.split_tried.get(owner, set()):
                    choices.append((score, index))
            for score, index in sorted(choices, key=lambda p: (-p[0], p[1])):
                nomination = {"candidate": index, "score": score,
                              "evidence": copy.deepcopy(self.owner_evidence[owner][index])}
                try:
                    children = self.nominate_split(owner, self.owner_candidates[index], nomination)
                except (ValueError, RuntimeError) as error:
                    if "budget" not in str(error):
                        raise
                    event["budget_rejections"].append({"candidate": index, "reason": str(error)})
                    continue
                event["trial_nomination"] = dict(nomination, children=children)
                break
        self.development_history.append(event)
