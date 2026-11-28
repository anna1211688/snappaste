# -*- coding: utf-8 -*-
"""单实例守卫测试。"""
from kivo.platform.single_instance import (
    SingleInstanceGuard, ERROR_ALREADY_EXISTS, _default_backend,
)


def test_first_instance_allowed():
    g = SingleInstanceGuard(backend=lambda n: (1, 0))
    assert g.acquire() is True
    assert g._handle == 1


def test_already_exists_blocked():
    g = SingleInstanceGuard(backend=lambda n: (1, ERROR_ALREADY_EXISTS))
    assert g.acquire() is False


def test_zero_handle_allowed():
    g = SingleInstanceGuard(backend=lambda n: (0, 0))
    assert g.acquire() is True


def test_backend_exception_allowed():
    def boom(n):
        raise RuntimeError("x")
    g = SingleInstanceGuard(backend=boom)
    assert g.acquire() is True


def test_default_backend_non_windows():
    # 当前测试环境是 Linux，默认后端应放行
    handle, err = _default_backend("any")
    assert handle == 1 and err == 0
    assert SingleInstanceGuard().acquire() is True


def test_handle_kept_after_acquire():
    g = SingleInstanceGuard(backend=lambda n: (4242, 0))
    g.acquire()
    assert g._handle == 4242
