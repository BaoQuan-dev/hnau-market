#!/bin/bash
# Render 构建脚本
# 此脚本在每次部署时自动运行

set -e  # 遇到错误立即退出

echo "=========================================="
echo "河南农业大学闲置交易平台 - 开始构建"
echo "=========================================="

# 1. 安装 Python 依赖
echo "[1/3] 安装 Python 依赖..."
pip install -r requirements.txt

# 2. 验证依赖安装
echo "[2/3] 验证依赖..."
python -c "import flask; import gunicorn; print(f'Flask version: {flask.__version__}')"

# 3. 确保数据库目录存在
echo "[3/3] 准备环境..."
mkdir -p /tmp

echo "=========================================="
echo "构建完成！"
echo "=========================================="
