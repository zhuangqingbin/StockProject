import csv
import io

from sqlalchemy import and_, func, literal, not_, or_, select

from apps.stock_bi_v1.backend.models.api_models import FilterMeta, ScreenerRequest
from apps.stock_bi_v1.backend.infrastructure.database import SessionLocal
from apps.stock_bi_v1.backend.models.db_models import DailyBasic, DailyKline, Moneyflow, StockBasic


FIELD_MAP = {
    "pct_chg": DailyKline.pct_chg,
    "close": DailyKline.close,
    "amount": DailyKline.amount,
    "vol": DailyKline.vol,
    "turnover_rate": DailyBasic.turnover_rate,
    "pe_ttm": DailyBasic.pe_ttm,
    "pb": DailyBasic.pb,
    "ps_ttm": DailyBasic.ps_ttm,
    "total_mv": DailyBasic.total_mv,
    "circ_mv": DailyBasic.circ_mv,
    "total_share": DailyBasic.total_share,
    "float_share": DailyBasic.float_share,
    "net_mf_amount": Moneyflow.net_mf_amount,
    "net_elg_amount": Moneyflow.buy_elg_amount - Moneyflow.sell_elg_amount,
    "net_lg_amount": Moneyflow.buy_lg_amount - Moneyflow.sell_lg_amount,
    "industry": StockBasic.industry,
    "market": StockBasic.market,
}

FILTER_META = [
    FilterMeta(field="pct_chg", label="涨跌幅", category="行情", operators=["gt", "lt", "between", "eq"]),
    FilterMeta(field="close", label="现价", category="行情", operators=["gt", "lt", "between", "eq"]),
    FilterMeta(field="amount", label="成交额", category="行情", operators=["gt", "lt", "between"]),
    FilterMeta(field="vol", label="成交量", category="行情", operators=["gt", "lt", "between"]),
    FilterMeta(field="turnover_rate", label="换手率", category="行情", operators=["gt", "lt", "between"]),
    FilterMeta(field="pe_ttm", label="PE(TTM)", category="估值", operators=["gt", "lt", "between"]),
    FilterMeta(field="pb", label="PB", category="估值", operators=["gt", "lt", "between"]),
    FilterMeta(field="ps_ttm", label="PS(TTM)", category="估值", operators=["gt", "lt", "between"]),
    FilterMeta(field="total_mv", label="总市值", category="估值", operators=["gt", "lt", "between"]),
    FilterMeta(field="circ_mv", label="流通市值", category="估值", operators=["gt", "lt", "between"]),
    FilterMeta(field="total_share", label="总股本", category="估值", operators=["gt", "lt", "between"]),
    FilterMeta(field="float_share", label="流通股本", category="估值", operators=["gt", "lt", "between"]),
    FilterMeta(field="net_mf_amount", label="主力净流入", category="资金", operators=["gt", "lt", "between"]),
    FilterMeta(field="net_elg_amount", label="特大单净流入", category="资金", operators=["gt", "lt", "between"]),
    FilterMeta(field="net_lg_amount", label="大单净流入", category="资金", operators=["gt", "lt", "between"]),
    FilterMeta(field="industry", label="行业", category="分类", operators=["eq", "contains"]),
    FilterMeta(field="market", label="市场", category="分类", operators=["eq"]),
]


def get_filters():
    return [item.model_dump() for item in FILTER_META]


def _latest_trade_date(session) -> str:
    return session.scalar(select(func.max(DailyKline.trade_date))) or ""


def _build_conditions(request: ScreenerRequest, trade_date: str):
    filters = [DailyKline.trade_date == trade_date, not_(or_(StockBasic.name.like("ST%"), StockBasic.name.like("*ST%")))]

    for condition in request.conditions:
        if condition.field == "is_st":
            filters = [DailyKline.trade_date == trade_date]
            if condition.value:
                filters.append(or_(StockBasic.name.like("ST%"), StockBasic.name.like("*ST%")))
            else:
                filters.append(not_(or_(StockBasic.name.like("ST%"), StockBasic.name.like("*ST%"))))
            continue

        column = FIELD_MAP.get(condition.field)
        if column is None:
            continue

        if condition.operator == "gt":
            filters.append(column > condition.value)
        elif condition.operator == "lt":
            filters.append(column < condition.value)
        elif condition.operator == "between" and isinstance(condition.value, list) and len(condition.value) == 2:
            filters.append(column.between(condition.value[0], condition.value[1]))
        elif condition.operator == "contains":
            filters.append(column.like(f"%{condition.value}%"))
        else:
            filters.append(column == condition.value)

    return filters


def _build_base_query(request: ScreenerRequest, trade_date: str):
    filters = _build_conditions(request, trade_date)
    sort_column = FIELD_MAP.get(request.sort_by, DailyKline.pct_chg)
    order_clause = sort_column.asc() if request.order == "asc" else sort_column.desc()

    query = (
        select(
            DailyKline.ts_code,
            StockBasic.name,
            StockBasic.industry,
            StockBasic.market,
            DailyKline.close,
            DailyKline.pct_chg,
            DailyKline.amount,
            DailyBasic.turnover_rate,
            DailyBasic.pe_ttm,
            DailyBasic.pb,
            DailyBasic.ps_ttm,
            DailyBasic.total_mv,
            Moneyflow.net_mf_amount,
        )
        .join(StockBasic, StockBasic.ts_code == DailyKline.ts_code)
        .outerjoin(
            DailyBasic,
            and_(DailyBasic.ts_code == DailyKline.ts_code, DailyBasic.trade_date == DailyKline.trade_date),
        )
        .outerjoin(
            Moneyflow,
            and_(Moneyflow.ts_code == DailyKline.ts_code, Moneyflow.trade_date == DailyKline.trade_date),
        )
        .where(*filters)
        .order_by(order_clause, DailyKline.ts_code.asc())
    )
    return query


def query(request: ScreenerRequest):
    with SessionLocal() as session:
        trade_date = _latest_trade_date(session)
        base_query = _build_base_query(request, trade_date)
        total_query = select(func.count()).select_from(base_query.subquery())
        total = session.scalar(total_query) or 0
        paged_query = base_query.offset(request.page * request.size).limit(request.size)
        rows = session.execute(paged_query).all()

    return {
        "total": int(total),
        "page": request.page,
        "size": request.size,
        "items": [
            {
                "ts_code": row.ts_code,
                "name": row.name or row.ts_code,
                "industry": row.industry or "",
                "market": row.market or "",
                "close": float(row.close or 0),
                "pct_chg": float(row.pct_chg or 0),
                "amount": float(row.amount or 0),
                "turnover_rate": float(row.turnover_rate or 0),
                "pe_ttm": float(row.pe_ttm or 0),
                "pb": float(row.pb or 0),
                "ps_ttm": float(row.ps_ttm or 0),
                "total_mv": float(row.total_mv or 0),
                "net_mf_amount": float(row.net_mf_amount or 0),
            }
            for row in rows
        ],
    }


def export_csv(request: ScreenerRequest) -> str:
    export_request = request.model_copy(update={"page": 0, "size": 5000})
    payload = query(export_request)
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=["ts_code", "name", "industry", "market", "close", "pct_chg", "amount", "turnover_rate", "pe_ttm", "pb", "ps_ttm", "total_mv", "net_mf_amount"],
    )
    writer.writeheader()
    writer.writerows(payload["items"])
    return buffer.getvalue()
