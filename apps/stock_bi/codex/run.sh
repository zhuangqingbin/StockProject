#!/bin/bash

# Stock BI 启动脚本
# 使用方法: ./run.sh

set -euo pipefail

cd "$(dirname "$0")"

echo "=========================================="
echo "     Stock BI - A股数据可视化平台"
echo "=========================================="

# 启动服务
echo "启动服务..."
echo ""
echo "访问地址:"
echo "  前端: http://localhost:8000/"
echo "  API:  http://localhost:8000/api/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=========================================="

exec python3 run.py
