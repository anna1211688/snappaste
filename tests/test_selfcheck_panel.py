# -*- coding: utf-8 -*-
"""软件自检数据层与面板测试。"""
import json

from kivo.core import selfcheck
from kivo.core.selfcheck import SelfCheckRunner
from kivo.ui.theme import Theme
from kivo.ui.panels.selfcheck_panel import SelfCheckPanel


def test_data_writable(tmp_path):
    ok, _ = selfcheck.check_data_writable(str(tmp_path))
    assert ok


def test_data_not_writable():
    ok, _ = selfcheck.check_data_writable("/nonexistent-dir-xyz")
    assert not ok


def test_config_check(tmp_path):
    cfg = tmp_path / "Config.ini"
    cfg.write_text("[Config]\nA=1\n", encoding="utf-8")
    ok, _ = selfcheck.check_config(str(cfg))
    assert ok


def test_config_check_gbk(tmp_path):
    # GBK 编码的老配置在 utf-8-sig 下解码失败: 自检项应报告失败而非抛异常
    cfg = tmp_path / "Config.ini"
    cfg.write_bytes("[Config]\n名字=值\n".encode("gbk"))
    ok, _ = selfcheck.check_config(str(cfg))
    assert not ok


def test_worker_run_fallback(qapp):
    from kivo.ui.panels.selfcheck_panel import _Worker

    class Boom:
        def run(self):
            raise RuntimeError("boom")

    got = []
    w = _Worker(Boom())
    w.finished.connect(lambda d: got.append(d))
    w.run()  # 直接调用, 验证异常兜底后仍发出 finished
    assert len(got) == 1
    assert all(not ok for ok, _ in got[0].values())


def test_records_good(tmp_path):
    rec = tmp_path / "records.json"
    rec.write_text(json.dumps(["a", "b"]), encoding="utf-8")
    ok, _ = selfcheck.check_records(str(rec))
    assert ok


def test_records_bad(tmp_path):
    rec = tmp_path / "records.json"
    rec.write_text("not json", encoding="utf-8")
    ok, _ = selfcheck.check_records(str(rec))
    assert not ok


def test_runner_all(tmp_path):
    cfg = tmp_path / "Config.ini"
    cfg.write_text("[Config]\nA=1\n", encoding="utf-8")
    rec = tmp_path / "records.json"
    rec.write_text("[]", encoding="utf-8")
    runner = SelfCheckRunner(
        str(tmp_path), str(cfg), str(rec),
        ocr_provider=lambda: "engine",
        translate_provider=lambda: "译文",
        hotkey_provider=lambda: 3)
    results = runner.run()
    assert results["data"][0]
    assert results["config"][0]
    assert results["records"][0]
    assert results["ocr"][0]
    assert results["translate"][0]
    assert results["hotkey"][0]
    assert results["hotkey"][1] == "3 个已注册"


def test_external_provider_exception():
    def boom():
        raise RuntimeError("x")
    ok, _ = SelfCheckRunner._external(boom)
    assert not ok


def test_hotkey_none():
    runner = SelfCheckRunner("", "", "", hotkey_provider=lambda: 0)
    ok, extra = runner._hotkey()
    assert not ok and "未注册" in extra


def test_panel_render(qapp, tmp_path):
    cfg = tmp_path / "Config.ini"
    cfg.write_text("[Config]\n", encoding="utf-8")
    rec = tmp_path / "records.json"
    rec.write_text("[]", encoding="utf-8")
    runner = SelfCheckRunner(str(tmp_path), str(cfg), str(rec))
    p = SelfCheckPanel(Theme(False), runner)
    p.show()
    qapp.processEvents()
    assert len(p._rows) == 6
