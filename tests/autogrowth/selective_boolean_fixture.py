"""Pure mechanical fixture extracted from the closed Boolean study.

No experiment runner, study schedule, stored outcomes or training is imported.
"""
import inspect
import itertools

from recon_lite_hector.learning.terminal_development import Coordinate, DevelopmentConfig
from recon_lite_hector.learning.context_decision import OwnershipLimits
from recon_lite_hector.learning.owner_development import OwnerDevelopmentConfig
from recon_lite_hector.learning.owner_birth_search import BirthSearchConfig
from recon_lite_hector.learning.fresh_owner import FreshOwnerDevelopment

BOOL = (False, True)
ROWS = tuple(itertools.product(BOOL, repeat=4))


class BooleanEnvironment:
    schema = tuple(Coordinate(f"coordinate-{i}", BOOL) for i in range(5))

    def __init__(self, row):
        self._row, self._executed = row, None

    def bindings(self):
        assert inspect.currentframe().f_back.f_code.co_name == "_catalog"
        return ("act-a", "act-b")

    def measure(self, coordinate, binding):
        assert inspect.currentframe().f_back.f_code.co_name == "_reader"
        return (*self._row, binding == "act-b")[coordinate]

    def execute(self, binding):
        assert inspect.currentframe().f_back.f_code.co_name == "_actuator"
        assert self._executed is None and binding in ("act-a", "act-b")
        self._executed = binding

    def outcome(self):
        x, y, z, _noise = self._row
        assert self._executed is not None
        return 1 if (self._executed == "act-b") == (y if z else x) else -1


def create_actor(seed, role):
    assert role == "current"
    return FreshOwnerDevelopment.create(
        schema=BooleanEnvironment.schema, state_coordinates=(0, 1, 2, 3), seed=seed,
        config=DevelopmentConfig(max_conditions=8),
        search=BirthSearchConfig(mode="residual"),
        development=OwnerDevelopmentConfig(),
        limits=OwnershipLimits(max_leaves=4, max_parameters=64,
                               max_definitions=256, max_physical_nodes=2048),
    )


def same_state(left, right):
    assert type(left) is type(right)
    excluded = {"graph", "rng", "proposal_rng", "exploration_rng"}
    assert vars(left).keys() == vars(right).keys()
    for name in vars(left).keys() - excluded:
        assert getattr(left, name) == getattr(right, name), name
    for name in ("rng", "proposal_rng", "exploration_rng"):
        assert getattr(left, name).getstate() == getattr(right, name).getstate()
    assert vars(left.graph) == vars(right.graph)
