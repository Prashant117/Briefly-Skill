# Prompt 6: Make Briefly work when no transcript is available

Read these first: `prompts/00-spec.md`, `briefly/SKILL.md`, `briefly/scripts/prep.py`, `briefly/scripts/test_prep.py`, `chatgpt/instructions.md` and `README.md`.

## The bug (reproduced 2026-10-19 on macOS, Python 3.9.6)

A video or audio file with **no embedded subtitles** (most phone, Zoom-local and screen recordings) never produces a brief:

```text
$ python3 briefly/scripts/prep.py meeting.mp4
Error: No subtitles found and faster-whisper is not installed. Run: pip install faster-whisper — or provide a transcript file.
exit=1
```

Transcription itself works. In an isolated venv, `pip install faster-whisper` installed cleanly on Python 3.9 (faster-whisper 1.2.1, ctranslate2 4.8.3, av 15.1.0), and `prep.py meeting.mp4` then returned `source: "whisper"` with an accurate transcript. With the default `small` model, the first run took 46 s (a one-time 464 MB model download to `~/.cache/huggingface`) and later runs took 3.8 s.

## Root causes (fix every one)

1. **Dead end instead of setup.** When `faster_whisper` can't be imported, `prep.py` stops. SKILL.md only says "offer `pip install faster-whisper`", so the model asks and gives up. Nothing automates the install.
2. **The install command can target the wrong Python.** A bare `pip install` may install into a different interpreter than the `python3` that runs `prep.py`. On macOS, the system Python can also refuse global installs.
3. **No visibility on the first run.** The 464 MB model download and long transcriptions print almost nothing, so the run looks frozen.
4. **Noisy stderr.** On macOS, numpy prints `RuntimeWarning: overflow encountered in matmul` from `faster_whisper/feature_extractor.py`. The transcript is still correct, but the warning looks like a failure.
5. **Hosted platforms** (claude.ai, ChatGPT Code Interpreter) can't download models. The current message is correct but not helpful.

## Required design (lead decision; implement exactly this)

### A. Self-provisioned, isolated Whisper environment

- Add a `--setup-whisper` flag to `prep.py`. It must:
  1. Create a venv at `~/.cache/briefly/whisper-venv`, overridable with the `BRIEFLY_WHISPER_VENV` environment variable (the tests need this). Create it with `[sys.executable, "-m", "venv", path]`.
  2. Run `[venv_python, "-m", "pip", "install", "--upgrade", "pip", "faster-whisper"]`, with progress going to stderr.
  3. Pre-download the model chosen by `--model` (default `small`) by running the venv Python with a one-line `WhisperModel(model, device="cpu", compute_type="int8")`. Print `Downloading Whisper model 'small' (~460 MB, one time)…` first. Approximate sizes: tiny 75 MB, base 145 MB, small 460 MB, medium 1.5 GB.
  4. Print exactly one JSON line, `{"setup": "ok"|"error", "python": "<venv python>", "model": "...", "error": null|"..."}`. Exit 0 on success, 1 on failure.
  5. Be idempotent. If the venv already imports `faster_whisper`, skip the install and only make sure the model is downloaded.
- `prep.py` itself stays **stdlib-only and Python 3.9 compatible**. Never import third-party packages at module level.

### B. Use that environment automatically

In `whisper()`, try backends in this order:
1. `faster_whisper` imports in the current interpreter → use it (current behaviour).
2. Else, if the venv Python exists → run it as a **worker** with a hidden flag: `[venv_python, __file__, "--whisper-worker", media_path, "--model", model, "--worker-out", tmp_json]`. The worker transcribes and writes Whisper-style JSON (`{"segments":[{"start","end","text"}], "duration": seconds}`). The parent then parses it with the existing `json_segments()`, so no new parsing code is needed. Set `source = "whisper"`. Pass the worker's stderr straight through so progress stays visible. Don't set a short timeout; transcription can take many minutes.
3. Else → error with this exact, actionable text:
   `No subtitles found and local transcription is not set up. Run: python3 <path-to>/prep.py --setup-whisper (one-time, ~560 MB) — or provide a transcript file.`
   Use the real absolute path of the script in the message.

### C. Progress and noise

- Print a percentage every ~60 s of audio processed: `Transcribing meeting.mp4: 12:00 / 47:31 (25%)`, using `info.duration`.
- Wrap transcription in `warnings.catch_warnings()` + `warnings.simplefilter("ignore", RuntimeWarning)`. Only `RuntimeWarning` is silenced; real exceptions still propagate.
- stdout must still carry only the JSON protocol lines (keep `contextlib.redirect_stdout(sys.stderr)` around third-party code).

### D. SKILL.md behaviour (Claude)

Replace the missing-faster-whisper sentence in **Errors** with this flow:
1. On the "local transcription is not set up" error, ask the user **once**: *"This recording has no subtitles. Set up free local transcription? One-time download, about 560 MB (faster-whisper + Whisper 'small'); audio never leaves this computer. Or send a transcript instead."*
2. On yes: run `python3 <skill-dir>/scripts/prep.py --setup-whisper`, then re-run the original prep command with the same inputs, and continue to the brief.
3. Tell the user that the first transcription of a long recording can take several minutes on CPU, and offer `--model base` if they want speed over name accuracy.
4. On claude.ai, try the setup once. If it fails (for example, no network), give the transcript-export steps from README "Where to get a transcript" in at most four short lines.

Keep D1–D9 untouched. SKILL.md body stays ≤ 150 lines.

### E. ChatGPT

Code Interpreter has no internet, so keep the transcript request. Replace the fallback sentence in `chatgpt/instructions.md` with a shorter version that includes the four export one-liners (Zoom, Teams, Meet, YouTube). The file must stay **≤ 8,000 characters** (it is at about 7,979 now, so cut elsewhere to make room). Never drop a rule.

### F. Docs

- README: in **Requirements**, change the faster-whisper row to "set up automatically on first use (asks first)". In **Installation → Claude Code**, replace `pip install faster-whisper` with the `--setup-whisper` command. Update the FAQ entry about transcribing.
- `prompts/00-spec.md` section B: document `--setup-whisper`, the venv location and the worker. Don't document `--whisper-worker` in `--help`; use `argparse.SUPPRESS`.
- `evals/RESULTS.md`: add a short "No-transcript fix" section with what was verified.

## Tests (add to `briefly/scripts/test_prep.py`; no network, no real model)

1. **Missing everywhere:** with `PATH` lacking ffprobe, `PYTHONPATH` pointing to a module that raises ImportError, and `BRIEFLY_WHISPER_VENV` set to an empty temp dir, a `.wav` input → `error` contains `--setup-whisper` and the absolute script path.
2. **Venv worker path:** create a fake "venv" whose `bin/python` is a small shell script that runs `sys.executable` with `PYTHONPATH` set to a mock `faster_whisper` module (same mock style as the existing tests). Point `BRIEFLY_WHISPER_VENV` at it, keep the parent's import failing, and run on a `.wav` → `source == "whisper"`, the transcript has the mocked text, and stdout has exactly one JSON line.
3. **Setup idempotency:** run `--setup-whisper` with `BRIEFLY_WHISPER_VENV` pointing to the fake venv that already imports the mock → `{"setup": "ok"}`, and no pip call happens (have the mock fail if pip is invoked).
4. **Warnings:** the mock emits `warnings.warn("overflow", RuntimeWarning)` during transcription → no warning text appears in stderr.
5. All existing tests still pass, and `ast.parse(..., feature_version=(3, 9))` still passes.

## Manual acceptance (run it and paste the results)

```bash
say -o /tmp/speech.aiff "Priya will send the launch copy by Thursday. We agreed to launch on Friday."
ffmpeg -y -v error -f lavfi -i color=c=black:s=160x90:r=1 -i /tmp/speech.aiff -shortest -c:v mpeg4 -c:a aac /tmp/meeting.mp4
python3 briefly/scripts/prep.py /tmp/meeting.mp4              # expect: the actionable --setup-whisper error
python3 briefly/scripts/prep.py --setup-whisper               # expect: {"setup": "ok", ...}
python3 briefly/scripts/prep.py /tmp/meeting.mp4 --force      # expect: source "whisper", correct text
python3 briefly/scripts/test_prep.py                          # expect: OK
```

Then, in Claude Code, ask "summarize /tmp/meeting.mp4". Confirm the skill asks once, sets up, and produces a brief with Priya / by Thursday as an action item and Friday as a decision.

## Done when

Every root cause above is fixed and all tests print `OK` on Python 3.9. The manual acceptance passes. `chatgpt/instructions.md` is ≤ 8,000 characters. The installed copy at `~/.claude/skills/briefly/` is refreshed with `rm -rf ~/.claude/skills/briefly && cp -R briefly ~/.claude/skills/`. Reply with the test output, the acceptance output, the `wc -c chatgpt/instructions.md` count, and a list of changed files. Do not commit or push.
