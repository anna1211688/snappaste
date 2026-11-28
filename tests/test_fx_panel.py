# -*- coding: utf-8 -*-
"""汇率数据层与面板测试。"""
import time

import pytest

from kivo.core.fx_store import FxStore, FX_CURRENCIES
from kivo.ui.theme import Theme
from kivo.ui.panels.fx_panel import FxPanel


def mock_rates():
    return {code: (1.0 if code == "USD" else 7.2 if code == "CNY"
                   else 0.92 if code == "EUR" else 110.0 if code == "JPY"
                   else 0.78) for code, _ in FX_CURRENCIES}


# ---------- FxStore ----------
def test_fmt():
    assert FxStore.fmt(200.0) == "200.00"
    assert FxStore.fmt(1.5) == "1.5000"
    assert FxStore.fmt(0.001) == "0.001000"


def test_convert():
    fx = FxStore()
    fx.rates = mock_rates()
    assert fx.convert(100, "CNY", "USD") == pytest.approx(100 / 7.2)
    assert fx.convert(1, "USD", "CNY") == pytest.approx(7.2)
    assert fx.convert(1, "X", "Y") is None


def test_table_rate():
    fx = FxStore()
    assert fx.table_rate("USD", "CNY") is None
    fx.rates = mock_rates()
    assert fx.table_rate("USD", "CNY") == pytest.approx(7.2)


# ---------- FxPanel ----------
@pytest.fixture
def fp(qapp):
    fx = FxStore()
    fx.rates = mock_rates()
    fx.updated = "Mock"
    fx.fetch = lambda: (fx.rates, fx.updated)  # 屏蔽联网
    p = FxPanel(Theme(False), fx)
    p.show()
    qapp.processEvents()
    return p


def _pump(qapp, panel, timeout=3.0):
    end = time.time() + timeout
    while panel.loading and time.time() < end:
        qapp.processEvents()
        time.sleep(0.01)
    qapp.processEvents()


def test_table_filled(fp):
    assert fp.table.rowCount() == len(FX_CURRENCIES)


def test_convert_ui(fp):
    fp.amount.setText("100")
    fp.from_cb.setCurrentIndex(fp.from_cb.findData("CNY"))
    fp.to_cb.setCurrentIndex(fp.to_cb.findData("USD"))
    fp._convert()
    assert "USD" in fp.result.text()


def test_bad_amount(fp):
    fp.amount.setText("abc")
    fp._convert()
    assert fp.result.text() == ""
    assert "金额" in fp.hint.text()


def test_swap(fp):
    fp.from_cb.setCurrentIndex(fp.from_cb.findData("CNY"))
    fp.to_cb.setCurrentIndex(fp.to_cb.findData("USD"))
    fp._swap()
    assert fp.from_cb.currentData() == "USD"
    assert fp.to_cb.currentData() == "CNY"


def test_base_change_table(fp):
    fp.base_cb.setCurrentIndex(fp.base_cb.findData("CNY"))
    fp._fill_table()
    # 基准 CNY 时 USD 汇率 = 1/7.2
    assert fp.table.rowCount() == len(FX_CURRENCIES)


def test_fetch_failure(qapp):
    fx = FxStore()
    def boom():
        raise RuntimeError("网络断了")
    fx.fetch = boom
    p = FxPanel(Theme(False), fx)
    p.show()
    _pump(qapp, p)
    assert "失败" in p.status.text()
    assert not p.loading
