"""Anonymous exactly-one actuator choice materialized as a ReCoN genome."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from .formal_engine import FormalReConEngine
from .graph import Graph, Node, NodeState, NodeType


def finite_local_uncertainty(exposures: int, population_exposures: int) -> float:
    """A finite, renewable uncertainty activation from local REAL counts.

    The one-count denominator regularizes an untried alternative; it is not
    a fabricated outcome or certification receipt. Unlike an infinite/ordinal
    first-contact tier, this signal can lose to an experienced good option.
    No epoch, board identity, reward label, or global activity enters it.
    This is a UCB-style exploration heuristic, not a calibrated confidence
    interval for a changing graph policy.
    """

    for value in (exposures, population_exposures):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("local exposure counts must be nonnegative integers")
    if exposures > population_exposures:
        raise ValueError("option exposure exceeds its local population")
    return math.sqrt(2.0 * math.log1p(population_exposures) / (1 + exposures))


@dataclass(frozen=True)
class AnonymousChoiceOption:
    """One semantic-free option already measured by graph terminals."""

    identity: str
    actuator_identity: str
    activation: float
    confirmed: bool = True


@dataclass(frozen=True)
class AnonymousChoiceEmission:
    actuator_identity: str
    option_identity: str
    activation: float
    formal_ticks: int


def _measured_terminal(value: float, confirmed: bool):
    def predicate(node: Node, _env: dict[str, object]) -> tuple[bool, bool]:
        node.activation.value = float(value)
        return True, bool(confirmed)
    return predicate


class AnonymousChoiceGenome:
    """Domain-blind genome primitive that lets the formal graph choose."""

    ROOT_ID = "generic_choice_root"

    def emit(self, options: Iterable[AnonymousChoiceOption], *, max_ticks: int = 32) -> AnonymousChoiceEmission:
        rows = tuple(options)
        if not rows:
            raise RuntimeError("anonymous choice requires at least one option")
        if len({row.identity for row in rows}) != len(rows):
            raise ValueError("anonymous option identities must be unique")
        graph = Graph()
        graph.add_node(Node(self.ROOT_ID, NodeType.SCRIPT, meta={
            "confirm_policy": "choice",
            "genome_primitive": "anonymous_exactly_one_choice",
        }))
        for index, row in enumerate(rows):
            option_id = f"generic_choice_option_{index}"
            sensor_id = f"generic_choice_measurement_{index}"
            graph.add_node(Node(option_id, NodeType.SCRIPT, meta={
                "confirm_policy": "and",
                "anonymous_option_identity": row.identity,
                "actuator_identity": row.actuator_identity,
                "choice_strength_node_ids": [sensor_id],
                "choice_strength_require_all": True,
                "choice_strength_aggregation": "minimum",
            }))
            graph.add_node(Node(
                sensor_id,
                NodeType.TERMINAL,
                predicate=_measured_terminal(row.activation, row.confirmed),
                meta={"terminal_kind": "anonymous_internal_measurement"},
            ))
            graph.add_hierarchy_pair(self.ROOT_ID, option_id)
            graph.add_hierarchy_pair(option_id, sensor_id)
        engine = FormalReConEngine(graph, record_trace=False)
        engine.request(self.ROOT_ID)
        engine.run(
            max_ticks=max_ticks,
            until=lambda item: item.g.nodes[self.ROOT_ID].state in {NodeState.CONFIRMED, NodeState.FAILED},
        )
        actuator = engine.emit_exactly_one_actuator(self.ROOT_ID)
        selected_id = str(graph.nodes[self.ROOT_ID].meta["choice_selected_child"])
        selected = graph.nodes[selected_id]
        return AnonymousChoiceEmission(
            actuator_identity=actuator,
            option_identity=str(selected.meta["anonymous_option_identity"]),
            activation=float(selected.activation.value),
            formal_ticks=engine.tick,
        )
