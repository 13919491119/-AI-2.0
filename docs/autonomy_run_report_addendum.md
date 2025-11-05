# Addendum: 在受信宿主机上执行 Canary 部署的操作手册

本文件为 `docs/autonomy_run_report.md` 的补充，提供了可直接复制执行的步骤与示例，便于在受信宿主机或 CI runner 上完成 canary 部署与回滚监控。

## 前提

- 只在受信宿主机或受管 CI runner 上执行。不要在不受信的共享环境中暴露 kubeconfig。
- 推荐使用受限的 service-account，仅对 `canary` 命名空间有 deploy/rollback 权限。

## 步骤示例

1) 将 `KUBE_CONFIG_DATA`（base64 编码的 kubeconfig）设为环境变量：

```bash
export KUBE_CONFIG_DATA="$(cat /path/to/kubeconfig | base64 -w0)"
```

2) 解码并写入临时 kubeconfig：

```bash
mkdir -p /tmp/xuanji_kube
echo "$KUBE_CONFIG_DATA" | base64 -d > /tmp/xuanji_kube/config
export KUBECONFIG=/tmp/xuanji_kube/config
```

3) 验证 manifests（dry-run）：

```bash
./tools/deploy_canary.sh --artifact artifacts --namespace canary --dry-run=true
```

4) 触发真实 canary（谨慎）：

```bash
./tools/deploy_canary.sh --artifact artifacts --namespace canary --dry-run=false
```

5) 启动回滚监控：

```bash
python3 tools/auto_rollback.py --canary-endpoint "http://canary-service.metrics.local/metrics" --threshold-file tools/rollback_thresholds.json --interval 30
```

6) 如果需要回滚（监控检测到 breach），在受信主机上执行：

```bash
KUBECONFIG=/tmp/xuanji_kube/config ./tools/rollback_helper.sh --deployment my-service --namespace canary --confirm --dry-run=false
```

7) 清理临时 kubeconfig：

```bash
shred -u /tmp/xuanji_kube/config || rm -f /tmp/xuanji_kube/config
rmdir /tmp/xuanji_kube || true
```

## 安全建议

- 为 canary 操作使用最小权限原则（least privilege）。
- 记录审计日志：将每次部署/回滚的命令与输出追加到 `logs/autonomy_audit.log`（或运维中心的集中日志系统）。

---

如果你希望，我可以：

- 在当前容器中生成 `artifacts` 包（无需 kubeconfig）并将路径写入 `docs/autonomy_run_report.md` 或本 addendum；
- 等待你以安全方式提供 `KUBE_CONFIG_DATA`，然后在受信宿主机上或在代理控制下自动完成部署并记录审计；
- 尝试分析 CI 失败日志并生成修复 PR 草案。
