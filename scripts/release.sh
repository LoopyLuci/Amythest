#!/usr/bin/env bash
set -euo pipefail
BUMP="${1:-patch}"
echo "==> bump version"
python scripts/bump_version.py "${BUMP}"
echo "==> build packages"
python -m build
echo "==> lint + test"
bash scripts/ci.sh
echo "==> tag"
TAG="v$(python -c 'import tomllib; print(tomllib.load(open("pyproject.toml","rb"))["project"]["version"])')"
git tag -a "${TAG}" -m "Release ${TAG}" || true
git push origin "${TAG}" || true
echo "==> release prepared: ${TAG}"
