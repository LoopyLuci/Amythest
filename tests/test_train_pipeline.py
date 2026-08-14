from amythest.encoding.trainer import build_training_records
from amythest.encoding.pipeline import encode_training_records

def test_train_pipeline_runs() -> None:
    records = build_training_records(["hello world", "foo bar"])
    encoded = encode_training_records(records)
    assert len(encoded) == len(records)
