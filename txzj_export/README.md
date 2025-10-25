# 天枢智鉴AI 3.0 系统

## 项目简介
天枢智鉴AI 3.0 是具备自主学习、自主优化、自主升级能力的多体系智能推理系统，支持六壬、六爻、八字、奇门、紫微等融合。

## 主要特性
- 自主学习和优化
- 自主升级能力
- 多体系融合
- 实时监控与健康评估
- 模块化设计，易于扩展
- 完善的API接口（FastAPI）

## 目录结构
```
celestial_nexus/
	├── __init__.py
	├── ai_core.py         # 主AI核心类
	├── config.py          # 配置项
	├── demo.py            # 演示脚本
	└── api.py             # FastAPI接口
requirements.txt
README.md
```

## 快速开始
### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行演示
```bash
python3 demo_run.py
```

### 3. 启动API服务
```bash
uvicorn celestial_nexus.api:app --reload
```

访问 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) 查看Swagger API文档。

## 单元测试
```bash
pytest
```

## 状态导出/导入
- 导出：GET `/export_state`
- 导入：POST `/import_state`，body为导出的json

## 扩展与部署
- 支持Docker部署，详见后续文档。
# -AI
传统文化预测
