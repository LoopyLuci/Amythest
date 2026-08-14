#!/usr/bin/env bash
set -euo pipefail
echo "==> pytest"
python -m pytest tests/ -q
echo "==> web build"
pushd web >/dev/null
npm run build
popd >/dev/null
echo "==> DVC dry-run"
if command -v dvc >/dev/null 2>&1; then
  dvc doctor || true
else
  echo "DVC not installed; skipping dvc doctor"
fi
echo "==> done"
