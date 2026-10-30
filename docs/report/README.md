# 深度学习课程论文

`template.tex` 是论文源文件，`template.pdf` 是当前待填写版本。封面个人信息、实验环境、结果、损失曲线、案例、讨论和结论均需在训练与评价完成后填写。当前模板中的数据规模和超参数是拟采用的实验方案，请根据实际训练配置核对。

在本目录运行 `tectonic template.tex` 编译。数据获取、训练及评价流程见项目根目录的 README。`scripts/report_figures.py` 可读取新训练的 `outputs/bart-2k/trainer_state.json` 和 `outputs/bart-10k/trainer_state.json` 生成损失图；生成后需在论文中替换曲线占位框。自划分测试集来源于有标签验证数据，并非官方测试集。
