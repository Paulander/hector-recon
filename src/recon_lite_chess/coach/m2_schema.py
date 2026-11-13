"""Explicit, opt-in current-board geometry for the two-action exercise."""

import chess

from recon_lite_hector.learning.terminal_development import Coordinate

from .terminal import ChessFeaturePort, DISTANCE, SCHEMA


M1_SCHEMA_VERSION = "chess_relational16.v1"
M2_SCHEMA_VERSION = "chess_relational20.v2"
M2_SCHEMA = SCHEMA + tuple(Coordinate(name, domain) for name, domain in (
    ("target_current_rook_file_distance", DISTANCE),
    ("target_current_rook_rank_distance", DISTANCE),
    ("target_nearest_file_edge_distance", tuple(range(4))),
    ("target_nearest_rank_edge_distance", tuple(range(4))),
))


def _schema_signature(schema):
    # Coordinate equality alone treats (False, True) as equal to (0, 1).
    return tuple((coordinate.name, type(coordinate.values[0]).__name__,
                  tuple(coordinate.values)) for coordinate in schema)


def schema_version(schema) -> str:
    """Recognize an exact typed schema; never infer a migration from length."""
    signature = _schema_signature(schema)
    for version, known in ((M1_SCHEMA_VERSION, SCHEMA),
                           (M2_SCHEMA_VERSION, M2_SCHEMA)):
        if signature == _schema_signature(known):
            return version
    raise ValueError("unrecognized chess terminal schema")


class M2ChessFeaturePort(ChessFeaturePort):
    """Twenty-coordinate port; every measurement remains a terminal request."""

    schema = M2_SCHEMA
    sensor_schema_version = M2_SCHEMA_VERSION

    def measure(self, coordinate, binding):
        if type(coordinate) is not int or not 0 <= coordinate < len(self.schema):
            raise ValueError("coordinate outside the declared twenty-coordinate schema")
        if coordinate < len(SCHEMA):
            return super().measure(coordinate, binding)
        if self.executed is not None:
            raise RuntimeError("an action invalidates this observation frame")
        move = self._moves[binding]
        rook = next(iter(self._board.pieces(chess.ROOK, chess.WHITE)))
        tx, ty = chess.square_file(move.to_square), chess.square_rank(move.to_square)
        rx, ry = chess.square_file(rook), chess.square_rank(rook)
        measurements = (abs(tx - rx), abs(ty - ry), min(tx, 7 - tx), min(ty, 7 - ty))
        return self.schema[coordinate].validate(measurements[coordinate - len(SCHEMA)])
