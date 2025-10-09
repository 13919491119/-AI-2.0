# 自动化网站与APP集成文档

## 概述

本文档描述了玄机AI系统的自动化静态网站部署和APP（微信）集成功能。所有功能均支持自主完成，无需人工干预。

## 功能特性

### 1. 微信服务端集成 (wechat_server.py)

自动集成微信公众号/小程序，提供运营报告接口。

**端口**: 8088

**功能**:
- 微信服务器验证接口 (GET /wechat)
- 微信消息处理 (POST /wechat)
- JSON格式报告接口 (GET /report)
- 健康检查 (GET /health)

**配置**:
```bash
export WECHAT_TOKEN="your_token_here"
```

### 2. 静态报告服务器 (static_report_server.py)

自动展示所有历史运营报告的Web界面。

**端口**: 8089

**功能**:
- 报告列表展示 (GET /)
- 单个报告查看 (GET /report/{report_name})
- 自动Markdown渲染
- 响应式设计

### 3. 系统自检 (system_check.py)

全面的系统状态检查工具。

**检查项目**:
- ✅ API服务状态 (8000端口)
- ✅ 报告前端状态 (8080端口)
- ✅ 微信服务状态 (8088端口)
- ✅ 静态服务器状态 (8089端口)
- ✅ 进程运行状态

**使用方法**:
```bash
python3 system_check.py
```

### 4. 运营报告生成器 (generate_operation_report.py)

自动生成Markdown格式的周期运营报告。

**输出内容**:
- 系统状态概览
- 核心指标统计
- 学习成果总结
- 量子纠缠增强说明
- 服务访问地址
- 部署方式说明

**使用方法**:
```bash
python3 generate_operation_report.py
```

## 部署流程

### 方式一：一键启动所有服务

```bash
bash start_all.sh
```

此脚本将自动启动：
1. FastAPI主服务 (8000端口)
2. 报告前端服务 (8080端口)
3. 微信集成服务 (8088端口)
4. 静态报告服务器 (8089端口)
5. 执行系统自检

### 方式二：单独部署微信服务

```bash
bash setup_wechat_integration.sh
```

此脚本将：
1. 检查并安装依赖
2. 配置环境变量
3. 启动微信服务器
4. 验证服务状态

### 方式三：手动启动各服务

```bash
# 启动微信服务
python3 wechat_server.py

# 启动静态报告服务器
python3 static_report_server.py

# 生成运营报告
python3 generate_operation_report.py

# 执行系统自检
python3 system_check.py
```

## 服务访问地址

| 服务名称 | 端口 | 访问地址 | 说明 |
|---------|------|---------|------|
| API服务 | 8000 | http://127.0.0.1:8000/status | 核心API接口 |
| 报告前端 | 8080 | http://127.0.0.1:8080/report | Web报告页面 |
| 微信集成 | 8088 | http://127.0.0.1:8088/report | 微信接口 |
| 静态报告中心 | 8089 | http://127.0.0.1:8089 | 报告列表 |

## 日志文件

所有服务的日志文件位于项目根目录：

- `api_server.log` - API服务日志
- `report_frontend.log` - 报告前端日志
- `wechat_server.log` - 微信服务日志
- `static_report_server.log` - 静态服务器日志

## 测试

运行集成测试：

```bash
python3 -m pytest tests/test_integration.py -v
```

或使用unittest：

```bash
python3 -m unittest tests/test_integration.py
```

## 故障排查

### 问题：服务启动失败

**解决方案**:
1. 检查端口是否被占用
2. 查看相应的日志文件
3. 运行系统自检：`python3 system_check.py`

### 问题：微信验证失败

**解决方案**:
1. 确认WECHAT_TOKEN配置正确
2. 检查微信服务器是否正确配置
3. 查看wechat_server.log日志

### 问题：报告生成失败

**解决方案**:
1. 确保API服务正在运行
2. 检查网络连接
3. 查看错误日志

## API集成示例

### Python集成

```python
import requests

# 获取微信报告
response = requests.get("http://127.0.0.1:8088/report")
report = response.json()
print(report)

# 健康检查
health = requests.get("http://127.0.0.1:8088/health")
print(health.json())
```

### JavaScript集成

```javascript
// 获取报告
fetch('http://127.0.0.1:8088/report')
  .then(res => res.json())
  .then(data => console.log(data));

// 健康检查
fetch('http://127.0.0.1:8089/health')
  .then(res => res.json())
  .then(data => console.log(data));
```

### cURL集成

```bash
# 微信报告
curl http://127.0.0.1:8088/report

# 静态服务器健康检查
curl http://127.0.0.1:8089/health

# 生成新报告
python3 generate_operation_report.py
```

## 公网部署建议

### 使用NGINX反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
    }

    location /report/ {
        proxy_pass http://127.0.0.1:8080/;
    }

    location /wechat/ {
        proxy_pass http://127.0.0.1:8088/;
    }

    location / {
        proxy_pass http://127.0.0.1:8089/;
    }
}
```

### 使用NGROK (快速测试)

```bash
# 微信服务
ngrok http 8088

# 静态网站
ngrok http 8089
```

## 自动化运维

### 定时任务示例 (crontab)

```bash
# 每天凌晨2点生成运营报告
0 2 * * * cd /path/to/project && python3 generate_operation_report.py

# 每小时执行系统自检
0 * * * * cd /path/to/project && python3 system_check.py
```

### Supervisor配置示例

```ini
[program:wechat_server]
command=python3 /path/to/project/wechat_server.py
autostart=true
autorestart=true
stderr_logfile=/var/log/wechat_server.err.log
stdout_logfile=/var/log/wechat_server.out.log

[program:static_server]
command=python3 /path/to/project/static_report_server.py
autostart=true
autorestart=true
stderr_logfile=/var/log/static_server.err.log
stdout_logfile=/var/log/static_server.out.log
```

## 安全建议

1. **环境变量**: 使用环境变量管理敏感配置
2. **访问控制**: 在生产环境中添加认证机制
3. **HTTPS**: 使用SSL/TLS加密通信
4. **防火墙**: 配置适当的防火墙规则
5. **日志审计**: 定期检查日志文件

## 更新日志

### v1.0.0 (2025-10-09)
- ✅ 初始版本发布
- ✅ 微信服务端集成
- ✅ 静态报告服务器
- ✅ 系统自检功能
- ✅ 运营报告生成器
- ✅ 一键部署脚本

---

*Celestial Nexus © 2025*
