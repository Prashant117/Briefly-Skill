#!/usr/bin/env python3
"""Normalize local transcripts; optionally extract subtitles or transcribe media."""
import argparse
from collections import Counter
import contextlib
import html
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

TEXT = {".txt", ".md", ".vtt", ".srt", ".json", ".docx"}
MEDIA = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".mp3", ".m4a",
         ".wav", ".aac", ".flac", ".ogg"}
CLOCK = r"\d+:\d{2}(?::\d{2})?(?:[.,]\d+)?"
STAMP = re.compile(r"^\s*[\[(]?(" + CLOCK + r")[\])]?(?:\s+|$)(.*)$")
MISSING_WHISPER = ("No subtitles found and faster-whisper is not installed. Run: "
                   "pip install faster-whisper — or provide a transcript file.")


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


def lines(raw, start=None, end=None, speaker=None, markup=True):
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
                yield start, end, speaker, text


def subtitles(raw):
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
        segments.extend(lines("\n".join(cue[timing + 1:]), start, end))
    if not segments:
        raise ValueError("No subtitle cues with text found")
    return segments, duration


def plain(raw):
    segments, duration = [], None
    for line in raw.splitlines():
        match = STAMP.match(line)
        start = seconds(match[1]) if match else None
        if start is not None:
            duration = max(duration or 0, start)
        segments.extend(lines(match[2] if match else line, start, start, markup=False))
    return segments, duration


def json_segments(data):
    items = data.get("segments") if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise ValueError("JSON must be a segment list or an object with segments")
    segments, duration = [], 0
    for item in items:
        start, end = seconds(item["start"]), seconds(item["end"])
        if end < start or not isinstance(item["text"], str):
            raise ValueError("Invalid segment end or text")
        speaker = item.get("speaker")
        if speaker is not None and not isinstance(speaker, str):
            raise ValueError("Segment speaker must be a string or null")
        duration = max(duration, end)
        segments.extend(lines(item["text"], start, end, speaker))
    return segments, duration


def whisper(path, model):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise ValueError(MISSING_WHISPER) from None
    segments, duration, report = [], 0, 60
    # Third-party model messages must never contaminate the JSON protocol.
    with contextlib.redirect_stdout(sys.stderr):
        engine = WhisperModel(model, device="auto", compute_type="int8")
        stream, info = engine.transcribe(str(path), vad_filter=True, beam_size=1)
        for segment in stream:
            start, end = seconds(segment.start), seconds(segment.end)
            segments.extend(lines(segment.text, start, end))
            duration = max(duration, end)
            if end >= report:
                print("Transcribed " + clock(end, True), file=sys.stderr)
                report = (int(end) // 60 + 1) * 60
        duration = max(duration, seconds(info.duration))
    return segments, duration, "whisper"


def media(path, model):
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
                segments, duration = subtitles(result.stdout)
                try:
                    duration = max(duration, seconds(info["format"]["duration"]))
                except (KeyError, ValueError, TypeError):
                    pass
                return segments, duration, "subtitles"
        except (subprocess.SubprocessError, ValueError) as exc:
            print("Subtitle extraction unavailable: " + str(exc), file=sys.stderr)
    return whisper(path, model)


def parse(path, model):
    suffix = path.suffix.lower()
    if suffix in MEDIA:
        return media(path, model)
    if suffix == ".docx":
        with zipfile.ZipFile(path) as doc:
            root = ET.fromstring(doc.read("word/document.xml"))
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        raw = "\n".join("".join(node.text or "" if node.tag == ns + "t" else " "
                                 for node in p.iter() if node.tag in {ns + "t", ns + "tab", ns + "br"})
                        for p in root.iter(ns + "p"))
    else:
        raw = path.read_text(encoding="utf-8-sig")
    if suffix in {".vtt", ".srt"}:
        segments, duration = subtitles(raw)
        return segments, duration, "subtitles"
    segments, duration = json_segments(json.loads(raw)) if suffix == ".json" else plain(raw)
    return segments, duration, "text"


def normalize(segments, duration, filename, dedupe=False):
    paragraphs, previous = [], None
    for start, end, speaker, text in segments:
        if dedupe and text == previous:
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
    for line in text.splitlines(keepends=True):
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
    parser.add_argument("inputs", metavar="INPUT", nargs="+")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--part-tokens", type=int, default=20000)
    parser.add_argument("--model", default="small")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.part_tokens < 1:
        parser.error("--part-tokens must be positive")
    inputs = []
    for value in args.inputs:
        path = Path(value).expanduser().resolve()
        try:
            children = sorted(p for p in path.iterdir() if p.is_file()
                              and p.suffix.lower() in TEXT | MEDIA and not generated(p)) if path.is_dir() else [path]
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
                match = re.search(r"\| duration: (\d+:\d{2}:\d{2}|null) \|", text.split("\n", 1)[0])
                duration = match[1] if match and match[1] != "null" else None
                source = "cache"
            else:
                segments, duration, source = parse(path, args.model)
                text, duration = normalize(segments, duration, path.name, path.suffix.lower() in {".srt", ".vtt"} or source == "subtitles")
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
