# 自动化复盘与优化说明（Automation README）

此文档说明本仓库中新加入的“双色球历史复盘 -> 指标驱动优化 -> 权重快照”自动化流程的目的、产物、如何回放以及后续建议。

注意：本说明针对开发/测试环境。生产部署前请依据运维安全与审计要求调整。

## 主要变更（代码/脚本）

- `ssq_batch_replay_learn.py`：
  - 增强字段解析（更鲁棒地识别 `期次`、`开奖日期`、`红球`、`蓝球` 等列）；
  - 生成传统文本报告 `reports/ssq_batch_replay_report.txt`；
  - 额外生成机器可读 JSON 汇总 `reports/ssq_batch_replay_summary.json`（包含每模型统计与 sample_details）。
- `optimize_models.py`：
  - 优化器优先读取 `reports/ssq_batch_replay_summary.json`/`reports/ssq_batch_replay_report.txt`，基于复盘指标（全中率/红球命中率/蓝球命中率）计算新权重并写回 `ssq_strategy_weights.json`；
  - 每次保存权重时生成审计快照到 `reports/weights_history/weights_{timestamp}.json`，便于回溯与回滚。
- `autonomous_run.py`：
  - 在 SSQ 闭环任务每轮完成后会尝试运行 `ssq_batch_replay_learn.py` 与 `optimize_models.py`（若文件存在），形成自动化闭环（复盘→优化→保存）。
  - 新增“AutoRL 轻量自进化”低频触发器：每隔 AUTORL_MIN_INTERVAL_HOURS（默认 12 小时）运行一次 `python -m autorl.runner`（人口规模与代数较小，便于在生产环境中低成本探索），并将产物写入 `reports/autorl_runs/`。

## AutoRL/Meta-RL（轻量版）

- 目录：`autorl/`
  - `specs.py`：定义轻量环境（非平稳 K 臂老虎机）与评估方法。
  - `pbt.py`：简易 PBT（Population-Based Training）实现，支持突变/利用。
  - `runner.py`：编排多环境评估、PBT 搜索、聚合指标、门控（基于 `avg_mean_reward` 的最小增益阈值），并把运行产物存到 `reports/autorl_runs/`。
  - `meta_metrics.py`：门控与最佳快照 `best.json` 维护。

- 产物路径：`reports/autorl_runs/`
  - `run_YYYYmmdd_HHMMSS.json`：每次运行的详细记录（参数、分环境指标、聚合指标、门控决策）。
  - `best.json`：当前最优聚合指标的快照（用于对比、门控）。

- 触发方式：
  - 自动：由 `autonomous_run.py` 低频触发（默认 12 小时一次，可通过环境变量 `AUTORL_MIN_INTERVAL_HOURS` 配置）。
  - 手动：
    ```bash
    python -m autorl.runner --population 8 --generations 6 --train-steps 300 --eval-steps 300
    ```

- 注意：该实现为“无第三方依赖”的工程骨架，便于后续替换为真实 RL 训练（例如接入 stable-baselines3/RLlib/Optuna/Ray Tune）。当前采用非平稳老虎机作为验证沙箱，重在流程与产物可追溯。

## 关键输出路径

- 文本复盘报告（人类可读）： `reports/ssq_batch_replay_report.txt`
- JSON 汇总（机器可读）： `reports/ssq_batch_replay_summary.json`（包含每模型统计与命中率）
- 指标历史（机器可读，按时间戳）： `reports/metrics_history/`（例如 `metrics_20251104_035446.json`）
- 当前融合权重： `ssq_strategy_weights.json`
- 权重快照（历史）： `reports/weights_history/`（按时间戳命名，例如 `weights_20251104_035446.json`）

## 如何手动回放（开发/调试）

在项目根目录下执行：

```bash
# 生成/更新文本报告与 JSON 汇总
python3 ssq_batch_replay_learn.py

# 基于最新报告运行优化器并生成权重快照
python3 optimize_models.py

# 查看最新权重
cat ssq_strategy_weights.json

# 列出历史快照
ls -lh reports/weights_history | tail -n +1
```

说明：如果 `ssq_batch_replay_learn.py` 已包含最新历史数据输出，可直接运行 `optimize_models.py`（优化器会自动尝试读取报告并做出决策）。

## 在 CI 中运行集成测试

此仓库已包含 GitHub Actions 工作流 `.github/workflows/ci.yml`：

- 默认行为（push / pull_request）：运行单元测试（会跳过标记为 `integration` 的测试）。
- 手动触发（Actions -> 选择 `CI` workflow -> Run workflow）：会启动本仓库的后端服务（使用 `uvicorn api_server:app` 在端口 8000）并运行所有标记为 `integration` 的测试。为使微信相关集成测试指向正确服务，工作流在运行测试前会设置环境变量 `WECHAT_BASE=http://127.0.0.1:8000`。

注意：集成测试可能需要额外环境变量或配置（例如微信的加密 key），请在触发前在 workflow 或仓库 secrets 中提供所需值。

## 回滚到指定权重快照

如果需要回滚到某一历史权重（例如 `weights_20251104_035446.json`），可以运行：

```bash
cp reports/weights_history/weights_20251104_035446.json /tmp/weights_snap.json
# 将 snapshot 中的 weights 部分恢复为主权重文件（请在恢复前备份当前权重）
python3 - <<'PY'
import json,sys
fn='/tmp/weights_snap.json'
with open(fn,'r',encoding='utf-8') as f:
    snap=json.load(f)
with open('ssq_strategy_weights.json','w',encoding='utf-8') as f:
    json.dump(snap['weights'],f,ensure_ascii=False,indent=2)
print('已恢复权重，请检查 ssq_strategy_weights.json')
PY
```

注意：生产环境回滚应当经过变更控制与审计流程。

## 建议与下一步（可选）

1. 将 `ssq_batch_replay_learn.py` 的 JSON 输出扩展为包含更多指标（例如红球命中率、蓝球命中率、每模型的置信区间），并把这些指标写入 `reports/metrics_history/` 以便做时间序列分析。
2. 将优化器升级为基于验证集或交叉验证的优化方法（例如贝叶斯优化或凸优化求解器），避免权重过于依赖短期波动。
3. 在 `autonomous_run.py` 中引入限流与阈值判断（例如：仅当指标显著提升或恶化时才更新权重），并把每次更新写入带签名的审计日志。
4. 添加单元测试：针对 `ssq_batch_replay_learn.py` 的解析逻辑与 `optimize_models.py` 的 metrics_to_weights 输出行为编写单元测试（pytest）。

## 联系和变更记录

- 自动化脚本由自动化代理在分支 `xuanji/safe-updates-auto-8e050d3a` 上提交。请查阅相关 PR：Auto: SSQ replay & optimizer automation (JSON reports, windowed summaries, metrics-driven optimizer, weight snapshots + signing)。
- 本 README 最后修改： 2025-11-04（自动生成）。

----
（该文件为自动生成的操作说明，供维护者参考）
