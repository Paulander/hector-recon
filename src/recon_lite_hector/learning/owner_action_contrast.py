"""Action-conditional nomination for the two-action owner trial.

Only residuals from executed actions enter these statistics. This changes which
locally observed route is nominated, not split access, feedback, or acceptance.
The four-cell requirement is deliberately specific to this two-action fixture;
it is not a general chess-action selection law.
"""
from dataclasses import dataclass, field

from .owner_trial_learning import LearningTrialOwnerDevelopment


@dataclass
class ActionContrastEvidence:
    counts: dict = field(default_factory=dict)
    sums: dict = field(default_factory=dict)

    def add(self, side, action, residual):
        key = (bool(side), action)
        self.counts[key] = self.counts.get(key, 0) + 1
        self.sums[key] = self.sums.get(key, 0.0) + residual

    def score(self, minimum):
        actions = {action for _, action in self.counts}
        if len(actions) != 2:
            return None
        first, second = sorted(actions)
        keys = ((False, first), (True, first), (False, second), (True, second))
        if min(self.counts.get(key, 0) for key in keys) < minimum:
            return None
        means = {key: self.sums[key] / self.counts[key] for key in keys}
        contrast = ((means[True, second] - means[False, second])
                    - (means[True, first] - means[False, first]))
        return contrast * contrast / sum(1 / self.counts[key] for key in keys)


class ActionContrastLearningTrialOwnerDevelopment(LearningTrialOwnerDevelopment):
    @classmethod
    def from_actor(cls, source, **kwargs):
        actor = super().from_actor(source, **kwargs)
        actor.action_contrast_evidence = {0: {}}
        return actor

    def _record_nomination_outcome(self, owner, action, residual, observations):
        evidence = self.action_contrast_evidence[owner]
        for index, side in enumerate(observations):
            evidence.setdefault(index, ActionContrastEvidence()).add(side, action, residual)

    def _nomination_score(self, owner, index, evidence):
        return self.action_contrast_evidence[owner][index].score(
            self.development_config.min_support)

    def nominate_split(self, owner, route, nomination=None):
        children = super().nominate_split(owner, route, nomination)
        for child in children:
            self.action_contrast_evidence[child] = {}
        return children
