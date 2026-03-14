import os
import sys


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from apps.stock_data_platform.DataFetch import StockBasicFetch


def main():
    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        print("TUSHARE_TOKEN is not set. Export it first to run fetch demos.")
        return

    fetcher = StockBasicFetch()
    data = fetcher.fetch(ts_code="000001.SZ")
    fetcher.summary_data()
    print(data.head())


if __name__ == "__main__":
    main()
