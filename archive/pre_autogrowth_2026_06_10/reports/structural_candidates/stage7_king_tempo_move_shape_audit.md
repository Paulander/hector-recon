# Stage 7 King-Tempo Move-Shape Audit

- Candidate: `cand.krk.box_shrink.king_tempo_handoff.v1`
- Causal status: `non_causal`
- Diagnosis: `king_tempo_contract_too_broad`
- Counts: {'probe_records': 8, 'probe_converting': 3, 'probe_nonconverting': 5, 'failed_sandbox_unique_moves': 2}

## Separating Terms

- Suggested required terms: ['compact_box_area_before_move', 'fence_survives_worst_reply']
- Suggested veto terms: ['box_area_large_before_move', 'king_moves_toward_rook_support']
- Converting common not failed common: ['compact_box_area_before_move', 'fence_survives_worst_reply']
- Failed common not converting common: ['box_area_large', 'box_area_large_before_move', 'king_moves_toward_rook_support', 'white_king_distance_to_rook_decreases']

## Interpretation

The failed sandbox did not prove the king-tempo idea wrong. It showed that the current contract is too broad: it fires in large-box states where the quiet king move does not produce conversion. The targeted converters are compact-box moves with worst-reply fence survival.

## Candidate Update

```json
{
  "schema_version": "structural_candidate_update.v1",
  "candidate_id": "cand.krk.box_shrink.king_tempo_handoff.v1",
  "candidate_status": "needs_contract_refinement",
  "diagnostic_labels": [
    "parameter_or_ontology_miscalibrated",
    "selected_successor_miscalibrated"
  ],
  "proposed_change": {
    "kind": "visible_move_shape_contract_refinement",
    "required_terms": [
      "compact_box_area_before_move",
      "fence_survives_worst_reply"
    ],
    "veto_terms": [
      "box_area_large_before_move",
      "king_moves_toward_rook_support"
    ],
    "notes": "The failed sandbox selected quiet king moves in large-box states. The targeted converters share compact box/worst-reply survival terms."
  },
  "promotion_status": "sandboxed",
  "causal_status": "non_causal",
  "credit": 0.0
}
```
