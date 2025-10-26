# 阶段 C — 完全自治 实施蓝图（高风险，需严格安全策略）

本文档汇总实现“完全自治”系统所需的组件、权限、流程、回滚策略与安全控制。请在有合规和运维批准前勿在生产环境启用以下自动化。

主要目标
- 使用受限权限的 service-account 在 CI 中自动合并通过的模型更新并将其部署到 canary 环境；
- 在 canary 运行自动 A/B/渐进流量拆分；
- 持续监控在线指标并在质量下降时自动回滚；
- 在低置信情况下触发人机混合决策（人工复核）。

关键构件（清单）
- Model packaging & signing: 模型 artifact 打包并产生 SHA256 + 可选签名（GPG/PKI）。
- Model registry: 存放 artifact、metadata、评估报告与签名。建议使用 S3 / artifact repo。
- CI workflow: 自动触发训练→评估→打包→上传 artifact→创建 PR →（合并后）自动部署到 canary。
- Deployment controller: 支持 canary/渐进发布与 A/B 路由（Kubernetes + Istio 或 feature-flag 服务）。
- Monitoring & metrics: Prometheus/Grafana + 自定义质量指标（accuracy, latency, error-rate, drift metrics）。
- Auto-rollback: 基于显式阈值和统计检验自动回滚并记录事件。
- HumanGate: 当自动决策置信不足或关键阈值接近时暂停并通知人工审查。

权限与最小授权（必需）
- CI service-account（仅限于目标 repo 的写入分支权限且不能直接绕过分支保护）;
- 部署 service-account（Kubernetes: limited namespace / only canary namespace）;
- 读写 artifact 存储（仅限 registry 路径）;
- 监控/报警写入权限（仅将报警推到已批准的紧急通道）。

安全与防护措施（必须实施）
1. 强制审计日志：所有自动合并、部署、回滚动作必须在审计日志中追加可验证的事件（artifact id、commit、metrics snapshot、trigger reason）。
2. 签名与可验证 artifact：除非 artifact 有有效签名，否则部署过程拒绝执行。
3. 阈值与多重检测：至少两项独立指标（例如 accuracy 回归 + 增加的 5xx 率）触发回滚。
4. Canary + 自动回滚：默认渐进发布（10% -> 30% -> 100%），每一步都有阈值检查。若不通过立即回滚并报警。
5. 人机混合决策：当置信度低或关键指标漂移但未达到强回滚阈值时暂停，并发送审核链接/上下文给指定审查者。
6. Secrets 管理：所有凭据存放在 CI/平台的 secret 存储（例如 GitHub Actions Secrets / Vault）；不在仓库或聊天中明文写出。

部署前的合规清单（示例）
- 完整的单元/集成/回归测试通过。
- 线下评估报告与基线对比（包含置信区间/显著性检验）。
- 监控/报警配置已准备好并与 on-call 联系人绑定。

说明
- 本仓库提供样例脚本和 workflow 模板（tools/ 和 .github/workflows/），在你把 secrets 和运行权限配置到 CI/平台后即可启用。

风险声明
- 任何允许 CI 自动合并并自动部署到生产的动作都有不可逆风险。在部署前，请保证你已完成风险评估并获得组织授权。

如需我现在在仓库中生成 workflow 和脚本以便你在有权限环境开启，回复 “生成实现文件”。
