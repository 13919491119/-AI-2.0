
# Celestial Nexus AI 系统

## 项目概述

本系统为传统文化预测领域的自主AI平台，融合六爻、小六壬、八字、奇门遁甲、紫微斗数等传统方法，并通过机器学习自主发现新模式，实现自我学习、自我优化和自我升级。

## 核心功能

- 自主模式发现：6种新型预测模式，30秒周期高频发现，置信度过滤，结构化知识库管理
- 多维度深度分析：性能、准确性、用户行为、系统健康
- 自动性能优化：响应时间、准确性、资源优化
- 安全监控与自动恢复：健康检查、错误检测、自我修复、优雅关机
- 自我升级能力：智能升级、回滚保护、升级历史

- 预测闭环与融合：`ssq_predict_cycle.py` 支持多策略（六爻/小六壬/奇门/AI）与启发式融合
- 自动调优器：`ssq_auto_tuner.py` 基于历史表现生成 `ssq_strategy_weights.json`，被融合逻辑自动读取
- 长期后台运行：`supervisord_xuanji_loops.conf` 新增 `xuanji_tuner` 每6小时自动更新权重
- 评估报告：`ssq_evaluate.py` 评估最近窗口命中表现，输出至 `reports/`（JSON/Markdown）
快速使用：

```bash
# 手动运行调优器（可选）
python ssq_auto_tuner.py --data ssq_history.csv --train-ai

```text
python ssq_evaluate.py

# 查看后台任务状态
supervisorctl -c /workspaces/-AI-2.0/supervisord.conf status
 

## 可视化架构图

```mermaid
graph TD
  A[API接口] -->|RESTful 7端点| B[AI核心引擎]
  B --> C[自主学习循环]
  B --> D[监控引擎]
  B --> E[升级引擎]
  B --> F[结构化知识库]
  C --> F
  D --> F
  E --> F
  B --> G[融合预测]
  G --> H[多系统分数]
  G --> I[量子融合+贝叶斯加权]
  F --> J[前端报告]
```bash

## 目录结构



celestial_nexus/
 ├── ai_core.py    # 核心AI引擎，三大自主循环
 ├── api.py        # FastAPI接口，7个端点
 ├── config.py     # 配置管理
 ├── monitor.py    # 性能与健康监控
 ├── upgrade.py    # 智能升级
 ├── pattern_discovery.py # 模式发现
 └── report_frontend.py   # 前端报告



## 快速开始

见 QUICK_START.md

## AI智能体元学习体系（一键启动）

该体系为系统主任务，统一编排端到端闭环与元学习：

- 预测 → 复盘 → 优化 → 权重快照 → 可视化 → 再预测（持续）
- AutoRL 自进化外环（低频触发、门控评估、最优快照）
- 强门控晋升/替换策略对接融合权重（可配置、安全回滚）

一键启动（推荐通过 Makefile）：

```bash
make start-meta
```

或直接运行脚本：

```bash
./start_ai_meta_system.sh
```

### 全自动运行、自适应调度与健康状态

系统自动执行“预测→复盘→优化→权重快照→可视化→再预测”闭环，并周期性低频触发 AutoRL 元学习外环。新增自适应调度与心跳机制：

- 心跳文件：`autonomous_heartbeat.json` 包含最近一轮耗时、循环计数、下一轮间隔、最后一次 AutoRL / 可视化时间戳。
- 自适应策略：读取上一轮耗时自动调整 `SSQ_CYCLE_INTERVAL_SECONDS`（启发式）并写入 `ai_meta_autoadapt.json`。
- 状态脚本：`tools/ai_meta_status.py` 输出整合状态（pid、心跳、自适应结果），可用于监控与运维。

启用自适应（默认已加载模块）：可通过环境变量限制区间：
```bash
export SSQ_ADAPT_MIN_SECONDS=0      # 最小间隔
export SSQ_ADAPT_MAX_SECONDS=3600   # 最大间隔
```

执行状态脚本查看当前运行情况：
```bash
python tools/ai_meta_status.py
python tools/ai_meta_status.py --check  # 失败返回非零码
```

心跳/适应文件示例字段：
```json
{
  "ts": 1730961234.12,
  "loop_count": 57,
  "duration_seconds": 4.83,
  "next_interval_sec": 7,
  "last_autorl_ts": 1730957000.55,
  "last_visual_ts": 1730953600.11
}
```

### 状态检查与 systemd 示例

若要快速判断主任务是否在运行，可使用仓库自带的状态脚本：

```bash
python tools/ai_meta_status.py --check
# 返回码 0 表示全部运行正常，非0 表示存在异常（便于监控系统使用）
```

系统还提供一个本地 HTTP 健康检查服务（默认仅监听 localhost:5001），支持两个端点：

- GET /health -> 简单 up/down（HTTP 200 或 503）
- GET /status -> 返回完整 JSON 状态（同 `ai_meta_status.py` 输出）

可通过环境变量调整监听地址：

```bash
export AI_HEALTH_HOST=127.0.0.1
export AI_HEALTH_PORT=5001
```


另外仓库提供了一个 `systemd` 单元示例，位于 `deploy/ai_meta_system.service`，适合在 Linux 服务器上托管：

- 将文件拷贝到 `/etc/systemd/system/ai_meta_system.service`，修改 `WorkingDirectory` 与 `User` 为目标环境后：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ai_meta_system.service
sudo journalctl -u ai_meta_system.service -f
```


关键环境变量（可按需覆盖）：

```bash
# 闭环与超时
SSQ_CYCLE_INTERVAL_SECONDS=0
SSQ_MAX_ATTEMPTS_PER_ISSUE=0
SSQ_MAX_SECONDS_PER_ISSUE=5

# 低频任务
AUTORL_MIN_INTERVAL_HOURS=12
VIS_MIN_INTERVAL_HOURS=6

# AutoRL→生产融合器策略
AUTORL_PROMOTE=1                          # 0 关闭，1 开启
AUTORL_PROMOTE_STRATEGY=promote           # blend | promote | replace
AUTORL_BLEND_ALPHA=0.05                   # blend 强度
AUTORL_PROMOTE_TARGET_WEIGHT=0.6          # promote 目标占比
AUTORL_REPLACE_WEIGHT=0.85                # replace 目标占比
AUTORL_PROMOTE_MIN_DELTA=0.02             # 与基线均值的最小提升
AUTORL_PROMOTE_LB_DELTA=0.02              # 与基线下置信界的最小提升
```

查看当前配置而不启动：

```bash
python -m ai_meta_system.main --print-config
```

## API自动生成文档

本系统基于 FastAPI，自动生成并托管 Swagger/OpenAPI 文档。

- 启动API服务后，访问 [http://localhost:8000/docs](http://localhost:8000/docs) 查看交互式API文档。
- 也可访问 [http://localhost:8000/redoc](http://localhost:8000/redoc) 查看完整API说明。

## 测试

- 单元测试：`python -m unittest tests/test_ai_core.py`
- API测试：`python -m unittest tests/test_api.py`

## 部署

- 演示模式：`python demo_run.py`
- 自主模式：`python autonomous_run.py`
- API服务：`uvicorn celestial_nexus.api:app --reload`
- Docker：
- `docker build -t celestial-nexus-ai .`
- `docker run -p 8000:8000 celestial-nexus-ai`

## 运维与生产组件

已集成以下基础运维能力：

| 组件 | 功能 | 相关文件 |
|------|------|----------|
| systemd 服务 | 微信对接守护进程自启动/重启 | `wechat_server.service` |
| Gunicorn | 生产 WSGI 部署(gevent) | `gunicorn_wechat.conf.py`, `start_wechat_gunicorn.sh` |
| Prometheus Metrics | `/metrics` 暴露请求计数/延迟/签名失败/去重命中 | `wechat_server.py` |
| 消息去重与重放保护 | 基于 MsgId+内容 哈希窗口缓存 | `wechat_server.py` |
| Redis 去重扩展 | 跨进程/多实例去重 (WECHAT_REDIS_URL) | `wechat_server.py` |
| 速率限制 | 每用户每分钟上限，可Redis扩展 | `wechat_server.py` |
| Logrotate | 日志滚动 14 天压缩 | `/etc/logrotate.d/celestial_wechat` (通过安装脚本生成) |
| Nginx 反向代理 | 统一 80/443 转发 `/wechat` `/health` `/metrics` | 安装脚本生成配置 |
| FastAPI 生产服务 | Gunicorn+Uvicorn Worker 部署 API | `gunicorn_api.conf.py`, `start_api_gunicorn.sh`, `celestial_api.service` |
| HTTPS 自动证书 | Let’s Encrypt 一键申请+续期 | `setup_https_certbot.sh` |
| 依赖冻结 | 生成 `requirements-lock.txt` | `install_ops_components.sh` |

### 快速安装 (需 root)

```bash
chmod +x install_ops_components.sh setup_https_certbot.sh
sudo ./install_ops_components.sh
# 若有域名: sudo ./setup_https_certbot.sh your.domain.com admin@your.domain.com


### 自定义环境变量

| 变量 | 说明 | 默认 |
|------|------|------|
| WECHAT_TOKEN | 主 Token | celestial_nexus_ai_token |
| WECHAT_ACCEPT_TOKENS | 兼容旧 Token 列表, 逗号分隔 | 空 |
| STRICT_WECHAT_VERIFY | 严格签名验证 (1/0) | 1 |
| WECHAT_ENCODING_AES_KEY | 安全模式 AES Key | 未设置则明文 |
| WECHAT_APPID | 公众号 AppID (安全模式需要) | 空 |
| WECHAT_PORT | 服务监听端口 | 9090 |
| USE_NGROK | 是否启用 Ngrok | false |
| WECHAT_DEDUP_WINDOW | 消息去重窗口(秒) | 120 |
| WECHAT_DEDUP_MAX | 去重缓存最大条目 | 500 |
| WECHAT_REDIS_URL | Redis 地址(启用分布式去重) | 空 |
| WECHAT_ORIGINAL_ID | 公众号原始ID (gh_开头) 用于安全校验 | 空 |
| STRICT_ORIGINAL_ID | 原始ID严格校验(1启用) | 0 |
| WECHAT_RATE_LIMIT_PER_MIN | 每用户每分钟消息上限(0关闭) | 0 |

### 监控指标 (Prometheus)

若安装了 `prometheus-client`，访问 `/metrics` 可见：


wechat_requests_total{method="GET",type="verify"}
wechat_requests_total{method="POST",type="incoming"}
wechat_request_latency_seconds_bucket{type="incoming",...}
wechat_signature_fail_total
wechat_dedup_hits_total

API 服务指标示例 (`/api_metrics` 通过 Nginx 或直接 `:8000/metrics`):


celestial_api_request_latency_seconds_bucket{path="/discover",le="0.1"} ...

```text



### 签名验证脚本



./verify_wechat_endpoint.sh  # 服务运行后执行，应显示 [PASS]



### 加密模式本地模拟 & 单测



celestial_api_requests_total{path="/health",method="GET",status="200"}
celestial_api_request_latency_seconds_bucket{path="/discover",le="0.1"} ...

export WECHAT_TOKEN=yourtoken
export WECHAT_ENCODING_AES_KEY=43位Key
export WECHAT_APPID=wx123...
python simulate_encrypted_message.py '测试加密消息'
cp .env.wechat.example .env.wechat && python simulate_encrypted_message.py '测试加密消息'
pytest -k wechat_crypto_flow  # 若已安装 pytest



### Prometheus 抓取与可视化

示例抓取配置：`prometheus_scrape_example.yml`
Grafana 仪表盘模板：`grafana_dashboard_wechat_api.json`
快速启动本地观测 (Prometheus+Grafana)：

```

docker compose -f docker-compose.observability.yml up -d

```

### Redis 配置

确保 Redis 服务正在运行，并设置以下环境变量：

```

export WECHAT_REDIS_URL=redis://localhost:6379

```

这将启用跨进程/多实例去重功能。
自定义告警规则示例：`prometheus_rules.yml`

### 上线完成报告

详见 `正式公众号上线完成报告.md`

### 系统自检

```

bash system_self_check.sh

```

### 日志位置

```

wechat_server.out.log / wechat_server.err.log / wechat_server.log

```

### 常见生产步骤

1. 部署代码并修改 `wechat_server.service` 中路径/环境变量
2. 运行 `install_ops_components.sh`
3. 配置域名 DNS 指向服务器公网IP
4. 运行 `setup_https_certbot.sh <domain> <email>` 获取证书
5. 在公众号平台填写 `https://<domain>/wechat` 与对应 Token
6. 通过 `./verify_wechat_endpoint.sh https://<domain>` 本地或服务器验证
7. 监控 `/health` 和 `/metrics`

### 消息加密 (安全模式)

设置：

```

export WECHAT_ENCODING_AES_KEY=公众号平台提供的43位Key
export WECHAT_APPID=wx....

```

重启服务后会自动启用加密解密 (POST 消息 encrypt_type=aes)。

## 创新亮点

- 超越传统方法的模式发现
- 完全自主操作，无需人工干预
- 生产就绪，支持监控、测试、文档、自动恢复

## 联系与支持

详见文档与API说明。

## 微信公众号集成

系统支持与微信公众号集成，提供多种集成模式：

- **Ngrok模式**：使用Ngrok创建公网可访问URL（需要Ngrok令牌）

  ```bash
  ./wechat_integration_selector.sh  # 选择选项1
  ```

- **本地模式**：使用本地端口，适合本地测试

  ```bash
  ./wechat_integration_selector.sh  # 选择选项2
  ```

- **FRP内网穿透**：使用FRP创建公网可访问URL（需要有公网服务器）

  ```bash
  ./wechat_integration_selector.sh  # 选择选项3
  ```

- **Nginx反向代理**：使用Nginx反向代理（适合生产环境）

  ```bash
  ./wechat_integration_selector.sh  # 选择选项4
  ```

详细配置说明请参阅 [公网访问配置指南](PUBLIC_ACCESS_CONFIGURATION.md)。如遇到Token验证失败问题，请参阅 [微信集成故障排除指南](WECHAT_TROUBLESHOOTING.md)。
