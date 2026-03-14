import os

import tushare as ts


def main():
    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        print("TUSHARE_TOKEN is not set. Export it first to run this demo.")
        return

    pro = ts.pro_api(token)
    df = pro.tmt_twincome(item="8")
    print(df.head())


if __name__ == "__main__":
    main()
