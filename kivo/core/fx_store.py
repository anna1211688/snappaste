# -*- coding: utf-8 -*-
"""汇率数据层: 货币表、在线汇率获取、换算与格式化。"""
from __future__ import annotations

import json

from . import network
from .i18n import tr

FX_CURRENCIES = [
    ("USD", "美元"), ("CNY", "人民币"), ("HKD", "港币"), ("EUR", "欧元"),
    ("GBP", "英镑"), ("JPY", "日元"), ("KRW", "韩元"), ("TWD", "新台币"),
    ("MOP", "澳门元"), ("AUD", "澳元"), ("CAD", "加元"), ("CHF", "瑞士法郎"),
    ("SGD", "新加坡元"), ("NZD", "新西兰元"), ("THB", "泰币"),
    ("MYR", "马来西亚林吉特"), ("IDR", "印尼盾"), ("PHP", "菲律宾比索"),
    ("VND", "越南盾"), ("INR", "印度卢比"), ("AED", "阿联酋迪拉姆"),
    ("SAR", "沙特里亚尔"), ("RUB", "俄罗斯卢布"), ("BRL", "巴西雷亚尔"),
    ("MXN", "墨西哥比索"), ("ZAR", "南非兰特"), ("TRY", "土耳其里拉"),
    ("SEK", "瑞典克朗"), ("NOK", "挪威克朗"), ("DKK", "丹麦克朗"),
    ("PLN", "波兰兹罗提"),
]


def currency_label(code: str) -> str:
    """货币代码对应的当前语言名称。"""
    return tr(f"currency.{code}")


class FxStore:
    def __init__(self):
        self.rates = None
        self.updated = ""

    def label(self, code):
        return f"{code} {currency_label(code)}"

    def fetch(self):
        import urllib.request
        req = urllib.request.Request(
            "https://open.er-api.com/v6/latest/USD",
            headers={"User-Agent": "KIVO"})
        with network.open_url_loose(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
        if data.get("result") != "success" or not isinstance(data.get("rates"), dict):
            raise RuntimeError(tr("fx.api_error"))
        self.rates = data["rates"]
        self.updated = data.get("time_last_update_utc", "")
        return self.rates, self.updated

    @staticmethod
    def fmt(v):
        if v >= 100:
            return f"{v:,.2f}"
        if v >= 1:
            return f"{v:,.4f}"
        return f"{v:.6f}"

    def table_rate(self, base, code):
        if not self.rates or base not in self.rates or code not in self.rates:
            return None
        return self.rates[code] / self.rates[base]

    def convert(self, amount, fr, to):
        if not self.rates or fr not in self.rates or to not in self.rates:
            return None
        return amount * self.rates[to] / self.rates[fr]
