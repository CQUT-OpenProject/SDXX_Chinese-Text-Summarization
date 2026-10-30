"""Create a reproducible local holdout from the labeled LCSTS validation split."""
import argparse
import json
import random
from pathlib import Path

from summarizer.data import read_records, write_jsonl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="LCSTS valid.jsonl")
    parser.add_argument("output_dir")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    rows = read_records(args.input)
    random.Random(args.seed).shuffle(rows)
    # Group by input text so repeated inputs cannot cross the local split.
    unique = {}
    for row in rows:
        unique.setdefault(row["text"], row)
    rows = list(unique.values())
    if len(rows) < 1725:
        raise ValueError("至少需要 1725 条不同原文")
    out = Path(args.output_dir)
    write_jsonl(out / "validation.jsonl", rows[:1000])
    write_jsonl(out / "holdout.jsonl", rows[1000:1725])
    (out / "split_info.json").write_text(json.dumps({
        "source": args.input, "seed": args.seed, "validation": 1000,
        "holdout": 725, "unique_source_texts": len(rows),
        "note": "Local split of labeled validation data; holdout is not the official test set."
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"验证集 1000 条，保留集 725 条；不同原文共 {len(rows)} 条")


if __name__ == "__main__":
    main()
