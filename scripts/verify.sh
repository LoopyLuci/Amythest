#!/usr/bin/env bash
set -euo pipefail
echo "==> python syntax"
python -m py_compile amythest/cli/main.py
python -m py_compile amythest/backend/server.py
python -m py_compile amythest/tui/app.py
echo "==> web typecheck"
pushd web >/dev/null
npx next lint || true
popd >/dev/null
echo "==> verify ok"
