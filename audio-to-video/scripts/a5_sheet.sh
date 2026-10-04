#!/bin/bash
# ورقة لقطات من أي فيديو (نسخة الأساس تقرأ ad-final.mp4 بس — هذي تقرأ رندر التجربة كمان).
#   bash a5_sheet.sh <الفيديو.mp4> <sheet.jpg> <t1> <t2> ...   — الأوقات بالثواني من بداية الملف نفسه
set -e
V="$1"; OUT="$2"; shift 2
TMP="$(mktemp -d)"; i=0; IN=""
for t in "$@"; do
  i=$((i+1)); f="$TMP/$(printf %02d $i).jpg"
  ffmpeg -v error -ss "$t" -i "$V" -frames:v 1 -vf "scale=300:-1" -y "$f"
  ffmpeg -v error -i "$f" -vf "drawtext=text='${t}s':x=8:y=8:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=5" -y "$f.l.jpg" 2>/dev/null || cp "$f" "$f.l.jpg"
  IN="$IN -i $f.l.jpg"
done
ffmpeg -v error $IN -filter_complex "hstack=inputs=$i" -y "$OUT"
rm -rf "$TMP"; echo "✅ $OUT  ($i لقطة)"
