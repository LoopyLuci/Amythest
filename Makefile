.PHONY: test web-build verify ci clean

test:
	python -m pytest tests/ -q

web-build:
	cd web && npm run build

verify: test web-build

ci: verify
	@if command -v dvc >/dev/null 2>&1; then dvc doctor || true; else echo "DVC not installed; skipping"; fi

clean:
	rm -rf .amythest web/out web/.next tmp_training_artifacts
