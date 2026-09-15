"""Initialize the existing owner-local learner without any learned prefix.

Only the declared terminal schema and generic organism configuration enter
construction. Actual bindings and measurements remain formal-terminal work.
"""
from .owner_birth_search import BirthSearchOwnerDevelopment
from .recursive_context import RecursiveConfig, RecursiveDevelopment
from .terminal_development import Coordinate, TerminalDevelopment


class FreshOwnerDevelopment(BirthSearchOwnerDevelopment):
    @classmethod
    def create(cls, *, schema, state_coordinates, seed=1, config=None, **kwargs):
        schema = tuple(schema)
        if not schema or not all(isinstance(c, Coordinate) for c in schema):
            raise ValueError("a fixed typed terminal schema is required")
        # Reuse only the empty structural constructor. There is no act/observe,
        # learned checkpoint, planted feature, route, binding or initial weight.
        source = RecursiveDevelopment(seed=seed, config=config,
            recursive_config=RecursiveConfig(role="flat", prefix=128))
        source.schema = schema
        # A formal SCRIPT must have a child. One generic unbound request site
        # keeps the zero-training checkpoint valid without reading a catalog.
        source._ensure_slots(1)
        return cls.from_actor(source, state_coordinates=state_coordinates,
                              search_seed=seed, **kwargs)

    def act(self, port, *, event_id, learn):
        if self.context_pending is not None or self.pending:
            raise RuntimeError("fresh owner requires immediate actual feedback")
        # Ownership and its matched exploration stream are active from action
        # zero. The ancestor's dormant flat-prefix RNG switch is never entered.
        birth_rng = self.rng
        self.rng = self.exploration_rng
        try:
            return TerminalDevelopment.act(self, port, event_id=event_id, learn=learn)
        finally:
            self.rng = birth_rng
