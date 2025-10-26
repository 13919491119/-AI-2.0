# 运行与守护（systemd）

本项目提供 systemd 单元用于在 Linux 服务器上实现自启动与异常自愈：

- 服务单元：
  - `systemd/xuanji-autonomous.service`：自主调度（闭环双色球 + 监控）
  - `systemd/xuanji-person.service`：历史人物循环任务
- 环境变量文件：`/etc/default/xuanji-ai`（一键脚本会生成模板）

## 一键安装/启动

```bash
sudo bash install_systemd_services.sh
```

安装后查看状态：

```bash
sudo systemctl status xuanji-autonomous xuanji-person
sudo journalctl -u xuanji-autonomous -f
```

## 参数与资源控制

通过 `/etc/default/xuanji-ai` 控制：

- `SSQ_CONSULT_EXTERNAL`：是否启用外部建议（1/0）
- `SSQ_CYCLE_INTERVAL_SECONDS`：闭环周期间隔（建议 300~900 秒以控资源；设 0 表示上一轮结束立即下一轮）
- `SSQ_MAX_ATTEMPTS_PER_ISSUE`：单期尝试上限，控制计算成本
- `DEEPSEEK_API_KEY`：Deepseek 密钥

修改后执行：

```bash
sudo systemctl daemon-reload
sudo systemctl restart xuanji-autonomous xuanji-person
```

## 容器或无 systemd 环境

请使用 `tools/guard_loops.sh` 守护，或 `start_services.sh` 统一启动。
