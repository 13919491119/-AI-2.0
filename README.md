# 全自动化运行与AI智能体元学习系统说明

> 日期：2025-11-08

本项目已进入“自愈 + 全自动化 + 元学习”自治运行模式。本文档详细说明：当前自动化是否已启动、核心组件与任务、心跳与监控机制、自愈策略、数据与结果产物、扩展与运维建议、快速启动与健康检测。

## 1. 自动化运行状态概述 ✅

系统关键任务已由守护进程统一启动并持续运行：

- `autonomous_run.py`：自主主循环 + 双色球闭环评估 + 低频 AutoRL + 可视化生成调度。
- `deep_learning_cycle.py`：持续元学习/深度训练迭代，结果 JSONL 增量写入与滚动。
- `yi_books_collect.py`：易学/文化书籍数据定期采集与摘要。
- `batch_predict_persons.py`：历史/人物批量预测迭代采样与增量输出。
- `knowledge_ingest_pipeline.py`（定时触发）: 主题与作者知识画像构建与汇总。

运行状态由 `ai_guard_supervisor.py` 统一监控与自愈，守护状态文件：`reports/ai_guard_status.json`。

附加支持：

- 心跳文件目录：`heartbeats/`（每个任务一个 JSON）。
- 统一健康检测脚本：`check_autonomy.py`（JSON 输出 + 退出码）。
- 一键启动脚本：`start_autonomy.py`（启动 + 自愈 + 快速状态摘要）。

## 2. 组件与任务说明

### 2.1 守护监控层 (`ai_guard_supervisor.py`)
职责：

- 进程存活检查 + 心跳超时判定（各任务独立阈值）。
- 异常退出自动重启 + 指数退避（避免频繁抖动）。
- 自愈动作：清理遗留 `git index.lock`、孤立 PID、确保 `logs/ reports/ heartbeats/` 目录存在。
- 定时调度知识摄取管线（默认每 6 小时，可用环境变量 `KNOWLEDGE_INGEST_INTERVAL_SEC` 覆盖）。
- 输出统一状态：`reports/ai_guard_status.json`（包含 running / fails / last_check）。

\n### 2.2 自主主循环 (`autonomous_run.py`)
功能：

- 单实例保障（PID 文件 + 运行时检查）。
- 启动核心 AI 引擎与闭环评估 `_ssq_cycle_loop`（0 间隔可连续评估）。
- 心跳：统一写入 `heartbeats/autonomous_run.json`，多模式字段（loop / ssq_cycle / error 状态）。
- 低频 AutoRL 调度（默认 ≥12 小时间隔，可调节 `AUTORL_MIN_INTERVAL_HOURS`）。
- 可视化生成调度（≥6 小时间隔，变量 `VIS_MIN_INTERVAL_HOURS`）。
- 异常捕获与错误日志：`logs/autonomous_run.err.log`。

\n### 2.3 深度学习循环 (`deep_learning_cycle.py`)
功能：

- 按轮次迭代训练/推理元学习单元，记录起止时间与耗时。
- 结果文件：`deep_learning_cycle_results.jsonl` 采用增量追加（避免覆盖）。
- 滚动策略：文件超过阈值（约 2MB）保留最近 500 行，防止无限膨胀。
- 心跳：`heartbeats/deep_learning_cycle.json` 包含 `round / time_end / records`。

\n### 2.4 书籍采集 (`yi_books_collect.py`)
功能：

- 周期采集易学与相关书籍信息，进行作者频次统计。
- 网络依赖优先使用 `requests`，失败自动降级到 `urllib`（增强鲁棒性）。
- 心跳：启动与采集完成均写入 `heartbeats/yi_books_collect.json`（字段：`books / top_authors`）。

\n### 2.5 人物批量预测 (`batch_predict_persons.py`)
功能：

- 批量人物特征与推理；当输入数据暂缺时进入等待心跳 -> 延迟 -> 重试（确保不退出）。
- 心跳：`heartbeats/batch_predict_persons.json` 包含 `round / samples`。
- 网络同样具备 requests→urllib 降级。

\n### 2.6 知识摄取管线 (`knowledge_ingest_pipeline.py`)
功能：

- 聚合文本资源主题 / 作者画像，生成知识摘要（结构化 JSON）。
- 统一由守护调度，心跳文件：`heartbeats/knowledge_ingest.json`（包含调度事件与间隔）。

\n### 2.7 元学习增强 (`meta_learning_enhancer.py`)
功能：

- 对原始深度学习循环结果进行二次加工：附加 `metric / model_version / quality_tag` 等占位符。
- 输出：`deep_learning_cycle_results_enriched.jsonl`。

\n### 2.8 心跳管理 (`heartbeat_manager.py`)
功能：

- 标准化心跳写入（时间戳、PID、扩展字段）到 `heartbeats/<name>.json`。
- 调用幂等，写入失败自动吞掉异常避免影响主流程。

\n### 2.9 健康检测脚本 (`check_autonomy.py`)
功能：

- 核查：状态文件、运行标记、心跳时效、关键结果文件是否存在与非空。
- 输出结构化 JSON + 退出码（0=pass,1=warn,2=fail）便于 CI / 报警整合。

## 3. 心跳与监控机制

| 任务 | 心跳文件 | 主要字段 | 超时阈值（秒） | 自愈策略 |
|------|----------|----------|---------------|----------|
| autonomous_run | heartbeats/autonomous_run.json | mode, loop_count, last_error, duration_seconds | 180 | 守护检测超时或进程消失 -> 重启 |
| deep_learning_cycle | heartbeats/deep_learning_cycle.json | round, time_end, records | 300 | 超时重启并清理失败计数 |
| yi_books_collect | heartbeats/yi_books_collect.json | books, top_authors | 7200 | 超时或进程退出 -> 重启采集 |
| batch_predict_persons | heartbeats/batch_predict_persons.json | round, samples | 300 | 任务退出或心跳冻结 -> 重启 |
| knowledge_ingest | heartbeats/knowledge_ingest.json | event, interval_sec | 默认 6h | 守护定时触发 |

监控循环间隔：约每 15 秒。重启退避：指数退避（首次立即，随后 2^fails 上限 300 秒）。

## 4. 自愈策略与鲁棒性设计

1. 进程存活与心跳双保险：仅心跳更新不足或进程缺失才触发重启。
2. 指数退避：避免频繁故障场景导致资源震荡。
3. Git 锁文件自动清理：无活动 git 进程时安全删除 `index.lock`。
4. 孤立 PID 文件清理：检测到 PID 不存活时移除旧 pid 文件。
5. 目录确保：`logs / reports / heartbeats` 启动前与巡检周期自动创建。
6. 网络降级：requests 不可用或失败时降级到 urllib，减少依赖阻塞。
7. 错误日志隔离：各任务独立日志文件，避免串扰；严重异常不会直接杀死主循环（吞并写入心跳字段）。

## 5. 数据与输出产物

| 文件 | 类型 | 作用 |
|------|------|------|
| deep_learning_cycle_results.jsonl | 增量JSONL | 原始元学习 / 深度循环输出（轮次 + 时长 + metrics） |
| deep_learning_cycle_results_enriched.jsonl | 增量JSONL | 增强后追加质量标记/版本号 |
| person_predict_results.jsonl | 增量JSONL | 人物批量预测结果（若文件名不同请同步更新 check 脚本） |
| knowledge_ingest_summary.json | JSON | 知识摄取主题与作者画像汇总 |
| reports/ai_guard_status.json | JSON | 当前多任务运行状态与失败计数 |
| heartbeats/*.json | JSON | 各任务活性与核心进度指标 |
| logs/*.log | 文本 | 运行与错误日志（可用于外部采集） |

文件膨胀控制：深度学习结果自动滚动；其他文件建议由外部归档策略（如按日期拆分，未来可扩展）。

## 6. 快速启动与健康检测

### 6.1 一键启动
 
\n```bash
```bash
python3 start_autonomy.py
```
行为：执行基本自愈 -> 启动守护 -> 打印状态摘要。若已运行则只显示当前状态。

### 6.2 单独启动（不推荐）
 
\n```bash
```bash
nohup python3 ai_guard_supervisor.py &
```
守护会检测并启动缺失的核心任务。

### 6.3 健康检测（CI / 报警）
 
\n```bash
```bash
python3 check_autonomy.py
```
退出码含义：0 正常 / 1 警告（例如某心跳缺失暂时恢复中）/ 2 严重失败。

## 7. 环境变量调优（可选）

| 变量 | 默认 | 说明 |
|------|------|------|
| KNOWLEDGE_INGEST_INTERVAL_SEC | 21600 | 知识摄取间隔（秒） |
| AUTORL_MIN_INTERVAL_HOURS | 12 | AutoRL 最小触发间隔（小时） |
| VIS_MIN_INTERVAL_HOURS | 6 | 可视化生成最小间隔（小时） |
| SSQ_CYCLE_INTERVAL_SECONDS | 0 | 闭环评估循环间隔（0=连续） |
| SSQ_MAX_SECONDS_PER_ISSUE | 5 | 单期评估最大耗时（秒） |
| SSQ_MAX_ATTEMPTS_PER_ISSUE | 0 | 单期尝试上限（0或负数=不限） |

## 8. 扩展与下一步建议

短期增强：
\n- 重启频次告警：统计连续 X 分钟内重启次数，写入 `reports/alerts.json`。
- Web 轻量仪表盘：展示任务状态/心跳时间差/最近错误。
- 结果归档策略：按日期拆分与压缩，降低主仓库体积。
- 指标持久化：Prometheus exporter 或 pushgateway 适配。

中期演进：
\n- 自适应资源控制：依据 CPU/内存占用与心跳速率动态调节循环间隔。
- 模型版本管理：将 `model_version` 与 artifacts 关联（例如存储到 `models/` + checksum）。
- 自动数据质量评估：对增量结果进行统计检验并标记异常轮次。

## 9. 故障排查速览

| 症状 | 可能原因 | 排查路径 | 修复 |
|------|----------|----------|------|
| 任务频繁重启 | 环境依赖缺失 / 数据空 / 逻辑异常 | 对应日志 / fails计数 | 修复脚本逻辑或补齐依赖 |
| 心跳未更新 | 死锁 / 异常未捕获 / IO 失败 | heartbeats/对应任务.json 时间戳 | 杀死进程让守护重启；检查日志 |
| 结果文件无增长 | 数据源断流 / 写入异常 | tail -f 对应结果文件 | 修复数据源/权限 |
| `index.lock` 常驻 | 外部 git 操作异常中断 | ls .git/index.lock | 停止 git 进程后删除锁 |

## 10. 全自动化达成要点总结

1. 多任务统一守护 + 心跳与进程双监控。
2. 自愈与指数退避降低人工干预需求。
3. 增量 + 滚动输出防止数据丢失与体积膨胀失控。
4. 低频策略（AutoRL / 可视化 / 知识摄取）与主循环并行互不阻塞。
5. 健康检测标准化（脚本 + 退出码）便于外部编排与告警。
6. 组件职责分层清晰（采集 / 预测 / 训练 / 摄取 / 增强 / 守护）。

如需进一步扩展或接入外部监控/告警，请参考第 8 节建议进行迭代。

---
如发现文档与实际代码有偏差，优先参考源码与运行日志，或提交 issue 进行同步更新。

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

## 运行与管理（快速参考）

下面是仓库中可用的三种运行/管理方式，按从开发到生产的推荐顺序列出：

1) 开发 / 快速本地运行（脚本）

- 一键安全启动（避免重复启动并写 pid 到 `logs/`）：
  ```bash
  ./start_all.sh
  ```

- 更稳健的示例（会在启动时写 pid 并写入 `logs/`）：
  ```bash
  ./scripts/start_all_with_pid.sh
  ```

- 记录当前运行进程到 `logs/`（只读、不会改动进程）：
  ```bash
  ./scripts/record_running_pids.sh
  cat logs/api.pid
  cat logs/report_frontend.pid
  ```

- 优雅停止基于 pid 文件的服务：
  ```bash
  ./scripts/stop_all_from_pids.sh
  ```

日志位置（脚本模式）: `logs/api_server.log`, `logs/report_frontend.log`, 以及 pid 文件在 `logs/*.pid`。

2) 使用 supervisord（长期运行 / 测试环境）

- 我们在仓库中提供了 supervisord 配置：`supervisord_manage_api_frontend.conf`，并已将其包含到主 `supervisord.conf`。
- 启动/控制（示例，开发环境已在工作区演示过）：
  ```bash
  supervisord -c /workspaces/-AI-2.0/supervisord_manage_api_frontend.conf
  supervisorctl -c /workspaces/-AI-2.0/supervisord_manage_api_frontend.conf status
  supervisorctl -c /workspaces/-AI-2.0/supervisord_manage_api_frontend.conf restart all
  ```

- supervisord 日志与程序日志：`logs/supervisor/*.out.log`, `logs/supervisor/*.err.log`。

3) systemd（生产部署推荐）

- 仓库包含 systemd 单元示例：`systemd/xuanji_api.service` 与 `systemd/report_frontend.service`，安装说明见 `INSTALL_SYSTEMD.md`。
- 在目标主机上复制 unit 文件到 `/etc/systemd/system/`，然后执行：
  ```bash
  sudo systemctl daemon-reload
  sudo systemctl enable --now xuanji_api.service report_frontend.service
  sudo systemctl status xuanji_api.service
  sudo journalctl -u xuanji_api.service -f
  ```

常见注意事项：
- 若使用虚拟环境（`.venv`），请在 supervisord 或 systemd 的 `ExecStart`/`command` 中使用虚拟环境下的 `python`/`uvicorn` 路径，或在 unit 中使用 `Environment=` 指定必要的变量。
- 确保 `logs/` 目录对运行服务的用户可写。
- 若服务由 supervisord 或 systemd 管理，则不需要再用脚本重复启动。

如果你需要我把 `ExecStart` 指向特定的虚拟环境或进一步生成更完整的 systemd unit（如 `User=`、`EnvironmentFile=`、资源限制、依赖单元），告诉我虚拟环境路径或你的偏好，我可以替你修改并提交。
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
