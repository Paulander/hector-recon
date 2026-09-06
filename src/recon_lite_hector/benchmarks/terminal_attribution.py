"""Named experimental controls, not the production developmental policy.

Only the declared schema and random seeds construct these plans. No positions,
terminal responses, rewards or validation outcomes are available to planning.
"""
from dataclasses import dataclass
import random

from recon_lite_hector.learning.terminal_development import (
    Condition, Coordinate, DevelopmentConfig, TerminalDevelopment,
)

ARMS = ("online_random", "fixed_random", "atomic_only")


@dataclass(frozen=True)
class Proposal:
    atoms: tuple[tuple[int, bool | int], ...]
    operator: str
    after_episode: int


def make_plans(schema: tuple[Coordinate, ...], *, seed: int, count: int,
               episodes: int) -> tuple[tuple[Proposal, ...], tuple[Proposal, ...]]:
    """Reuse production birth grammar with a separate, outcome-blind RNG.

    Atomic controls use unique literals, never duplicates that silently increase
    the effective update rate. Reject an impossible matched budget up front.
    """
    vocabulary = [(i, value) for i, coord in enumerate(schema) for value in coord.values]
    if not 1 <= count <= len(vocabulary) or episodes < 1:
        raise ValueError("budget must fit the unique atomic vocabulary and positive episodes")
    generator = TerminalDevelopment(
        seed=f"proposals:{seed}", config=DevelopmentConfig(max_conditions=count))
    generator.schema = schema
    for episode in range(1, episodes + 1):
        generator.completed = episode
        generator._birth()
        if len(generator.conditions) == count:
            break
    if len(generator.conditions) != count:
        raise ValueError("episode budget cannot reveal the full mixed representation")
    mixed = tuple(Proposal(c.atoms, c.operator, c.born)
                  for c in generator.conditions.values())
    rng = random.Random(f"atoms:{seed}")
    atomic = tuple(Proposal((atom,), "and", 0) for atom in rng.sample(vocabulary, count))
    return mixed, atomic


class AttributionDevelopment(TerminalDevelopment):
    """Same graph action/credit implementation; only representation timing varies.

    All arms disable retirement to isolate representation/timing from survival.
    Production TerminalDevelopment, including its pruning and RNG, is unchanged.
    """

    def __init__(self, schema, *, seed, arm, mixed, atomic):
        if arm not in ARMS:
            raise ValueError("unknown attribution arm")
        if not mixed or len(mixed) != len(atomic):
            raise ValueError("arms require equal nonzero condition-weight budgets")
        for plan in (mixed, atomic):
            keys = {(p.operator, p.atoms) for p in plan}
            if len(keys) != len(plan):
                raise ValueError("duplicate structural definitions")
            for p in plan:
                if p.operator not in ("and", "or", "xor") or not 1 <= len(p.atoms) <= 3:
                    raise ValueError("unsupported condition grammar")
                if len({i for i, _ in p.atoms}) != len(p.atoms):
                    raise ValueError("condition coordinates must be distinct")
                for index, value in p.atoms:
                    if not 0 <= index < len(schema):
                        raise ValueError("coordinate outside schema")
                    schema[index].validate(value)
        if any(len(p.atoms) != 1 or p.operator != "and" for p in atomic):
            raise ValueError("atomic control must contain only single readers")
        if any(p.after_episode < 1 for p in mixed):
            raise ValueError("online proposals must follow a completed exercise")
        if list(mixed) != sorted(mixed, key=lambda p: p.after_episode):
            raise ValueError("proposal schedule must be chronological")
        super().__init__(seed=f"exploration:{seed}",
                         config=DevelopmentConfig(max_conditions=len(mixed)))
        self.schema = tuple(schema)
        self.arm = arm
        self.plan = tuple(atomic if arm == "atomic_only" else mixed)
        if arm != "online_random":
            for proposal in self.plan:
                self._install(proposal)

    def _install(self, proposal):
        cid = self.next_condition
        self.next_condition += 1
        condition = Condition(cid, proposal.atoms, proposal.operator, self.completed)
        self.conditions[cid] = condition
        for slot in range(self.slots):
            self._add_condition_slot(condition, slot)

    def _birth(self):
        if self.arm == "online_random":
            for proposal in self.plan:
                if proposal.after_episode == self.completed:
                    self._install(proposal)

    def _prune(self):
        # Laboratory control held equal in all three arms, not a proposed
        # production survival law. Young candidates still act and learn.
        pass
