"""One-time promotion of the already validated, trusted M1 checkpoint.

Run with the immutable 12fa306c source on PYTHONPATH, never the moving worktree.
This is serialization and evidence packaging only: no training or evaluation.
The checkpoint hash is pinned before unpickling; output files are exclusive.
"""
import argparse
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
import pickle

CHECKPOINT_SHA256 = "ae8d5c2e64f6c14e98cca5440db9885e3bfde4e67e728e628838427889f99b96"
RUNTIME_SHA256 = "fa7ad67ce5176f144e51667bb46ff8712ff3d8ac3da24f41d24bc0ae021185bd"


def write_new(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(payload)
    return hashlib.sha256(payload).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--scope-completion", type=Path)
    args = parser.parse_args()
    evidence, root = args.evidence, args.repository
    checkpoint = evidence / "selective_m1_retention_seed61/checkpoint-000002048.pkl.gz"
    payload = checkpoint.read_bytes()
    if hashlib.sha256(payload).hexdigest() != CHECKPOINT_SHA256:
        raise ValueError("not the approved checkpoint")
    # Do not relabel a conversion performed under moving/new module code as
    # an original-source export merely because the stored manifest says so.
    try:
        from recon_lite_chess.experiments.selective_m1 import source_identity
        executing_source = source_identity()
    except (ImportError, OSError) as error:
        raise RuntimeError("export requires the complete immutable M1 source archive") from error
    if executing_source["code_sha256"] != RUNTIME_SHA256:
        raise RuntimeError("executing runtime does not match the checkpoint source identity")
    state = pickle.loads(gzip.decompress(payload))
    if (json.dumps(executing_source, sort_keys=True)
            != json.dumps(state.source, sort_keys=True)):
        raise RuntimeError("executing runtime does not match the checkpoint source identity")
    actor = state.organism
    assert actor.completed == 2048 and len(actor.conditions) == 12
    assert not actor.pending and actor.owner_pending is None
    actor.validate_ownership()
    actor.graph.validate_formal_pairs()
    artifact = gzip.compress(pickle.dumps(actor, protocol=5), mtime=0)
    target = root / "src/recon_lite_chess/checkpoints/selective_m1_seed61.pkl.gz"
    artifact_sha = write_new(target, artifact)
    receipts, sources = [], {}
    for split, filename in (
        ("train", "selective_m1_confirmation_seed61/training-evaluation.json"),
        ("development", "selective_m1_retention_seed61/development-000002048.json"),
        ("confirmation", "selective_m1_confirmation_seed61/fresh-evaluation.json"),
    ):
        raw = (evidence / filename).read_bytes()
        report = json.loads(raw)
        assert report["positions"] == report["mates"]
        sources[split] = {"path": filename, "sha256": hashlib.sha256(raw).hexdigest(),
                          "positions": report["positions"]}
        receipts.extend({"split": split, "fen": row["fen"], "action": row["action"]}
                        for row in report["rows"])
    assert len(receipts) == len({r["fen"] for r in receipts}) == 1384
    panel = gzip.compress(json.dumps(receipts, sort_keys=True).encode(), mtime=0)
    panel_sha = write_new(root / "tests/autogrowth/data/selective_m1/m1_validated_receipts.json.gz", panel)
    manifest = {
        "format": "selective-m1-actor.v1", "source_commit": "12fa306c",
        "original_checkpoint_sha256": CHECKPOINT_SHA256,
        "original_code_sha256": state.source["code_sha256"],
        "artifact_sha256": artifact_sha, "artifact_bytes": len(artifact),
        "python": state.source["python"], "chess": state.source["chess"],
        "seed": 61, "completed_actions": actor.completed,
        "topology": {"conditions": len(actor.conditions), "nodes": len(actor.graph.nodes),
                     "edges": len(actor.graph.edges), "definitions": len(actor.expression_ids)},
        "config": asdict(actor.config), "limits": asdict(actor.ownership_limits),
        "development": asdict(actor.development_config),
        "birth_search": asdict(actor.birth_search_config),
        "reclosure_enabled": actor.reclosure_enabled,
        "prospective_resource_cost": actor.prospective_resource_cost,
        "validation_sources": sources, "validation_panel_sha256": panel_sha,
        "scope": "1384 declared KRK M1 positions / 173 D4 orbits; not full legal KRK",
        "retention": "224/224 at all nine checks across 1024 additional ordinary actions",
        "conversion": "Actor only, no weight/topology/config/history changes; schedule omitted",
    }
    if args.scope_completion is not None:
        manifest["scope_completion"] = export_completion(args.scope_completion, root)
        manifest["scope"] = ("1512 legal White-to-move KRK mate-in-one positions / "
                             "189 D4 orbits; ordinary placement scope, no draw history")
    write_new(target.with_name("selective_m1_seed61.json"),
              (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode())
    print(json.dumps({"artifact_sha256": artifact_sha, "bytes": len(artifact),
                      "validation_panel_sha256": panel_sha}, indent=2))


def export_completion(evidence, root):
    """Package only the newly authorized 128-position completion receipts."""
    report = json.loads((evidence / "result.json").read_text())
    assert report["checkpoint_sha256"] == CHECKPOINT_SHA256
    assert report["positions"] == report["mates"] == 128 and not report["learning"]
    raw = (evidence / "receipts.jsonl").read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    assert len(rows) == 128 and all(r["reward"] == 1 for r in rows)
    receipts = [{"split": "scope_completion", "fen": r["fen"], "action": r["action"]}
                for r in rows]
    sha = write_new(root / "tests/autogrowth/data/selective_m1/m1_scope_completion_receipts.json.gz",
                    gzip.compress(json.dumps(receipts, sort_keys=True).encode(), mtime=0))
    return {"positions": 128, "mating_orbits": 16,
            "receipts_sha256": hashlib.sha256(raw).hexdigest(),
            "validation_panel_sha256": sha}


if __name__ == "__main__":
    main()
