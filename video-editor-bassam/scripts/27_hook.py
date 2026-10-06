#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""27_hook.py — الهوك (أول ٣ ثواني) وصورة الغلاف. مشترك بين المهارتين — المرجع: references/hook.md

  python3 27_hook.py <work> plan                    # أول الجمل بتوقيتها + الأنماط + آخر أنماطه (لا تكرّرها)
  python3 27_hook.py <work> check                   # قبل الرندر: hook.json · النمط ما يتكرر · أول كابشن ≤ 0.5 ث
  python3 27_hook.py <work> check --out <فيديو.mp4> # بعد الرندر: يقيس الصورة نفسها بأول ٣ ثواني
  python3 27_hook.py <work> cover <فيديو.mp4> [--t 1.2]   # صورة الغلاف ← <work>/cover.jpg
  python3 27_hook.py <work> log --name "<اسم المقطع>"     # بعد التسليم: يسجّل النمط بسجلّه (hooks.json)

<work>/hook.json — تكتبه أنت بعد ما يختار الهوك:
  {"pattern": "question", "text": "ليش ٩٠٪ يفشلون بأول سنة؟", "s": 0.0, "e": 2.4,
   "visual": "px_hook.mp4", "cover_t": 1.2, "cover_title": "ليش ٩٠٪ يفشلون؟"}
يخرج بالرمز 3 لو فشل الفحص."""
import sys, os, json, subprocess, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _paths

PATTERNS = {
    "question": "سؤال صادم بخط ضخم يملأ الشاشة",
    "number":   "رقم ضخم يعدّ قدامه",
    "visual":   "صورة أو مقطع حقيقي ملء الشاشة بتقريب سريع",
    "promise":  "وعد بالنتيجة («بـ٣٠ ثانية بتعرف…»)",
    "contrast": "قبل وبعد · خطأ وصح — شاشة مقسومة",
    "myth":     "الخطأ الشائع مشطوب («لا تسوي كذا»)",
    "story":    "من نص القصة — أقوى لحظة أولاً ثم نرجع",
    "behind":   "الكلمة ورا الشخص (فيديو فيه وجه بس — 11_behind_text.js)",
}
FIRST_CAP = 0.5    # أول كابشن (نفس 08_safe_check)
FIRST_SEEN = 0.3   # أول عنصر بالصورة
HOOK_MAX = 3.5     # الهوك يخلص قبل كذا
WIN = 3.0          # نقيس أول ٣ ثواني
FPS = 30
MOVE_MIN = 0.15  # ٪ من البكسلات — أقل تغيّر مقبول بكل ثانية من أول ٣


def die(msg, code=2):
    print(msg); sys.exit(code)


def arg(k, d=None):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv and sys.argv.index(k) + 1 < len(sys.argv) else d


def history():
    return _paths.load("hooks.json", [])


def audio_only(W):
    return os.path.exists(os.path.join(W, "audio_only.json"))


def cmd_plan(W):
    cp = os.path.join(W, "caps.json")
    if os.path.exists(cp):
        print("أول الكلام — الهوك من هنا (أو من أقوى جملة بالمقطع لو نمطه «story»):")
        for i, c in enumerate(json.load(open(cp, encoding="utf-8"))["cards"][:4]):
            print(f"  {i}  [{c['s']:5.2f}–{c['e']:5.2f}]  " + " ".join(w["t"] for w in c["w"]))
    print("\nالأنماط:")
    for k, v in PATTERNS.items():
        if k == "behind" and audio_only(W):
            continue
        print(f"  {k:<9} {v}")
    h = history()[-3:]
    if h:
        print("\nآخر أنماطه (⛔ لا تعيد آخر واحد):  " + " ← ".join(f"{x['pattern']} ({x['name']})" for x in h))
    print("\nاعرض عليه ٢–٣ صيغ للهوك من كلامه، ثم اكتب <work>/hook.json (الصيغة بأول السكربت).")


def frames(video, dur, w=180, h=320):
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-t", f"{dur}", "-i", video,
                          "-vf", f"fps={FPS},scale={w}:{h},format=gray", "-f", "rawvideo", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)


def check_video(video):
    """الصورة نفسها: شي يبان بأول 0.3 ث · لا بداية من السواد · حدث بكل ثانية من أول ٣.
    يمسك البداية الجامدة والفاضية والتلاشي من الأسود — جودة الفكرة نفسها شغل hook.md وعينك."""
    f = frames(video, WIN)
    if len(f) < FPS:
        return [f"❌ الفيديو أقصر من ثانية ({len(f)} إطار)"], []
    errs, info = [], []
    k0 = min(int(FIRST_SEEN * FPS), len(f) - 1)
    if f[0].mean() < 14 and f[0].std() < 6:
        errs.append("❌ يبدأ من السواد — الإطار الأول لازم فيه شي (لا تلاشي من الأسود)")
    if f[k0].std() < 8:
        errs.append(f"❌ عند {FIRST_SEEN} ث الشاشة سادة — أول عنصر لازم يبان قبلها")
    # «تغيّر» = نسبة البكسلات اللي تغيّرت بقوة (> 30) بين إطار واللي قبله بـ0.2 ث — دخول كلمة · قطع · صورة.
    # الحد 0.15٪ ≈ كلمة واحدة بحجم الكابشن تدخل. الشاشة الجامدة = صفر.
    lag = int(0.2 * FPS)
    for sec in range(int(WIN)):
        a, b = max(lag, sec * FPS), min(len(f), (sec + 1) * FPS)
        best = max(((abs(f[i] - f[i - lag]) > 30).mean() * 100 for i in range(a, b)), default=0)
        info.append(f"{sec}–{sec + 1} ث: {best:.2f}٪")
        if best < MOVE_MIN:
            errs.append(f"❌ الثانية {sec}–{sec + 1} جامدة (أقوى تغيّر {best:.2f}٪ < {MOVE_MIN}٪) — زِد حدثاً: كلمة تدخل · قطع · رقم")
    return errs, info


def cmd_check(W):
    out = arg("--out")
    errs = []
    hp = os.path.join(W, "hook.json")
    if not os.path.exists(hp):
        die("❌ ما فيه <work>/hook.json — صمّم الهوك أولاً (27_hook.py <work> plan)", 3)
    hk = json.load(open(hp, encoding="utf-8"))
    pat = hk.get("pattern")
    if pat not in PATTERNS:
        errs.append(f"❌ النمط «{pat}» مو من الأنماط: {' · '.join(PATTERNS)}")
    if pat == "behind" and audio_only(W):
        errs.append("❌ «behind» يحتاج وجهاً — المقطع صوت بس")
    h = [x for x in history() if x.get("name") != arg("--name")]
    if h and h[-1].get("pattern") == pat:
        errs.append(f"❌ نفس نمط آخر مقطع ({h[-1]['name']}: {pat}) — غيّره")
    if not hk.get("text"):
        errs.append("❌ hook.json بلا text — جملة الهوك نفسها")
    e = float(hk.get("e", 0))
    if e <= 0 or e > HOOK_MAX:
        errs.append(f"❌ الهوك ينتهي عند {e} ث — لازم بين 0 و{HOOK_MAX}")
    vis = hk.get("visual")
    if vis and not os.path.exists(os.path.join(W, "assets", vis)):
        errs.append(f"❌ صورة الهوك {vis} مو موجودة بـ<work>/assets")
    cp = os.path.join(W, "caps.json")
    if os.path.exists(cp):
        cards = json.load(open(cp, encoding="utf-8"))["cards"]
        if cards and cards[0]["s"] > FIRST_CAP:
            errs.append(f"❌ أول كابشن عند {cards[0]['s']:.2f} ث — لازم قبل {FIRST_CAP} (قص السكتة الأولى)")
    if out:
        if not os.path.exists(out):
            die(f"❌ الفيديو مو موجود: {out}", 3)
        ve, info = check_video(out)
        errs += ve
        print("التغيّر بأول ٣ ثواني — " + " · ".join(info))
    for x in errs:
        print(x)
    if errs:
        print(f"❌ الهوك ما عدّى ({len(errs)})"); sys.exit(3)
    print(f"✅ الهوك سليم — {pat}: «{hk.get('text', '')}»")


def cmd_cover(W):
    if len(sys.argv) < 4:
        die("الاستعمال: 27_hook.py <work> cover <فيديو.mp4> [--t ث]")
    video = sys.argv[3]
    hp = os.path.join(W, "hook.json")
    hk = json.load(open(hp, encoding="utf-8")) if os.path.exists(hp) else {}
    t = arg("--t") or hk.get("cover_t")
    if t is None:
        # أوضح إطار بالهوك: أعلى طاقة حواف (النص الضخم والصورة الواضحة) بين 0.3 ونهاية الهوك
        import numpy as np
        end = min(float(hk.get("e", WIN)) or WIN, WIN)
        f = frames(video, end, 180, 320)
        lo = int(FIRST_SEEN * FPS)
        if len(f) <= lo:
            t = 0.0
        else:
            sc = [np.abs(np.diff(x, axis=0)).mean() + np.abs(np.diff(x, axis=1)).mean() for x in f[lo:]]
            t = (lo + int(np.argmax(sc))) / FPS
    t = float(t)
    o = os.path.join(W, "cover.jpg")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", "-q:v", "2", o],
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(o):
        die(f"❌ ما قدرت أطلّع الغلاف: {r.stderr.strip()[-200:]}", 3)
    print(f"✅ {o}  (عند {t:.2f} ث)")
    print("   الشبكة بحسابه تقصّ الغلاف لـ3:4 — الكلام المهم لازم بين y 240 و1680. اعرضه عليه.")


def cmd_log(W):
    name = arg("--name") or os.path.basename(W)
    hp = os.path.join(W, "hook.json")
    if not os.path.exists(hp):
        die("❌ ما فيه hook.json", 3)
    hk = json.load(open(hp, encoding="utf-8"))
    _paths.ensure()
    h = [x for x in history() if x.get("name") != name]
    h.append({"name": name, "date": datetime.date.today().isoformat(), "pattern": hk.get("pattern"),
              "text": hk.get("text", "")})
    json.dump(h, open(_paths.data("hooks.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"✅ سُجّل: {name} ← {hk.get('pattern')}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(2)
    W = os.path.abspath(sys.argv[1])
    if not os.path.isdir(W):
        die(f"⛔ مجلد الشغل مو موجود: {W}")
    {"plan": cmd_plan, "check": cmd_check, "cover": cmd_cover, "log": cmd_log}.get(
        sys.argv[2], lambda _W: (print(__doc__), sys.exit(2)))(W)
