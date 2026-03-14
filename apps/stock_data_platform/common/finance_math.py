import math


def get_pv(pmt, rate, n):
    q = 1 / (1 + rate)
    return pmt * (1 - q**n) / (1 - q)


def get_pmt(pv, rate, n):
    q = 1 / (1 + rate)
    return pv * (1 - q) / (1 - q**n)


def get_rate(pv, pmt, n):
    low_rate, high_rate = 0.0, 10.0
    while low_rate < high_rate:
        mid_rate = (low_rate + high_rate) / 2
        if abs(get_pv(pmt, mid_rate, n) - pv) < 1e-5:
            return mid_rate
        if get_pv(pmt, mid_rate, n) > pv:
            low_rate = mid_rate
        else:
            high_rate = mid_rate
    return low_rate


def get_n(pv, pmt, rate):
    q = 1 / (1 + rate)
    return math.log(1 - pv / pmt * (1 - q), q)
