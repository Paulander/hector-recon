# Fivefold owner experiment: learning appears, retention improves selectively

2026-09-14. User explicitly authorized five times the training before changing
the mechanism. Protocol: [OWNER_NOMINATION_FIVEFOLD.md](OWNER_NOMINATION_FIVEFOLD.md),
implementation/runner commit `66c5f5cd`, branch `codex/context-owned-decisions`.
This run completed and its original verifier passed. The earlier pilot's failed
progress-copy verification remains preserved separately; it was not relabeled.

## Fixed comparison and outcome

Same seeds 10/11, same environment and all 63 learner/core source files unchanged.
Repeat each original phase order five times: prefix 128→640, mostly-B 128→640,
mostly-A 128→640. Each continuation arm receives 1,280 training actions after
conversion at 640, ending at 1,920. All learner parameters remain unchanged,
including the original flat learner's `RecursiveConfig.prefix=128`.

| Seed | Arm | After 640 prefix | After mostly B | Final | Final A / B | Best measured | Parameters | Physical nodes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | Unsplit | 8/16 | 8/16 | 12/16 | 8/8 + 4/8 | 13/16 | 21 | 115 |
| 10 | Context splitting | 8/16 | 10/16 | 11/16 | 5/8 + 6/8 | 11/16 | 42 | 473 |
| 11 | Unsplit | 6/16 | 12/16 | 13/16 | 6/8 + 7/8 | 14/16 | 18 | 97 |
| 11 | Context splitting | 6/16 | 12/16 | 14/16 | 6/8 + 8/8 | 14/16 | 46 | 557 |

The short pilot finished all four arms at 8/16. With more experience both mechanisms
learn, and splitting finishes one point below control in seed 10 and one above in
seed 11. Their combined endpoint totals tie at 25/32. Two seeds do not establish
a general advantage; substantially larger execution graphs are a real cost.

The longer prefix itself did not improve these seeds: seed 10 stayed 8/16 and seed 11
fell 8→6/16. Their first 128-action actors reproduce the previous run's states exactly.
The subsequent arms therefore share genuine matched starting states, but these
are not competent initial A policies. Both prefix and continuation were lengthened;
do not attribute every short-versus-long difference solely to child sample density.
This is still a small development task, not evidence of chess transfer.

## Retention, not just final totals

| Seed | Arm | Original A successes lost by end of mostly B | B successes at that boundary | Those B successes lost by final | Prefix successes lost by final |
| --- | --- | --- | --- | --- | --- |
| 10 | Unsplit | 4 | 4 | 1 (row 11) | 2 (rows 6,7) |
| 10 | Context splitting | 0 | 6 | 0 | 2 (rows 8,9) |
| 11 | Unsplit | 0 | 8 | 1 (row 7) | 2 (rows 7,12) |
| 11 | Context splitting | 0 | 8 | 0 | 0 |

At the mostly-B boundary, seed 10's unsplit actor still scores 4/8 on A but has
replaced all four A successes from its prefix. The split actor preserves them
at that measurement. At the final endpoint after returning to mostly A, both split
actors solve every B success measured at the boundary, while each control has lost
one. This endpoint comparison does not establish uninterrupted retention.

This is selective evidence for retention, with an acquisition tradeoff in seed 10.
The split seed 10 temporarily loses B row 6 at 1,472 and later recovers it; it also
eventually loses two prefix A successes. Split seed 11 repeatedly swaps success
between A rows 4 and 12; at the endpoint row 4 fails and row 12 is solved. Across
the 20 continuation measurements, row-loss events are 15 versus 3 for seed 10 and 15
versus 10 for seed 11 (unsplit versus split). These counts are descriptive; the arms
also acquire different sets of successes, so they are not a normalized forgetting
rate. Full per-row trajectories are in the machine-readable analysis.

## Actual context exposure

The final contexts now receive substantial experience, with uneven visitation:

| Seed | Final child visits | Development opportunities in those children |
| --- | --- | --- |
| 10 | 236, 308, 272, 272 | 3, 4, 4, 4 |
| 11 | 243, 617, 116, 112 | 3, 9, 1, 1 |

In the short pilot, final children received only 4–28 visits and had no subsequent
64-visit development opportunity. Here both split actors add new scoring conditions
(14 and 10). Thus the short experiment stopped before an important part of child
development could happen. Nevertheless, fivefold total experience does not equalize
visits across contexts: two seed 11 children still receive only one development
opportunity. The controls each receive 1,280 local continuation visits and 20
development opportunities. Do not count their 640 inherited root visits as new
continuation experience.

## Follow-up mechanism investigation from saved evidence

No learner was changed after observing these outcomes. The planned offline audit
examined action distinctions, fixed-weight capacity, and whether new conditions
can activate under their owning context.

| Seed | Arm | New conditions | Cannot activate in their context | Distinguish actions in that context | Final perfect-ranking capacity |
| --- | --- | --- | --- | --- | --- |
| 10 | Unsplit | 16 | 0 | 8 | Feasible with different weights |
| 10 | Context splitting | 14 | 7 | 4 | Infeasible |
| 11 | Unsplit | 15 | 0 | 7 | Infeasible |
| 11 | Context splitting | 10 | 2 | 5 | Infeasible |

These condition counts describe births, including later retirements. Zero actual
credit was recorded for every one of the nine unreachable split-arm births. The
controls had no unreachable births; seed 10's final newborn had no later training.

A concrete seed 10 example: owner 6's route entails x=true and y=true. At event 1088,
it births condition 54, which requires x=false. The full contribution is therefore
identically false. This is a contradiction between graph expressions, independent
of which action the environment rewards. Over the complete finite Boolean domain,
the audit checks both action bindings on every row; no task answer enters training.

Growth has thus resumed, but some opportunities create unusable conditions. The
current random birth law samples the full coordinate vocabulary without checking
compatibility with the owning context. That is a concrete next development target;
more samples can allow other proposals to appear, but cannot make a contradictory
condition itself useful. Do not globally discard state-only definitions: they can
be valuable routing/composition components even when they add no immediate action
contrast as a weighted scorer.

The fixed-weight audit makes a further distinction. Seed 10's control has sufficient
final ranking capacity but its learned weights choose incorrectly on four rows.
Both split graphs retain exact forced-tie failures (seed 10 rows 5/10/11, seed 11 row 5),
so weights alone cannot repair their full policies. Seed 11's unsplit graph can
distinguish actions on every row but has a joint ranking conflict. The feasibility
checks use unrestricted offline weights only; no witness is installed or executed.
The code validates all 64 final chosen actions against their saved score definitions.

## Verification and resources

- 6,400 training actions, exactly five times the short pilot's 1,280.
- 1,344 scheduled evaluation actions and 1,344 separate frozen reproductions;
  9,088 environment executions in this experiment. No automatic retry or recovery
  training was performed. The repeated phase order is the authorized intervention.
- All 100 blocks and 106 checkpoints verified. Individual immutable submitted and
  credited action records agree with sealed journals and recursive hash manifests.
  The original verifier passed; no progress-copy reconciliation was needed.
- All 63 learner/core source hashes match the previous run. Source snapshots bind
  the recorder, protocol and runtime to this attempt; both first 128-action states
  reproduce the earlier actors exactly.
- 30 focused tests passed in 14.03 s, including four new schedule/recorder tests.
  The prior 267-test compatibility suite remains evidence for unchanged source;
  this was not a fresh full 271-test invocation.
- Worker elapsed 824.145 s (13 m 44 s), including full verification; peak RSS 42,060 KiB
  (41.1 MiB). One CPU,2 GiB address-space ceiling,1,200 s worker and 1,230 s independent
  wall stops. The saved-graph analysis took 0.414 s and executed no environment action.

## Revised decision

The sample-density objection was material. Replace the short pilot's provisional
negative interpretation with mixed acquisition and encouraging measured retention
evidence. Keep ownership experimental and keep the ordinary learner as a baseline.

The next local mechanism checkpoint should address context-compatible, action-useful
growth, rather than presuming that children cannot develop or immediately adding
freezing. Establish a generic rule from the graph's own logical constraints or
actual local confirmations; do not inject the offline-identified conditions. Keep
compatibility, action-contrast prioritization and split/birth scheduling as separable
changes. Unwitnessed rare combinations are not the same as logically impossible
ones, and state-only reusable structure must remain available.

An equal-total-experience comparison and a comparison with sufficient measured
child exposure answer different questions. Record both costs and per-context
visits in the next protocol. A common physical trunk, safe shared trainable
knowledge, local freezing/reopening and full goal arbitration remain unimplemented.

All processes have stopped. This turn completed the authorized rerun and the
saved-evidence mechanism investigation; no subsequent learner change or additional
training experiment was launched.

Evidence: `reports/autogrowth/development/OWNER_FIVEFOLD_ANALYSIS_20260914.json`,
`OWNER_FIVEFOLD_CHECKS_20260914.json`, and
`scripts/autogrowth/analyze_owner_fivefold.py`.
