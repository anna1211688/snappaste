# -*- coding: utf-8 -*-
"""语音转写与翻译: 标准库手写 multipart 上传 /audio/transcriptions, 再经 AI 通道翻译。"""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
import uuid

from . import network
from .util import redact_ai_detail
from .ai import http_base

MAX_SIZE = 25 * 1024 * 1024
STT_DEFAULT = "whisper-1"
MIME = {".ogg": "audio/ogg", ".oga": "audio/ogg", ".opus": "audio/ogg",
        ".m4a": "audio/mp4", ".aac": "audio/aac", ".mp3": "audio/mpeg",
        ".wav": "audio/wav", ".webm": "audio/webm", ".flac": "audio/flac"}

TRANS_TARGETS = [("中文", "zh-CN"), ("繁體中文", "zh-TW"), ("English", "en"),
                 ("日本語", "ja"), ("한국어", "ko"), ("Français", "fr"),
                 ("Deutsch", "de"), ("Español", "es"), ("Русский", "ru"),
                 ("Português", "pt"), ("Italiano", "it"), ("ไทย", "th"),
                 ("Tiếng Việt", "vi")]


def tgt_name(code):
    for n, c in TRANS_TARGETS:
        if c == code:
            return n
    return "中文"


def tgt_code(name):
    for n, c in TRANS_TARGETS:
        if n == name:
            return c
    return "zh-CN"


def encode_multipart(boundary, fields, files):
    """手写 multipart/form-data; fields=[(name,value)], files=[(name,filename,mime,data)]。"""
    out = bytearray()
    b = boundary.encode("utf-8")
    for name, value in fields:
        out += b"--" + b + b"\r\n"
        out += ('Content-Disposition: form-data; name="%s"\r\n\r\n' % name).encode("utf-8")
        out += str(value).encode("utf-8") + b"\r\n"
    for name, filename, mime, data in files:
        out += b"--" + b + b"\r\n"
        out += ('Content-Disposition: form-data; name="%s"; filename="%s"\r\n'
                % (name, filename)).encode("utf-8")
        out += ('Content-Type: %s\r\n\r\n' % mime).encode("utf-8")
        out += data + b"\r\n"
    out += b"--" + b + b"--\r\n"
    return bytes(out)


def safe_filename(name, ext):
    safe = "".join(ch for ch in os.path.basename(name) if ch.isalnum() or ch in "._-")
    if not safe or "." not in safe:
        safe = "voice" + ext
    return safe[:120]


class VoiceClient:
    def __init__(self, config, ai_client):
        self.config = config
        self.ai_client = ai_client

    def _stt_model(self):
        return (self.config.get("AI", "VoiceModel", fallback=STT_DEFAULT)
                or STT_DEFAULT).strip()[:120]

    def resolve_mime(self, path):
        ext = os.path.splitext(path)[1].lower()
        mime = MIME.get(ext)
        if not mime:
            raise RuntimeError("不支持这个音频格式 (支持 %s)。"
                               % "、".join(sorted(MIME)))
        return ext, mime

    def transcribe(self, path, cfg, language="", timeout=120):
        ext, mime = self.resolve_mime(path)
        try:
            size = os.path.getsize(path)
        except OSError as e:
            raise RuntimeError("读不到这个音频文件: " + str(e))
        if size <= 0:
            raise RuntimeError("这个音频文件是空的 (0 字节)。")
        if size > MAX_SIZE:
            raise RuntimeError("音频超过转写接口 25 MB 的上限, 请先裁剪或压缩。")
        with open(path, "rb") as f:
            data = f.read()
        boundary = "----KIVOvoice" + uuid.uuid4().hex
        fields = [("model", self._stt_model())]
        if language:
            fields.append(("language", language))
        body = encode_multipart(
            boundary, fields,
            [("file", safe_filename(path, ext), mime, data)])
        url = http_base(cfg["base"]) + "/audio/transcriptions"
        headers = {"Content-Type": "multipart/form-data; boundary=" + boundary,
                   "Authorization": "Bearer " + cfg["key"], "User-Agent": "KIVO"}
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with network.open_url(req, timeout=max(5, min(int(timeout), 300))) as resp:
                raw = resp.read(8 * 1024 * 1024 + 1)
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read(2048).decode("utf-8", "replace")
            except Exception:
                pass
            raise RuntimeError("语音转写失败 (HTTP %s): %s"
                               % (exc.code, redact_ai_detail(detail, cfg["key"])[:300])) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError("连不上语音转写服务: " + str(exc.reason)) from exc
        try:
            obj = json.loads(raw.decode("utf-8"))
        except Exception:
            raise RuntimeError("转写服务返回的内容不是有效 JSON。")
        text = (obj.get("text") or "").strip() if isinstance(obj, dict) else ""
        if not text:
            raise RuntimeError("转写结果为空: 可能没有可识别的人声, 或模型不被支持。")
        return text

    def translate_text(self, text, target_code, timeout=90):
        messages = [
            {"role": "system",
             "content": ("你是专业口译/笔译。把用户提供的语音转写文本翻译成%s, 只输出译文本身, "
                         "保持自然通顺, 不要解释、不要附原文、不要加任何标记。"
                         % tgt_name(target_code))},
            {"role": "user", "content": text}]
        return (self.ai_client.chat_messages(
            messages, temperature=0.3, max_tokens=2048,
            timeout=timeout, route="voice") or "").strip()
