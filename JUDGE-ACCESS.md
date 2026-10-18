# Judge access + submission runbook (prep only - needs Akash's go)

Status: PREPARED, nothing executed. Repo is still private
(github.com/akashrajeev/veil); nothing pushed, no collaborators added, no
visibility change, no Devpost submission.

## What's ready
- Branch `submission-ready` (bundle: veil-submission-ready.bundle): latest
  lab work (real public-calendar cases, /real demo page, 291 tests green:
  287 unit + 4 official-MCP-SDK network) plus LICENSE (MIT),
  FRICTION-LOG.md, DEVPOST-SUBMISSION.md, this file. All commits authored as
  Akash Rajeev <akashrajeev.313@gmail.com>, on the v8 baseline lineage.
- Final demo video in private Drive: Veil-final-demo-20261018.mp4 (2:32).

## Route A (recommended): keep repo private, add Amazon's judges
Rules allow a private repo shared with the Amazon team; access stays free
through Nov 20. Commands once Akash approves:
    git push origin submission-ready:main
    gh repo edit akashrajeev/veil --default-branch main   # if needed
    # Settings > Collaborators > Add people, all six from the rules page:
    #   chris-trag, knmeiss, giolaq, anishamalde, mosesroth, emersonsklar
    gh api repos/akashrajeev/veil/collaborators/chris-trag -X PUT
    gh api repos/akashrajeev/veil/collaborators/knmeiss -X PUT
    gh api repos/akashrajeev/veil/collaborators/giolaq -X PUT
    gh api repos/akashrajeev/veil/collaborators/anishamalde -X PUT
    gh api repos/akashrajeev/veil/collaborators/mosesroth -X PUT
    gh api repos/akashrajeev/veil/collaborators/emersonsklar -X PUT
Why A first: zero permanence; collaborators can be removed after judging.
Note: main on GitHub is currently the older Oct 14 build (e17af19); pushing
submission-ready to main replaces it - that is the point, but it is his call.

## Route B: public repo
    git push origin submission-ready:main
    gh repo edit akashrajeev/veil --visibility public --accept-visibility-change-consequences
LICENSE (MIT) is already at the repo root so GitHub auto-detects it (rules:
license must be detectable at the top of the repo page).

## Then the Devpost form (akashrajeev.313@gmail.com, registered solo)
1. Upload Veil-final-demo-20261018.mp4 to his YouTube as PUBLIC (rules
   require public YouTube/Vimeo; judges not required to watch beyond 3:00).
2. Fill the form from DEVPOST-SUBMISSION.md: tagline, description, per-tool
   product feedback (MCP spec/docs, official MCP Python SDK, Google Calendar
   API).
3. Paste the repo URL; mention judge-collaborator access if Route A.
4. Submit before Friday Oct 23, 2026 12:00 PM PT (= Oct 24, 12:30 AM IST).

## Decisions that stay Akash's
- Route A vs B (private+judges vs public).
- YouTube upload visibility (public required by rules).
- Hitting submit on Devpost.
- License choice if he prefers Apache-2.0 over MIT (swap before pushing).
