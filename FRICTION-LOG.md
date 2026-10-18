# Friction log - Amazon Developer Hackathon (Alexa+ track)

Real integration friction hit while building Veil, a self-hosted MCP server
(JSON-RPC 2.0 over Streamable HTTP, protocol 2025-11-25) with a simulated
Alexa+ web client. Dates are IST. Each entry lists impact and the workaround
we shipped.

## 1. No participant access to gated Alexa+ developer tools (2026-10-13)
Per the hackathon FAQ, participants get no access to the gated Alexa+
developer tools (Category SDK, MCP Toolkit, CLI, Web Simulator). There is no
way to validate a project against the real Alexa+ runtime - voice
turn-taking, card rendering, session behavior, account linking.
Workaround: built a simulated Alexa+ web client (`/alexa`) over our own MCP
server, following the public spec, and used the official MCP Python SDK
client as the interoperability stand-in. The simulation is labelled as such
everywhere it appears. What would help: a read-only hosted "hello world"
endpoint or a conformance suite for the real runtime, even without device
features.

## 2. Streamable HTTP: client boot reconciliation is unspecified (2026-10-14/15)
Spec 2025-11-25 defines sessions (Mcp-Session-Id) but not how a web client
should attach to an existing server session. Two real defects followed:
(a) a two-call check-then-start was not atomic - a delayed second tab could
read "no session" before the first tab's start landed, then start AFTER an
answer had landed, silently wiping a live session's ledger;
(b) an unrecognized or failed status response failed OPEN toward a fresh
start, again erasing state.
Workaround: atomic `only_if_uninitialized` start under the server lock and a
fail-closed attach path ("session state unknown, no automatic reset"). What
would help: a spec note or reference flow for idempotent client boot over
Streamable HTTP.

## 3. Session attach semantics and edge codes (2026-10-15)
A tab attaching to an existing session must learn the session's active
configuration; nothing in the spec carries it, and showing local defaults
made the UI lie about a live session. Recovery behavior for 404 (unknown
session), 400 (unsupported protocol version) and DELETE teardown also had to
be hand-rolled.
Workaround: operator view doubles as the config source of truth; attach syncs
from it. Covered by driven-browser tests.

## 4. Concurrency guidance for stateful tools (2026-10-15)
The spec is silent on serializing tool calls that share server-side state.
40 fully interleaved concurrent calls across two MCP surfaces only stayed
consistent after we put all tool handling under one process lock with atomic
(tmp + fsync + replace) session writes. A short "stateful servers" section in
the docs would save every multi-tab builder the same discovery.

## 5. Official MCP Python SDK v2 renamed FastMCP (2026-10-18)
A fresh `pip install mcp` today installs 2.x, where `mcp.server.fastmcp`
(FastMCP) was renamed to MCPServer. Code written against the v1 API - what
the current getting-started material produces - fails at import. The
in-product error message pointing at the migration guide was genuinely
helpful, but a deprecation window or an alias would have avoided the break.
Workaround: pinned `mcp<2` (1.30.0); migration to MCPServer planned
post-submission.

## 6. Real calendar data: Google free/busy and ICS in the wild (2026-10-16/17)
Testing against real schedule data surfaced two things: Google Calendar's
free/busy API returns `notFound` for the public holiday calendar (an
availability-unknown response that must fail closed, not read as "free"),
and real public ICS feeds exercise the awkward corners - UTC `Z` times,
explicit TZID, floating times under X-WR-TIMEZONE, all-day VALUE=DATE events
spanning midnight UTC, RRULE recurrences. Our importer now covers 4,622 real
events across 4 feeds; RRULE events are skipped and counted rather than
expanded silently.

## What worked well
- The MCP spec's JSON-RPC 2.0 core and the initialize / tools/list /
  tools/call flow: a stdlib-only implementation interoperated with the
  official Python SDK client on the first recorded run.
- The 2025-11-25 protocol-version negotiation shape (explicit version
  header, clean 400 on unsupported) made version handling testable.
- The SDK's v2 migration error message names the rename and links the
  migration guide - best-case breakage UX.
