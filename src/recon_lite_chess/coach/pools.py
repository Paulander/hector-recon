"""Offline curation only. Solving a candidate here never supplies an action label.

Only FENs leave preparation. D4-equivalent boards always belong to the same split,
including when the same pool is regenerated on a second computer.
"""

import hashlib
import json
from pathlib import Path
import random

import chess


def orbit_key(board: chess.Board) -> str:
    squares = (board.king(chess.WHITE), next(iter(board.pieces(chess.ROOK, chess.WHITE))),
               board.king(chess.BLACK))
    images = []
    for reflection in (False, True):
        for rotations in range(4):
            row = []
            for square in squares:
                x, y = chess.square_file(square), chess.square_rank(square)
                if reflection:
                    x = 7 - x
                for _ in range(rotations):
                    x, y = 7 - y, x
                row.append(chess.square(x, y))
            images.append(tuple(row))
    return ",".join(map(str, min(images)))


def _mate_available(board: chess.Board) -> bool:
    for move in list(board.legal_moves):
        board.push(move)
        mate = board.is_checkmate()
        board.pop()
        if mate:
            return True
    return False


def prepare(directory: Path, *, seed: int, train: int, validation: int, test: int,
            max_attempts: int = 1_000_000) -> dict:
    counts = {"train": train, "validation": validation, "test": test}
    if any(n < 1 for n in counts.values()):
        raise ValueError("all splits must have a positive size")
    if directory.exists():
        raise FileExistsError("pool directory exists; reuse it or choose a new directory")
    rng = random.Random(seed)
    rows = {key: [] for key in counts}
    seen = set()
    edge = [sq for sq in chess.SQUARES if chess.square_file(sq) in (0, 7)
            or chess.square_rank(sq) in (0, 7)]
    for attempt in range(max_attempts):
        if all(len(rows[key]) == count for key, count in counts.items()):
            break
        # Geometry curates exercises only. It never enters the learner as a
        # stage, reward bonus, chosen action, or supplied tactical detector.
        bk = rng.choice(edge)
        wk, wr = rng.sample([sq for sq in chess.SQUARES if sq != bk], 2)
        board = chess.Board(None)
        for square, kind, color in ((wk, chess.KING, True), (wr, chess.ROOK, True),
                                    (bk, chess.KING, False)):
            board.set_piece_at(square, chess.Piece(kind, color))
        board.turn = chess.WHITE
        if not board.is_valid() or board.is_game_over(claim_draw=False):
            continue
        fen = board.fen()
        if fen in seen:
            continue
        canonical = orbit_key(board)
        bucket = int(hashlib.sha256(f"{seed}:{canonical}".encode()).hexdigest()[:8], 16) % 10
        split = "train" if bucket < 8 else "validation" if bucket == 8 else "test"
        if len(rows[split]) >= counts[split] or not _mate_available(board):
            continue
        rows[split].append(fen)
        seen.add(fen)
    if any(len(rows[key]) != count for key, count in counts.items()):
        raise RuntimeError(f"pool budget exhausted: { {k: len(v) for k, v in rows.items()} }")
    directory.mkdir(parents=True)
    manifest = {"schema": "mate_one_pool.v1", "seed": seed, "splits": {},
                "curation": "legal KRK with an available mate; only positions exported",
                "partition": "D4 orbit hash; 80/10/10"}
    for split, fens in rows.items():
        data = ("\n".join(fens) + "\n").encode()
        (directory / f"{split}.txt").write_bytes(data)
        manifest["splits"][split] = {
            "count": len(fens), "sha256": hashlib.sha256(data).hexdigest(),
            "distinct_orbits": len({orbit_key(chess.Board(fen)) for fen in fens}),
        }
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def load_split(directory: Path, split: str) -> tuple[tuple[str, ...], str]:
    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest["schema"] != "mate_one_pool.v1" or split not in ("train", "validation", "test"):
        raise ValueError("unsupported pool schema/split")
    data = (directory / f"{split}.txt").read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    rows = tuple(data.decode().splitlines())
    if digest != manifest["splits"][split]["sha256"] or len(rows) != manifest["splits"][split]["count"]:
        raise ValueError("pool content differs from its frozen manifest")
    return rows, digest
