# Generic-Core Renewable Topology Work Package

Date: 2026-07-12. Track: generic-core development. Status: PI-authorized and
frozen before implementation.

## Predecessor

The immutable key-door package at `f5d56d2` learned persistent key decisions
and the new regime perfectly but retained old-regime door success at 0.0. Every
door action used all four lifetime candidate slots by observation 512; no
regime-1 cue composite could be born.

## Hypothesis

Treating the four-candidate limit as concurrent live structural capacity, while
allowing pruned candidates to release their slot under a separate bounded
lifetime proposal budget, will let learner-local residuals nominate regime-1
cue composites. This renewed topology will improve old/new regime coexistence
without replay, weight freezing, learning-rate changes, or host phase signals.

## Strongest null

Renewed slots merely grow more irrelevant structure; mature phase-0 candidates
still occupy capacity; shared primitive weights still invert the old mapping;
new composites form but do not affect behavior; extra compute rather than
renewal causes improvement; or the laboratory implicitly resets topology at the
phase boundary.

## Exactly one changed scientific factor

The predecessor uses:

- maximum four candidates over the learner's entire lifetime.

This package uses:

- maximum four concurrently live `trial` or `mature` candidates;
- `pruned` candidates remain in the audit ledger but release their live slot;
- maximum 64 total proposals per action over the full 8,192-episode run.

There is no phase-boundary notification, slot reset, candidate deletion from the
ledger, pair reproposal, replay, consolidation, slow-weight freeze, altered
credit, altered learning rate, altered proposal interval, or added operator.

## Frozen implementation contract

- add `max_total_proposals` to the generic composition configuration;
- default behavior remains the old lifetime cap for existing callers;
- proposal eligibility requires both live count below `max_candidates` and
  total proposal count below `max_total_proposals`;
- a mature candidate consumes a live slot;
- trial expiry or causal pruning releases a live slot;
- an already proposed pair cannot be proposed again;
- snapshots report total, live, trial, mature, and pruned counts.

Lifecycle tests must prove slot release, mature-slot retention, lifetime-budget
enforcement, and unchanged legacy defaults without using frozen task seeds.

## Frozen environment and learner

Reuse the key-door environment and all learner settings exactly:

- 20 fresh tasks, seeds 20261101–20261120;
- 4,096 regime-0 then 4,096 regime-1 episodes;
- no regime-0 replay after the observable regime change;
- 512 untouched evaluation episodes per regime;
- two learner-selected actions per episode and terminal-only ±1 valence;
- persistent versus transition-reset arms;
- online learning rate 0.08, proposal interval 128, minimum support 16,
  burn-in 8, 32 confirmations, causal margin 0.01, resource cost 0.002,
  trial expiry 512;
- epsilon 0.15 and discount 0.97;
- identical identity permutation, legal-action interface, topology operators,
  credit, graphs, outcome function, and evaluation.

The runner must reuse the predecessor's frozen environment implementation and
record its hash.

## Measurements

In addition to all predecessor metrics:

- total and live candidate counts over final state;
- proposal birth observations and state;
- regime-0 versus regime-1 cue/regime candidate identity;
- actions that reached four mature live candidates;
- total proposal budget consumption;
- old/new full and composite-disabled behavior.

## Gates

Development support requires every gate:

1. persistent tasks with a mature cue/regime-1 pair: at least 16/20;
2. persistent median regime-0 joint success: at least 0.70;
3. persistent median regime-1 joint success: at least 0.85;
4. persistent median key accuracy: at least 0.90 in both regimes;
5. persistent joint success exceeds reset on at least 16/20 tasks in both
   regimes;
6. median full-minus-composite-disabled joint success: at least 0.15;
7. total proposals never exceed 64 and live candidates never exceed four per
   action;
8. graph/update mismatches and trial-root leakage are zero;
9. configured experience, legal-action, RNG-call, and compute budgets match on
   20/20 tasks.

The reduced old-regime threshold is preregistered because this package changes
only structural opportunity, not consolidation. Full retention remains the
longer-term criterion and any residual loss must be reported.

## Stop rule

Commit and push contract, implementation, and runner before generating fresh
tasks. Execute once. Any failed gate closes the package without adding replay,
changing plasticity, enlarging budgets, or rerunning. Builder-run measurements
are not independent confirmation.
