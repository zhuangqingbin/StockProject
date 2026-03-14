#!/usr/bin/env python3
"""
Stock BI 启动脚本
"""
import os
import sys

# 添加仓库根目录到 path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, REPO_ROOT)

import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("  Stock BI - A股数据可视化平台")
    print("=" * 60)
    print()
    print("  Frontend: http://localhost:8000/")
    print("  API Docs: http://localhost:8000/api/docs")
    print()
    print("=" * 60)
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[os.path.dirname(os.path.abspath(__file__))]
    )
