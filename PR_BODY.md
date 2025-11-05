# feat: add safe autonomous workflow, FastAPI smoke service, and monitoring

## 简要说明

该 PR 为“玄机”系统添加了一组安全优先的自动化改进，主要目标是可审计、低风险地支持后续的自动化/升级流程。默认保留自我升级为 dry-run/manual 模式（需要人工批准才能实际应用升级）。

## 包含的改动

- 添加/清理 FastAPI 推理 smoke 服务：`api/server.py`（异步后台加载模型，/health、/predict、/model-info、/reload-model）。
- 添加轻量监控守护脚本：`tools/monitor_xuanji.py`（轮询日志、检测 `upgrade_plan_*` 文件、输出到 `logs/monitor.log`）。
- 修复训练脚本的导入问题：`experiments/train.py`（使其能从仓库根直接运行以便 smoke 训练）。
- 其他轻量的 lint/type 修复以提高可维护性。

## 验证步骤

1. 应用 patch 并切换到分支：

```bash
git checkout -b xuanji/safe-updates
git am --signoff < xuanji_changes.patch
```

1. 启动 API：

```bash
# 推荐通过环境变量控制端口，避免与已有进程冲突。例如
PORT=8000 uvicorn api.server:app --host 127.0.0.1 --port ${PORT}

# 或使用仓库附带的安全启动脚本，会自动选择一个未占用的端口
./tools/start_api_safely.sh
# 验证： GET /health -> {"status":"ok"}
```

1. 运行 smoke 训练：

```bash
python3 experiments/train.py --min-samples 200
```

1. 启动监控守护：

```bash
python3 tools/monitor_xuanji.py &
```

## 回滚策略

若需回滚，可使用 `git revert <commit>` 或在 PR 被合并后使用 GitHub 的 revert 功能。

## 备注

- 自我升级保持 dry-run/manual，任何自动升级需要明确批准。
