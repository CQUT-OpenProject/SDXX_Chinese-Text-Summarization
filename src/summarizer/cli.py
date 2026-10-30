import argparse
import json
import shutil
import sys
import time
from pathlib import Path

from .data import iter_records, read_records, sample_stream, write_jsonl
from .metrics import aggregate


def load_config(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def prepare(args):
    paths = [Path(args.train).resolve(), Path(args.validation).resolve(), Path(args.test).resolve()]
    if len(set(paths)) != 3:
        raise ValueError("训练、验证和测试输入必须是三个不同文件")
    out = Path(args.output_dir).resolve()
    if any(path == (out / f"{name}.jsonl") for path in paths for name in ("train", "validation", "test")):
        raise ValueError("输出文件不能覆盖任何输入文件")
    excluded = set()
    if args.exclude_eval_texts:
        for path in paths[1:]:
            excluded.update(row["text"] for row in iter_records(path, args.text_field, args.summary_field))
    for name, path, count in zip(("train", "validation", "test"), paths, (args.train_size, args.validation_size, None)):
        records = iter_records(path, args.text_field, args.summary_field)
        if name == "train" and excluded:
            records = (row for row in records if row["text"] not in excluded)
        rows = sample_stream(records, count, args.seed) if count is not None else list(records)
        write_jsonl(out / f"{name}.jsonl", rows)
        print(f"{name}: {len(rows)} 条 -> {out / (name + '.jsonl')}")


def train(args):
    from datasets import Dataset
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, DataCollatorForSeq2Seq, Seq2SeqTrainer, Seq2SeqTrainingArguments, set_seed

    cfg = load_config(args.config)
    set_seed(cfg["seed"])
    revision = cfg.get("model_revision", "main")
    tokenizer = AutoTokenizer.from_pretrained(cfg["model_name"], revision=revision)
    model = AutoModelForSeq2SeqLM.from_pretrained(cfg["model_name"], revision=revision)
    def tokenize(batch):
        inputs = tokenizer(batch["text"], max_length=cfg["max_source_length"], truncation=True)
        targets = tokenizer(text_target=batch["summary"], max_length=cfg["max_target_length"], truncation=True)
        inputs["labels"] = targets["input_ids"]
        return inputs
    def dataset(path):
        return Dataset.from_list(read_records(path)).map(tokenize, batched=True, remove_columns=["text", "summary"])
    training = dataset(cfg["train_file"])
    validation = dataset(cfg["validation_file"])
    output = Path(cfg["output_dir"])
    training_args = Seq2SeqTrainingArguments(
        output_dir=str(output), eval_strategy="epoch", save_strategy="epoch",
        load_best_model_at_end=True, metric_for_best_model="eval_loss", greater_is_better=False,
        per_device_train_batch_size=cfg["batch_size"], per_device_eval_batch_size=cfg["batch_size"],
        learning_rate=cfg["learning_rate"], num_train_epochs=cfg["epochs"], seed=cfg["seed"],
        save_total_limit=2, report_to="none", use_cpu=args.cpu, logging_steps=50,
    )
    trainer = Seq2SeqTrainer(model=model, args=training_args, train_dataset=training,
                             eval_dataset=validation, data_collator=DataCollatorForSeq2Seq(tokenizer, model=model),
                             processing_class=tokenizer)
    trainer.train()
    final = output / "best_model"
    trainer.save_model(str(final))
    tokenizer.save_pretrained(str(final))
    trainer.state.save_to_json(str(output / "trainer_state.json"))
    shutil.copyfile(args.config, output / "experiment_config.json")
    print(f"最佳模型已保存至 {final}")


def generator(cfg, model_path, strategy, cpu):
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    device = "cpu" if cpu else ("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_path).to(device).eval()
    settings = cfg["generation"]
    strategy = strategy or settings["strategy"]
    if strategy not in ("greedy", "beam"):
        raise ValueError(f"未知解码策略: {strategy}")
    beams = 1 if strategy == "greedy" else settings["num_beams"]
    if beams < 1:
        raise ValueError("num_beams 必须大于零")
    def generate(text):
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=cfg["max_source_length"], return_token_type_ids=False).to(device)
        with torch.inference_mode():
            ids = model.generate(**inputs, max_new_tokens=cfg["max_target_length"], num_beams=beams, do_sample=False)
        # BERT tokenizer inserts spaces between Chinese characters during decoding.
        return "".join(tokenizer.decode(ids[0], skip_special_tokens=True).split())
    return generate


def model_path(args, cfg):
    return args.model or str(Path(cfg["output_dir"]) / "best_model")


def predict(args):
    cfg = load_config(args.config)
    generate = generator(cfg, model_path(args, cfg), args.strategy, args.cpu)
    print(generate(args.text))


def evaluate(args):
    cfg = load_config(args.config)
    rows = read_records(args.input or cfg["test_file"])
    if args.method == "lead30":
        generate = lambda text: text[:30]
    else:
        generate = generator(cfg, model_path(args, cfg), args.strategy, args.cpu)
    start = time.perf_counter()
    results = [{**row, "prediction": generate(row["text"])} for row in rows]
    elapsed = time.perf_counter() - start
    metrics = aggregate([r["prediction"] for r in results], [r["summary"] for r in results])
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    write_jsonl(output / "predictions.jsonl", results)
    (output / "metrics.json").write_text(json.dumps({"count": len(rows), "method": args.method, "strategy": (args.strategy or cfg["generation"]["strategy"]) if args.method == "model" else None, "scores": metrics, "generation_seconds": elapsed, "mean_prediction_chars": sum(len(r["prediction"]) for r in results) / len(results)}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="中文短文本摘要实验")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare", help="转换已有的训练、验证和测试划分")
    for split in ("train", "validation", "test"):
        p.add_argument(f"--{split}", required=True)
    p.add_argument("--text-field", default="text")
    p.add_argument("--summary-field", default="summary")
    p.add_argument("--train-size", type=int)
    p.add_argument("--validation-size", type=int)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--exclude-eval-texts", action="store_true", help="从训练输入排除与验证或测试原文完全相同的记录")
    p.add_argument("--output-dir", default="data/processed")
    p.set_defaults(func=prepare)
    p = sub.add_parser("train", help="微调 BART")
    p.add_argument("--config", default="configs/default.json")
    p.add_argument("--cpu", action="store_true")
    p.set_defaults(func=train)
    for name, fn in (("predict", predict), ("evaluate", evaluate)):
        p = sub.add_parser(name)
        p.add_argument("--config", default="configs/default.json")
        p.add_argument("--model", help="模型目录或 Hugging Face 模型 ID")
        p.add_argument("--strategy", choices=("greedy", "beam"))
        p.add_argument("--cpu", action="store_true")
        if name == "predict":
            p.add_argument("--text", required=True)
        else:
            p.add_argument("--method", choices=("model", "lead30"), default="model")
            p.add_argument("--input", help="覆盖配置中的测试文件")
            p.add_argument("--output-dir", default="outputs/evaluation")
        p.set_defaults(func=fn)
    args = parser.parse_args()
    try:
        args.func(args)
    except (ValueError, OSError, ImportError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
