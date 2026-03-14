"""
LLM 服务 - 处理自然语言到 SQL/可视化配置的转换
"""
import json
import re
from typing import Optional, Dict, Any, List
import httpx

from ..config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL


# 系统提示词
SYSTEM_PROMPT = """你是一个专业的 A 股市场数据分析助手。你需要根据用户的自然语言查询，生成相应的分析结果。

## 可用数据
- daily_kline 表：日K线数据
  - ts_code: 股票代码（如 000001.SZ, 600000.SH）
  - trade_date: 交易日期
  - open, high, low, close: 开高低收
  - pct_chg: 涨跌幅（%）
  - vol: 成交量（手）
  - amount: 成交额（千元）

## 股票代码规则
- 60xxxx.SH, 68xxxx.SH: 上海（68为科创板）
- 00xxxx.SZ, 30xxxx.SZ: 深圳（30为创业板）
- 4xxxxx.BJ, 8xxxxx.BJ: 北交所

## 响应格式
你必须返回一个 JSON 对象，包含以下字段：
{
    "reply": "给用户的自然语言回复，简洁专业",
    "action": "需要执行的操作类型",
    "params": {}  // 操作参数
}

## 支持的 action 类型

1. "overview" - 市场概览
   params: {"trade_date": "YYYY-MM-DD" 或 null}

2. "ranking" - 排行榜
   params: {
       "sort_by": "pct_chg" | "amount" | "vol",
       "order": "desc" | "asc",
       "limit": 10-50,
       "market": "科创板" | "创业板" | "沪市主板" | "深市主板" | "北交所" | null
   }

3. "sector_stats" - 板块统计
   params: {}

4. "distribution" - 涨跌分布
   params: {}

5. "kline" - K线图
   params: {"ts_code": "股票代码", "days": 60}

6. "amount_trend" - 成交额趋势
   params: {"days": 30}

7. "limit_trend" - 涨停趋势
   params: {"days": 30}

8. "custom_query" - 自定义 SQL 查询（复杂查询时使用）
   params: {"sql": "SELECT ...", "chart_type": "table" | "bar" | "line" | "pie"}

## 示例

用户: "今天市场怎么样"
响应:
{
    "reply": "为您获取今日市场概览数据",
    "action": "overview",
    "params": {"trade_date": null}
}

用户: "显示涨幅前10的股票"
响应:
{
    "reply": "为您展示今日涨幅榜前10名",
    "action": "ranking",
    "params": {"sort_by": "pct_chg", "order": "desc", "limit": 10}
}

用户: "科创板今天表现怎么样"
响应:
{
    "reply": "为您分析科创板今日表现",
    "action": "ranking",
    "params": {"sort_by": "pct_chg", "order": "desc", "limit": 20, "market": "科创板"}
}

请始终返回有效的 JSON，不要包含任何其他文字。"""


class LLMService:
    """LLM 服务类"""
    
    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.base_url = OPENAI_BASE_URL
        self.model = OPENAI_MODEL
    
    async def parse_query(self, user_message: str, context: Optional[List[dict]] = None) -> Dict[str, Any]:
        """
        解析用户查询，返回操作指令
        
        Args:
            user_message: 用户输入的自然语言
            context: 对话上下文
        
        Returns:
            包含 reply, action, params 的字典
        """
        # 如果没有配置 API Key，使用规则匹配
        if not self.api_key:
            return self._rule_based_parse(user_message)
        
        try:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
            
            # 添加上下文
            if context:
                for msg in context[-5:]:  # 只保留最近5条
                    messages.append(msg)
            
            messages.append({"role": "user", "content": user_message})
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.3,
                        "max_tokens": 1000
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    # 解析 JSON
                    return self._parse_json_response(content)
                else:
                    # API 调用失败，回退到规则匹配
                    return self._rule_based_parse(user_message)
                    
        except Exception as e:
            print(f"LLM API error: {e}")
            return self._rule_based_parse(user_message)
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """解析 LLM 返回的 JSON"""
        try:
            # 尝试直接解析
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试提取 JSON 块
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
        
        # 解析失败，返回默认
        return {
            "reply": content if content else "抱歉，我没有理解您的问题",
            "action": "overview",
            "params": {}
        }
    
    def _rule_based_parse(self, message: str) -> Dict[str, Any]:
        """基于规则的意图识别（无需 LLM）"""
        message = message.lower().strip()
        
        # 市场概览
        if any(kw in message for kw in ["市场", "大盘", "概览", "怎么样", "今天"]):
            if "涨" in message and ("榜" in message or "前" in message or "top" in message):
                pass  # 跳过，让下面的排行榜规则处理
            else:
                return {
                    "reply": "为您获取市场概览数据",
                    "action": "overview",
                    "params": {}
                }
        
        # 排行榜
        if any(kw in message for kw in ["涨幅", "跌幅", "榜", "排行", "前", "top"]):
            # 判断排序方向
            if "跌" in message:
                order = "asc"
                sort_by = "pct_chg"
                reply = "为您展示跌幅榜"
            elif "成交额" in message or "金额" in message:
                order = "desc"
                sort_by = "amount"
                reply = "为您展示成交额排行榜"
            elif "成交量" in message or "量" in message:
                order = "desc"
                sort_by = "vol"
                reply = "为您展示成交量排行榜"
            else:
                order = "desc"
                sort_by = "pct_chg"
                reply = "为您展示涨幅榜"
            
            # 提取数量
            limit = 20
            num_match = re.search(r'(\d+)', message)
            if num_match:
                limit = min(int(num_match.group(1)), 100)
            
            # 提取市场
            market = None
            if "科创" in message:
                market = "科创板"
            elif "创业" in message:
                market = "创业板"
            elif "北交" in message:
                market = "北交所"
            elif "主板" in message:
                if "沪" in message or "上海" in message:
                    market = "沪市主板"
                elif "深" in message or "深圳" in message:
                    market = "深市主板"
            
            return {
                "reply": reply,
                "action": "ranking",
                "params": {
                    "sort_by": sort_by,
                    "order": order,
                    "limit": limit,
                    "market": market
                }
            }
        
        # 板块分析
        if any(kw in message for kw in ["板块", "行业", "对比"]):
            return {
                "reply": "为您分析各板块表现",
                "action": "sector_stats",
                "params": {}
            }
        
        # 涨跌分布
        if any(kw in message for kw in ["分布", "直方图", "histogram"]):
            return {
                "reply": "为您展示涨跌幅分布",
                "action": "distribution",
                "params": {}
            }
        
        # K线
        if any(kw in message for kw in ["k线", "kline", "走势"]):
            # 尝试提取股票代码
            code_match = re.search(r'(\d{6})', message)
            if code_match:
                code = code_match.group(1)
                # 判断交易所后缀
                if code.startswith(('60', '68')):
                    ts_code = f"{code}.SH"
                elif code.startswith(('00', '30')):
                    ts_code = f"{code}.SZ"
                else:
                    ts_code = f"{code}.BJ"
                
                return {
                    "reply": f"为您展示 {ts_code} 的K线走势",
                    "action": "kline",
                    "params": {"ts_code": ts_code, "days": 60}
                }
        
        # 成交额趋势
        if "成交额" in message and ("趋势" in message or "变化" in message or "走势" in message):
            return {
                "reply": "为您展示成交额趋势",
                "action": "amount_trend",
                "params": {"days": 30}
            }
        
        # 涨停趋势
        if "涨停" in message and ("趋势" in message or "变化" in message or "走势" in message or "家数" in message):
            return {
                "reply": "为您展示涨停家数趋势",
                "action": "limit_trend",
                "params": {"days": 30}
            }
        
        # 热力图
        if "热力图" in message or "heatmap" in message:
            return {
                "reply": "为您生成板块热力图",
                "action": "sector_stats",
                "params": {"chart_type": "heatmap"}
            }
        
        # 默认返回概览
        return {
            "reply": "为您获取市场概览数据。您可以尝试以下指令：\n- 显示涨幅前10\n- 各板块表现\n- 涨跌分布\n- 查看 600000 K线",
            "action": "overview",
            "params": {}
        }


# 单例
llm_service = LLMService()
