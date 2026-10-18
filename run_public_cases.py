"""Re-run every pinned public real-feed case through the importer and the
official-SDK MCP route (twice, for restart persistence). Writes aggregate
validation results only: no busy intervals, windows or masks are printed,
but masks ARE recorded in the result files (public schedule data only)."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from calendar_input import minimize

ROOT = Path(__file__).parent
CASES = ROOT / 'examples' / 'public-cases'
OUT = ROOT / 'validation-results' / 'public-cases'
ASOF = '2026-10-16T21:30:00+05:30'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    summary = []
    for case_dir in sorted(CASES.iterdir()):
        if not (case_dir / 'freebusy.json').exists():
            continue
        name = case_dir.name
        meta = json.loads((case_dir / 'meta.json').read_text())
        payload = json.loads((case_dir / 'freebusy.json').read_text())
        windows = json.loads((case_dir / 'windows.json').read_text())
        snap = minimize(payload, windows, source='real-public-ics', as_of=ASOF)
        with tempfile.TemporaryDirectory() as tmp:
            snap_path = Path(tmp) / 'snapshot.json'
            state_path = Path(tmp) / 'ledger.json'
            snap_path.write_text(json.dumps(snap))
            runs = []
            for _ in range(2):  # second run reuses the ledger: restart persistence
                proc = subprocess.run(
                    [sys.executable, str(ROOT / 'run_calendar_sdk_check.py'),
                     '--snapshot', str(snap_path), '--state', str(state_path)],
                    capture_output=True, text=True, timeout=120)
                runs.append({'exit': proc.returncode,
                             'result': json.loads(proc.stdout.strip().splitlines()[-1]) if proc.returncode == 0 else None})
        record = {'case': name, 'description': meta['description'],
                  'source_url': meta['source_url'], 'fetched': meta['fetched'],
                  'conversion': meta['conversion'], 'free_mask': snap['free_mask'],
                  'sdk_runs': runs,
                  'passed': all(r['exit'] == 0 and r['result'] and r['result']['passed'] for r in runs)}
        (OUT / f'{name}.json').write_text(json.dumps(record, indent=1, sort_keys=True))
        summary.append({'case': name, 'free_mask': snap['free_mask'], 'passed': record['passed']})
        print(json.dumps(summary[-1], sort_keys=True))
    ok = all(s['passed'] for s in summary)
    print(json.dumps({'all_passed': ok, 'cases': len(summary)}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
