"""Isolated owner-development extension: reject proven-impossible new births.

Proposal generation and installation mirror the unchanged owner control. One
draw per opportunity, including rejected draws; no replacement search or merging.
"""
import copy
from dataclasses import asdict, replace
from time import perf_counter

from .context_compatibility import CompatibilityConfig, Verdict, prepare_check, solve_prepared
from .owner_development import AdaptiveOwnerDevelopment
from .recursive_context import Expression, combine
from .terminal_development import Condition, PlasticWeight


class CompatibleOwnerDevelopment(AdaptiveOwnerDevelopment):
    @classmethod
    def from_actor(cls, source, *, compatibility=None, **kwargs):
        actor = super().from_actor(source, **kwargs)
        actor.compatibility_config = compatibility or CompatibilityConfig()
        actor.rejection_cache = {}
        actor.birth_proposals = []
        return actor

    def _compatibility(self, owner, expression):
        config = self.compatibility_config
        if not config.enabled:
            return Verdict("disabled"), False
        prepared = prepare_check(self.leaves[owner].path, expression, self.schema, config)
        if isinstance(prepared, Verdict):
            return prepared, False
        key = (owner, prepared.signature)
        if key in self.rejection_cache:
            return Verdict("impossible", reason="cached proof"), True
        verdict = solve_prepared(prepared)
        if verdict.status == "impossible":
            if len(self.rejection_cache) >= config.cache_entries:
                del self.rejection_cache[next(iter(self.rejection_cache))]
            self.rejection_cache[key] = verdict
        return verdict, False

    def _birth_local(self, owner):
        record = {"episode": self.completed, "owner": owner,
                  "path": self.leaves[owner].path, "local_visit": self.owner_visits[owner],
                  "proposal": None, "outcome": None, "birth": None}
        self.birth_proposals.append(record)
        if len(self.conditions) >= self.ownership_limits.max_parameters:
            record["outcome"] = "parameter budget: no draw"
            return None
        rng = self.proposal_rng
        indices = rng.sample(range(len(self.schema)), rng.randint(1, min(3, len(self.schema))))
        atoms = tuple(sorted((i, rng.choice(self.schema[i].values)) for i in indices))
        operator = rng.choices(("and", "or", "xor"), weights=(8, 1, 1))[0] if len(atoms) > 1 else "and"
        expression = combine(operator, tuple(Expression("read", atom=atom) for atom in atoms))
        record["proposal"] = expression
        if expression in self.owner_seen[owner]:
            record["outcome"] = "already seen"
            return None
        started = perf_counter()
        verdict, cached = self._compatibility(owner, expression)
        record.update(verdict=asdict(verdict), cached=cached,
                      check_seconds=perf_counter()-started)
        if verdict.status == "impossible":
            record["outcome"] = "contradiction"
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
            record["outcome"] = "graph budget"
            return None
        trial.birth_proposals[-1].update(outcome="born", birth=cid)
        self.__dict__ = trial.__dict__
        return cid
