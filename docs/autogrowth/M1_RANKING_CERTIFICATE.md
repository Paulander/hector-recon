# Tie-aware follow-up to the M1 representation diagnosis

This is a declared **post-hoc** clarification, motivated by the first diagnostic's
strict-ranking infeasibility results. It does not change that original protocol
or count further work as part of the original run. No learner mechanism changes.

The original check demanded every win strictly outrank every failure. That can
miss a valid policy using favorable ties. Here every observed exercise must have
exactly one winning move; otherwise the calculation refuses the stronger claim.
For each winning/losing pair, require positive support margin if the existing
reverse-lexical slot tiebreak favors the loss, and nonnegative margin if it favors
the win. On a finite homogeneous system, strictly positive margins may be scaled
to at least one. This makes feasibility equivalent to a perfect fixed-weight
policy on these rows under the existing tie rule, in exact arithmetic. Any
numerical feasible solution must also reproduce the selected winners directly.

Also look for elementary contradictions: the same signed combination of gate
weights required to be both positive and nonpositive, or a zero difference
required to be positive. Such a pair proves impossibility without relying on the
optimizer. Publish the signed gate-difference vector and margins only, never the
board, action labels or a fitted policy. No fitted coefficients enter the actor.

Use the exact same eight frozen actors and 256/128 train/development rows.
Reconstruct the temporary laboratory data because the first run intentionally
does not persist an alternative-action dataset. **7,039 additional laboratory
transitions, zero actor moves, zero training moves; one process, 180 seconds,
one attempt, no extension.** The final test remains closed. Require source,
checkpoint and pool identity; preserve a failure record if incomplete.

The implementation is the isolated module
`recon_lite_chess.experiments.m1_ranking_certificate`. Four generic tests cover
favorable/unfavorable ties, a contradictory pair with distinct signatures, a
context conjunction that removes the contradiction, and rejection of multiple
winning actions. These are mechanism fixtures, never chess training structures.
