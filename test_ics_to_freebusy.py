import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from ics_to_freebusy import convert, parse_duration, unfold
from calendar_input import minimize

ROOT = Path(__file__).parent
CASES = ROOT / 'examples' / 'public-cases'
ASOF = '2026-10-16T21:30:00+05:30'

# Expected free masks recomputed by hand from the pinned real feeds.
EXPECTED_MASKS = {
    'fosdem-2026-sunday': 1,        # only the pre-09:00 Brussels window is free
    'epl-2026-10-17': 1,            # only the 08:00-09:30 UTC window is free
    'india-holidays-diwali-2026': 0,  # merged all-day block covers both days' windows
    'f1-las-vegas-2026': 12,        # race overlaps windows 0,1; windows 2,3 free
}


class ParserTests(unittest.TestCase):
    def test_unfold_continuation(self):
        self.assertEqual(unfold('A:abc\r\n def\r\nB:x\n'), ['A:abcdef', 'B:x'])

    def test_z_timestamps(self):
        ics = 'X-WR-TIMEZONE:UTC\nBEGIN:VEVENT\nDTSTART:20261017T113000Z\nDTEND:20261017T131500Z\nEND:VEVENT'
        payload, stats = convert(ics, 'pub', '2026-10-17T00:00:00Z', '2026-10-18T00:00:00Z')
        self.assertEqual(payload['calendars']['pub']['busy'],
                         [{'start': '2026-10-17T11:30:00+00:00', 'end': '2026-10-17T13:15:00+00:00'}])
        self.assertEqual(stats['skipped_malformed_events'], 0)

    def test_floating_uses_feed_timezone(self):
        ics = 'X-WR-TIMEZONE;VALUE=TEXT:Europe/Brussels\nBEGIN:VEVENT\nDTSTART:20260201T090000\nDTEND:20260201T095000\nEND:VEVENT'
        payload, _ = convert(ics, 'pub', '2026-02-01T00:00:00+01:00', '2026-02-02T00:00:00+01:00')
        self.assertEqual(payload['calendars']['pub']['busy'][0]['start'], '2026-02-01T09:00:00+01:00')

    def test_explicit_tzid_beats_feed_timezone(self):
        ics = ('X-WR-TIMEZONE:UTC\nBEGIN:VEVENT\nDTSTART;TZID=Asia/Kolkata:20261017T170000\n'
               'DTEND;TZID=Asia/Kolkata:20261017T180000\nEND:VEVENT')
        payload, _ = convert(ics, 'pub', '2026-10-17T00:00:00Z', '2026-10-18T00:00:00Z')
        from calendar_input import instant
        self.assertEqual(instant(payload['calendars']['pub']['busy'][0]['start']),
                         instant('2026-10-17T11:30:00Z'))

    def test_all_day_becomes_utc_midnight_to_midnight(self):
        ics = 'BEGIN:VEVENT\nDTSTART;VALUE=DATE:20261108\nDTEND;VALUE=DATE:20261109\nEND:VEVENT'
        payload, stats = convert(ics, 'pub', '2026-11-08T00:00:00Z', '2026-11-10T00:00:00Z')
        self.assertEqual(payload['calendars']['pub']['busy'],
                         [{'start': '2026-11-08T00:00:00+00:00', 'end': '2026-11-09T00:00:00+00:00'}])
        self.assertEqual(stats['all_day_events_in_range'], 1)

    def test_recurring_events_skipped_not_expanded(self):
        ics = ('BEGIN:VEVENT\nDTSTART:20261017T100000Z\nDTEND:20261017T110000Z\nRRULE:FREQ=WEEKLY\nEND:VEVENT\n'
               'BEGIN:VEVENT\nDTSTART:20261017T120000Z\nDTEND:20261017T130000Z\nEND:VEVENT')
        payload, stats = convert(ics, 'pub', '2026-10-17T00:00:00Z', '2026-10-18T00:00:00Z')
        self.assertEqual(stats['skipped_recurring_events'], 1)
        self.assertEqual(len(payload['calendars']['pub']['busy']), 1)

    def test_overlaps_merged_and_clipped_to_coverage(self):
        ics = ('BEGIN:VEVENT\nDTSTART:20261017T090000Z\nDTEND:20261017T100000Z\nEND:VEVENT\n'
               'BEGIN:VEVENT\nDTSTART:20261017T093000Z\nDTEND:20261017T110000Z\nEND:VEVENT\n'
               'BEGIN:VEVENT\nDTSTART:20261016T230000Z\nDTEND:20261017T010000Z\nEND:VEVENT')
        payload, _ = convert(ics, 'pub', '2026-10-17T00:00:00Z', '2026-10-18T00:00:00Z')
        self.assertEqual(payload['calendars']['pub']['busy'], [
            {'start': '2026-10-17T00:00:00+00:00', 'end': '2026-10-17T01:00:00+00:00'},
            {'start': '2026-10-17T09:00:00+00:00', 'end': '2026-10-17T11:00:00+00:00'}])

    def test_duration_fallback(self):
        self.assertEqual(parse_duration('PT1H45M').total_seconds(), 6300)

    def test_no_metadata_leaks(self):
        ics = ('BEGIN:VEVENT\nUID:secret-uid@x\nSUMMARY:Private thing\nLOCATION:Somewhere\n'
               'DTSTART:20261017T100000Z\nDTEND:20261017T110000Z\nEND:VEVENT')
        payload, _ = convert(ics, 'pub', '2026-10-17T00:00:00Z', '2026-10-18T00:00:00Z')
        self.assertNotIn('secret', json.dumps(payload))
        self.assertNotIn('Private', json.dumps(payload))


class PublicCaseTests(unittest.TestCase):
    def test_pinned_real_feeds_give_expected_masks(self):
        for name, mask in EXPECTED_MASKS.items():
            d = CASES / name
            payload = json.loads((d / 'freebusy.json').read_text())
            windows = json.loads((d / 'windows.json').read_text())
            with self.subTest(case=name):
                snap = minimize(payload, windows, source='real-public-ics', as_of=ASOF)
                self.assertEqual(snap['free_mask'], mask)
                self.assertEqual(snap['source'], 'real-public-ics')

    def test_real_api_error_response_fails_closed(self):
        # Shape actually returned by Google free/busy for the public holiday
        # calendar (domain=global, reason=notFound) on 2026-10-16.
        payload = {'start': '2026-11-08T00:00:00Z', 'end': '2026-11-10T00:00:00Z',
                   'calendars': {'en.indian#holiday@group.v.calendar.google.com':
                                 {'busy': [], 'errors': [{'domain': 'global', 'reason': 'notFound'}]}}}
        windows = json.loads((CASES / 'india-holidays-diwali-2026' / 'windows.json').read_text())
        with self.assertRaises(ValueError):
            minimize(payload, windows, source='live-google-freebusy', as_of=ASOF)

    def test_no_events_means_free_in_this_calendar_only(self):
        payload = {'start': '2026-10-16T00:00:00+05:30', 'end': '2026-10-23T00:00:00+05:30',
                   'calendars': {'primary': {'busy': [], 'errors': []}}}
        windows = [{'start': f'2026-10-{17+i}T10:00:00+05:30', 'end': f'2026-10-{17+i}T11:00:00+05:30'}
                   for i in range(4)]
        snap = minimize(payload, windows, source='live-google-freebusy', as_of=ASOF)
        self.assertEqual(snap['free_mask'], 15)


if __name__ == '__main__':
    unittest.main()
