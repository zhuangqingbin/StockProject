import os
import sys


def main() -> None:
    # Ensure we can import from the same directory
    sys.path.append(os.path.dirname(__file__))
    try:
        from test1 import fab  # type: ignore
    except Exception as import_error:  # pragma: no cover
        raise RuntimeError("Failed to import fab from test1.py") from import_error

    for n in (10, 100):
        value = fab(n)
        print(f"fab({n}) = {value}")


if __name__ == "__main__":
    main()


