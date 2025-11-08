#!/usr/bin/env bash
# 简单 wrapper：打印 ai_meta_system 状态（JSON）并返回 code
python -m ai_meta_system.status
exit $?
