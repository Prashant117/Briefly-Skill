#!/usr/bin/env python3
"""Run with plain python3. All fixtures and outputs stay in a temporary folder."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

SCRIPT = Path(__file__).with_name("prep.py")


def run(*args, code=0, env=None):
    result = subprocess.run([sys.executable, str(SCRIPT)] + [str(a) for a in args],
                            capture_output=True, text=True, env=env, timeout=30)
    assert result.returncode == code, (result.returncode, result.stdout, result.stderr)
    rows = [json.loads(line) for line in result.stdout.splitlines()]
    for row in rows:
        assert set(row) == {"input", "transcript", "parts", "source", "duration", "est_tokens", "error"}
        if row["error"] is None:
            text = Path(row["transcript"]).read_text()
            assert row["est_tokens"] == len(text) // 4
    return rows


def body(row):
    return Path(row["transcript"]).read_text().split("\n", 1)[1]


def main():
    ast.parse(SCRIPT.read_text(), feature_version=(3, 9))
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        def write(name, text):
            path = root / name
            path.write_text(text)
            return path

        vtt = write("voices.vtt", """WEBVTT

NOTE ignore this block
00:00:00.000 --> 00:00:01.000
not dialogue

STYLE
::cue { color: red; }

first-id
00:00:00.000 --> 00:00:05.000 align:start
<v Alice><i>Hello &amp; welcome.</i>

00:00:05.000 --> 00:00:10.000
<v Alice>We will review the launch.

00:00:10.000 --> 00:00:12.000
<v Bob>Agreed.

00:00:35.000 --> 00:00:40.000
<v Alice>Next topic.
""")
        row = run(vtt)[0]
        assert row["source"] == "subtitles" and row["duration"] == "00:00:40"
        assert body(row).splitlines() == ["[00:00] Alice: Hello & welcome. We will review the launch.",
                                          "[00:10] Bob: Agreed.", "[00:35] Alice: Next topic."]
        assert "not dialogue" not in body(row)
        inline = write("inline.vtt", "WEBVTT\n\n00:00:00.000 --> 00:00:04.000\n<v Ana>Hello.</v><v Bo>Thanks.</v>\n")
        assert body(run(inline)[0]) == "[00:00] Ana: Hello.\n[00:00] Bo: Thanks.\n"
        boundary = write("boundary.srt", "1\n00:00:00,000 --> 00:00:10,000\nFirst.\n\n2\n00:00:20,000 --> 00:00:30,000\nSecond.\n")
        assert body(run(boundary)[0]) == "[00:00] First.\n[00:20] Second.\n"

        rolling = "WEBVTT\n\n"
        for n in range(12):
            texts = (["Sentence number {} introduces a useful concept.".format(n - 1)] if n else [])
            texts.append("Sentence number {} introduces a useful concept.".format(n))
            rolling += "00:00:{:02d}.000 --> 00:00:{:02d}.000 position:10%\n{}\n\n".format(
                n, n + 1, "\n".join("<c><00:00:00.200>" + s + "</c>" for s in texts))
        row = run(write("rolling.vtt", rolling))[0]
        for n in range(12):
            assert body(row).count("Sentence number {} introduces".format(n)) == 1
        assert len(Path(row["transcript"]).read_text()) < len(rolling) * .6

        srt = write("captions.srt", """1
00:00:00,000 --> 00:00:10,000
Priya: First point.

2
00:00:25,000 --> 00:00:35,000
Priya: Second point.

3
00:00:35,000 --> 00:00:40,000
Priya: Third point.
""")
        row = run(srt)[0]
        assert body(row).splitlines() == ["[00:00] Priya: First point.", "[00:25] Priya: Second point. Third point."]

        segments = [{"start": 3600, "end": 3605, "text": "I'll send it.", "speaker": "Ana"},
                    {"start": 3610, "end": 3615, "text": "Thank you."}]
        for name, data in [("dict.json", {"segments": segments}), ("list.json", segments)]:
            row = run(write(name, json.dumps(data)))[0]
            assert row["duration"] == "01:00:15"
            assert body(row) == "[1:00:00] Ana: I'll send it.\n[1:00:10] Thank you.\n"
        row = run(write("tenhours.json", json.dumps([{"start": 36000, "end": 36005, "text": "Late."}])))[0]
        assert row["duration"] == "10:00:05" and "[10:00:00]" in body(row)

        docx = root / "document.docx"
        with zipfile.ZipFile(docx, "w") as doc:
            doc.writestr("word/document.xml", '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Alice: Hello</w:t></w:r><w:r><w:t> there.</w:t></w:r></w:p><w:p><w:r><w:t>Bob: Thanks.</w:t></w:r></w:p></w:body></w:document>')
        row = run(docx)[0]
        assert body(row) == "Alice: Hello there.\nBob: Thanks.\n" and row["duration"] is None

        plain = write("plain.txt", "Alice:   hello   there.\nBob: Use a < b > c.\nAgain.\nAgain.\n")
        row = run(plain)[0]
        assert row["duration"] is None and "[00:" not in body(row)
        assert body(row) == "Alice: hello there.\nBob: Use a < b > c.\nAgain.\nAgain.\n"
        stamped = write("times.md", "00:12 Alice: First.\n[00:42] Bob: Second.\n(00:12:03) Third.\n")
        row = run(stamped)[0]
        assert body(row) == "[00:12] Alice: First.\n[00:42] Bob: Second.\n[12:03] Third.\n"

        teams = write("teams.txt", "Alice Smith   0:03\nHello everyone.\nStill Alice.\n"
                      "Bob Jones   0:41\nI'll send the deck.\nLet's meet at 10:30\n")
        assert body(run(teams)[0]) == ("[00:03] Alice Smith: Hello everyone. Still Alice.\n"
                                       "[00:41] Bob Jones: I'll send the deck. Let's meet at 10:30\n")
        meet = write("meet.txt", "00:05:00\nAlice: Agreed.\nBob: Ok.\n[00:06:00] Cara: Next.\nUntimed.\n")
        assert body(run(meet)[0]) == "[05:00] Alice: Agreed.\n[05:00] Bob: Ok.\n[06:00] Cara: Next.\nUntimed.\n"

        same = write("same-stem.vtt", "WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nFrom VTT.\n")
        run(same)
        older = write("same-stem.txt", "From TXT.\n")
        os.utime(older, (0, 0))
        row = run(older)[0]
        assert row["source"] == "text" and body(row) == "From TXT.\n"

        large = write("large.txt", "".join("Line {} {}\n".format(n, "word " * 25) for n in range(90)))
        row = run(large, "--part-tokens", 1000)[0]
        assert len(row["parts"]) >= 3
        pieces = [Path(p).read_text() for p in row["parts"]]
        assert all(len(p) // 4 <= 1000 for p in pieces)
        assert "".join(pieces) == body(row)
        mtime = Path(row["transcript"]).stat().st_mtime_ns
        assert run(large, "--part-tokens", 700)[0]["source"] == "cache"
        assert Path(row["transcript"]).stat().st_mtime_ns == mtime
        assert run(large, "--force")[0]["source"] == "text"
        assert not list(root.glob("large.part*.txt"))
        os.utime(large, ns=(mtime + 1000000000, mtime + 1000000000))
        assert run(large)[0]["source"] == "text"
        enormous = write("enormous.txt", "x" * 5000)
        assert "line exceeds" in run(enormous, "--part-tokens", 1000, code=1)[0]["error"]
        assert not enormous.with_name("enormous.transcript.txt").exists()

        batch = root / "batch"
        batch.mkdir()
        (batch / "good.txt").write_text("Useful text.")
        (batch / "bad.docx").write_bytes(b"not a zip")
        (batch / "ignore.csv").write_text("ignored")
        (batch / "nested").mkdir()
        (batch / "nested" / "skip.txt").write_text("not recursive")
        rows = run(batch)
        assert len(rows) == 2 and rows[0]["error"] and rows[1]["error"] is None
        assert len(run(batch)) == 2  # Generated transcripts are not fresh inputs.
        assert run(root / "absent.txt", code=1)[0]["error"]
        assert run(write("bad.json", '{"segments":[{"start":-1,"end":1,"text":"x"}]}'), code=1)[0]["error"]
        assert run(write("empty.srt", ""), code=1)[0]["error"]
        collisions = [write("same.txt", "one"), write("same.md", "two")]
        assert all(row["error"] for row in run(*collisions, code=1))
        out = root / "out"
        assert Path(run(plain, "--out", out)[0]["transcript"]).parent == out.resolve()

        # Deterministic optional-backend tests: no model downloads or pip needed.
        modules = root / "modules"
        modules.mkdir()
        module = modules / "faster_whisper.py"
        module.write_text('raise ImportError("intentionally unavailable")\n')
        env = dict(os.environ, PYTHONPATH=str(modules), PATH=str(root / "no-tools"))
        help_result = subprocess.run([sys.executable, str(SCRIPT), "--help"],
                                     capture_output=True, text=True, env=env, timeout=30)
        assert help_result.returncode == 0 and "INPUT" in help_result.stdout
        media = root / "audio.wav"
        media.write_bytes(b"dummy input for mocked backend")
        assert "pip install faster-whisper" in run(media, code=1, env=env)[0]["error"]
        module.write_text('''from types import SimpleNamespace as S
print("import noise")
class WhisperModel:
    def __init__(self, model, device, compute_type):
        assert (model, device, compute_type) == ("small", "auto", "int8")
        print("backend noise")
    def transcribe(self, path, vad_filter, beam_size):
        assert vad_filter is True and beam_size == 1
        return iter([S(start=0, end=65, text="Spoken words.")]), S(duration=70)
''')
        row = run(media, env=env)[0]
        assert row["source"] == "whisper" and row["duration"] == "00:01:10"
        assert "[00:00] Spoken words." in body(row)
        module.write_text('raise RuntimeError("cache must not load backend")\n')
        assert run(media, env=env)[0]["source"] == "cache"
        assert run(media, "--force", code=1, env=env)[0]["error"]

        if shutil.which("ffprobe") and shutil.which("ffmpeg") and importlib.util.find_spec("faster_whisper") is None:
            wav = root / "real.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=d=2", str(wav)],
                           capture_output=True, text=True, check=True, timeout=30)
            assert "pip install faster-whisper" in run(wav, code=1)[0]["error"]
        else:
            print("Skipped real no-Whisper media check: tools unavailable or backend installed.", file=sys.stderr)
    print("OK")


if __name__ == "__main__":
    main()
