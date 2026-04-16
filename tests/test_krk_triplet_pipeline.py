import argparse
import importlib.util
import sys
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
        samples_per_cycle=3,
        stage0_eval_samples=4,
        stage1_eval_samples=5,
        seed=11,
        device="cpu",
        stage0_balance_corners=True,
    )

    plan = _pipeline.build_plan(args)
    manifest = _pipeline.manifest_for(args, plan)

    assert plan.learner_path == tmp_path / "run" / "baseline" / "final_learner.pkl"
    assert plan.topology_path == tmp_path / "run" / "topology" / "krk_entry_topology.json"
    assert len(plan.commands) == 4
    assert "--load-learner" not in plan.commands[0]
    assert "--seed" in plan.commands[0]
    assert manifest["formal_validation"]["validated"] is False
    assert manifest["training"]["stage0_cycles"] == 1
    assert manifest["evaluation"]["stage1_stage_filter"] == 1
