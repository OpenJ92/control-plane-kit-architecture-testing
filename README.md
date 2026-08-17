# control-plane-kit-architecture-testing

Standard-library-only architecture testing language for Control Plane Kit
repositories.

This repository is development tooling. Production packages, services, SDKs,
interpreters, providers, and OCI images must not depend on or contain it.
Consumers install an exact reviewed source coordinate for test execution and
own their concrete architecture decisions.

## Python source facts

The immutable source-fact language describes imports, aliases, and lexical call
targets without reading files or executing inspected code. `analyze_source`
interprets caller-supplied Python text using the executing Python version's
standard-library AST grammar.

## Architecture policies

Closed import-surface and call-surface policies compare admitted source facts
with exact expected multisets. Evaluation is deterministic, bounded, and pure;
consumers own their repository-specific allowlists.

## Reproducible release candidates

Repository-only support defines the exact build-input lock, immutable release
report, canonical report codec, and complete wheel/source-distribution verifier
for version `0.1.0`. These values verify already-produced candidate bytes. The
later build stage owns acquisition and isolated construction, and the candidate
is not published by this stage.

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

The installed package performs no filesystem scanning, environment access,
plugin discovery, logging, process execution, network access, mutation,
rewrite, or autofix. Caller-supplied source text and admitted facts remain
bounded values. Repository-only artifact verification reads only the explicitly
selected candidate directory and never publishes or repairs its contents.
