"""Backend abstraction for model serving and module injection."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GenerationRequest:
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.2
    top_p: float = 0.95
    stop: list[str] | None = None
    extra: dict[str, object] | None = None


@dataclass(frozen=True)
class GenerationResponse:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model: str = ""
    active_modules: list[str] | None = None


class ModelBackend(ABC):
    @abstractmethod
    def load_base_model(self, model_name: str, model_path: Path | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def inject_modules(self, modules: list[dict[str, object]]) -> None:
        raise NotImplementedError

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        raise NotImplementedError

    @abstractmethod
    def unload(self) -> None:
        raise NotImplementedError
