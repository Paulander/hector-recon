from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import chess
import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
except ImportError:
    class _DummyEnv:
        def reset(self, seed: Optional[int] = None):
            if seed is not None:
                self.np_random = np.random.default_rng(seed)
            elif not hasattr(self, "np_random"):
                self.np_random = np.random.default_rng()

    class _DummyBox:
        def __init__(self, low: int, high: int, shape: tuple[int, ...], dtype: Any):
            self.low = low
            self.high = high
            self.shape = shape
            self.dtype = dtype

    class _DummyDiscrete:
        def __init__(self, n: int):
            self.n = n

    class _DummySpaces:
        Box = _DummyBox
        Discrete = _DummyDiscrete

    class _DummyGym:
        Env = _DummyEnv

    gym = _DummyGym()  # type: ignore
    spaces = _DummySpaces()  # type: ignore

from benchmark_common import KPK_STAGES, generate_kpk_curriculum_position


class KPKStageEnv(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        stage: int,
        max_moves: int = 100,
        render_mode: Optional[str] = None,
    ):
        super().__init__()
        self.stage = stage
        self.max_moves = max_moves
        self.render_mode = render_mode

        self.observation_space = spaces.Box(
            low=-6, high=6, shape=(64,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(218)

        self.board: Optional[chess.Board] = None
        self.move_count = 0
        self.legal_moves_list: list[chess.Move] = []
        self.last_outcome = "unknown"

    def _get_obs(self) -> np.ndarray:
        obs = np.zeros(64, dtype=np.float32)
        assert self.board is not None
        for sq in range(64):
            piece = self.board.piece_at(sq)
            if piece:
                val = piece.piece_type
                if piece.color == chess.BLACK:
                    val = -val
                obs[sq] = val
        return obs

    def _get_info(self) -> Dict[str, Any]:
        assert self.board is not None
        return {
            "fen": self.board.fen(),
            "legal_moves": len(self.legal_moves_list),
            "move_count": self.move_count,
            "stage": self.stage,
            "outcome": self.last_outcome,
        }

    def _generate_position(self) -> chess.Board:
        stage = KPK_STAGES[self.stage]
        return generate_kpk_curriculum_position(stage)

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)
        self.move_count = 0
        self.last_outcome = "in_progress"

        if options and options.get("fen"):
            board = chess.Board(options["fen"])
            if not board.is_valid():
                raise ValueError(f"Invalid FEN in reset options: {options['fen']}")
            self.board = board
        else:
            self.board = self._generate_position()

        self.legal_moves_list = list(self.board.legal_moves)
        return self._get_obs(), self._get_info()

    def step(self, action: int):
        assert self.board is not None

        if not self.legal_moves_list:
            self.last_outcome = "loss"
            return self._get_obs(), -1.0, True, False, self._get_info()

        action = int(action)
        if action >= len(self.legal_moves_list):
            move = self.np_random.choice(self.legal_moves_list)
        else:
            move = self.legal_moves_list[action]

        promoted = move.promotion is not None
        self.board.push(move)
        self.move_count += 1

        reward = 0.0
        terminated = False
        truncated = False

        if self.board.is_checkmate():
            reward = 1.0
            terminated = True
            self.last_outcome = "checkmate"
        elif promoted:
            reward = 0.5
            terminated = True
            self.last_outcome = "promotion"
        elif self.board.is_stalemate() or self.board.is_insufficient_material():
            reward = -0.5
            terminated = True
            self.last_outcome = "draw"
        elif self.move_count >= self.max_moves:
            reward = -0.2
            truncated = True
            self.last_outcome = "timeout"
        else:
            black_moves = list(self.board.legal_moves)
            if black_moves:
                black_move = self.np_random.choice(black_moves)
                self.board.push(black_move)
                self.move_count += 1
            if self.board.is_checkmate():
                reward = -1.0
                terminated = True
                self.last_outcome = "loss"
            elif (
                self.board.is_stalemate()
                or self.board.is_insufficient_material()
                or self.board.can_claim_draw()
            ):
                reward = -0.5
                terminated = True
                self.last_outcome = "draw"
            elif self.move_count >= self.max_moves:
                reward = -0.2
                truncated = True
                self.last_outcome = "timeout"

        if not terminated and not truncated:
            self.legal_moves_list = list(self.board.legal_moves)
            if not self.legal_moves_list:
                terminated = True
                if self.board.is_checkmate():
                    reward = -1.0
                    self.last_outcome = "loss"
                else:
                    reward = -0.5
                    self.last_outcome = "draw"
        else:
            self.legal_moves_list = []

        return self._get_obs(), reward, terminated, truncated, self._get_info()

    def render(self):
        if self.render_mode == "human" and self.board:
            print(self.board)
