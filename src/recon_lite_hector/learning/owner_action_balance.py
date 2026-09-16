"""Owner-local action coverage at the existing stochastic exploration events.

The graph still chooses and executes the binding. This law only directs the
already bounded internal exploration signal toward a less-sampled action of
the formally active owner. It uses no reward sign, correct action, row identity
or unchosen outcome. This two-action pilot is not a chess exploration policy.
"""
from recon_lite.graph import NodeState

from .owner_action_contrast import ActionContrastLearningTrialOwnerDevelopment


class OwnerBalancedActionContrastDevelopment(ActionContrastLearningTrialOwnerDevelopment):
    @classmethod
    def from_actor(cls, source, **kwargs):
        actor = super().from_actor(source, **kwargs)
        actor.action_visits = {0: {}}
        actor.exploration_owner = None
        return actor

    def _exploration_slot(self, engine, env, bindings):
        gates = tuple(f"gate:0:{leaf.bias_id}" for leaf in self.leaves.values())
        for gate in gates:
            engine.request(gate)
        engine.run(max_ticks=40, env=env,
                   until=lambda e: all(self.graph.nodes[gate].state in
                                       (NodeState.CONFIRMED, NodeState.FAILED) for gate in gates))
        matching = [leaf.identity for leaf in self.leaves.values()
                    if self.graph.nodes[f"gate:0:{leaf.bias_id}"].state == NodeState.CONFIRMED]
        if len(matching) != 1:
            raise RuntimeError("exploration requires exactly one formal owner")
        owner = matching[0]
        self.exploration_owner = owner
        counts = self.action_visits[owner]
        least = min(counts.get(binding, 0) for binding in bindings)
        options = [slot for slot, binding in enumerate(bindings)
                   if counts.get(binding, 0) == least]
        return options[self.rng.randrange(len(options))]

    def _before_execute(self, engine, env, *, event_id, slot, prediction, learn):
        super()._before_execute(engine, env, event_id=event_id, slot=slot,
                                prediction=prediction, learn=learn)
        if self.exploration_owner is not None:
            if self.exploration_owner != self.owner_pending[2]:
                raise RuntimeError("pre-choice exploration crossed formal ownership")
            self.exploration_owner = None

    def observe(self, feedback):
        if self.candidate_pending is None:
            raise RuntimeError("action coverage requires a pending actual choice")
        owner, action = self.candidate_pending[2], feedback.action
        super().observe(feedback)
        counts = self.action_visits[owner]
        counts[action] = counts.get(action, 0) + 1

    def nominate_split(self, owner, route, nomination=None):
        children = super().nominate_split(owner, route, nomination)
        for child in children:
            self.action_visits[child] = {}
        return children
