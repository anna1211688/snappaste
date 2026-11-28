# -*- coding: utf-8 -*-
"""语音模块单元测试 (不联网)。"""
import pytest

from kivo.core import voice


class FakeConfig:
    def __init__(self, values=None):
        self._values = values or {}

    def get(self, section, key, fallback=None):
        return self._values.get((section, key), fallback)


class TestMime:
    def setup_method(self):
        self.vc = voice.VoiceClient(FakeConfig(), None)

    def test_known_ext(self):
        assert self.vc.resolve_mime("a.WAV") == (".wav", "audio/wav")

    def test_unknown_ext_raises(self):
        with pytest.raises(RuntimeError):
            self.vc.resolve_mime("a.txt")

    def test_stt_model_default(self):
        assert self.vc._stt_model() == voice.STT_DEFAULT

    def test_stt_model_custom(self):
        cfg = FakeConfig({("AI", "VoiceModel"): "gpt-4o-transcribe"})
        assert voice.VoiceClient(cfg, None)._stt_model() == "gpt-4o-transcribe"


class TestMultipart:
    def test_fields_and_files(self):
        body = voice.encode_multipart(
            "BB", [("model", "whisper-1")],
            [("file", "a.mp3", "audio/mpeg", b"RAWDATA")])
        assert b"--BB" in body
        assert b'name="model"' in body
        assert b"whisper-1" in body
        assert b"Content-Type: audio/mpeg" in body
        assert b"RAWDATA" in body
        assert body.endswith(b"--BB--\r\n")

    def test_safe_filename(self):
        assert voice.safe_filename("normal.mp3", ".mp3") == "normal.mp3"

    def test_safe_filename_strips_unsafe(self):
        out = voice.safe_filename('a"b<>c.mp3', ".mp3")
        assert '"' not in out and "<" not in out

    def test_safe_filename_fallback(self):
        assert voice.safe_filename("???", ".mp3") == "voice.mp3"


class TestTargets:
    def test_tgt_name(self):
        assert voice.tgt_name("zh-CN") == "中文"
        assert voice.tgt_name("ja") == "日本語"

    def test_tgt_name_unknown(self):
        assert voice.tgt_name("xx") == "中文"

    def test_tgt_code(self):
        assert voice.tgt_code("English") == "en"

    def test_tgt_code_unknown(self):
        assert voice.tgt_code("外星语") == "zh-CN"
