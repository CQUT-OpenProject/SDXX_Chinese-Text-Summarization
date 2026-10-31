# 中文短文本摘要生成

《深度学习》课程设计：使用中文 BART 研究短文本摘要，并比较原文截取、TextRank、训练数据规模和解码方式。

[课程报告 PDF](<docs/基于 Transformer 的中文短文本摘要生成方法实现与研究.pdf>) · [实验数据与结果](docs/experiment-data/README.md) · [LaTeX 报告模板](<report(template)/template.tex>)

## 环境与数据准备

项目需要 Python 3.10 及以上。根据训练设备安装与其匹配的 PyTorch，再安装项目依赖；使用 NVIDIA GPU 时，请按 PyTorch 的安装说明选择匹配的 CUDA 版本。项目提供 Dockerfile，也可使用 OrbStack 或其他 Docker 环境。

```bash
python -m pip install -e .
```

数据准备脚本会从固定版本的 `aligeniewcp22/LCSTS` 下载数据，原始训练文件约 903 MB，再按种子 42 划分、抽样并校验文件哈希。脚本在 Docker 容器的 `/workspace` 下运行；数据写入被 Git 忽略的 `data/` 目录。

```bash
docker build -t chinese-summarizer .
docker run --rm -v "$PWD:/workspace" -e PYTHONPATH=/workspace/src chinese-summarizer sh scripts/prepare_data.sh
```

自划分测试集从整理版本的有标签验证数据中抽取。公开再分发数据时，请遵守数据来源的使用条件。

## 训练与评价

`configs/bart-2k.json` 和 `configs/bart-10k.json` 分别配置两组实验。安装环境并准备数据后，可在项目目录运行：

```bash
PYTHONPATH=src python -m summarizer.cli train --config configs/bart-2k.json
PYTHONPATH=src python -m summarizer.cli train --config configs/bart-10k.json
```

训练自动使用可用设备；若需强制使用 CPU，在命令末尾添加 `--cpu`。完整的两组训练、截取基线、TextRank 和四组模型解码对照也可在容器中运行：

```bash
docker run --rm -v "$PWD:/workspace" -e PYTHONPATH=/workspace/src chinese-summarizer sh scripts/run_experiments.sh
```

如容器支持 NVIDIA GPU，需使用适合该设备的 PyTorch/CUDA 环境并配置 GPU 直通。各方法的结果写入 `outputs/experiments/`，模型及训练记录写入 `outputs/bart-2k/` 和 `outputs/bart-10k/`。

测试代码可通过 `PYTHONPATH=src python -m unittest discover -s tests -v` 运行。

实验图表可通过 `python scripts/report_figures.py` 生成到 `outputs/report-figures/`；脚本需要 ReportLab 和 macOS 中文字体。
