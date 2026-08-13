# Amythest

Amythest is a knowledge-OS for foundation models: the base model is the runtime,
modules are the software, and the harness is the package manager + OS kernel.

## Install

```bash
pip install -e .
```

## Verify

```bash
python -m pytest tests/ -q
python -m amythest list
python -m amythest status
```

## Generate example modules

```bash
python -m amythest.examples
```

End-to-end demo:
```bash
python amythest/examples/e2e.py
```

Smoke test:
```bash
python amythest/examples/smoke.py
```

Verify server:
```bash
python amythest/examples/verify_server.py
```

## CLI

Run the CLI with:
```bash
python -m amythest --help
```

Create a module package from a text file or directory:
```bash
python -m amythest create ./notes.txt --name notes --version 1.0.0 --author test --description "Notes module" --type knowledge
```

Install and manage modules:
```bash
python -m amythest install ./notes-1.0.0.apkg
python -m amythest activate notes 1.0.0
python -m amythest list
python -m amythest status
```

## TUI

```bash
python -m amythest.tui
```

Shortcuts:
- `l` refresh modules
- `a` activate selected
- `d` deactivate selected
- `p` pause agent
- `r` resume agent
- `k` kill agent
- `/` command input
- `q` quit

## Runtime API

```bash
uvicorn amythest.backend.server:app --host 127.0.0.1 --port 8125
```

Endpoints:
- `GET /status`
- `GET /modules`
- `POST /modules/{name}/{version}/activate`
- `POST /modules/{name}/{version}/deactivate`
- `POST /recommend`
- `POST /hitl/evaluate`
- `GET /hitl/queue`
- `POST /hitl/{request_id}/approve`
- `POST /hitl/{request_id}/reject`

## Web dashboard

Build frontend:
```bash
cd web && npm install && npm run build
```

Serve built dashboard + API:
```bash
uvicorn amythest.backend.serve_dashboard:serve_dashboard --host 127.0.0.1 --port 8125
```

Or serve only API:
```bash
uvicorn amythest.backend.server:app --host 127.0.0.1 --port 8125
```

Pages:
- `/` live status, shortcuts, module composition, recommendations
- `/modules` module table with activate/deactivate
- `/hitl` approval queue with approve/reject

## Module package format

A `.apkg` is a zip archive:
```text
module.apkg
  manifest.json
  weights/adapter.safetensors
  weights/adapter_config.json
  index/chunks.jsonl
  templates/system_prompt.txt
  templates/few_shot_examples.jsonl
  tools/tools.yaml
  tests/benchmark.jsonl
```

## Documentation

- `docs/Amythest-Architecture.md`
- `docs/APKG_FORMAT.md`
