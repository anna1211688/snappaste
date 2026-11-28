# -*- coding: utf-8 -*-
"""开发者工具箱数据层: 时间戳/JSON/正则/Base64/单位换算纯函数。"""
from __future__ import annotations

import base64
import json
import re
from datetime import datetime


def ts_to_date(ts):
    return datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")


def date_to_ts(s):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return int(datetime.strptime(s.strip(), fmt).timestamp())
        except ValueError:
            continue
    raise ValueError("bad date format")


def json_pretty(s):
    return json.dumps(json.loads(s), ensure_ascii=False, indent=2)


def json_minify(s):
    return json.dumps(json.loads(s), ensure_ascii=False, separators=(",", ":"))


def regex_find(pattern, text, ignore_case=False):
    flags = re.IGNORECASE if ignore_case else 0
    return [m.group(0) for m in re.compile(pattern, flags).finditer(text)]


def b64_encode(s):
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def b64_decode(s):
    return base64.b64decode(s.encode("ascii")).decode("utf-8")


UNIT_FACTORS = {
    "length": {"mm": 1.0, "cm": 10.0, "m": 1000.0, "km": 1_000_000.0,
               "in": 25.4, "ft": 304.8, "mile": 1_609_344.0},
    "weight": {"g": 1.0, "kg": 1000.0, "t": 1_000_000.0,
               "lb": 453.59237, "oz": 28.349523125},
    "data": {"B": 1.0, "KB": 1024.0, "MB": 1024.0 ** 2,
             "GB": 1024.0 ** 3, "TB": 1024.0 ** 4},
}


def unit_convert(value, category, frm, to):
    factors = UNIT_FACTORS[category]
    return float(value) * factors[frm] / factors[to]
