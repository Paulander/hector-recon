"""Exposure-grounded learning before bounded prospective split assessment.

The original trial law remains an unchanged control. Only timing/assessment
lifecycle changes here; all graph execution, credit, growth and RNGs are reused.
"""
import copy
from dataclasses import dataclass, field

from .owner_trial import TrialOwnerDevelopment, StemCellState


@dataclass
class AssessmentClock:
    start: int | None = None  # Number of preceding real region requests.
    started_at: int | None = None
    learning_counts: dict = field(default_factory=dict)
    reviews: list = field(default_factory=list)


class LearningTrialOwnerDevelopment(TrialOwnerDevelopment):
    @classmethod
    def from_actor(cls, source, **kwargs):
        actor = super().from_actor(source, **kwargs)
        actor.assessment_clocks = {}
        return actor

    def nominate_split(self, owner, route, nomination=None):
        children = super().nominate_split(owner, route, nomination)
        trial = self.split_trials[owner]
        self.assessment_clocks[(owner, trial.born)] = AssessmentClock()
        return children

    def _resolve_trial(self, parent):
        # Suppress only the old fixed256-request decision. New decisions happen
        # after the same actual feedback has been recorded by super.observe.
        pass

    def observe(self, feedback):
        assignment = self.split_use_pending
        super().observe(feedback)
        if assignment is None:
            return
        parent, born = assignment[2], assignment[5]
        trial = self.split_trials[parent]
        clock = self.assessment_clocks[(parent, born)]
        count = len(trial.outcomes)
        interval = self.development_config.develop_every
        parent_count = sum(not r.enabled for r in trial.outcomes)
        if clock.start is None and min(parent_count, *trial.child_exposures.values()) >= interval:
            # Readiness depends only on already observed exposure, never reward
            # sign or an evaluation score. This outcome stays in learning history.
            clock.start = count
            clock.started_at = self.completed
            clock.learning_counts = {parent: parent_count, **trial.child_exposures}
            trial.state = StemCellState.PROBATION
        window = self.owner_trial_config.window
        age = count - clock.start if clock.start is not None else 0
        if age in (window, 2*window):
            summary = self.trial_summary(trial)
            clock.reviews.append(dict(summary, episode=self.completed))
            if summary['accepted']:
                self._finish_trial(parent, accepted=True, reason='accepted prospective access benefit')
                return
            if age == 2*window:
                self._finish_trial(parent, accepted=False, reason='unproven after two assessments')
                return
            # One later assessment was allocated at birth. Keep this exact
            # candidate, with all its weights, visits and failed review history.
        if count == 6*window:
            self._finish_trial(parent, accepted=False, reason='unproven at lifetime budget')

    def trial_summary(self, trial):
        clock = self.assessment_clocks[(trial.parent, trial.born)]
        rows = trial.outcomes[clock.start:] if clock.start is not None else []
        def contrast(items):
            groups = [[r.reward for r in items if r.enabled == enabled] for enabled in (False, True)]
            return sum(groups[1])/len(groups[1])-sum(groups[0])/len(groups[0]) if all(groups) else None
        counts = [sum(r.enabled == enabled for r in rows) for enabled in (False, True)]
        # Use real controlling-child identities. Each UseOutcome's event matches
        # a recorded assignment; per-child totals at assessment start are saved.
        children = {c: trial.child_exposures[c]-clock.learning_counts.get(c, 0)
                    for c in trial.children} if clock.start is not None else {c: 0 for c in trial.children}
        config = self.owner_trial_config
        supported = min(counts) >= config.min_arm and min(children.values()) >= config.min_child
        gain = contrast(rows)
        accepted = (len(rows) in (config.window, 2*config.window) and supported
                    and gain >= config.min_reward_gain)
        return {'assigned':len(trial.outcomes), 'assessment_assigned':len(rows),
            'assessment_start':clock.start, 'assessment_started_at':clock.started_at,
            'learning_counts':dict(clock.learning_counts), 'arm_counts':counts,
            'child_exposures':dict(trial.child_exposures), 'assessment_child_exposures':children,
            'mean_reward_gain':gain,
            'review_segment_gains':[contrast(rows[:config.window]),contrast(rows[config.window:])],
            'supported':supported, 'accepted':accepted, 'reviews_completed':len(clock.reviews)}

    def _finish_trial(self, parent, *, accepted, reason):
        actor = copy.deepcopy(self)
        trial = actor.split_trials.pop(parent)
        trial.resolution = dict(actor.trial_summary(trial), episode=actor.completed, reason=reason)
        assert trial.resolution['accepted'] == accepted
        trial.state = StemCellState.MATURE if accepted else StemCellState.PRUNED
        trial.stats.record_intervention('positive' if accepted else 'neutral')
        removed = (parent,) if accepted else trial.children
        retired = []
        for owner in removed:
            leaf = actor.leaves.pop(owner)
            retired.append((leaf, tuple(actor.conditions.pop(cid) for cid in leaf.contributions)))
        trial.retired = tuple(retired)
        if accepted:
            actor.ownership_history.append({'episode':actor.completed,'parent':retired[0][0],
                'route':trial.route,'children':trial.children,'conditions':retired[0][1],
                'trial_born':trial.born,'acceptance':trial.resolution})
        actor.split_trial_history.append(trial)
        actor.split_enabled.pop(parent, None)
        actor._rebuild(self.slots)
        self.__dict__ = actor.__dict__
