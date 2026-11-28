# -*- coding: utf-8 -*-
"""AI 客户端: OpenAI 兼容 /chat/completions, 多服务商、流式、429 退避、同服务商故障切换。

只依赖标准库 urllib 与 ConfigManager; 调用方须在后台线程执行。
"""
from __future__ import annotations

import datetime
import json
import re
import time
import urllib.request
import urllib.error
import urllib.parse
import ipaddress

from .util import redact_ai_detail, redact_secrets
from . import network
from .i18n import tr


def provider_label(svc_key):
    """服务商显示名按当前语言返回；未注册的回退为 key。"""
    return tr(f"prov.{svc_key}")

# 服务 -> (显示名, 接口地址, 默认模型)
AI_PRESETS = {
    "zhipu": ("智谱 GLM-4V-Flash (免费)", "https://open.bigmodel.cn/api/paas/v4", "glm-4v-flash"),
    "bailian": ("阿里云百炼 Qwen-VL", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-vl-plus"),
    "siliconflow": ("硅基流动 Qwen2.5-VL", "https://api.siliconflow.cn/v1", "Qwen/Qwen2.5-VL-7B-Instruct"),
    "openai": ("OpenAI GPT-4o", "https://api.openai.com/v1", "gpt-4o"),
    "gemini": ("Google Gemini", "https://generativelanguage.googleapis.com/v1beta/openai", "gemini-2.0-flash"),
    "claude": ("Anthropic Claude", "https://api.anthropic.com/v1", "claude-sonnet-4-5-20250929"),
    "deepseek": ("DeepSeek (深度求索)", "https://api.deepseek.com/v1", "deepseek-chat"),
    "moonshot": ("Kimi (Moonshot)", "https://api.moonshot.cn/v1", "moonshot-v1-8k-vision-preview"),
    "volcengine": ("火山方舟 豆包", "https://ark.cn-beijing.volces.com/api/v3", "doubao-1-5-vision-pro-32k-250115"),
    "hunyuan": ("腾讯混元", "https://api.hunyuan.cloud.tencent.com/v1", "hunyuan-vision"),
    "qianfan": ("百度千帆 文心", "https://qianfan.baidubce.com/v2", "ernie-4.5-turbo-vl"),
    "xai": ("xAI Grok", "https://api.x.ai/v1", "grok-2-vision"),
    "dots": ("Dots 点点 (免费体验)", "https://note3-prev-api.askdiandian.com/v1", "dots3-note-prev"),
    "ollama": ("Ollama 本地/自建", "http://localhost:11434/v1", "qwen2.5vl"),
    "custom": ("自定义 (OpenAI 兼容接口)", "", ""),
}

AI_ROUTES = {"chat": "RouteChat", "vision": "RouteVision", "reply": "RouteReply",
             "text": "RouteText", "annotate": "RouteAnnotate", "voice": "RouteVoice"}


def http_base(u):
    """接口地址校验规整: 仅 http/https, 公网 http 拒绝 (明文 Key 风险), 去尾斜杠。"""
    u = (u or "").strip()
    p = urllib.parse.urlparse(u)
    if p.scheme not in ("http", "https") or not p.netloc or any(c in u for c in " \t\r\n"):
        shown = u[:60] or tr("aierr.empty_value")
        raise RuntimeError(tr("aierr.bad_base", u=shown))
    if p.scheme == "http":
        host = (p.hostname or "").lower()
        local = host in ("localhost",) or host.endswith(".local")
        if not local:
            try:
                ip = ipaddress.ip_address(host)
                local = ip.is_loopback or ip.is_private or ip.is_link_local
            except ValueError:
                local = False
        if not local:
            shown = u[:60] or tr("aierr.empty_value")
            raise RuntimeError(tr("aierr.public_http", u=shown))
    return u.rstrip("/")


def parse_retry_after(value):
    """Retry-After: 数字秒 (0-30) 或 HTTP 日期; 无法解析返回 None。"""
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        v = int(value)
        return float(v) if 0 <= v <= 30 else None
    try:
        import email.utils
        dt = email.utils.parsedate_to_datetime(value)
        return max(0.0, (dt - datetime.datetime.now(dt.tzinfo)).total_seconds())
    except Exception:
        return None


class AIClient:
    def __init__(self, config):
        """config: ConfigManager。用户可见错误文案经 core.i18n 按当前语言返回。"""
        self.config = config

    # ---------- 配置解析 ----------
    def _g(self, key, d=""):
        return (self.config.get("AI", key, fallback=d) or d).strip()

    def cfg(self, svc=None):
        g = self._g
        svc = svc or g("Service", "zhipu") or "zhipu"
        if svc not in AI_PRESETS:
            svc = "zhipu"
        _name, pbase, pmodel = AI_PRESETS[svc]
        pre = svc.capitalize()
        active = svc == (g("Service", "zhipu") or "zhipu")
        return {
            "service": svc,
            "key": g(pre + "Key") or (g("ApiKey") if active else ""),
            "base": g(pre + "Base") or (g("BaseUrl") if active else "") or pbase,
            "model": g(pre + "Model") or (g("Model") if active else "") or pmodel,
        }

    def cfg_for(self, route):
        rk = AI_ROUTES.get(route or "")
        if rk:
            svc = (self.config.get("AI", rk, fallback="") or "").strip()
            if svc in AI_PRESETS:
                c = self.cfg(svc)
                if c["key"]:
                    model = (self.config.get("AI", rk + "Model", fallback="") or "").strip()[:200]
                    if model:
                        try:
                            profiles = json.loads(
                                self.config.get("AI", "ModelProfiles", fallback="{}") or "{}")
                            rows = profiles.get(svc, []) if isinstance(profiles, dict) else []
                            allowed = any(isinstance(x, dict) and x.get("model") == model
                                         and x.get("enabled", True)
                                         for x in rows if isinstance(rows, list))
                        except Exception:
                            allowed = False
                        if allowed:
                            c["model"] = model
                    return c
        return self.cfg()

    def ready(self, route=None):
        return bool((self.cfg_for(route) if route else self.cfg())["key"])

    # ---------- 模型目录 ----------
    def fetch_models(self, cfg, timeout=15):
        base = http_base(cfg.get("base", ""))
        if not base:
            raise RuntimeError(tr("aierr.need_base"))
        headers = {"Authorization": "Bearer " + (cfg.get("key") or ""), "User-Agent": "KIVO"}
        req = urllib.request.Request(base + "/models", headers=headers, method="GET")
        try:
            with network.open_url(req, timeout=max(3, min(int(timeout), 30))) as resp:
                raw = resp.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                raise RuntimeError(tr("aierr.models_too_large"))
            data = json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read(2048).decode("utf-8", "replace")
            except Exception:
                pass
            detail = redact_ai_detail(detail, cfg.get("key") or "")
            raise RuntimeError(tr("aierr.fetch_models_fail",
                                 code=exc.code, detail=detail[:300])) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(tr("aierr.cannot_connect_models",
                                 reason=str(exc.reason))) from exc
        items = data.get("data", []) if isinstance(data, dict) else []
        models = []
        for item in items[:500]:
            if not isinstance(item, dict):
                continue
            mid = item.get("id")
            if isinstance(mid, str):
                mid = mid.strip()
                if mid and len(mid) <= 200 and not any(ord(ch) < 32 for ch in mid):
                    models.append(mid)
        return sorted(set(models), key=str.casefold)

    # ---------- 核心对话请求 ----------
    def chat_messages(self, messages, cfg=None, temperature=0.7, max_tokens=1024, timeout=90,
                      route=None, stream_callback=None, cancel_event=None):
        cfg = cfg or (self.cfg_for(route) if route else self.cfg())
        if not cfg["key"]:
            raise RuntimeError(tr("aierr.need_key"))
        if not cfg["base"] or not cfg["model"]:
            raise RuntimeError(tr("aierr.incomplete"))
        if cfg.get("service") == "zhipu":
            max_tokens = max(1, min(int(max_tokens), 1024))
        payload = {"model": cfg["model"], "max_tokens": max_tokens,
                   "temperature": temperature, "messages": messages}
        headers = {"Content-Type": "application/json",
                   "Authorization": "Bearer " + cfg["key"], "User-Agent": "KIVO"}
        if cfg.get("service") == "dots":
            headers["api-key"] = cfg["key"]
            think = False
            if route in (None, "chat"):
                try:
                    think = (self.config.get("AI", "Thinking", fallback="0") or "0").strip() == "1"
                except Exception:
                    think = False
            payload["chat_template_kwargs"] = {"enable_thinking": think}

        def _send(pl, rate_retried=False):
            req_payload = dict(pl)
            if stream_callback is not None:
                req_payload["stream"] = True
            req = urllib.request.Request(http_base(cfg["base"]) + "/chat/completions",
                                         data=json.dumps(req_payload).encode("utf-8"),
                                         headers=headers)
            try:
                open_timeout = min(timeout, 45) if stream_callback is not None else timeout
                with network.open_url(req, timeout=open_timeout) as r:
                    if stream_callback is None:
                        raw = r.read(2 * 1024 * 1024 + 1)
                        if len(raw) > 2 * 1024 * 1024:
                            raise RuntimeError(tr("aierr.response_too_large"))
                        return json.loads(raw.decode("utf-8"))
                    chunks, raw_lines, saw_sse = [], [], False
                    while not (cancel_event is not None and cancel_event.is_set()):
                        line = r.readline(1024 * 1024 + 1)
                        if not line:
                            break
                        if len(line) > 1024 * 1024:
                            raise RuntimeError(tr("aierr.stream_line_too_large"))
                        line = line.decode("utf-8", "replace").strip()
                        if not line:
                            continue
                        if not line.startswith("data:"):
                            if not line.startswith(":"):
                                raw_lines.append(line)
                            continue
                        data_line = line[5:].strip()
                        if data_line == "[DONE]":
                            break
                        saw_sse = True
                        try:
                            event = json.loads(data_line)
                        except Exception:
                            continue
                        if isinstance(event, dict) and event.get("error"):
                            raise RuntimeError(str(event["error"])[:500])
                        choices = event.get("choices", []) if isinstance(event, dict) else []
                        if not choices or not isinstance(choices[0], dict):
                            continue
                        delta = choices[0].get("delta", {})
                        piece = delta.get("content", "") if isinstance(delta, dict) else ""
                        if isinstance(piece, list):
                            piece = "".join(str(p.get("text", "")) for p in piece
                                            if isinstance(p, dict))
                        if isinstance(piece, str) and piece:
                            chunks.append(piece)
                            stream_callback(piece)
                    if saw_sse:
                        return {"choices": [{"message": {"content": "".join(chunks)}}]}
                    if cancel_event is not None and cancel_event.is_set():
                        return {"choices": [{"message": {"content": ""}}]}
                    raw = ("\n".join(raw_lines)).encode("utf-8") + r.read(2 * 1024 * 1024 + 1)
                    if len(raw) > 2 * 1024 * 1024:
                        raise RuntimeError(tr("aierr.response_too_large"))
                    return json.loads(raw.decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code == 429 and not rate_retried:
                    wait_s = parse_retry_after(e.headers.get("Retry-After"))
                    if wait_s is not None:
                        capped = min(10.0, wait_s)
                        if cancel_event is not None:
                            if cancel_event.wait(capped):
                                raise RuntimeError("stopped")
                        else:
                            time.sleep(capped)
                        return _send(pl, True)
                try:
                    detail = e.read(2048).decode("utf-8", "ignore")[:200]
                except Exception:
                    detail = ""
                detail = redact_ai_detail(detail, cfg.get("key") or "")
                detail = re.sub(r"[\r\n\t]+", " ", detail).strip()[:160]
                err = RuntimeError(tr("aierr.http", code=e.code, detail=detail))
                err._kivo_status = e.code
                raise err
            except Exception as e:
                if isinstance(e, RuntimeError):
                    raise
                raise RuntimeError(tr("aierr.conn",
                                     detail=redact_secrets(str(e))))

        def _extract(d):
            try:
                msg = d["choices"][0]["message"]
            except Exception:
                raise RuntimeError(tr("aierr.bad_format"))
            c = msg.get("content")
            if isinstance(c, list):
                c = "".join(str(p.get("text", "")) for p in c if isinstance(p, dict))
            return (c or "").strip(), (msg.get("reasoning_content") or "")

        try:
            content, reasoning = _extract(_send(payload))
        except Exception as primary_error:
            if (stream_callback is not None or
                    (self.config.get("AI", "AutoFallback", fallback="0") or "0").strip() != "1"):
                raise
            if getattr(primary_error, "_kivo_status", None) in (401, 403):
                raise
            try:
                raw = json.loads(self.config.get("AI", "ModelProfiles", fallback="{}") or "{}")
                rows = raw.get(cfg.get("service"), []) if isinstance(raw, dict) else []
            except Exception:
                rows = []
            attempted = {cfg.get("model")}
            tried = 0
            for profile in rows if isinstance(rows, list) else []:
                if not isinstance(profile, dict) or not profile.get("enabled", True):
                    continue
                candidate = str(profile.get("model", "")).strip()[:200]
                if not candidate or candidate in attempted:
                    continue
                if tried >= 2:
                    raise primary_error
                tried += 1
                attempted.add(candidate)
                retry_payload = dict(payload)
                retry_payload["model"] = candidate
                try:
                    content, reasoning = _extract(_send(retry_payload))
                    if content:
                        break
                except Exception:
                    continue
            else:
                raise primary_error
        if not content and reasoning and cfg.get("service") == "dots":
            payload["chat_template_kwargs"] = {"enable_thinking": False}
            content, reasoning = _extract(_send(payload))
        return content
