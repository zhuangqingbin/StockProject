import os
import sys


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load_stock_basic_fetch():
    try:
        from apps.stock_data_platform.DataFetch import StockBasicFetch
    except ModuleNotFoundError:
        if REPO_ROOT not in sys.path:
            sys.path.insert(0, REPO_ROOT)
        from apps.stock_data_platform.DataFetch import StockBasicFetch
    return StockBasicFetch


def main():
    stock_basic_fetch = _load_stock_basic_fetch()
    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        print("TUSHARE_TOKEN is not set. Export it first to run fetch demos.")
        return

    fetcher = stock_basic_fetch()
    data = fetcher.fetch(ts_code="000001.SZ")
    fetcher.summary_data()
    print(data.head())


if __name__ == "__main__":
    main()
