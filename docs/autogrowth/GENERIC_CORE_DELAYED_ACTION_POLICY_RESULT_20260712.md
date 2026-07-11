# Generic-Core Delayed Action Policy: Raw Development Result

Date: 2026-07-12. Track: generic-core development. Confirmation claim: none.
The builder and runner are the same agent.

## Frozen execution

The contract was committed and pushed at `a4ed2df`. Implementation, lifecycle
tests, the graph AND-aggregation repair, and the runner were committed and
pushed at `9646ded` before task generation. The frozen seeds were executed
once. No outcome-driven code, threshold, budget, task, or hyperparameter change
was made.

Before the run, integration testing found a pre-existing graph defect: AND
aggregation iterated `(child_id, weight)` pairs as node IDs, so every child
lookup failed. The one-line tuple-unpacking repair is covered by the new
materialization/activation regression test. This was an instrument repair before
any frozen row existed, not a post-result rescue.

## Raw measurements

| Measurement | Frozen requirement | Observed |
|---|---:|---:|
| Persistent accuracy higher than reset | at least 16/20 tasks | 20/20 |
| Persistent median full-graph accuracy | at least 0.90 | 1.000000 |
| Median full-minus-composite-disabled accuracy | at least 0.20 | 0.540039 |
| Persistent task with mature hidden signal pair | at least 16/20 | 20/20 |
| Graph/update prediction mismatches | zero | zero |
| Trial script root edges | zero | zero |
| Identical configured episode/action/candidate budgets | 20/20 | 20/20 |

Descriptive distributions:

- persistent full-graph accuracy mean 0.993164, median 1.0, range 0.9375–1.0;
- per-step-reset accuracy mean 0.505176, median 0.519531, range
  0.345703–0.662109;
- persistent composite-disabled accuracy mean 0.506055, median 0.459961, range
  0.246094–0.943359;
- every persistent task credited exactly 4,096 selected decisions; every reset
  task credited zero;
- every persistent terminal saw a one-decision trace; every reset terminal saw
  an empty trace;
- both action channels consumed the same maximum four-candidate budget in every
  persistent task, with different candidates surviving future causal tests.

Artifact:
`reports/autogrowth/generic_core/delayed_action_policy_anonymous_xor_20260712.json`

- artifact SHA-256:
  `1269c214487c26736aec6acedcb257697b3a1a79ef9eca7bfa8e3798ce5b33e0`;
- source commit:
  `9646dedde58b242c8e866a4b743c303aa305e3cb`;
- task-row SHA-256:
  `5694684d39fde4fb4b0fbfa0f929d546a3c970d9aabdcc616e08a9860b49bfc5`;
- episodic implementation SHA-256:
  `25a4d3260af48cf82e2022c60b0d2a66c1dc7685b2e36582d3855ead151682d6`;
- frozen composition implementation SHA-256:
  `0b647e16fc2173535d1d01bdfd076947a5dd2d0fc304a9372f805f8161941f2d`;
- runner SHA-256:
  `ad2b449bb1a08a4891a17292b1b026ad69b1dc1e22b24b4499491ceeed528a36`.

## Narrow supported statement

On this frozen delayed contextual-action family, a policy starting with a bias
root and anonymous legal action channels learned from selected-action terminal
valence. Primitive terminals were added as encountered; residual-ranked pair
scripts were born in shadow; only future-error-positive scripts acquired a
weighted SUB edge into the action-score root; and the exact resulting graph sum
both selected the action and supplied the prediction updated by credit.

The 54-point median paired ablation drop is direct evidence that the final
behavior was mediated by grown topology rather than merely accompanied by it.
The reset control establishes that the same terminal outcomes cannot train the
initial choice when its responsibility trace is discarded before reward.

## Limits and semantic correction

- This is builder-run development evidence, not independent confirmation.
- The four intervening events are elapsed environment-clock calls with no new
  observations, choices, or state dynamics. This is a delayed contextual bandit,
  not yet a genuine multi-state trajectory or key-door task. Calling it a full
  real-environment rollout would repeat the semantic error identified by the
  audit.
- Action scoring uses continuous terminal/AND activations and weighted graph
  edges. It does not yet exercise the formal REQUEST/CONFIRM state machine as a
  value or option controller.
- The host supplies literal terminals, legal action identities, episode
  boundaries, and scalar valence. It does not supply the answer, but ReCoN does
  not yet discover objects, actions, or its own curriculum.
- The reset control deliberately receives no terminal responsibility and is
  therefore a sharp temporal-credit control, not a competitive alternative
  learner.
- The task remains anonymous XOR with nuisance variables. There is no rare
  adversarial reply, lower-tail policy selection, recursive composition,
  reusable option, mid-run dynamics change, or cross-domain transfer.
- Mature-composite ablation reuses evaluation rows for paired measurement but
  performs no learning. Those rows are development data permanently.

## Decision boundary

Do not tune or rerun this package. The next gap is robust closed-loop choice:
the lower-tail return memory has passed isolated semantics but is not yet the
quantity used to select and update graph actions. A new package must freeze that
integration against a rare-refutation environment before adding key-door
sequences or returning to KRK. Independent reproduction remains necessary
before a confirmation claim.
