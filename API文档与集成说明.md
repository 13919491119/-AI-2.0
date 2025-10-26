# 玄机AI2.0 FastAPI OpenAPI 文档说明

- 访问 http://localhost:8000/docs 可获得自动生成的 Swagger UI 文档。
- 主要接口：

## POST /run_xuanji_ai
- 参数：
  - input: str  # 你的自然语言指令，如“学习成果”、“双色球预测”、“双色球复盘: 01 02 03 04 05 06|07”
- 返回：
  - result: str  # AI2.0 推理/分析结果

### 示例：
```
curl -X POST http://localhost:8000/run_xuanji_ai -H "Content-Type: application/json" -d '{"input": "双色球预测"}'
```

## GET /
- 健康检查，返回 {"msg": "XuanjiAI2.0 API is running."}

---

# 外部 Python 集成示例

```python
import requests
resp = requests.post("http://localhost:8000/run_xuanji_ai", json={"input": "双色球预测"})
print(resp.json()["result"])
```

# 其他语言/平台可直接用 HTTP POST 方式集成。

---

## GET /ssq/eval_multi
- 功能：评估“多候选（Top-N）”推荐场景在最近窗口内的效果提升。
- 参数：
  - window: int，最近评估窗口期数（默认 120）
  - n: int，每期生成候选数量，范围 1..50（默认 5）
  - diversify: bool，是否启用候选去相似（默认 true）
  - seed: int，可复现随机种子（默认 42）
- 返回字段：
  - avg_best_reds_hit: 窗口内每期Top-N中最佳红球命中数的平均值
  - blue_hit_rate_any: 窗口内是否“任一候选命中蓝球”的比例
  - full_matches: 完全匹配（6红+1蓝）在窗口内出现的次数
  - topk_multi: best_red_hit_ge_2/3/4 计数
  - details_tail: 最近10期的详细记录

示例：
```
curl "http://localhost:8000/ssq/eval_multi?window=120&n=5&diversify=true&seed=42"
```
