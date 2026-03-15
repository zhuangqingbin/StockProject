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
echo "实际访问地址会在后端启动日志中输出"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=========================================="

exec python3 run.py
