"""Remote backend that talks to an OpenAI-compatible inference server."""

from __future__ import annotations

import httpx

from amythest.backend.interface import GenerationRequest, GenerationResponse, ModelBackend


class RemoteBackend(ModelBackend):
    def __init__(self, base_url: str, api_key: str = "sk-placeholder") -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_name = ""
        self.active_modules: list[str] = []

    def load_base_model(self, model_name: str, model_path: None = None) -> None:
        self.model_name = model_name

    def inject_modules(self, modules: list[dict[str, object]]) -> None:
        names = [str(m.get("name", "")) for m in modules if m.get("name")]
        self.active_modules = names

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        payload = {
            "model": self.model_name,
            "prompt": request.prompt,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "stop": request.stop,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        with httpx.Client(timeout=httpx.Timeout(60)) as client:
            resp = client.post(f"{self.base_url}/v1/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        text = data["choices"][0]["text"]
        usage = data.get("usage", {})
        return GenerationResponse(
            text=text,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            model=self.model_name,
            active_modules=self.active_modules,
        )

    def unload(self) -> None:
        self.model_name = ""
        self.active_modules = []
