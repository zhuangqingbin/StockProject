import uvicorn

from apps.stock_bi_v1.backend.infrastructure.settings import API_HOST, API_PORT


def main():
    uvicorn.run("apps.stock_bi_v1.backend.main:app", host=API_HOST, port=API_PORT, reload=False)


if __name__ == "__main__":
    main()
