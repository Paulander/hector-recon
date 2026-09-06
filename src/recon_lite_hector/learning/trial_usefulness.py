"""Bounded randomized access to one TRIAL, grounded in actual scalar outcomes.

This gathers usefulness evidence. It does not choose a new nominee, change the
randomization rate from scores, promote, retire, or freeze the ordinary actor.
"""
from dataclasses import asdict, dataclass
import math
import random

from recon_lite.graph import LinkType, Node, NodeType
from .live_trial import TrialCondition, TrialDevelopment
from .terminal_development import _reader


@dataclass(frozen=True)
class UsefulnessConfig:
    window_episodes: int = 128
    enable_probability: float = 0.5

    def __post_init__(self):
        if self.window_episodes < 1 or not 0 < self.enable_probability < 1:
            raise ValueError("positive window and probability strictly between zero and one required")


@dataclass(frozen=True)
class UseOutcome:
    event_id: int
    action: str
    enabled: bool
    participated: bool
    reward: float


def _permission(node, env):
    """Leaf internal terminal: reads the local, pre-action assignment only."""
    enabled = node.meta["enabled"]
    node.activation.value = float(enabled)
    return True, enabled


class UsefulnessDevelopment(TrialDevelopment):
    def __init__(self, *, seed=1, usefulness_config=None, **kwargs):
        super().__init__(seed=seed, **kwargs)
        self.usefulness_config = usefulness_config or UsefulnessConfig()
        self.use_rng = random.Random(f"trial-use:{seed}")
        self.use_enabled = True  # Transient execution assignment, not competence.
        self.use_pending = None
        self.use_outcomes = []  # Bounded history; retained even if the trial retires.

    def __getstate__(self):
        if self.use_pending is not None:
            raise RuntimeError("checkpoint requires completed trial-use feedback")
        return super().__getstate__()

    def _add_condition_slot(self, condition, slot):
        if not isinstance(condition, TrialCondition):
            return super()._add_condition_slot(condition, slot)
        gate = f"gate:{slot}:{condition.identity}"
        pattern = f"use:pattern:{slot}:{condition.identity}"
        permit = f"use:permit:{slot}:{condition.identity}"
        for nid, policy in ((gate, "and"), (pattern, condition.operator)):
            self.graph.add_node(Node(nid, NodeType.SCRIPT, meta={
                "confirm_policy": policy, "condition_id": condition.identity}))
            self.graph.nodes[nid].activation.value = 1.0
        self.graph.add_hierarchy_pair(f"option:{slot}", gate)
        self.graph.edge_by_key[(gate, f"option:{slot}", LinkType.SUR)].w = condition.weight
        self.graph.add_hierarchy_pair(gate, pattern)
        self.graph.add_node(Node(permit, NodeType.TERMINAL, predicate=_permission,
                                 meta={"enabled": self.use_enabled}))
        self.graph.add_hierarchy_pair(gate, permit)
        for index, expected in condition.atoms:
            reader = f"read:{slot}:{index}:{int(expected)}"
            if reader not in self.graph.nodes:
                self.graph.add_node(Node(reader, NodeType.TERMINAL, predicate=_reader,
                                         meta={"slot": slot, "atom": (index, expected)}))
            self.graph.add_hierarchy_pair(pattern, reader)

    def _set_enabled(self, enabled):
        self.use_enabled = enabled
        for node in self.graph.nodes.values():
            if node.predicate is _permission:
                node.meta["enabled"] = enabled

    def act(self, port, *, event_id, learn):
        if self.pending or self.shadow_pending is not None or self.use_pending is not None:
            raise RuntimeError("trial-use requires feedback after each actual action")
        if learn and event_id <= self.last_event:
            raise ValueError("action event must increase; cannot duplicate credit")
        age = self.completed - self.trial_config.after_episode
        trial = self.trial_condition
        probe = (learn and 0 <= age < self.usefulness_config.window_episodes
                 and trial is not None and trial.identity in self.conditions)
        rng_state, old_enabled = self.use_rng.getstate(), self.use_enabled
        enabled = self.use_rng.random() < self.usefulness_config.enable_probability if probe else True
        self._set_enabled(enabled)
        try:
            action = super().act(port, event_id=event_id, learn=learn)
        except Exception:
            self.use_rng.setstate(rng_state)
            self._set_enabled(old_enabled)
            raise
        if probe:
            self.use_pending = (event_id, action, enabled)
        return action

    def observe(self, feedback):
        assignment = self.use_pending
        if assignment is not None:
            if (feedback.event_id, feedback.action) != assignment[:2]:
                raise ValueError("outcome does not bind to trial-use assignment")
            if not math.isfinite(float(feedback.reward)):
                raise ValueError("reward must be finite")
            participated = self.trial_condition.identity in self.pending[-1][3]
            if participated and not assignment[2]:
                raise RuntimeError("disabled trial acquired actual-action eligibility")
        # Ordinary validation/credit executes before recording any extra evidence.
        super().observe(feedback)
        if assignment is not None:
            self.use_outcomes.append(UseOutcome(*assignment[:2], assignment[2],
                                                participated, float(feedback.reward)))
            self.use_pending = None

    def usefulness_report(self):
        """Local scalar summary over ALL assigned outcomes, never activation-filtered.

        Randomization estimates access value along this adaptive learning history,
        not the value of having trained a different topology throughout its life.
        No iid confidence interval or automatic maturity claim is attached.
        """
        groups = {}
        for enabled in (False, True):
            rows = [r for r in self.use_outcomes if r.enabled == enabled]
            groups["enabled" if enabled else "disabled"] = {
                "count": len(rows), "reward_sum": sum(r.reward for r in rows),
                "mean_reward": sum(r.reward for r in rows) / len(rows) if rows else None,
                "positive": sum(r.reward > 0 for r in rows),
                "negative": sum(r.reward < 0 for r in rows),
                "participations": sum(r.participated for r in rows)}
        on, off = groups["enabled"]["mean_reward"], groups["disabled"]["mean_reward"]
        p, n = self.usefulness_config.enable_probability, len(self.use_outcomes)
        return {"config": asdict(self.usefulness_config), "assigned_episodes": n,
                "groups": groups,
                "mean_reward_difference": None if on is None or off is None else on - off,
                "randomized_reward_contrast": (sum(r.reward / p if r.enabled else -r.reward / (1 - p)
                                                   for r in self.use_outcomes) / n if n else None),
                "window_elapsed": self.completed >= self.trial_config.after_episode
                                    + self.usefulness_config.window_episodes}

    def _prune(self):
        trial = self.trial_condition
        was_live = trial is not None and trial.identity in self.conditions
        super()._prune()
        if not was_live or trial.identity in self.conditions:
            return
        # The base lifecycle removes the outer gates. Remove their private wrapper
        # descendants too, preserving shared readers and the historical records.
        remove = {f"use:{kind}:{slot}:{trial.identity}"
                  for kind in ("pattern", "permit") for slot in range(self.slots)}
        for nid, node in self.graph.nodes.items():
            if node.predicate is _reader and all(p in remove for p in self.graph.all_parents(nid)):
                remove.add(nid)
        nodes = [n for nid, n in self.graph.nodes.items() if nid not in remove]
        edges = [e for e in self.graph.edges if e.src not in remove and e.dst not in remove]
        self.graph.__init__()
        for node in nodes:
            self.graph.add_node(node)
        for edge in edges:
            self.graph.add_edge(edge.src, edge.dst, edge.ltype)
            replacement = self.graph.edge_by_key[(edge.src, edge.dst, edge.ltype)]
            replacement.w, replacement.meta = edge.w, edge.meta
        self.graph.validate_formal_pairs()
