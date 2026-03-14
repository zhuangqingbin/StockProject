from shared.stock_core.db import create_mysql_engine


def get_engine():
    return create_mysql_engine()
