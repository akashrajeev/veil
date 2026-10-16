# Veil review map

A bounded synthetic demo of conversation-aware calendar disclosure. No public
release, project license, live Alexa integration or real booking is included.

| Claim | Mechanism | Evidence to inspect | Limit |
|---|---|---|---|
| Two individually harmless replies can reveal one fact together | Observer groups identical visible prefixes and recomputes exact support | Original comparison; `test_ordinary_demo.py` | Selected synthetic examples, not prevalence in real households |
| Guard checks the policy choice as well as the answer | Evaluate every output cell in the current compatible class before stepping | `engine.py`, `test_evidence.py`, independent `oracle.py` | Declared finite prior, one observer/one binary fact |
| Refusal cannot depend on the actual secret within the current class | Policy selected from the compatible class, not actual world | `run_spike.py`, full-visible dialogue tests | No private approval protocol implemented |
| Safe scheduling remains useful | Enumerate 64 ordered nonempty slot policies; maximize successful prior mass then minimize public cost | `test_weighted_optimum.py`, `measurements.json` | Exact only in this policy family; feasible actual meetings can still be declined |
| Replies are truthful, not merely privacy-bound-safe | Independent observer checks all supported calendar replies and every meeting | `test_truthful_queries.py`, false-answer CLI controls | Typed four-window answers, no general semantic correctness |
| Explanations/suggestions are counted as observable | Encode decision evidence and suggestions in replayed traces | `test_dialog.py`, `test_alternatives.py`, expanded replay | No timing/transport or collusion model |
| Saved history survives normal restart | Model-bound ledger replay; flushed atomic replacement | `test_restart_equivalence.py`, HTTP/state-fault tests | Local operator can edit/reset; no authenticated storage or rollback prevention |
| Downloads can be checked offline | Audit verifier; embedded exact imported input and complete result replay | `test_offline_cli.py`, browser downloaded-byte checks | Hashes are not signatures; input realism is not established |
| Assistant tool sequences cannot narrow the protected window | Group all 16 calendars by identical visible MCP transcripts; each group must stay exactly half free | `mcp_independence_check.py` length-3 run, `test_mcp.py` | One observer/one fact, typed vocabulary, simulated transport |
| Two windows can be protected jointly, not just per-margin | Guard preserves the full joint distribution over the 4-cell protected pattern; parity/XOR question admitted by any per-bit marginal guard is refused | `joint_engine.py`, `joint_check.py`, `joint_mcp_check.py` (uniform length-3 + weighted legs), `joint_composition_check.py`, `test_joint.py` | 1-2 protected windows; declared joint prior is the product of per-window priors (independence declared), not arbitrary correlations |
| Operator and assistant surfaces stay separated | Token-gated `/mcp-operator`; operator tools are Unknown tool on `/mcp` | `test_mcp.py`, `MCP.md` | Local demo token embedded in `/alexa`; not authentication |
| Simulated approvals leak nothing while pending or declined | Pending and declined results are identical for every calendar | `mcp_independence_check.py` approvals check | Simulated in-app channel; no message and no real person |
| Operator inference after disclosures matches the room's real posterior | Repeated-approval composition groups full visible transcripts and compares each group's fraction with the operator claim | `mcp_independence_check.py` composition mode (uniform) and weighted-composition mode (declared prior [1,3], weighted posterior) | Direct answers pause after a disclosure |
| Source ZIP can be reproduced and checked | Stable entry timestamps, source manifest, excluded local-state paths | `test_package_lab.py`, `package_lab.py --verify` | Archive hygiene/corruption checks, not authenticity |

## Inspect first

- QUICKSTART.md: short local hands-on path.
- VALIDATION.md: timestamped measured checkpoints, including fixes and caveats.
- README.md: full boundaries and earlier measurements.
- DEPENDENCIES.md: runtime and optional test dependency inventory.
- MCP.md: MCP endpoints, simulated client and approval path, with their checks.

## Key interpretation traps

- Zero support shift protects the declared fact only. Other details can be disclosed.
- A fact already certain in the prior is not made secret by zero further shift.
- NO_MEETING is a selected-policy result, not proof of actual infeasibility.
- Changing a public experiment limit is not private consent.
- Bob's known calendar must condition the prior before inference checks.
- The shared operator page intentionally shows synthetic fixture/configuration.
- Unsupported text uses a fixed refusal, not a model interpreting arbitrary prompts.
- The ordinary-query example is a deliberately correlated four-world prior.
- The `/alexa` page and MCP endpoints are a local simulation; no Amazon service or device is involved.
- An approved simulated disclosure pauses direct answers; that is a ledger-staleness guard, not a consent system.

## Research angle, not a novelty certificate

Private scheduling predates Veil. Its proposed demo angle is the observable
transcript-aware controller plus inference lens under an explicit bounded model.
The linked paper ideas are motivation, not replicated results, and the tests do
not establish a universal inference-prevention theorem. See README.md sources.
