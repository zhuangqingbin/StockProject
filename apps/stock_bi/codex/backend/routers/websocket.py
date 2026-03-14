"""
WebSocket 实时数据推送
当数据库数据更新时，通知前端自动刷新
"""
import asyncio
import json
from datetime import datetime
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import text

from ..database import engine
from ..cache import cache

router = APIRouter(tags=["websocket"])

# 活跃的 WebSocket 连接
active_connections: Set[WebSocket] = set()

# 记录最后检查的交易日期
_last_trade_date: str = ""


class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"📡 WebSocket 连接: {len(self.active_connections)} 个活跃连接")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        print(f"📡 WebSocket 断开: {len(self.active_connections)} 个活跃连接")
    
    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        if not self.active_connections:
            return
        
        message_str = json.dumps(message, ensure_ascii=False)
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except Exception:
                disconnected.add(connection)
        
        # 清理断开的连接
        for conn in disconnected:
            self.active_connections.discard(conn)
    
    async def send_to(self, websocket: WebSocket, message: dict):
        """发送消息给指定连接"""
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception:
            self.disconnect(websocket)


manager = ConnectionManager()


def get_latest_trade_date() -> str:
    """获取最新交易日期"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT MAX(trade_date) FROM daily_kline")).scalar()
        if result:
            return str(result)[:8] if len(str(result)) >= 8 else str(result)
    return ""


async def check_data_update():
    """检查数据是否有更新"""
    global _last_trade_date
    
    current_date = get_latest_trade_date()
    
    if _last_trade_date and current_date != _last_trade_date:
        # 数据有更新，广播通知
        await manager.broadcast({
            "type": "data_updated",
            "trade_date": current_date,
            "previous_date": _last_trade_date,
            "timestamp": datetime.now().isoformat()
        })
        # 清除缓存
        cache.clear()
        print(f"🔔 数据更新: {_last_trade_date} → {current_date}")
    
    _last_trade_date = current_date
    return current_date


async def data_update_checker():
    """后台任务：定期检查数据更新"""
    global _last_trade_date
    _last_trade_date = get_latest_trade_date()
    
    while True:
        await asyncio.sleep(30)  # 每30秒检查一次
        try:
            await check_data_update()
        except Exception as e:
            print(f"⚠️ 检查数据更新失败: {e}")


@router.websocket("/ws/market")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 连接端点"""
    await manager.connect(websocket)
    
    try:
        # 发送初始状态
        current_date = get_latest_trade_date()
        await manager.send_to(websocket, {
            "type": "connected",
            "trade_date": current_date,
            "timestamp": datetime.now().isoformat()
        })
        
        # 保持连接，接收客户端消息
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 处理客户端命令
                if message.get("type") == "ping":
                    await manager.send_to(websocket, {"type": "pong"})
                elif message.get("type") == "get_status":
                    await manager.send_to(websocket, {
                        "type": "status",
                        "trade_date": get_latest_trade_date(),
                        "connections": len(manager.active_connections)
                    })
            except json.JSONDecodeError:
                pass
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"⚠️ WebSocket 错误: {e}")
        manager.disconnect(websocket)


async def notify_data_update(trade_date: str = None):
    """手动触发数据更新通知"""
    if trade_date is None:
        trade_date = get_latest_trade_date()
    
    await manager.broadcast({
        "type": "data_updated",
        "trade_date": trade_date,
        "timestamp": datetime.now().isoformat(),
        "manual": True
    })
    
    # 清除缓存
    cache.clear()
    
    return {"status": "notified", "connections": len(manager.active_connections)}
