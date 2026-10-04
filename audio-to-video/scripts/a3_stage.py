#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""جدول النوافذ لمقطع صوتي: نافذة الفيديو مخفية (NONE) طول المقطع — الشاشة كلها للرسم.
   python3 a3_stage.py <work>

⛔ لا تشغّل 18_stage_from_scenes.py من الأساس على مقطع صوتي: يملأ الفجوات بـFULL،
   فيطلع الإطار الساكن (لون سادة) مكان الوجه. هذا السكربت بديله.
ويكتب formats.json لكل مشهد بـScenes.tsx (NONE) — عشان فواحص الأساس تقرأ نفس الصيغة."""
import re, io, json, sys, os
W = os.path.abspath(sys.argv[1]) + "/"
json.dump([{"s": 0, "e": 999, "m": "NONE"}], open(W + "stage.json", "w"), indent=1)

names = []
if os.path.exists(W + "Scenes.tsx"):
    s = io.open(W + "Scenes.tsx", encoding="utf-8").read()
    names = re.findall(r"const (\w+) = \(\{t", s) + re.findall(r"<(\w+) t=\{t\} A=\{", s)
names = [n for n in dict.fromkeys(names) if n not in ("Scenes", "VideoOverlay")]
json.dump({n: "NONE" for n in names}, open(W + "formats.json", "w"), ensure_ascii=False, indent=1)

# الانتقالات ما تُشتق آلياً هنا: المشاهد تتبدّل كل ثوانٍ، وووش مع كل تبديلة يتجاوز حاكم المؤثرات.
# الأصوات تُختار بيدك عند لحظاتها (sfx.md بالأساس). نضمن بس إن المفاتيح موجودة.
sp = W + "sfx.json"
d = json.load(open(sp)) if os.path.exists(sp) else {"outro": 0}
d.setdefault("outro", 0); d.setdefault("whoosh_up", []); d.setdefault("whoosh_down", [])
json.dump(d, open(sp, "w"), ensure_ascii=False, indent=1)
print(f"✅ stage.json — الشاشة كلها للرسم · {len(names)} مشهد بـformats.json")
