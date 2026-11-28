# -*- coding: utf-8 -*-
"""计算器状态机与面板测试。"""
import pytest

from kivo.core import calc_store as calc_mod
from kivo.core.calc_store import CalcStore, fmt, apply, ERROR
from kivo.ui.theme import Theme
from kivo.ui.panels.calc_panel import CalcPanel


@pytest.fixture(autouse=True)
def _isolated_hist(tmp_path, monkeypatch):
    monkeypatch.setattr(calc_mod, "CALC_HISTORY_PATH", str(tmp_path / "calc_history.json"))


def test_fmt():
    assert fmt(20.0) == "20"
    assert fmt(1.5) == "1.5"
    assert fmt(float("inf")) == ERROR


def test_apply_div_zero():
    with pytest.raises(ZeroDivisionError):
        apply(1, "÷", 0)
    assert apply(2, "×", 3) == 6


def test_addition():
    s = CalcStore()
    s.digit("1"); s.digit("2")
    s.set_op("+")
    s.digit("8")
    s.equals()
    assert s.display == "20"


def test_chained_op():
    s = CalcStore()
    s.digit("2"); s.set_op("+"); s.digit("3"); s.set_op("+")
    assert s.display == "5"


def test_divide_by_zero():
    s = CalcStore()
    s.digit("5"); s.set_op("÷"); s.digit("0"); s.equals()
    assert s.display == ERROR
    assert s.acc is None


def test_clear_and_back():
    s = CalcStore()
    s.digit("9"); s.back()
    assert s.display == "0"
    s.digit("7"); s.clear()
    assert s.display == "0"


def test_percent_and_negate():
    s = CalcStore()
    s.digit("5"); s.digit("0"); s.percent()
    assert s.display == "0.5"
    s.negate()
    assert s.display == "-0.5"


def test_dot():
    s = CalcStore()
    s.dot(); s.digit("5")
    assert s.display == "0.5"


def test_history():
    s = CalcStore()
    s.digit("2"); s.set_op("+"); s.digit("2"); s.equals()
    assert len(s.history) == 1
    s.pick_history(0)
    assert s.display == "4"
    s.clear_history()
    assert s.history == []


def test_panel_render(qapp):
    p = CalcPanel(Theme(False))
    p.show()
    qapp.processEvents()
    assert p.disp_lab.text() == "0"
    assert p.hist_list.count() >= 1
