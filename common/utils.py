from contextlib import contextmanager
import time
import chinese_calendar
import datetime

@contextmanager
def timer(name):
    start = time.time()
    yield
    print(f'[{name}] done in {time.time() - start:.2f} s')

