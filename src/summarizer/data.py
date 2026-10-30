import csv
import json
import random
from pathlib import Path


def read_records(path, text_field="text", summary_field="summary"):
    path = Path(path)
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    elif path.suffix.lower() == ".jsonl":
        rows = []
        with path.open(encoding="utf-8-sig") as f:
            for number, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{number}: JSON 格式错误: {exc.msg}") from exc
    else:
        raise ValueError(f"不支持的文件格式：{path}；请使用 CSV 或 JSONL")
    records = []
    for number, row in enumerate(rows, 1):
        if not isinstance(row, dict) or not all(isinstance(row.get(k), str) and row[k].strip() for k in (text_field, summary_field)):
            raise ValueError(f"{path}: 第 {number} 条记录缺少非空字符串字段 {text_field!r} 或 {summary_field!r}")
        records.append({"text": row[text_field].strip(), "summary": row[summary_field].strip()})
    if not records:
        raise ValueError(f"{path}: 数据为空")
    return records


def sample_records(records, count, seed):
    if count is None:
        return records
    if count <= 0 or count > len(records):
        raise ValueError(f"抽样数量必须在 1 到 {len(records)} 之间，实际为 {count}")
    return random.Random(seed).sample(records, count)


def write_jsonl(path, records):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
