# -*- coding: utf-8 -*-
"""世界时钟数据层: 城市目录、时区构造、当前时间与跨时区换算。"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

CLOCK_CATALOG = [
    ("北京", "Asia/Shanghai", 8), ("香港", "Asia/Hong_Kong", 8),
    ("台北", "Asia/Taipei", 8), ("新加坡", "Asia/Singapore", 8),
    ("曼谷", "Asia/Bangkok", 7), ("雅加达", "Asia/Jakarta", 7),
    ("马尼拉", "Asia/Manila", 8), ("东京", "Asia/Tokyo", 9),
    ("首尔", "Asia/Seoul", 9), ("孟买", "Asia/Kolkata", 5.5),
    ("悉尼", "Australia/Sydney", 10), ("墨尔本", "Australia/Melbourne", 10),
    ("奥克兰", "Pacific/Auckland", 12), ("迪拜", "Asia/Dubai", 4),
    ("伊斯坦布尔", "Europe/Istanbul", 3), ("莫斯科", "Europe/Moscow", 3),
    ("开罗", "Africa/Cairo", 2), ("约翰内斯堡", "Africa/Johannesburg", 2),
    ("伦敦", "Europe/London", 0), ("巴黎", "Europe/Paris", 1),
    ("柏林", "Europe/Berlin", 1), ("罗马", "Europe/Rome", 1),
    ("纽约", "America/New_York", -5), ("多伦多", "America/Toronto", -5),
    ("芝加哥", "America/Chicago", -6), ("丹佛", "America/Denver", -7),
    ("洛杉矶", "America/Los_Angeles", -8), ("温哥华", "America/Vancouver", -8),
    ("圣保罗", "America/Sao_Paulo", -3),
]

CLOCK_DEFAULT = ["Asia/Shanghai", "Asia/Tokyo", "Asia/Seoul", "Asia/Singapore",
                  "Australia/Sydney", "Asia/Dubai", "Europe/Moscow",
                  "Europe/London", "Europe/Paris", "America/New_York",
                  "America/Los_Angeles"]

WEEKDAYS = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")


def make_tz(name, std_hours):
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(name)
    except Exception:
        return timezone(timedelta(hours=std_hours))


class ClockStore:
    def __init__(self, config):
        self.config = config

    def _entry(self, tzname):
        for n, t, h in CLOCK_CATALOG:
            if t == tzname:
                return n, t, h
        try:
            from zoneinfo import ZoneInfo
            off = datetime(2024, 1, 15, tzinfo=ZoneInfo(tzname)).utcoffset()
            std = off.total_seconds() / 3600.0 if off else 0
            name = tzname.rsplit("/", 1)[-1].replace("_", " ")
            return name, tzname, std
        except Exception:
            return None

    def selected(self):
        raw = self.config.get("Config", "ClockCities", fallback="") or ""
        picked, seen = [], set()
        for tz in (x.strip() for x in raw.split(",")):
            if not tz or tz in seen:
                continue
            seen.add(tz)
            e = self._entry(tz)
            if e is not None:
                picked.append(e)
        if not picked:
            picked = [e for tz in CLOCK_DEFAULT if (e := self._entry(tz))]
        return picked[:15]

    @staticmethod
    def now_in(tz):
        return datetime.now(tz)

    @staticmethod
    def convert(local_dt, target_tz):
        # local_dt 视为本地时区时间, 转目标时区
        local_aware = local_dt.astimezone()
        return local_aware.astimezone(target_tz)

    @staticmethod
    def is_day(tz):
        return 7 <= datetime.now(tz).hour < 19
