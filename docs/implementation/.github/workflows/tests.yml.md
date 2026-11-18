Source: [.github/workflows/tests.yml](../../../../.github/workflows/tests.yml).
Maintain this document alongside its source file. When the source or relevant
imported contracts change, verify and update this companion in the same change.

This workflow invokes the repository's authoritative test.sh on develop-targeted PRs, main/develop pushes and manual dispatch. It selects the runner, checkout action, read-only contents permission, timeout and cancellation grouping; it does not reimplement package tests. A feature branch targeting a different PR base may not receive this workflow. A cancelled run is not success, and concurrency grouping can cancel an older run on the same ref. Changes to CI or gate prerequisites must remain coordinated with the actual harness.
