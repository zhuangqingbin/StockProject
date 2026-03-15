"""
Stock BI 后端主入口
FastAPI 应用 - 优化版本 v2.1（支持实时更新）
"""
import asyncio
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .infrastructure.cache import cache
from .infrastructure.database import Base, engine
from .infrastructure.settings import API_HOST, API_PORT
from .routers import market, chat
from .routers.websocket import router as ws_router, data_update_checker, notify_data_update
from .precompute import ensure_summary_table, get_latest_trade_date, get_summary, precompute_and_save

# 创建 FastAPI 应用
app = FastAPI(
    title="Stock BI API",
    description="A股市场数据可视化 API - 优化版本",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(market.router)
app.include_router(chat.router)
app.include_router(ws_router)  # WebSocket 实时推送

# 静态文件目录
FRONTEND_DIST_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
FRONTEND_ASSETS_DIR = os.path.join(FRONTEND_DIST_DIR, "assets")

# 挂载静态文件
if os.path.exists(FRONTEND_ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=FRONTEND_ASSETS_DIR), name="assets")


@app.get("/")
async def root():
    """首页 - 返回前端页面"""
    index_path = os.path.join(FRONTEND_DIST_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Stock BI API", "docs": "/api/docs"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """应用启动事件 - 预热缓存 + 启动实时监控"""
    base_url = f"http://localhost:{API_PORT}"
    print("=" * 50)
    print("Stock BI Server Starting... v2.1")
    print(f"API Docs: {base_url}/api/docs")
    print(f"Frontend: {base_url}/")
    print(f"WebSocket: ws://localhost:{API_PORT}/ws/market")
    print("=" * 50)
    
    # 1. 确保预计算表存在
    try:
        ensure_summary_table()
    except Exception as e:
        print(f"⚠️ 创建预计算表失败: {e}")
    
    # 2. 预热最新交易日数据（检查数据完整性，必要时重新预计算）
    try:
        latest = get_latest_trade_date()
        if latest:
            print(f"🔄 检查最新交易日 {latest} 的数据...")
            
            # 先清空缓存，确保获取数据库最新数据
            cache.clear()
            summary = get_summary(latest)
            
            # 检查 industry_ranking 是否有 avg5_pct_chg 字段（Treemap 所需）
            industry_ranking = summary.get('industry_ranking', [])
            needs_recompute = False
            
            if industry_ranking:
                first_item = industry_ranking[0]
                if 'avg5_pct_chg' not in first_item:
                    needs_recompute = True
                    print("⚠️ 检测到旧数据结构（缺少avg5_pct_chg），需要重新预计算...")
            
            if needs_recompute:
                print(f"🔄 重新预计算 {latest} 的数据...")
                cache.clear()
                summary = precompute_and_save(latest)
                print(f"✅ 重新预计算完成")
            
            print(f"✅ 数据就绪: {summary.get('total_stocks', 0)} 只股票")
    except Exception as e:
        print(f"⚠️ 预热缓存失败: {e}")
    
    # 3. 启动数据更新监控任务
    asyncio.create_task(data_update_checker())
    print("📡 数据更新监控已启动 (每30秒检查一次)")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    print("Stock BI Server Shutting down...")


# 用于直接运行
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
