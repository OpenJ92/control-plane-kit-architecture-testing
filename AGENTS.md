# control-plane-kit-architecture-testing Agent Guide

Canonical contract: `cpk-agent-contract/v1`

Source: [CPK #1741](https://github.com/OpenJ92/control-plane-kit/issues/1741).
This root guide carries the shared contract needed to work in this repository
without another checkout. Local testing-tool rules may tighten it; they may not
weaken authorization, Docker-only validation, truthful uncertainty, test
ownership, or GitHub-memory requirements.

## Shared Product Boundary

CPK is a human-authorized, AI-assisted infrastructure control plane. Providers
own external runtime truth. CPK owns topology, inspectable plans, execution of
approved actions, durable history, and truthful bounded reports. Consequential
mutation, destructive cleanup, public exposure, cost/capacity or credential
changes, cross-provider movement, adoption, and ambiguous retry require
explicit approval. Never fabricate success, ownership, graph advancement, or
cleanup, and never blindly redispatch an ambiguous external mutation.

This repository is pure development tooling. It does not grant provider,
runtime, product, or control-plane authority and must not become a parallel
implementation of another package's semantics.

## Durable Memory And Collaboration

GitHub issues, PRs, and material comments are durable project memory. Commits,
hashes, local logs, `/tmp` packets, inventories, task messages, and chat are
supporting coordinates only. Record decisions, releases, stops, evidence
meaning, reviews, and handoffs on the governing issue or PR.

When roles are assigned, North coordinates; Vale implements the bounded change;
Meridian reviews independently and reports findings-first `PASS` or `HOLD`.
Assignments and handoffs state the GitHub artifact, base/destination, scope,
suite/prerequisites, authority limits, stop conditions, and next reviewer.
Silence is not approval.

Keep tests and review proportional. Architecture-testing owns a generic fact
and policy language, not source-layout ceremony for every consumer. Consumer
tests must not use it to police helper names, duplicate another package's state
machine, or turn fixture examples into runtime invariants.

## Shared Validation And Stops

All executable validation uses this repository's Docker-backed `./test.sh` and
its pinned Python images. Do not use host Python/PostgreSQL, venvs, host `pip`,
alternate databases, shims, or custom wrappers. If the suite or prerequisite is
missing, cannot start, or fails for apparatus, stop and ask; do not improvise,
silently retry, rebaseline, or repair shared state.

This repository has no provider/destructive authority. Stop when ownership,
base/destination, suite prerequisites, or GitHub/local decision state is
uncertain, or when a requested policy would encode another package's semantics.

`control-plane-kit-architecture-testing` is a separately installable,
standard-library-only development-tooling distribution for Control Plane Kit
repositories. Production packages and images must never depend on it.

## Branch Flow

Inherit only the branch topology documented in `GIT-FLOW.md`:

```text
main
  develop
    codex/<issue-id>-<slug>
```

Feature branches target `develop`. Promote `develop` to `main` only after a
coherent reviewed vertical is accepted.

The canonical proportional-evidence contract in this guide supersedes the
legacy mandatory-red process in `GIT-FLOW.md`.

## Issue Loop

For non-trivial work:

```text
current behavior and public contract
  -> smallest bounded implementation and proportional tests
    -> authoritative Docker-backed ./test.sh
      -> concrete review
        -> decision log and dependent handoff
```

Split work when facts, policy interpretation, consumer integration, or
reproducibility become independently meaningful review surfaces. Do not begin
a dependent child before its predecessor is accepted.

## Ownership

This repository owns generic test-time architecture language and its pure
interpretation. Consumer repositories own their concrete package boundaries,
allowed dependencies, call surfaces, and policy decisions.

The installed package must remain independent from Control Plane Kit Core,
Operations, SDKs, interpreters, servers, secrets, products, providers, and
entrypoints. It must not become a production dependency or an authority for
application behavior.

## Testing

Use `./test.sh` for authoritative validation. It runs standard-library
`unittest` in pinned Docker images and proves package build, compile, and
outside-source installation. Do not use host Python, pytest, hidden
collection, `xfail`, proof-changing options, or skips.

Tests must fail for missing behavior, not collection, imports, Docker setup,
or malformed fixtures. Use tests-before-source target-red evidence when an
explicit migration/parity contract or a necessary causality proof calls for it;
it is not universal ceremony.

## Security And Effects

The v0.1 installed package is pure development tooling. It must not read
repositories by itself, scan filesystems, inspect environment variables,
discover plugins, use clocks or ID generators, open network connections,
start subprocesses, log source, mutate files, rewrite code, or provide
autofixes.

Facts, errors, findings, tests, and logs must never retain or echo source text,
literal candidates, secrets, credentials, or arbitrary AST dumps. Every PR
must state new surfaces, supply-chain inputs, redaction behavior, mutation
authority, and residual risk even when the answer is none.

## Review And Handoff

Every PR receives a correctness, API, dependency, test-integrity, security,
and packaging review. Record exact base/head coordinates, owning validation,
chosen shape, rejected alternatives, risks, and the next child's accepted
handoff.
