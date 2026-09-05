"""The complete coach/organism information boundary.

No graph, candidate, value, virtual frame, target move, or exercise family is
part of this protocol. A sensor supplies a frozen board measurement. The native
organism reconstructs its own rules-model state from that measurement.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PositionReading:
    pieces: tuple[tuple[int, int, bool], ...]
    white_to_move: bool
    halfmove_clock: int
    fullmove_number: int


@dataclass(frozen=True)
class BoardSensor:
    """Read-only measured feature space, with no reference to the live board."""

    reading: PositionReading

    def measure(self) -> PositionReading:
        return self.reading


@dataclass(frozen=True)
class Feedback:
    event_id: int
    action: str | None
    reward: float
    reason: str


class Organism(Protocol):
    def act(self, sensor: BoardSensor, *, event_id: int, learn: bool) -> str | None: ...

    def observe(self, feedback: Feedback) -> None: ...
