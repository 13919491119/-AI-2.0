部署说明：AI Meta System systemd 单元

将 `deploy/ai_meta_system.service` 拷贝到目标服务器的 `/etc/systemd/system/`，然后启用并启动：

```bash
sudo cp deploy/ai_meta_system.service /etc/systemd/system/ai_meta_system.service
sudo systemctl daemon-reload
sudo systemctl enable --now ai_meta_system.service
sudo journalctl -u ai_meta_system -f
```

注意：
- 修改 `WorkingDirectory` 至实际的代码目录（示例使用 `/workspaces/-AI-2.0`）。
- 可在单元文件中设置环境变量，或使用 `/etc/default/ai_meta_system` 加载。
