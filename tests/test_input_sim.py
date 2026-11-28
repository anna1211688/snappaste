# -*- coding: utf-8 -*-
"""input_sim 纯逻辑测试 (平台无关); Win32 路径在非 Windows 自动降级。"""
from kivo.platform import input_sim


class TestTypeUnits:
    def test_ascii_pair(self):
        units = input_sim.type_units("A")
        assert len(units) == 2
        down, up = units
        assert down[0] == ord("A") and down[2] is False and down[3] is True
        assert up[2] is True

    def test_newline_uses_return_vk(self):
        units = input_sim.type_units("\n")
        assert [(u[1], u[2]) for u in units] == [
            (input_sim.VK_RETURN, False), (input_sim.VK_RETURN, True)]

    def test_tab_uses_vk(self):
        units = input_sim.type_units("\t")
        assert all(u[3] is False for u in units)
        assert units[0][1] == 0x09

    def test_cr_ignored(self):
        assert input_sim.type_units("\r") == []

    def test_supplementary_plane_is_surrogate_pair(self):
        units = input_sim.type_units("😀")
        downs = [u for u in units if u[2] is False]
        assert len(downs) == 2  # 两个 UTF-16 码元, 不被截断
