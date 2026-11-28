# -*- coding: utf-8 -*-
"""项目工作台管理 (projects.json): 模板、加载校验、CRUD、笔记/待办/链接、限额。"""
from __future__ import annotations

import time

from . import data
from .i18n import tr
from .paths import PROJECTS_PATH

PROJECT_MAX = 30
NOTES_MAX = 20000
TODO_MAX = 100
LINK_MAX = 50

PROJECT_TEMPLATES = [
    {"key": "office", "title": "通用办公写作",
     "desc": "覆盖总结、写作、润色与翻译，结论先行、结构清晰。",
     "todos": ["明确本次写作的目标与读者", "列出提纲，结论先行", "完成初稿并润色校对"]},
    {"key": "data", "title": "数据分析与可视化",
     "desc": "读取表格与数据、核验统计口径，输出分析结论与图表建议。",
     "todos": ["确认数据来源与统计口径", "清洗数据并核对关键指标", "输出结论与可视化建议"]},
    {"key": "meeting", "title": "会议与信息复盘",
     "desc": "会议纪要、决策与待办提取，跨聊天和文档追踪进展。",
     "todos": ["整理会议纪要与关键决策", "拆解待办并指定负责人和时间", "跟进各项进展直到关闭"]},
    {"key": "market", "title": "市场调研与竞品分析",
     "desc": "行业与竞品调研，统一维度对比，输出结论与建议。",
     "todos": ["确定调研范围与对比维度", "收集行业与竞品资料", "统一维度对比并输出建议"]}]


def _sanitize(c):
    if not isinstance(c, dict) or not isinstance(c.get("id"), int):
        return None
    title = str(c.get("title") or tr("project.untitled"))[:80]
    notes = str(c.get("notes") or "")[:NOTES_MAX]

    todos, seen_t = [], set()
    for t in c.get("todos") if isinstance(c.get("todos"), list) else []:
        if not isinstance(t, dict):
            continue
        tx = str(t.get("text") or "").strip()[:500]
        if not tx or tx in seen_t:
            continue
        seen_t.add(tx)
        todos.append({"text": tx, "done": bool(t.get("done"))})
        if len(todos) >= TODO_MAX:
            break

    links, seen_l = [], set()
    for l in c.get("links") if isinstance(c.get("links"), list) else []:
        if not isinstance(l, dict):
            continue
        kind = l.get("kind") if l.get("kind") in ("file", "url") else "url"
        name = str(l.get("name") or "").strip()[:200]
        path = str(l.get("path") or "").strip()[:1000]
        if not path or path in seen_l:
            continue
        seen_l.add(path)
        links.append({"name": name or path, "path": path, "kind": kind})
        if len(links) >= LINK_MAX:
            break

    tpl = c.get("template")
    return {"id": c["id"], "title": title, "notes": notes, "todos": todos,
            "links": links, "created": c.get("created") or 0,
            "updated": c.get("updated") or 0, "pin": 1 if c.get("pin") else 0,
            "template": tpl if isinstance(tpl, str) and tpl else ""}


class ProjectStore:
    def __init__(self, path: str = PROJECTS_PATH):
        self.path = path
        self.projects = self._load()

    def _load(self):
        raw = data.load_json(self.path, [], validator=lambda o: isinstance(o, list))
        out = []
        for c in raw:
            s = _sanitize(c)
            if s is not None:
                out.append(s)
        return out[:PROJECT_MAX]

    def save(self):
        data.save_json(self.path, self.projects[:PROJECT_MAX], where="save-projects")

    def get(self, pid):
        return next((p for p in self.projects if p["id"] == pid), None)

    def create(self, template_key=None, title=None):
        tpl = next((t for t in PROJECT_TEMPLATES if t["key"] == template_key), None)
        pid = int(time.time() * 1000)
        if tpl is not None:
            k = tpl["key"]
            title = title or tr(f"tpl.{k}.title")
            tpl_todos = [tr(f"tpl.{k}.todo{i}") for i in (1, 2, 3)]
            todos = [{"text": x, "done": False} for x in tpl_todos]
            note, tpl_key = tr(f"tpl.{k}.desc"), k
        else:
            title = title or tr("project.untitled")
            todos, note, tpl_key = [], "", ""
        now = time.time()
        project = {"id": pid, "title": title[:80], "notes": note, "todos": todos,
                   "links": [], "created": now, "updated": now, "pin": 0,
                   "template": tpl_key}
        self.projects.insert(0, project)
        del self.projects[PROJECT_MAX:]
        self.save()
        return project

    def delete(self, pid):
        before = len(self.projects)
        self.projects = [p for p in self.projects if p["id"] != pid]
        if len(self.projects) != before:
            self.save()

    # ---------- 笔记 ----------
    def set_notes(self, pid, notes):
        p = self.get(pid)
        if p is not None:
            p["notes"] = notes.strip()[:NOTES_MAX]
            p["updated"] = time.time()
            self.save()

    # ---------- 待办 ----------
    def add_todo(self, pid, text):
        p = self.get(pid)
        if p is None or len(p["todos"]) >= TODO_MAX:
            return False
        text = text.strip()[:500]
        if not text:
            return False
        p["todos"].append({"text": text, "done": False})
        p["updated"] = time.time()
        self.save()
        return True

    def toggle_todo(self, pid, i):
        p = self.get(pid)
        if p is not None and 0 <= i < len(p["todos"]):
            p["todos"][i]["done"] = not p["todos"][i]["done"]
            self.save()

    def remove_todo(self, pid, i):
        p = self.get(pid)
        if p is not None and 0 <= i < len(p["todos"]):
            del p["todos"][i]
            self.save()

    # ---------- 链接 ----------
    def add_link(self, pid, name, path, kind="url"):
        p = self.get(pid)
        if p is None or len(p["links"]) >= LINK_MAX:
            return False
        path = path.strip()[:1000]
        if not path:
            return False
        p["links"].append({"name": name.strip()[:200] or path,
                           "path": path, "kind": kind if kind in ("file", "url") else "url"})
        self.save()
        return True

    def remove_link(self, pid, i):
        p = self.get(pid)
        if p is not None and 0 <= i < len(p["links"]):
            del p["links"][i]
            self.save()
