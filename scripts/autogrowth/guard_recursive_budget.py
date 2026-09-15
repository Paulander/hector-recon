"""Portable independent wall/RSS guard for one bounded experiment process."""
import argparse
import json
import os
import resource
import signal
import subprocess
import sys
import time


def guard(command, seconds):
    env = dict(os.environ, PYTHONHASHSEED="0", OPENBLAS_NUM_THREADS="1",
               OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", VECLIB_MAXIMUM_THREADS="1",
               NUMEXPR_NUM_THREADS="1")
    def child_limits():
        if sys.platform != "darwin":
            resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    worker = subprocess.Popen(command, env=env, start_new_session=True, preexec_fn=child_limits)
    started = time.monotonic()
    reason = None
    try:
        while worker.poll() is None:
            if time.monotonic() - started > seconds:
                reason = "wall limit"
                break
            # Linux hard AS limits also cover virtual allocations. Do not use ps
            # there: a container's proc mount can expose a different PID namespace.
            if sys.platform == "darwin":
                rss = subprocess.run(["ps", "-o", "rss=", "-p", str(worker.pid)],
                                     capture_output=True, text=True, timeout=2)
                if rss.returncode == 0 and rss.stdout.strip():
                    if int(rss.stdout.strip()) > 2 * 1024**2:
                        reason = "2 GiB worker RSS limit"
                        break
                elif worker.poll() is None:
                    try:
                        worker.wait(timeout=.1)
                    except subprocess.TimeoutExpired:
                        reason = "memory monitor unavailable"
                        break
            try:
                worker.wait(timeout=.5)
            except subprocess.TimeoutExpired:
                pass
        if reason:
            print(json.dumps({"guard": "stopped", "reason": reason}), flush=True)
    finally:
        if worker.poll() is None:
            os.killpg(worker.pid, signal.SIGTERM)
            try:
                worker.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(worker.pid, signal.SIGKILL)
                worker.wait(timeout=5)
    return 124 if reason else worker.returncode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=int, default=620)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not 1 <= args.seconds <= 620 or not args.command:
        parser.error("a command and a 1..620 second budget are required")
    command = args.command[1:] if args.command[0] == "--" else args.command
    sys.exit(guard(command, args.seconds))
