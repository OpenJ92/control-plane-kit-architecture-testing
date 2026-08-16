# Git Flow

Normal development follows:

```text
main
  develop
    codex/<issue-id>-<slug>
```

- `main` contains accepted coherent releases.
- `develop` integrates reviewed child issues in dependency order.
- `codex/*` branches begin at the exact accepted `develop` coordinate and open
  pull requests into `develop`.
- `develop` reaches `main` only through a reviewed promotion after the parent
  acceptance laws pass.

Do not push feature implementation directly to `main` or `develop`. The empty
genesis commit shared by both branches is the one bootstrap exception.
