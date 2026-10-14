
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
