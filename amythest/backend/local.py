from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from amythest.backend.interface import GenerationRequest, GenerationResponse, ModelBackend

try:
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    HAS_TRANSFORMERS = True
except ModuleNotFoundError:
    HAS_TRANSFORMERS = False


@dataclass(frozen=True)
class ModelState:
    model_name: str
    weight_hash: str
    device: str = "cpu"


class LocalBackend(ModelBackend):
    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or Path.home() / ".amythest" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.model: object | None = None
        self.tokenizer: object | None = None
        self.model_name = ""
        self.device = "cpu"
        self.active_adapters: dict[str, Path] = {}
        self.state: ModelState | None = None

    def load_base_model(self, model_name: str, model_path: Path | None = None, device_map: str = "auto", load_in_4bit: bool = False) -> None:
        if not HAS_TRANSFORMERS:
            raise RuntimeError("transformers/torch not installed; cannot load local model.")
        source = model_path or model_name
        self.tokenizer = AutoTokenizer.from_pretrained(source, cache_dir=self.cache_dir)
        model_kwargs: dict[str, object] = {
            "cache_dir": self.cache_dir,
            "device_map": device_map if device_map in {"auto", "cpu", "cuda", "mps"} else "auto",
            "torch_dtype": torch.float32,
        }
        if load_in_4bit:
            try:
                from transformers import BitsAndBytesConfig  # type: ignore
                model_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True)
            except ModuleNotFoundError:
                load_in_4bit = False
        self.model = AutoModelForCausalLM.from_pretrained(source, **model_kwargs)
        self.model_name = model_name
        resolved_device = "cuda" if _cuda_available() else "cpu"
        self.device = resolved_device
        self.state = ModelState(
            model_name=model_name,
            weight_hash=_weight_hash(self.model),
            device=self.device,
        )

    def ensure_model(self, model_name: str | None = None, device_map: str = "auto", load_in_4bit: bool = False) -> None:
        if self.model is None or self.tokenizer is None:
            target = model_name or "distilgpt2"
            self.load_base_model(target, device_map=device_map, load_in_4bit=load_in_4bit)

    def inject_modules(self, modules: list[dict[str, object]]) -> None:
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
            resolved = path
            if path.suffix.lower() == ".apkg":
                from amythest.encoding.trainer import extract_adapter_dir
                resolved = extract_adapter_dir(path)
            self.model = PeftModel.from_pretrained(self.model, str(resolved))
            self.active_adapters[name] = resolved

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
    except RuntimeError:
        return False


def _weight_hash(model: object) -> str:
    h = hashlib.sha256()
    for p in model.parameters():
        h.update(p.detach().cpu().numpy().tobytes()[:1024])
    return h.hexdigest()[:16]
