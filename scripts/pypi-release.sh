#!/usr/bin/env bash
set -euo pipefail

#~/.pypirc at ~/

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYPROJECT="$ROOT_DIR/pyproject.toml"
PYTHON_BIN="${PYTHON_BIN:-python3}"
TWINE_CONFIG="${TWINE_CONFIG:-$HOME/.pypirc}"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/pypi-release.sh version [patch|minor|major|X.Y.Z]
  ./scripts/pypi-release.sh build
  ./scripts/pypi-release.sh check
  ./scripts/pypi-release.sh upload [pypi|testpypi]
  ./scripts/pypi-release.sh release [patch|minor|major|X.Y.Z] [pypi|testpypi]

Notes:
  - Requires: python build twine
  - Reads credentials from ~/.pypirc by default
EOF
}

ensure_tools() {
  command -v "$PYTHON_BIN" >/dev/null
  "$PYTHON_BIN" -m build --version >/dev/null
  "$PYTHON_BIN" -m twine --version >/dev/null
}

read_version() {
  "$PYTHON_BIN" - <<'PY'
import pathlib, re
text = pathlib.Path("pyproject.toml").read_text(encoding="utf-8")
m = re.search(r'(?m)^version\s*=\s*"([^"]+)"\s*$', text)
if not m:
    raise SystemExit("version not found in pyproject.toml")
print(m.group(1))
PY
}

set_version() {
  local target="$1"
  "$PYTHON_BIN" - "$target" <<'PY'
import pathlib, re, sys
target = sys.argv[1]
p = pathlib.Path("pyproject.toml")
text = p.read_text(encoding="utf-8")
new, n = re.subn(
    r'(?m)^(version\s*=\s*")([^"]+)("\s*)$',
    rf'\g<1>{target}\g<3>',
    text,
    count=1,
)
if n != 1:
    raise SystemExit("Failed to update version in pyproject.toml")
p.write_text(new, encoding="utf-8")
print(target)
PY
}

bump_semver() {
  local mode="$1"
  "$PYTHON_BIN" - "$mode" <<'PY'
import pathlib, re, sys
mode = sys.argv[1]
text = pathlib.Path("pyproject.toml").read_text(encoding="utf-8")
m = re.search(r'(?m)^version\s*=\s*"([^"]+)"\s*$', text)
if not m:
    raise SystemExit("version not found")
parts = m.group(1).split(".")
if len(parts) != 3 or not all(p.isdigit() for p in parts):
    raise SystemExit("version must be strict semver X.Y.Z for bump")
maj, mino, pat = map(int, parts)
if mode == "patch":
    pat += 1
elif mode == "minor":
    mino += 1
    pat = 0
elif mode == "major":
    maj += 1
    mino = 0
    pat = 0
else:
    raise SystemExit("invalid bump mode")
target = f"{maj}.{mino}.{pat}"
new, n = re.subn(
    r'(?m)^(version\s*=\s*")([^"]+)("\s*)$',
    rf'\g<1>{target}\g<3>',
    text,
    count=1,
)
if n != 1:
    raise SystemExit("failed to write version")
pathlib.Path("pyproject.toml").write_text(new, encoding="utf-8")
print(target)
PY
}

build_pkg() {
  rm -rf dist build *.egg-info
  "$PYTHON_BIN" -m build
}

check_pkg() {
  "$PYTHON_BIN" -m twine check dist/*
}

upload_pkg() {
  local repo="${1:-pypi}"
  if [[ ! -f "$TWINE_CONFIG" ]]; then
    echo "Missing twine config: $TWINE_CONFIG" >&2
    exit 1
  fi
  "$PYTHON_BIN" -m twine upload --config-file "$TWINE_CONFIG" --repository "$repo" dist/* --verbose
}

cmd="${1:-}"
case "$cmd" in
  version)
    ensure_tools
    arg="${2:-}"
    if [[ -z "$arg" ]]; then
      echo "Current version: $(read_version)"
      exit 0
    fi
    case "$arg" in
      patch|minor|major) nv="$(bump_semver "$arg")" ;;
      *) nv="$(set_version "$arg")" ;;
    esac
    echo "Version set to: $nv"
    ;;
  build)
    ensure_tools
    build_pkg
    ;;
  check)
    ensure_tools
    check_pkg
    ;;
  upload)
    ensure_tools
    upload_pkg "${2:-pypi}"
    ;;
  release)
    ensure_tools
    v="${2:-patch}"
    repo="${3:-pypi}"
    case "$v" in
      patch|minor|major) nv="$(bump_semver "$v")" ;;
      *) nv="$(set_version "$v")" ;;
    esac
    echo "Releasing version: $nv"
    build_pkg
    check_pkg
    upload_pkg "$repo"
    ;;
  *)
    usage
    exit 1
    ;;
esac
