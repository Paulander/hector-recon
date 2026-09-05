"""The complete coach/organism information boundary.

No graph, candidate, value, virtual frame, target move, or exercise family is
part of the teaching signal. The current embodiment offers typed coordinate
measurements and primitive actions to graph terminals. BoardSensor is retained
only for the historical hybrid adapter and its regression tests.
"""

from dataclasses import dataclass
from typing import Protocol, TypeVar


Observation = TypeVar("Observation", contravariant=True)


@dataclass(frozen=True)
class PositionReading:
    pieces: tuple[tuple[int, int, bool], ...]
    white_to_move: bool
    halfmove_clock: int
    fullmove_number: int


@dataclass(frozen=True)
class BoardSensor:
    """Legacy read-only board snapshot; not a learned feature-terminal substrate."""

    reading: PositionReading

    def measure(self) -> PositionReading:
        return self.reading


@dataclass(frozen=True)
class Feedback:
    """Scalar teaching signal plus binding to the learner's own submitted action.

    Event/action fields prevent stale or duplicate credit. They are not feature
    inputs. Outcome categories and diagnostic explanations stay in the coach.
    """

    event_id: int
    action: str | None
    reward: float


class Organism(Protocol[Observation]):
    def act(self, sensor: Observation, *, event_id: int, learn: bool) -> str | None: ...

    def observe(self, feedback: Feedback) -> None: ...
