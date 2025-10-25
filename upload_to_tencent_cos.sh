#!/bin/bash
# 腾讯云COS自动上传脚本
# 使用前请先安装coscmd并完成coscmd config配置
# 上传大文件时建议使用分片上传，coscmd会自动处理

# 本地文件路径
LOCAL_FILE="ai2.0_source.zip"
# COS目标路径（可自定义子目录）
COS_PATH="/backup/ai2.0_source.zip"

# 检查coscmd是否安装
if ! command -v coscmd &> /dev/null; then
    echo "未检测到coscmd，请先运行: pip install coscmd"
    exit 1
fi

# 上传文件
coscmd upload "$LOCAL_FILE" "$COS_PATH"

if [ $? -eq 0 ]; then
    echo "上传成功：$LOCAL_FILE -> $COS_PATH"
else
    echo "上传失败，请检查coscmd配置和网络连接。"
    exit 2
fi
