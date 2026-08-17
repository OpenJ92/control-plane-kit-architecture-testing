#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_FRONTEND="build==1.3.0"
BUILD_BACKEND="setuptools==83.0.0"
BUILD_INPUT_LOCK="$ROOT/test_support/build-inputs.json"
RELEASE_REPORT_SUPPORT="$ROOT/test_support/release_report.py"
OFFLINE_BUILD_INSTALL_FLAGS=(
  --no-index
  --find-links
  /tmp/build-wheelhouse
  --require-hashes
  --only-binary=:all:
  --no-deps
)

test -f "$BUILD_INPUT_LOCK"
test -f "$RELEASE_REPORT_SUPPORT"
echo "phase=reproducible-build contract=declared"

PYTHON_IMAGES=(
  "python:3.11-slim@sha256:a630a63cdb314e2d138a2fca3e375e319e8568346ffafac5b980f888630ac4f1"
  "python:3.12-slim@sha256:2c941e860699f878900b0edc2403613c234d4b32eda3cc9fa7036991a2a63c4a"
  "python:3.13-slim@sha256:ffb752e139c0a19692a43af8d8523b274222dd68eebad5d583b45c2201c6e30a"
  "python:3.14-slim@sha256:ce40764625a4ff50df3548277632e7f96c4e77fe75fa848aae9885476e7df5a4"
)

for image in "${PYTHON_IMAGES[@]}"; do
  version="${image#python:}"
  version="${version%%-*}"
  echo "phase=source-tests python=${version}"
  docker run --rm \
    -v "$ROOT:/source:ro" \
    -e PYTHONDONTWRITEBYTECODE=1 \
    -e "BUILD_BACKEND=$BUILD_BACKEND" \
    -e "CPK_PYTHON_VERSION=$version" \
    "$image" \
    sh -ceu '
      cd /source
      PYTHONPATH=src python -m unittest discover -s tests -v
      echo phase=compile
      mkdir /tmp/package
      cp -a /source/src /source/tests /tmp/package/
      cd /tmp/package
      python -m compileall src tests
      echo "phase=installed-package python=${CPK_PYTHON_VERSION}"
      mkdir /tmp/install-source
      cp /source/pyproject.toml /source/README.md /source/LICENSE /tmp/install-source/
      cp -a /source/src /tmp/install-source/
      python -m pip install --disable-pip-version-check "$BUILD_BACKEND" >/tmp/backend-install.log
      python -m pip install --no-build-isolation --no-deps /tmp/install-source >/tmp/package-install.log
      mkdir /tmp/outside
      cd /tmp/outside
      python /source/test_support/installed_package.py
    '
done

echo "phase=build"
docker run --rm \
  -v "$ROOT:/source:ro" \
  -e PYTHONDONTWRITEBYTECODE=1 \
  "${PYTHON_IMAGES[3]}" \
  sh -ceu "
    mkdir /tmp/package /tmp/outside
    cp /source/pyproject.toml /source/README.md /source/LICENSE /tmp/package/
    cp -a /source/src /source/tests /source/test_support /tmp/package/
    cd /tmp/package
    python -m pip install --disable-pip-version-check '${BUILD_FRONTEND}' '${BUILD_BACKEND}' >/tmp/build-install.log
    python -m build --sdist --wheel --no-isolation
    echo phase=artifact-inspection
    python test_support/inspect_artifacts.py dist
    echo phase=installed-package
    python -m venv /tmp/installed
    /tmp/installed/bin/python -m pip install --disable-pip-version-check --no-deps dist/*.whl >/tmp/package-install.log
    cd /tmp/outside
    /tmp/installed/bin/python /tmp/package/test_support/installed_package.py
  "
