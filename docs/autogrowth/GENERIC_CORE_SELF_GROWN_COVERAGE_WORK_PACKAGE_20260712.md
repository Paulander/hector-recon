# Generic-Core Self-Grown Contextual Coverage Work Package

Date: 2026-07-12. Track: generic-core development. Status: PI-authorized and
frozen before implementation.

## Basis and question

The 2x2 ceiling showed that additive contextual pairs are sufficient:
exhaustive bounded coverage passed 18/20, sparse high gain passed 17/20, and
their combination passed 20/20. Sparse bounded topology covered only about 3/8
contextual components and failed.

Question: under ordinary [-1,1] bounds and a protected mastered baseline, can
the existing anonymous residual miner autonomously approach sufficient
contextual coverage when its local live ecology is expanded from four to eight?

Strongest null: extra capacity merely admits more arbitrary pairs; residual
ranking does not beat a matched-random ecology, coverage stays sparse, or any
coexistence gain comes from unequal topology/compute rather than informative
nomination.

## Common checkpoint

Use fresh seeds 20261801--20261820. Train 4,096 regime-0 episodes, evaluate 512
disjoint development rows, require joint success >=0.85 on all tasks, serialize
the complete state, and clone it into all arms. Freeze shared bias/primitives
byte-identically throughout phase 1.

## Exactly one capacity factor and selectivity control

All arms retain [-1,1] bounds, terminal-only outcome learning, 4,096 identical
regime-1 rows, proposal interval 128, support 16, 64-total lifetime bound, and
unchanged causal promote/prune gates. No candidate is injected or named.

1. **four-ranked:** current four-live residual-ranked ecology.
2. **eight-ranked:** eight-live residual-ranked ecology in door channels.
3. **eight-random:** eight-live matched-random ecology in door channels.

Key-action channels remain four-live residual-ranked. The two eight-live arms
have identical capacity, proposal timing, lifecycle, experience and policy RNG
budgets. Random nomination may consume its learner-local RNG; proposal counts
and opportunities must be matched and recorded.

## Measurements and gates

Record phase-0 mastery/clone parity, old retention trajectory at phase-1
episodes 512/1024/2048/4096, final old/new performance, separate topology and
candidate ablations, exact contextual coverage/sign/saturation, proposal
counts/states, shared hashes, clipping, action/observation digests, parity,
trial leakage and budgets.

Development support requires every gate:

1. eight-ranked median old/new joint each >=0.85;
2. at least 16/20 eight-ranked tasks achieve both >=0.85;
3. median old drop <=0.05;
4. median old/new topology effects each >=0.10;
5. eight-ranked per-task minimum(old,new) exceeds four-ranked on >=14/20 and
   eight-random on >=14/20;
6. median paired minimum advantage over eight-random >=0.10;
7. eight-ranked median contextual coverage exceeds both controls and reaches
   at least 6/8;
8. eight-ranked and eight-random have identical configured proposal intervals,
   observation opportunities, live/lifetime bounds and experience on 20/20;
   realized proposal counts are recorded but may diverge through lifecycle;
9. shared hashes, clone parity, graph parity, trial isolation, experience and
   resource bounds pass on 20/20.

## Interpretation and stop

- Ranked passes and beats random: self-grown nomination can use added ecology
  selectively; proceed only to confirmation/bridge planning.
- Both eight-live arms improve equally: capacity, not residual signal, explains
  the benefit.
- Ranked coverage rises but performance fails: bounded gain remains limiting.
- Neither improves: current miner/lifecycle cannot realize the proven ceiling.

Commit/push contract, runner and tests before fresh tasks; pass all suites and a
retired-seed smoke test; execute once. No tuning, injection, gain change,
confirmation, native integration or KRK claim is authorized.
