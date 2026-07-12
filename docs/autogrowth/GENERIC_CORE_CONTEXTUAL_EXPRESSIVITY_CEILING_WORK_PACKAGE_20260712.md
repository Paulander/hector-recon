# Generic-Core Contextual Expressivity Ceiling Work Package

Date: 2026-07-12. Track: generic-core development. Status: PI-authorized and
frozen before implementation.

## Predecessor diagnosis

The phase-split package proved mastery followed by forgetting and showed that
shared overwrite is causal. However, freezing shared weights yielded medians
0.938 old / 0.714 new and only 2/20 coexistence tasks. Contextual coverage was
typically 3/8 cue x regime x action components, with saturated weights and
frequent raw-score clipping. Responsibility allocation cannot solve a policy
that current contextual topology cannot express.

## Question and strongest null

Question: with a mastered shared baseline frozen, is coexistence limited by
missing contextual pair coverage, bounded contextual gain, both, or additive
pair expressivity itself?

Strongest null: neither exhaustive pair availability nor higher gain permits
coexistence; the required policy is not expressible by this additive contextual
adapter family, or any apparent ceiling comes from solution labels, mutable
shared weights, unequal experience, or post-hoc arm choice.

## Common checkpoint

Use fresh seeds 20261701--20261720. Train regime 0 for 4,096 episodes with the
unchanged broadcast learner, evaluate 512 disjoint development rows, and require
joint success at least 0.85 on all 20 tasks. Serialize/hash the complete state
and deep-clone it into every arm. If any task fails, stop before phase 1.

All shared bias and primitive weights are laboratory-frozen throughout phase 1.
This package is an expressivity ceiling, not an autonomous mechanism.

## Frozen 2x2 arms

Cross exactly two factors:

| Arm | Contextual topology | Parameter/output bounds |
|---|---|---|
| sparse-bounded | existing self-grown checkpoint topology | [-1, 1] |
| sparse-high-gain | existing self-grown checkpoint topology | [-4, 4] |
| exhaustive-bounded | exhaustive content-blind pair topology | [-1, 1] |
| exhaustive-high-gain | exhaustive content-blind pair topology | [-4, 4] |

For exhaustive arms, before phase 1 and without using correctness or hidden
mapping, ensure one mature zero-weight composite for every Cartesian product:

`door action x observable cue literal x observable regime literal`

This is eight pair adapters. Existing candidates remain. Missing pairs are
inserted as laboratory-authored mature adapters with zero weight; duplicate
mature pairs are not added. Their weights learn only from terminal outcome under
the unchanged legacy candidate update. No sign, target action, inversion,
reward, or solution label is supplied.

Higher-gain arms change both parameter and output bounds to [-4, 4], as one
predeclared diagnostic gain factor. Targets remain terminal +/-1. Shared weights
remain numerically frozen even though their values lie within the wider bounds.

## Training and measurements

Every arm consumes the same 4,096 regime-1 rows, policy RNG budget, legal-action
interface, and standard evaluation budget. Action-conditioned observations may
diverge and are hashed.

Measure:

- phase-0 mastery and checkpoint parity;
- old development performance after phase-1 episodes 512, 1,024, 2,048, 4,096;
- untouched final old/new joint, key, and door performance;
- separate old/new all-composite effects;
- individual candidate ablations;
- mature pair coverage, sign agreement, and saturation;
- raw shared/contextual contributions, output clipping, and parameter clipping;
- shared-weight hash before/after phase 1;
- action/observation digests, topology/resource counts, graph parity and trial
  leakage.

## Gates and deterministic interpretation

An arm achieves the expressivity ceiling only if:

1. median old and new joint success are both at least 0.85;
2. at least 16/20 tasks individually achieve both at least 0.85;
3. median old drop from phase 0 is at most 0.05;
4. median old and new all-composite effects are each at least 0.10;
5. shared weights are byte-identical before/after on 20/20 tasks;
6. exhaustive arms expose all eight mature pairs on 20/20 tasks;
7. clone parity, equal standard budgets, graph parity, trial isolation, and
   frozen source/resource bounds pass.

Interpret the first passing condition only descriptively; no arm is selected:

- sparse-bounded passes: the prior ceiling failure was sampling variation;
- sparse-high-gain alone passes: gain is binding;
- exhaustive-bounded passes: coverage is binding;
- exhaustive-high-gain alone passes: both coverage and gain are required;
- no arm passes: additive cue x regime pairs are insufficient.

Factor medians and paired task differences are descriptive diagnostics and
cannot relax a gate.

## Stop and claim limits

Commit/push contract, implementation, tests, and runner before fresh tasks.
Pass the complete core plus injection, frozen-shared, gain, checkpoint, and
runner tests. Execute once. Any exception, invariant failure, or post-generation
change closes the package without modifying coverage, bounds, maturity,
training, pools, or gates.

This package uses laboratory-authored exhaustive topology and an explicit phase
freeze. It can establish representational sufficiency only. It makes no
autogrowth, confirmation, native-substrate, or KRK claim.
