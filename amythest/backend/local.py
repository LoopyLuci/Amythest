"""Local model backend with module injection support."""

from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from amythest.backend.interface import GenerationRequest, GenerationResponse, ModelBackend

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    import torch

    HAS_TRANSFORMERS = True
except Exception:
    HAS_TRANSFORMERS = False


@dataclass(frozen=True)
class ModelState:
    model_name: str
    weight_hash: str
    device: str = "cpu"


class LocalBackend(ModelBackend):
    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        self.cache_dir = cache_dir or Path.home() / ".amythest" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.model: Optional[object] = None
        self.tokenizer: Optional[object] = None
        self.model_name = ""
        self.device = "cpu"
        self.active_adapters: Dict[str, Path] = {}
        self.state: Optional[ModelState] = None

    def load_base_model(self, model_name: str, model_path: Optional[Path] = None) -> None:
        if not HAS_TRANSFORMERS:
            raise RuntimeError("transformers/torch not installed; cannot load local model.")
        source = model_path or model_name
        self.tokenizer = AutoTokenizer.from_pretrained(source, cache_dir=self.cache_dir)
        self.model = AutoModelForCausalLM.from_pretrained(
            source,
            cache_dir=self.cache_dir,
            device_map="auto" if _cuda_available() else "cpu",
            torch_dtype=torch.float32,
        )
        self.model_name = model_name
        self.device = "cuda" if _cuda_available() else "cpu"
        self.state = ModelState(
            model_name=model_name,
            weight_hash=_weight_hash(self.model),
            device=self.device,
        )

    def inject_modules(self, modules: List[Dict[str, object]]) -> None:
        if not HAS_TRANSFORMERS or self.model is None:
            raise RuntimeError("Model not loaded.")
        for m in modules:
            adapter_path = m.get("adapter_path")
            name = str(m.get("name", ""))
            if not adapter_path or not name:
                continue
            path = Path(adapter_path)
            if not path.exists():
                continue
            if name in self.active_adapters:
                continue
            self.model = PeftModel.from_pretrained(self.model, path)
            self.active_adapters[name] = path

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded.")
        inputs = self.tokenizer(request.prompt, return_tensors="pt").to(self.device)
        with torch.no_grad():
            out = self.model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        text = self.tokenizer.decode(out[0], skip_special_tokens=True)
        prompt_len = inputs["input_ids"].shape[-1]
        return GenerationResponse(
            text=text,
            prompt_tokens=prompt_len,
            completion_tokens=max(0, len(out[0]) - prompt_len),
            model=self.model_name,
            active_modules=list(self.active_adapters.keys()),
        )

    def unload(self) -> None:
        self.model = None
        self.tokenizer = None
        self.active_adapters.clear()
        self.state = None


def _cuda_available() -> bool:
    if not HAS_TRANSFORMERS:
        return False
    try:
        return torch.cuda.is_available()
    except Exception:
        return False


def _weight_hash(model: object) -> str:
    h = hashlib.sha256()
    for p in model.parameters():
        h.update(p.detach().cpu().numpy().tobytes()[:1024])
    return h.hexdigest()[:16]
