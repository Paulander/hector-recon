# Owner-local action coverage: bounded pilot

Declared before study play on 2026-09-16. This is a two-action Boolean mechanism
test, not chess. The completed seeds 30–32 action-contrast cohort remains closed.

## Hypothesis and single intervention

The previous four-cell action-contrast ranker could nominate an irrelevant noise
route because the policy had executed only eight `act-a` actions by episode 128.
At that point noise happened to be the sole candidate with enough observations
of both actions on both route sides. This pilot asks whether improving actual
action coverage at the currently active owner makes route competition less
eligibility-biased. It does **not** test a new local-reward hierarchy.

Fresh seeds 33, 34, 35 each receive the unchanged 1,920-action schedule in
three matched arms: `current`, `action-contrast`, and `owner-balance`. The last
inherits the action-contrast nomination, prospective acceptance, learning,
birth/retirement, limits and 0.25 stochastic exploration rate unchanged. At an
existing exploration event only, it formally requests the owner gates, then
directs the same bounded graph exploration signal toward a least-sampled legal
action of that owner (random tie-break). The graph still chooses and executes.
Counts are updated only from its submitted and credited action; no row index,
reward sign, target, unchosen outcome or evaluation result enters this choice.
No coordinate or route is specially treated. Child owners begin local counts
at zero. There is no globally scheduled nomination delay or new reward.

## Fixed execution and decision

One worker; independent Mac RSS guard at 2 GiB; 3,600-second wall/CPU cap;
numerical threads fixed to one. Each 64-action block seals submitted/credited
records, checkpoint and 16-case greedy evaluation. Stop on the first failure,
preserve evidence, and do not retry or tune. Verify source hashes, actual
action credit, trial records, local action counts, all checkpoints and frozen
evaluations. Three fixture seeds outside the study and the existing focused
tests must pass before play.

Primary endpoint: paired final correct/16 for owner-balance versus both arms.
Secondary: action counts and route eligibility at the first root nomination,
route identities/states, A/B retention, stored nodes/parameters and allocation.
Advance only to a separate replication if at least two seeds beat the
action-contrast arm, no seed loses more than two rows versus current, no root
noise partition survives merely through exclusive eligibility, all integrity
checks pass, and graph costs remain bounded. Otherwise stop this particular
coverage rule. Three seeds are descriptive evidence, not a reliability claim.
