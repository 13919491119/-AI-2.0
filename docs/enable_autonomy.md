# 启用完全自治（Phase C）指南（安全与权限配置）

此文档说明将仓库中“完全自治”模板切换为真实可运行的步骤。**请在专门的测试/预发布环境中先完成全部步骤并验证后再在生产环境中启用。**

1) 必要的 Secrets（至少）

- GH_TOKEN: 用于 gh CLI 自动创建/合并 PR（最小权限：repo:pull_requests, repo:status）
- ENABLE_PHASE_C: set to 'true' to allow workflows to run
- AUTO_MERGE: set to 'true' to allow auto merging (慎用)
- KUBE_CONFIG_DATA: base64-encoded kubeconfig for a restricted service-account with access only to canary namespace
- CANARY_METRICS_URL: metrics endpoint for canary to be polled by auto_rollback

2) 最小 IAM / RBAC 建议

- CI service account: can create branches and open PRs, but NOT bypass branch protection
- Deployment service account: only allowed to deploy to 'canary' namespace and cannot modify cluster-wide resources

3) CI 配置（示例 GitHub Actions）

- 在 repository settings -> secrets 中添加上面的 secrets
- 打开 `.github/workflows/auto-full-autonomy.yml`，将 DRY_RUN 或条件设置调整为你允许的级别

4) 审计与回滚

- 在可部署环境中启用审计日志
- 配置 Prometheus/Grafana 告警，确保工具可以调用 rollback

5) 人机混合（建议）

- 初始阶段保持 `HumanGate` 审批（tools/human_gate.py）启用，直到自动化运行稳定

6) 风险与保险措施

- 在 CI 中保留 DRY_RUN flag 作为最后安全阀
- 每个自动合并事件需要 artifact 签名或 CI 指纹

如需我为你把这些 secrets 的检查点/CI status check 写成详细步骤或在 repository 中生成可直接 paste 的 IAM policy 示例，回复“生成权限策略示例”。
