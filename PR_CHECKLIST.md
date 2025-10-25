# PR 审阅检查清单（xuanji/safe-updates）

目的：帮助审阅者在合并前快速验证安全改动和 smoke 测试。

必检项：

- [ ] patch 应用于干净分支并且能被 `git am` 或 `git apply` 成功应用；无冲突。
- [ ] 按 PR 文档步骤启动 API：
  - `uvicorn api.server:app --host 127.0.0.1 --port 8000`，验证 `GET /health` 返回 200 且 body 包含 `{"status":"ok"}`。
- [ ] smoke 训练可运行（小数据集）：
  - `python3 experiments/train.py --min-samples 200`（或更小的 `--min-samples` 用于 CI），确认没有导入错误并生成 `ssq_ai_model_state.json`。
- [ ] 监控守护能正常启动：
  - `python3 tools/monitor_xuanji.py &`，确认 `logs/monitor.log` 有周期性条目并且没有异常崩溃。
- [ ] 本地 lint/type 检查：`flake8`/`pyright`（若项目使用）无致命错误。
- [ ] 快速安全审阅：确认没有将凭据、密钥或敏感信息加入仓库／日志。
- [ ] 回滚步骤已在 PR 描述中列出，且可在本地复现。

可选项（合并前建议）：

- 在 CI 中加入 `uvicorn` 快速启动检查（端口替换为随机或 CI 支持的方式）和 `experiments/train.py` 的 smoke 测试。
- 将 API 绑定改为通过环境变量控制的端口，避免默认冲突（例如 `PORT=${PORT:-8000}`）。

备注：当前 workspace 里监控日志显示有持续的 `address already in use (127.0.0.1:8000)` 错误，可能是存在旧的 uvicorn 进程（PID 18359）占用端口；请在合并前确认不会在部署阶段重复启动相同端口的服务。