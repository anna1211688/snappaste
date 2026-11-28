# -*- coding: utf-8 -*-
"""翻译引擎单元测试 (不联网)。"""

from kivo.core import translate


class FakeConfig:
    def __init__(self, values=None):
        self._values = values or {}

    def get(self, section, key, fallback=None):
        return self._values.get((section, key), fallback)


class TestBasics:
    def test_has_cjk(self):
        assert translate.has_cjk("你好世界")
        assert not translate.has_cjk("hello world")

    def test_lang_maps(self):
        assert translate._BAIDU_LANG["zh-CN"] == "zh"
        assert translate._YOUDAO_LANG["zh-TW"] == "zh-CHT"


class TestClient:
    def setup_method(self):
        self.tc = translate.TranslateClient(FakeConfig())

    def test_default_service_free(self):
        assert self.tc.trans_cfg()["service"] == "free"

    def test_custom_service(self):
        cfg = FakeConfig({("Translate", "Service"): "baidu",
                          ("Translate", "BaiduAppId"): "id",
                          ("Translate", "BaiduKey"): "key"})
        c = translate.TranslateClient(cfg).trans_cfg()
        assert c["service"] == "baidu"
        assert c["baidu_id"] == "id"

    def test_unknown_service_falls_back(self):
        cfg = FakeConfig({("Translate", "Service"): "weird"})
        assert translate.TranslateClient(cfg).trans_cfg()["service"] == "free"

    def test_empty_text(self):
        assert self.tc.translate_to("   ", "zh-CN") == ""

    def test_already_chinese_short_circuit(self):
        out = self.tc.translate_to("这是一段足够长的中文内容来测试", "zh-CN")
        assert out == "这是一段足够长的中文内容来测试"

    def test_translate_direction(self):
        assert self.tc.translate("") == ""

    def test_cache_roundtrip(self):
        key = ("hello", "zh-CN", None)
        assert self.tc._cache_get(key) is None
        self.tc._cache_put(key, "你好")
        assert self.tc._cache_get(key) == "你好"

    def test_cache_eviction(self):
        for i in range(translate.CACHE_MAX + 5):
            self.tc._cache_put((f"k{i}", "t", None), f"v{i}")
        assert len(self.tc._cache) <= translate.CACHE_MAX

    def test_circuit_starts_alive(self):
        assert self.tc._alive("google")

    def test_hard_failure_opens_circuit(self):
        self.tc._mark("google", False, hard=True)
        assert not self.tc._alive("google")

    def test_success_closes_circuit(self):
        self.tc._mark("google", False, hard=True)
        self.tc._mark("google", True)
        assert self.tc._alive("google")

    def test_soft_failures_accumulate(self):
        self.tc._mark("api", False)
        assert self.tc._alive("api")  # 1 次还不熔断
        self.tc._mark("api", False)
        self.tc._mark("api", False)
        assert not self.tc._alive("api")  # 3 次熔断
