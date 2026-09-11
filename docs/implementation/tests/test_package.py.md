Source: [tests/test_package.py](../../../tests/test_package.py).
Maintain this document alongside its source file. When the source or relevant imported contracts change, verify and update this companion in the same change.

This file checks the accepted package facade, dependency-free runtime metadata,
repository scaffold and Docker gate wiring. Its fixture expects the checkout
mounted as /source by [test.sh](../test.sh.md); running it from an arbitrary
directory is not an equivalent invocation.

Gate/workflow tests inspect selected source markers and executable mode. They
do not run each declared phase or prove a pinned image was downloaded. Installed
artifact behavior is separately exercised by the gate's package smoke helpers.
The GenesisPackageTests name is historical: the asserted facade now includes
source facts and policy evaluation, not merely __version__. Coordinate
intentional public-surface changes across these assertions, metadata and smoke
helpers rather than treating the old README genesis description as current.
