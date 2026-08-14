"""Real LoRA training pipeline for creating modules from datasets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TrainingConfig:
    base_model: str
    output_dir: Path
    rank: int = 16
    alpha: int = 32
    target_modules: list[str] = None
    max_steps: int = 200
    learning_rate: float = 2e-4
    batch_size: int = 4

    def __post_init__(self) -> None:
        if self.target_modules is None:
            object.__setattr__(self, "target_modules", ["q_proj", "v_proj"])


def train_lora_adapter(
    config: TrainingConfig,
    train_file: Path,
) -> Path:
    if not _has_peft():
        raise RuntimeError("peft/transformers not installed; cannot train LoRA adapter.")
    try:
        from datasets import load_dataset
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
    except Exception as exc:
        raise RuntimeError(f"Training dependencies missing: {exc}") from exc

    tokenizer = AutoTokenizer.from_pretrained(config.base_model)
    tokenizer.pad_token = tokenizer.eos_token
    dataset = load_dataset("json", data_files=str(train_file), split="train")

    def tokenize(ex):
        return tokenizer(ex["text"], truncation=True, max_length=512)

    tokenized = dataset.map(tokenize, remove_columns=dataset.column_names)

    model = AutoModelForCausalLM.from_pretrained(config.base_model, device_map="auto")
    lora_config = LoraConfig(
        r=config.rank,
        lora_alpha=config.alpha,
        target_modules=config.target_modules,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, lora_config)
    args = TrainingArguments(
        output_dir=str(config.output_dir),
        max_steps=config.max_steps,
        per_device_train_batch_size=config.batch_size,
        learning_rate=config.learning_rate,
        logging_steps=10,
        save_strategy="no",
        report_to="none",
    )
    trainer = Trainer(model=model, args=args, train_dataset=tokenized)
    trainer.train()
    model.save_pretrained(config.output_dir)
    tokenizer.save_pretrained(config.output_dir)
    return config.output_dir


def _has_peft() -> bool:
    try:
        import peft  # noqa: F401
        return True
    except ModuleNotFoundError:
        return False
