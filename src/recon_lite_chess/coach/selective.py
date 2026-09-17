"""Fresh chess embodiment of the existing local refinement learners.

The factory supplies the declared terminal schema and resource knobs only. It
does not supply a condition, a move label, a corner rule, or learned weights.
The ordinary role is the unchanged terminal learner, not a matched causal
control for every mechanism in the refinement family.
"""
from dataclasses import replace

from recon_lite_hector.learning.context_decision import OwnershipLimits
from recon_lite_hector.learning.owner_birth_search import BirthSearchConfig
from recon_lite_hector.learning.owner_development import OwnerDevelopmentConfig
from recon_lite_hector.learning.refining_route_action import (
    ProspectiveRefiningRouteActionDevelopment,
    RefiningRouteActionDevelopment,
)
from recon_lite_hector.learning.terminal_development import DevelopmentConfig

from .terminal import SCHEMA, TerminalOrganism


# These measurements depend only on the current board. All other declared
# coordinates describe the candidate primitive move and may vary by binding.
STATE_COORDINATES = (0, 2, 3, 4, 5, 10, 11, 14, 15)
ROLES = ("selective", "refining", "ordinary")


class SelectiveMateOneOrganism(ProspectiveRefiningRouteActionDevelopment):
    """Embodiment marker; action selection and learning stay in the generic core."""

    embodiment = "typed_feature_terminals_v1"


class RefiningMateOneOrganism(RefiningRouteActionDevelopment):
    """Same chess terminals, with the existing non-prospective refinement control."""

    embodiment = "typed_feature_terminals_v1"


def create_actor(*, seed=1, role="selective", config=None, limits=None,
                 search=None, development=None, prospective_resource_cost=0.25):
    """Construct a zero-training actor, keeping reclosure and owner splitting off.

    ``config`` contains shared weight-learning, exploration and pruning knobs.
    The remaining settings apply to the refinement-family roles only. Their
    defaults expose all 42 existing state equality readers, 64 randomly drawn
    ordinary birth candidates, and one development opportunity per 64 actions.
    Larger graph limits accommodate the variable number of legal chess moves;
    they do not populate the graph with learned conditions.
    """
    if role not in ROLES:
        raise ValueError(f"unknown mate-one actor role: {role!r}")
    config = config or DevelopmentConfig()
    if role == "ordinary":
        if any(value is not None for value in (limits, search, development)):
            raise ValueError("ordinary role takes DevelopmentConfig only")
        return TerminalOrganism(seed=seed, config=config)

    limits = limits or OwnershipLimits(
        max_leaves=1, max_parameters=96, max_definitions=512,
        max_physical_nodes=32768,
    )
    search = search or BirthSearchConfig(mode="residual", candidates=64)
    development = replace(
        development or OwnerDevelopmentConfig(candidates=42), split_enabled=False,
    )
    implementation = (SelectiveMateOneOrganism if role == "selective"
                      else RefiningMateOneOrganism)
    options = ({"prospective_resource_cost": prospective_resource_cost}
               if role == "selective" else {})
    actor = implementation.create(
        schema=SCHEMA, state_coordinates=STATE_COORDINATES, seed=seed,
        config=config, limits=limits, search=search, development=development,
        reclosure_enabled=False, **options,
    )
    if actor.reclosure_enabled:
        raise RuntimeError("mate-one curriculum requires reclosure disabled")
    return actor
