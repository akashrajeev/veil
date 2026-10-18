> New private real-input/official-SDK lab: see [REAL-CALENDAR-LAB.md](REAL-CALENDAR-LAB.md). The original web demo below is still synthetic.

# Veil

An Alexa-style local simulation that checks what a conversation reveals about a
protected calendar fact. Not live Alexa, a natural-language assistant, or a
privacy guarantee for real calendars.

## Run locally

Python 3.10+ required, no Python packages or keys:

    python3 server.py

Open http://127.0.0.1:8765 in your own browser. Start the conversation, ask the
second question, then find a shared window. The server listens on localhost only.
Do not deploy this demonstration as a multi-user service.

## Test

    python3 verify_all.py
    python3 verify_all.py --full

With the local server running:

    python3 api-test.py

Optional browser tests need Node.js and the pinned Playwright dev dependency:

    npm ci
    npx playwright install chromium
    npm run test:browser

Browser screenshots are written to shots/. No browser/account access is needed.
The application itself has no JavaScript dependencies and no remote runtime
assets. package-lock.json pins the optional testing dependency.

## What the demo actually does

Alice's synthetic calendar is free in early prep, late prep, and dinner. Bob is
free in early prep and dinner. The observer knows Bob's calendar, not Alice's.
Every possible Alice calendar is equally likely in the declared model.

Two questions: can Alice cover exactly one of the prep windows, and is she free
for late prep? Alone, either reply leaves early-prep availability at 50%. Together
the replies expose it. This is a deliberately selected composition example, not
proof this is a common or natural household request.

The unguarded run answers both and selects early prep. Veil answers the first,
uniformly declines the second and selects dinner.

The MCP demo (see MCP.md) can also protect TWO windows jointly: the guard then
preserves the whole free/busy pattern of the pair, not each window alone. A
per-window guard provably cannot do this - the "exactly one of the two prep
windows" question keeps each margin at 50% while exposing the joint pattern -
and that question ships in the demo as the built-in counterexample. It evaluates every output cell
including refusals, policy identity and final selected window. Refusal is an
endpoint: private approvals are not implemented. Both scheduling computations
use the engine; answers are not a precomputed result table. Buttons provide typed
commands, not natural-language interpretation.

The observer panels replay the actually emitted sequence over all 16 worlds
consistent with Bob's initial knowledge. They compute exact posterior support
with a separate observer implementation. The operator can inspect the real
synthetic fixture. The shared page is not an access-control/security boundary.

## Measured evidence

The original B handoff passed39 unit tests. The continuing lab has expanded coverage; use the current test runner for its total. API and headless browser checks pass, including reload
persistence, actual dinner selection, desktop/390/320px widths, no page errors.
The first mobile verification found overflowing tiles; four-column mobile tiles
fixed it and updated screenshots were inspected.

The independent observer imports no controller helpers. Across 256 equally
weighted joint calendars, 175 have a feasible shared window. After the composition
conversation: guard completes 112 of 175 feasible cases with zero tested
protected-fact probability shift; naive completes 175 but shifts it up to 0.5.
Without those prior questions direct strict scheduling reaches 148 feasible cases.
Every selected meeting was actually available to both people.

81 length-four request sequences, 20,736 world traces and 1,296 resident-audience
sequence checks passed, with no prefix violations or invalid meetings. 80 seeded
weighted-domain trials plus 60 additional weighted audience trials passed. A
128-world correlated-calendar control leaks under public-prior-only checking
(32 resident prefix cells); audience-conditioned checking has zero.

Mutation controls detect secret-dependent refusals, unchecked final meetings,
visible approval signals and secret-dependent error shapes. They do not prove
safe real approvals or errors are implemented. Measured JSON files record actual
runs, not planned targets. oracle.py is independently implemented, not a third-
party audit or general proof. One declared binary fact can remain protected while
other calendar information is disclosed.

## Boundaries

One observer/one fact, finite declared prior, four windows, supported policy family
of 64 ordered slot subsets. Not global optimality over every possible protocol.
No encryption, differential privacy, multi-audience composition, collusion model,
real-life prior discovery, semantic inference protection, authenticated storage,
rollback protection, or timing/transport mitigation. Budgets 0.125/0.25 do not
improve main-fixture usefulness; 0.5 permits full revelation of its protected bit.

.state/dinner.json contains the saved synthetic transcript and model hash.
Reload/server restart keeps history. Malformed state, wrong model, changed budget,
unsupported sequence, and a transcript impossible for the selected fixture are
rejected. This is validation, not cryptographic storage. Reset deliberately starts
another synthetic experiment, not a privacy-budget reset for real conversations.
The browser submits its expected step; duplicate or stale advance requests return current state without advancing. API requests omitting that optional value advance normally.
No calendar booking or real message is sent.

No public release, hosting, repo sharing, license choice, video or submission is
part of this local build. Visual direction B (Conversation lab) selected for the comparison demo.

## Research and prior art

Private scheduling predates this prototype. The proposed angle is an observable,
composition-aware disclosure controller and live inference lens in a bounded
consumer simulation, not inventing a private scheduler.

- CalBench: https://arxiv.org/html/2605.09823v3
- PiSAs: https://arxiv.org/html/2607.05318v1
- Inference-aware guidance: https://arxiv.org/html/2607.16710v1
- MCIP (safety-enhanced MCP variant adding tracking tools and a trained guard model, plus an unsafe-behavior taxonomy/benchmark; Veil stays an ordinary MCP server instead): https://aclanthology.org/2025.emnlp-main.62/
- Calendar matching: https://github.com/horse-3903/calendar-matcher
- Private calendar scheduling: https://github.com/jnagykuhlen/PrivateCalendarScheduling

No paper code or figures copied. Paper results not independently replicated here.

## Hands-on walkthrough

Unzip, enter the veil folder, and run python3 server.py. Open the localhost URL
above. Reset both runs, then click the advance button three times. After the
second question, compare naive 100% with guarded 50%; after the third, compare
early prep with dinner. Reload and confirm the conversation stays at step 3.
No email, browser sign-in, key, microphone, spend or installation needed for this
walkthrough. A Python-equipped computer is needed; the ZIP is not a phone-hosted
interactive app. A free port 8765 is required; stop another local process there if
necessary, or inspect server.py before changing its host/port expectations.

## Overnight lab features

The selected B page keeps the original comparison and adds a collapsed scenario
lab: four presets or custom fictional calendars, any ONE protected slot fact,
strict/quarter/open public experiment limits, direct-vs-composition order,
public inconvenience costs, prefix inference trail and JSON experiment downloads.
Compare-all-limits does not represent private consent. Quarter does not improve
main-fixture scheduling over strict; open can fully reveal its protected fact.

Typed request preview accepts a listed alias vocabulary only. Free-order dialogue
persists separate history; Start new synthetic dialogue binds lab calendars/fact/
limit, then Ask and remember records typed requests. New sessions bind the selected public costs and prior odds. Existing sessions keep their original configuration. Unsupported language
uniformly refuses. No general natural-language understanding, live voice or Alexa.

Download guarded audit JSON, or export the saved free dialogue audit. Offline:

    python3 audit_export.py --verify downloaded-audit.json
    python3 verify_all.py --full

The audit contains all declared synthetic worlds, not private recipient data.
Full-visible dialogue outputs and class-wide explanations are tested as observable.
CLI dialogue is also available: python3 dialog.py --help. Limits/schema validation
and atomic writes are not authenticated storage, rollback protection or multi-user
security. Operator endpoints expose synthetic actual calendars deliberately.
Generation tokens stop delayed pre-reset requests from advancing a new experiment.

Scheduling costs are PUBLIC integer experiment weights, not hidden preferences.
Private preferences, multiple protected facts, multiple audiences, collusion,
actual privacy approvals and cryptographic separation remain unimplemented.
Optimization is exact only over the supported 64 ordered slot policies, not every
possible conversation. Earlier versioned Drive handoffs remain unchanged.

### Later overnight extensions

New dialogue sessions bind public cost/prior parameters (versioned configuration hash);
legacy sessions retain their history. Supported typed availability questions cover
all four windows. Shortcuts and labeled free-window checkboxes help discover the
bounded vocabulary. The lab compares a simple unguarded earliest-slot baseline,
not every existing scheduler. JSON experiment import can run explicitly weighted
or correlated observer-conditioned models; no arbitrary code or external URLs.
Initial fact certainty is warned, not described as secrecy. Imported-run results
are downloadable. Example JSON files live in examples/.

    python3 experiment_spec.py examples/correlated-observer-domain.json
    python3 adaptive_dialog_sweep.py

Downloaded dialogue audit uses the same audit_export.py --verify command. Trace
schema/depth/weights/model hash are checked. These checks don't authenticate the
source or prove the declared prior matches reality. Partition caching is bounded
and tested equivalent to uncached decisions. Cost preferences and synthetic priors
are PUBLIC and fixed for a session; changing them requires a new experiment.

### Session reliability and continuation

Saved dialogue v4 binds public costs, prior odds, protected slot and budget. The
active parameters are displayed beside its history; changing lab controls doesn't
change an existing conversation. Legacy state migrates without clearing history.
Writes flush before atomic replacement. Injected save failures return an error
rather than a remembered answer. This is accidental-edit/recovery handling, not
cryptographic integrity, secure storage, rollback protection or a multi-user app.

Free dialogue suggests supported safe next requests. Suggestions are class-wide
and included as observable output in tests. A scheduling suggestion is not a
promise an actual slot will be returned. NO_MEETING means the selected supported
policy returned none; it is not proof of infeasibility. In the main strict
composition fixture144 worlds return none:81 have no common window,63 have one
that the supported safe policy does not expose.112 schedule. Distinguish useful
bounded policy control from globally optimal privacy-preserving coordination.

The03:32 checkpoint covered134 non-spike tests plus12 spike tests; later refinements add coverage. Additional adaptive/spec-fuzz scripts report sampled controls separately.
Later edits may change counts; run the suite instead of relying on this historical
checkpoint statement. HTTP fault/concurrency tests need no real accounts.

### Later review readiness

Lab controls are remembered in this browser only and validated on restore. Saved
session parameters remain separate and visible. Failed experiments clear the last
downloadable result, so an old result cannot masquerade as the failed run's output.
Correcting invalid controls lets the lab recompute without touching session history.

Independent supported-policy optimality now includes100 seeded weighted/public-
cost cases, still only64 candidate policies. Long-history/session envelope fault
controls and HTTP save-failure tests cover reliability boundaries. The04:41
checkpoint completed142 non-spike tests plus12 spike tests; later test counts must
be measured, not assumed from this historical statement.

### Ordinary-query illustrative example

Load the ordinary-query example beside JSON import, or run:

    python3 experiment_spec.py examples/ordinary-questions-correlated.json

The deliberately constructed four-world prior makes late-prep and dinner-
availability replies each harmless for early-prep support alone, but revealing
together. Cleanup is always free in that declared prior. Guard refuses the second
reply uniformly and schedules cleanup. This is not a learned household model or
proof of typical behavior; original independent256-world comparison is unchanged.
Expanded short-sequence sweep covers87,808 traces over seven intents/depth3 and
sixteen resident-calendar classes, in four bounded batches. Zero observed declared-
bound violations or invalid meetings, not all priors or unbounded interaction proof.

### Private source package checks

The handoff ZIP omits local session state, caches, screenshots and installed
browser dependencies. SOURCE-MANIFEST.json lists source-file hashes for detecting
accidental corruption. To check an extracted download without git:

    python3 package_lab.py --verify ../downloaded-package.zip

A hash manifest is not a signature and does not authenticate who made a package.
Creating a new deterministic ZIP from a git working copy requires git:

    python3 package_lab.py ../veil-source.zip

The application and its default Python tests do not need git. Build only from the
intended private checkout; this command does not approve release or upload.

Offline audit verification checks both protected-fact support and truthful
supported calendar replies. Exit0 means the declared artifact passed; exit1
means a privacy-bound violation, invalid meeting or false calendar answer was
observed; exit2 means the input could not be validated or read. A failed audit
must not be described as verified. NO_MEETING is still a policy result, not an
independent claim of infeasibility. These tests concern declared synthetic data.

Imported experiment-result downloads include `input_spec` and a canonical input
SHA-256, so the exact declared synthetic prior, requests, costs and budget can be
replayed. Save the `input_spec` object as a JSON file, then run
`python3 experiment_spec.py saved-input.json`. The hash detects accidental input
changes; it is not a signature or evidence that the declared prior is realistic.

For a downloaded imported-result file, no manual object copying is needed:

    python3 experiment_spec.py --verify-result downloaded-result.json

The command reruns its declared input and compares the complete result, including
the input fingerprint and measured outputs. An edited or inconsistent result is
rejected. A passing exact rerun still does not establish realistic priors or an
authenticated source.

## MCP server and simulated assistant client

See MCP.md. `python3 server.py` also serves a Streamable HTTP MCP endpoint at `/mcp` and a simulated voice-assistant page at `/alexa` (not Alexa+ and no Amazon service is contacted).
