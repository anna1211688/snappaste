# -*- coding: utf-8 -*-
"""更新模块单元测试 (不联网)。"""
from kivo.core import update


class FakeConfig:
    def __init__(self, values=None):
        self._values = values or {}

    def get(self, section, key, fallback=None):
        return self._values.get((section, key), fallback)


class TestVersion:
    def test_release_tuple(self):
        assert update.ver_tuple("v1.7.1") == (1, 7, 1, 1)

    def test_beta_tuple(self):
        t = update.ver_tuple("1.8.0-beta1")
        assert t[-2:] == (0, 1)

    def test_beta_before_release(self):
        assert update.ver_tuple("1.8.0-beta1") < update.ver_tuple("1.8.0")

    def test_patch_version(self):
        assert update.is_newer("1.5.0.1", "1.5.0")

    def test_is_newer_true_false(self):
        assert update.is_newer("1.8.0", "1.7.2")
        assert not update.is_newer("1.7.2", "1.8.0")
        assert not update.is_newer("1.8.0", "1.8.0")


class TestAssets:
    def test_prefers_same_version(self):
        data = {"tag_name": "v1.8.0", "assets": [
            {"name": "KIVO-Setup-1.7.0.exe", "browser_download_url": "old"},
            {"name": "KIVO-Setup-1.8.0.exe", "browser_download_url": "new"}]}
        url, name = update.pick_setup_asset(data)
        assert name == "KIVO-Setup-1.8.0.exe"
        assert url == "new"

    def test_fallback_first_match(self):
        data = {"tag_name": "v1.8.0", "assets": [
            {"name": "KIVO-Setup-1.7.0.exe", "browser_download_url": "only"}]}
        url, name = update.pick_setup_asset(data)
        assert name == "KIVO-Setup-1.7.0.exe"

    def test_no_asset(self):
        assert update.pick_setup_asset({"assets": []}) == ("", "")

    def test_pick_sig(self):
        data = {"assets": [{"name": "KIVO-Setup-1.8.0.exe.sig",
                            "browser_download_url": "sigu"}]}
        assert update.pick_sig_asset(data, "KIVO-Setup-1.8.0.exe") == "sigu"

    def test_pick_sig_missing(self):
        assert update.pick_sig_asset({"assets": []}, "x.exe") == ""


class TestSignature:
    def test_empty_sig_invalid(self):
        assert update.verify_update_sig("n", "v", "h", "") is False

    def test_garbage_sig_invalid(self):
        import base64
        bad = base64.b64encode(b"short").decode()
        assert update.verify_update_sig("n", "v", "h", bad) is False


class TestTagAndMirror:
    def test_tag_from_location(self):
        assert update.tag_from_location(
            "https://github.com/x/releases/tag/v1.8.0?a=1") == "v1.8.0"

    def test_tag_bad_location(self):
        assert update.tag_from_location("https://other/x") == ""

    def test_mirror_rewrite(self):
        cfg = FakeConfig({("Network", "UpdateMirror"): "https://mirror.test"})
        c = update.UpdateClient(cfg)
        out = c.mirror_rewrite("https://api.github.com/repos/x/releases/latest")
        assert out == "https://mirror.test/repos/x/releases/latest"

    def test_mirror_no_mirror_passthrough(self):
        c = update.UpdateClient(FakeConfig())
        assert c.mirror_rewrite("https://api.github.com/x") == "https://api.github.com/x"

    def test_mirror_non_github_passthrough(self):
        cfg = FakeConfig({("Network", "UpdateMirror"): "https://m.test"})
        c = update.UpdateClient(cfg)
        assert c.mirror_rewrite("https://other.com/x") == "https://other.com/x"
