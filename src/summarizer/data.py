import csv
import json
import random
from pathlib import Path


def iter_records(path, text_field="text", summary_field="summary"):
    path = Path(path)
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as f:
            yield from _validate_rows(csv.DictReader(f), path, text_field, summary_field)
    elif path.suffix.lower() == ".jsonl":
        with path.open(encoding="utf-8-sig") as f:
            def rows():
                for number, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValueError(f"{path}:{number}: JSON 格式错误: {exc.msg}") from exc
            yield from _validate_rows(rows(), path, text_field, summary_field)
    else:
        raise ValueError(f"不支持的文件格式：{path}；请使用 CSV 或 JSONL")


def _validate_rows(rows, path, text_field, summary_field):
    count = 0
    for number, row in enumerate(rows, 1):
        if not isinstance(row, dict) or not all(isinstance(row.get(k), str) and row[k].strip() for k in (text_field, summary_field)):
            raise ValueError(f"{path}: 第 {number} 条记录缺少非空字符串字段 {text_field!r} 或 {summary_field!r}")
        count += 1
        yield {"text": row[text_field].strip(), "summary": row[summary_field].strip()}
    if not count:
        raise ValueError(f"{path}: 数据为空")


def read_records(path, text_field="text", summary_field="summary"):
    return list(iter_records(path, text_field, summary_field))


def sample_stream(records, count, seed):
    """Uniform reservoir sample without holding the whole input in memory."""
    if count <= 0:
        raise ValueError("抽样数量必须大于零")
    rng = random.Random(seed)
    sample = []
    total = 0
    for total, record in enumerate(records, 1):
        if total <= count:
            sample.append(record)
        else:
            index = rng.randrange(total)
            if index < count:
                sample[index] = record
    if total < count:
        raise ValueError(f"抽样数量必须在 1 到 {total} 之间，实际为 {count}")
    return sample


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
