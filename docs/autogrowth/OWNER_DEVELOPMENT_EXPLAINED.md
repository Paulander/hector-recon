# What Hector can currently learn, and what remains missing

This explains the active September restart and the owner-development prototype.
Historical heuristic/handover demonstrations are separate evidence. The current
mechanism studies use a small Boolean task; the new ownership mechanism has not
yet been demonstrated in chess.

The latest [fivefold experiment](OWNER_NOMINATION_FIVEFOLD_RESULTS.md) changes the
interpretation of the initial short pilot. With more experience, unsplit/split
endpoints are 12/11 for seed 10 and 13/14 for seed 11, out of 16. Both split actors
solve all their earlier measured B successes at the final endpoint after returning
to mainly A, while each control has lost one. Seed 10 temporarily loses and recovers
one B row, and seed 11 keeps swapping A successes. This is mixed acquisition evidence
with an endpoint retention benefit, larger graphs and remaining failures. It does
not establish reliable protection.
The [short pilot](OWNER_NOMINATION_RESULTS.md), where every arm stayed at 8/16,
remains preserved with its qualified evidence audit; the longer run's verifier
passed directly.

## 1. Learning which action to choose

The environment supplies declared measurements through input terminals. SCRIPTs
combine their confirmations, and weighted SUR contributions give each legal action
a score. The formal choice node selects one binding; an output terminal executes
it. Only then does the environment return that action's scalar reward.

For one local decision:

    Q(s,a) = b + sum_j w_j phi_j(s,a)

Here phi_j is a confirmed Boolean condition, w_j its learned contribution, and b
the bias. Q is a prediction used to rank actions; it is not a supplied answer.
There are separate execution instances for action bindings, with shared learned
definitions/parameters where that ownership is intended.

If the prediction was Q and actual reward r, the prediction error is e=r-Q.
The existing rule gives the bias and each active contribution the same increment:

    delta = learning_rate * e / (1 + number_of_active_conditions)

This is a normalized local gradient step on the linear score. There is no
autograd/backpropagation through the Boolean gates or topology. The rule credits
participation in the chosen action; it does not know which participant caused
success. An inactive condition is not an observed counterfactual action outcome.

The observation/action boundary, score-based graph choice, event-bound feedback
and saved-state continuation have direct tests. Ordinary learning also improved
many M1 actors, sometimes after long plateaus. What it has not shown is monotonic
progress or general mate-in-one mastery across arbitrary positions.

## 2. Learning structure, and why the earlier version could forget

The older learner can propose terminal combinations and refine an individual
weighted contribution using a context G:

    w F -> w0 F NOT(G) + w1 F G, initially w0=w1=w.

Its nested AND/OR/exactly-one definitions execute as SCRIPT hierarchies. A split
starts with the old scores; subsequent rewards can specialize its two weights.
The recursive experiments demonstrated actual experience-guided refinements, but
also forgetting. Their generic nomination law is supplied code, not a growth
policy that the graph itself has learned.

The limitation is scope: other contributions remain shared. In the audited loss,
the specific B contribution survived and improved, while broader A competitors
strengthened enough to defeat it. Keeping B's own weight fixed would not protect
its action ordering. Total score can hide this: new successes can replace old ones.

## 3. What context ownership changes

The new operation gives each context its own complete local scorer, including all
competing contributions and its bias:

    Q(s,a) = (1-G(s)) Q0(s,a) + G(s) Q1(s,a).

At the split, both scorers inherit the existing parameter values. Afterwards,
only the applicable owner's parameters receive that outcome's credit. Its local
development rules also operate on that owner's structure. With fixed routing and
immutable definitions, this prevents direct updates in one context from changing
the inactive context's scores. Mechanical tests check this, including nested
splits, actual learning of both competing actions and restored continuation.

It does not protect two different situations that still fall into the same owner.
Nor does it guarantee that a proposed route is useful. Bad routing can partition
the wrong distinction or leave the important distinction unresolved. Future changes
to shared trainable representations would need their own protection argument.

An owner is currently runtime metadata tying together graph-executed contributions
and their credit/evidence. It is not yet a learned goal module with an independent
competence estimate or a self-programmed developmental controller.

## 4. The new step: choosing splits from experience

Previously we supplied G in mechanical tests. The new experimental class samples
candidate state-only conditions from its readers and existing definitions. Ordinary
SCRIPTs observe these on the current frame before action execution. The owner
records each candidate's truth value together with the original prediction error,
after the actual outcome arrives.

At a fixed local visit interval, it compares mean errors with G true and false:

    split_score = n0*n1/(n0+n1) * (mean_error1 - mean_error0)^2.

A positive difference with enough observations nominates a split if it fits the
budgets. It means "this distinction separates my past errors," not "this is the
correct solution" or "more structure is definitely necessary." Action selection,
exploration, changing weights and sample imbalance can all affect the statistic.
The environment does not tell the owner which phase it is in, where to split or
what it should have done. Candidate vocabulary and the developmental rule remain
supplied architectural choices.

When no split is made, the visited owner may propose a shallow composition. Aged,
weak local contributions may retire while their evidence remains recorded. Children
start new context-specific counts; parent evidence remains ancestry. All ordinary
weights stay plastic. No adaptive freezing/reopening rule is implemented.

The pilot exposed a missing coordination rule. Its split opportunities replaced
ordinary condition-birth opportunities, and newly divided children waited for
their own experience counts. Neither enabled actor acquired a new scoring feature
after conversion. Seed 10 began with no conditions that distinguished the actions;
copying them into contexts could not change that. Seed 11 had partial action
distinctions but still lacked enough to solve the task. Separating situations and
learning which action is better are different achievements. Both must remain
possible as development proceeds.

Fivefold experience gave the final children 112–617 visits and allowed new scoring
features to appear. That makes the short pilot an inadequate basis for dismissing
the mechanism. The longer audit found a more specific problem: 9 of 24 new
split-arm conditions cannot activate under their owning routes. For example, an
x=true context grew an x=false condition. These logical contradictions are
different from rare conditions that merely have not been observed yet. A generic
compatibility rule is now a more concrete target than immediately adding freezing.

## 5. Reuse is partly present; efficient shared hierarchy is still missing

Sharing an immutable expression definition is implemented. Sharing one physical
SCRIPT across incompatible requests is not allowed: execution ownership and frame
bindings must remain correct. The first ownership compiler repeats context-gated
contributions in the execution graph, so it does not yet build the one-copy common
trunk we discussed. It also copies scoring parameters when splitting.

Consequently the first mechanism buys isolation at extra cost. Common-subexpression
factoring, semantic duplicate handling, safe sharing of trainable structure and
deciding when two contexts should share learning remain separate problems. An exact
algebraic merge can preserve current scores while changing later credit dynamics.

SUB/SUR express hierarchical request/confirmation. POR/RET express temporal order;
greater specificity alone is not temporal order. Learned multi-step procedures,
goal arbitration, competence-based handover, imagination and a learned world model
are not demonstrated by this new owner prototype.

## How to read the pilot

`OWNER_NOMINATION_PILOT.md` declares a small enabled/disabled owner-splitting
comparison with the same local lifecycle, scalar rewards and resource ceilings.
The resulting `OWNER_NOMINATION_RESULTS.md` is the evidence record. This is an
intermediate test of the new runtime, not the full contributor-split versus
restructuring versus freezing comparison. A high toy score is useful development
evidence; gains, losses, failed nominations and cost determine the next engineering
question. The original learner remains a necessary baseline for that later study.

## Vocabulary

| Term | Meaning here |
| --- | --- |
| Policy | The rule the current graph actually uses to choose an action. |
| Reward | The scalar outcome of the action actually executed. |
| Prediction error / residual | Received reward minus the score predicted before acting. |
| Credit assignment | Deciding which participating parameters change after that outcome. |
| Plasticity | The ability of a parameter or structure to keep changing through experience. |
| Interference | Learning on one situation changes the action ordering in another. |
| Representational capacity | What the current expressions could rank correctly with some weights; distinct from what the learned weights do. |
| Context owner | One contextual decision's private parameters, local evidence and development scope. |
| Structure discovery | Selecting new combinations or partitions through experience under supplied generic development rules. |
| Factoring | Reusing a common computation instead of keeping separate copies; future credit must also remain well defined. |


## Context compatibility checkpoint, 2026-09-14

The next isolated increment is now tested: before installing a new condition,
the organism can check whether it contradicts the immutable context that owns it.
This uses only its own logical definitions and declared sensor domains. It does
not decide that an unobserved combination is impossible, nor decide which action
is correct. Unknown checks still permit the trial, under a bounded compute budget.

In the matched longer experiment, nine impossible births were avoided and both
learning trajectories stayed exactly the same. Graphs ended473→403 and557→531
nodes; scores stayed11/16 and14/16. This establishes a useful reduction in wasted
structure for these seeds. It does not resolve incomplete learning, shared-credit
interference, duplicate structure or retention. Those need separate increments.
See [the completed results](OWNER_COMPATIBILITY_RESULTS.md).
