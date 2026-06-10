# Learned Endgame Switching (Router) Spec

## Goal
Replace the current *binary material router* (KPK/KQK/KRK picked via `active_endgame`) with a *trainable router* that can learn to allocate control among endgame subgraphs based on continuous affordance-like signals and learned gate edge weights.

Concrete outcome we care about:
- In a KPK near-promotion setting, the system locks into the KPK subgraph before promotion, and then reliably hands over to the correct successor subgraph *after* promotion:
  - Promote to Queen -> hand over to KQK
  - Promote to Rook  -> hand over to KRK
- The handover latency target is 1 move (promotion move is made under KPK; next move is made under the successor subgraph).
- The *choice* of successor subgraph should become learned: routing preferences are represented by edge weights and improved via the existing plasticity/consolidation loop.

## Non-goals
- Solving full chess or making the whole unified graph strong.
- Making endgame detectors prior-free. The point is to make routing learnable; some priors remain (affordance models, or even material features).
- Rewriting the entire training harness. This should be an incremental refactor that preserves existing behavior behind a flag.

## Current Behavior (main branch)
### Where routing happens today
- `src/recon_lite_chess/scripts/endgame_gate.py`
  - Computes `env["endgame_gate"]["activations"]` using *binary* pattern detectors (exact KPK/KQK/KRK).
  - Writes `env["endgame_gate"]["active_endgame"]` as an argmax over those binaries.
- `demos/persistent/full_game_train.py`
  - If not already locked, it calls `gate_node.predicate(..., env)` and then uses `active_endgame` to call:
    - `engine.lock_subgraph(f"{active_endgame}_root", sentinel_fn)`
- `src/recon_lite/engine.py`
  - Implements `SubgraphLock` and `_step_subgraph`, so execution collapses into the chosen subgraph until it yields `env[subgraph]["policy"]["suggested_move"]`.

### What is "automatic" vs "learned" today
- The *handover event* (KPK -> KQK after promotion) is automatic because the sentinel/pattern changes, not because an explicit phase rule was authored.
- The *routing decision* is mostly hardcoded because `active_endgame` is derived from binary detectors, and the training loop follows it directly. There is little room for learned preference because there is no overlap (ties are rare; signals are 0/1).

## Design Overview
We introduce a router policy that computes a routing score per endgame and chooses which subgraph to lock into.

### Router inputs
1. `gate_signal[subgraph]` in [0,1]
   - Prefer continuous "affordance" signals to create overlap (so learning matters).
   - Source:
     - Use existing `src/recon_lite_chess/affordance/sensors.py` via `compute_all_affordances(board)`
     - Or use `src/recon_lite_chess/graph/subgraph_gates.py` (`compute_subgraph_gates`)
2. `learned_weight[subgraph]`
   - Derived from the *existing* gate-to-subgraph root edge weights in the unified graph:
     - `endgame_gate -> kpk_root` (SUB)
     - `endgame_gate -> kqk_root` (SUB)
     - `endgame_gate -> krk_root` (SUB)
   - These weights are already compatible with M3/M4 (they are POR/SUB edges) and are already included in the "fullgame whitelist" logic in `demos/persistent/full_game_train.py` (edges whose `dst.endswith("_root")`).

### Router policy
For each candidate subgraph `s` in {kpk, kqk, krk}:

```
score[s] = gate_signal[s] * weight[endgame_gate -> s_root]
```

Selection:
- Greedy argmax over `score`, with optional exploration:
  - epsilon-greedy: with prob eps pick random among candidates above a minimum gate threshold
  - or softmax over `score` with temperature `T`

Locking:
- If `max(score)` exceeds a minimum threshold, lock into `*_root` via `engine.lock_subgraph(...)`.
- Continue to use subgraph sentinels to unlock when the situation changes (promotion, capture, etc.).

### Learning signal (credit assignment)
Critical point: the router must receive credit/blame for its choice.

We do this by ensuring the *selected routing edge* is treated as "fired" for the episode:
- When the router locks into `s_root`, we record a routing event:
  - a fired-edge entry for `endgame_gate->s_root:SUB`
  - and/or directly increment the corresponding edge trace if your training loop uses `edge.trace` accumulation

Then the existing per-episode reward already used in `demos/persistent/full_game_train.py` (tick reward, outcome reward) will update those gate weights through M3/M4.

This is the minimal wiring needed to make "switching" learnable without inventing a new learning subsystem.

## Implementation Plan
### Step 0: Keep backward compatibility
Add a flag/setting so the old behavior remains available:
- `router_mode = "binary_active_endgame"` (default initially)
- `router_mode = "learned_affordance"`

### Step 1: Expose continuous gate signals
Option A (minimal code movement):
- Extend `src/recon_lite_chess/scripts/endgame_gate.py` so its predicate can optionally write:
  - `env["endgame_gate"]["signals"] = {"kpk": float, "kqk": float, "krk": float}`
  - computed via `compute_all_affordances(board)`
- Leave `activations` and `active_endgame` intact for legacy.

Option B (reuse existing module):
- In `demos/persistent/full_game_train.py`, compute:
  - `signals = compute_subgraph_gates(board, phase=..., use_affordance=True)`
  - and stash it into `env["endgame_gate"]["signals"]` for logging.

### Step 2: Implement router selection in `full_game_train.py`
Replace the `active_endgame` selection when `router_mode == learned_affordance`:
- Collect gate-to-root weights from the unified graph:
  - Find edges where `src == "endgame_gate"`, `dst in {"kpk_root","kqk_root","krk_root"}`, `ltype == SUB`
- Compute `score[s] = signals[s] * weight[s]`
- Apply selection policy (argmax or softmax)
- Lock subgraph root and record the routing edge as fired (for learning)

### Step 3: Ensure routing edges are learnable
Add one of:
- **Fired-edge accounting**: append `{"src":"endgame_gate","dst":f"{s}_root","ltype":"SUB"}` into the episode's fired-edge list used by plasticity/consolidation.
- **Trace increment**: locate the edge object in `g.edges` and increment `edge.trace += 1.0` when routing is chosen.

Acceptance check:
- After N training games, `weights/latest/fullgame_consol.json` should show changes in `w_base` for `endgame_gate->*_root:SUB` edges.

### Step 4 (optional): Randomize promotion to Q or R
To reduce "cheating" and force correct successor identification:
- In `src/recon_lite_chess/scripts/kpk.py` promotion move selection:
  - Add a controlled randomization (or env flag) choosing QUEEN vs ROOK on promotion rank.
  - Example control mechanisms:
    - env var `KPK_PROMOTE_PIECE` in {"Q","R","QR"} where "QR" means randomized
    - or pass `env["kpk"]["promotion_policy"] = "random_qr"` from the trainer

This ensures post-promotion endgame is not always KQK.

### Step 5: Focused training scenario ("bridge")
We want a training distribution where:
- KPK is present and within 2 moves of promotion
- After promotion, the agent must continue and deliver mate (KQK or KRK) or at minimum demonstrate correct routing and a legal successor move.

Data:
- Reuse `data/bridge/near_promo.fens` (1 move) for sanity.
- Add `data/bridge/two_moves_to_promo.fens` (2 moves) to make routing matter earlier (affordances overlap more).

Episode termination options:
- "Short bridge": stop immediately after promotion + 1 successor move, reward correctness/latency.
- "Full conversion": continue until checkmate/timeout, reward outcome.

The "short bridge" version is the cleanest way to isolate router learning.

## Metrics and Logging
Log per move:
- gate signals (kpk/kqk/krk)
- selected subgraph
- selected routing scores and edge weights
- whether lock/unlock happened (and why, via sentinel)
- handover latency (promotion ply -> first successor ply)
- routing accuracy:
  - after promotion to Q: selected == kqk
  - after promotion to R: selected == krk

## Expected Failure Modes
- If `signals` are effectively one-hot (close to binary), router weights won't learn much.
  - Fix: use affordances and ensure overlap in positions.
- If routing edge is not credited as fired, weights won't update.
  - Fix: explicit fired-edge record or trace increment.
- If KQK/KRK subgraphs are weak, outcome-based reward is too noisy for router learning.
  - Fix: use "short bridge" reward, or pretrain subgraphs first.

## Acceptance Criteria (implementation-level)
1. Router mode flag toggles behavior without breaking legacy runs.
2. In learned router mode, `endgame_gate->*_root` weights measurably change after training.
3. In a bridge evaluation set, routing accuracy improves relative to untrained weights.
4. Handover latency remains 1 move in the promotion bridge.

## "Did I already do this?" Checklist
This can be true if you previously:
- computed affordance signals and used them for routing,
- multiplied by gate edge weights (or otherwise used weights in selection),
- and credited the chosen gate edge for learning.

Fast way to confirm:
- Search for code that reads `compute_subgraph_gates` (or `compute_all_affordances`) and then calls `lock_subgraph` based on *weighted scores* rather than `active_endgame`.
- Search for explicit trace increments or fired-edge insertion for `endgame_gate->kpk_root` etc.

If any of the above exists on another branch, we should port the minimal diff back onto `main` instead of re-implementing.

