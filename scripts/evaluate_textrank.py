"""Evaluate a deterministic sentence-level TextRank baseline on JSONL records."""
import argparse
import json
import math
import re
import time
from collections import Counter
from pathlib import Path

from summarizer.data import read_records, write_jsonl
from summarizer.metrics import aggregate


def tokens(sentence):
    # Chinese characters are individual tokens; contiguous Latin letters/digits are words.
    return re.findall(r'[\u4e00-\u9fff]|[A-Za-z0-9]+', sentence.lower())


def summarize(text, limit=30):
    sentences = [s.strip() for s in re.split(r'(?<=[。！？!?；;])|[\r\n]+', text) if s.strip()]
    if not sentences:
        return ''
    words = [Counter(tokens(s)) for s in sentences]
    n = len(sentences)
    edges = [[0.0] * n for _ in sentences]
    for i in range(n):
        for j in range(i):
            a, b = sum(words[i].values()), sum(words[j].values())
            denom = math.log1p(a) + math.log1p(b)
            weight = sum((words[i] & words[j]).values()) / denom if denom else 0.0
            edges[i][j] = edges[j][i] = weight
    sums = [sum(row) for row in edges]
    scores = [1.0 / n] * n
    for _ in range(100):
        dangling = sum(scores[j] for j in range(n) if sums[j] == 0) / n
        updated = [(1.0 - 0.85) / n + 0.85 * (dangling + sum(
            scores[j] * edges[j][i] / sums[j] for j in range(n) if sums[j]
        )) for i in range(n)]
        if max(abs(a-b) for a,b in zip(updated,scores)) < 1e-8:
            scores = updated
            break
        scores = updated
    # Stable tie-breaking favors the first sentence. Truncate to match Lead-30.
    return sentences[max(range(n), key=lambda i: (scores[i], -i))][:limit]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', default='data/processed/test.jsonl')
    parser.add_argument('--output-dir', default='outputs/experiments/textrank')
    args = parser.parse_args()
    rows = read_records(args.input)
    start = time.perf_counter()
    results = [{**row, 'prediction': summarize(row['text'])} for row in rows]
    elapsed = time.perf_counter() - start
    scores = aggregate([r['prediction'] for r in results], [r['summary'] for r in results])
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    write_jsonl(output / 'predictions.jsonl', results)
    metrics = {'count': len(results), 'method': 'textrank_sentence', 'scores': scores,
               'mean_prediction_chars': sum(len(r['prediction']) for r in results) / len(results),
               'generation_seconds': elapsed,
               'settings': {'sentence_delimiters': '。！？!?；; and newline', 'tokenization': 'Chinese characters, lowercase Latin alphanumeric runs',
                            'edge_weight': 'multiset overlap / (log(1 + token_count_i) + log(1 + token_count_j))',
                            'damping': 0.85, 'max_iterations': 100, 'tolerance': 1e-8,
                            'selection': 'highest scoring sentence; first on ties; first 30 characters'}}
    (output / 'metrics.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(metrics, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
