## 2026-10-15 00:30 IST restart-persistence checkpoint

- restart_check.py (ships; real HTTP server, real .state file): build a session over the
  operator+assistant MCP surfaces (answer + uniform refusal recorded), hard-kill the server
  process, restart it, and verify the SAME session is still guarded: identical generation
  (056d6d51...), events (2), config (protected window early prep, calendar 7), alive
  calendars, information bits, unchanged refusal ("I can't answer that."), deterministic
  next answer. All 7 checks passed; artifact validation-results/restart-check.json.
  Scope: single-window default config; joint configs and approval-state persistence across
  restart are NOT covered by this check.
- Draft state-persistence claim promoted only after this test, citing it by name.

## 2026-10-15 00:25 IST attach-sync + honest-error checkpoint

- HONESTY FIX (reviewer catch): the fail-closed error text previously said "Nothing was
  started or reset" - an overclaim, since a failed/malformed RESPONSE can mean the request
  committed but the transport failed. The error now states the honest epistemic position:
  "Could not confirm the household session state - the check may not have reached the server,
  so the session state is unknown. No automatic reset will be attempted. Retry re-checks
  first: it attaches if a session exists and starts one only if none does." Verified by
  route-intercepted malformed-response test: the error renders and zero plain (unsafe) start
  calls are issued.
- ATTACH CONFIG SYNC (reviewer requirement): a tab that attaches to an existing session used
  to show its OWN default selects (calendar 7, single-window) even when the active session
  was configured differently - the controls looked authoritative while describing nothing.
  On attach, the scenario selects now sync from the operator view (active calendar,
  protected window(s), declared priors; joint sessions populate the second window + its
  prior). Select values outside the offered options are left untouched rather than
  mis-set. Verified live: tab1 starts joint (early+late); tab2 attaches and its controls
  show early prep + late prep - the ACTIVE configuration. The "applies on 'new simulation'"
  note continues to cover mid-session select edits (changes are pending until the operator
  explicitly starts a new simulation). operator() now returns the view on both exits so the
  sync and the panel read the same response.

## 2026-10-15 00:20 IST ensure-initialized checkpoint (race actually closed)

- FINDING (preserved, replaces the earlier too-mild wording): the v3/v4 boot design had TWO
  real defects. (1) The drift fallback (start when status was missing or the events count was
  absent) FAILED OPEN: an unrecognized or failed status response could trigger a start that
  resets a live answered session. (2) The two-call check-then-start was not atomic: a delayed
  second first-boot could read initialized===false before the first tab's start, then start
  AFTER the first tab's answer had landed - erasing that answer from the ledger. Not
  harmless; both are closed below.
- FIX:
  - Server: veil_start_household accepts only_if_uninitialized (boolean, schema + validated).
    When true, the handler checks and starts ATOMICALLY under the existing process lock: if a
    session exists it returns {already_running: true, events: N} and does NOT reset; if none
    exists it starts. Assistant surface untouched (operator tool only).
  - UI: boot makes exactly ONE operator call - veil_start_household with
    only_if_uninitialized=true - and branches on the response: already_running -> attach
    notice with the heard-count; fresh start -> new-simulation notice; anything else
    (transport failure, error, malformed shape) -> "Could not verify the household session.
    Nothing was started or reset." plus a retry control whose only action is the same
    check-first ensure call. No code path from an unrecognized response leads to a start.
  - The explicit reset stays an operator-only control and says so in the page
    ("new simulation (operator-only control)").
- TESTS:
  - Unit (test_mcp.py): ensure starts on empty state; ensure after an answered question
    returns already_running with events=1 and preserves the session generation (a differing
    config in the ensure call does NOT alter the running session); plain start without the
    flag still resets; only_if_uninitialized must be a boolean.
  - Driven (external harness, not shipped): startA -> answerA -> delayed bootB attaches with
    the same generation (543bd376... observed identical before/after), tabA reload attaches,
    malformed ensure response renders the fail-closed error + retry and issues ZERO plain
    start calls. 390px viewport: no horizontal overflow.
- SCOPE NOTE: mcp_server.py's hash changes with this checkpoint. The change is additive to
  the OPERATOR start path (new optional arg + early-return branch); the assistant-surface
  request/response behavior exercised by the exhaustive sweeps is untouched, and the sweeps'
  recorded bounds reference the earlier hash as labeled in their artifacts.

## 2026-10-15 00:10 IST concurrency + process-log checkpoint

- CONCURRENCY: all MCP tool calls (assistant and operator surfaces) are serialized under one
  process lock (server.py LOCK around mcp_server.handle), and session writes are atomic
  (tmp file + fsync + replace). Tested: 20 concurrent veil_start_household (operator) x 20
  concurrent veil_ask (assistant), fully interleaved - 40/40 responses isError:false, state
  file valid JSON afterwards. Concurrent first-ever boot from two tabs on an empty state:
  both tabs pass the initialized===false check and both start (last-writer-wins); with
  identical default selects both starts create the same household and both tabs converge to
  one consistent shared session (verified: after a question in one tab, both attach views
  report the same heard-count and identical operator readouts). RESIDUAL SCOPE: if two
  first-booting tabs used DIFFERENT operator selects, the last boot's configuration wins; the
  losing tab's operator view reflects the winner's actual configuration on refresh, and the
  transcript announces the active configuration - operator confusion is possible, a split or
  corrupted ledger is not (single shared session, serialized writes). No silent weakening:
  the enforced configuration is always the one displayed.
- BOOT GUARD SOURCING: the attach decision keys on the real, unit-tested contract
  (test_status_before_start_and_after pins veil_status -> initialized===false on empty
  state). The guard starts a household only when status is missing, initialized===false, or
  the events count is absent (contract drift) - it never resets on an unknown-but-initialized
  shape; drift fails toward a fresh start, not toward wiping a session.
- BOUNDS CLARIFICATION (cross-epoch enumeration): the 7,136-pair result covers length-2
  histories split across two epochs over the typed vocabulary and the 38 checked
  configurations. It does NOT enumerate longer histories, multi-epoch splits, or
  configurations outside the checked set; the fix (boot attach) is what removes the reset
  vector, the enumeration bounds what the vector could have composed.
- PROCESS LOG (discarded run, not green): at ~23:59 a verify_all run reported "Ran 230 tests,
  OK (skipped=2)" because the demo server was still holding port 8765, which contaminated
  server-dependent test collection. That run is DISCARDED - not cited as a pass anywhere.
  The recorded green for v3 is the clean rerun with the port free: 234 unit + 12 spike, all
  rc 0. Lesson recorded: verify_all must run with the demo server stopped.

## 2026-10-15 00:00 IST session-attach checkpoint (UI ledger persistence + cross-epoch enumeration)

- FINDING (UI-level, reported by reviewer): every page load used to call veil_start_household
  with the select defaults, wiping the single shared server session's ledger on reload AND on
  any new tab, while the operator view then claimed 16/16 calendars and 0 bits for a room that
  had already heard answers. Ground truth (the selected synthetic calendar) persisted across
  the wipe. test_restart_equivalence did not cover this (it tests server-restart persistence,
  not UI boot behavior).
- CROSS-EPOCH SAFETY ENUMERATION (cross_epoch_check.py, in-process MCP handler, assistant
  surface): for all 38 configurations (single: 4 protected windows x 5 priors; joint: 6 window
  pairs x 3 prior combinations) x all 16 calendars, computed the fresh-safe set F (questions
  answered on an empty ledger), then tested every ordered pair (a1, a2) in F x F in ONE
  session: 7,136 ordered pairs, 0 pairs where a2 is refused after a1 while both are fresh-safe.
  Bounded result: within the typed request vocabulary, splitting questions across a UI reset
  cannot compose a pair the same-session guard would have refused. This is a statement about
  the checked configurations and vocabulary, not a general impossibility proof; calendar-
  identity bits (a displayed, non-protected quantity) DO compose across resets.
- FIX (UI only; engine and joint contract untouched):
  - boot() now ATTACHES to the existing household: it checks veil_status (assistant surface,
    returns scope + answered-count only - no calendar data crosses the assistant/operator
    boundary) and starts a household only when none exists (initialized === false). On attach
    it states how many answers the room has already heard and that the ledger still counts
    them; the operator view refreshes from the real session, so reloads and new tabs show the
    true remaining-calendars state instead of a false 16/16.
  - Driven-UI regression (external Playwright-core harness, not shipped): reload after an
    answered question keeps 8/16 alive and the same bit counts; a second tab attaches without
    resetting (shared session, counts advance consistently across tabs); the explicit reset
    still works. 390px viewport: no horizontal overflow.
  - Reset relabeled to an explicit operator action: "new simulation (operator reset)" with the
    in-UI statement that it starts a NEW SIMULATION - the model treats the room as a fresh
    observer and excludes the prior conversation; it is not a privacy reset, and a real room
    would still remember. The operator-selected calendar stays selectable (no silent
    re-randomization of ground truth). Result artifact:
    validation-results/cross-epoch-pair-check.json.

## 2026-10-14 23:45 IST reviewer-build UI checkpoint (autoplay removed, XOR suggestion)

- REMOVED all URL-hash boot automation from alexa.html: the legacy `#autoplay` branch and
  the three screenshot-harness branches (`#joint-demo`, `#joint-approve`, `#joint-approved`)
  added during lab validation. Reviewer builds must not reset state or approve requests
  from a URL hash; screenshot/test automation lives outside the product (external
  Playwright-core driver, not shipped). Exact behavioral diff: boot() no longer reads
  location.hash; page load always performs the same normal boot (fresh single-window
  household). Driven-UI verification after removal (external driver, system Chrome):
  normal boot == #joint-demo boot (identical transcript); joint flow via real clicks
  (select second window -> start -> click XOR suggestion) refuses with "I can't answer
  that."; with-Veil pattern stays quarters (0 of 2 bits) while unguarded collapses to
  [50%,0,0,50%] (1 of 2 bits); mobile 390px full page has no horizontal overflow
  (scrollWidth check), suggestion row wraps, same click flow works; reload boots clean
  (fresh household by design; ledger persistence is covered by test_restart_equivalence).
  One benign /favicon.ico 404 (no favicon link in page; pre-existing).
- Suggestion row gained the XOR question as a one-click button (previously type-only).
- Legend is joint-aware: "the protected window(s) - one or two, per the scenario selects".
- validation-results/utility-table.json added: admission vs usefulness measured separately
  (bounds stated); the {early prep+dinner} degenerate config (bob's shared windows exactly
  the protected pair: admitted 96/96, meeting returned 0/96) is documented as the visible
  privacy/utility tradeoff, not hidden by a "scheduling never lost" claim.

## 2026-10-14 23:30 IST joint multi-window protection checkpoint (lab candidate)

New contract: an operator may declare ONE or TWO jointly protected windows; the guard
then preserves the full JOINT distribution over the protected free/busy pattern
(budget 0 = exact), not each window's margin. Declared joint prior = product of the
per-window declared priors (independence declared). Fresh results on this tree:

- `joint_check.py` engine-level: uniform 4,032 runs and weighted product prior
  [1,3]x[2,1] 4,032 runs (6 protected pairs x 16 calendars x length<=2), 0 joint
  violations. Parity negative control: per-bit marginal guards both ADMIT the XOR
  question ("can alice cover exactly one of the two prep windows") while the joint
  guard REFUSES it (answer collapses the joint to [1/2, 0, 0, 1/2]).
- `joint_mcp_check.py` assistant surface, grouping by FULL visible transcripts:
  uniform length<=3, 38,304 runs, 5,810 groups, 0 deviations. Weighted leg
  (`joint_mcp_weighted.py`, weight-normalized): 5,376 runs, 673 groups, 0 deviations.
- `joint_composition_check.py`: pre-disclosure uniformity 0 violations; pending/declined
  approval paths calendar-independent; post-disclosure 120 groups, operator-STATED
  joint == actual joint, 0 mismatches. Computed utility over 47 reachable states:
  dinner/cleanup/shared-window admitted everywhere; protected direct asks and the XOR
  question refused everywhere (the XOR output IS a joint-pattern function).
- Entropy contract: product prior [1,3]x[2,1] = 1.73 bits (matches manual); safe answers
  keep protected_joint_bits exactly 0.0 while calendar identity moves.
- Oracle independence: harnesses compute group distributions from raw calendar bit
  arithmetic + exact fractions, NOT the engine's joint_support. Seeded-leak control on
  a copied tree (parity force-admitted): uniform probe flags 2/2 groups; weighted check
  flags 60/700 groups with measured posteriors [2/5,0,0,3/5] and [0,6/7,1/7,0], matching
  manual computation; counts ([1/2,0,0,1/2]) differ from weights as designed.
- Harness bugs found and fixed during this checkpoint (preserved, not rewritten): (1)
  post-approval transcripts wrongly held to the pre-disclosure prior; (2) pending/declined
  uniformity compared transcripts including calendar-dependent guarded prefixes; (3)
  weighted leg compared raw counts against the weighted prior (the 673/673 failed run is
  retained in validation-results). All three were oracle-side; no engine change resulted.
- Provenance: MCP sweep started 22:56:56 IST against mcp_server.py sha256
  1142c3cdfba023a2129e72f5d220b3aaf7b80f805ef40c0857cf32629df3ffa5 (RECONSTRUCTED by
  reversing the 23:00 operator-readout patch, verified by re-application; not captured at
  start). That patch touched only operator-view readout code; a 672-run bridge on the
  post-patch server (hash 202f8c0b970cf09351cb882fb5c5d9f0a367eca2849bc51e93f5256f3c41de8d)
  showed 0 deviations. Full sweep re-attachment to the final packaged tree is recorded in
  validation-results/PROVENANCE-JOINT.md.


## 2026-10-14 06:37 IST correctness checkpoint

Fresh `python3 verify_all.py`: 155 unit tests and 12 correctness-spike tests,
all passed. The independent observer now checks every emitted meeting in a
trace, rather than only the last meeting. A negative control with an unavailable
first meeting followed by an available final meeting is detected. Malformed
or out-of-range meeting outputs count as invalid instead of crashing the checker.
This repaired a verification gap; no controller-generated invalid meeting was
observed in this checkpoint. Storage-fault controls cover intent preview and
saved-dialogue audit, with JSON 503 responses rather than disconnected requests.
No visual layout or privacy scope changed.

## 2026-10-14 06:46 IST import/audit validation checkpoint

Fresh `python3 verify_all.py`: 161 unit tests and 12 correctness-spike tests,
all passed. Dialogue audit metadata must now match its protected-slot bit,
prior weights, calendar keys and complete 16-world observer-conditioned domain.
The declared hash and dialogue configuration are required. This catches
accidentally mislabeled artifacts; it is not authentication or a real-world
prior check. Generic guarded artifacts continue to verify their declared model.
Zero-denominator rational budgets are rejected as validation errors in the
engine, saved ledgers, offline audit files and JSON experiment imports. An HTTP
import carrying `1/0` returns JSON 400 rather than dropping the connection.

## 2026-10-14 07:06 IST clean extraction checkpoint

A fresh deterministic source ZIP was extracted into a separate clean directory.
`python3 verify_all.py` completed there: 164 unit tests plus 12 correctness-spike
tests, all passed. Its 64-entry source manifest verified. No existing local
session, installed Node dependency or repository metadata was bundled. The
source-package hash checks accidental corruption, not authenticity. Git is
needed only to create a package from a checkout, not to run the application,
default tests or check an already-created ZIP.

## 2026-10-14 07:18 IST answer truthfulness checkpoint

The independent observer now checks the four supported Alice availability reply
formats and the two-prep-window parity answer against each declared world's
calendar, in addition to checking every emitted meeting. An injected false parity
answer in all 16 observer-compatible worlds can have zero protected-fact shift;
the offline verifier nevertheless reports 16 invalid calendar answers and exits1.
Privacy-bound adherence does not establish answer truthfulness.
The 64-model adaptive depth8 sweep passed 1,024 world traces with zero bound
violations, invalid meetings or invalid calendar answers. This is sampled finite
model evidence, not coverage of every adversary or real prior. No UI change.

## 2026-10-14 07:29 IST model invariance checkpoint

Seeded finite-model tests passed under global positive prior-weight scaling,
world-key relabeling/reversal and positive public-cost scaling. These changes
preserve emitted policy/answer events and posterior support where tested; scaled
public evidence weights/cost numbers are allowed to differ. This checks exact
arithmetic and identity/order independence, not equivalence of real priors.
The malformed synthetic-input sweep again rejected all 500 seeded mutations.
Fresh default verification passed 170 unit tests plus12 correctness-spike tests.

## 2026-10-14 07:40 IST offline operator workflow checkpoint

Fresh verification passed174 unit tests plus12 correctness-spike tests. Actual
subprocess controls cover valid audit success (exit0), observed false answers or
bound violations (exit1), and invalid/missing input (exit2 with readable error,
no traceback). A 16MB file bound applies before offline audit parsing. This
bound protects the local demo workflow; it is not a security certification.

## 2026-10-14 08:00 IST expanded observer replay checkpoint

All four bounded expanded-vocabulary batches completed with the strengthened
independent truthfulness checker:343 length-three orders,16 resident classes,
5,488 class-sequence checks and87,808 world traces. Zero declared-bound violation
cells, invalid meetings or false supported calendar replies. The original
three-intent/four-step sweep also passed20,736 traces and1,296 checks;60 seeded
weighted-audience trials passed908 checks. The public-prior-only negative control
still yields32 unsafe conditioned cells; resident-conditioned protection yields0.
These are bounded finite-model replay results, not all priors or unbounded proof.

## 2026-10-14 08:11 IST browser/download checkpoint

Restarted the local server from current source. Original comparison, expanded
feature path and keyboard regressions passed. Fresh390/320px feature screenshots
were visually inspected: controls, configuration/history and constructed-prior
caveat are visible, with no horizontal overflow. Keyboard/live-region checks are
not a screen-reader audit. Browser download regression now saves actual dialogue
audit bytes and verifies them with the offline checker; lab/import downloads
are parsed and checked as JSON, not accepted by filename alone. The test's first
import assertion used the wrong object nesting, then was corrected to the actual
download schema and rerun successfully. No application layout was changed.

## 2026-10-14 08:33 IST exact imported-result replay checkpoint

Imported results now carry a deep-copied exact synthetic input model and canonical
input hash. The browser download test saves this input, reruns it through the
standalone experiment CLI, and compares the complete result for exact equality.
That end-to-end downloaded-input replay passed. Source input changes after a run
do not mutate its recorded model. Fresh default verification passed176 unit plus
12 spike tests. No page layout or privacy scope changed; these are declared-model
reproducibility checks, not prior authenticity or realism checks.

## 2026-10-14 08:44 IST one-command downloaded-result verification

`experiment_spec.py --verify-result downloaded-result.json` reruns the embedded
synthetic input and compares the full result without manual JSON copying. Actual
subprocess success and changed-fingerprint failure paths passed. Fresh default
verification passed179 unit plus12 correctness-spike tests. Exact reproducibility
is not authenticity or realistic-prior validation. No visual change.

## 2026-10-14 08:55 IST private package path checkpoint

Package creation rejects symlink/non-regular sources and resolved paths outside
the project. Verification rejects archive symlinks, Windows-style separators/
drive paths, malformed manifest roots and oversized entry totals before reading
payloads. Six package regressions passed; the previously delivered186-test ZIP
still verifies through the stricter checker. Fresh default suite passed182 unit
plus12 spike tests. These are bounded archive hygiene checks, not a signed supply
chain or permission to publish.

## 2026-10-14 09:16 IST guided checkpoint consistency

Both guided and free dialogue saves now use the flushed atomic replacement
helper. Tests confirm fsync is called and a failed guided replacement preserves
the prior loadable checkpoint. This is accidental-failure handling, not rollback
protection or cryptographic persistence. Fresh default verification passed184
unit plus12 correctness-spike tests. QUICKSTART.md gives a short private hands-on
path and exact offline checks without changing the selected B UI.

## 2026-10-14 09:27 IST symmetric protected-bit and budget invariants

Seeded finite-model tests confirm complementing the protected binary label leaves
tested decisions unchanged and complements posterior support. Wider INITIAL
public budgets do not reduce scheduling success within the64 supported policies.
This is not a promise about actual outcomes after different disclosure histories,
nor global optimality across protocols. Targeted invariance/weighted-optimization/
preference suite passed13 tests. Fresh default verification passed186 unit plus12
correctness-spike tests. No privacy-model or visual change.

## 2026-10-14 09:38 IST deeper adaptive/restart checkpoint

A new96-model adaptive replay at depth32 checked1,536 world traces with zero
bound violations, invalid meetings or false supported calendar answers. Requests
are selected only from public observed prefixes. This remains sampled finite-model
evidence, not arbitrary-adversary coverage. Across24 seeded fixed-public-config
sessions,16 requests each, serialization before every request preserved complete
responses, state and final ledger. Fresh verification passed187 unit plus12 spike
tests. No model or visual expansion.

## 2026-10-14 09:48 IST verification-runner contract checkpoint

Runner controls verify that child failure or timeout stops immediately without a
passing summary, and that invalid timeouts are rejected before any child run.
`--full` help now accurately names its two extra original sweeps; expanded and
adaptive scripts are separate, as QUICKSTART.md documents. Fresh default suite
passed191 unit plus12 correctness-spike tests. No application/UI/model change.

## 2026-10-14 10:19 IST documented walkthrough replay

Restarted current server and reran comparison, expanded feature/download and
keyboard browser paths successfully. Ran the exact QUICKSTART offline ordinary-
query example, verified its downloaded-result equivalent by embedded-input replay,
and exported/verified the original guarded audit. Both report zero tested bound
violations, invalid meetings and invalid calendar answers. The ordinary-query
actual world schedules cleanup; its across-world mean selected slot2 is a metric
over different output cells, not a contradiction of that actual-world result.
Current source changes since the203-test package are review documentation only.

## 2026-10-14 10:30 IST full-visible weighted adaptive dialogue

A new32-model/depth16 sweep includes every returned dialogue result field in the
observable prefix: intent, decision evidence, posterior/world counts, event count
and safe-next suggestions. Requests depend on that public prefix only. State is
serialized before each request. All512 world traces passed with zero tested bound
violations, invalid meetings or false calendar replies. This is sampled finite-
model coverage, not arbitrary-adversary proof. Operator-only stored actual fixture
is not a private recipient channel. Run `python3 full_dialogue_sweep.py` separately;
it is not included in the default or --full verification jobs.

## 2026-10-14 10:51 IST correlated weighted adaptive control

An additional seeded128-model/depth24 replay used explicitly correlated calendar
subsets, independently assigned positive per-world weights and public-prefix
adaptive requests. It checked1,089 world traces with zero bound violations,
invalid meetings or false supported calendar replies. This complements fixed
full-calendar dialogue tests: it checks the core evidence channel in arbitrary
sampled declared subsets, not the fixed dialogue API or real-prior discovery.
Seed104951 and measured output are recorded in correlated-adaptive-measurements.json.
The original one-off replay now has an exact standalone route:
`python3 correlated_adaptive_sweep.py`. Its fresh rerun matches every non-timing
field. It is separate from the default suite; the default count remains203.

## 2026-10-14 11:12 IST final-candidate browser/readiness check

Current server restart followed by original comparison, full feature/download
path and keyboard controls passed. No page errors or horizontal overflow in the
tested390/320px widths. Required runtime, short guide, claim/evidence review map
and separate full-visible/correlated replay scripts are present. No new visual
or model change. Final candidate remains the203-test source shape; clean package
verification will be repeated before delivery.

## 2026-10-14 13:22 IST MCP surface checkpoint

`python3 server.py` now also serves a Streamable HTTP MCP endpoint (protocol
2025-11-25, JSON-RPC 2.0) with an assistant surface (`/mcp`: veil_ask,
veil_status, veil_request_approval, veil_check_approval) and a token-gated
operator surface (`/mcp-operator`: veil_start_household, veil_operator_view,
veil_decide_approval). `/alexa` is a simulated voice-assistant web client; no
Amazon service or device is contacted. Assistant results carry only what the
room hears plus an event count; operator tools return Unknown tool on the
assistant endpoint. Session handling covers Mcp-Session-Id, 404 for unknown
sessions, 400 for unsupported protocol versions and DELETE teardown, plus
Origin/Host checks. Fresh default verification passed 209 unit tests (the 191
prior tests plus 18 new MCP tests) and, as a separate job, 12
correctness-spike tests.

## 2026-10-14 13:56 IST simulated approval and independence checkpoint

A refusal can now be followed by a simulated in-app approval request
(veil_request_approval, decided via veil_decide_approval). No message is sent
and no real person is asked; the operator plays Alice and first sees what the
room would infer if she approved. After an approved disclosure the guard's
ledger no longer describes what the room knows, so direct answers pause until
the household is reset; each further answer needs its own approval. Approval
state is in memory only. Exhaustive checks on the assistant-facing surface,
all run on this build: pending/declined approval paths identical for every
calendar (448 runs, 0 calendar-dependent cells); repeated-approval composition
comparing the operator-stated inference with the room's real posterior
(18,944 runs, 6,160 visible-transcript groups, 0 mismatches); length-3
request-sequence independence (25,536 calendar runs, 5,646 distinct visible
transcripts, 0 groups not half free). The browser approval flow was driven end
to end on this build (refusal, simulated request, approve, disclosed answer,
paused direct answers) with page-error checks and inspected screenshots.
One-time interoperability with the official MCP Python SDK client passed
(initialize, tools/list, tools/call); it is not a repo dependency and not
Alexa+ runtime integration. These remain finite synthetic-model results, not
a real-consent or privacy guarantee.

## 2026-10-14 14:02 IST MCP-candidate package checkpoint

A fresh deterministic source ZIP was built with `python3 package_lab.py` (82
source files plus source manifest) and verified with `--verify`. It was
extracted into a separate clean directory, where `python3 verify_all.py`
completed: 209 unit tests plus, as a separate job, 12 correctness-spike tests,
all passed. No local session state, installed Node dependency or repository
metadata was bundled. The source-package hash checks accidental corruption,
not authenticity. The `/alexa` visual design remains provisional pending
owner feedback; any further code change requires rerunning the affected
checks before delivery.

## 2026-10-14 14:26 IST negative control for the MCP independence check

An ad-hoc control (in-process, no repo files changed) wrapped `mcp_server.handle`
so the assistant-facing veil_status result also carried the protected-window
bit of the actual synthetic calendar. Rerunning the transcript grouping for
window "early prep" over all seven request texts and 16 calendars flagged all
24 visible-transcript groups (112 runs) as not half free, and the check exits
nonzero. The exhaustive check therefore catches a deliberate leak rather than
passing vacuously. The unmodified final build passes the same check with 0
violations (see the 13:56 checkpoint).

## 2026-10-14 17:36 IST negative control made runnable

The 14:26 ad-hoc control is now reproducible as `python3 negative_control_check.py`
(in-process wrap of `mcp_server.handle`; server code unchanged). Measured on the
working tree: 112 runs, 24 visible-transcript groups, 24 flagged with the injected
leak, `leak_caught_in_every_group: true`, exit code 0. The unmodified
`python3 mcp_independence_check.py 3` still passes with 0 violations on the same tree.

## 2026-10-14 19:04 IST information-bits readout (loop-1 improvement)

The operator view, without-Veil counterfactual and every approval preview now report
information gained so far in the finite uniform-prior model: protected_window_bits
(binary free/busy variable of the protected window, prior entropy 1 bit) and
calendar_bits (calendar identity, prior 4 bits). Measured on this tree:
verify_all 209 unit tests one job + 12 spike separate job (return codes 0);
mcp_independence_check.py 3 - 448 approval runs (0 exceptions), 25,536 runs,
5,646 transcripts, 0 groups not half free, max_protected_window_information_bits 0.0;
composition 18,944 runs, 6,160 groups, 0 mismatches; negative_control_check.py 112
runs, 24/24 groups flagged, exit 0; browser approval-flow test passes and the bits
readout is legible in the /alexa operator panel (screenshots reviewed).

## 2026-10-14 20:15 IST stale-request invalidation + generation-bound approval ids (loop-4 functional)

Pending approval requests now go STALE (terminal, never approvable, discloses nothing) when
the conversation basis changes before Alice decides - a new answer, or another approved
disclosure. Approval ids are opaque strings bound to the full household generation, so a
delayed old-id check/decide cannot target a reissued request after reset or reconnect.
Measured on this tree: verify_all 215 unit tests one job (191 non-MCP + 24 MCP, including
stale-after-new-answer, stale-after-another-approval, unchanged-conversation-decidable,
stale-discloses-nothing, reset cross-generation aliasing, reconnect no-memory) plus, as a
separate job, 12 correctness-spike tests (return codes 0); approvals check 448 runs, 0
cells with calendar dependence; length-3 sweep 25,536 runs, 5,646 distinct transcripts, 0
groups not half free, max_protected_window_information_bits 0.0; composition 18,944 runs,
6,160 transcript groups, 0 groups where the operator claim differs from the room posterior
(composition and approvals rerun after the id change with returned-id capture; ids
normalized out of compared transcripts as per-household uniqueness randomness, not
calendar information); negative_control_check.py 112 runs, 24/24 groups flagged, exit 0;
browser approval-flow test passes and the stale state renders end to end with string ids
(screenshots reviewed).

## 2026-10-14 20:20 IST scenario calendar input (loop-5 functional)

`veil_start_household` (operator surface only) accepts `alice_calendar` (integer 0-15, default
7): a selectable synthetic calendar - a reviewer can rerun the demo against any of the 16
calendars in the declared finite model without editing code. Operator view reports the chosen
calendar. Assistant surface cannot set or see it (tested: assistant-surface call errors).
Measured on this tree: verify_all 217 unit tests one job (191 non-MCP + 26 MCP: scenario
calendar accepted and bruteforce-matched, range/type boundaries 16/-1/'x'/7.5/true/false/null
rejected, assistant-surface call refused, default unchanged) plus, as a separate job, 12
correctness-spike tests (return codes 0). The exhaustive sweep, composition, approvals and
negative-control numbers from the 20:15 checkpoint are PRIOR RUNS on the loop-4 tree: they
exercise the default start path, which this change does not alter (the new branch is inert
without the parameter); they are not post-v7 validation of the selectable-calendar path, which
is covered by the unit tests above.

## 2026-10-14 20:25 IST scenario selects in the /alexa operator panel (loop-6 functional)

The operator panel now exposes the selectable synthetic calendar (0-15) and protected window as
selects, applied on 'start a new household'; Bob's side never shows them. Boundary hardening:
alice_calendar rejects range/type edges (16/-1/'x'/7.5/true/false/null) and assistant-surface
calls are refused (tested). Measured on this tree: verify_all 217 unit tests one job
(191 non-MCP + 26 MCP) plus, as a separate job, 12 correctness-spike tests (return codes 0);
browser check with calendar 5 + cleanup: guarded 50% cannot-tell, unguarded 0% known-busy, bits
readouts 0/1 and 1/1 bits as expected (screenshot reviewed). Exhaustive sweep/composition/
approvals/negative-control numbers remain the 20:15 prior runs on the loop-4 tree (default
start path unchanged); the selectable-calendar path is unit-tested, not exhaustively swept.

## 2026-10-14 20:29 IST demo client covers the approval lifecycle + smoke test (loop-7 functional)

mcp_client_demo.py (the judge's first command) now exercises the simulated approval lifecycle
on the assistant surface only: refuse -> request approval -> pending -> conversation advances ->
stale -> re-ask. New McpClientDemo smoke test runs the client against a live server on an
isolated state file and asserts the lifecycle output fragments. Measured on this tree: verify_all
218 unit tests one job (191 non-MCP + 27 MCP) plus, as a separate job, 12 correctness-spike
tests (return codes 0).


## 2026-10-14 20:34 IST live-vs-record approval limits (loop-8 functional)

Stale requests no longer consume the per-household limit: the cap is 8 LIVE (non-stale)
requests; stale records stay visible and retained records are bounded at 64. The operator view
refreshes stale status before rendering (previously a just-advanced conversation could render
as pending until the next preview). Measured on this tree: 29 MCP tests pass (live cap reached
with 8 pendings, all 8 stale after one advance, 8 more allowed; record limit at 64 with the
error naming the record limit). Measured: verify_all 220 unit tests one job (191 non-MCP + 29 MCP)
plus, as a separate job, 12 correctness-spike tests (return codes 0).


## 2026-10-14 20:40 IST pending-queue cap semantics (loop-8 revision) + composition3 check

Cap terminology corrected: the per-household limit is 8 PENDING requests (Alice's decision
queue); decided (approved/declined) and stale records do not occupy it (tested: a decline frees
the slot immediately), retained records bounded at 64. Measured: verify_all 220 unit tests one
job (191 non-MCP + 29 MCP) plus, as a separate job, 12 correctness-spike tests (return codes 0).
Falsification-targeted check added: mcp_independence_check.py composition3 runs the repeated-
approval composition check with up to THREE approved disclosures - the hypothesis it could
falsify is that the disclosed-mode region composition diverges from the room's real posterior
at three disclosures in ways pairs do not expose. Expected scope 80,384 sessions (4 windows x
8 pre-histories x 157 approval combos x 16 calendars). RESULT (21:28): 80,384 composition runs,
39,760 visible transcript groups, 0 groups where the operator's stated inference differed from the
room's real posterior - the hypothesis was not falsified. An earlier 61,952-run estimate undercounted
the combos (permutations, not combinations).

## 2026-10-14 21:50 IST declared non-uniform prior - validated

veil_start_household accepts an optional declared prior [busy, free] (integer weights 1-9, default
[1, 1] uniform); operator surface only. information_bits generalized: prior entropy H2(p0) for the
protected window and 3 + H2(p0) for calendar identity, posteriors weight-based; reduces exactly to
the previous 1-bit/4-bit numbers under the uniform default. Contract (MCP.md): weights describe
ONLY the protected bit's distribution - the other three calendar bits stay uniform and independent;
not arbitrary correlated priors. UI: the operator % uses the operator-stated weighted fraction;
raw calendar counts are labeled as raw, not probabilities, when the prior is non-uniform; the
operator panel exposes a prior select next to the calendar/window scenario selects.
- unit: verify_all 221 unit tests one job (191 non-MCP + 30 MCP) plus, as a separate job, 12
  correctness-spike tests (return codes 0) on this tree. Boundary rejections tested: None, True,
  False, {}, [1.5,3], [1,'3'], [1,True], [-1,3], [0,3], [1,10], [1], [1,2,3], '13'; [9,9] accepted.
- mcp_independence_check.py weighted (length 3, prior [1,3]): 25,536 runs, 5,646 distinct
  assistant-visible transcripts, 0 groups off the exact 1:3 weighted protected-window ratio,
  max protected-window information 0.0 bits. The guard preserves the declared prior exactly.
- mcp_independence_check.py weighted-composition (up to 2 approved disclosures, prior [1,3]):
  18,944 runs, 6,160 visible transcript groups, 0 groups where the operator's stated post-approval
  inference differed from the room's WEIGHTED posterior.
- mcp_client_demo smoke (real MCP client over HTTP): rc 0 on this tree.
Scope: weighted checks above run prior [1,3] only; the uniform default remains covered by the
earlier uniform exhaustive runs plus composition3 (80,384 runs, 0 mismatches) on this tree.

## 2026-10-14 22:30 IST final-tree uniform reruns + provenance

The uniform exhaustive checks were rerun on the FINAL tree (declared-prior feature present,
uniform default exercised): main(3) approvals 448 runs / 0 calendar-dependence and sweep
25,536 runs / 5,646 distinct transcripts / 0 groups not half free / max 0.0 protected bits;
composition(2) 18,944 runs / 6,160 visible transcript groups / 0 operator-vs-room mismatches.
Per-result provenance (start times, server-code and tree hashes) is in
validation-results/PROVENANCE.md. The earlier composition3 (80,384 runs / 0 mismatches, up to 3
approved disclosures) attaches to the tree as of 20:40 only - it predates the declared-prior
feature; the uniform-default code paths it exercised are unchanged since. The /alexa page gained
a "Try this in 3 minutes" judge script (UI only; validated end-to-end by DOM: guarded refusal at
0 bits vs unguarded fully-known contrast pre-approval, bits moving by exactly the disclosed
amount after approval).

## Approval persistence fix + restart scenario C (engine hash TBD at commit)

Finding (restart_check scenario C, pre-fix): the post-disclosure pause lifted on a server process restart because approval records were memory-only; after restart _disclosed() was false and direct answers resumed while the room had heard the disclosed answer. Ledger, generation and events persisted; the enforcement state did not.

Fix: approval records persist with the session envelope (validated, bounded at 64 records, atomic tmp+fsync+replace writes under the server lock). Legacy envelopes without an approvals key fail closed: decisions never wrote to the ledger, so their history cannot be reconstructed; direct answers pause until an operator starts a new simulation or Alice approves answers one at a time, and the fail-closed marker itself persists. Pending approvals that survive a restart keep their generation and stale basis; an intervening answer still marks them stale and decide refuses stale requests.

Validation after fix: restart_check.py scenarios A/B/C all PASS (B updated: pending approvals now survive restart, recorded in validation-results/restart-check.json); unit suite 240 tests OK (4 new approval-persistence tests in test_mcp.py: decided-approval pause survives restart, pending survives then goes stale, legacy fail-closed + new-simulation clears, oversize records rejected).

## 2026-10-15 00:38 IST sweep run: known harness bug #3 reproduced (oracle-side, not engine)

The full joint sweep launched 00:38 against engine 2f3a24ae ran joint_mcp_check.py for both legs. Uniform leg: 38,304 runs / 5,810 groups / 0 deviations, PASS (joint-mcp-final-2f3a24ae.json). The weighted leg failed 673/673 - the same headcount-vs-weighted-prior oracle bug already documented as harness bug #3 in PROVENANCE-JOINT.md (joint_mcp_check.py's weighted leg counts calendars, not prior weights; every group including pure-refusal groups flags). Preserved as joint-mcp-weighted-headcount-bug-20261015.json. The corrected weight-normalized oracle is joint_mcp_weighted.py; weighted evidence comes from that script.

## Oracle consolidation + pre-flight sanity gate (engine 106f424f, 2026-10-15 01:37)

After the second headcount-bug instance, the weight-normalized oracle is consolidated into the single entrypoint joint_mcp_check.py (both legs; joint_mcp_weighted.py is now a deprecation shim so the headcount oracle cannot be run by mistake). Under uniform priors the weight-normalized oracle reduces exactly to the old headcount, so the committed uniform artifact (joint-mcp-final-2f3a24ae.json) remains valid.

Sanity gate before the final-hash sweep (all pass, recorded here): (1) pure-refusal group under priors [1,3]x[2,1] gives weight-normalized distribution [1/6, 1/2, 1/12, 1/4] = declared weighted prior exactly; (2) uniform priors reduce to headcount [1/4 x4]; (3) a seeded leak of one protected bit through the assistant surface splits the refusal group in two and the consolidated comparison flags both; (4) negative_control_check.py on the fixed engine: 112 runs, 24/24 groups flagged, leak caught every time (validation-results/negative-control-106f424f.json).

## 2026-10-15 final-hash full sweep, engine 106f424f (post approval-persistence fix)

Consolidated weight-normalized oracle (joint_mcp_check.py 82f27e0f, single entrypoint after the headcount-bug consolidation) against mcp_server.py sha256 106f424fe512b70ecfc453de9e2d242ee9d96d08db6c9fa04e303e0690cfd922, full visible assistant-surface transcripts:
- uniform_length<=3: 38,304 runs / 5,810 transcript groups / 0 groups with joint deviation - PASS (joint-mcp-final-106f424f.json)
- weighted_[1,3]x[2,1]_length<=2_weight-normalized: 5,376 runs / 673 groups / 0 deviations - PASS (joint-mcp-weighted-final-106f424f.json); first corrected weighted measurement on this engine
Pre-flight sanity gate (weighted refusal == prior, uniform == headcount, seeded leak flags, negative control 24/24) recorded above at 01:37. verify_all on this build: 240 unit + 12 spike green (verify-all-106f424f.json).
