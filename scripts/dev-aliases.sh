#!/usr/bin/env bash
#
# Dev aliases for the local PyPI release helper in ./scripts/pypi-release.sh.
#
# Usage:
#   source ./scripts/dev-aliases.sh
#
# Alias guide:
#   pver         Show the current package version from pyproject.toml.
#   pbump-patch  Bump patch version for bugfixes or compatible fixes.
#                Example: 0.1.0 -> 0.1.1
#   pbump-minor  Bump minor version for backward-compatible features.
#                Example: 0.1.0 -> 0.2.0
#   pbump-major  Bump major version for breaking changes.
#                Example: 0.1.0 -> 1.0.0
#   pbuild       Build the distribution artifacts into ./dist.
#   pcheck       Run twine checks against the built artifacts.
#   pupload-test Upload the current ./dist artifacts to TestPyPI.
#   pupload      Upload the current ./dist artifacts to PyPI.
#   prelease     One-command shortcut for:
#                ./scripts/pypi-release.sh release patch pypi
#                This bumps patch, builds, checks, and uploads to PyPI.
#
# Start-to-end example flow:
#   source ./scripts/dev-aliases.sh
#   pver
#   pbump-patch
#   pbuild
#   pcheck
#   pupload-test
#   pupload
#
# Example release sequence with versions:
#   Start at 0.1.0
#   Run pbump-patch  -> 0.1.1
#   Run pbuild       -> create dist artifacts for 0.1.1
#   Run pcheck       -> validate package metadata and files
#   Run pupload-test -> publish 0.1.1 to TestPyPI for verification
#   Run pupload      -> publish 0.1.1 to PyPI
#
# Shortcut alternative:

alias pver='./scripts/pypi-release.sh version'
alias pbump-patch='./scripts/pypi-release.sh version patch'
alias pbump-minor='./scripts/pypi-release.sh version minor'
alias pbump-major='./scripts/pypi-release.sh version major'
alias pbuild='./scripts/pypi-release.sh build'
alias pcheck='./scripts/pypi-release.sh check'
alias pupload='./scripts/pypi-release.sh upload pypi'
alias pupload-test='./scripts/pypi-release.sh upload testpypi'
alias prelease='./scripts/pypi-release.sh release patch pypi'
