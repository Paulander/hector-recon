# Four versus eight decision owners

Declared 2026-09-15 before cohort play. The user explicitly authorized the
proposed experiment while discussing composition and maturation. The previous
fresh cohort is closed; this study uses new seeds and no saved training state.

## One changed setting

Fresh seeds 15, 16, 17, each with an owners-4 and owners-8 arm. Both use the
current residual-ranked 24-candidate birth search, including its 25% uniform
selection path. Only OwnershipLimits.max_leaves differs, four versus eight.
All other initial state, route/condition pools and four RNG streams must match.
The four-owner factory must exactly reproduce the existing residual/current
factory. No learner or existing recorder source is changed.

Keep learning rate .3, exploration .25, development every64 active-owner visits,
minimum evidence support4, and current split-replaces-birth scheduling. Keep
pruning age256 local visits and effective-weight threshold .02, consolidation,
zero-weight scoring births and behavior-preserving whole-owner inheritance.
Retain max_parameters64, max_definitions256, max_physical_nodes2048 and depth4.
These ceilings need not all bind. Children may split recursively under the
existing local residual rule; no route, useful feature or weight is supplied.
Split opportunities are not chosen from evaluation results.

The current learner has no active TRIAL-to-MATURE promotion. Its route pool is
frozen at initialization and fresh actors receive eight atomic state tests.
Scoring births use the existing shallow Boolean grammar, which lacks k-of-n.
This experiment does not change those mechanisms, freeze weights, add delayed
splitting, compensate child exposure, or introduce depth-dependent timing.

## Fixed play and limits

Each actor starts with zero completed actions, one zero-valued bias owner and
no imported training. Use the existing seed-generated1920-action schedule:
640 A,640 mostly B,640 mostly A. Phase identities and desired actions never
enter the learner. Only terminal observations and the submitted action's
actual scalar reward enter its existing local development and credit rules.

Evaluate all16 Boolean rows on disposable clones initially and every64 actions.
Record the same16 rows for frozen reproduction from each saved checkpoint.
Totals:11520 training,2976 scheduled evaluation,2976 frozen reproduction actions;
180 blocks and186 checkpoints. No score-based stopping, seed replacement, extra
play, retry or automatic extension, including if eight owners delay acquisition.

One CPU; numerical libraries one thread;2 GiB address space;64 MiB per file;
3600-second worker deadline and3630-second independent GNU timeout with5-second
kill grace. If interrupted, preserve the attempt and report incomplete evidence.

## Verification and interpretation

Use the unchanged immutable per-action submission/credit recorder and block
seals. Snapshot runtime sources before play, check them again at completion,
verify initial state apart from the declared limit, reconstruct all candidate
residual histories and scalar credit from actual logs, reproduce every frozen
evaluation, and verify paired exploration RNG states. Every checkpoint must
retain its arm's original limits. Focused tests check factory equality, matched
early actual learning, recursive growth beyond four and checkpoint isolation.

Report full row-level acquisition/loss/recovery, phase-boundary A/B retention,
first and sustained measured perfection, owner split times, first scoring birth,
per-owner exposure, condition births/pruning and physical/parameter cost.
Initial chance successes are not acquired skills. Since extra splits consume
development opportunities and reset child-local visits, eight owners may delay
useful scoring conditions. Equal global experience is not equal child experience.
Do not infer that a lower score disproves recursive isolation itself.

Offline analysis may inspect scores or capacity but cannot install fitted
weights, select training routes or otherwise steer the learner. This small
cohort is development evidence, not a default change or a chess result. The
private work branch may be published; main is unchanged.
