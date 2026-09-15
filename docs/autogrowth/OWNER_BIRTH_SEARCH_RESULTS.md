# Owner-local birth selection: completed factorial pilot

2026-09-15. Protocol: [OWNER_BIRTH_SEARCH.md](OWNER_BIRTH_SEARCH.md), fixed in local
`c834e24a` before play and published as the identical source tree in remote
`3b41349ec4563f2d859b55310532b3bf3703452b`. No runtime setting changed during play.

**Residual nomination with the existing development schedule is the strongest
candidate for a follow-up, but it has not solved retention. Extra birth
opportunities add cost and do not consistently improve behavior. Main is unchanged.**

These are two reused seeds on the 16-row Boolean development task. Each arm uses
the same 24-condition pool for its seed, the same event-640 source and the same
1,280-action mostly-B/mostly-A continuation. The old compatibility experiment
is historical context, not the matched random null: the fixed pool changes
proposal availability even in random mode. There is no new chess result.

## Matched outcomes

| Nomination / schedule | Seed 10 | Seed 11 | Total | Final physical nodes, seeds 10 / 11 |
| --- | ---: | ---: | ---: | ---: |
| Random / current | 13/16 | 16/16 | 29/32 | 529 / 633 |
| Residual / current | 14/16 | 16/16 | 30/32 | 515 / 605 |
| Random / extra after split | 14/16 | 13/16 | 27/32 | 579 / 671 |
| Residual / extra after split | 14/16 | 16/16 | 30/32 | 577 / 665 |

With the current schedule, ranking gains one endpoint success in seed10 and ties
seed11. Seed11 first reaches16/16 at event1408 under ranking versus1920 under
random choice:512 fewer continuation actions. It remains perfect at every later
scheduled checkpoint. The extra/ranked arm first reaches16 at1472,64 actions
later than current/ranked. No seed10 arm reaches16.

The extra schedule admits exactly three more births per seed:15→18 for seed10,
14→17 for seed11. All attempted nominations become births in this pilot. It gains
one endpoint success in random seed10 but loses three in random seed11. It changes
neither ranked endpoint and adds62/60 physical nodes versus current/ranked.
Realized parameter counts are43/50,42/47,47/53 and47/52 in table order. Physical
counts include candidate-observer overhead and are not counts of independent
learned concepts. Ranking also changes subsequent pruning, so lower node counts
cannot be attributed solely to choosing simpler expressions.

## Acquisition and retention are different results

Each prefix has only four solved A rows, despite640 training actions. This remains
a weak-prefix acquisition pilot, not a mature-skill retention benchmark.

| Nomination / schedule | Fewest original A successes retained at measured checkpoints, seeds10 /11 (out of4) | Seed10 final A/B | Seed10 boundary B successes retained at endpoint |
| --- | --- | --- | --- |
| Random / current | 2 /1 | 6/8,7/8 | 7/8 |
| Residual / current | 4 /3 | 8/8,6/8 | 6/8 |
| Random / extra | 2 /1 | 7/8,7/8 | 6/7 |
| Residual / extra | 2 /3 | 8/8,6/8 | 6/8 |

Ranking/current better preserves the initially solved A rows at the measured
checkpoints in both seeds. But seed10 learns all eight B rows by the phase
boundary and then loses rows6/7, while random/current loses only row6. Its extra
A acquisition outweighs the additional B loss in the endpoint total. Neither
the gain nor the loss should be hidden by that total. Random/extra's seven final
B successes include replacement: one boundary success is lost and another B
row is acquired. Both seed10 extra arms temporarily drop to4/16 at event768.

All seed11 arms retain their eight boundary B successes at every later measured
checkpoint. Random/extra ends with5/8 A; the other three end with8/8 A. These
64-action measurements do not establish uninterrupted retention between checks.

## Mechanism and evidence

Residual selection is actually exercised: current/ranked makes13 and9 ranked
selections in seeds10/11; extra/ranked makes11 and10. Remaining selections use the
declared random/fallback path. Both modes consume the same lottery-draw pattern
per nomination opportunity. The candidate pool and exploration streams are
matched across all four arms per seed; selected actions and subsequent evidence
are allowed to diverge. No task labels, alternative outcomes, diagnostic fitted
weights, semantic merging or freezing enter the learner.

All10,240 training actions,2,560 scheduled evaluation actions and2,560 frozen
reproduction actions completed:15,360 actual environment actions overall.
The original immutable-block checks pass all160 blocks and168 new checkpoints;
two exact source checkpoint copies are retained. The additional verifier
reconstructs every owner's candidate residual counts and sums from recorded real
actions at all160 checkpoint boundaries, including retained ancestor evidence.
All76 execution-source hashes match their snapshots; all63 original learner/core
files remain unchanged. All73 distinct focused checks pass, including14 new
mechanism/recorder tests. Test fixtures are separate from the experiment counts.

Runtime2182.989s (36m23s), peak RSS46,200KiB (45.12MiB), one CPU, within the2GiB
and3600s worker limits. Complete, no retry, no process remains running.

The analysis preserves the legacy recorder's ordinary-only birth count under
`ordinary_births_after_conversion` and computes total accepted births from the
complete nomination records, including the extra opportunities. Direct condition
identity credit counts do not include credit later received by cloned descendants;
they are not causal-usefulness or maturity measures.

## Continuation and main

Keep compatibility and the current64-visit schedule as the reference. Preserve
random nomination as the matched control. Residual/current is promising enough
for a fixed fresh-seed replication and a separately declared strong-prefix
retention comparison; two reused seeds do not justify a production default.
Do not add another growth/freeze/merge mechanism before that comparison is defined.
The fixed candidate pool also remains an experimental restriction, not open-ended
structural discovery. Protection/reopening and shared execution factoring remain
on the recovered architecture plan as separate later work.

Do not merge the entire work branch into main merely because the compatibility
check passes: the recovered branch already contained157 changed files relative to the stable
main base before this increment, including several distinct experiments. A reviewed integration of experimental
modules is different from promoting their behavior to a default. This turn
publishes the private work branch and evidence; it does not merge main.

Remote publication uses source-tree snapshots because ordinary Git transport
has no credentials here. Original local commits/history remain intact. The
September14 local `bc61220e` tree is published at `d7ec0e1`; the implementation
tree `c834e24a` is published at `3b41349`. These are different commit objects with
verified identical respective trees, not claims of an exact-history Git push.

Evidence: `snapshots/autogrowth/owner-birth-search-20260915/`,
`reports/autogrowth/development/OWNER_BIRTH_SEARCH_20260915.json`, and
`reports/autogrowth/development/OWNER_BIRTH_SEARCH_CHECKS_20260915.json`.
