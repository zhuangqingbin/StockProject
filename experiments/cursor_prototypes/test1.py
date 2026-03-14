def fab(n: int) -> int:
    """
    Calculate the n-th Fibonacci number with F0=0, F1=1.

    :param n: Non-negative integer index.
    :return: F(n)
    """
    if not isinstance(n, int):
        raise TypeError("n must be an integer")
    if n < 0:
        raise ValueError("n must be non-negative")

    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


