#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""يحوّل الملف الصوتي إلى مصدر تفهمه أدوات المهارة الأساس.
   python3 a1_prepare.py <الملف الصوتي> <work>

ليش: أدوات video-editor-bassam كلها تقرأ <work>/src.mov (فيديو + صوت). بدل ما نعدّلها،
نبني src.mov من إطار ساكن بلون الخلفية + صوته كما هو. الإطار ما يظهر أبداً بالناتج:
جدول النوافذ (a3_stage.py) يخلّي نافذة الفيديو NONE طول المقطع، فالشاشة كلها للرسم.

⛔ صوته يُنسخ بلا أي معالجة (القاعدة ١٩ بالأساس) — فك الضغط لـPCM فقط، بلا ضغط ولا تنقية ولا تعديل علو.
⛔ لا يكتب فوق ملفه الأصلي أبداً — المخرج داخل <work> فقط."""
import sys, os, json, subprocess

if len(sys.argv) < 3:
    print(__doc__); sys.exit(2)
SRC = os.path.abspath(sys.argv[1]); W = os.path.abspath(sys.argv[2])
if not os.path.isfile(SRC):
    sys.exit(f"⛔ الملف مو موجود: {SRC}")
os.makedirs(W, exist_ok=True)
OUT = os.path.join(W, "src.mov")
if os.path.abspath(OUT) == SRC:
    sys.exit("⛔ الملف الصوتي نفسه اسمه src.mov داخل مجلد الشغل — انقله أو سمّه باسم ثاني أولاً")

def probe(kind):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", kind, "-show_entries",
                        "stream=codec_type", "-of", "csv=p=0", SRC], capture_output=True, text=True)
    return [x for x in r.stdout.split() if x]

if not probe("a"):
    sys.exit("⛔ الملف ما فيه صوت — أرسل ملفاً صوتياً (mp3 · wav · m4a · aac · ogg · flac) أو فيديو فيه صوت")
if probe("v") and not SRC.lower().endswith((".mp3", ".m4a", ".aac", ".ogg", ".flac", ".wav", ".opus")):
    print("ℹ️  الملف فيه صورة — بنستعمل صوته بس. (لو هو فيديو يتكلم فيه شخص، المهارة الأساس أنسب له.)")

dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", SRC],
                           capture_output=True, text=True).stdout.strip() or 0)
if dur < 3:
    sys.exit(f"⛔ الصوت قصير جداً ({dur:.1f} ث)")

theme_p = os.path.join(W, "theme.json")
bg = "#101418"
if os.path.exists(theme_p):
    th = json.load(open(theme_p, encoding="utf-8"))
    bg = th.get("bg", bg)
    th["noZoom"] = True          # ما فيه وجه يُقرَّب عليه
    json.dump(th, open(theme_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
else:
    print("⚠️  ما فيه theme.json بمجلد الشغل بعد — انسخ profile.json له قبل الرندر (القالب يرفض بدونه)")

rc = subprocess.call(["ffmpeg", "-v", "error",
    "-f", "lavfi", "-i", f"color=c={bg.replace('#', '0x')}:s=1080x1920:r=30",
    "-i", SRC, "-map", "0:v", "-map", "1:a:0", "-shortest",
    "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage", "-crf", "30", "-pix_fmt", "yuv420p",
    "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
    "-c:a", "pcm_s24le", "-ar", "48000", "-ac", "2", "-y", OUT])
if rc:
    sys.exit(rc)

json.dump({"audioOnly": True, "source": SRC, "duration": round(dur, 3)},
          open(os.path.join(W, "audio_only.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if not os.path.exists(os.path.join(W, "mode.json")):
    json.dump({"mode": "full"}, open(os.path.join(W, "mode.json"), "w"))
m, s = divmod(int(round(dur)), 60)
print(f"✅ الصوت جاهز — المدة {m}:{s:02d} · {OUT}")
