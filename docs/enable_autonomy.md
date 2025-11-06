# 启用完全自治（Phase C）指南（安全与权限配置）

此文档说明将仓库中“完全自治”模板切换为真实可运行的步骤。**请在专门的测试/预发布环境中先完成全部步骤并验证后再在生产环境中启用。**

1. 必要的 Secrets（至少）

- GH_TOKEN: 用于 gh CLI 自动创建/合并 PR（最小权限：repo:pull_requests, repo:status）
- ENABLE_PHASE_C: set to 'true' to allow workflows to run
- AUTO_MERGE: set to 'true' to allow auto merging (慎用)
- KUBE_CONFIG_DATA: base64-encoded kubeconfig for a restricted service-account with access only to canary namespace
- CANARY_METRICS_URL: metrics endpoint for canary to be polled by auto_rollback

1. 最小 IAM / RBAC 建议

- CI service account: can create branches and open PRs, but NOT bypass branch protection
- Deployment service account: only allowed to deploy to 'canary' namespace and cannot modify cluster-wide resources

1. CI 配置（示例 GitHub Actions）

- 在 repository settings -> secrets 中添加上面的 secrets
- 打开 `.github/workflows/auto-full-autonomy.yml`，将 DRY_RUN 或条件设置调整为你允许的级别

1. 审计与回滚

- 在可部署环境中启用审计日志
- 配置 Prometheus/Grafana 告警，确保工具可以调用 rollback

1. 人机混合（建议）

- 初始阶段保持 `HumanGate` 审批（tools/human_gate.py）启用，直到自动化运行稳定

1. 风险与保险措施

- 在 CI 中保留 DRY_RUN flag 作为最后安全阀
- 每个自动合并事件需要 artifact 签名或 CI 指纹

如需我为你把这些 secrets 的检查点/CI status check 写成详细步骤或在 repository 中生成可直接 paste 的 IAM policy 示例，回复“生成权限策略示例”。

---

附注（由自动化代理在容器内做出的默认选择）

在本仓库运行的自动化代理已选择以下安全优先的默认路径：

- 在当前容器内只进行 dry-run / 准备性操作（生成 patch、CI 模板、审计日志、构建本地分支），但不会将分支或代码直接推送到远端，因为当前容器未配置 Git 远端。
- 若你希望由本容器直接推送并创建 PR，请在回复中提供远端仓库 URL（SSH 或 HTTPS）并确认允许在此环境使用凭据；否则请在受信任的宿主机上运行仓库内的一键脚本 `tools/run_full_autonomy.sh`（默认同样以 dry-run 执行），在宿主机上提供必要的 secrets 后可执行真实推送/自动合并/部署。

注：所有关键操作（推送、PR 创建、合并、部署）都会写入审计日志并保留回滚路径。此附注已被记录为本地审计条目（见 `docs/autonomy_decision.md`）。
