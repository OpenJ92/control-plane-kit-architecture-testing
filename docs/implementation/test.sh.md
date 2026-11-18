Source: [test.sh](../../test.sh).
Maintain this document alongside its source file. When the source or relevant
imported contracts change, verify and update this companion in the same change.

This is the owning executable gate, separate from the pure installed package.
It runs source tests, compilation and outside-source installation checks across
the selected Python image versions, then builds wheel/sdist and inspects and
installs the resulting wheel. Source is mounted read-only; work is copied into
container-local temporary directories. Build frontend/backend and image
coordinates are explicitly selected here and must be reviewed when adopted.

The shell uses fail-fast execution and serial stages. Completion of an early
Python/version phase is not completion of the build/artifact/install phases.
`docker run --rm` removes each container on exit; the script does not conduct a
separate residue audit or remove cached base images. It creates transient
containers even though README wording about creating no package-owned resources
can be read too broadly.

Dependencies include [artifact inspection](../../test_support/inspect_artifacts.py),
[installed-package admission](../../test_support/installed_package.py) and
[pyproject.toml](../../pyproject.toml). Package installation may use network
access; do not describe this harness as pure because the shipped language is
pure. Invoke it only through the repository's authorized Docker validation
workflow. Documentation authoring did not run the gate.
