import gzip
import json
from pathlib import Path

from recon_lite_chess.autogrowth import (
    TG48a2SameSideEpisodeTrainingConfig,
    run_tg48a2_same_side_episode_training,
)
from recon_lite_chess.autogrowth.tg48a2_same_side_episode_training import (
    _credit_assignments,
    _episode_success,
    _trajectory_reward,
)
from recon_lite_chess.autogrowth.tg48a2_same_side_microstage import FORBIDDEN_MICROSTAGE_TERMS


def test_training_strategy_note_records_episode_first_policy() -> None:
    note = Path("docs/autogrowth/TRAINING_STRATEGY_NOTE.md")
    assert note.exists()
    text = note.read_text(encoding="utf-8")
    for phrase in (
        "Episode-First Curriculum After Mate-in-2",
        "Mate-in-1 and Mate-in-2 are degenerate exceptions",
        "Multi-Ply Curriculum Requires Trajectory Reward",
        "move-local scoring may still exist as diagnostics",
        "eligibility traces or discounted credit",
        "Trainer-side playout",
        "must not become a hidden runtime selector",
        "TG48a2 Same-Side Rook-Danger",
        "TG48b and TG48c",
    ):
        assert phrase in text


def test_episode_reward_keeps_partial_and_false_basin_out_of_success() -> None:
    partial_channels, partial_reward = _trajectory_reward("partial_only_near_basin", {})
    false_channels, false_reward = _trajectory_reward("graph_positive_false_basin", {})
    unsafe_channels, unsafe_reward = _trajectory_reward("rook_blunder", {})

    assert partial_reward < 0
    assert false_reward < 0
    assert unsafe_reward < 0
    assert partial_channels["false_basin"] < 0
    assert false_channels["false_basin"] < 0
    assert unsafe_channels["terminal_failure"] < 0
    assert _episode_success("partial_only_near_basin") is False
    assert _episode_success("graph_positive_false_basin") is False
    assert _episode_success("rook_blunder") is False
    assert _episode_success("safer_opposed_or_killbox_geometry") is True
    assert _episode_success("validated_mate1_entry") is True


def test_episode_credit_assigns_discounted_trace_across_white_moves() -> None:
    assignments = _credit_assignments(
        terminal_activations_by_white_ply=[
            ["micro_action:piece_type=4"],
            ["micro_delta:axis_pattern=improved"],
            ["micro_guard:rook_risk_after=0"],
        ],
        reward_channels={
            "foundation_handoff": 0.0,
            "lateral_escape": 3.0,
            "geometry_transition": 5.0,
            "safety": 1.0,
            "false_basin": 0.0,
            "terminal_failure": 0.0,
        },
        trajectory_reward=9.0,
        gamma=0.75,
    )

    assert len(assignments) == 3
    assert assignments[0]["discount"] == 0.5625
    assert assignments[1]["discount"] == 0.75
    assert assignments[2]["discount"] == 1.0
    assert assignments[2]["discounted_reward"] > assignments[1]["discounted_reward"] > assignments[0]["discounted_reward"]


def test_tg48a2_episode_tiny_run_writes_artifact_and_preserves_purity(tmp_path: Path) -> None:
    output_dir = tmp_path / "tg48a2_episode"
    cfg = TG48a2SameSideEpisodeTrainingConfig(
        output_dir=str(output_dir),
        output_path=str(output_dir / "krk_tg48a2_same_side_episode_training.json"),
        markdown_path=str(output_dir / "krk_tg48a2_same_side_episode_training.md"),
        train_episode_trace_path=str(output_dir / "pools" / "train_episode_traces.jsonl.gz"),
        eval_episode_trace_path=str(output_dir / "pools" / "eval_episode_traces.jsonl.gz"),
        failure_episode_pool_path=str(output_dir / "pools" / "failure_episode_pool.jsonl.gz"),
        promoted_terminal_audit_path=str(output_dir / "pools" / "promoted_terminal_audit.jsonl.gz"),
        reward_channel_audit_path=str(output_dir / "pools" / "reward_channel_audit.jsonl.gz"),
        board_sample_path=str(output_dir / "pools" / "board_samples.md"),
        train_count=4,
        heldout_count=3,
        regression_count=2,
        decoy_count=2,
        hard_decoy_count=2,
        max_generation_attempts=80_000,
        max_white_moves=3,
        max_total_plies=6,
        m4_min_positive_support=1,
        m4_min_negative_support=1,
    )

    result = run_tg48a2_same_side_episode_training(config=cfg)
    payload = json.loads(Path(cfg.output_path).read_text(encoding="utf-8"))

    assert result.decision["checkpoint_pass"] is True
    assert payload["provenance"]["primary_training_unit"] == "episode_trajectory"
    assert payload["provenance"]["move_local_reward_primary"] is False
    assert payload["training_strategy"]["episode_first_after_mate2"] is True
    assert payload["training_strategy"]["trainer_side_playout_not_runtime_selector"] is True
    assert payload["decision"]["parent_foundation_weight_delta_during_stage"] == 0
    assert payload["decision"]["parent_foundation_m3_delta_during_stage"] == 0
    assert payload["decision"]["parent_foundation_m4_delta_during_stage"] == 0
    assert payload["decision"]["runtime_tablebase_or_dtm_move_source"] is False
    assert payload["decision"]["action_ranker_used_for_runtime"] is False
    assert payload["decision"]["python_final_selector_used"] is False
    assert payload["decision"]["direct_provider_override"] is False
    assert payload["decision"]["same_side_labels_learner_visible"] is False

    for path in (
        cfg.train_episode_trace_path,
        cfg.eval_episode_trace_path,
        cfg.failure_episode_pool_path,
        cfg.promoted_terminal_audit_path,
        cfg.reward_channel_audit_path,
        cfg.board_sample_path,
    ):
        assert Path(path).exists()

    with gzip.open(cfg.train_episode_trace_path, "rt", encoding="utf-8") as handle:
        train_traces = [json.loads(line) for line in handle]
    assert train_traces
    for trace in train_traces:
        assert trace["terminal_activations_by_white_ply"]
        assert len(trace["terminal_activations_by_white_ply"]) == len(trace["credit_assignments"])
        assert all("reply_total" in item for item in trace["legal_reply_coverage"])
        assert trace["trainer_side_playout_used_for_runtime_selection"] is False

    with gzip.open(cfg.eval_episode_trace_path, "rt", encoding="utf-8") as handle:
        eval_traces = [json.loads(line) for line in handle]
    assert all(not trace["episode_success"] for trace in eval_traces if trace["graph_positive_false_basin"])
    assert all(not trace["episode_success"] for trace in eval_traces if trace["partial_only_near_basin"])
    assert all(
        not (trace["endpoint_validated_mate1"] or trace["endpoint_validated_mate2"])
        or trace["endpoint_validated_entry"]
        for trace in eval_traces
    )

    learner_visible = {
        "terminal_keys": [
            row["terminal_key"]
            for row in payload["m4_audit"]["candidate_rows"]
        ],
        "train_terminal_activations": [
            trace["terminal_activations_by_white_ply"]
            for trace in train_traces
        ],
    }
    lowered = json.dumps(learner_visible).lower()
    for term in FORBIDDEN_MICROSTAGE_TERMS:
        assert term not in lowered

    assert "parent_episode_success_rate" in payload["decision"]
    assert "same_side_subskill_success_rate" in payload["decision"]
    assert "promoted_lateral_escape_affordance_count" in payload["decision"]
    assert "promoted_geometry_transition_affordance_count" in payload["decision"]
    assert "promoted_foundation_handoff_affordance_count" in payload["decision"]
    assert "promoted_veto_count" in payload["decision"]
