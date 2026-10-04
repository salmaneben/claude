#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""يحدّد مكان مهارة video-editor-bassam (المهارة الأساس) ويطبع مسارها.
   python3 _base.py            → يطبع المسار، أو يخرج بالرمز 2 لو ما لقيها

هذه المهارة لا تنسخ أدوات المهارة الأساس — تستعملها من مكانها، فأي تحديث لها يصل هنا تلقائياً.
ترتيب البحث: متغيّر البيئة VEB_SKILL ← مجلد شقيق ← مجلدات المهارات المعروفة (بعمق محدود)."""
import os, sys, glob

NAME = "video-editor-bassam"

def _ok(d):
    p = os.path.join(d, "SKILL.md")
    if not os.path.isfile(p) or not os.path.isdir(os.path.join(d, "scripts")):
        return False
    with open(p, encoding="utf-8") as f:
        head = f.read(600)
    return f"name: {NAME}" in head

def find():
    env = os.environ.get("VEB_SKILL")
    if env and _ok(env):
        return os.path.abspath(env)
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cands = [os.path.join(os.path.dirname(here), NAME)]
    home = os.path.expanduser("~")
    roots = [os.path.join(home, ".claude"), os.path.join(home, "Library", "Application Support", "Claude"),
             os.environ.get("APPDATA", ""), os.environ.get("LOCALAPPDATA", ""), "/mnt/skills", "/mnt/user-data"]
    for r in filter(None, roots):
        if not os.path.isdir(r):
            continue
        for depth in range(0, 6):
            pat = os.path.join(r, *(["*"] * depth), NAME)
            cands += glob.glob(pat)
    for c in cands:
        if _ok(c):
            return os.path.abspath(c)
    return None

if __name__ == "__main__":
    b = find()
    if not b:
        sys.exit("⛔ ما لقيت مهارة video-editor-bassam — هذه المهارة تحتاجها مثبّتة. "
                 "لو مكانها غير معتاد: VEB_SKILL=<المسار>")
    print(b)
