# Expert Follow-Up Context

This folder contains additional context for the second expert review round.

## How To Read This Bundle

The article and bridge demo are earlier proof-of-concept artifacts. They show that Hector already had an activation-driven endgame handover path, especially KPK to KQK, using an endgame gate, material/affordance sensors, weighted routing edges, and ReCoN activation dynamics.

They should not be treated as the final desired mechanism. Since then, the project has moved toward learned triplet curricula and compiled KRK micro-scripts. The current design question is how to evolve the existing bridge/gate/affordance machinery into a less hardcoded, more learned, more explicit architecture based on skill contracts and handoff packets.

## Folder Contents

- `article_bridge/`
  - AAAI article PDF and draft.
  - Bridge demo HTML.
  - Router bridge JSON artifact.

- `bridge_source/`
  - Existing endgame gate, affordance sensors, subgraph gates, unified graph builder, affordance-reward bandit helpers, and KPK/KQK handover tests.

- `krk_triplet_source/`
  - Newer KRK landmark/adaptive curriculum files and triplet-to-topology pipeline scripts.

- `krk_artifacts/`
  - Compact JSON artifacts from the latest clean Stage 5 KRK run and conversion diagnostic.

## Review Focus

Please advise how to evolve the existing bridge/gate/affordance machinery into the proposed skill-contract and handoff-packet architecture rather than assuming the project is starting from zero.

Important question:

Should the current `endgame_gate` become a generic `AffordanceHub`, or should it remain a top-level material/endgame router while each domain gets its own skill-level affordance hub?
