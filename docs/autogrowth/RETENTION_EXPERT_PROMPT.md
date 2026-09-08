# Independent expert review: retention in a developing ReCoN

Copy this document into a separate expert instance. It requests analysis, not
authorization to modify the repository or launch training. The evidence appendix
will identify the completed retention investigation when available.

## Your assignment

Critically examine retention and learning in Hector, a request confirmation
network (ReCoN). Do not simply approve the present direction, assume that a new
retention module is necessary, or reverse-engineer a chess solution. Recommend
the smallest generic, internally implementable next experiment. Separate what
the evidence establishes from your hypotheses and proposed architecture.

The long-term goal is a graph that grows useful topology from a top goal and
learns by acting: mate in one (M1), mate in two, full king-rook versus king,
then independently trained king-queen and pawn-promotion skills. A larger graph
should learn to request and coordinate independently trained subgraphs through
contextual affordance and outcome-grounded child value. Hand-coded material
switches are not the target. The immediate question is much narrower: why does
learning one M1 alternative sometimes lose another, and what should change next?

## Hard information boundary

- The environment owns the chess board and rules. It provides legal primitive
  action bindings. The graph observes only through its input terminals and acts
  only through an output terminal selecting one binding.
- The declared feature space is a fixed-length vector of heterogeneous scalar
  domains, not a board matrix. Geometry is allowed. A terminal can select a
  sparse subset; no graph-side side channel receives the whole vector.
- The current coach gives +1 for actual checkmate and -1 for failure after the
  submitted White move. It does not inspect the graph or imagined states to
  choose rewards, growth, pruning or consolidation. Curating exercises is allowed.
- No correct-action labels, mate distances, after-state scores, tablebases,
  authored mating predicates, pattern-specific growth rules or retention lists
  may enter learning. Offline diagnostic labels and fitted coefficients are
  never supplied to an actor.
- Generic local plasticity, birth/death laws and Boolean operators may be
  implemented in Python. That is an architectural prior, not automatically
  cheating. Report what is supplied and what is learned.
- Two atoms can be useless individually but useful together. Young compositions
  must be allowed to act and learn without first requiring individual maturity.
  Applicable history must survive retirement or a change of storage identity.

## Current narrow implementation

There are 16 Boolean or 0–7 coordinates: side to move, whether the bound actuator
moves the rook, absolute king file/rank separation, rook-to-opponent-king
file/rank separation, bound target-to-opponent-king and target-to-own-king
file/rank separation, separate opponent-king file/rank edge flags, target
file/rank alignment with the opponent king, and king file/rank alignment.
Target coordinates describe action parameters on the current board; the
feature adapter does not push hypothetical moves to evaluate consequences.
This is a substantial geometric prior, which must be acknowledged honestly.

Conditions are randomly proposed combinations of one to three equality readers
on distinct coordinates. Operators are AND, OR or exactly-one (called xor in
code; do not assume arbitrary-arity parity). Multi-reader operator probabilities
are 0.8/0.1/0.1. Individual terminals remain leaves. A shallow condition contributes
through signed SUR support to each action option when its readers confirm.
Definitions and their learned weights are shared across physical action-binding
copies. This is not yet arbitrary hierarchical factoring or learned symmetry.

For an option a, the effective score is

    q(a) = b + sum_j w_j * g_j(a),    g_j(a) in {0, 1}.

Formal request/confirmation computes the choice; without exploration it selects
maximum support with the existing deterministic slot tie rule. With probability
epsilon an internal exploration terminal makes a uniformly sampled legal binding
win. The actually selected option and actual reward determine credit. For M1:

    delta = eta * (reward - q(selected)) / (1 + number of active conditions)
    b_fast += delta
    w_j_fast += delta for each selected, active condition j.

This is selected-action scalar prediction-error learning. Please examine whether
that objective and its sampling distribution necessarily produce the action
rankings we want; do not equate existence of separating weights with convergence
of this update. There is no contrastive correct-action signal.

Current experiments use eta=0.3, a cap of 64 live shared conditions, two birth
attempts per episode when capacity permits, a 256-episode grace period and
pruning every 32 episodes when abs(effective weight)<0.02. The production default
cap is 96; do not confuse it with this experiment. Shared readers needed by
retained parents survive. Definitions of retired conditions and their statistics
persist, and identical live/retired definitions are excluded from random birth.
All current conditions remain TRIAL; there is no demonstrated maturity selector.

Fast and slow fields exist, but the ordinary path only transfers a fraction of
the bias's fast value to its slow value every 32 episodes. Effective sums and
ordinary condition updates remain unchanged. This is not evidence of functional
consolidation. Raw child activation is likewise not calibrated competence.

## Evidence before the current retention investigation

We are making a clean restart, not claiming to have solved M1, autonomous
structural discovery, handover or a world model. Tests establish the observation
boundary and formal computation. Birth is random; behaviorally useful weighted
compositions do not by themselves demonstrate adaptive proposal selection.

- An earlier condition ablation reduced a saved actor from 124/128 to 75/128
  without multi-reader contributions and to 4/128 without all condition
  contributions. This demonstrates dependence in that policy, not optimal or
  minimal structure, or reliable superiority of one growth method.
- A larger 64 versus 32 condition budget won four fresh-seed pairs and tied two
  at 1,280 training decisions. Continuing ordinary play also escaped some
  plateaus without a mechanism change. Neither effect guarantees retention.
- Holding topology fixed while continuing edge learning improved zero of 15
  earlier comparisons, tied twelve and worsened three. That was another set of
  histories; it does not prove all retention mechanisms ineffective.
- At 4,096 decisions, seeds 4/7/9 scored 128/126/111 on 128 development rows.
  Seed 9's 17 failures were all corner king separation (file,rank)=(2,1).
  Its graph admitted perfect ordering on each inspected split even though its
  actual policy failed. Separate-split feasibility was not a joint-set proof.
- Both epsilon=0.25 and epsilon=0.50 then received 2,048 additional training
  decisions on the same 256 training positions, with evaluations fixed in advance:

| Seed | Rate | 4,096 | 4,608 | 5,120 | 6,144 |
| --- | --- | --- | --- | --- | --- |
| 4 | .25 | 128 | 128 | 128 | 128 |
| 4 | .50 | 128 | 128 | 128 | 128 |
| 7 | .25 | 126 | 126 | 128 | 128 |
| 7 | .50 | 126 | 120 | 128 | 128 |
| 9 | .25 | 111 | 122 | 124 | 124 |
| 9 | .50 | 111 | 120 | 124 | 124 |

Seed 9 learned all 17 old failures but lost four previously solved corner
(1,2) rows, one symmetry orbit. Both arms have identical final solved/failed
partitions, not necessarily identical actions. These are new losses, not four
old residual failures. Seed 7 recovered its earlier losses; higher exploration
temporarily produced six additional losses before recovery.

Actual training had 160 corner-(2,1) opportunities and 232 corner-(1,2)
opportunities per arm. Seed 9 obtained 106/67 wins on the former and 167/130 on
the latter at .25/.50. Every corner training position won at least once in each
arm. Training and development symmetry orbits are disjoint: this does not prove
experience on the exact lost orbit. Raising exploration gave no final benefit
and reduced positive examples. Initial random states match, but exploration
changes later random consumption, so do not assume per-event RNG coupling.

An old authored corner AND/OR recognizer showed expressibility, not autonomous
discovery. Historical rank-first versus file-first edge helpers also existed.
The current adapter exposes both axes and both corner edge flags; that old
precedence/shadowing bug is not present in this active information path. Do not
copy the old corner rule into learning. Conversely, do not dismiss functional
duplication or missing useful joint features merely because many nodes exist.

## Questions to answer

1. Rank plausible explanations: inadequate current representation, destructive
   turnover, interference from the selected-action objective, policy-dependent
   exposure, constant step-size fluctuations, insufficient experience, missing
   reusable factorization/invariance, or something else. For each give a
   falsifier and distinguish retention from failure to generalize to an orbit.
2. Can the existing local rule resolve this without a new mechanism? What would
   demonstrate that its objective is conflicting with policy ranking, rather
   than just learning slowly? Which offline diagnostics are descriptive, and
   which prospective ordinary-play controls would establish causality?
3. Propose at most three minimal generic designs if the evidence warrants them.
   Specify equations, locally available inputs, state, timing and resource cost.
   Discuss signed weights, joint-only usefulness, young structures and preserving
   corrective learning. If proposing replay, say exactly what the organism stores
   internally from real terminal experience and reward; no laboratory buffer or
   answer extraction is allowed. If proposing consolidation, explain the actual
   behavioral protection and how it can later be corrected.
4. How should edge adaptation, growth and retention balance? Separate a concrete
   testable first mechanism from speculative adaptive learning rates. Do not
   globally freeze topology or introduce a coach-side “failed pattern” controller.
5. Keep future child competence/handover compatible with your design, but do not
   add a hierarchy just to patch four M1 rows. Distinguish goal value, availability,
   uncertainty and operational action confirmation.

Deliver: a concise diagnosis with confidence/unknowns, ranked design options,
one first experiment with unchanged/no-op controls and predefined success/failure
criteria, and what should not be added yet. Consider retention across learned
contexts, acquisition and compute, not just four targeted scores. If using
research, cite primary sources and identify analogies rather than assuming a
published result transfers to ReCoN. You may disagree with our interpretation.

## Repository and evidence pointers

Repository: https://github.com/Paulander/hector-recon

Work branch: `codex/residual-shadow-nomination`. `main` contains official guidance
and the restart baseline; it does not contain every experimental extension.
The pre-diagnostic exploration result is pinned at
`37e064ecbd6203163c8376c5a0882ed8070dbcae`.

Read `AGENTS.md`, `docs/autogrowth/ARCHITECTURE_CONSTITUTION.md`,
`docs/autogrowth/M1_RETENTION.md`, `docs/autogrowth/M1_EXPLORATION.md`, and
`src/recon_lite_hector/learning/terminal_development.py` on the work branch.
Reports are in `reports/autogrowth/development/`. Private checkpoints are not
in git. If access is unavailable, use this prompt and state that limitation;
do not claim to have inspected unavailable code or data.

At initial publication the new retention diagnostic is declared but unexecuted.
Its result appendix will be added below after the bounded run. Do not assume its
outcome from the hypotheses above.
