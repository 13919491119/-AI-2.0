# SSQ 自动化复盘与优化变更记录

生成时间（UTC）：2025-11-04T02:33:12Z

变更概述：

- 为 `ssq_batch_replay_learn.py` 添加了机器可读 JSON 输出（`reports/ssq_batch_replay_summary.json`）并生成窗口化摘要（_100/_500/_1000）。同时增强了 CSV 字段名的兼容性（支持多种中文/英文列名），并使用时区感知时间戳。
- 为 `optimize_models.py` 添加了对 JSON 汇总的优先读取逻辑，并在每次优化后把权重快照写入 `reports/weights_history/weights_snapshot_<timestamp>.json`（包含 metrics，便于审计和回滚），同时使用时区感知时间戳。
- 在 `autonomous_run.py` 中把批量复盘与优化脚本在每轮 SSQ 闭环完成后触发（若脚本存在），实现自动闭环执行。

产出文件（示例）：

- `reports/ssq_batch_replay_report.txt`（文本报告）
- `reports/ssq_batch_replay_summary.json`（机器可读汇总）
- `reports/ssq_batch_replay_summary_window_100.json` / `_500.json` / `_1000.json`（窗口化摘要）
- `reports/weights_history/weights_snapshot_20251104_023312.json`（权重快照历史）
- `ssq_strategy_weights.json`（当前生效权重）

短期建议（可立即实施）：

1. 固定 JSON schema（加入 `schema_v`, `generated_at`, `models->{total,red_hit,blue_hit,full_hit,sample_details}`），并把 schema 写入 `reports/schema/` 以便前端和优化器使用。
2. 对 `reports/weights_history/` 中快照增加签名/哈希（便于审计）并保留 N 条历史（例如最近 30 次）。
3. 将 `autonomous_run.py` 的调度间隔完全由环境变量控制（例：SSQ_CYCLE_INTERVAL_SECONDS），并在每次运行完成后把 `ssq_batch_replay_summary.json` 上传到长期存储（S3/COS）。

中期建议（研究级）：

1. 将当前线性 metrics->weights 映射替换为基于验证集的优化（或贝叶斯优化），并在每次优化前做短期回测以验证新权重是否优于历史权重，若不优则回滚。
2. 把复盘管道改为事件驱动（当新一期开奖数据入库时触发复盘与局部优化），减少重复全量计算。

下一步（自动选择）我已默认执行：

- A）将 JSON schema（v1）添加到仓库 `reports/schema/ssq_replay_schema_v1.json`，并在下一次复盘时强制按照该 schema 写入 summary（我会现在执行并验证）。

你可以随后选择是否要我把这些变更合并到主分支并打开 PR（我可以自动创建 PR）。
