# Real public-calendar cases (branch lab/real-public-calendar-cases-20261016)

Built 2026-10-16 on top of `lab/real-calendar-mcp-20261016` (commit 8a544ff).
Goal: test the real-input path (importer + joint guard + official-SDK MCP route)
against real, busy, real-world schedule data instead of made-up fixtures.

## Data: real and public

All four pinned cases under `examples/public-cases/` derive ONLY busy/free
timing from real public iCalendar feeds. Event titles, places, people and UIDs
are discarded by the converter (`ics_to_freebusy.py`). No personal calendar
data is in any case, snapshot, ledger or result file.

| case | real source (fetched 2026-10-16) | shape | free_mask |
|---|---|---|---|
| fosdem-2026-sunday | https://fosdem.org/2026/schedule/ical | 1079 real events, floating times in Europe/Brussels, merged to one 09:00-18:15 block | 1 |
| epl-2026-10-17 | https://ics.fixtur.es/v2/league/premier-league.ics | real Premier League fixtures for Sat 17 Oct 2026, UTC kickoffs (11:30 / 14:00 / 16:30) | 1 |
| india-holidays-diwali-2026 | https://calendar.google.com/calendar/ical/en.indian%23holiday%40group.v.calendar.google.com/public/basic.ics | real all-day VALUE=DATE events; merged block spans midnight UTC both days | 0 |
| f1-las-vegas-2026 | https://f1calendar.com/download/f1-calendar_gp.ics | real night race 22 Nov 2026 04:00-06:00 UTC; partial overlaps on both window edges | 12 |

A fifth live check used the owner's connected Google account read-only on
2026-10-16: the real free/busy API returns `notFound` for the public holiday
calendar (Google does not serve free/busy for it) - the importer refuses this
response (fail closed: availability unknown is not free), covered by
`test_real_api_error_response_fails_closed`. A fresh free/busy read of the
owner's primary calendar for 16-23 Oct 2026 again returned zero busy
intervals, so it added no new busy evidence; the raw response was not kept.

## Verified

- Conversion of 4,622 real events across 4 feeds: UTC `Z` times, explicit
  TZID, floating times under `X-WR-TIMEZONE`, all-day DATE events, RRULE
  events skipped and counted, overlap merging, coverage clipping. 12 new
  converter/importer tests (`test_ics_to_freebusy.py`).
- Each case minimizes through `calendar_input.py` under the new honest
  provenance label `real-public-ics` and passes the official-SDK MCP check
  (protocol 2025-11-25, Streamable HTTP) TWICE per case including restart
  persistence (`run_public_cases.py`, results in
  `validation-results/public-cases/`). Truthful outputs are asserted against
  the private mask; nothing private is printed.
- Joint guard on real masks: direct questions about jointly protected windows
  0 and 1 are refused (`NEEDS_PRIVATE_DECISION`); unprotected windows answer
  truthfully; scheduling still finds a real free window (f1 case).
- Regression: full suite 270 tests OK, 4 SDK network tests OK, 44 existing
  server/http tests OK, 5 new fold-in page tests OK (`test_real_demo.py`).

## Demo fold-in (same branch)

`/real` on the local demo server runs the same importer + joint guard over
the pinned public cases with provenance shown in the UI (source URL, fetch
date, event counts). It is honestly labelled: real public timing data,
declared model assumptions, not a real-world privacy guarantee. The page
uses the same `CalendarGuard` the MCP SDK server wraps; MCP transport detail
stays in MCP.md. The original synthetic pages are unchanged.

## Not verified / limits

- No real PERSON's busy calendar has been run: the owner's primary is free
  for the tested week and holiday/classroom shared calendars expose no busy
  intervals via free/busy. Diverse personal busy-calendar behavior remains
  unvalidated.
- Public feeds are historical/future public schedules, not live availability;
  `real-public-ics` snapshots do not pause after 30 minutes (that rule only
  fits `live-google-freebusy`). They are one-time reads of pinned feeds.
- All-day events are approximated as UTC midnight-to-midnight; the holiday
  feed carries no timezone of its own.
- Recurring (RRULE) events are skipped, not expanded (none were present in
  the pinned ranges; they are counted in meta.json if they appear).
- Feed correctness is taken as published; no independent verification of the
  schedules themselves.
- Still no real Alexa+, LLM, second person's calendar, continuous sync or
  actual booking.
