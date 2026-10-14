# Try Veil privately

This is a local synthetic calendar demo, not live Alexa or a real-calendar
privacy guarantee. No account, key, spend or Python package is needed.
Use a computer with Python3.10 or newer. The ZIP is not a phone-hosted app.

## Start

1. Extract the full ZIP and open a terminal in its `veil` folder.
2. Run `python3 server.py`.
3. Open `http://127.0.0.1:8765` in your browser.

If the server reports that port8765 is busy, stop the other process using it.
Keep the terminal open. Press Ctrl+C there when finished.

## The original three-step comparison

1. Click Reset both runs, then advance twice.
2. The unguarded side reaches 100% support for the protected fact; guarded stays 50%.
3. Advance again. Unguarded picks early prep; guarded picks dinner.
4. Reload. The guided history should remain at step 3.

The synthetic operator page shows both calendars. It is not recipient separation
or secure storage. Reset starts a new experiment, not a real privacy-budget reset.

## Try the selected conversation lab

Open "Try another synthetic scenario". Pick fictional calendars, ONE protected
window, public prior/costs and a public limit. Run or compare the experiment.
Changing lab controls does not change an existing saved dialogue. Start a new
synthetic dialogue to bind them, choose a supported shortcut, then Ask and remember.
Reload to inspect the bound parameters/history. Unsupported language refuses;
this is a typed vocabulary, not general natural-language understanding.

Open the explicit-model section and load the ordinary-query example. It uses a
deliberately constructed four-world prior, not learned household behavior. Two
ordinary availability replies together reveal early prep in that declared model;
the guard refuses the second and schedules cleanup.

## Check downloaded evidence

Save a dialogue audit, then run:

    python3 audit_export.py --verify downloaded-audit.json

Save an imported-result download, then run:

    python3 experiment_spec.py --verify-result downloaded-result.json

Run the default test suite:

    python3 verify_all.py

Tests do not book a calendar, send messages, use accounts or contact APIs.
Supported policies can decline a feasible meeting. NO_MEETING means no result
from the selected policy, not proof that no common window exists. Zero change
in one protected fact does not mean zero disclosure of other calendar details.

The demo covers one observer, one fact and declared finite worlds only. No public
release, hosting, project license, submission or live Alexa connection is included.

`verify_all.py --full` also runs the original audience-sequence and weighted-
audience sweeps. Expanded seven-intent and adaptive replays are separate:

    python3 extended_sequence_sweep.py --from-bob 0 --to-bob 4
    python3 adaptive_dialog_sweep.py

The first command is one resident batch; repeat ranges 4..8, 8..12, 12..16 for the
full expanded model. See VALIDATION.md for completed measured checkpoints, not
an assumption that every check runs in the default command.

The full-visible weighted adaptive response check is another separate replay:

    python3 full_dialogue_sweep.py

It includes explanations and safe-next suggestions as observable results.
