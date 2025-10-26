# 快速入门指南

## 环境准备
- Python 3.10+
- pip install -r requirements.txt

## 启动API服务
```bash
uvicorn celestial_nexus.api:app --reload
```
访问 http://localhost:8000/docs 查看API文档。

## 演示脚本
```bash
python demo_run.py
```

## 自主模式
```bash
python autonomous_run.py
```

## 单元测试
```bash
python -m unittest tests/test_ai_core.py
python -m unittest tests/test_api.py
```

## Docker部署
```bash
docker build -t celestial-nexus-ai .
docker run -p 8000:8000 celestial-nexus-ai
```

## 双色球开奖：互联网抓取与入库（新增）

- 编排脚本：`tools/fetch_and_store_ssq.py`
	- 默认只在开奖窗口（北京时间 周二/周四/周日 21:30–22:30）执行
	- 强制运行（联调）：`SSQ_PROVIDER=file IMPORT_ANYTIME=1 python tools/fetch_and_store_ssq.py`
- 提供者：`SSQ_PROVIDER=auto|cwl|file|mock`（默认 `auto`）
	- file 联调用路径：`data/latest_ssq.json`
- 守护脚本：`tools/ssq_fetch_daemon.py`（开奖窗口内轮询，成功一次当日不再重复）
- API 触发：`POST /ssq/fetch_now`（参数 `force` 可选）
- 状态与评估：`static/ssq_import_status.json`、`reports/ssq_eval_*.json`/`reports/latest_eval.json`

注意：首次上线建议用 `tools/reconcile_ssq_from_tsv.py --apply` 或 `tools/sanitize_ssq_from_tsv.py` 以 TSV 为权威源修正 `ssq_history.csv`，再用 `python -c "from ssq_db import sync_from_csv; print(sync_from_csv('ssq_history.csv'))"` 将 CSV 全量同步回数据库。
