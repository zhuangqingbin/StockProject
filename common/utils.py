from contextlib import contextmanager
import time

@contextmanager
def timer(name):
    start = time.time()
    yield
    print(f'[{name}] done in {time.time() - start:.2f} s')