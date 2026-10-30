import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from summarizer.cli import prepare, evaluate
from summarizer.data import read_records, sample_records, sample_stream
from summarizer.metrics import aggregate, rouge_pair


class CoreTests(unittest.TestCase):
    def test_metrics(self):
        self.assertEqual(rouge_pair("甲乙", "甲乙"), {"rouge1": 1.0, "rouge2": 1.0, "rougeL": 1.0})
        self.assertEqual(rouge_pair("甲", "乙")["rouge1"], 0)
        self.assertAlmostEqual(rouge_pair("甲乙", "甲丙")["rouge1"], 0.5)
        with self.assertRaises(ValueError):
            aggregate([], [])

    def test_invalid_and_sample(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.jsonl"
            path.write_text('{"text":"内容"}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "summary"):
                read_records(path)
        items = list(range(30))
        self.assertEqual(sample_records(items, 10, 42), sample_records(items, 10, 42))
        with self.assertRaises(ValueError):
            sample_records(items, 31, 42)
        self.assertEqual(sample_stream(iter(items), 10, 42), sample_stream(iter(items), 10, 42))
        self.assertEqual(len(set(sample_stream(iter(items), 10, 42))), 10)
        with self.assertRaises(ValueError):
            sample_stream(iter(items), 31, 42)

    def test_prepare_and_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = []
            for name in ("train", "validation", "test"):
                path = root / (name + ".jsonl")
                path.write_text(''.join(json.dumps({"body": name + str(i), "title": name}, ensure_ascii=False) + '\n' for i in range(3)), encoding="utf-8")
                paths.append(str(path))
            args = SimpleNamespace(train=paths[0], validation=paths[1], test=paths[2], text_field="body", summary_field="title", train_size=2, validation_size=1, seed=42, output_dir=str(root / "processed"), exclude_eval_texts=True)
            prepare(args)
            self.assertEqual(len(read_records(root / "processed/train.jsonl")), 2)
            self.assertEqual(len(read_records(root / "processed/validation.jsonl")), 1)
            self.assertEqual(len(read_records(root / "processed/test.jsonl")), 3)
            self.assertTrue(all(r["text"].startswith("test") for r in read_records(root / "processed/test.jsonl")))
            cfg = root / "config.json"
            cfg.write_text(json.dumps({"test_file": str(root / "processed/test.jsonl")}), encoding="utf-8")
            evaluate(SimpleNamespace(config=str(cfg), input=None, method="lead30", output_dir=str(root / "result")))
            results = [json.loads(line) for line in (root / "result/predictions.jsonl").read_text().splitlines()]
            self.assertEqual(results[0]["prediction"], "test0")

    def test_excludes_evaluation_text_from_training(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, texts in (("train", ["重复", "保留"]), ("validation", ["重复"]), ("test", ["测试"])):
                (root / (name + ".jsonl")).write_text(
                    "".join(json.dumps({"text": text, "summary": "摘要"}, ensure_ascii=False) + "\n" for text in texts), encoding="utf-8")
            prepare(SimpleNamespace(train=str(root / "train.jsonl"), validation=str(root / "validation.jsonl"),
                test=str(root / "test.jsonl"), text_field="text", summary_field="summary", train_size=1,
                validation_size=None, seed=42, output_dir=str(root / "out"), exclude_eval_texts=True))
            self.assertEqual(read_records(root / "out/train.jsonl")[0]["text"], "保留")


if __name__ == "__main__":
    unittest.main()
