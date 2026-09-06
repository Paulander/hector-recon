# ReCoN architecture constitution

Status: active from the 2026-09-06 restart. This defines the intended system,
not a claim that the current implementation has achieved it.

## Objective

ReCoN should develop useful topology and behavior through interaction. For the
chess line it begins with M1, progresses through M2 and outward KRK, then learns
KQK/KPK skills and contextual coordination between independently trained
subgraphs. Eventually, a larger ReCoN should learn which subgraph or plan to
request from contextual affordance and expected goal value. A material switch
or authored phase selector is not that capability.

The current restart establishes the substrate first. Its only architectural
claim is a clean information path: terminals observe and act, the graph decides,
and actual behavior produces scalar feedback. Whether useful topology can grow
adaptively and whether modules can hand over control remain open experiments.

## System boundary

Four roles must stay distinct:

### Environment

Owns the board, chess rules, legal action bindings, real state transitions and
observable outcomes. It may expose declared measurements and execute the exact
primitive action selected by the graph. Knowing chess rules is permitted.

It must not provide the learner with a correct move, mate distance, tablebase
value, successor score, hidden solution predicate or authored strategy. A future
opponent may choose its own moves using a declared policy; its private evaluation
does not become a learner input or reward.

### Generic embodiment and runtime

Provides the feature-port contract, input/output terminals, binding and frame
semantics, request/confirmation execution, generic Boolean/temporal operators,
plasticity and structural birth/death machinery. These are architectural priors,
just as an artificial neural network is supplied neurons and an update rule.

Python implementation is not itself external scaffolding. It becomes scaffolding
when task answers or undeclared environment facts enter policy, credit or growth.

### Learner and graph

Own learned readers, compositions, connections, weights, eligibility, hypothesis
history, competence/value and eventual delegation. Every environmental influence
on these decisions must arrive through terminal responses or action-bound scalar
outcomes. Internal graph state may influence the learner through explicit local
mechanisms; it must not be converted into a coach-side teaching oracle.

### Coach and laboratory

The coach selects exercises, lets the organism act and returns the observed
outcome. Current M1 gives +1 for actual mate and -1 for failure after the one
allowed White move. Later tasks may use final win/draw/loss and a declared small
speed term, but not correct-action or geometric shaping labels.

The offline laboratory may curate positions, verify pool properties, inspect the
graph and run interventions. Those facts must not influence online action,
reward, growth, pruning or consolidation. A test harness can establish evidence;
it is not part of the organism.

## Feature space and terminals

For one schema, the environment exposes a fixed-length vector with heterogeneous
coordinate domains. One coordinate can be Boolean, another a bounded integer,
another a normalized continuous value. This is not an m-by-n board matrix.

A terminal selects one or more coordinates or a region within their declared
domains. Different terminals may read different-dimensional subspaces. Geometric
coordinates such as piece distance, edge status and alignment are permitted.
Supplying them is a representational prior, so their task specificity and total
coverage must be reported. Supplying opposition, “this move mates,” a mate family
or a correct action would supply the solution and violate the target.

Input, output and internal terminals are leaves. A sensor implementation may
serve several terminal instances for efficiency only if each retains independent
request, binding and frame behavior. The policy does not receive a whole feature
vector through a side channel.

Two readers can have zero marginal value while their AND, OR, exactly-one or
later temporal composition is decisive. Trial composition must therefore precede
individual maturity. Useful shared readers survive while any retained composition
depends on them.

## Learning and structural development

Generic random proposals are allowed, but random birth is not adaptive growth.
Keep separate evidence for:

1. proposal or birth;
2. learned behavioral contribution;
3. experience-guided proposal selection;
4. survival or pruning;
5. reuse across contexts or tasks; and
6. causal effect on actual behavior.

Participation, correlation, prediction and counterfactual intervention are also
different evidence. Lifecycle names must reflect the evidence actually obtained.
Pruning removes current influence, not applicable history; an identical reborn
hypothesis must not appear naïve merely because its storage object is new.

Fast plasticity should support correction. Slow consolidation should preserve
something measurably useful without freezing the learner. A transfer between two
fields that leaves the policy and update law unchanged is not yet consolidation
in the behavioral sense.

## Goals, competence and handover

Request confirmation has local operational meaning. Confirmation by an action
chooser means that it selected an action, not that the environment goal succeeded.
A child module must learn a separate contextual estimate of availability,
expected goal value and uncertainty from real successes and failures.

The parent should receive child responses through ordinary internal terminals and
learn which child to request. Delegation must affect the actual selected behavior,
survive response permutation/disconnection tests and preserve independently
learned child skills. Raw activation magnitude, branch size, exploration bonuses
or a hand-coded material detector are not comparable competence values.

Joint experience will normally be needed to learn coordination, but this does not
imply erasing or jointly retraining the child policies. Plastic parent interfaces
and correctable child competence estimates are the intended separation.

## Temporal structure and virtual frames

POR/RET, internal terminals and virtual frames are generic mechanisms to add when
multi-step tasks require them. A virtual frame changes the state in which ordinary
terminals measure; it does not permit a hidden solver. Dream execution cannot
execute real actuators or create real reward, maturity or ground truth. Imagined
paths can propose or prioritize a plan, but final credit must ultimately connect
to observed outcomes or an already outcome-grounded child value.

## Evidence discipline

Mechanism tests, chess performance and architectural claims are separate. Tests
may plant structures to isolate expressivity. Training runs must report actual
moves and outcomes. Comparisons must include the null that best explains the
result, matched budgets where practical and independent seeds before general
claims. Physical graph replicas and shared learned definitions are reported
separately.

High validation thresholds can define scientific mastery or curriculum decisions;
they do not prevent an immature organism from acting and learning. Viewed rows are
development data. Preserve a final set until a configuration is deliberately
frozen. Negative results remain part of the organism's applicable experience and
the project's evidence.

Historical reports and the AAAI paper explain how the project arrived here. They
are a source of mechanisms and failure modes, not authority over this boundary.
