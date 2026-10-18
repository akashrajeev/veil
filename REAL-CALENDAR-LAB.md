# Real calendar input lab

Private branch: `lab/real-calendar-mcp-20261016`, based on joint candidate v8.
This is a second entry point, not a replacement of the original synthetic UI.

## What is real, and what is still a model

- The input adapter accepts a successful Google free/busy response, checks coverage and projects it into four public candidate windows. It never needs event titles, descriptions, attendees, places, links, OAuth tokens or calendar writes.
- `calendar_mcp_server.py` uses the official MCP Python SDK 1.30.0, with a separate official SDK client. Actual runtime calls use Streamable HTTP and negotiate protocol 2025-11-25. These are structured tools, not a language model.
- The real-input tools use Veil's joint guard. Actual availability can come from the calendar, but the 16 counterfactual worlds and independent uniform prior are still declared assumptions. Real data does not establish a real-world privacy guarantee.
- No real Alexa+, Amazon device, LLM, second person's calendar, continuous calendar sync or actual booking is connected.
- The original `/alexa` page remains synthetic. Do NOT put real input in its operator panel: that panel deliberately shows ground truth for explanation.

## Honest evidence

On October 16, 2026, one user-approved, read-only live free/busy snapshot passed the official SDK flow twice, including a server restart. Private availability results are not included here. This narrow test verifies the input path, not diverse busy-calendar behavior, and says nothing about unsynced calendars or real-world commitments.

No personal intervals, selected real windows, account identifiers, raw responses, minimized real snapshots or real ledgers are included in this package. Personal test data was local only and deleted after testing. The reproducible example is wholly made up, not anonymized real records. Busy windows in that fixture exercise overlap and boundary handling.

## Reproduce the made-up schedule

Python 3.10+. The original UI still needs only the standard library. This separate SDK lab needs its pinned dependencies:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-real-calendar.lock
python3 calendar_input.py --input examples/calendar-fixture-freebusy.json \
  --windows examples/calendar-fixture-windows.json --source synthetic-fixture \
  --as-of 2030-01-07T00:00:00+05:30 --output .private/fixture.json
.venv/bin/python run_calendar_sdk_check.py --snapshot .private/fixture.json --state .private/fixture-ledger.json
```

The check starts a separate loopback SDK server, uses a randomly generated bearer token internally, runs the official SDK client, checks truthful outputs, prints only aggregate status, and stops the server. Run it again with the same ledger to test restart persistence.

For interactive use, generate a random token locally into `VEIL_LAB_TOKEN` (at least 32 characters, never commit or share it), run the server with the two private paths above, then run `.venv/bin/python calendar_mcp_client.py`. Its default output hides private tool results. `--fixture-output` is only for synthetic servers.

Available tools: `calendar_windows`, `calendar_availability(window)`, `calendar_prep_parity`, `calendar_find_window`. The observer's four-window availability is a public test assumption, not a live second person's calendar. Windows 0 and 1 are jointly protected by default. There is no approval/release tool on the real-input surface; requests that would leak are refused.

## A future approved live read

Get a Google free/busy response for one approved calendar and bounded range; do not export full events. Feed it and four publicly chosen, sorted, non-overlapping windows into `calendar_input.py` with `--source live-google-freebusy`. Set `--as-of` to when the read occurred. Keep the response, snapshot and ledger outside the package and source control. Provenance is a caller declaration, not a cryptographic attestation; do not label a fixture as live.

The adapter rejects calendar errors, missing busy arrays, uncovered windows, naive timestamps and invalid intervals. Any busy overlap means the candidate is unavailable; half-open boundaries are handled correctly. Empty successful busy arrays mean free in this calendar only.

Real snapshots pause after 30 minutes, rather than silently claiming fresh availability. A refresh is not automatic. Changes to snapshot or model refuse to reuse an old ledger. Do not reset the conversation to evade earlier disclosures; a real refresh needs a transcript/privacy design review. This is an experimental snapshot workflow, not deployment-ready scheduling.

## Verification

```sh
python3 verify_all.py
.venv/bin/python -m unittest test_calendar_mcp -v
```

The regular verifier now includes 30 input/guard tests, on top of the original 240 tests and 12-test spike. Four separate SDK/network tests check initialization, discovery, structured calls, unauthorized access, absent operator tools, invalid arguments, shared ledger and restart. The input tests also cover persistence failure before release, stale snapshots, strict schemas, file permissions, and joint invariants across all 16 actual masks.

## Limits and security

This is a private, single-conversation, loopback-only lab. Bearer authentication and absence of an operator API reduce accidental exposure; they do not make it a multi-user service. No concurrent server processes should share a ledger. Files use mode 0600 and are ignored by Git, not encrypted. The SDK transport is tested for interoperability, not certified for every MCP conformance case. The package does not contain a personal calendar connector, credentials or a hosted deployment.

## Sources checked

- Amazon official rules: https://amazonappdev2026.devpost.com/rules
- Amazon organizer FAQ: https://amazonappdev2026.devpost.com/details/faqs
- Official pinned SDK source/docs: https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/v1.30.0/README.md

The organizer FAQ says gated Alexa+ tools are unavailable to hackathon participants, and a web page making actual initialize/tools-list/tools-call requests over Streamable HTTP can demonstrate a self-hosted MCP server. This lab does not claim to connect to Alexa+.
