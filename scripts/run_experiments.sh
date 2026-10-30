#!/bin/sh
# Run inside the project image with /workspace mounted and PYTHONPATH=/workspace/src.
set -eu
cd /workspace
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-6}"
export MKL_NUM_THREADS="$OMP_NUM_THREADS"
mkdir -p outputs/experiments
python -m summarizer.cli train --config configs/bart-2k.json ${DEVICE_FLAG:-}
python -m summarizer.cli train --config configs/bart-10k.json ${DEVICE_FLAG:-}
python -m summarizer.cli evaluate --config configs/bart-10k.json --method lead30 --output-dir outputs/experiments/lead30 ${DEVICE_FLAG:-}
python scripts/evaluate_textrank.py --input data/processed/test.jsonl --output-dir outputs/experiments/textrank
for size in 2k 10k; do
  for strategy in greedy beam; do
    python -m summarizer.cli evaluate --config "configs/bart-$size.json" --method model --strategy "$strategy" --output-dir "outputs/experiments/bart-$size-$strategy" ${DEVICE_FLAG:-}
  done
done
