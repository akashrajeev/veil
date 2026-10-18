# Veil - Devpost submission text (draft for review)

## Tagline
The conversation ledger for shared assistants: it checks what the whole
conversation reveals, so two harmless replies can't jointly expose someone's
private plan.

## Description (features and functionality)

A shared-home assistant answers everyone in the room, and every answer
teaches the room something. Ask about dinner, then about the early prep
window, and two perfectly ordinary replies can add up to certainty about a
plan someone wanted kept private. Today's assistants answer each turn in
isolation - the leak is in the combination.

Veil is a self-hosted MCP server (JSON-RPC 2.0 over Streamable HTTP, MCP
spec 2025-11-25) that puts a disclosure guard in front of a shared
assistant. It keeps a ledger of everything the room has heard and checks
every candidate reply - answers, refusals, and the final scheduling choice -
against the whole transcript before speaking.

What it does, live in the demo:

- Catches conversation-level leaks. Unguarded, the room narrows a private
  window from 16 possible calendars to 100% certainty in two questions. With
  Veil, the room stays at 50/50 - and the assistant still does its job,
  finding a shared dinner slot that reveals nothing new.
- Protects windows jointly, not just one at a time. A parity question that
  any per-window guard would answer is refused, because the answer would
  expose the joint pattern of two protected windows. All four joint patterns
  hold at their declared 25% while scheduling still succeeds.
- Refuses safely. A refusal is identical whether the hidden answer is yes or
  no, so even the refusal carries no information.
- Asks first when answering would disclose. The owner previews exactly what
  the room would learn (100% certainty, 8 calendars left) before approving a
  single answer. After a disclosure, direct answers pause until reset.
- Maintains state across sessions. The approval record and guard state are
  persisted and survive a full server restart - a context-aware add-on, not
  a stateless wrapper.
- Runs on real schedule data. Real public calendar feeds (a Premier League
  fixture list, an F1 race weekend, a conference schedule, public holidays),
  reduced to busy/free timing, flow through the same importer, guard, and
  MCP route: protected questions refused, unprotected answered truthfully, a
  real free window scheduled.

Every claim is executable and checkable: 63,840 exhaustive sweep runs with
zero tested violations across single-window and joint models, 5,376
weighted-prior joint runs, an injected leak caught in 24/24 transcript
groups, 448 approval-path runs with pending and declined replies
indistinguishable, and interoperability with the official MCP Python SDK
client. All results are measured inside the declared finite model; artifacts
ship in the repo under validation-results/.

The demo uses a simulated Alexa+ web client (clearly labelled), as the
hackathon rules allow: no Amazon service or device is contacted, and the MCP
server is the real integration surface.

Built by Akash Rajeev. Python standard library only - `python3 server.py`,
no keys, no installs.

## Product feedback (per tool/API/SDK)

### Model Context Protocol spec + modelcontextprotocol.io docs
- Used for: the entire integration surface - a self-hosted MCP server over
  Streamable HTTP, protocol 2025-11-25.
- Worked well: the JSON-RPC 2.0 core and initialize / tools/list /
  tools/call flow; a stdlib-only implementation interoperated with the
  official Python SDK client on the first run. Explicit protocol-version
  handling made version checks easy to test.
- Needs work: client boot reconciliation for existing sessions (idempotent
  attach), concurrency guidance for stateful tools, and recovery behavior
  for 404/400/DELETE session edges are unspecified - we hand-rolled all
  three. (Details in FRICTION-LOG.md.)
- Onboarding: zero to a working stdlib server in a day from the spec alone.
- Build again: Yes - the protocol is a clean fit for agent surfaces; we
  would adopt the real Alexa+ MCP toolkit the moment access opens.

### Official MCP Python SDK
- Used for: interoperability validation - the official client against our
  server, and a real-calendar MCP lab client/server pair.
- Worked well: first-run interop against a from-spec server; the v2
  migration error message names the rename and links the migration guide.
- Needs work: the 2.x release renamed FastMCP to MCPServer and broke v1-era
  imports on a fresh install; a deprecation alias would have avoided it. We
  pinned mcp<2.
- Onboarding: quickstart gets to hello world fast.
- Build again: Yes, on the pinned 1.x for now, migrating to 2.x with the
  guide.

### Google Calendar API (free/busy, read-only validation)
- Used for: validating the real-calendar input path against a live personal
  calendar, free/busy scope only.
- Worked well: clean free/busy query shape; fast.
- Needs work: free/busy returns notFound for the public holiday calendar -
  availability-unknown must not read as "free"; document the per-calendar
  coverage limits.
- Onboarding: OAuth setup was the slowest part; API use itself was simple.
- Build again: Yes for availability reads; we'd want a documented way to
  probe which calendars free/busy actually covers.

## Submission checklist state (for reviewer, not for the form)
- Demo video: Veil-final-demo-20261018.mp4, 2:32 (< 3:00), needs public
  YouTube upload by Akash.
- Repo: private github.com/akashrajeev/veil + judge collaborators, or public
  + LICENSE - Akash's call (prep done, see JUDGE-ACCESS.md).
- Friction log: FRICTION-LOG.md (in repo).
