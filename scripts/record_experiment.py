"""Record input hashes and library versions for the current experiment."""
import hashlib
import json
import platform
from pathlib import Path

import accelerate
import datasets
import torch
import transformers


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


files = ["data/processed-2k/train.jsonl", "data/processed/train.jsonl",
         "data/processed/validation.jsonl", "data/processed/test.jsonl",
         "configs/bart-2k.json", "configs/bart-10k.json",
         "src/summarizer/cli.py", "src/summarizer/data.py", "src/summarizer/metrics.py",
         "scripts/split_lcsts_validation.py"]
manifest = {
    "dataset": "aligeniewcp22/LCSTS",
    "dataset_revision": "0056707cbf6a5ece8a70c550ed00a451a7449903",
    "holdout": "725 examples sampled from labeled validation split; not official test set",
    "sha256": {path: sha256(path) for path in files},
    "python": platform.python_version(), "torch": torch.__version__,
    "cuda_runtime": torch.version.cuda, "transformers": transformers.__version__,
    "datasets": datasets.__version__, "accelerate": accelerate.__version__,
    "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
}
path = Path("outputs/experiments/manifest.json")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"实验记录已保存至 {path}")
