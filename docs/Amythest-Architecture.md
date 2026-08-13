# Amythest: Modular Scalable Model Architecture

## Overview

Amythest is a knowledge-OS for foundation models:
- Base model = runtime / brain / personality.
- Modules = knowledge, skills, tools, behaviors.
- Harness = package manager, module loader, scheduler, HITL policy engine.

## Module Package: `.apkg`

A `.apkg` is a zip archive with this layout:

```text
module.apkg
  manifest.json
  weights/
    adapter.safetensors
    adapter_config.json
  index/
    vectors.faiss
    chunks.jsonl
  templates/
    system_prompt.txt
    few_shot_examples.jsonl
  tools/
    tools.yaml
  tests/
    benchmark.jsonl
```

## Module Types

| Type        | Use                 | Contents                              | Injection Method       |
|-------------|---------------------|---------------------------------------|------------------------|
| knowledge   | Facts, docs, data   | Vector index + summary adapter        | RAG + port injection   |
| skill       | How to do something | LoRA adapter + prompt template        | Adapter merge + ports  |
| personality | Behavior, tone      | Prompt template + small adapter       | Prompt + port injection|
| tool        | External APIs/tools | Tool definitions + validation harness | Tool registration       |
| language    | Multi-lingual       | Vocabulary adapter + prompts          | Adapter + special tokens|
| composite   | Multiple types      | Combination of above                  | Multi-port injection   |

## Runtime

- ModuleManager installs, loads, unloads, composes, and resolves conflicts.
- ModuleDatabase stores metadata, activation history, and file paths.
- Textual TUI provides live module management, agent logs, metrics, and HITL queue.
- CLI supports `/create`, `/install`, `/activate`, `/deactivate`, `/uninstall`, `/list`, `/discover`, `/status`, `/doctor`.

## Automatic Module Selection

- Semantic search over module metadata.
- Dependency resolution.
- Conflict detection with priority/recency/scope rules.
- Runtime composition summary.

## Example Modules

Run:
```bash
python -m amythest.examples
amythest list
```

Generated modules:
- `python-3.12-knowledge`
- `agentic-runtime-skills`

## TUI

```bash
python -m amythest.tui
```

Shortcuts:
- `l` refresh modules
- `a` activate selected
- `d` deactivate selected
- `/` command input
- `q` quit
