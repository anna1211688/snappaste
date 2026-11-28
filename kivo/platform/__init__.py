# -*- coding: utf-8 -*-
"""平台隔离层: Windows 专属系统能力在此集中，非 Windows 安全降级。"""
import sys

IS_WINDOWS = sys.platform == "win32"
