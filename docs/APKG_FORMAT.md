# Amythest Module Package Format

## .apkg format specification

Amythest modules are distributed as `.apkg` files. An `.apkg` is a ZIP archive with a fixed directory layout.

### Required layout

```text
module.apkg
  manifest.json
  weights/
    adapter.safetensors   # optional
    adapter_config.json   # optional
  index/
    vectors.faiss         # optional
    chunks.jsonl          # optional
  templates/
    system_prompt.txt     # optional
    few_shot_examples.jsonl # optional
  tools/
    tools.yaml            # optional
  tests/
    benchmark.jsonl       # optional
```

### manifest.json schema

```json
{
  "name": "python-3.12-knowledge",
  "version": "1.2.0",
  "author": "LoopyLuci",
  "description": "Complete Python 3.12 standard library knowledge",
  "type": "knowledge",
  "base_model": {
    "name": "amythest-base",
    "version": "1.0.0",
    "architecture": "dense-70b"
  },
  "dependencies": [
    {"name": "programming-fundamentals", "version": ">=2.0.0"}
  ],
  "injection_ports": [0, 4, 8, 12],
  "size_mb": 45,
  "created_at": "2026-08-04T00:00:00Z",
  "tags": ["programming", "python", "stdlib"],
  "benchmark_score": 0.94
}
```
