"""TG26h FeatureHub / terminal substrate revival.

This checkpoint keeps the dense Mate_In_1/Mate_In_2 curriculum runway, but
represents behavior-changing credit as first-class TERMINAL nodes with local
weights instead of treating ``ActionRanker.choose`` as the main learner.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

import chess

from recon_lite_hector.nodes.stem_cell import StemCellState, StemCellTerminal

from recon_lite_chess.features.hub import FeatureHub, create_default_hub
from recon_lite_chess.features.krk_features import KRKFeatures

from .features import extract_learner_features, validate_learner_record
from .foundation_curriculum import (
    ActionRanker,
    _action_feature_keys,
    _forced_mate_in_two_first_moves,
    _generate_forced_mate_in_two_positions,
    _generate_mate_in_one_positions,
    _mate_moves,
    _mirrored_positions,
    _move_reward,
    _rook_missing_or_attacked,
    _train_mate_in_one,
    _train_mate_in_two,
    _evaluate_mate_in_one,
    _evaluate_mate_in_two,
)


SAFE_FEATURE_HUB_NAMES = (
    "opposition_status",
    "mobility",
    "king_tropism",
    "mobility_restriction",
    "tempo_advantage",
    "mating_net_present",
    "enemy_king_rank",
    "enemy_king_file",
    "enemy_king_at_edge",
    "enemy_king_in_corner",
    "enemy_king_mobility",
    "enemy_king_mobility_raw",
    "stalemate_danger",
)

ACTION_AFTER_EXCLUDED_TERMINAL_FLAGS = frozenset({"is_checkmate"})


@dataclass(frozen=True)
class TerminalSubstrateConfig:
    seed: int = 20260612
    mate1_train_count: int = 300
    mate1_heldout_count: int = 100
    mate1_mirror_count: int = 40
    mate2_train_count: int = 300
    mate2_heldout_count: int = 100
    mate2_enabled: bool = True
    max_generation_attempts: int = 500_000
    eta_m3: float = 0.10
    rich_feature_credit_scale: float = 0.25
    mate1_pass_threshold: float = 0.95
    mate2_pass_threshold: float = 0.80
    max_samples: int = 12


@dataclass
class FeatureVectorTerminal:
    """One spawned/specialized TERMINAL pattern over the feature vector."""

    terminal_key: str
    cell: StemCellTerminal
    local_weight: float = 0.0
    positive_credit: int = 0
    negative_credit: int = 0
    neutral_credit: int = 0
    request_exposures: int = 0
    activation_count: int = 0
    confirm_count: int = 0

    def update(self, *, reward: float, eta: float, scale: float, cycle: int) -> None:
        self.request_exposures += 1
        self.activation_count += 1
        self.local_weight += eta * scale * reward
        self.cell.xp += 1
        self.cell.total_exposures += 1
        self.cell.candidate_stats.record_request(parent_id="terminal_feature_parent")
        self.cell.candidate_stats.record_activation(parent_id="terminal_feature_parent")
        if reward > 0.0:
            self.positive_credit += 1
            self.confirm_count += 1
            self.cell.xp_successes += 1
            self.cell.candidate_stats.record_confirm(cycle, parent_id="terminal_feature_parent")
            self.cell.candidate_stats.record_intervention("positive")
        elif reward < 0.0:
            self.negative_credit += 1
            self.cell.xp_failures += 1
            self.cell.candidate_stats.record_intervention("negative")
        else:
            self.neutral_credit += 1
            self.cell.candidate_stats.record_intervention("neutral")
        self.cell.candidate_stats.recompute_survival(
            xp=self.cell.xp,
            solidify_xp=self.cell.XP_SOLIDIFY,
        )

    def to_dict(self) -> dict[str, Any]:
        learner_visible = {
            "node_type": "TERMINAL",
            "terminal_key": self.terminal_key,
            "stem_cell_state": self.cell.state.name,
            "local_weight": round(self.local_weight, 6),
            "positive_credit": self.positive_credit,
            "negative_credit": self.negative_credit,
            "neutral_credit": self.neutral_credit,
            "request_exposures": self.request_exposures,
            "activation_count": self.activation_count,
            "confirm_count": self.confirm_count,
            "relation_to_output": "local_terminal_affordance_weight",
            "chooses_move_directly": False,
        }
        validate_learner_record(learner_visible)
        return {
            "cell": self.cell.to_dict(),
            "learner_visible": learner_visible,
            "diagnostics": {
                "m3_local_weight": round(self.local_weight, 6),
                "positive_credit": self.positive_credit,
                "negative_credit": self.negative_credit,
                "neutral_credit": self.neutral_credit,
            },
        }


@dataclass
class TerminalAffordanceLearner:
    """Terminal-native substrate used for TG26h foundation reproduction."""

    terminals: dict[str, FeatureVectorTerminal]
    eta_m3: float
    rich_feature_credit_scale: float
    hub: FeatureHub
    m3_update_count: int = 0
    cycle: int = 0
    feature_cache: dict[str, dict[str, float]] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        eta_m3: float,
        rich_feature_credit_scale: float = 0.25,
    ) -> "TerminalAffordanceLearner":
        return cls(
            terminals={},
            eta_m3=eta_m3,
            rich_feature_credit_scale=rich_feature_credit_scale,
            hub=create_default_hub(),
        )

    def get_terminal(self, terminal_key: str) -> FeatureVectorTerminal:
        terminal = self.terminals.get(terminal_key)
        if terminal is None:
            cell = StemCellTerminal(f"tg26h_terminal_{len(self.terminals):05d}")
            cell.state = StemCellState.TRIAL
            cell.trial_node_id = f"TRIAL_{cell.cell_id}"
            cell.trial_parent_id = "terminal_feature_parent"
            cell.metadata = {
                "node_type": "TERMINAL",
                "terminal_kind": "feature_vector_pattern",
                "terminal_key": terminal_key,
                "relation_types": ["SUB", "SUR", "POR"],
                "fan_in_allowed": True,
            }
            terminal = FeatureVectorTerminal(terminal_key=terminal_key, cell=cell)
            self.terminals[terminal_key] = terminal
        return terminal

    def train_position(self, board: chess.Board, *, positive_moves: set[str]) -> dict[str, int]:
        rewards = {
            move.uci(): _move_reward(board, move, positive_moves=positive_moves)
            for move in board.legal_moves
        }
        return self.train_position_rewards(board, move_rewards=rewards)

    def train_position_rewards(self, board: chess.Board, *, move_rewards: Mapping[str, float]) -> dict[str, int]:
        updates = {"positive": 0, "negative": 0, "neutral": 0}
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            reward = float(move_rewards.get(move.uci(), 0.0))
            self.cycle += 1
            for terminal_key, scale in terminal_action_feature_keys(
                board,
                move,
                hub=self.hub,
                feature_cache=self.feature_cache,
            ):
                terminal = self.get_terminal(terminal_key)
                effective_scale = 1.0 if scale >= 1.0 else self.rich_feature_credit_scale
                terminal.update(
                    reward=reward,
                    eta=self.eta_m3,
                    scale=effective_scale,
                    cycle=self.cycle,
                )
                self.m3_update_count += 1
            if reward > 0.0:
                updates["positive"] += 1
            elif reward < 0.0:
                updates["negative"] += 1
            else:
                updates["neutral"] += 1
        return updates

    def choose(self, board: chess.Board) -> chess.Move | None:
        options: list[tuple[float, str, chess.Move]] = []
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            options.append((self.weight_for_move(board, move), move.uci(), move))
        if not options:
            return None
        options.sort(reverse=True)
        return options[0][-1]

    def weight_for_move(self, board: chess.Board, move: chess.Move) -> float:
        return sum(
            self.terminals[terminal_key].local_weight
            for terminal_key, _scale in terminal_action_feature_keys(
                board,
                move,
                hub=self.hub,
                feature_cache=self.feature_cache,
            )
            if terminal_key in self.terminals
        )

    def active_terminal_count(self, board: chess.Board, move: chess.Move) -> int:
        return sum(
            1
            for terminal_key, _scale in terminal_action_feature_keys(
                board,
                move,
                hub=self.hub,
                feature_cache=self.feature_cache,
            )
            if terminal_key in self.terminals
        )

    def to_dict(self, *, max_terminals: int = 24) -> dict[str, Any]:
        terminals = sorted(
            self.terminals.values(),
            key=lambda item: item.local_weight,
            reverse=True,
        )
        return {
            "terminal_count": len(terminals),
            "m3_update_count": self.m3_update_count,
            "top_positive_terminals": [
                terminal.to_dict()
                for terminal in terminals[:max_terminals]
            ],
            "top_negative_terminals": [
                terminal.to_dict()
                for terminal in sorted(terminals, key=lambda item: item.local_weight)[:max_terminals]
            ],
        }


@dataclass(frozen=True)
class TerminalSubstrateResult:
    config: TerminalSubstrateConfig
    action_ranker_audit: dict[str, Any]
    feature_coverage: dict[str, Any]
    dataset: dict[str, Any]
    action_ranker_baseline: dict[str, Any]
    terminal_native: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26h_terminal_substrate_revival.v0",
            "checkpoint": "TG26h_terminal_substrate_revival",
            "config": asdict(self.config),
            "audit": {
                "action_ranker_behavior_changing_uses": self.action_ranker_audit,
                "feature_coverage": self.feature_coverage,
            },
            "dataset": self.dataset,
            "training_runway": {
                "staged_experience_distribution": True,
                "mate1_source": "generated legal KRK mate-in-1 variants",
                "mate2_source": "generated legal KRK forced mate-in-2 variants",
                "schedule_labels_learner_visible": False,
                "runtime_tablebase_or_dtm_move_source": False,
                "direct_provider_override": False,
            },
            "local_recon_structure": {
                "primary_behavior_path": "FeatureHub/generic vector TERMINAL substrate",
                "candidate_node_type": "TERMINAL",
                "output_interface": "legal ACTION option supplied by environment",
                "behavior_choice_mediated_by_terminal_activations": True,
                "terminal_weights_receive_m3_credit": True,
                "action_ranker_status": "diagnostic_baseline_scaffolding",
                "remaining_scaffold": [
                    "synchronous Python legal-move enumeration",
                    "terminal activations are evaluated in a batch loop rather than the full tick engine",
                ],
                "direct_move_override": False,
            },
            "action_ranker_baseline": self.action_ranker_baseline,
            "terminal_native": self.terminal_native,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


@dataclass(frozen=True)
class TerminalFoundationBundle:
    """Reusable trained TG26h foundation learners for downstream curriculum."""

    config: TerminalSubstrateConfig
    mate1_train: tuple[str, ...]
    mate1_heldout: tuple[str, ...]
    mate1_mirror: tuple[str, ...]
    mate2_train: tuple[str, ...]
    mate2_heldout: tuple[str, ...]
    mate1_learner: TerminalAffordanceLearner
    mate2_first_learner: TerminalAffordanceLearner | None
    payload: dict[str, Any]


def run_terminal_substrate_revival(
    *,
    config: TerminalSubstrateConfig,
) -> TerminalSubstrateResult:
    bundle = train_terminal_foundation_bundle(config=config)
    action_baseline = _run_action_ranker_baseline(
        config=config,
        mate1_train=bundle.mate1_train,
        mate1_heldout=bundle.mate1_heldout,
        mate1_mirror=bundle.mate1_mirror,
    )
    terminal_native = bundle.payload
    decision = _decision(config=config, terminal_native=terminal_native)
    return TerminalSubstrateResult(
        config=config,
        action_ranker_audit=action_ranker_behavior_audit(),
        feature_coverage=feature_substrate_coverage_sample(bundle.mate1_train[0]),
        dataset={
            "mate1_train_count": len(bundle.mate1_train),
            "mate1_heldout_count": len(bundle.mate1_heldout),
            "mate1_mirror_count": len(bundle.mate1_mirror),
            "mate2_train_count": terminal_native["mate2"]["dataset"]["train_count"],
            "mate2_heldout_count": terminal_native["mate2"]["dataset"]["heldout_count"],
        },
        action_ranker_baseline=action_baseline,
        terminal_native=terminal_native,
        decision=decision,
    )


def train_terminal_foundation_bundle(
    *,
    config: TerminalSubstrateConfig,
) -> TerminalFoundationBundle:
    """Train TG26h Mate_In_1/Mate_In_2 terminal learners and keep objects."""

    mate1_train = tuple(_generate_mate_in_one_positions(
        count=config.mate1_train_count,
        seed=config.seed,
        max_attempts=config.max_generation_attempts,
    ))
    used = set(mate1_train)
    mate1_heldout = tuple(_generate_mate_in_one_positions(
        count=config.mate1_heldout_count,
        seed=config.seed + 1,
        excluded=used,
        max_attempts=config.max_generation_attempts,
    ))
    mate1_mirror = tuple(_mirrored_positions(mate1_heldout, limit=config.mate1_mirror_count))

    terminal_native = _run_terminal_native(
        config=config,
        mate1_train=mate1_train,
        mate1_heldout=mate1_heldout,
        mate1_mirror=mate1_mirror,
    )
    return TerminalFoundationBundle(
        config=config,
        mate1_train=mate1_train,
        mate1_heldout=mate1_heldout,
        mate1_mirror=mate1_mirror,
        mate2_train=tuple(terminal_native["mate2"].get("train_fens", ())),
        mate2_heldout=tuple(terminal_native["mate2"].get("heldout_fens", ())),
        mate1_learner=terminal_native["_mate1_learner"],
        mate2_first_learner=terminal_native["_mate2_first_learner"],
        payload=_strip_runtime_learners(terminal_native),
    )


def extract_terminal_feature_vector(
    board: chess.Board,
    *,
    hub: FeatureHub | None = None,
) -> dict[str, float]:
    """Return generic-safe feature coordinates for terminal spawning."""

    features: dict[str, float] = {
        key: value
        for key, value in extract_learner_features(board).items()
        if key not in ACTION_AFTER_EXCLUDED_TERMINAL_FLAGS
    }
    features.update(_king_geometry_features(board))
    feature_hub = hub or create_default_hub()
    hub_values = feature_hub.compute_all(board, force=True)
    for name in SAFE_FEATURE_HUB_NAMES:
        if name in hub_values:
            features[f"feature_hub_{name}"] = float(hub_values[name])
    validate_learner_record(features)
    return features


def terminal_action_feature_keys(
    board: chess.Board,
    move: chess.Move,
    *,
    hub: FeatureHub | None = None,
    feature_cache: dict[str, dict[str, float]] | None = None,
) -> tuple[tuple[str, float], ...]:
    """Build active TERMINAL keys for a legal move candidate."""

    after = board.copy(stack=False)
    after.push(move)
    before_features = _cached_terminal_feature_vector(board, hub=hub, feature_cache=feature_cache)
    after_features = _cached_terminal_feature_vector(after, hub=hub, feature_cache=feature_cache)
    keys: list[tuple[str, float]] = []
    for action_key in _action_feature_keys(board, move):
        keys.append((f"action_pattern:{action_key}", 1.0))
    for key, value in sorted(before_features.items()):
        keys.append((f"before_terminal:{key}={_bucket(value)}", 0.25))
    for key, value in sorted(after_features.items()):
        if key in ACTION_AFTER_EXCLUDED_TERMINAL_FLAGS:
            continue
        keys.append((f"after_terminal:{key}={_bucket(value)}", 0.25))
    for key in sorted(before_features.keys() & after_features.keys()):
        if key in ACTION_AFTER_EXCLUDED_TERMINAL_FLAGS:
            continue
        keys.append((
            f"delta_terminal:{key}={_delta_bucket(after_features[key] - before_features[key])}",
            0.25,
        ))
    validate_learner_record([key for key, _scale in keys])
    return tuple(keys)


def _cached_terminal_feature_vector(
    board: chess.Board,
    *,
    hub: FeatureHub | None,
    feature_cache: dict[str, dict[str, float]] | None,
) -> dict[str, float]:
    if feature_cache is None:
        return extract_terminal_feature_vector(board, hub=hub)
    cache_key = board.fen()
    cached = feature_cache.get(cache_key)
    if cached is None:
        cached = extract_terminal_feature_vector(board, hub=hub)
        feature_cache[cache_key] = cached
    return cached


def action_ranker_behavior_audit() -> dict[str, Any]:
    """Static audit of current behavior-changing ActionRanker usage."""

    return {
        "status": "ActionRanker remains useful as diagnostic scaffolding, not the TG26h primary learner",
        "behavior_changing_paths": [
            {
                "path": "src/recon_lite_chess/autogrowth/foundation_curriculum.py",
                "symbols": [
                    "ActionRanker.choose",
                    "_evaluate_mate_in_one",
                    "_evaluate_mate_in_two",
                ],
                "classification": "behavior-changing synchronous ranker in TG25/TG26 foundation path",
            },
            {
                "path": "src/recon_lite_chess/autogrowth/edge_fence_curriculum.py",
                "symbols": [
                    "_choose_repaired_stage_move",
                    "_score_after_black_reply",
                    "_mate2_handoff_converts",
                ],
                "classification": "behavior-changing or deep-scoring scaffold for edge/fence curriculum validation",
            },
            {
                "path": "src/recon_lite_chess/autogrowth/persisted_pool_validation.py",
                "symbols": ["_evaluate_pool", "_build_pool"],
                "classification": "pool scheduling/evaluation scaffold that depends on trained ranker weights",
            },
        ],
        "tg26h_change": (
            "Mate_In_1/Mate_In_2 reproduction now has a separate terminal-native "
            "path with graph-visible StemCellTerminal state; ActionRanker is reported "
            "as a comparison baseline."
        ),
    }


def feature_substrate_coverage_sample(sample_fen: str) -> dict[str, Any]:
    board = chess.Board(sample_fen)
    hub = create_default_hub()
    hub.compute_all(board, force=True)
    current_features = sorted(extract_learner_features(board))
    terminal_features = sorted(extract_terminal_feature_vector(board, hub=hub))
    hub_features = sorted(hub.list_features())
    krk_features = KRKFeatures.feature_names()
    requested = {
        "black_king_edge_distance": {
            "current_autogrowth": "black_king_nearest_edge_distance" in current_features,
            "feature_hub": "enemy_king_at_edge" in hub_features,
            "older_krk_features": "enemy_king_edge_distance" in krk_features,
            "tg26h_terminal": "black_king_nearest_edge_distance" in terminal_features,
        },
        "delta_edge_distance": {
            "current_autogrowth": "available in post-move action/delta scoring, not a board sensor",
            "feature_hub": False,
            "older_krk_features": False,
            "tg26h_terminal": "delta_terminal:black_king_nearest_edge_distance" in " ".join(
                key for key, _scale in terminal_action_feature_keys(board, next(iter(board.legal_moves)), hub=hub)
            ),
        },
        "white_king_black_king_distance": {
            "current_autogrowth": "white_king_to_black_king_distance" in current_features,
            "feature_hub": False,
            "older_krk_features": "king_distance" in krk_features,
            "tg26h_terminal": "white_king_to_black_king_distance" in terminal_features,
        },
        "king_file_rank_deltas": {
            "current_autogrowth": False,
            "feature_hub": "enemy_king_file" in hub_features and "enemy_king_rank" in hub_features,
            "older_krk_features": False,
            "tg26h_terminal": {
                "king_file_delta",
                "king_rank_delta",
                "king_file_delta_abs",
                "king_rank_delta_abs",
            }.issubset(terminal_features),
        },
        "same_file_rank_and_opposition": {
            "current_autogrowth": False,
            "feature_hub": "opposition_status" in hub_features,
            "older_krk_features": "opposition_status" in krk_features,
            "tg26h_terminal": {
                "king_same_file",
                "king_same_rank",
                "direct_file_opposition",
                "direct_rank_opposition",
                "diagonal_opposition",
                "distant_opposition_parity",
                "feature_hub_opposition_status",
            }.issubset(terminal_features),
        },
        "knight_distance": {
            "current_autogrowth": False,
            "feature_hub": False,
            "older_krk_features": False,
            "tg26h_terminal": "king_knight_distance_like" in terminal_features,
        },
        "side_to_move_tempo": {
            "current_autogrowth": "side_white_to_move" in current_features,
            "feature_hub": "tempo_advantage" in hub_features,
            "older_krk_features": "side_to_move" in krk_features,
            "tg26h_terminal": {"side_white_to_move", "halfmove_clock_bucket"}.issubset(terminal_features),
        },
        "rook_safety": {
            "current_autogrowth": "rook_attacked_by_black" in current_features,
            "feature_hub": False,
            "older_krk_features": "rook_safe" in krk_features,
            "tg26h_terminal": {"rook_safe", "rook_attacked_by_black"}.issubset(terminal_features),
        },
        "confinement_preservation": {
            "current_autogrowth": "present in TG26/TG26g stage scoring, not core learner feature vector",
            "feature_hub": "enemy_king_mobility" in hub_features,
            "older_krk_features": {
                "box_area",
                "box_min_side",
                "rook_fence_distance",
            }.issubset(set(krk_features)),
            "tg26h_terminal": {
                "confinement_file_span",
                "confinement_rank_span",
                "confinement_area",
            }.issubset(terminal_features),
        },
        "black_reply_mobility": {
            "current_autogrowth": "black_reply_mobility" in current_features,
            "feature_hub": "enemy_king_mobility" in hub_features,
            "older_krk_features": False,
            "tg26h_terminal": "black_reply_mobility" in terminal_features,
        },
        "affordance_and_handoff_confidence": {
            "current_autogrowth": "handoff confidence is trainer-side diagnostics in TG26d-g",
            "feature_hub": "affordance_krk" in hub_features,
            "older_krk_features": "can_mate_now" in krk_features,
            "tg26h_terminal": "not learner-visible in this foundation checkpoint",
        },
    }
    return {
        "sample_fen": sample_fen,
        "current_autogrowth_feature_count": len(current_features),
        "feature_hub_feature_count": len(hub_features),
        "older_krk_feature_count": len(krk_features),
        "tg26h_terminal_feature_count": len(terminal_features),
        "safe_feature_hub_names_used_by_tg26h": list(SAFE_FEATURE_HUB_NAMES),
        "requested_feature_availability": requested,
        "learner_firewall": {
            "validated_terminal_features": True,
            "terminal_after_action_excludes_is_checkmate": True,
            "stage_schedule_labels_learner_visible": False,
            "forbidden_terms_checked_by": "src/recon_lite_chess/autogrowth/features.py::validate_learner_record",
        },
    }


def _run_action_ranker_baseline(
    *,
    config: TerminalSubstrateConfig,
    mate1_train: tuple[str, ...],
    mate1_heldout: tuple[str, ...],
    mate1_mirror: tuple[str, ...],
) -> dict[str, Any]:
    mate1_ranker = ActionRanker.create(eta_m3=config.eta_m3)
    mate1_pre = _evaluate_mate_in_one(
        mate1_heldout,
        ranker=ActionRanker.create(eta_m3=config.eta_m3),
        max_samples=config.max_samples,
    )
    mate1_train_metrics = _train_mate_in_one(mate1_train, ranker=mate1_ranker)
    mate1_heldout_metrics = _evaluate_mate_in_one(mate1_heldout, ranker=mate1_ranker, max_samples=config.max_samples)
    mate1_mirror_metrics = _evaluate_mate_in_one(mate1_mirror, ranker=mate1_ranker, max_samples=config.max_samples)
    mate1_pass = mate1_heldout_metrics["accuracy"] >= config.mate1_pass_threshold
    mate2_metrics = {
        "enabled": False,
        "reason": "disabled_or_mate1_not_passed",
        "dataset": {"train_count": 0, "heldout_count": 0},
    }
    mate2_ranker: ActionRanker | None = None
    if config.mate2_enabled and mate1_pass:
        mate2_train = tuple(_generate_forced_mate_in_two_positions(
            count=config.mate2_train_count,
            seed=config.seed + 2,
            max_attempts=config.max_generation_attempts,
        ))
        mate2_heldout = tuple(_generate_forced_mate_in_two_positions(
            count=config.mate2_heldout_count,
            seed=config.seed + 3,
            excluded=set(mate2_train),
            max_attempts=config.max_generation_attempts,
        ))
        mate2_ranker = ActionRanker.create(eta_m3=config.eta_m3)
        train = _train_mate_in_two(mate2_train, first_ranker=mate2_ranker, mate_ranker=mate1_ranker)
        heldout = _evaluate_mate_in_two(
            mate2_heldout,
            first_ranker=mate2_ranker,
            mate_ranker=mate1_ranker,
            max_samples=config.max_samples,
        )
        mate2_metrics = {
            "enabled": True,
            "dataset": {"train_count": len(mate2_train), "heldout_count": len(mate2_heldout)},
            "train_fens": mate2_train,
            "heldout_fens": mate2_heldout,
            "training": train,
            "heldout": heldout,
            "m4_consolidation_event_count": int(
                heldout["conversion_rate"] >= config.mate2_pass_threshold
                and mate2_ranker.m3_update_count > 0
            ),
        }
    return {
        "status": "diagnostic_baseline_scaffolding",
        "mate1": {
            "pre_training_heldout": mate1_pre,
            "training": mate1_train_metrics,
            "heldout": mate1_heldout_metrics,
            "mirror_generalization": mate1_mirror_metrics,
            "m3_update_count": mate1_ranker.m3_update_count,
            "m4_consolidation_event_count": int(mate1_pass and mate1_ranker.m3_update_count > 0),
        },
        "mate2": mate2_metrics,
        "ranker": mate1_ranker.to_dict(max_nodes=12),
        "mate2_first_ranker": None if mate2_ranker is None else mate2_ranker.to_dict(max_nodes=12),
    }


def _run_terminal_native(
    *,
    config: TerminalSubstrateConfig,
    mate1_train: tuple[str, ...],
    mate1_heldout: tuple[str, ...],
    mate1_mirror: tuple[str, ...],
) -> dict[str, Any]:
    mate1_learner = TerminalAffordanceLearner.create(
        eta_m3=config.eta_m3,
        rich_feature_credit_scale=config.rich_feature_credit_scale,
    )
    mate1_pre = _evaluate_terminal_mate_in_one(
        mate1_heldout,
        learner=TerminalAffordanceLearner.create(
            eta_m3=config.eta_m3,
            rich_feature_credit_scale=config.rich_feature_credit_scale,
        ),
        max_samples=config.max_samples,
    )
    mate1_train_metrics = _train_terminal_mate_in_one(mate1_train, learner=mate1_learner)
    mate1_heldout_metrics = _evaluate_terminal_mate_in_one(
        mate1_heldout,
        learner=mate1_learner,
        max_samples=config.max_samples,
    )
    mate1_mirror_metrics = _evaluate_terminal_mate_in_one(
        mate1_mirror,
        learner=mate1_learner,
        max_samples=config.max_samples,
    )
    mate1_pass = mate1_heldout_metrics["accuracy"] >= config.mate1_pass_threshold
    mate2_metrics: dict[str, Any] = {
        "enabled": False,
        "reason": "disabled_or_mate1_not_passed",
        "dataset": {"train_count": 0, "heldout_count": 0},
        "m4_consolidation_event_count": 0,
    }
    mate2_learner: TerminalAffordanceLearner | None = None
    if config.mate2_enabled and mate1_pass:
        mate2_train = tuple(_generate_forced_mate_in_two_positions(
            count=config.mate2_train_count,
            seed=config.seed + 2,
            max_attempts=config.max_generation_attempts,
        ))
        mate2_heldout = tuple(_generate_forced_mate_in_two_positions(
            count=config.mate2_heldout_count,
            seed=config.seed + 3,
            excluded=set(mate2_train),
            max_attempts=config.max_generation_attempts,
        ))
        mate2_learner = TerminalAffordanceLearner.create(
            eta_m3=config.eta_m3,
            rich_feature_credit_scale=config.rich_feature_credit_scale,
        )
        train = _train_terminal_mate_in_two(
            mate2_train,
            first_learner=mate2_learner,
            mate_learner=mate1_learner,
        )
        heldout = _evaluate_terminal_mate_in_two(
            mate2_heldout,
            first_learner=mate2_learner,
            mate_learner=mate1_learner,
            max_samples=config.max_samples,
        )
        mate2_metrics = {
            "enabled": True,
            "dataset": {"train_count": len(mate2_train), "heldout_count": len(mate2_heldout)},
            "train_fens": mate2_train,
            "heldout_fens": mate2_heldout,
            "training": train,
            "heldout": heldout,
            "m4_consolidation_event_count": int(
                heldout["conversion_rate"] >= config.mate2_pass_threshold
                and mate2_learner.m3_update_count > 0
            ),
        }
    return {
        "status": "primary_terminal_native_checkpoint",
        "mate1": {
            "pre_training_heldout": mate1_pre,
            "training": mate1_train_metrics,
            "heldout": mate1_heldout_metrics,
            "mirror_generalization": mate1_mirror_metrics,
            "m3_update_count": mate1_learner.m3_update_count,
            "m4_consolidation_event_count": int(mate1_pass and mate1_learner.m3_update_count > 0),
        },
        "mate2": mate2_metrics,
        "terminal_substrate": mate1_learner.to_dict(max_terminals=12),
        "mate2_first_terminal_substrate": None if mate2_learner is None else mate2_learner.to_dict(max_terminals=12),
        "_mate1_learner": mate1_learner,
        "_mate2_first_learner": mate2_learner,
    }


def _strip_runtime_learners(payload: dict[str, Any]) -> dict[str, Any]:
    stripped = dict(payload)
    stripped.pop("_mate1_learner", None)
    stripped.pop("_mate2_first_learner", None)
    return stripped


def _train_terminal_mate_in_one(
    fens: Iterable[str],
    *,
    learner: TerminalAffordanceLearner,
) -> dict[str, Any]:
    fen_list = tuple(fens)
    totals = {"positive": 0, "negative": 0, "neutral": 0}
    for fen in fen_list:
        board = chess.Board(fen)
        positives = {move.uci() for move in _mate_moves(board)}
        updates = learner.train_position(board, positive_moves=positives)
        for key in totals:
            totals[key] += updates[key]
    return {
        "position_count": len(fen_list),
        "positive_updates": totals["positive"],
        "negative_updates": totals["negative"],
        "neutral_updates": totals["neutral"],
        "m3_update_count": learner.m3_update_count,
        "terminal_count": len(learner.terminals),
    }


def _train_terminal_mate_in_two(
    fens: Iterable[str],
    *,
    first_learner: TerminalAffordanceLearner,
    mate_learner: TerminalAffordanceLearner,
) -> dict[str, Any]:
    fen_list = tuple(fens)
    first_totals = {"positive": 0, "negative": 0, "neutral": 0}
    second_updates = 0
    for fen in fen_list:
        board = chess.Board(fen)
        forced = {move.uci() for move in _forced_mate_in_two_first_moves(board)}
        updates = first_learner.train_position(board, positive_moves=forced)
        for key in first_totals:
            first_totals[key] += updates[key]
        for first in _forced_mate_in_two_first_moves(board):
            after_first = board.copy(stack=False)
            after_first.push(first)
            for reply in sorted(after_first.legal_moves, key=lambda item: item.uci()):
                before_mate = after_first.copy(stack=False)
                before_mate.push(reply)
                positives = {move.uci() for move in _mate_moves(before_mate)}
                before = mate_learner.m3_update_count
                mate_learner.train_position(before_mate, positive_moves=positives)
                second_updates += mate_learner.m3_update_count - before
    return {
        "position_count": len(fen_list),
        "first_move_positive_updates": first_totals["positive"],
        "first_move_negative_updates": first_totals["negative"],
        "first_learner_m3_update_count": first_learner.m3_update_count,
        "second_mate_learner_extra_m3_updates": second_updates,
        "first_terminal_count": len(first_learner.terminals),
        "mate_terminal_count": len(mate_learner.terminals),
    }


def _evaluate_terminal_mate_in_one(
    fens: Iterable[str],
    *,
    learner: TerminalAffordanceLearner,
    max_samples: int,
) -> dict[str, Any]:
    fen_list = tuple(fens)
    rows = []
    correct = 0
    legal_moves = 0
    matched_positions = 0
    wrong_actions = 0
    suppressed_wrong_actions = 0
    active_counts: list[int] = []
    for fen in fen_list:
        board = chess.Board(fen)
        move = learner.choose(board)
        positives = {item.uci() for item in _mate_moves(board)}
        is_correct = move is not None and move.uci() in positives
        correct += int(is_correct)
        legal_moves += board.legal_moves.count()
        candidate_counts = [
            learner.active_terminal_count(board, legal)
            for legal in board.legal_moves
        ]
        matched_positions += int(any(count > 0 for count in candidate_counts))
        active_counts.extend(candidate_counts)
        for legal in board.legal_moves:
            if legal.uci() in positives:
                continue
            wrong_actions += 1
            suppressed_wrong_actions += int(learner.weight_for_move(board, legal) < 0.0)
        rows.append({
            "fen": fen,
            "selected": None if move is None else move.uci(),
            "correct_moves": sorted(positives),
            "correct": is_correct,
            "legal_move_count": board.legal_moves.count(),
            "selected_active_terminal_count": 0 if move is None else learner.active_terminal_count(board, move),
        })
    total = len(rows)
    validate_learner_record([
        {
            "selected": row["selected"],
            "correct": row["correct"],
            "selected_active_terminal_count": row["selected_active_terminal_count"],
        }
        for row in rows[:max_samples]
    ])
    return {
        "position_count": total,
        "correct_count": correct,
        "accuracy": 0.0 if total == 0 else correct / total,
        "top_ranked_action_correctness": 0.0 if total == 0 else correct / total,
        "avg_legal_move_count": 0.0 if total == 0 else round(legal_moves / total, 6),
        "candidate_activation_rate": 0.0 if total == 0 else matched_positions / total,
        "avg_active_terminal_count_per_action": (
            0.0 if not active_counts else round(sum(active_counts) / len(active_counts), 6)
        ),
        "wrong_action_suppression_rate": (
            0.0 if wrong_actions == 0 else suppressed_wrong_actions / wrong_actions
        ),
        "wrong_action_suppressed_count": suppressed_wrong_actions,
        "wrong_action_available_count": wrong_actions,
        "wrong_action_count": total - correct,
        "samples": rows[:max_samples],
    }


def _evaluate_terminal_mate_in_two(
    fens: Iterable[str],
    *,
    first_learner: TerminalAffordanceLearner,
    mate_learner: TerminalAffordanceLearner,
    max_samples: int,
) -> dict[str, Any]:
    fen_list = tuple(fens)
    rows = []
    converted = 0
    first_success = 0
    chain_steps = 0
    replied_mated = 0
    replied_total = 0
    for fen in fen_list:
        board = chess.Board(fen)
        forced = {move.uci() for move in _forced_mate_in_two_first_moves(board)}
        first = first_learner.choose(board)
        first_ok = first is not None and first.uci() in forced
        first_success += int(first_ok)
        all_replies_mated = False
        reply_rows = []
        if first is not None:
            after_first = board.copy(stack=False)
            after_first.push(first)
            all_replies_mated = True
            for reply in sorted(after_first.legal_moves, key=lambda item: item.uci()):
                before_mate = after_first.copy(stack=False)
                before_mate.push(reply)
                mate_move = mate_learner.choose(before_mate)
                mates = {move.uci() for move in _mate_moves(before_mate)}
                ok = mate_move is not None and mate_move.uci() in mates
                chain_steps += 1
                replied_total += 1
                replied_mated += int(ok)
                all_replies_mated = all_replies_mated and ok
                reply_rows.append({
                    "black_reply": reply.uci(),
                    "selected_mate": None if mate_move is None else mate_move.uci(),
                    "correct_mates": sorted(mates),
                    "mated": ok,
                })
        converted += int(first_ok and all_replies_mated)
        rows.append({
            "fen": fen,
            "selected_first": None if first is None else first.uci(),
            "forced_first_moves": sorted(forced),
            "first_move_success": first_ok,
            "all_replies_mated": all_replies_mated,
            "reply_checks": reply_rows[:8],
        })
    total = len(rows)
    return {
        "position_count": total,
        "first_move_success_count": first_success,
        "first_move_success_rate": 0.0 if total == 0 else first_success / total,
        "conversion_count": converted,
        "conversion_rate": 0.0 if total == 0 else converted / total,
        "forced_mate_reply_coverage": 0.0 if replied_total == 0 else replied_mated / replied_total,
        "chain_request_count": total,
        "chain_step_count": chain_steps,
        "chain_completion_count": converted,
        "wrong_first_move_count": total - first_success,
        "samples": rows[:max_samples],
    }


def _king_geometry_features(board: chess.Board) -> dict[str, float]:
    wk = board.king(chess.WHITE)
    bk = board.king(chess.BLACK)
    rook = _white_rook_square(board)
    if wk is None or bk is None:
        return {
            "king_file_delta": 0.0,
            "king_rank_delta": 0.0,
            "king_file_delta_abs": 8.0,
            "king_rank_delta_abs": 8.0,
            "king_same_file": 0.0,
            "king_same_rank": 0.0,
            "king_same_diagonal": 0.0,
            "direct_file_opposition": 0.0,
            "direct_rank_opposition": 0.0,
            "diagonal_opposition": 0.0,
            "distant_opposition_parity": 0.0,
            "king_knight_distance_like": 0.0,
            "halfmove_clock_bucket": min(10.0, float(board.halfmove_clock)),
            "rook_safe": 0.0,
            "rook_same_file_as_black_king": 0.0,
            "rook_same_rank_as_black_king": 0.0,
            "rook_to_black_king_file_delta_abs": 8.0,
            "rook_to_black_king_rank_delta_abs": 8.0,
            "confinement_file_span": 8.0,
            "confinement_rank_span": 8.0,
            "confinement_area": 64.0,
        }
    wk_file, wk_rank = chess.square_file(wk), chess.square_rank(wk)
    bk_file, bk_rank = chess.square_file(bk), chess.square_rank(bk)
    file_delta = wk_file - bk_file
    rank_delta = wk_rank - bk_rank
    file_abs = abs(file_delta)
    rank_abs = abs(rank_delta)
    rook_file = -1 if rook is None else chess.square_file(rook)
    rook_rank = -1 if rook is None else chess.square_rank(rook)
    confinement_file_span, confinement_rank_span = _confinement_spans(board, rook, bk)
    payload = {
        "king_file_delta": float(file_delta),
        "king_rank_delta": float(rank_delta),
        "king_file_delta_abs": float(file_abs),
        "king_rank_delta_abs": float(rank_abs),
        "king_same_file": 1.0 if file_abs == 0 else 0.0,
        "king_same_rank": 1.0 if rank_abs == 0 else 0.0,
        "king_same_diagonal": 1.0 if file_abs == rank_abs else 0.0,
        "direct_file_opposition": 1.0 if file_abs == 0 and rank_abs == 2 else 0.0,
        "direct_rank_opposition": 1.0 if rank_abs == 0 and file_abs == 2 else 0.0,
        "diagonal_opposition": 1.0 if file_abs == rank_abs == 2 else 0.0,
        "distant_opposition_parity": 1.0
        if (
            (file_abs == 0 and rank_abs > 2 and rank_abs % 2 == 0)
            or (rank_abs == 0 and file_abs > 2 and file_abs % 2 == 0)
            or (file_abs == rank_abs and file_abs > 2 and file_abs % 2 == 0)
        )
        else 0.0,
        "king_knight_distance_like": 1.0 if sorted((file_abs, rank_abs)) == [1, 2] else 0.0,
        "halfmove_clock_bucket": min(10.0, float(board.halfmove_clock)),
        "rook_safe": 0.0 if _rook_missing_or_attacked(board) else 1.0,
        "rook_same_file_as_black_king": 1.0 if rook_file == bk_file else 0.0,
        "rook_same_rank_as_black_king": 1.0 if rook_rank == bk_rank else 0.0,
        "rook_to_black_king_file_delta_abs": 8.0 if rook is None else float(abs(rook_file - bk_file)),
        "rook_to_black_king_rank_delta_abs": 8.0 if rook is None else float(abs(rook_rank - bk_rank)),
        "confinement_file_span": float(confinement_file_span),
        "confinement_rank_span": float(confinement_rank_span),
        "confinement_area": float(confinement_file_span * confinement_rank_span),
    }
    validate_learner_record(payload)
    return payload


def _confinement_spans(board: chess.Board, rook: int | None, black_king: int) -> tuple[int, int]:
    if rook is None:
        return 8, 8
    rook_file, rook_rank = chess.square_file(rook), chess.square_rank(rook)
    bk_file, bk_rank = chess.square_file(black_king), chess.square_rank(black_king)
    file_span = 8
    rank_span = 8
    if rook_file < bk_file:
        file_span = 7 - rook_file
    elif rook_file > bk_file:
        file_span = rook_file
    if rook_rank < bk_rank:
        rank_span = 7 - rook_rank
    elif rook_rank > bk_rank:
        rank_span = rook_rank
    return max(1, file_span), max(1, rank_span)


def _white_rook_square(board: chess.Board) -> int | None:
    rooks = sorted(board.pieces(chess.ROOK, chess.WHITE))
    return rooks[0] if rooks else None


def _bucket(value: float) -> str:
    numeric = float(value)
    if abs(numeric - round(numeric)) < 1e-9:
        return str(int(round(numeric)))
    return f"{round(numeric * 4.0) / 4.0:.2f}"


def _delta_bucket(value: float) -> str:
    if value > 0.25:
        return "positive"
    if value < -0.25:
        return "negative"
    return "zero"


def _decision(
    *,
    config: TerminalSubstrateConfig,
    terminal_native: dict[str, Any],
) -> dict[str, Any]:
    mate1_passed = terminal_native["mate1"]["heldout"]["accuracy"] >= config.mate1_pass_threshold
    mate2_enabled = bool(terminal_native["mate2"].get("enabled"))
    mate2_passed = bool(
        mate2_enabled
        and terminal_native["mate2"]["heldout"]["conversion_rate"] >= config.mate2_pass_threshold
    )
    return {
        "status": (
            "tg26h_terminal_foundation_mate1_mate2_passed"
            if mate1_passed and mate2_passed
            else "tg26h_terminal_foundation_mate1_passed"
            if mate1_passed
            else "tg26h_terminal_foundation_failed"
        ),
        "mate1_passed": mate1_passed,
        "mate1_heldout_accuracy": terminal_native["mate1"]["heldout"]["accuracy"],
        "mate1_mirror_accuracy": terminal_native["mate1"]["mirror_generalization"]["accuracy"],
        "mate1_m3_update_count": terminal_native["mate1"]["m3_update_count"],
        "mate1_m4_consolidation_event_count": terminal_native["mate1"]["m4_consolidation_event_count"],
        "mate2_enabled": mate2_enabled,
        "mate2_passed": mate2_passed,
        "mate2_conversion_rate": None
        if not mate2_enabled
        else terminal_native["mate2"]["heldout"]["conversion_rate"],
        "mate2_m4_consolidation_event_count": int(
            terminal_native["mate2"].get("m4_consolidation_event_count", 0)
        ),
        "action_ranker_claim_status": "diagnostic_baseline_only",
        "terminal_native_ready_for_edge_fence_rerun": mate1_passed and mate2_passed,
        "fence_m4_consolidation_allowed": False,
        "broad_krk_allowed": False,
        "ecological_spawning_allowed": False,
        "schedule_labels_learner_visible": False,
        "direct_provider_override": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "next_recommended_checkpoint": (
            "Rerun edge/fence validation with the terminal-native foundation path and keep "
            "ActionRanker only as an ablation baseline."
            if mate1_passed and mate2_passed
            else "Repair terminal-native Mate_In_1/Mate_In_2 before returning to edge/fence."
        ),
    }
