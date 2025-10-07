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
