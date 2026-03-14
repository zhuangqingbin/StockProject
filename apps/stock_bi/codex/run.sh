#!/bin/bash

# Stock BI 启动脚本
# 使用方法: ./run.sh

cd "$(dirname "$0")"

echo "=========================================="
echo "     Stock BI - A股数据可视化平台"
echo "=========================================="

# 检查依赖
echo "检查依赖..."
pip3 install -q -r requirements.txt

# 启动服务
echo "启动服务..."
echo ""
echo "访问地址:"
echo "  前端: http://localhost:8000/"
echo "  API:  http://localhost:8000/api/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=========================================="

python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
