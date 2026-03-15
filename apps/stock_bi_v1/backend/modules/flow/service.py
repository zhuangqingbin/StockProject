from apps.stock_bi_v1.backend.modules.flow import repository


def get_north_money(days: int = 30):
    rows = repository.get_north_money(days)
    rows.reverse()
    return [
        {
            "trade_date": row.trade_date,
            "hgt": float(row.hgt or 0),
            "sgt": float(row.sgt or 0),
            "north_money": float(row.north_money or 0),
            "south_money": float(row.south_money or 0),
        }
        for row in rows
    ]


def get_stock_flow(ts_code: str, days: int = 30):
    rows = repository.get_stock_flow(ts_code, days)
    rows.reverse()
    return [
        {
            "trade_date": row.trade_date,
            "buy_elg_amount": float(row.buy_elg_amount or 0),
            "sell_elg_amount": float(row.sell_elg_amount or 0),
            "buy_lg_amount": float(row.buy_lg_amount or 0),
            "sell_lg_amount": float(row.sell_lg_amount or 0),
            "buy_md_amount": float(row.buy_md_amount or 0),
            "sell_md_amount": float(row.sell_md_amount or 0),
            "buy_sm_amount": float(row.buy_sm_amount or 0),
            "sell_sm_amount": float(row.sell_sm_amount or 0),
            "net_mf_amount": float(row.net_mf_amount or 0),
        }
        for row in rows
    ]


def get_stock_flow_detail(ts_code: str, trade_date: str):
    row = repository.get_stock_flow_detail(ts_code, trade_date)
    if row is None:
        return {"trade_date": trade_date, "ts_code": ts_code}
    return {
        "trade_date": row.trade_date,
        "ts_code": row.ts_code,
        "buy_elg_amount": float(row.buy_elg_amount or 0),
        "sell_elg_amount": float(row.sell_elg_amount or 0),
        "buy_lg_amount": float(row.buy_lg_amount or 0),
        "sell_lg_amount": float(row.sell_lg_amount or 0),
        "buy_md_amount": float(row.buy_md_amount or 0),
        "sell_md_amount": float(row.sell_md_amount or 0),
        "buy_sm_amount": float(row.buy_sm_amount or 0),
        "sell_sm_amount": float(row.sell_sm_amount or 0),
        "net_mf_amount": float(row.net_mf_amount or 0),
    }
