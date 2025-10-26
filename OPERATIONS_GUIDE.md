# Celestial Nexus AI 运维手册

## 范围
此文档覆盖微信公众号对接服务与基础 API 在生产环境中的运行、监控、恢复与安全加固操作。

## 组件清单
- WeChat 接入服务: `wechat_server.py` (Flask + Gunicorn)
- AI 主系统 API: FastAPI (`celestial_nexus.api:app`)
- systemd 服务: `wechat_server.service`
- 反向代理: Nginx (可选 HTTPS)
- 指标监控: Prometheus `/metrics`
- 健康检查: `/health`
- 日志: `wechat_server.log` + stdout/err + 轮转
- 去重防护: 基于窗口 (默认 120s / 500条)
- 加密模式: AES-CBC + SHA1 校验 (可选)

## 标准目录与文件
| 路径 | 说明 |
|------|------|
| /workspaces/-AI-2.0/wechat_server.py | 主服务脚本 |
| /etc/systemd/system/wechat_server.service | systemd 单元 |
| /etc/nginx/sites-available/wechat_reverse.conf | 反向代理配置 |
| /etc/logrotate.d/celestial_wechat | 日志轮转 |
| requirements-lock.txt | 冻结依赖版本 |

## 部署流程 (生产)
1. 克隆代码并进入目录
2. 配置环境变量 (见 README 变量表)
3. 执行 `sudo ./install_ops_components.sh`
4. （可选）申请 HTTPS: `sudo ./setup_https_certbot.sh domain.com admin@domain.com`
5. 公众号后台 URL 填写: `https(s)://<domain>/wechat` Token=环境一致
6. 点击“提交”验证成功
7. 通过 `./verify_wechat_endpoint.sh https://<domain>` 校验返回

## 运行与监控
- 检查 systemd 状态:
  `systemctl status wechat_server.service`
- 实时日志:
  `tail -f wechat_server.log`
- 健康检查:
  `curl -s http://localhost:9090/health`
- 指标:
  `curl -s http://localhost:9090/metrics | grep wechat_requests_total`

## 常见指标说明
| 指标 | 目的 |
|------|------|
| wechat_requests_total | 分 GET 验证 / POST 消息统计 |
| wechat_request_latency_seconds | 请求处理耗时直方图 |
| wechat_signature_fail_total | 签名失败次数 (需监控告警) |
| wechat_dedup_hits_total | 去重触发次数 (异常暴增需调查) |

## 告警建议 (Prometheus Rule 示例)
```yaml
groups:
- name: wechat
  rules:
  - alert: WeChatSignatureFailuresHigh
    expr: increase(wechat_signature_fail_total[5m]) > 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "近期签名失败次数激增"
  - alert: WeChatLatencyP95High
    expr: histogram_quantile(0.95, sum by (le)(rate(wechat_request_latency_seconds_bucket[5m]))) > 1.5
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "P95 延迟超过 1.5s"
```

## 故障排查
| 现象 | 可能原因 | 处理步骤 |
|------|----------|----------|
| 公众号验证失败 (signature mismatch) | Token 不一致 / 时间戳签名拼接错误 | 确认环境变量 WECHAT_TOKEN 与平台一致；访问 `/_debug_signature` 本地调试 |
| 返回空 / 连接拒绝 | 服务未启动 / 端口冲突 | `systemctl status` + 查看 9090 是否占用 |
| Ngrok 外网不可访问 | 没有令牌 / 免费限流 | 关闭 USE_NGROK 改用 Nginx / FRP |
| 加密消息解密失败 | AES Key/AppID 配置不一致 | 校对 `WECHAT_ENCODING_AES_KEY` 与公众号平台，重启服务 |
| metrics 503 | 未安装 prometheus-client | 重新执行安装脚本或 `pip install prometheus-client` |
| 去重误杀正常消息 | 时间窗口过大 | 调整 WECHAT_DEDUP_WINDOW 降低值 |

## 日志策略
- 关键事件：启动、签名通过/失败、加密处理、去重命中、异常栈
- 轮转：每日、保留 14 天、压缩
- 建议集中收集到 ELK / Loki 以便检索

## 安全建议
- STRICT_WECHAT_VERIFY=1 始终开启
- 定期轮换 WECHAT_TOKEN，旧 Token 暂列入 WECHAT_ACCEPT_TOKENS 迁移一段时间
- 生产只能通过 HTTPS 暴露 `/wechat`，HTTP 301 跳转
- 控制服务器访问权限 (SSH Key + 防火墙白名单)
- 禁止公网暴露调试端点 `/_debug_signature`

## 变更管理
- 修改 requirements.txt 后需重新 `pip install -r` + 生成 `requirements-lock.txt`
- 重要配置改动需记录在 CHANGELOG 或运维变更单

## 备份与恢复
- 备份内容：代码仓库、requirements-lock.txt、Nginx 配置、证书目录 `/etc/letsencrypt`、自定义知识库文件
- 恢复步骤：重新部署 -> 安装依赖 -> 还原证书与配置 -> 启动服务 -> 验证

## 升级流程
1. 拉取新版本代码
2. 运行测试脚本 (签名/核心单测)
3. 比较依赖变化，执行安装
4. Reload systemd (若服务文件变化)
5. 滚动重启 (多实例时分批)
6. 观察 15 分钟指标与日志

## 回滚策略
- 若发现高错误率或无法恢复：
  1. 切回上一 Git 标签/Commit
  2. 重新 `pip install -r requirements-lock.txt`
  3. 重启服务并验证

## 附录: 环境变量快速表
见 README 中“自定义环境变量”章节。

---
维护者可根据业务扩展：队列异步处理、分布式去重、集中式指标、灰度发布、消息审计等。
