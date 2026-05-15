# Architecture Preservation Note: Handoff Diagnostics and M1-M5

The handoff, role, and stagnation work extends observability and future growth evidence. It does not replace the older learning stack.

- `HandoffPacket` is trace evidence. It records confirmed terms, failures, selected routes, and continuation exports after ReCoN dynamics have already happened. It must not directly route or activate a skill.
- `ShadowStemCandidate` is a growth proposal. It can be queued and prioritized for offline review or later promotion, but it must not create durable nodes during gameplay.
- `SkillContractStats` is reliability evidence. It can be stored and exported, but it must not affect behavior unless a later milestone exposes it through visible TERMINAL/SCRIPT state.
- M3 is temporary within-episode plasticity. Fast edge deltas adapt behavior during an episode and are reset rather than treated as durable topology.
- M4 is slow cross-game consolidation. It consumes `EpisodeSummary.edge_delta_sums` plus episode reward/outcome signals to update persistent edge weights. Handoff diagnostics may travel as learning-event metadata without becoming consolidation inputs by themselves.
- M5 is topology promotion/pruning. Structural growth remains shadow/proposal/promote-only and offline until explicitly promoted; there is no live topology mutation during gameplay in the current handoff/stagnation milestones.
- Provider promotion records are also trace evidence. A `provider_promotion_event` may record that a versioned overlay passed guardrails, but the record itself does not promote topology or alter routing. Promotion remains an explicit offline M5 action.

Structural growth complements plasticity. M3/M4 adjust the strength of existing temporal/support structure, while M5 proposes or promotes topology changes when repeated evidence shows that the current graph needs new structure.
