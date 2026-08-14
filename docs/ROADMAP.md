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
**Status:** In progress

- [x] LoRA training stub with `package_module_outputs`
- [ ] Real adapter export from training script
- [ ] Atomic checkpoint + rollback endpoints
- [ ] Hardware optimization: device map, 4-bit, KV cache tuning
- [ ] DVC-based model/artifact versioning

## Phase 4 — Productionization
**Status:** Pending

- [ ] Docker multi-stage build with dashboard
- [ ] Recharts metrics visualization in dashboard
- [ ] Configurable HITL policy files
- [ ] Self-hosted deployment guide
- [ ] Long-term archive format and portability checks

---

## Current milestone
Deliver Phase 3 with at least one working local completion, checkpoint/rollback API, and hardware-selection knobs.
