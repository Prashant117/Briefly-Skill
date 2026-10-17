# Briefly

Turn transcripts and video/audio recordings into grounded English briefs with timestamped takeaways, decisions and action items. Claude and ChatGPT share one Python script and one template.

## Install

- **Claude Code:** run `mkdir -p ~/.claude/skills && cp -R briefly ~/.claude/skills/` from this folder. Ask Claude to use Briefly on your transcript or recording.
- **claude.ai:** upload `briefly.zip` through **Settings → Capabilities → Skills → Upload**, where available. Enable code execution and file creation.
- **ChatGPT Custom GPT:** follow [chatgpt/SETUP.md](chatgpt/SETUP.md). Paste `chatgpt/instructions.md` into Instructions, upload the canonical `prep.py` and `template.md` as Knowledge, and enable Code Interpreter & Data Analysis.

## Local use and checks

Use Python 3.9 or later. Transcript formats: TXT, Markdown, VTT, SRT, Whisper JSON and DOCX.

```sh
python3 briefly/scripts/prep.py recording.vtt
python3 briefly/scripts/test_prep.py
```

The script prepares transcripts; the skill/model writes the brief. For local media, install ffmpeg/ffprobe to extract embedded subtitles. Optional local transcription: `pip install faster-whisper` (model weights must be available).

No URL downloading, cloud transcription APIs or speaker diarization. In hosted sandboxes without transcription tools, provide a transcript.

See [evals/RESULTS.md](evals/RESULTS.md) for measured checks and platform blockers, and [evals/chatgpt-manual-test.md](evals/chatgpt-manual-test.md) for the Custom GPT checklist. Live Claude quality remains ungraded while Claude Code is signed out.
