# control-plane-kit-architecture-testing

Standard-library-only architecture testing language for Control Plane Kit
repositories.

This repository is development tooling. Production packages, services, SDKs,
interpreters, providers, and OCI images must not depend on or contain it.
Consumers install an exact reviewed source coordinate for test execution and
own their concrete architecture decisions.

## Genesis Surface

Version `0.1.0` establishes only one importable package namespace:

```python
from control_plane_kit_architecture_testing import __version__

assert __version__ == "0.1.0"
```

The root export is deliberately limited to `__version__`. Follow-up issues add
the first immutable language and interpretation boundaries tests-before-source.

## Install

Install from a checkout:

```bash
python -m pip install .
```

The distribution has no runtime dependencies and supports Python 3.11 through
Python 3.14. It is not published to a package index by this issue.

## Test

Run the authoritative Docker-first package gate:

```bash
./test.sh
```

The gate uses immutable Python image coordinates, runs `unittest` and compile
proofs on every supported version, builds both wheel and source distribution,
inspects the artifacts, and imports the installed wheel outside the checkout.
It creates no package-owned container, network, volume, or image; immutable
Python base images may remain in Docker's ordinary local cache.

## Security

The genesis package performs no source inspection, filesystem scanning,
environment access, plugin discovery, logging, subprocess, network, mutation,
rewrite, or autofix. Docker and package construction exist only in the
repository test gate.
