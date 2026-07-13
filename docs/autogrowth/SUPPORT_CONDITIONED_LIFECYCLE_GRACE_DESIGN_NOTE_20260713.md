# Support-Conditioned Lifecycle Grace: Design Note

Date: 2026-07-13. Status: design for external adjudication only; not a frozen
work package and not authorization for fresh execution.

## Evidence requiring the next isolation

In the completed exact-evidence package, all targets were discovered and exact
measurement integrity passed, but the weakest target reached median retained
support only 7.5 at its first review and 12.5 at its second. Eighteen targets were
then pruned under the unchanged two-review rule with support 5--22. Exact requests
improved paired minimum support over activation in 14/20 tasks, but median gain
was only 2. Increasing exploration throughput would mix allocation dose with
lifecycle. The predeclared next factor is therefore grace conditional on local
support acquisition.

## Candidate generic rule

A trial below `min_eligible_support` should not consume unlimited life merely
because its deficit terminal is positive. At each review, the graph-local state
may expose:

- current exact retained support;
- exact support gained or lost since the prior review;
- whether its request SCRIPT emitted during the interval;
- a bounded remaining uncertainty/grace budget.

A candidate may defer unsupported pruning only while it is requesting and making
positive retained-support progress, subject to a frozen maximum review age. It
still receives no rent, reward, maturity, or exploitative root access until
support 32 and ordinary causal adjudication. Support loss through Algorithm-R
eviction reactivates deficit but cannot reset the lifetime cap. Mature candidates
remain ineligible to request.

This is locally measurable generic metabolism. The laboratory may audit the
trajectory but must not inspect target identity or decide individual extensions.
A likely causal comparison is current exact-directed two-review grace versus one
predeclared support-conditioned cap, with activation proxy, ordinary rent, and
fixed reference retained as controls. A grace-dose ladder or changed exploration
rate would add factors and should not be combined with the first test.

## Questions for external review

1. Should the cap be chosen from the observed acquisition rate (now development
   data) or from a generic resource budget independent of this task?
2. Should positive progress mean strictly increasing retained support at every
   review, or a bounded moving trend robust to reservoir eviction?
3. Should stalled candidates be pruned immediately after one no-progress review,
   or retain the original two-review protection inside the cap?
4. Is priority still a binding transfer gate in the grace package, or should it
   remain separately `not_identified` while evidence/maturation are tested?
5. What fresh contiguous seed range and cohort size should be frozen after this
   result and its rows are retired?

Do not implement or run this mechanism until those choices, arms, gates, and
fresh pool are independently frozen.
