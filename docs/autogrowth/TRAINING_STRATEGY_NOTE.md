# Training Strategy Note

Date: 2026-07-01

## Episode-First Curriculum After Mate-in-2

KRK curriculum stages after Mate-in-1 and Mate-in-2 should be trained as episodes from a starting position to an endpoint, horizon, or failure. The training unit is the trajectory, not a single isolated move.

Mate-in-1 and Mate-in-2 are degenerate exceptions:

- Mate-in-1 is one white move, so move-local reward is the whole episode.
- Mate-in-2 is one first white move away from a known Mate-in-1 continuation after every legal black reply, so first-move credit can be tightly validated by all-reply continuation.

Later stages are different. Same-side rook-danger, edge killbox, fence establishment, king approach, and broader edge/fence stages are multi-ply skills. A good first move may only become meaningful after black replies and after the resulting state transitions toward a safer or more useful subproblem.

## Multi-Ply Curriculum Requires Trajectory Reward

For multi-ply stages, move-local scoring may still exist as diagnostics, pruning, or cheap trainer-side hints, but it should not be the primary success claim. The primary claim should be episode-level:

- Did the episode reach a validated foundation entry?
- Did it transition to a safer or more useful geometry?
- Did it preserve rook safety and confinement through replies?
- Did it avoid graph-positive validator-false states, partial-only near-basin support, stalemate, illegal moves, and rook loss?

The final episode reward should be propagated back over the white-move terminal activations that participated in the episode. Use eligibility traces or discounted credit so the latest causally relevant white move receives strongest credit or debt, while earlier moves receive discounted credit or debt.

## Trainer-Side Playout Boundary

Trainer-side playout and validation are allowed for:

- generating experience;
- assigning reward and debt;
- evaluating heldout positions;
- diagnosing failures;
- writing artifacts.

They must not become a hidden runtime selector. Runtime behavior must remain mediated through ReCoN terminal/script/action structure, M3/M4 weights, and graph activation. No runtime engine/provider/selector, tablebase/DTM/Stockfish move source, Python final selector, direct provider override, or hardcoded FEN/move repair is allowed.

## TG48a2 Same-Side Rook-Danger

The move-local TG48a2 microstage showed that safe lateral rook moves were usually available, but the graph did not learn a useful heldout affordance from isolated move scoring. This should be treated as an infrastructure/diagnostic failure, not evidence that the skill is unlearnable.

TG48a2 should now train episodes:

```text
same-side rook-danger start
-> safe lateral rook move
-> black reply
-> preserve rook/fence/confinement
-> transition toward opposed-side, edge-killbox, or foundation-friendly geometry
```

Credit should be assigned after the episode endpoint is known, then discounted back through the white-move terminal activations.

## TG48b and TG48c

The same policy applies to later curriculum steps:

- TG48b fence establishment should reward trajectories that establish and preserve a useful fence through replies, not just one locally attractive rook or king move.
- TG48c king approach should reward approach only when it remains compatible with confinement, rook safety, and eventual foundation handoff.

Move-local diagnostics can help explain candidate actions, but multi-ply curriculum claims must be episode-level claims.
