set shell := ["bash", "-lc"]

default:
	@just --list

test:
	python -m pytest tests/ -q

web-build:
	cd web && npm run build

lint:
	ruff check amythest tests
	cd web && npx next lint || true

package:
	python -m build --wheel --sdist

verify: test web-build lint package

ci: verify
	@if command -v dvc >/dev/null 2>&1; then dvc doctor || true; else echo "DVC not installed; skipping"; fi

cd:
	bash scripts/cd.sh

clean:
	rm -rf .amythest web/out web/.next tmp_training_artifacts

training-install:
	pip install -e ".[training]"
