# control-plane-kit-architecture-testing Agent Guide

`control-plane-kit-architecture-testing` is a separately installable,
standard-library-only development-tooling distribution for Control Plane Kit
repositories. Production packages and images must never depend on it.

## Branch Flow

Use the topology documented in `GIT-FLOW.md`:

```text
main
  develop
    codex/<issue-id>-<slug>
```

Feature branches target `develop`. Promote `develop` to `main` only after a
coherent reviewed vertical is accepted.

## Issue Loop

For non-trivial work:

```text
governing laws
  -> child dry run
    -> tests-only target red
      -> smallest implementation
        -> Docker package gate
          -> skeptical review
            -> dependent handoff
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

Issue #2 owns only the package and repository scaffold. Issue #3 owns the first
structural source language. Issue #4 owns policy and finding semantics. Issue
#5 owns reproducibility and first-consumer acceptance. Do not introduce those
later concepts early.

## Testing

Use `./test.sh` for authoritative validation. It runs standard-library
`unittest` in pinned Docker images and proves package build, compile, and
outside-source installation. Do not use host Python, pytest, hidden
collection, `xfail`, proof-changing options, or skips.

Tests must fail for missing behavior, not collection, imports, Docker setup,
or malformed fixtures. Preserve tests-before-source red evidence for every
semantic change.

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
and packaging review. Record exact base/head coordinates, red-to-green
evidence, chosen shape, rejected alternatives, risks, and the next child's
accepted handoff.
