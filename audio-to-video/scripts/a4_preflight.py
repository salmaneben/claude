#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""الفواحص كلها لمقطع صوتي — بديل 22_preflight.py بالأساس.
   python3 a4_preflight.py <work> [--name "<اسم المقطع>"] [--out <المسلَّم.mp4>] [--gap 4]

قبل الرندر: a3_stage · 19 (فراغ وجمود) · 05b المؤثرات · 13 التكرار · 16 التغطية (حد أقسى: 4 ث)
بعد الرندر (--out): 25 الومضات · 20 الصوت كما دخل · المدة
متخطّى عمداً (يخص الوجه أو الفيديو المصوّر): 12 الوجه · 21 اللون · 23 النظرة · 24 القطع · معدل البت.
يخرج بالرمز 3 لو أي فاحص فشل."""
import sys, os, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _base

if len(sys.argv) < 2:
    print(__doc__); sys.exit(2)
W = os.path.abspath(sys.argv[1]); HERE = os.path.dirname(os.path.abspath(__file__))
B = _base.find() or sys.exit("⛔ ما لقيت المهارة الأساس"); K = os.path.join(B, "scripts")
arg = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
NAME, OUT, GAP = arg("--name", os.path.basename(W)), arg("--out"), arg("--gap", "4")
_mp = os.path.join(W, "mode.json")
MODE = json.load(open(_mp)).get("mode", "full") if os.path.exists(_mp) else "full"
HAS_SFX = os.path.exists(os.path.join(W, "sfx.wav")) or os.path.exists(os.path.join(W, "sfx_events.json"))

def run(label, cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=W)
    out = (r.stdout + r.stderr).strip().splitlines()
    last = next((l for l in reversed(out) if l.strip()), "")
    return (label, r.returncode == 0, last[:110], "\n".join(out))

rows = [run("a3 جدول النوافذ", [sys.executable, os.path.join(HERE, "a3_stage.py"), W])]
if MODE == "full":
    _st = os.path.join(W, "style.json")
    if os.path.exists(_st) and json.load(open(_st)).get("style") in ("collage", "documentary", "board", "vox") \
            and os.path.exists(os.path.join(W, "sfx_events.json")):
        subprocess.run([sys.executable, os.path.join(B, "styles", "collage", "mix_sfx.py"), W], capture_output=True, cwd=W)
    rows.append(run("19 فراغ · جمود", [sys.executable, os.path.join(K, "19_scene_audit.py"), W]))
    rows.append(run("13 تكرار الآليات", ["node", os.path.join(K, "13_repeat_check.js"), W, NAME]))
    rows.append(run(f"16 التغطية (≤{GAP} ث)", ["node", os.path.join(K, "16_coverage_check.js"), W, GAP]))
else:
    print(f"الوضع: {MODE} — بلا مشاهد (كابشن فوق الخلفية الحيّة)")
if HAS_SFX and os.path.exists(os.path.join(W, "sfx.json")):
    rows.append(run("05b حاكم المؤثرات", [sys.executable, os.path.join(K, "05b_sfx_audit.py"), W]))

if OUT:
    rows.append(run("25 ومضات بيضاء", [sys.executable, os.path.join(K, "25_flash_check.py"), W, OUT]))
    if os.path.exists(os.path.join(W, "voice.wav")):
        rows.append(run("20 الصوت كما دخل", [sys.executable, os.path.join(K, "20_voice_check.py"), W, OUT]))
    d = lambda f: float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                                       capture_output=True, text=True).stdout.strip() or 0)
    caps = json.load(open(os.path.join(W, "caps.json")))["total"]
    o = d(OUT); ok = o >= caps - 0.2
    rows.append(("المدة", ok, f"الناتج {o:.2f} ث · الكلام {caps:.2f} ث" + ("" if ok else " — الناتج أقصر"), ""))

w = max(len(r[0]) for r in rows)
print(f"\n{'الفاحص':<{w}}  الحالة  الخلاصة"); print("─" * (w + 60))
for label, ok, last, _ in rows:
    print(f"{label:<{w}}  {'✅' if ok else '❌'}      {last}")
fails = [r for r in rows if not r[1]]
if fails:
    print(f"\n❌ {len(fails)} فاحص فشل — التفاصيل:")
    for label, _, _, full in fails:
        print(f"\n── {label} ──\n{full[-1500:]}")
    sys.exit(3)
print("\n✅ كل الفواحص بصفر" + (" — جاهز للتسليم" if OUT else " — جاهز للرندر"))
