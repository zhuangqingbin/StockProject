"""
简单的内存缓存，避免重复查询数据库
"""
import time
from typing import Any, Dict, Optional
from functools import wraps

class SimpleCache:
    """简单的内存缓存，带过期时间"""
    
    def __init__(self, default_ttl: int = 300):  # 默认 5 分钟
        self._cache: Dict[str, tuple] = {}  # {key: (value, expire_time)}
        self._default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key in self._cache:
            value, expire_time = self._cache[key]
            if time.time() < expire_time:
                return value
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存值"""
        if ttl is None:
            ttl = self._default_ttl
        self._cache[key] = (value, time.time() + ttl)
    
    def delete(self, key: str):
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self):
        """清空所有缓存"""
        self._cache.clear()


# 全局缓存实例
cache = SimpleCache(default_ttl=300)  # 5 分钟过期


def cached(ttl: int = 300):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存 key
            key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            # 尝试从缓存获取
            result = cache.get(key)
            if result is not None:
                return result
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            cache.set(key, result, ttl)
            
            return result
        return wrapper
    return decorator
