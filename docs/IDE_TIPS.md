# VS Code/Pylance 使用提示（容器内开发）

如果在编辑器里看到 "无法解析导入 fastapi.responses" 或类似提示，多数是解释器不在容器内环境。

建议：

1. 选择正确的 Python 解释器
   - 命令面板：Python: Select Interpreter
   - 选择以 "/usr/local/bin/python" 或容器内 venv 为前缀的解释器。

2. 确认依赖安装位置
   - 在容器终端执行 `pip show fastapi`/`pip show pydantic` 确认版本。
   - 若缺失，安装 `pip install -r requirements.txt`。

3. 触发索引刷新
   - 重启 Pylance 服务：命令面板 -> Developer: Reload Window。

4. 避免多重工作区干扰
   - 确保当前工作区只打开本项目，或为每个项目单独窗口。

5. 补充设置（可选）
   - settings.json 中指定 Python 默认解释器路径，或开启 `python.analysis.extraPaths` 指向源码目录。

这些提示不影响运行时（Gunicorn/Uvicorn）服务，只是编辑器内的智能提示与诊断配置问题。