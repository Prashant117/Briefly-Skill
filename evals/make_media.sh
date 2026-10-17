#!/bin/sh
# Generate a tiny local video with embedded text subtitles. No network access.
set -eu
script_dir=$(CDPATH= cd "$(dirname "$0")" && pwd)
output=${1:-$script_dir/fixtures/media-sample.mp4}
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
python3 - "$script_dir/fixtures/team-sync.vtt" "$scratch/captions.srt" <<'PY'
from pathlib import Path
import re
import sys

source = Path(sys.argv[1]).read_text()
excerpts = [("Alice", "Today we need", 0, 5),
            ("Priya", "I'll send", 6, 11),
            ("Mina", "I'll validate", 12, 18)]
cues = []
for i, (speaker, prefix, start, end) in enumerate(excerpts, 1):
    matches = [line for line in re.findall(r"<v " + speaker + r">([^\n]+)", source)
               if line.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError("Expected exactly one fixture line for " + speaker)
    cues.append("{}\n00:00:{:02d},000 --> 00:00:{:02d},000\n{}: {}\n".format(
        i, start, end, speaker, matches[0]))
Path(sys.argv[2]).write_text("\n".join(cues))
PY
ffmpeg -v error -n -f lavfi -i 'color=c=black:s=160x90:r=1:d=20' \
  -f lavfi -i 'sine=frequency=440:duration=20' -i "$scratch/captions.srt" \
  -map 0:v -map 1:a -map 2:s -c:v mpeg4 -c:a aac -c:s mov_text -t 20 "$output"
