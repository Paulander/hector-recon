# TG28c Frozen Foundation Response Cache + Bridge Retrieval

Result: bounded pass as a diagnosis, not an edge/fence advancement.

TG28c built a memoized frozen-native foundation response cache and used it for bridge candidate retrieval evidence. The cache is not a provider: final candidate behavior remains mediated through native bridge/foundation-response/safety/actuator terminals and `FormalReConEngine` confirmation.

Key metrics:

- foundation frozen: true
- Mate_In_1 sanity: 1.0
- Mate_In_2 sanity: 1.0
- foundation cache states: 226
- cache/live mismatches: 0
- sampled basin states: 34
- foundation-positive basin states: 9
- foundation-negative basin states: 25
- bridge heldout: 4
- safe/cache-scored bridge candidates: 36
- bridge candidates with frozen-foundation response: 0
- selected moves: 0
- null moves: 4
- failure bucket: `safe_candidates_exist_but_no_foundation_response`

Interpretation:

TG28b's zero bridge response was not a side-to-move bookkeeping bug and not a cache/live mismatch. The frozen TG27b foundation recognizes known Mate_In_1/Mate_In_2 basin states, but it does not recognize the current edge/fence bridge candidate successors or reply-envelope states. The next checkpoint should not scale edge/fence. It should either build a better indexed foundation-response retrieval map over candidate successor states, or run a semi-frozen foundation adaptation pass on edge/bridge-produced continuation states while preserving the same ReCoN graph mediation boundary.
