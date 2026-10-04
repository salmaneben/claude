#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""خطة القص للصوت.   python3 a2_cut.py <work> [--keep-pauses]

الافتراضي: نفس قص المهارة الأساس (01_cut_plan.py) — يشيل السكتات الطويلة.
--keep-pauses: ما يشيل شي. للتعليق الصوتي المنتج مسبقاً (فيه موسيقى، أو وقفات مقصودة،
أو صوت مولّد بالذكاء الاصطناعي وتوقيته مضبوط) — القص فيه يكسر الإيقاع ويقطع الموسيقى."""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _base

W = os.path.abspath(sys.argv[1])
if "--keep-pauses" in sys.argv:
    src = os.path.join(W, "src.mov")
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                               capture_output=True, text=True).stdout.strip())
    json.dump({"keep": [[0.0, dur]], "total": dur, "src_dur": dur}, open(os.path.join(W, "cut.json"), "w"), indent=1)
    print(f"✅ بلا قص — المدة كما هي {dur:.2f} ث")
else:
    B = _base.find() or sys.exit("⛔ ما لقيت المهارة الأساس")
    sys.exit(subprocess.call([sys.executable, os.path.join(B, "scripts", "01_cut_plan.py"), W]))
