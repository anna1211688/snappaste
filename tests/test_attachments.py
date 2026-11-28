# -*- coding: utf-8 -*-
"""附件解析单元测试 (不联网)。"""
import io
import os
import zipfile

from kivo.core import attachments


def make_docx(path, paragraphs):
    paras = "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs)
    xml = ('<?xml version="1.0"?><w:document xmlns:w="w">' + paras + "</w:document>")
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("word/document.xml", xml)


def make_xlsx(path, rows, shared=None):
    shared = shared or []
    ss = "".join(f"<si><t>{s}</t></si>" for s in shared)
    sheet_rows = []
    for r in rows:
        cells = "".join(
            f'<c r="A1" t="s"><v>{v}</v></c>' if isinstance(v, int)
            else f'<c><v>{v}</v></c>' for v in r)
        sheet_rows.append(f"<row>{cells}</row>")
    sheet = ('<?xml version="1.0"?><worksheet xmlns="s">' + "".join(sheet_rows) + "</worksheet>")
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("xl/sharedStrings.xml",
                   '<?xml version="1.0"?><sst xmlns="s">' + ss + "</sst>")
        z.writestr("xl/worksheets/sheet1.xml", sheet)


class TestReadEntry:
    def test_plain_text(self, tmp_path):
        p = tmp_path / "a.txt"
        p.write_text("你好 world", encoding="utf-8")
        text, err = attachments.read_attach_text(str(p))
        assert text == "你好 world" and err == ""

    def test_old_format_rejected(self, tmp_path):
        p = tmp_path / "a.doc"
        p.write_text("x")
        text, err = attachments.read_attach_text(str(p))
        assert text == "" and "docx" in err

    def test_missing_file(self, tmp_path):
        text, err = attachments.read_attach_text(str(tmp_path / "nope.txt"))
        assert text == "" and err

    def test_empty_text_file(self, tmp_path):
        p = tmp_path / "a.txt"
        p.write_text("   ", encoding="utf-8")
        text, err = attachments.read_attach_text(str(p))
        assert text == "" and err

    def test_oversize(self, tmp_path):
        p = tmp_path / "big.txt"
        with open(p, "wb") as f:
            f.write(b"x" * (attachments.RAW_SIZE_LIMIT + 1))
        text, err = attachments.read_attach_text(str(p))
        assert "12MB" in err


class TestDocxXlsx:
    def test_docx_extract(self, tmp_path):
        p = tmp_path / "a.docx"
        make_docx(str(p), ["第一段", "第二段"])
        text, err = attachments.read_attach_text(str(p))
        assert "第一段" in text and "第二段" in text

    def test_xlsx_extract_shared(self, tmp_path):
        p = tmp_path / "a.xlsx"
        make_xlsx(str(p), [[0]], shared=["苹果"])
        text, err = attachments.read_attach_text(str(p))
        assert "苹果" in text


class TestPdfHelpers:
    def test_decode_utf16(self):
        assert attachments.pdf_decode_text(b"\xfe\xff\x00h\x00i") == "hi"

    def test_unescape_newline(self):
        assert attachments.pdf_unescape_literal(b"a\\nb") == b"a\nb"

    def test_unescape_octal(self):
        assert attachments.pdf_unescape_literal(b"\\101") == b"A"

    def test_unescape_parens(self):
        assert attachments.pdf_unescape_literal(b"\\(\\)") == b"()"
