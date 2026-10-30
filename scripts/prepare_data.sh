#!/bin/sh
# Run inside the project container. Downloads the pinned source dataset if absent.
set -eu
cd /workspace
revision=0056707cbf6a5ece8a70c550ed00a451a7449903
base="https://huggingface.co/datasets/aligeniewcp22/LCSTS/resolve/$revision"
mkdir -p data/raw/lcsts data/splits data/processed-2k
python - "$base" <<'PY'
from pathlib import Path
import sys, urllib.request
base = sys.argv[1]
for name in ('train.jsonl', 'valid.jsonl'):
    path = Path('data/raw/lcsts') / name
    if not path.exists():
        tmp = path.with_suffix('.part')
        print(f'Downloading {name} ...', flush=True)
        urllib.request.urlretrieve(f'{base}/{name}', tmp)
        tmp.replace(path)
PY
python scripts/split_lcsts_validation.py data/raw/lcsts/valid.jsonl data/splits --seed 42
python -m summarizer.cli prepare --train data/raw/lcsts/train.jsonl --validation data/splits/validation.jsonl --test data/splits/holdout.jsonl --train-size 10000 --seed 42 --exclude-eval-texts --output-dir data/processed
python - <<'PY'
from summarizer.data import iter_records, sample_stream, write_jsonl
write_jsonl('data/processed-2k/train.jsonl', sample_stream(iter_records('data/processed/train.jsonl'), 2000, 42))
PY
python - <<'PY'
from pathlib import Path
import hashlib
expected = {
'data/processed/train.jsonl':'38ed53e33466784336cd1546288180106031814e0ad923ffa60ea9368bca5205',
'data/processed-2k/train.jsonl':'f3fedc83472deef7de6574369039c7dedc16a9a010e678ec0362ea5d5c4f052d',
'data/processed/validation.jsonl':'bc9c4f659f0ad09f0b047e0ee4174ac54357855dfc5d904328f794e09fb981e7',
'data/processed/test.jsonl':'de3171c2bfc967be79a1718572f9aefe8640f42b8de2af78a2fff6be49768511',
}
for file, checksum in expected.items():
    actual = hashlib.sha256(Path(file).read_bytes()).hexdigest()
    if actual != checksum: raise SystemExit(f'Data mismatch: {file}: {actual}')
print('All data hashes verified.')
PY
