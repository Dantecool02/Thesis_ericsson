#!/bin/bash
# usage: render.sh <deck.pptx> <outdir>   -> outdir/deck.pdf + outdir/png/*.png  (via Keynote)
IN="$1"; OUT="$2"; rm -rf "$OUT"; mkdir -p "$OUT/png"
osascript <<OSA
tell application "Keynote"
  launch
  set theDoc to open POSIX file "$IN"
  delay 3
  export theDoc to POSIX file "$OUT/deck.pdf" as PDF with properties {PDF image quality:Best}
  export theDoc to POSIX file "$OUT/png" as slide images with properties {image format:PNG}
  close theDoc saving no
end tell
OSA
echo "rendered: $(ls "$OUT/png" | wc -l | tr -d ' ') slides -> $OUT"
