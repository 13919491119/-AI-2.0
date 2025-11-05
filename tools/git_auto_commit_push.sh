#!/bin/bash
# 自动化：每天定时将更改文件暂存、提交并同步到远程仓库
cd "$(dirname "$0")/.."
git add .
git commit -m "[自动任务] 每日自动暂存、提交和同步所有更改文件" || exit 0
git push || exit 0
