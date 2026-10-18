"""Convert a PUBLIC iCalendar (.ics) feed into Google free/busy response shape.

Only timed busy intervals are derived. Event titles, descriptions, locations,
attendees, URLs and UIDs are discarded by design. Recurring events (RRULE) are
skipped and counted, not expanded. All-day VALUE=DATE events become
midnight-to-midnight UTC busy intervals (documented approximation).

Usage: ics_to_freebusy.py --ics feed.ics --calendar-id public-label \
  --start 2026-02-01T00:00:00+01:00 --end 2026-02-02T00:00:00+01:00 \
  --output freebusy.json --stats stats.json
"""
import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from calendar_input import instant, private_write

PROP = re.compile(r'^([A-Za-z0-9-]+)((?:;[A-Za-z0-9-]+=[^;:]+)*):(.*)$')


def unfold(text):
    lines = []
    for raw in text.replace('\r\n', '\n').replace('\r', '\n').split('\n'):
        if raw[:1] in (' ', '\t') and lines:
            lines[-1] += raw[1:]
        elif raw:
            lines.append(raw)
    return lines


def parse_dt(name, params, value, default_tz):
    value = value.strip()
    pmap = dict(p.lstrip(';').split('=', 1) for p in re.findall(r';[A-Za-z0-9-]+=[^;:]+', params))
    if pmap.get('VALUE') == 'DATE' or re.fullmatch(r'\d{8}', value):
        day = datetime.strptime(value, '%Y%m%d').replace(tzinfo=timezone.utc)
        return day, True
    if re.fullmatch(r'\d{8}T\d{6}Z', value):
        return datetime.strptime(value, '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc), False
    if not re.fullmatch(r'\d{8}T\d{6}', value):
        raise ValueError(f'unsupported {name} value: {value!r}')
    tz = ZoneInfo(pmap['TZID']) if 'TZID' in pmap else default_tz
    return datetime.strptime(value, '%Y%m%dT%H%M%S').replace(tzinfo=tz), False


def convert(ics_text, calendar_id, start, end):
    lines = unfold(ics_text)
    feed_tz = timezone.utc
    for line in lines:
        m = PROP.match(line)
        if m and m.group(1) == 'X-WR-TIMEZONE':
            try:
                feed_tz = ZoneInfo(m.group(3).strip())
            except Exception:
                feed_tz = timezone.utc
            break
    lo, hi = instant(start), instant(end)
    busy, skipped_recurring, skipped_malformed, all_day_count, total = [], 0, 0, 0, 0
    event = None
    for line in lines:
        if line == 'BEGIN:VEVENT':
            event = {}
        elif line == 'END:VEVENT' and event is not None:
            total += 1
            if 'RRULE' in event or 'RDATE' in event:
                skipped_recurring += 1
            elif 'DTSTART' not in event:
                skipped_malformed += 1
            else:
                s, s_allday = event['DTSTART']
                try:
                    if 'DTEND' in event:
                        e, _ = event['DTEND']
                    elif 'DURATION' in event:
                        e = s + parse_duration(event['DURATION'])
                    elif s_allday:
                        e = s + timedelta(days=1)
                    else:
                        raise ValueError('no end')
                except ValueError:
                    skipped_malformed += 1
                    event = None
                    continue
                if e > s and s < hi and e > lo:
                    if s_allday:
                        all_day_count += 1
                    busy.append((max(s, lo), min(e, hi)))
            event = None
        elif event is not None:
            m = PROP.match(line)
            if m and m.group(1) in ('DTSTART', 'DTEND', 'RRULE', 'RDATE', 'DURATION'):
                name, params, value = m.group(1), m.group(2), m.group(3)
                if name in ('DTSTART', 'DTEND'):
                    try:
                        event[name] = parse_dt(name, params, value, feed_tz)
                    except (ValueError, KeyError):
                        event['MALFORMED'] = True
                else:
                    event[name] = value.strip()
    busy.sort()
    merged = []
    for s, e in busy:
        if merged and s <= merged[-1][1]:
            if e > merged[-1][1]:
                merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    payload = {'start': start, 'end': end, 'calendars': {calendar_id: {
        'busy': [{'start': s.isoformat(), 'end': e.isoformat()} for s, e in merged]}}}
    stats = {'calendar_id': calendar_id, 'feed_timezone': str(feed_tz),
             'total_vevents': total, 'busy_intervals_in_range': len(merged),
             'all_day_events_in_range': all_day_count,
             'skipped_recurring_events': skipped_recurring,
             'skipped_malformed_events': skipped_malformed,
             'coverage': {'start': start, 'end': end}}
    return payload, stats


def parse_duration(value):
    m = re.fullmatch(r'P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?', value.strip())
    if not m:
        raise ValueError(f'unsupported DURATION: {value!r}')
    d, h, mi, s = (int(g) if g else 0 for g in m.groups())
    return timedelta(days=d, hours=h, minutes=mi, seconds=s)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ics', required=True)
    p.add_argument('--calendar-id', required=True)
    p.add_argument('--start', required=True)
    p.add_argument('--end', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--stats', required=True)
    a = p.parse_args()
    payload, stats = convert(Path(a.ics).read_text(encoding='utf-8', errors='replace'),
                             a.calendar_id, a.start, a.end)
    private_write(a.output, payload)
    Path(a.stats).write_text(json.dumps(stats, indent=2, sort_keys=True))
    print(json.dumps(stats, sort_keys=True))
