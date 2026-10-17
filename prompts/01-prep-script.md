# Prompt 1: Build `prep.py` + `test_prep.py`

Read `prompts/00-spec.md` in full first. Sections B and F are your contract.

## Task
Create `briefly/scripts/prep.py` and `briefly/scripts/test_prep.py`.

## Hard constraints
- **Python 3.9 compatible.** No `match`, no `X | Y` type unions, no `str.removeprefix` without a fallback. Use only the stdlib (`argparse, json, re, zipfile, subprocess, shutil, html, pathlib, sys, os`). `faster_whisper` is imported lazily, only inside the whisper function.
- One file and plain functions. No classes unless one is clearly smaller. Target **≤ 300 lines** for prep.py.
- The stdout/stderr/exit-code behaviour must match spec B exactly. Other tools parse stdout.
- Internally, every parser returns the same shape: a list of `(start_seconds_or_None, speaker_or_None, text)`. One shared function then does merging, formatting, dedupe, header, splitting and writing. Never write per-format formatting code.
- Run subprocess calls with an argument list (no `shell=True`) and a timeout.
- Wrap each input in its own try/except, so one broken file doesn't stop a batch.

## Tests (`test_prep.py`)
Plain `assert` with a `if __name__ == "__main__":` runner that prints `OK` and creates its own fixtures in a `tempfile.TemporaryDirectory()`. Cover:
1. VTT with `<v Alice>` tags → speakers preserved, `[mm:ss]` format.
2. YouTube-style rolling VTT (each line repeated in the next cue, with `<c>` and `<00:00:01.200>` inline tags) → no duplicate lines, and output is at least 40% smaller than the input.
3. SRT → cue numbers are gone, and cues merge into ≤ 30 s paragraphs.
4. Whisper JSON segments, both the dict form and the list form.
5. `.docx` built in the test with `zipfile` (a minimal `word/document.xml`) → text extracted.
6. Plain `.txt` with no timestamps → passthrough, `duration` null.
7. Splitting: a synthetic transcript at about 3× `--part-tokens 1000` → 3 or more parts, each ≤ 1000 est tokens, no lines lost (concatenating the parts equals the transcript body).
8. Cache: a second run reports `source: "cache"`, and `--force` bypasses it.
9. Batch: a directory with one good file and one corrupt `.docx` → two JSON lines, the corrupt one has `error` set, exit code 0.
10. A media file with no subs and no faster-whisper → `error` contains "pip install faster-whisper". Skip this test if ffprobe is missing **or** faster_whisper is installed. Generate the file with `ffmpeg -f lavfi -i sine=d=2 x.wav` when ffmpeg exists.
11. Duration ≥ 1 h → `[h:mm:ss]` timestamps.

Call the script through `subprocess` with `sys.executable`, so the tests exercise the real CLI.

## Done when
- `python3 briefly/scripts/test_prep.py` prints `OK` on Python 3.9.
- `python3 briefly/scripts/prep.py --help` works with faster-whisper NOT installed.
- Reply with: the line counts of both files, the test output, and any spec ambiguity you resolved (with your choice).
