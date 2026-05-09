# Prompt For External Expert AI

Please read the attached context files before answering.

We are building ReCoN-lite, a Request-Confirmation Network chess system. The immediate domain is chess, but the deeper goal is an explainable, self-organizing cognition architecture. KRK is our controlled proving ground, not the final goal.

Do not focus mainly on how to solve KRK. Instead, use the current KRK work to reason about the larger architecture problem:

- composing independently learned subgraphs,
- routing between them through affordances,
- designing handoff between endgame/tactic/strategy modules,
- deciding what internal terminals should monitor,
- governing stem-cell spawning, pruning, and consolidation,
- preserving explainability while scaling toward full-game chess.

We currently have strong local KRK skills through mate basin, edge traps, and fence establishment. The known weak point is not local one-ply skill selection; it is robust multi-step handoff/conversion and eventually composition with other subgraphs such as KQK, KPK, tactics, and middlegame plans.

Please give concrete design recommendations. Prioritize the next 2-3 architectural decisions and the next 2-3 implementation steps.

We especially need help deciding:

1. Whether to introduce an explicit affordance-routing layer now.
2. How to represent handoff between independently learned subgraphs.
3. How to design internal/meta terminals without over-engineering them.
4. How to govern online stem-cell spawning and pruning during gameplay.
5. How to structure reusable concepts so KRK, KQK, KPK, tactics, and later full-game play can share knowledge.

Please preserve the ReCoN philosophy:

- explainable graph structure,
- request-confirmation semantics,
- local terminals,
- inspectable activations,
- staged growth,
- eventual self-monitoring/self-referential control.

When useful, challenge the architecture. We want practical improvement suggestions, not affirmation.
