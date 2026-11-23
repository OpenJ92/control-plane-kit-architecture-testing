# Git Flow

`main` is the persistent integration branch.

1. Start a temporary `codex/<issue-id>-<slug>` branch at the accepted `main`
   commit. Record the base and the governing issue in the pull request.
2. Open the pull request against `main`. Integrate through the reviewed pull
   request after its Docker-backed `./test.sh` gate passes.
3. Verify the merged commit and record the handoff. Retire the temporary branch
   after checking for dependent work and active reservations.
