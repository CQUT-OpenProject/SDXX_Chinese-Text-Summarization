# 中文短文本摘要生成

基于 Transformer/BART 的中文生成式摘要课程项目。包含数据转换、微调、生成、前 30 字基线和字符级 ROUGE 评价。仓库内样例为虚构数据，仅用于检查流程；尚无正式实验结果。

## 环境

需要 Python 3.10 或以上。以下命令均在项目根目录运行：

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

默认模型为 [OpenMOSS-Team/bart-base-chinese](https://huggingface.co/OpenMOSS-Team/bart-base-chinese)，首次使用需联网下载，或在配置中指定已下载的本地模型目录。PyTorch 会自动选择 CUDA、可用的 macOS MPS 或 CPU；`train`、`predict`、`evaluate` 可加 `--cpu` 强制使用 CPU。正式微调建议使用 GPU；CPU 更适合小样本检查。

## 数据准备

LCSTS 有不同的发布及整理版本，字段名和划分可能不同。请先取得数据并检查其来源、使用条件、实际字段及官方划分；原先推荐的数据集链接当前可能无法访问。把各划分整理为 UTF-8 JSONL（一行一个 JSON 对象）或带表头的 CSV，再分别传入。不要把测试集混入训练或验证数据。示例字段如下：

```json
{"text":"一段原文", "summary":"对应的参考摘要"}
```

```bash
summarizer prepare --train data/raw/train.jsonl --validation data/raw/validation.jsonl --test data/raw/test.jsonl \
  --text-field text --summary-field summary --train-size 10000 --validation-size 1000 --seed 42
```

字段名根据实际数据修改；三个文件须分别对应已有划分。训练和验证数据按种子独立抽样，测试文件完整保留；不指定样本数量时保留完整划分。输出为 `data/processed/{train,validation,test}.jsonl`。若数据量不足，请减小抽样数量。该工具不会自动判断不同文件之间的重复样本或数据泄漏。

使用虚构样例检查数据流程：

```bash
summarizer prepare --train examples/train.jsonl --validation examples/validation.jsonl --test examples/test.jsonl --output-dir data/processed
summarizer evaluate --method lead30 --output-dir outputs/lead30
```

## 训练与预测

编辑 `configs/default.json` 设置模型、数据路径、随机种子、长度和训练参数。路径均相对于运行命令时的工作目录。默认从验证损失最低的 epoch 保存模型，并在输出目录保留检查点和实际使用的配置。

```bash
summarizer train --config configs/default.json
summarizer predict --text '学校举办科技节，学生展示机器人与人工智能项目。' --strategy beam
summarizer evaluate --method model --strategy greedy --output-dir outputs/greedy
summarizer evaluate --method model --strategy beam --output-dir outputs/beam
```

预测和评估默认加载配置中 `output_dir/best_model`；可使用 `--model` 指定本地模型目录或 Hugging Face 模型 ID。greedy 使用一个 beam；beam 宽度由配置的 `generation.num_beams` 指定。模型生成的 BERT 分词空格会被移除，适合本项目中文摘要，但含英文空格的文本可能受到影响。

评估生成 `predictions.jsonl` 和 `metrics.json`。ROUGE-1、ROUGE-2 和 ROUGE-L 是去除空白后的字符级 F1，按样本取算术平均，范围为 0–1；不同分词或聚合方法的结果不能直接比较。配置中的输出长度在生成时表示最多新生成 token 数，训练目标编码时表示最大 token 数。

## 实验建议

固定种子分别准备 2,000 和 10,000 条训练样本，并使用独立配置和输出目录；保持验证和测试集一致。比较前 30 字基线及不同模型的 ROUGE，再比较同一模型的 greedy 和 beam 输出，并抽取样本进行事实性、遗漏和流畅度分析。示例数据只用于验证程序，不能作为实验结论。

## 测试

```bash
python -m unittest discover -s tests -v
```
