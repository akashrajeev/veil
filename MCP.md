# Veil as an MCP server, plus a simulated voice-assistant client

Veil's disclosure guard is exposed as a self-hosted MCP server (JSON-RPC 2.0 over
Streamable HTTP, protocol 2025-11-25, Python standard library only).

This is NOT a connection to Alexa+ or any Amazon service or device. `/alexa` is a
simulated voice-assistant web client that calls the MCP server. Calendars are synthetic.

## Two endpoints, enforced separation

- `POST http://127.0.0.1:8765/mcp` - assistant surface. Tools: `veil_ask`, `veil_status`.
  Results contain only what the room hears plus an event count. Operator tools return "Unknown tool" here.
- `POST http://127.0.0.1:8765/mcp-operator` - demo operator surface, needs the `X-Veil-Operator`
  token the server embeds in the `/alexa` page (new each start). Tools: `veil_start_household`,
  `veil_operator_view` (guarded inference plus the unguarded counterfactual, which necessarily reveals
  the synthetic protected fact). Anyone who can load `/alexa` locally can act as operator; this is a
  local demo, not an authentication or recipient-privacy claim.

## Try it

    python3 server.py                  # terminal 1
    python3 mcp_client_demo.py         # terminal 2: initialize, tools/list, tools/call
    # or open http://127.0.0.1:8765/alexa

Supported requests: `is alice free for early prep|late prep|dinner|cleanup`,
`can alice cover exactly one of the two prep windows`, `find a shared window`.
Anything else is refused. This is a typed vocabulary, not natural-language understanding.

## Checks

- `python3 -m unittest test_mcp` - protocol, surface separation, HTTP origin/token checks, brute-force counterfactual.

The operator view also reports information gained so far (prior entropy minus current
posterior entropy) in the finite model under the session's DECLARED prior over the
protected window's binary free/busy variable: `information_bits.protected_window_bits`
(prior entropy H2(p0); max H2(p0)) and `information_bits.calendar_bits` for calendar
identity (prior entropy 3 + H2(p0): eight calendars per bit value, weighted by the
declared prior). `protected_window_prior_bits` and `calendar_prior_bits` report the
prior entropies the UI displays against. Both appear on the with-Veil view, the
without-Veil counterfactual and every approval preview. They are distinct quantities:
guarded answers can disclose calendar information while protected_window_bits stays 0 -
the guard's invariant until Alice approves. The default prior is UNIFORM [1, 1]
(H2 = 1 bit, identity 4 bits, count-based posteriors exactly as the composition check
compares them); the operator may declare non-uniform odds [busy, free] with integer
weights 1-9 on veil_start_household, and all readouts become weight-based. Exact contract: the
weights describe ONLY the protected bit's distribution - the other three calendar bits stay uniform
and independent, so this is not arbitrary correlated priors over the 16 calendars.
- `python3 mcp_independence_check.py 3` - exhaustive: approvals check (pending/declined paths identical for every
  calendar), then for every protected window, request sequence (length up to N) and all 16 Alice calendars,
  calendars with identical assistant-visible transcripts are exactly half free in the protected window.
- `python3 mcp_independence_check.py weighted` - the same grouping property under a declared NON-UNIFORM
  prior [1, 3]: same-transcript groups preserve the prior's weighted protected-window ratio exactly.
  Length 3 takes about 10 minutes.
- `python3 mcp_independence_check.py composition` - repeated-approval check: the operator-stated inference after
  approved disclosures must equal the room's real posterior, grouped by full visible transcript.
- `python3 negative_control_check.py` - negative control: wraps `mcp_server.handle` in-process only (server
  unchanged) so assistant-surface veil_status leaks the protected-window bit, then reruns the 'early prep'
  transcript grouping (7 request texts x 16 calendars, 112 runs). Passes only when the grouping flags every
  group, proving the independence check catches an injected leak every time. See VALIDATION.md.

These are separate routes: `verify_all.py` runs the unit suite and the correctness spikes;
`mcp_independence_check.py 3` runs the approvals check plus the exhaustive independence sweep;
`mcp_independence_check.py composition` runs the repeated-approval composition check;
`negative_control_check.py` runs the negative control. Together they reproduce every cited result.
- Interoperability was also checked once with the official MCP Python SDK client (not a dependency of this repo).

Limits: POST/JSON only (GET returns 405, no SSE stream, sessions, auth or batching); one conversation at a time;
one observer; a declared prior over the protected fact(s)' binary values only (default uniform); no private-approval path exists, so refusals just refuse.

## Joint protection (one OR two protected windows)

`veil_start_household` also accepts `protected_windows` (1 or 2 DISTINCT window names, instead of
`protected_window`) plus optional `priors` (one [busy, free] integer-weight pair per window, 1-9).
With two protected windows the guard preserves the full JOINT distribution over the 4-cell free/busy
pattern, not each window's margin separately. The declared joint prior is the PRODUCT of the per-window
priors (independence declared) - not an arbitrary correlated joint prior. The operator view reports
`protected_windows`, `joint_support` (per-pattern fractions, column order stated), declared priors, and
`information_bits.protected_joint_bits` (prior minus posterior entropy of the joint pattern) alongside
calendar-identity bits. The assistant surface never receives the joint support or configuration.

Why it matters: with {early prep, late prep} jointly protected, the question "can alice cover exactly
one of the two prep windows" (XOR of the two protected bits) leaves EACH window's margin exactly 50/50,
so any per-window (marginal) guard admits it - while its answer collapses the joint pattern to
[1/2, 0, 0, 1/2]. The joint guard refuses it. That question is the built-in parity negative control.

Joint checks (oracle implementations independent of the engine's joint_support - raw calendar bit
arithmetic plus exact fractions):
- `python3 joint_check.py` - engine-level: exhaustive joint sweep (6 protected pairs x 16 calendars x
  length<=2, uniform and weighted), parity negative control, utility comparison.
- `python3 joint_mcp_check.py` - assistant surface: groups by the FULL visible transcript (every ask
  result incl. refusals/suggestions plus final status); uniform length<=3 (38,304 runs) and weighted
  [1,3]x[2,1] length<=2 legs. (Use `joint_mcp_weighted.py` for the weight-normalized weighted leg alone.)
- `python3 joint_composition_check.py` - pre-disclosure uniformity, pending/declined approval-path
  calendar-independence, and post-disclosure: the operator-STATED joint must equal each transcript
  group's ACTUAL joint distribution; computed per-state utility; weighted entropy contract.
- Seeded-leak oracle control: a copied tree with the parity policy force-admitted is flagged by both
  the uniform and weighted checks (see VALIDATION.md).

`mcp_client_demo.py` runs against the live server and shows the assistant surface end to end:
guarded answers, a refusal, then the simulated approval lifecycle - request, pending, the
conversation moving on, the request going stale, and a fresh re-ask. Alice's decision side is
the SIMULATED operator panel or the token-gated operator endpoint; the client never touches it.

## Scenario input (operator surface)

`veil_start_household` accepts an optional `alice_calendar` (integer 0-15, default 7): a selectable
synthetic calendar - which of the 16 calendars in the declared finite model is the ground truth the guard
protects. This lets a reviewer rerun the demo against any of those 16 calendars without editing code. It
is operator-surface only; the assistant surface cannot set or see it. An optional `prior` ([busy, free]
integer weights 1-9, default [1, 1]) declares non-uniform odds for the protected window on the same
operator surface; every exhaustive check runs the default uniform prior unless stated, and the declared-prior
path is covered by unit tests plus the weighted check above. The /alexa operator panel exposes the calendar
choice (calendar + protected window selects, applied on 'start a new household'); Bob's side never shows it.

## Simulated private approval (optional path)

A refusal can be followed by `veil_request_approval`, which creates a pending request on a SIMULATED in-app
channel. No message is sent to anyone and no real person is asked. The operator panel (`veil_decide_approval`)
plays Alice and first shows what the room could infer if she approved. Pending and declined results are
identical for every calendar (tested exhaustively). If Alice approves, exactly that one answer is disclosed
and, because the guard's ledger no longer describes what the room knows, Veil then refuses all direct answers
until the household is reset; each further answer needs its own approval. Approval state is in memory only.

A pending request is bound to the conversation state Alice would decide on. If the shared transcript
advances (a new answer is given) or another disclosure is approved before she decides, the request goes
STALE: a terminal status that can never be approved and discloses nothing - ask again on the current
conversation. This is state-change invalidation, not time-based expiry; a connected deployment would add
a wall-clock TTL on top. Requests never survive reset (the request list is cleared) or reconnect (state
is in memory only), so an old request id cannot become valid again. The per-household limit is 8 PENDING
requests - Alice's decision queue. Decided (approved/declined) and stale records stay visible in the
operator panel but do not occupy the queue; retained records are bounded at 64.

Approval ids are opaque strings bound to the full household generation (`<generation>-<sequence>`), so a
delayed check/decide from an older household or an older process cannot target a reissued id, and browser
clients face no integer-precision limits. This is per-session simulation housekeeping, not authenticated
recipient or session binding: a connected deployment would tie requests to an authenticated recipient
channel instead.

## Designed next step (not implemented): multi-fact protection under a joint contract

Protecting several windows at once is NOT today's marginal check per window. Parity-style
requests can disclose a joint fact (e.g. the XOR of two protected bits) while each bit
individually stays exactly half free. The correct contract is joint uniformity: calendars
with identical assistant-visible transcripts must be uniform over the JOINT protected
configuration (all 2^k combinations equally likely), and the approval preview must price
joint information gain the same way. Implementation would generalize dialog.py's
single-bit protected variable, the session model and every exhaustive check; deferred to
keep the verified single-fact core stable.