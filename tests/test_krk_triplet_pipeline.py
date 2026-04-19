import argparse
import importlib.util
import pickle
import sys
from types import SimpleNamespace
from pathlib import Path


_pipeline = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "run_krk_triplet_pipeline",
        Path(__file__).resolve().parents[1] / "scripts" / "run_krk_triplet_pipeline.py",
    )
)
assert _pipeline.__spec__ is not None
assert _pipeline.__spec__.loader is not None
sys.modules["run_krk_triplet_pipeline"] = _pipeline
_pipeline.__spec__.loader.exec_module(_pipeline)


def test_krk_triplet_pipeline_plan_uses_fresh_paths(tmp_path):
    args = argparse.Namespace(
        output_dir=tmp_path / "run",
        stage0_cycles=1,
        stage1_cycles=2,
        load_learner=None,
        samples_per_cycle=3,
        stage0_eval_samples=4,
        stage1_eval_samples=5,
        seed=11,
        device="cpu",
        snapshot_every=1,
        min_mature_for_goals=6,
        feature_set="krk_rich_v1",
        max_curriculum_stage=3,
        landmark_cycles=4,
        allow_prune_foundation=False,
        adaptive_curriculum=True,
        eval_every=5,
        patience=3,
        min_cycles_per_stage=10,
        max_cycles_per_stage=80,
        adaptive_eval_samples=12,
        stage1_position_mode="hybrid",
        stage1_hybrid_random_ratio=0.5,
        stage1_eval_position_mode="random",
        stage1_eval_hybrid_random_ratio=0.5,
        stage0_balance_corners=True,
    )

    plan = _pipeline.build_plan(args)
    manifest = _pipeline.manifest_for(args, plan)

    assert plan.learner_path == tmp_path / "run" / "baseline" / "final_learner.pkl"
    assert plan.topology_path == tmp_path / "run" / "topology" / "krk_entry_topology.json"
    assert len(plan.commands) == 4
    assert "--load-learner" not in plan.commands[0]
    assert "--seed" in plan.commands[0]
    assert "--snapshot-every" in plan.commands[0]
    assert "--min-mature-for-goals" in plan.commands[0]
    assert "--feature-set" in plan.commands[0]
    assert "krk_rich_v1" in plan.commands[0]
    assert "--max-curriculum-stage" in plan.commands[0]
    assert "3" in plan.commands[0]
    assert "--landmark-cycles" in plan.commands[0]
    assert "4" in plan.commands[0]
    assert "--adaptive-curriculum" in plan.commands[0]
    assert "--eval-every" in plan.commands[0]
    assert "--adaptive-eval-samples" in plan.commands[0]
    assert "12" in plan.commands[0]
    assert "--stage1-position-mode" in plan.commands[0]
    assert "--position-mode" in plan.commands[3]
    assert manifest["formal_validation"]["validated"] is False
    assert manifest["training"]["stage0_cycles"] == 1
    assert manifest["training"]["min_mature_for_goals"] == 6
    assert manifest["training"]["feature_set"] == "krk_rich_v1"
    assert manifest["training"]["max_curriculum_stage"] == 3
    assert manifest["training"]["landmark_cycles"] == 4
    assert manifest["training"]["adaptive_curriculum"] is True
    assert manifest["training"]["adaptive_eval_samples"] == 12
    assert manifest["training"]["stage1_position_mode"] == "hybrid"
    assert manifest["evaluation"]["stage1_eval_position_mode"] == "random"
    assert manifest["evaluation"]["stage1_stage_filter"] == 1


def test_krk_triplet_pipeline_readiness_detects_empty_stage0(tmp_path):
    learner_path = tmp_path / "learner.pkl"
    learner = SimpleNamespace(sensors=[], actuators=[], goal_memories=[])
    with learner_path.open("wb") as fh:
        pickle.dump(learner, fh)

    readiness = _pipeline.learner_readiness(learner_path)

    assert readiness["ready"] is False
    assert readiness["mature_sensors"] == 0
    assert readiness["actuators"] == 0
    assert readiness["mate_in_1_goal_memories"] == 0


def test_krk_triplet_pipeline_plan_passes_hybrid_eval_ratio(tmp_path):
    args = argparse.Namespace(
        output_dir=tmp_path / "run",
        stage0_cycles=1,
        stage1_cycles=1,
        load_learner=None,
        samples_per_cycle=5,
        stage0_eval_samples=5,
        stage1_eval_samples=5,
        seed=11,
        device="cpu",
        snapshot_every=1,
        min_mature_for_goals=6,
        feature_set="legacy",
        max_curriculum_stage=1,
        landmark_cycles=10,
        allow_prune_foundation=False,
        adaptive_curriculum=False,
        eval_every=5,
        patience=3,
        min_cycles_per_stage=10,
        max_cycles_per_stage=80,
        adaptive_eval_samples=None,
        stage1_position_mode="mate_in_2",
        stage1_hybrid_random_ratio=0.5,
        stage1_eval_position_mode="hybrid",
        stage1_eval_hybrid_random_ratio=0.25,
        stage0_balance_corners=True,
    )

    plan = _pipeline.build_plan(args)

    assert "--position-mode" in plan.commands[3]
    assert "hybrid" in plan.commands[3]
    assert "--hybrid-random-ratio" in plan.commands[3]
    assert "0.25" in plan.commands[3]


def test_krk_triplet_pipeline_plan_passes_load_learner(tmp_path):
    learner_path = tmp_path / "stage1.pkl"
    args = argparse.Namespace(
        output_dir=tmp_path / "run",
        stage0_cycles=0,
        stage1_cycles=0,
        load_learner=learner_path,
        samples_per_cycle=5,
        stage0_eval_samples=5,
        stage1_eval_samples=5,
        seed=11,
        device="cpu",
        snapshot_every=1,
        min_mature_for_goals=6,
        feature_set="krk_rich_v1",
        max_curriculum_stage=2,
        landmark_cycles=10,
        allow_prune_foundation=False,
        adaptive_curriculum=True,
        eval_every=5,
        patience=3,
        min_cycles_per_stage=10,
        max_cycles_per_stage=80,
        adaptive_eval_samples=None,
        stage1_position_mode="mate_in_2",
        stage1_hybrid_random_ratio=0.5,
        stage1_eval_position_mode="mate_in_2",
        stage1_eval_hybrid_random_ratio=0.5,
        stage0_balance_corners=True,
    )

    plan = _pipeline.build_plan(args)
    manifest = _pipeline.manifest_for(args, plan)

    assert "--load-learner" in plan.commands[0]
    assert str(learner_path) in plan.commands[0]
    assert manifest["training"]["load_learner"] == str(learner_path)
