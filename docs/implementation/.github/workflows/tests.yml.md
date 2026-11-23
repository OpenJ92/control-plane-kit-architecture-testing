Source: [.github/workflows/tests.yml](../../../../.github/workflows/tests.yml).
Maintain this document alongside its source file. When the source or relevant
imported contracts change, verify and update this companion in the same change.

The workflow runs the repository's Docker-backed `./test.sh` on pull requests
targeting `main`, pushes to `main`, and manual dispatch. It selects the runner,
pinned checkout action, read-only contents permission and timeout. A newer run
in the same workflow and ref group can cancel an older one. Verify the result
for the revision being reviewed.
