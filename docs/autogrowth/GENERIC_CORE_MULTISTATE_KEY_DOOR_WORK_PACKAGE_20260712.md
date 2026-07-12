# Generic-Core Multi-State Key-Door Work Package

Date: 2026-07-12. Track: generic-core development. Status: authorized and
frozen before implementation.

## Scope correction

The estimator repair passed, and the PI authorized proceeding to key-door.
This package isolates the next unestablished mechanism: actual multi-state
responsibility. It does not combine lower-tail risk adjustment into contextual
composition yet, because doing so would add a second untested scientific factor.
Robust one-state choice remains separately certified development evidence.

## Hypothesis

The unchanged graph-grown episodic policy can learn a two-decision anonymous
key-door task from terminal-only valence when actual selected graph
responsibility persists across the action-dependent transition. The same policy
with its trace cleared at the transition will learn the terminal door decision
but cannot reliably learn the earlier key decision.

The persistent learner will retain its first-regime competence after a visible
mid-run regime change while acquiring the new door mapping in grown topology.

## Strongest null

Success comes from host action targets, stage or regime labels encoding the
answer, intermediate reward, unchanged observations, evaluation reuse, direct
Python choice, primitive marginal shortcuts, topology that does not affect
behavior, or a reset control with unequal experience/compute.

## Learner/laboratory boundary

The learner receives:

- anonymous active terminal IDs at each state;
- anonymous legal action IDs for that state;
- its exact graph action scores and selected activation responsibility;
- one real transition event after the key action;
- terminal scalar valence only after the door action.

It does not receive correct key/door identity, XOR, success predicates, regime
meaning, task seed, stage names, transition answer, evaluation results, or
intermediate reward.

Legal-action sets and terminal valence are environment interfaces. The
laboratory may report hidden identities only after the run.

## Exactly one factor

- persistent arm retains the selected key trace across the action-dependent
  transition and credits both selected decisions at terminal;
- transition-reset arm clears responsibility after the key transition and
  therefore credits only the selected door decision.

Both arms have identical graph code, candidate law, learning rates, exploration
draw budget, observations, legal action sets, episode count, terminal outcome
function, phase order, topology budget, and evaluation rows.

## Frozen environment

- 20 tasks, seeds 20261001–20261020;
- four anonymous legal actions: two key actions and two door actions;
- key state: two hidden signal bits plus two nuisance bits, one literal terminal
  per bit; correct key is randomized/inverted XOR;
- transition state records the actually selected key through one of two
  anonymous carried-object terminals;
- door state: carried-key terminal, one door-cue bit, two nuisance bits, and one
  anonymous regime terminal;
- terminal success requires both the correct key and the correct door;
- regime 0 door mapping uses the cue; regime 1 inverts it;
- 4,096 regime-0 training episodes followed by 4,096 regime-1 episodes;
- no regime-0 replay after the change;
- 512 untouched regime-0 and 512 untouched regime-1 evaluation episodes;
- no intermediate reward or host-selected action.

The regime terminal makes the changed dynamics observable but does not encode
which action is correct. This tests contextual acquisition and retention, not
unannounced nonstationarity.

## Frozen learner

- the graph-backed episodic composition implementation from `9646ded`;
- the online-composition configuration frozen at `9f601cd`;
- epsilon-greedy exploration 0.15 and discount 0.97;
- maximum four candidates per action;
- residual-ranked pair proposals, shadow trials, future paired-error/resource
  survival, mature AND-script root edges, and no recursive composition;
- graph score used for choice must equal the prediction updated at terminal;
- legal-action filtering may only restrict which environment-provided action
  channels are scored; it may not rank or label them.

## Measurements

- joint episode success by regime and arm;
- key and door decision accuracy separately;
- full graph versus mature-composite-disabled paired evaluation;
- regime-0 retention after regime-1 training;
- credited trace lengths and decision counts;
- graph/update mismatches and trial-root leakage;
- per-action candidate lifecycle, hidden signal/regime-pair diagnostic, node and
  edge counts;
- matched action-score, RNG-call, episode, and candidate budgets;
- source, implementation, runner, transition-row, and evaluation hashes.

## Gates

Development support requires every gate:

1. persistent joint success exceeds reset on at least 16/20 tasks in both
   regimes;
2. persistent median regime-0 joint success after all training is at least 0.85;
3. persistent median regime-1 joint success is at least 0.85;
4. persistent median key accuracy is at least 0.90 in both regimes;
5. median persistent full-minus-composite-disabled joint success is at least
   0.15 across the two regimes;
6. at least 16/20 persistent tasks mature a hidden key signal pair and a hidden
   door cue/regime pair;
7. graph/update mismatches and trial-root leakage are zero;
8. configured experience, legal-action, RNG-call, and candidate budgets match
   on 20/20 tasks.

## Stop rule

Lifecycle tests may not generate frozen seeds. Commit and push contract,
implementation, and runner before task generation. Execute the frozen range
once. Any failed gate closes this package without tuning, additional phases, or
KRK transfer. Builder-run evidence is not independent confirmation.
