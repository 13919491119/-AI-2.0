# 安装 systemd 单元示例（xuanji API 与 report frontend）

这些 unit 文件位于 `systemd/` 目录：

- `systemd/xuanji_api.service` — 运行 uvicorn celestial_nexus.api
- `systemd/report_frontend.service` — 运行 `celestial_nexus/report_frontend.py`

注意事项
- 如果你使用虚拟环境，请把 `ExecStart` 修改为指向虚拟环境中的 `uvicorn` 或 `python3`，例如：
  ExecStart=/home/youruser/.venvs/xuanji/bin/uvicorn celestial_nexus.api:app --host 0.0.0.0 --port 8000
- 日志默认写入仓库 `logs/` 目录；确保该目录对 systemd 服务用户可写（或修改为合适路径）。

安装与启用（在目标主机上运行，需 root 或 sudo 权限）
```bash
# 1. 复制 unit 文件到 systemd 目录
sudo cp systemd/xuanji_api.service /etc/systemd/system/
sudo cp systemd/report_frontend.service /etc/systemd/system/

# 2. 创建/确认日志目录（如果需要）
sudo mkdir -p /workspaces/-AI-2.0/logs
sudo chown -R youruser:yourgroup /workspaces/-AI-2.0/logs

# 3. 重新加载 systemd，并启用/启动服务
sudo systemctl daemon-reload
sudo systemctl enable xuanji_api.service
sudo systemctl enable report_frontend.service
sudo systemctl start xuanji_api.service
sudo systemctl start report_frontend.service

# 4. 检查状态与日志
sudo systemctl status xuanji_api.service
sudo journalctl -u xuanji_api.service -f

# 若使用虚拟环境或需要环境变量，可在 unit 中使用 Environment= 或 EnvironmentFile=
```

如需我帮你把 `ExecStart` 指向特定虚拟环境或把这些单元部署到目标服务器，请提供虚拟环境路径或允许我运行相应命令（注意：需要 sudo 权限，必须由你手动在目标主机执行）。
