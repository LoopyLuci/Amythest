# Amythest Development Roadmap

## Goal
Turn Amythest from a demo harness into a production-ready modular model runtime with real inference, trained modules, semantic selection, atomic checkpointing, and functional interfaces.

---

## Phase 1 — Runtime foundation
**Status:** Complete

- [x] Core module package format (`.apkg`)
- [x] SQLite-backed module database
- [x] CLI: install/activate/deactivate/list/status
- [x] Textual TUI with module management
- [x] FastAPI backend: modules, HITL, status, usage
- [x] Next.js web dashboard with live API data
- [x] Tests + smoke test + server verification

## Phase 2 — Intelligence and selection
**Status:** Complete

- [x] Semantic module index with FAISS + fallback
- [x] Auto-rebuild index on module changes
- [x] `POST /recommend` endpoint
- [x] Usage tracking API (`POST /usage`, `/usage/rate`)
- [x] `/metrics` endpoint
- [x] Local inference fallback (`POST /v1/completions`)

## Phase 3 — Training, checkpointing, and hardware
**Status:** Complete

- [x] LoRA training pipeline (`amythest/encoding/train.py`)
- [x] Trainer packaging helpers (`write_adapter_bytes`, `package_module_outputs`)
- [x] Adapter export + `.apkg` packaging verified end-to-end
- [x] Atomic checkpoint + rollback endpoints
- [x] Hardware optimization: device map, 4-bit quantization knobs
- [x] Optional DVC dependency and artifact tracking docs
- [x] Configurable HITL policy files (`amythest/policies/default.yaml`)

## Phase 4 — Productionization
**Status:** In progress

- [x] Dockerfile for self-hosted deployment
- [x] Recharts metrics visualization in dashboard
- [x] Self-hosted deployment guide in README
- [ ] Long-term archive format and portability checks

---

## Current milestone
Deliver Phase 4 with verifiable deployment artifacts and dashboard observability.
