# Joint-protection provenance (2026-10-14 late-evening IST lab candidate)

This file accompanies the single-fact PROVENANCE.md. Both contracts ship in this tree;
the single-fact results in the other files here are unchanged and still apply.

## Runs of record (joint contract)

| File | What | Result |
|---|---|---|
| joint.json | Gap measurement on the SHIPPED single-fact guard: 1,461 transcript groups, 777 with joint deviation - every case pins only the UNPROTECTED second bit (product working as designed); motivates multi-window protection | evidence |
| joint-engine-check.json | Engine-level joint sweep: uniform 4,032 runs + weighted [1,3]x[2,1] 4,032 runs, parity negative control (marginal admits / joint refuses), computed utility | 0 violations |
| joint-mcp.json (line 1) | Assistant-surface uniform sweep, length<=3, full visible transcripts: 38,304 runs, 5,810 groups | 0 deviations |
| joint-mcp.json (line 2) | FAILED weighted leg, count-vs-weight harness bug #3 - RETAINED as evidence, superseded by: | failed (oracle bug) |
| joint-mcp-weighted.json | Corrected weight-normalized weighted leg: 5,376 runs, 673 groups | 0 deviations |
| joint-comp.json | Composition (pre/pending-declined/post-disclosure 120 groups), computed utility (47 states), entropy contract | all pass |
| leak-weighted.json + uniform probe | Seeded-leak oracle control (parity force-admitted on a copied tree): weighted 60/700 groups flagged, uniform probe 2/2 flagged, posteriors match manual [2/5,0,0,3/5], [0,6/7,1/7,0] | oracle catches leak |

## Harness bugs found and fixed (oracle-side only; no engine change resulted)

1. Composition pre-check grouped by full transcript INCLUDING approved disclosures and
   tested the pre-disclosure prior (wrong expectation; post-check was correct).
2. Pending/declined uniformity compared transcripts that included calendar-dependent
   guarded prefixes (approval messages must be compared alone).
3. Weighted sweep compared raw calendar COUNTS against the WEIGHTED declared prior
   (the retained 673/673 failed run; fixed by weight-normalizing).

## Source provenance

- MCP uniform sweep started 22:56:56 IST against mcp_server.py sha256
  1142c3cdfba023a2129e72f5d220b3aaf7b80f805ef40c0857cf32629df3ffa5 - RECONSTRUCTED
  (reversed the 23:00 operator-readout patch, verified by re-application; NOT captured at start).
- The 23:00 patch touched only operator-view readout code (joint_information_bits,
  joint_unguarded_view, Session._view_joint/preview); assistant-surface code unchanged
  (per-line diff). Bridge: 672 runs on the post-patch server, 0 deviations - the bridge
  is NOT a full post-patch sweep.
- Final packaged tree: see zip header note and git-agnostic tree hash below; the packaged
  mcp_server.py sha256 is 202f8c0b970cf09351cb882fb5c5d9f0a367eca2849bc51e93f5256f3c41de8d
  (docs/legend edits after the sweep do not alter server behavior).
- Weighted corrected leg + composition + leak controls ran against the packaged
  mcp_server.py (202f8c0b...) except where a file is labeled otherwise.
