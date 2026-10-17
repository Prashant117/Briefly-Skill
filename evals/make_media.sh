#!/bin/sh
# Generate a tiny local video with embedded text subtitles. No network access.
set -eu
output=${1:-evals/fixtures/media-sample.mp4}
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
cat > "$scratch/captions.srt" <<'SRT'
1
00:00:00,000 --> 00:00:05,000
Alice: We need to settle the launch timing and support plan.

2
00:00:06,000 --> 00:00:11,000
Priya: I'll send the final launch copy by Thursday.

3
00:00:12,000 --> 00:00:18,000
Mina: I'll validate the invoice totals against the test orders.
SRT
ffmpeg -v error -n -f lavfi -i 'color=c=black:s=160x90:r=1:d=20' \
  -f lavfi -i 'sine=frequency=440:duration=20' -i "$scratch/captions.srt" \
  -map 0:v -map 1:a -map 2:s -c:v mpeg4 -c:a aac -c:s mov_text -t 20 "$output"
