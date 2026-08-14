#!/usr/bin/env bash
set -euo pipefail
ARTIFACT_DIR="${1:-tmp_training_artifacts}"
REMOTE="${2:-local}"
if ! command -v dvc >/dev/null 2>&1; then
  echo "DVC is not installed. Install with: pip install dvc" >&2
  exit 1
fi
dvc add "${ARTIFACT_DIR}"
dvc push -r "${REMOTE}"
git add "${ARTIFACT_DIR}.dvc" .gitignore
git commit -m "Add versioned training artifacts: ${ARTIFACT_DIR}"
git push
