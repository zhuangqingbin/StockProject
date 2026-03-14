from typing import Dict, List, Optional

from .llm_service import llm_service


async def resolve_intent(user_message: str, context: Optional[List[dict]] = None) -> Dict:
    return await llm_service.parse_query(user_message, context)
