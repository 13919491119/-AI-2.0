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
