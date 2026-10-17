# Briefly evaluation results

18 October 2026 · macOS (Apple Silicon) · Python 3.9.6 · Claude Code, Opus 5.5 · skill installed at `~/.claude/skills/briefly/`.

**Claude: all 8 fixtures pass, with 0 MUST NOT violations, after two rule fixes. ChatGPT: still a manual check**, run with [chatgpt-manual-test.md](chatgpt-manual-test.md). The graded Claude outputs are in [outputs/claude/](outputs/claude/), with one file per fixture plus `rollup.md`. They were saved as `<stem>.brief.md` during the run and renamed here because `.gitignore` excludes `*.brief.md`.

Grading method: I wrote the briefs blind, before reading `expected.md`, then graded them against it. The 130k-token fixture went through the real map-reduce path: 7 parts, mapped by 2 parallel subagents (parts 1–4 and 5–7), then reduced in the main session. The completion at 6:15:00 in part 5 was linked back to the task created at 4:10:00 in part 4.

| Fixture | Platform | MUST (x/y) | MUST NOT violations | Format | prep time | Notes |
|---|---|---|---|---|---|---|
| team-sync.vtt | Claude Code | 8/8 | 0 | ✅ | 0.17 s | Friday replaces Tuesday; log task is Unassigned |
| lecture-youtube.vtt | Claude Code | 3/3 | 0 | ✅ | 0.06 s | 793 → 265 tokens (66.6% smaller); homework owner fixed to Unassigned (fix 3) |
| interview.srt | Claude Code | 2/2 | 0 | ✅ | 0.06 s | 4 item sections are `None stated.`; TL;DR written normally |
| notes-plain.txt | Claude Code | 4/4 | 0 | ✅ | 0.05 s | Untimed: no refs, duration `—`, empty Ref cells |
| whisper.json | Claude Code | 6/6 | 0 | ✅ | 0.05 s | English output, translation warning; "keep the name" decision fixed (fix 4) |
| long-allhands.txt | Claude Code | 3/3 | 0 | ✅ | 0.08 s | 130,516 tokens, 7 parts; 5 open actions; completed screenshot task excluded |
| media-sample.mp4 | Claude Code | 3/3 | 0 | ✅* | 0.13 s | source=subtitles, no Whisper; *summary is 64 words, below 80, by design (no padding) |
| podcast.srt | Claude Code | 4/4 | 0 | ✅ | 0.06 s | Claim attributed to Omar; owners Unassigned (fix 3); agenda due phrase moved to Due |
| Roll-up (8 inputs) | Claude Code | ✅ | 0 | ✅ | — | Same names in different files kept separate |
| team-sync, lecture, whisper, long, podcast | ChatGPT | —/— | not graded | not graded | — | Pending the manual checklist; `which ffprobe` in Code Interpreter is still unknown |

Prep times are cold wall-clock times for `prep.py` alone, not model response times. Every small fixture is under the 2 s target.

## Fixes made in this run

1. `briefly/scripts/prep.py`: **wrong-file cache hit.** `meeting.txt` silently reused the transcript made earlier from `meeting.vtt` (same stem). The cache is now reused only when its `# source:` header names the same input file.
2. `briefly/scripts/prep.py`: **Teams/Otter/Meet exports lost timestamps and speakers.** A `Name   0:03` line, or a `00:05:00` line on its own, now applies its time and speaker to the text lines that follow. Lines that merely end in a time ("Let's meet at 10:30") are not treated as headings.
3. Rule D2 (`SKILL.md`, `chatgpt/instructions.md`, `prompts/00-spec.md`): tasks aimed at the audience (students, listeners) get owner `Unassigned`. The first run wrote "Students" and "Listeners", which is reproducible across two content types.
4. Rule D3 (same three files): a firm "we will…" choice nobody challenged counts as a Decision. The first run filed "keep the Sahyog name" under Key Points.
5. `briefly/scripts/test_prep.py`: added regression tests for fixes 1 and 2. The suite prints `OK`.
6. `chatgpt/instructions.md`: removed the Claude-only destinations and a duplicate "no preamble" line, so the new rules fit: **7,979 characters** (7,997 bytes), under 8,000.
7. Rebuilt `briefly.zip` from the current `briefly/` folder. Updated `README.md`.

One-off slip, no rule added: the podcast's "before joining the call" first landed in the task text instead of the Due column.

## Repo audit fixes (second pass)

Found by probing `prep.py` with real-world inputs. Each fix has a regression test, and every fixture's transcript is byte-for-byte unchanged.

1. **Encoding:** Windows-1252 and UTF-16 subtitle/text files failed with a UTF-8 decode error. They now decode correctly.
2. **Media + transcript pairs:** a folder with `lecture.m4a` and `lecture.srt` failed on both files, because of an output-name collision. The media file is now skipped in favour of its transcript.
3. **JSON errors:** malformed segments gave `'text'` or `string indices must be integers`. They now give "Each JSON segment needs start, end and text".
4. **Zoom text export:** `[Alice] 00:01:02` headings kept the brackets in the speaker name.
5. **Test coverage:** added a real embedded-subtitle MP4 test. It proves Whisper is never loaded when subtitles exist.
6. **Docs:**
   - SKILL.md runs the script by its full path, so no change of directory is needed.
   - SETUP.md pointed to the wrong checklist file, and it now states the custom-GPT retirement plainly.
   - `make_media.sh` can be re-run.
   - README explains how to build `briefly.zip`, which is git-ignored.

Verified externally: OpenAI's [migration guide](https://learn.chatgpt.com/docs/migrate-custom-gpts) says custom GPTs are moving to plugins and stop running at retirement (no date given). Codex loads skills from `.agents/skills/` ([Build skills](https://learn.chatgpt.com/docs/build-skills)).

## Trigger review

15 of 15 queries in `trigger-queries.md` route correctly, judged from the SKILL.md description. The description is unchanged. This is a review of the wording, not an observed routing test.

## Remaining limitations

- **ChatGPT quality is ungraded.** I can't operate a Custom GPT from here. Run the checklist and paste the outputs back for grading.
- **Real Whisper transcription is untested.** faster-whisper isn't installed, and the backend logic is covered by a mocked test.
- The 7,979-character GPT instructions leave about 20 characters of headroom. Any future rule must replace wording rather than add to it.
- Token counts are estimates (`len // 4`). One line longer than `--part-tokens` gives an error; raise the limit.
