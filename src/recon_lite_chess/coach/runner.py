"""Prepare exercises, train by playing, and evaluate in a separate process."""

import argparse
from dataclasses import asdict, dataclass, field
import gzip
import hashlib
import json
import os
from pathlib import Path
import pickle
import platform
import random
import signal
import time
import uuid

import chess
import numpy

from .exercise import play_mate_one
from .interface import Organism
from .pools import load_split, prepare


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def source_identity() -> dict:
    root = Path(__file__).resolve().parents[3]
    paths = []
    for subdir in ("libs/recon-lite/src", "src/recon_lite_hector",
                   "src/recon_lite_chess/autogrowth", "src/recon_lite_chess/coach"):
        paths.extend((root / subdir).rglob("*.py"))
    h = hashlib.sha256()
    for path in sorted(paths):
        h.update(path.relative_to(root).as_posix().encode())
        h.update(path.read_bytes())
    return {"code_sha256": h.hexdigest(), "python": platform.python_version_tuple()[:2],
            "chess": chess.__version__, "numpy": numpy.__version__,
            "pythonhashseed": os.environ.get("PYTHONHASHSEED", "unset")}


def _atomic_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


@dataclass
class RunState:
    organism: Organism
    pool_digest: str
    seed: int
    source: dict
    next_event: int = 0
    order: list[int] = field(default_factory=list)
    cursor: int = 0
    rng: random.Random = field(default_factory=random.Random)
    mates: int = 0
    real_moves: int = 0
    illegal: int = 0
    abstentions: int = 0

    def next_position(self, fens: tuple[str, ...]) -> str:
        if self.cursor >= len(self.order):
            self.order = list(range(len(fens)))
            self.rng.shuffle(self.order)
            self.cursor = 0
        fen = fens[self.order[self.cursor]]
        self.cursor += 1
        return fen

    def progress(self) -> dict:
        return {"attempts": self.next_event, "real_white_moves": self.real_moves,
                "checkmates": self.mates,
                "training_success_rate": self.mates / self.next_event if self.next_event else 0.0,
                "illegal_actions": self.illegal, "abstentions": self.abstentions,
                "seed": self.seed, "train_pool_sha256": self.pool_digest}


def save_checkpoint(state: RunState, directory: Path) -> Path:
    """Commit the opaque organism and coach schedule together at an episode boundary."""
    name = f"checkpoint-{state.next_event:09d}-{uuid.uuid4().hex[:8]}.pkl.gz"
    path = directory / name
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=1, mtime=0) as stream:
            pickle.dump(state, stream, protocol=pickle.HIGHEST_PROTOCOL)
        raw.flush()
        os.fsync(raw.fileno())
    temporary.replace(path)
    _atomic_json(directory / "latest.json", {
        "schema": "mate_one_coach_checkpoint.v1", "file": name,
        "sha256": _digest(path), "source": state.source, **state.progress(),
    })
    # Each name is immutable; latest.json never points at a partially written file.
    checkpoints = sorted(directory.glob("checkpoint-*.pkl.gz"), key=lambda p: p.stat().st_mtime_ns)
    for old in checkpoints[:-2]:
        if old != path:
            old.unlink()
    return path


def load_checkpoint(directory: Path) -> RunState:
    manifest = json.loads((directory / "latest.json").read_text())
    if manifest["schema"] != "mate_one_coach_checkpoint.v1":
        raise ValueError("unsupported checkpoint schema")
    if json.dumps(manifest["source"], sort_keys=True) != json.dumps(source_identity(), sort_keys=True):
        raise ValueError("learner code/runtime differs from checkpoint; use its original checkout/environment")
    name = manifest["file"]
    if Path(name).name != name:
        raise ValueError("checkpoint must be inside its run directory")
    path = directory / name
    if _digest(path) != manifest["sha256"]:
        raise ValueError("checkpoint transport hash mismatch")
    with gzip.open(path, "rb") as stream:
        state = pickle.load(stream)
    if (not isinstance(state, RunState) or state.next_event != manifest["attempts"]
            or state.pool_digest != manifest["train_pool_sha256"]
            or state.source != source_identity()):
        raise ValueError("checkpoint and continuation manifest disagree")
    return state


def _trim_uncommitted_trace(path: Path, next_event: int) -> None:
    if not path.exists():
        return
    temporary = path.with_suffix(".tmp")
    with path.open() as source, temporary.open("w") as target:
        for line in source:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                break  # An interrupted final write was never committed.
            if event["event_id"] < next_event:
                target.write(line)
    temporary.replace(path)


def train(args: argparse.Namespace) -> dict:
    from .native import NativeOrganism

    fens, digest = load_split(args.pool, "train")
    directory = args.run
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / "run.lock"
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise RuntimeError("run is locked; use separate directories on two computers. "
                           "After a crash, remove run.lock only once the old process has stopped.") from exc
    old_handlers = {}
    stopping = [False]
    started = time.monotonic()
    try:
        if (directory / "final_test_opened.json").exists():
            raise RuntimeError("this run opened its final test and is frozen for further training")
        if args.resume:
            state = load_checkpoint(directory)
            if state.pool_digest != digest or state.seed != args.seed:
                raise ValueError("resume requires the original training pool and seed")
        else:
            if (directory / "latest.json").exists() or (directory / "moves.jsonl").exists():
                raise FileExistsError("run already exists; use --resume or a new directory")
            state = RunState(NativeOrganism(), digest, args.seed, source_identity(),
                             rng=random.Random(args.seed))
            save_checkpoint(state, directory)  # Durable empty-learned-state start.
        trace_path = directory / "moves.jsonl"
        _trim_uncommitted_trace(trace_path, state.next_event)
        # Complete an in-flight action/feedback transaction before saving. Raising
        # KeyboardInterrupt inside a weight update would make a partial snapshot.
        for sig in (signal.SIGINT, signal.SIGTERM):
            old_handlers[sig] = signal.signal(sig, lambda *_: stopping.__setitem__(0, True))
        with trace_path.open("a", encoding="utf-8") as trace:
            while state.next_event < args.episodes:
                if stopping[0] or (directory / "STOP").exists():
                    break
                if args.wall_seconds and time.monotonic() - started >= args.wall_seconds:
                    break
                attempt = play_mate_one(state.organism, state.next_position(fens),
                                        event_id=state.next_event, learn=True)
                state.next_event += 1
                state.mates += int(attempt.reason == "checkmate")
                state.real_moves += attempt.real_moves
                state.illegal += int(attempt.reason == "illegal_action")
                state.abstentions += int(attempt.reason == "no_action")
                trace.write(json.dumps(asdict(attempt), separators=(",", ":")) + "\n")
                trace.flush()
                if state.next_event % args.checkpoint_every == 0:
                    save_checkpoint(state, directory)
                if state.next_event % args.progress_every == 0:
                    print(json.dumps(state.progress()), flush=True)
        save_checkpoint(state, directory)
        summary = {**state.progress(), "invocation_seconds": round(time.monotonic() - started, 3),
                   "stop_reason": "budget_complete" if state.next_event >= args.episodes else
                   "requested_stop" if stopping[0] or (directory / "STOP").exists() else "wall_limit",
                   "validation_used_for_training": False,
                   "exercise": "mate within one own move; +1 mate, -1 exercise failure"}
        _atomic_json(directory / "progress.json", summary)
        return summary
    finally:
        for sig, handler in old_handlers.items():
            signal.signal(sig, handler)
        lock.rmdir()


def evaluate(args: argparse.Namespace) -> dict:
    # Own the same lock as training: a check-then-read would allow a trainer
    # to start while evaluation opened the final test and froze this run.
    lock = args.run / "run.lock"
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise RuntimeError("stop the active training/evaluation before evaluating its checkpoint") from exc
    try:
        return _evaluate_locked(args)
    finally:
        lock.rmdir()


def _evaluate_locked(args: argparse.Namespace) -> dict:
    if args.split == "test":
        if (args.run / "final_test_opened.json").exists():
            raise FileExistsError("this run already opened its final test")
        # Record the opening before any test positions/outcomes are read.
        with (args.run / "final_test_opened.json").open("x") as marker:
            json.dump({"opened": True, "source": source_identity()}, marker)
    fens, digest = load_split(args.pool, args.split)
    state = load_checkpoint(args.run)
    _, training_digest = load_split(args.pool, "train")
    if training_digest != state.pool_digest:
        raise ValueError("evaluation pool is not the training run's frozen pool")
    output = args.run / f"evaluation-{args.split}-{state.next_event:09d}.json"
    if output.exists():
        raise FileExistsError("this checkpoint/split was already evaluated")
    result = {"schema": "mate_one_coach_evaluation.v1", "split": args.split,
              "count": len(fens), "pool_sha256": digest, "training_attempts": state.next_event,
              "checkmates": 0, "illegal_actions": 0, "abstentions": 0,
              "learning": False}
    for i, fen in enumerate(fens):
        attempt = play_mate_one(state.organism, fen, event_id=i, learn=False)
        result["checkmates"] += int(attempt.reason == "checkmate")
        result["illegal_actions"] += int(attempt.reason == "illegal_action")
        result["abstentions"] += int(attempt.reason == "no_action")
    result["success_rate"] = result["checkmates"] / len(fens)
    _atomic_json(output, result)
    return result


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare", help="offline position curation; exports no answer moves")
    p.add_argument("--pool", type=Path, required=True)
    p.add_argument("--seed", type=int, default=20260905)
    p.add_argument("--train", type=int, default=256)
    p.add_argument("--validation", type=int, default=128)
    p.add_argument("--test", type=int, default=128)
    p = sub.add_parser("train", help="play repeated exercises against the opaque organism")
    p.add_argument("--pool", type=Path, required=True)
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--episodes", type=int, default=20000,
                   help="total target, including restored attempts; zero initializes only")
    p.add_argument("--wall-seconds", type=int, default=3600)
    p.add_argument("--checkpoint-every", type=int, default=256)
    p.add_argument("--progress-every", type=int, default=64)
    p.add_argument("--resume", action="store_true")
    p = sub.add_parser("evaluate", help="read-only; does not update the saved organism")
    p.add_argument("--pool", type=Path, required=True)
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--split", choices=("validation", "test"), default="validation")
    args = parser.parse_args(argv)
    if args.command == "prepare":
        result = prepare(args.pool, seed=args.seed, train=args.train,
                         validation=args.validation, test=args.test)
    elif args.command == "train":
        if (args.episodes < 0 or min(args.checkpoint_every, args.progress_every) < 1
                or args.wall_seconds < 0):
            parser.error("intervals must be positive; episodes/wall-seconds must be nonnegative")
        result = train(args)
    else:
        result = evaluate(args)
    print(json.dumps(result, indent=2), flush=True)
