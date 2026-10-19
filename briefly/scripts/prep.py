#!/usr/bin/env python3
"""Normalize local transcripts; optionally extract subtitles or transcribe media."""
import argparse
from collections import Counter
import contextlib
import html
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import warnings
import xml.etree.ElementTree as ET
import zipfile

TEXT = {".txt", ".md", ".vtt", ".srt", ".json", ".docx"}
MEDIA = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".mp3", ".m4a",
         ".wav", ".aac", ".flac", ".ogg"}
CLOCK = r"\d+:\d{2}(?::\d{2})?(?:[.,]\d+)?"
STAMP = re.compile(r"^\s*[\[(]?(" + CLOCK + r")[\])]?(?:\s+|$)(.*)$")
HEADING = re.compile(r"^\s*(.{0,60}?)\s*[\[(]?(" + CLOCK + r")[\])]?\s*$")
SIZES = {"tiny": "75 MB", "base": "145 MB", "small": "460 MB", "medium": "1.5 GB"}


def seconds(value):
    if isinstance(value, str) and ":" in value:
        fields = value.replace(",", ".").split(":")
        value = sum(float(n) * 60 ** i for i, n in enumerate(reversed(fields)))
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError("Times must be finite, nonnegative seconds")
    return value


def clock(value, hours=False):
    value = int(value)
    return ("{}:{:02d}:{:02d}".format(value // 3600, value // 60 % 60, value % 60)
            if hours else "{:02d}:{:02d}".format(value // 60, value % 60))


def lines(raw, metadata, start=None, end=None, speaker=None, markup=True):
    for line in raw.splitlines():
        spans = re.split(r"(<v(?:\.[^\s>]+)*\s+[^>]+>|</v>)", line) if markup else [line]
        for span in spans:
            voice = re.fullmatch(r"<v(?:\.[^\s>]+)*\s+([^>]+)>", span) if markup else None
            if voice or (markup and span == "</v>"):
                speaker = html.unescape(voice[1]).strip() if voice else None
                continue
            text = " ".join((html.unescape(re.sub(r"<[^>]*>", "", span)) if markup else span).split())
            name = re.match(r"^([^:]{1,60}):\s+(.+)$", text)
            if name:
                speaker, text = name[1].strip(), name[2]
            if text:
                metadata["ends"].append(end)
                yield start, speaker, text


def subtitles(raw, metadata):
    segments, duration = [], 0
    raw = raw.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    for block in re.split(r"\n\s*\n", raw.strip()):
        if re.match(r"^(WEBVTT|NOTE|STYLE|REGION)(?:\s|$)", block):
            continue
        cue = block.splitlines()
        timing = next((i for i, line in enumerate(cue) if "-->" in line), None)
        if timing is None:
            continue
        match = re.fullmatch(r"\s*(" + CLOCK + r")\s+-->\s+(" + CLOCK + r")(?:\s+.*)?", cue[timing])
        if not match:
            raise ValueError("Invalid subtitle timing: " + cue[timing])
        start, end = seconds(match[1]), seconds(match[2])
        if end < start:
            raise ValueError("Subtitle ends before it starts")
        duration = max(duration, end)
        segments.extend(lines("\n".join(cue[timing + 1:]), metadata, start, end))
    if not segments:
        raise ValueError("No subtitle cues with text found")
    metadata.update(duration=duration, source="subtitles")
    return segments


def heading(line):
    """Teams/Otter "Name   0:03" or Meet "00:05:00" on its own line; text follows."""
    match = HEADING.match(line)
    words = match[1].split() if match else []
    if match and len(words) <= 4 and not re.search(r"[.,;:!?]$", match[1]) \
            and not any(w[0].islower() for w in words):
        return seconds(match[2]), match[1].strip("[]") or None
    return None


def plain(raw, metadata):
    segments, duration, carried = [], None, (None, None)
    for line in raw.splitlines():
        header = heading(line)
        if header:
            carried = header
            duration = max(duration or 0, header[0])
            continue
        match = STAMP.match(line)
        start, speaker = (seconds(match[1]), None) if match else carried
        if match:
            carried = (None, None)
            duration = max(duration or 0, start)
        segments.extend(lines(match[2] if match else line, metadata, start, start, speaker, markup=False))
    metadata["duration"] = duration
    return segments


def json_segments(data, metadata):
    items = data.get("segments") if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise ValueError("JSON must be a segment list or an object with segments")
    segments, duration = [], 0
    for item in items:
        try:
            start, end = seconds(item["start"]), seconds(item["end"])
            text = item["text"]
        except (KeyError, TypeError):
            raise ValueError("Each JSON segment needs start, end and text") from None
        if end < start or not isinstance(text, str):
            raise ValueError("Invalid segment end or text")
        speaker = item.get("speaker")
        if speaker is not None and not isinstance(speaker, str):
            raise ValueError("Segment speaker must be a string or null")
        duration = max(duration, end)
        segments.extend(lines(text, metadata, start, end, speaker))
    metadata["duration"] = duration
    return segments


def missing():
    return ("No subtitles found and local transcription is not set up. Run: python3 {} --setup-whisper "
            "(one-time, ~560 MB) — or provide a transcript file.").format(Path(__file__).resolve())


def venv_python():
    root = Path(os.environ.get("BRIEFLY_WHISPER_VENV") or "~/.cache/briefly/whisper-venv").expanduser()
    return root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def backend():
    # Third-party model messages must never contaminate the JSON protocol.
    with contextlib.redirect_stdout(sys.stderr):
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            return None
    return WhisperModel


def transcribe(path, model, WhisperModel):
    """Run faster-whisper; return Whisper-style JSON for json_segments()."""
    segments, report = [], 60
    print("Loading Whisper model '{}'".format(model), file=sys.stderr)
    # numpy on macOS warns "overflow encountered in matmul"; the transcript is still correct.
    with contextlib.redirect_stdout(sys.stderr), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        engine = WhisperModel(model, device="auto", compute_type="int8")
        stream, info = engine.transcribe(str(path), vad_filter=True, beam_size=1)
        total = seconds(info.duration)
        for segment in stream:
            start, end = seconds(segment.start), seconds(segment.end)
            segments.append(dict(start=start, end=end, text=segment.text))
            if end >= report:
                print("Transcribing {}: {} / {} ({}%)".format(
                    path.name, clock(end, total >= 3600), clock(total, total >= 3600),
                    min(100, int(end * 100 / total)) if total else 0), file=sys.stderr)
                report = (int(end) // 60 + 1) * 60
    return dict(segments=segments, duration=total)


def worker(media_path, model, out):
    """Hidden --whisper-worker mode, run by the isolated venv's Python."""
    try:
        engine = backend()
        data = transcribe(Path(media_path), model, engine) if engine else dict(error=missing())
    except Exception as exc:
        data = dict(error=str(exc) or type(exc).__name__)
    Path(out).write_text(json.dumps(data), encoding="utf-8")
    return 1 if "error" in data else 0


def whisper(path, model, metadata):
    engine, python = backend(), venv_python()
    if engine:
        data = transcribe(path, model, engine)
    elif python.exists():
        print("Using local Whisper environment: " + str(python.parent.parent), file=sys.stderr)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "whisper.json"
            # No timeout: long recordings take many minutes on CPU. stderr passes through for progress.
            done = subprocess.run([str(python), str(Path(__file__).resolve()), "--whisper-worker", str(path),
                                   "--model", model, "--worker-out", str(out)], stdout=sys.stderr)
            try:
                data = json.loads(out.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                raise ValueError("Local transcription failed (worker exit {})".format(done.returncode)) from None
        if "error" in data:
            raise ValueError(data["error"])
    else:
        raise ValueError(missing())
    segments = json_segments(data, metadata)
    metadata.update(duration=max(metadata["duration"], seconds(data["duration"])), source="whisper")
    return segments


def setup(model):
    python = venv_python()
    root, step = python.parent.parent, "Creating the Whisper environment"
    try:
        if not python.exists():
            print("{}: {}".format(step, root), file=sys.stderr)
            subprocess.run([sys.executable, "-m", "venv", str(root)], stdout=sys.stderr, check=True)
        if subprocess.run([str(python), "-c", "import faster_whisper"],
                          stdout=sys.stderr, stderr=subprocess.DEVNULL).returncode:
            step = "Installing faster-whisper"
            print(step + "…", file=sys.stderr)
            subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "pip", "faster-whisper"],
                           stdout=sys.stderr, check=True)
        step = "Downloading Whisper model '{}'".format(model)
        print("{} ({}one time)…".format(step, "~" + SIZES[model] + ", " if model in SIZES else ""), file=sys.stderr)
        subprocess.run([str(python), "-c", "import sys; from faster_whisper import WhisperModel; "
                        "WhisperModel(sys.argv[1], device='cpu', compute_type='int8')", model],
                       stdout=sys.stderr, check=True)
        error = None
    except (OSError, subprocess.CalledProcessError) as exc:
        error = "{} failed: {}".format(step, exc)
        print("Error: " + error, file=sys.stderr)
    print(json.dumps(dict(setup="error" if error else "ok", python=str(python), model=model, error=error)))
    return 1 if error else 0


def media(path, model, metadata):
    if shutil.which("ffprobe") and shutil.which("ffmpeg"):
        try:
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "s:0", "-show_entries",
                 "stream=index:format=duration", "-of", "json", str(path)],
                capture_output=True, text=True, timeout=30, check=True)
            info = json.loads(probe.stdout)
            if info.get("streams"):
                print("Extracting subtitles: " + path.name, file=sys.stderr)
                result = subprocess.run(
                    ["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:s:0", "-f", "srt", "-"],
                    capture_output=True, text=True, timeout=300, check=True)
                segments = subtitles(result.stdout, metadata)
                try:
                    metadata["duration"] = max(metadata["duration"], seconds(info["format"]["duration"]))
                except (KeyError, ValueError, TypeError):
                    pass
                return segments
        except (subprocess.SubprocessError, ValueError) as exc:
            print("Subtitle extraction unavailable: " + str(exc), file=sys.stderr)
    metadata["ends"].clear()
    return whisper(path, model, metadata)


def decode(data):
    # Old/Windows subtitle files are often UTF-16 or cp1252, not UTF-8.
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")


def parse(path, model, metadata):
    suffix = path.suffix.lower()
    if suffix in MEDIA:
        return media(path, model, metadata)
    if suffix == ".docx":
        with zipfile.ZipFile(path) as doc:
            root = ET.fromstring(doc.read("word/document.xml"))
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        raw = "\n".join("".join(node.text or "" if node.tag == ns + "t" else " "
                                 for node in p.iter() if node.tag in {ns + "t", ns + "tab", ns + "br"})
                        for p in root.iter(ns + "p"))
    else:
        raw = decode(path.read_bytes())
    if suffix in {".vtt", ".srt"}:
        return subtitles(raw, metadata)
    return json_segments(json.loads(raw), metadata) if suffix == ".json" else plain(raw, metadata)


def normalize(segments, metadata, filename):
    duration = metadata["duration"]
    paragraphs, previous = [], None
    for (start, speaker, text), end in zip(segments, metadata["ends"]):
        if metadata["source"] == "subtitles" and text == previous:
            continue
        previous = text
        if (paragraphs and start is not None and paragraphs[-1][0] is not None
                and speaker == paragraphs[-1][1] and 0 <= start - paragraphs[-1][0] < 30
                and (end or start) - paragraphs[-1][0] < 30):
            paragraphs[-1][2] += " " + text
        else:
            paragraphs.append([start, speaker, text])
    if not paragraphs:
        raise ValueError("No transcript text found")
    body = "\n".join(("[" + clock(start, (duration or 0) >= 3600) + "] " if start is not None else "")
                     + (speaker + ": " if speaker else "") + text
                     for start, speaker, text in paragraphs) + "\n"
    duration = "{:02d}:{:02d}:{:02d}".format(int(duration) // 3600, int(duration) // 60 % 60, int(duration) % 60) if duration is not None else None
    # Include the header itself in the token estimate; settle its digit count.
    estimate = 0
    while True:
        result = "# source: {} | duration: {} | est_tokens: {}\n{}".format(
            " ".join(filename.split()), duration or "null", estimate, body)
        if len(result) // 4 == estimate:
            return result, duration
        estimate = len(result) // 4


def split(text, limit):
    if len(text) // 4 <= limit:
        return []
    parts, current = [], ""
    for line in text.partition("\n")[2].splitlines(keepends=True):
        if len(line) // 4 > limit:
            raise ValueError("A transcript line exceeds --part-tokens; increase the limit")
        if current and len(current + line) // 4 > limit:
            parts.append(current)
            current = ""
        current += line
    if current:
        parts.append(current)
    return parts


def generated(path):
    return bool(re.search(r"(?:\.transcript\.txt|\.part\d+\.txt|\.brief\.(?:md|json))$", path.name))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", metavar="INPUT", nargs="*", help="transcript/media files or folders (non-recursive)")
    parser.add_argument("--out", type=Path, help="output folder (default: next to each input)")
    parser.add_argument("--part-tokens", type=int, default=20000, help="max estimated tokens per part file (default: 20000)")
    parser.add_argument("--model", default="small", help="faster-whisper model for media without subtitles (default: small)")
    parser.add_argument("--force", action="store_true", help="ignore the cached transcript and rebuild it")
    parser.add_argument("--setup-whisper", action="store_true",
                        help="one-time: install faster-whisper and the --model into an isolated venv "
                             "(~/.cache/briefly/whisper-venv, or $BRIEFLY_WHISPER_VENV), then exit")
    parser.add_argument("--whisper-worker", help=argparse.SUPPRESS)
    parser.add_argument("--worker-out", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.setup_whisper:
        return setup(args.model)
    if args.whisper_worker:
        return worker(args.whisper_worker, args.model, args.worker_out)
    if not args.inputs:
        parser.error("at least one INPUT is required (or use --setup-whisper)")
    if args.part_tokens < 1:
        parser.error("--part-tokens must be positive")
    inputs = []
    for value in args.inputs:
        path = Path(value).expanduser().resolve()
        try:
            children = sorted(p for p in path.iterdir() if p.is_file()
                              and p.suffix.lower() in TEXT | MEDIA and not generated(p)) if path.is_dir() else [path]
            # lecture.mp4 + lecture.srt is one recording: use the transcript, skip slow media.
            stems = {p.stem for p in children if p.suffix.lower() in TEXT}
            for skipped in [p for p in children if p.suffix.lower() in MEDIA and p.stem in stems]:
                print("Skipping {}: using its transcript file instead".format(skipped.name), file=sys.stderr)
                children.remove(skipped)
            inputs.extend(children or [path])
        except OSError:
            inputs.append(path)
    outputs = [(args.out.expanduser().resolve() if args.out else p.parent) / (p.stem + ".transcript.txt") for p in inputs]
    counts, input_set = Counter(outputs), set(inputs)
    success = False
    for path, output in zip(inputs, outputs):
        row = dict(input=str(path), transcript=str(output), parts=[], source=None,
                   duration=None, est_tokens=0, error=None)
        try:
            if not path.is_file() or path.suffix.lower() not in TEXT | MEDIA:
                raise ValueError("Not a supported file, or directory has no supported files: " + str(path))
            if counts[output] > 1 or output in input_set:
                raise ValueError("Output filename collides with another input: " + str(output))
            print("Preparing: " + path.name, file=sys.stderr)
            cached = output.exists() and output.stat().st_mtime_ns >= path.stat().st_mtime_ns and not args.force
            if cached:
                text = output.read_text(encoding="utf-8")
                # meeting.vtt and meeting.txt share a transcript path; only reuse our own.
                cached = text.startswith("# source: {} |".format(" ".join(path.name.split())))
            if cached:
                match = re.search(r"\| duration: (\d+:\d{2}:\d{2}|null) \|", text.split("\n", 1)[0])
                duration = match[1] if match and match[1] != "null" else None
                source = "cache"
            else:
                metadata = dict(duration=None, ends=[], source="text")
                segments = parse(path, args.model, metadata)
                source = metadata["source"]
                text, duration = normalize(segments, metadata, path.name)
            chunks = split(text, args.part_tokens)
            parts = [output.parent / (path.stem + ".part{:02d}.txt".format(i)) for i in range(1, len(chunks) + 1)]
            if any(p in input_set for p in parts):
                raise ValueError("Part filename collides with an input")
            output.parent.mkdir(parents=True, exist_ok=True)
            if not cached:
                output.write_text(text, encoding="utf-8")
            for part, chunk in zip(parts, chunks):
                part.write_text(chunk, encoding="utf-8")
            for old in output.parent.iterdir():
                if re.fullmatch(re.escape(path.stem) + r"\.part\d+\.txt", old.name) and old not in parts and old not in input_set:
                    old.unlink()
            row.update(parts=[str(p) for p in parts], source=source, duration=duration, est_tokens=len(text) // 4)
            success = True
        except Exception as exc:
            row["error"] = str(exc) or type(exc).__name__
            print("Error: " + row["error"], file=sys.stderr)
        print(json.dumps(row, ensure_ascii=False))
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
