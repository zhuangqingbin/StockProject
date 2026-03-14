from typing import Union


def code_add_suffix(ts_code: Union[str, int]) -> str:
    if isinstance(ts_code, int):
        code = str(ts_code)
    elif isinstance(ts_code, str):
        code = ts_code
    else:
        raise ValueError(f"ts_code({ts_code}) must be int or str.")

    if code.endswith((".SH", ".SZ", ".BJ")):
        return code
    if code.startswith(("60", "68")):
        return f"{code}.SH"
    if code.startswith(("00", "30")):
        return f"{code}.SZ"
    if code.startswith(("4", "8")):
        return f"{code}.BJ"
    raise ValueError(f"ts_code({ts_code}) must start with 60/68/00/30/4/8")
