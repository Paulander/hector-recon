"""One outcome-nominated live TRIAL, using the ordinary terminal actor's credit.

The experiment's role and episode budget are fixed at construction. The organism
selects a definition from its own retained history; the coach supplies no index,
feature values, action preferences, or graph intervention.
"""
from dataclasses import dataclass

from .residual_shadow import Definition, Evidence, ShadowDevelopment
from .terminal_development import Condition, PlasticWeight, TerminalDevelopment


@dataclass(frozen=True)
class TrialConfig:
    role: str = "ranked"
    after_episode: int = 128

    def __post_init__(self):
        if self.role not in ("none", "ranked", "random"):
            raise ValueError("trial role must be none, ranked or random")
        if self.after_episode < 1:
            raise ValueError("positive trial episode required")


@dataclass
class TrialCondition(Condition):
    source_index: int = -1
    # Same object as the original shadow record, including adverse evidence.
    # It is historical prediction evidence, not live participation or maturity.
    source_evidence: Evidence | None = None


class TrialDevelopment(ShadowDevelopment):
    """One-action developmental experiment with one additional lifetime slot.

Before attachment all roles behave exactly like ShadowDevelopment. Afterwards
all shadow requests/updates stop, and only ordinary actor learning continues.
The original random-birth cap is unchanged; this experiment can add at most one
condition beyond it. There is no replacement if the nominee collides or retires.
"""

    def __init__(self, *, trial_config=None, **kwargs):
        super().__init__(**kwargs)
        self.trial_config = trial_config or TrialConfig()
        if self.trial_config.after_episode <= self.shadow_config.discovery_episodes:
            raise ValueError("attachment requires a prospective interval after discovery")
        self.trial_condition = None
        self.trial_decision = None
        self.live_counts = {"episodes": 0, "active": 0, "positive_active": 0,
                            "negative_active": 0, "reward_sum_active": 0.0}

    def _begin_trial(self):
        if self.pending or self.shadow_pending is not None:
            raise RuntimeError("attachment requires completed actual feedback")
        if self.completed != self.trial_config.after_episode or self.trial_decision is not None:
            raise RuntimeError("one attachment decision at the declared episode only")
        role = self.trial_config.role
        decision = {"role": role, "after_episode": self.completed}
        if role == "none":
            decision["status"] = "no_addition"
        elif self.shadow.nomination is None:
            decision["status"] = "no_nomination"
        else:
            index = self.shadow.nomination[role]
            definition = self.shadow.definitions[index]
            decision["source_index"] = index
            key = (definition.operator, definition.atoms)
            live = {Definition(c.operator, c.atoms) for c in self.conditions.values()}
            if definition in live:
                decision["status"] = "already_live"
            elif key in self.retired_conditions:
                decision["status"] = "already_retired"
            else:
                evidence = self.shadow.evidence[index]
                condition = TrialCondition(
                    self.next_condition, definition.atoms, definition.operator, self.completed,
                    weight=PlasticWeight(fast=evidence.weight), source_index=index,
                    source_evidence=evidence)
                self.next_condition += 1
                self.conditions[condition.identity] = condition
                for slot in range(self.slots):
                    self._add_condition_slot(condition, slot)
                self.trial_condition = condition
                decision["status"] = "attached"
        self.trial_decision = decision

    def _before_execute(self, engine, env, *, event_id, slot, prediction, learn):
        if self.completed < self.trial_config.after_episode:
            super()._before_execute(engine, env, event_id=event_id, slot=slot,
                                    prediction=prediction, learn=learn)

    def observe(self, feedback):
        if self.completed < self.trial_config.after_episode:
            super().observe(feedback)
            if self.completed == self.trial_config.after_episode:
                self._begin_trial()
            return
        # Inspect only the internal eligibility record for the submitted action.
        # Base validation runs before any mutation of these additional records.
        active = bool(self.pending and self.trial_condition is not None
                      and self.trial_condition.identity in self.pending[-1][3])
        TerminalDevelopment.observe(self, feedback)
        self.live_counts["episodes"] += 1
        if active:
            reward = float(feedback.reward)
            self.live_counts["active"] += 1
            self.live_counts["positive_active"] += int(reward > 0)
            self.live_counts["negative_active"] += int(reward < 0)
            self.live_counts["reward_sum_active"] += reward
