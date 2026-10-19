# Briefly — Skill Development Plan

**Goal:** turn a video transcript or video/audio file into: TL;DR, Summary, Key Points, Decisions, Action Items, Next Steps, Open Questions.
**Targets:** Claude (Claude Code + claude.ai Skills) and ChatGPT (Custom GPT).
**Owner/lead decisions:** below. Open questions at the end. Each one has a default, so the build can start now.

---

## 1. Lead decisions (final unless an open question changes them)

| # | Decision | Why |
|---|---|---|
| D1 | **One portable core**: `SKILL.md` (Agent Skills format) + one stdlib-only Python script `scripts/prep.py` + one output template. ChatGPT gets the same script + template as Knowledge files, plus an instructions file that mirrors `SKILL.md`. | One source of truth. No drift between Claude and ChatGPT. |
| D2 | **The LLM does the thinking; the script does the cleanup.** `prep.py` converts any input to a compact, timestamped transcript. The model then does the extraction in **one pass**. | Speed comes from cutting tokens, not from adding code. Raw VTT/SRT and YouTube auto-captions shrink by 40–70% after cleanup. |
| D3 | **Supported inputs (v1):** `.txt .md .vtt .srt .json` (Whisper-style segments) `.docx` (Teams/Zoom/Meet exports), pasted text, and media `.mp4 .mov .mkv .webm .mp3 .m4a .wav`. | These cover Zoom, Teams, Meet, YouTube, Otter and Whisper exports. |
| D4 | **Media pipeline, fastest path first:** (1) embedded subtitle track via `ffmpeg`, which is instant; (2) local `faster-whisper` (default model `small`, int8, VAD on; `--model base` for speed) when it's installed; (3) otherwise stop and ask the user for a transcript. | Subtitles are free. Whisper only runs when it has to. No API keys in v1. `small` gets names right more often, and names decide action-item owners. |
| D5 | **Scale strategy:** the script splits the transcript into **parts of about 20k tokens**. If the total is ≤ 100k tokens, the model reads every part and synthesizes once. If it's > 100k, it does map-reduce: notes per part, then one merge. In Claude Code the map step runs in parallel subagents. | 20k matches the tool read limits in Claude Code and ChatGPT. Single pass is fastest and most coherent. Map-reduce only kicks in for transcripts over about 10 hours. |
| D6 | **Batch:** `prep.py` accepts many files or a folder. Output is one brief per file, plus an optional roll-up. | Scalable without extra machinery. |
| D7 | **Cache:** if `<name>.transcript.txt` exists and is newer than the input, the script reuses it. | Re-runs are instant, and Whisper never runs twice. |
| D8 | **Output:** Markdown in chat (a fixed template), **and saved as `<stem>.brief.md` next to the input** when the input was a file. JSON when the user asks (`<stem>.brief.json`). Pasted text → chat only. | Readable in chat, kept on disk, and still parseable for automation. |
| D9 | **Grounding rules:** every item cites a `[mm:ss]` timestamp. Owners and due dates appear only if stated, otherwise `Unassigned` / `—`. An empty section reads "None stated." The model never invents anything. | Made-up owners are the #1 failure in meeting summarizers. |
| D10 | **Action Item vs Next Step:** an Action Item is a concrete task someone committed to or was assigned. A Next Step is the agreed direction or plan with no specific owner or task. | Removes the most common ambiguity in output. |
| D11 | **Python 3.9-compatible, stdlib only** in `prep.py`. `faster-whisper` is an optional import. | Your Mac has Python 3.9.6. The ChatGPT and claude.ai sandboxes have no internet for pip. |
| D12 | **Output is always English.** Non-English or code-mixed transcripts are translated. Names, product terms and titles keep their original spelling. A warning line says what was translated. | One consistent language across every brief. |
| D13 | **All four content types are first-class:** meetings, lectures/courses, YouTube/podcasts, interviews. The 7 headings never change; the spec gives a per-type rule for what goes in each section. | Same template everywhere, with type-aware extraction. |

**Skipped for v1:** speaker diarization (pyannote is heavy and needs an HF token), YouTube URL download, integrations (Notion/Jira/Slack), a cloud transcription API, and a second Whisper backend (mlx). Add each one if an open question comes back "yes".

---

## 2. Platform matrix

| Capability | Claude Code (local) | claude.ai (Skill upload) | ChatGPT (Custom GPT) |
|---|---|---|---|
| Transcript files / pasted text | ✅ | ✅ | ✅ |
| Video with embedded subs | ✅ ffmpeg | ✅ if sandbox has ffmpeg | ✅ if sandbox has ffmpeg (verify in Prompt 5) |
| Video without subs (Whisper) | ✅ after one-time `prep.py --setup-whisper` (asks first) | ❌ no model download → ask for transcript | ❌ same |
| Parallel map-reduce | ✅ subagents | sequential | sequential |
| Upload size | unlimited | sandbox limit | 512 MB/file |

---

## 3. File layout (final deliverable)

```
Briefly/
├── PLAN.md                     ← this file
├── prompts/                    ← give these to the build LLM, in order
├── briefly/                    ← THE Claude skill (copy to ~/.claude/skills/ or zip for claude.ai)
│   ├── SKILL.md
│   ├── scripts/prep.py
│   ├── scripts/test_prep.py
│   └── references/template.md
├── chatgpt/
│   ├── instructions.md         ← paste into Custom GPT "Instructions" (≤ 8,000 chars)
│   ├── SETUP.md                ← click-by-click GPT builder setup
│   └── (Knowledge = briefly/scripts/prep.py + briefly/references/template.md)
└── evals/
    ├── fixtures/               ← sample inputs
    ├── expected.md             ← what a correct brief must/must not contain
    └── RESULTS.md              ← filled in during Prompt 5
```

---

## 4. Build sequence

| Step | Prompt file | Output | Done when |
|---|---|---|---|
| 0 | `prompts/00-spec.md` | the shared contract; every other prompt references it | — |
| 1 | `prompts/01-prep-script.md` | `prep.py` + `test_prep.py` | `python3 briefly/scripts/test_prep.py` passes on Python 3.9 |
| 2 | `prompts/02-skill-md.md` | `SKILL.md` + `template.md` | under 300 lines; triggers on the eval queries |
| 3 | `prompts/03-chatgpt.md` | `chatgpt/instructions.md` + `SETUP.md` | instructions ≤ 8,000 chars |
| 4 | `prompts/04-fixtures-evals.md` | `evals/fixtures/*`, `expected.md` | 8 fixtures exist and prep.py handles every one |
| 5 | `prompts/05-run-evals.md` | `RESULTS.md`, fixes | every must-pass check is green on both platforms |

Steps 1 and 4 are independent and can run in parallel. Steps 2 and 3 need step 1's CLI to be final.

---

## 5. Open questions: resolved (2026-10-18)

| # | Question | Answer |
|---|---|---|
| 1 | ChatGPT form factor | Custom GPT |
| 2 | Video with no subs on web | Ask the user for a transcript (no API) |
| 3 | Content types | All four: meetings, lectures/courses, YouTube/podcasts, interviews (D13) |
| 4 | Output destination | Markdown in chat + saved `.brief.md` file (D8) |
| 5 | YouTube URLs | Not in v1 |
| 6 | Speakers | Names from the transcript only |
| 7 | Language | Always English (D12) |
| 8 | Whisper model | `small` (D4) |

No open questions remain. The prompts in `prompts/` are final.
