# -*- coding: utf-8 -*-
"""AI 客户端单元测试 (不联网)。"""
import io

import pytest
from PIL import Image

from kivo.core import ai, ai_image


class FakeConfig:
    """内存假配置: 模拟 ConfigManager.get。"""
    def __init__(self, values=None):
        self._values = values or {}

    def get(self, section, key, fallback=None):
        return self._values.get((section, key), fallback)


class TestHttpBase:
    def test_https_trim_slash(self):
        assert ai.http_base("https://api.x.com/v1/") == "https://api.x.com/v1"

    def test_reject_non_http(self):
        for bad in ("ftp://x", "file:///x", "not a url", ""):
            with pytest.raises(RuntimeError):
                ai.http_base(bad)

    def test_reject_public_http(self):
        with pytest.raises(RuntimeError):
            ai.http_base("http://api.public.com/v1")

    def test_allow_localhost_http(self):
        assert ai.http_base("http://localhost:11434/v1") == "http://localhost:11434/v1"

    def test_allow_private_ip_http(self):
        assert "192.168.1.5" in ai.http_base("http://192.168.1.5:8080")


class TestRetryAfter:
    def test_seconds(self):
        assert ai.parse_retry_after("5") == 5.0

    def test_out_of_range(self):
        assert ai.parse_retry_after("99") is None

    def test_invalid(self):
        assert ai.parse_retry_after("nope") is None
        assert ai.parse_retry_after("") is None


class TestCfg:
    def test_default_service(self):
        client = ai.AIClient(FakeConfig())
        c = client.cfg()
        assert c["service"] == "zhipu"
        assert c["base"] == ai.AI_PRESETS["zhipu"][1]
        assert c["model"] == ai.AI_PRESETS["zhipu"][2]

    def test_explicit_service_uses_own_fields(self):
        cfg = FakeConfig({
            ("AI", "Service"): "openai",
            ("AI", "OpenaiKey"): "openai-key",
            ("AI", "OpenaiModel"): "gpt-4o-mini",
        })
        client = ai.AIClient(cfg)
        c = client.cfg("openai")
        assert c["key"] == "openai-key"
        assert c["model"] == "gpt-4o-mini"

    def test_unknown_service_falls_back(self):
        cfg = FakeConfig({("AI", "Service"): "ghost"})
        assert ai.AIClient(cfg).cfg()["service"] == "zhipu"

    def test_ready(self):
        cfg = FakeConfig({("AI", "ZhipuKey"): "k123"})
        assert ai.AIClient(cfg).ready() is True
        assert ai.AIClient(FakeConfig()).ready() is False

    def test_cfg_for_route_override(self):
        cfg = FakeConfig({
            ("AI", "Service"): "zhipu",
            ("AI", "ZhipuKey"): "zp-key",
            ("AI", "OpenaiKey"): "oa-key",
            ("AI", "RouteChat"): "openai",
        })
        client = ai.AIClient(cfg)
        c = client.cfg_for("chat")
        assert c["service"] == "openai"
        assert c["key"] == "oa-key"

    def test_cfg_for_invalid_route_uses_active(self):
        client = ai.AIClient(FakeConfig())
        assert client.cfg_for("nope")["service"] == "zhipu"


class TestAiImage:
    def test_fit_downscales_long_edge(self):
        big = Image.new("RGB", (2000, 1000), "white")
        out = ai_image.fit_image(big)
        assert max(out.size) == ai_image.IMG_MAX_EDGE

    def test_fit_keeps_small(self):
        small = Image.new("RGB", (300, 200))
        out = ai_image.fit_image(small)
        assert out.size == (300, 200)

    def test_dataurl_prefix(self):
        img = Image.new("RGB", (10, 10), "blue")
        url = ai_image.image_dataurl(img)
        assert url.startswith("data:image/jpeg;base64,")
