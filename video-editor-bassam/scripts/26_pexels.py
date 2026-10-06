#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""26_pexels.py — صور ومقاطع حقيقية من Pexels، حسب حاجة كل لحظة. مشترك بين المهارتين
(video-editor-bassam و audio-to-video).

  python3 26_pexels.py key <المفتاح>                 # يحفظ مفتاح الواجهة بمجلد بياناته — مرة وحدة
  python3 26_pexels.py <work> plan                   # جمل الكلام بتوقيتها + قالب pexels.json + تفضيله
  python3 26_pexels.py <work> fetch [--per 3] [--force]   # يبحث وينزّل المرشّحين لكل لحظة ← <work>/pexels/
  python3 26_pexels.py <work> sheet                  # ورقة مرشّحين: صف لكل لحظة ← <work>/pexels_sheet_<N>.jpg
  python3 26_pexels.py <work> pick <لحظة> <رقم> [--dur 3.5] [--from 0]
                                                     # يعتمد مرشّحاً ← <work>/assets/px_<لحظة>.jpg|mp4
  python3 26_pexels.py <work> credits                # أصحاب المعتمد فقط ← <work>/credits.txt

<work>/pexels.json — تكتبه أنت بعد ما تقرأ الكلام (اللحظات الملموسة بس: شخص · مكان · غرض · موقف):
  {"moments": [
    {"id": "hook", "at": 0.0, "say": "…", "query": "crowded city street night", "kind": "video", "dur": 2.5},
    {"id": "m1",   "at": 7.4, "say": "…", "query": "tired office worker desk", "kind": "photo"},
    {"id": "m2",   "at": 15.0, "say": "…", "query": "ocean waves aerial",      "kind": "both"}]}
  kind = photo | video | both — **حسب الحاجة**: حركة أو مكان حيّ ← video · شي ثابت أو شخص ← photo · ما تدري ← both.
  query بالإنجليزي، ٢–٤ كلمات تصف المشهد لا الفكرة («empty wallet» مو «poverty»).

المفتاح: متغيّر البيئة PEXELS_API_KEY، وإلا <مجلد بياناته>/pexels.json. ⛔ لا ينحفظ بمجلد الشغل ولا بمجلد المهارة.
تفضيله: prefs.stockMedia بـprofile.json ← auto (حسب الحاجة — الافتراضي) · photos · videos · none.
"""
import sys, os, json, shutil, subprocess, urllib.request, urllib.parse, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _paths

API = os.environ.get("PEXELS_API_BASE", "https://api.pexels.com").rstrip("/")
UA = "video-editor-bassam/1.0"
PER = 3            # مرشّحين لكل لحظة
MAX_DUR = 15       # أطول مقطع نفضّله (ث) — الأطول يدخل بس لو ما كفى العدد
PHOTO_H = 2200     # ارتفاع الصورة المطلوب (يكفي 1920 مع حركة كاميرا بطيئة)
RL = {}            # آخر قراءة لحد الطلبات


def die(msg, code=2):
    print(msg); sys.exit(code)


def arg(k, d=None):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv and sys.argv.index(k) + 1 < len(sys.argv) else d


# ── المفتاح ─────────────────────────────────────────────
def key_path():
    return _paths.data("pexels.json")


def get_key():
    k = os.environ.get("PEXELS_API_KEY", "").strip()
    if k:
        return k
    p = key_path()
    if os.path.exists(p):
        k = json.load(open(p, encoding="utf-8")).get("key", "").strip()
    if not k:
        die("⛔ ما فيه مفتاح للجلب التلقائي. احفظه مرة وحدة: python3 26_pexels.py key <المفتاح>\n"
            "   (أو متغيّر البيئة PEXELS_API_KEY). بدونه: ابحث يدوياً من مصادر مجانية (القاعدة ٨٥).", 5)
    return k


def save_key(k):
    _paths.ensure()
    p = key_path()
    json.dump({"key": k.strip()}, open(p, "w", encoding="utf-8"))
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass
    print(f"✅ المفتاح محفوظ بـ{p} (خارج المهارة ومجلدات الشغل)")


# ── الشبكة ─────────────────────────────────────────────
def get_json(path, params):
    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": get_key(), "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            RL["left"] = r.headers.get("X-Ratelimit-Remaining")
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            die("⛔ المفتاح مرفوض (401/403) — تأكد منه أو احفظه من جديد: 26_pexels.py key <المفتاح>", 5)
        if e.code == 429:
            die("⛔ وصلنا حد الطلبات بالساعة — انتظر شوي ثم أعد fetch (اللي نزل ما ينعاد).", 6)
        die(f"⛔ خطأ من الخادم {e.code} على {path}", 4)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        die(f"⛔ ما قدرت أوصل للخادم ({getattr(e, 'reason', e)}) — الشبكة مقفلة أو ما فيه نت.\n"
            "   بالسحابة: لازم api.pexels.com و images.pexels.com و videos.pexels.com مسموحة بإعدادات البيئة.", 4)


def download(url, dst):
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        return True
    tmp = dst + ".part"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
            shutil.copyfileobj(r, f)
        os.replace(tmp, dst)
        return True
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        if os.path.exists(tmp):
            os.remove(tmp)
        print(f"   ⚠️ فشل تنزيل {os.path.basename(dst)}: {getattr(e, 'reason', e)}")
        return False


# ── الاختيار ───────────────────────────────────────────
def sized(url, h):
    """صورة Pexels بارتفاع محدد (الرابط الأصلي يقبل معاملات الحجم) — بدل الأصل الثقيل."""
    return url + ("&" if "?" in url else "?") + f"auto=compress&cs=tinysrgb&h={h}"


def search_photos(q, n):
    d = get_json("/v1/search", {"query": q, "orientation": "portrait", "per_page": 15})
    out = []
    for p in d.get("photos", []):
        if p.get("height", 0) < p.get("width", 1):
            continue
        out.append({"type": "photo", "pid": p["id"], "w": p["width"], "h": p["height"],
                    "url": sized(p["src"]["original"], PHOTO_H), "page": p.get("url", ""),
                    "by": p.get("photographer", ""), "by_url": p.get("photographer_url", ""),
                    "alt": p.get("alt", "")})
        if len(out) >= n:
            break
    return out


def best_file(files):
    """ملف عمودي بأعلى ارتفاع ≤ 1920 (لا 4K — ثقيل بلا فايدة)، وإلا أصغر الأعلى."""
    port = [f for f in files if f.get("height") and f.get("width") and f["height"] >= f["width"] and f.get("link")]
    if not port:
        return None
    under = [f for f in port if f["height"] <= 1920]
    return max(under, key=lambda f: f["height"]) if under else min(port, key=lambda f: f["height"])


def search_videos(q, n):
    d = get_json("/videos/search", {"query": q, "orientation": "portrait", "per_page": 15})
    short, long_ = [], []
    for v in d.get("videos", []):
        f = best_file(v.get("video_files", []))
        if not f:
            continue
        c = {"type": "video", "pid": v["id"], "w": f["width"], "h": f["height"], "dur": v.get("duration", 0),
             "url": f["link"], "page": v.get("url", ""), "by": v.get("user", {}).get("name", ""),
             "by_url": v.get("user", {}).get("url", ""), "thumb": v.get("image", "")}
        (short if c["dur"] <= MAX_DUR else long_).append(c)
    return (short + long_)[:n]


def pref_mode(W):
    prof = _paths.load("profile.json", {})
    t = os.path.join(W, "theme.json")
    if not prof and os.path.exists(t):
        prof = json.load(open(t, encoding="utf-8"))
    pr = prof.get("prefs", {})
    m = pr.get("stockMedia")
    if m is None:
        m = "none" if pr.get("stockImages") is False else "auto"
    return m


def kinds_for(kind, mode):
    want = {"photo": ["photo"], "video": ["video"], "both": ["photo", "video"]}.get(kind, ["photo", "video"])
    if mode == "photos":
        return ["photo"]
    if mode == "videos":
        return ["video"]
    return want


# ── الأوامر ────────────────────────────────────────────
def load_plan(W):
    p = os.path.join(W, "pexels.json")
    if not os.path.exists(p):
        die("⛔ ما فيه <work>/pexels.json — اكتب اللحظات أولاً (شوف: 26_pexels.py <work> plan)")
    ms = json.load(open(p, encoding="utf-8")).get("moments", [])
    ids = [m.get("id") for m in ms]
    if not ms or any(not i for i in ids) or len(set(ids)) != len(ids):
        die("⛔ pexels.json: كل لحظة لازم لها id فريد و query")
    for m in ms:
        if not m.get("query"):
            die(f"⛔ اللحظة {m['id']} بلا query")
    return ms


def found_path(W):
    return os.path.join(W, "pexels_found.json")


def cmd_plan(W):
    mode = pref_mode(W)
    print(f"تفضيله: stockMedia = {mode}" + ("  ⛔ ما يبي صوراً خارجية — لا تجلب" if mode == "none" else ""))
    cp = os.path.join(W, "caps.json")
    if os.path.exists(cp):
        for i, c in enumerate(json.load(open(cp, encoding="utf-8"))["cards"]):
            print(f"  {i:>2}  [{c['s']:6.2f}]  " + " ".join(w["t"] for w in c["w"]))
    print('\nاكتب <work>/pexels.json — اللحظات الملموسة بس، و"hook" للحظة الافتتاح لو تحتاج صورة أو مقطعاً:')
    print(json.dumps({"moments": [{"id": "hook", "at": 0.0, "say": "…", "query": "…", "kind": "video", "dur": 2.5},
                                  {"id": "m1", "at": 7.4, "say": "…", "query": "…", "kind": "photo"}]},
                     ensure_ascii=False, indent=1))


def cmd_fetch(W):
    mode = pref_mode(W)
    if mode == "none":
        die("⛔ تفضيله «لا صور خارجية» (prefs.stockMedia = none) — ما جلبت شي.", 0)
    per = int(arg("--per", PER))
    force = "--force" in sys.argv
    ms = load_plan(W)
    fp = found_path(W)
    found = json.load(open(fp, encoding="utf-8")) if os.path.exists(fp) else {}
    D = os.path.join(W, "pexels"); os.makedirs(D, exist_ok=True)
    total = 0
    for m in ms:
        ks = kinds_for(m.get("kind", "both"), mode)
        old = found.get(m["id"])
        if old and not force and old.get("query") == m["query"] and old.get("kinds") == ks and \
                all(os.path.exists(os.path.join(W, c["file"])) for c in old["cands"]):
            print(f"• {m['id']}: موجود من قبل ({len(old['cands'])} مرشّح) — --force لإعادة البحث")
            total += len(old["cands"]); continue
        cands = []
        if ks == ["photo", "video"]:
            # «الاثنين»: نوزّع العدد — الصور أولاً ثم المقاطع، ونكمّل من النوع الثاني لو نقص
            ph = search_photos(m["query"], per); vd = search_videos(m["query"], per)
            half = (per + 1) // 2
            cands = ph[:half] + vd[:per - half]
            pool = ph[half:] + vd[per - half:]
            cands += pool[:per - len(cands)]
        elif ks == ["photo"]:
            cands = search_photos(m["query"], per)
        else:
            cands = search_videos(m["query"], per)
        kept = []
        for n, c in enumerate(cands, 1):
            ext = "jpg" if c["type"] == "photo" else "mp4"
            rel = os.path.join("pexels", f"{m['id']}_{n}.{ext}")
            if download(c["url"], os.path.join(W, rel)):
                c.update({"n": n, "file": rel}); kept.append(c)
        found[m["id"]] = {"query": m["query"], "kinds": ks, "at": m.get("at"), "say": m.get("say", ""),
                          "dur": m.get("dur"), "cands": kept}
        desc = " · ".join(f"{c['n']}:" + ("صورة" if c["type"] == "photo" else f"مقطع {c['dur']}ث") for c in kept)
        print(f"• {m['id']} «{m['query']}» ← {len(kept)} مرشّح  {desc}" + ("  ⚠️ ولا نتيجة — غيّر الكلمات" if not kept else ""))
        total += len(kept)
        json.dump(found, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(found, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n✅ {total} مرشّح لـ{len(ms)} لحظة بـ{D}" + (f" · باقي من حد الطلبات: {RL['left']}" if RL.get("left") else ""))
    print("التالي: 26_pexels.py <work> sheet ← اقرأ الورقة وافحص قيوده (القاعدة ١١) قبل pick.")


def thumb(W, c, out, label):
    src = os.path.join(W, c["file"])
    vf = ("scale=216:384:force_original_aspect_ratio=increase,crop=216:384,"
          f"drawtext=text='{label}':x=6:y=6:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=5")
    pre = ["-ss", "1"] if c["type"] == "video" and c.get("dur", 0) > 1.5 else []
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *pre, "-i", src, "-frames:v", "1", "-vf", vf, out], capture_output=True)
    if r.returncode != 0:   # بعض نسخ ffmpeg بلا drawtext — بدون عنوان أحسن من لا شي
        subprocess.run(["ffmpeg", "-v", "error", "-y", *pre, "-i", src, "-frames:v", "1",
                        "-vf", "scale=216:384:force_original_aspect_ratio=increase,crop=216:384", out], capture_output=True)
    return os.path.exists(out)


def cmd_sheet(W):
    fp = found_path(W)
    if not os.path.exists(fp):
        die("⛔ ما فيه مرشّحين — شغّل fetch أولاً")
    found = json.load(open(fp, encoding="utf-8"))
    per = max((len(v["cands"]) for v in found.values()), default=0)
    if not per:
        die("⛔ ولا مرشّح نزل")
    T = os.path.join(W, ".pxsheet"); shutil.rmtree(T, ignore_errors=True); os.makedirs(T)
    rows = []
    for mid, v in found.items():
        if not v["cands"]:
            continue
        tiles = []
        for c in v["cands"]:
            lab = f"{mid} {c['n']} " + ("IMG" if c["type"] == "photo" else f"VID {c.get('dur', 0)}s")
            o = os.path.join(T, f"{mid}_{c['n']}.png")
            if thumb(W, c, o, lab):
                tiles.append(o)
        while len(tiles) < per:   # صف ناقص يتعبّى بفراغ أسود عشان الأعمدة تتطابق
            o = os.path.join(T, f"{mid}_pad{len(tiles)}.png")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=216x384", "-frames:v", "1", o])
            tiles.append(o)
        ro = os.path.join(T, f"row_{mid}.png")
        if per == 1:
            shutil.copy(tiles[0], ro)
        else:
            ins = sum((["-i", t] for t in tiles), [])
            subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", f"hstack=inputs={len(tiles)}", ro])
        rows.append(ro)
    outs = []
    for k in range(0, len(rows), 4):   # ٤ صفوف بالورقة — أطول من كذا تصغر بالقراءة وتضيع التفاصيل
        part = rows[k:k + 4]; o = os.path.join(W, f"pexels_sheet_{k // 4 + 1}.jpg")
        if len(part) == 1:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", part[0], o])
        else:
            ins = sum((["-i", r] for r in part), [])
            subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", f"vstack=inputs={len(part)}", o])
        outs.append(o)
    shutil.rmtree(T, ignore_errors=True)
    for o in outs:
        print(f"✅ {o}")
    print("كل صف = لحظة، والرقم بالزاوية = رقم المرشّح للـpick. اعرض الورقة عليه لو يبي يختار بنفسه.")


def cmd_pick(W):
    if len(sys.argv) < 5:
        die("الاستعمال: 26_pexels.py <work> pick <لحظة> <رقم> [--dur ث] [--from ث]")
    mid, n = sys.argv[3], int(sys.argv[4])
    found = json.load(open(found_path(W), encoding="utf-8")) if os.path.exists(found_path(W)) else {}
    v = found.get(mid) or die(f"⛔ ما فيه لحظة اسمها {mid} بـpexels_found.json")
    c = next((x for x in v["cands"] if x["n"] == n), None) or die(f"⛔ اللحظة {mid} ما فيها مرشّح رقم {n}")
    A = os.path.join(W, "assets"); os.makedirs(A, exist_ok=True)
    src = os.path.join(W, c["file"])
    for ext in ("jpg", "mp4"):   # اختيار جديد لنفس اللحظة يشيل القديم (لو تغيّر النوع)
        old = os.path.join(A, f"px_{mid}.{ext}")
        if os.path.exists(old):
            os.remove(old)
    if c["type"] == "photo":
        name = f"px_{mid}.jpg"; shutil.copy(src, os.path.join(A, name))
        info = f"صورة {c['w']}×{c['h']}"
    else:
        name = f"px_{mid}.mp4"
        dur = float(arg("--dur", v.get("dur") or 3.0)); start = float(arg("--from", 0))
        dur = max(0.5, min(dur, max(0.5, c.get("dur", dur) - start)))
        # ⛔ بلا صوت (-an) — صوته هو الوحيد بالمقطع. 1080×1920 · 30 إطار · أوسمة 709 مثل باقي الرندر.
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start}", "-i", src, "-t", f"{dur}", "-an",
                            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p",
                            "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                            "-movflags", "+faststart", os.path.join(A, name)], capture_output=True, text=True)
        if r.returncode != 0:
            die(f"⛔ فشل قص المقطع: {r.stderr.strip()[-300:]}", 4)
        info = f"مقطع {dur:.1f}ث من {start:.1f}ث · بلا صوت"
    pp = os.path.join(W, "pexels_picks.json")
    picks = json.load(open(pp, encoding="utf-8")) if os.path.exists(pp) else {}
    picks[mid] = {"file": name, "type": c["type"], "n": n, "pid": c["pid"], "page": c["page"],
                  "by": c["by"], "by_url": c["by_url"], "at": v.get("at")}
    json.dump(picks, open(pp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    tag = "<Img src={staticFile('%s')}/>" % name if c["type"] == "photo" else \
          "<OffthreadVideo muted src={staticFile('%s')}/>  (داخل <Sequence from={…}>)" % name
    print(f"✅ {mid} ← {name}  ({info})\n   بالمشهد: {tag}")
    print("   ⛔ افحص قيوده على كل فريم من الجزء المستعمل (القاعدة ١١) — مو عيّنة.")


def cmd_credits(W):
    pp = os.path.join(W, "pexels_picks.json")
    if not os.path.exists(pp):
        die("ما فيه مصادر معتمدة — ما يحتاج ملف أصحاب.", 0)
    picks = json.load(open(pp, encoding="utf-8"))
    lines, seen = ["Photos & videos from Pexels (pexels.com):"], set()
    for mid, p in picks.items():
        if p["page"] in seen:   # نفس المصدر بلحظتين يُذكر مرة
            continue
        seen.add(p["page"])
        kind = "Photo" if p["type"] == "photo" else "Video"
        lines.append(f"- {kind} by {p['by']} — {p['page']}")
    open(os.path.join(W, "credits.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines)); print(f"\n✅ {os.path.join(W, 'credits.txt')} — اختياري بوصف المنشور (مو شرط بالرخصة).")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "key":
        save_key(sys.argv[2]); sys.exit(0)
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(2)
    W = os.path.abspath(sys.argv[1])
    if not os.path.isdir(W):
        die(f"⛔ مجلد الشغل مو موجود: {W}")
    {"plan": cmd_plan, "fetch": cmd_fetch, "sheet": cmd_sheet, "pick": cmd_pick,
     "credits": cmd_credits}.get(sys.argv[2], lambda _W: (print(__doc__), sys.exit(2)))(W)
