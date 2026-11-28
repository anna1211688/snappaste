# -*- coding: utf-8 -*-
"""附件文本提取 (纯标准库): PDF/Word/Excel, 防解压炸弹, 统一入口按扩展名分发。"""
from __future__ import annotations

import html as _html
import io
import os
import re
import zipfile
import zlib

from .i18n import tr

ATTACH_INFLATE_LIMIT = 20 * 1024 * 1024
ATTACH_TEXT_LIMIT = 4 * 1024 * 1024
ATTACH_ENTRY_LIMIT = 2000
RAW_SIZE_LIMIT = 12 * 1024 * 1024


class AttachLimit(Exception):
    """解压/提取超过安全上限。"""


# ---------- PDF ----------
def pdf_unescape_literal(b):
    out = bytearray()
    i = 0
    while i < len(b):
        c = b[i]
        if c == 0x5C and i + 1 < len(b):
            n = b[i + 1]
            if n in b"nrtbf":
                out.append({0x6E: 10, 0x72: 13, 0x74: 9, 0x62: 8, 0x66: 12}[n])
                i += 2
                continue
            if n in b"()\\":
                out.append(n)
                i += 2
                continue
            if 0x30 <= n <= 0x37:
                j = i + 1
                octd = b""
                while j < len(b) and j < i + 4 and 0x30 <= b[j] <= 0x37:
                    octd += bytes([b[j]])
                    j += 1
                out.append(int(octd, 8) & 0xFF)
                i = j
                continue
            out.append(n)
            i += 2
            continue
        out.append(c)
        i += 1
    return bytes(out)


def pdf_decode_text(b):
    if b[:2] == b"\xfe\xff":
        try:
            return b[2:].decode("utf-16-be", "ignore")
        except Exception:
            return ""
    try:
        return b.decode("utf-8")
    except Exception:
        return b.decode("latin-1", "ignore")


def extract_pdf_text(data):
    chunks, total = [], 0
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", data, re.S):
        raw = m.group(1)
        try:
            raw = zlib.decompressobj().decompress(raw, 8 * 1024 * 1024)
        except Exception:
            pass
        total += len(raw)
        if total > ATTACH_INFLATE_LIMIT:
            raise AttachLimit("pdf")
        if b"Tj" not in raw and b"TJ" not in raw:
            continue
        for tm in re.finditer(
                rb"\((?:\\.|[^\\()])*\)\s*Tj|\[(?:\\.|[^\[\]])*\]\s*TJ|<([0-9A-Fa-f\s]+)>\s*Tj",
                raw):
            seg = tm.group(0)
            if tm.group(1) is not None:
                try:
                    hexs = re.sub(rb"\s", b"", tm.group(1)).decode("ascii")
                    chunks.append(pdf_decode_text(bytes.fromhex(hexs)))
                except Exception:
                    pass
                chunks.append("\n")
                continue
            for pm in re.finditer(rb"\((?:\\.|[^\\()])*\)|<([0-9A-Fa-f\s]+)>", seg):
                if pm.group(1) is not None:
                    try:
                        hexs = re.sub(rb"\s", b"", pm.group(1)).decode("ascii")
                        chunks.append(pdf_decode_text(bytes.fromhex(hexs)))
                    except Exception:
                        pass
                else:
                    chunks.append(pdf_decode_text(pdf_unescape_literal(pm.group(0)[1:-1])))
            chunks.append("\n")
        if sum(len(c) for c in chunks) > ATTACH_TEXT_LIMIT:
            break
    return "".join(chunks).strip()


# ---------- zip 安全读 ----------
def zip_read_bytes(z, name, budget):
    try:
        info = z.getinfo(name)
    except KeyError:
        return None
    if info.file_size > budget:
        raise AttachLimit(name)
    with z.open(name) as fp:
        data = fp.read(budget + 1)
    if len(data) > budget:
        raise AttachLimit(name)
    return data


def extract_docx_text(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if len(z.namelist()) > ATTACH_ENTRY_LIMIT:
            raise AttachLimit("docx")
        raw = zip_read_bytes(z, "word/document.xml", 8 * 1024 * 1024)
        if raw is None:
            return ""
        xml = raw.decode("utf-8", "ignore")
    xml = re.sub(r"<w:tab[^>]*/>", "\t", xml)
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<[^>]+>", "", xml)
    return _html.unescape(xml).strip()


def extract_xlsx_text(data):
    def _clean(s):
        return _html.unescape(re.sub(r"<[^>]+>", "", s)).strip()

    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = set(z.namelist())
        if len(names) > ATTACH_ENTRY_LIMIT:
            raise AttachLimit("xlsx")
        shared = []
        if "xl/sharedStrings.xml" in names:
            sraw = zip_read_bytes(z, "xl/sharedStrings.xml", 8 * 1024 * 1024)
            sx = (sraw or b"").decode("utf-8", "ignore")
            shared = [_clean(si) for si in re.findall(r"<si>(.*?)</si>", sx, re.S)]
        out = []
        sheets = sorted(n for n in names
                        if n.startswith("xl/worksheets/sheet") and n.endswith(".xml"))[:8]
        for sn in sheets:
            raw = zip_read_bytes(z, sn, 6 * 1024 * 1024)
            if raw is None:
                continue
            sx = raw.decode("utf-8", "ignore")
            for row in re.findall(r"<row[^>]*>(.*?)</row>", sx, re.S):
                cells = []
                for cm in re.finditer(r"<c\b([^>]*)>(.*?)</c>", row, re.S):
                    attrs, inner = cm.group(1), cm.group(2)
                    t_m = re.search(r'\bt="(\w+)"', attrs)
                    t = t_m.group(1) if t_m else None
                    vm = re.search(r"<v>(.*?)</v>", inner, re.S)
                    if vm is not None:
                        val = _html.unescape(vm.group(1)).strip()
                        if t == "s":
                            try:
                                val = shared[int(val)]
                            except Exception:
                                pass
                        cells.append(val)
                    else:
                        tm2 = re.search(r"<t[^>]*>(.*?)</t>", inner, re.S)
                        cells.append(_clean(tm2.group(1)) if tm2 is not None else "")
                if any(cells):
                    out.append("\t".join(cells))
    return "\n".join(out).strip()


# ---------- 统一入口 ----------
def read_attach_text(path):
    """返回 (text, err); 不支持/超限/无文字返回人话 err。"""
    ext = os.path.splitext(path)[1].lower()
    fail = tr("att.read_fail")
    try:
        size = os.path.getsize(path)
    except OSError:
        return "", fail
    if size > RAW_SIZE_LIMIT:
        return "", tr("att.too_large")
    if ext in (".doc", ".xls", ".ppt", ".rtf"):
        return "", tr("att.unsupported")
    try:
        with open(path, "rb") as af:
            data = af.read()
    except OSError:
        return "", fail
    try:
        if ext == ".pdf":
            text = extract_pdf_text(data)
        elif ext == ".docx":
            text = extract_docx_text(data)
        elif ext == ".xlsx":
            text = extract_xlsx_text(data)
        else:
            text = None
            for enc in ("utf-8-sig", "gbk"):
                try:
                    text = data.decode(enc)
                    break
                except Exception:
                    text = None
            if text is None:
                return "", fail
    except AttachLimit:
        return "", tr("att.bomb")
    except Exception:
        return "", fail
    text = (text or "").strip()
    if not text:
        return "", tr("att.no_text")
    return text, ""
