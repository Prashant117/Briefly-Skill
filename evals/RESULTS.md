# Briefly evaluation results

18 October 2026 · macOS · Python 3.9.6 · Claude Code 2.1.291.

**Package ready; live model quality remains ungraded.** Claude Code reported `loggedIn: false` / `authMethod: none`. The user chose to finish with Claude checks marked blocked. The skill was installed at `~/.claude/skills/briefly/` and verified against all four canonical files, but no Claude briefs or map-reduce run were produced. No accessible Custom GPT test session was available in the connected browser; the requested manual checklist is provided instead. ChatGPT outputs have not been returned, and its ffprobe availability is **unknown**.

`python3 briefly/scripts/test_prep.py` → **OK** on Python 3.9.6. Both generators ran successfully. Every fixture was then prepared cold under `/usr/bin/time -p`; all eight JSON rows had `error: null`, and every small fixture met the <2 s target. Timings below are local prep wall times, not Claude or ChatGPT response times. Score `—/—` means ungraded, never a passing score or zero violations.

| Fixture | Platform | MUST (x/y) | MUST NOT violations | Format | prep time | Notes |
|---|---|---|---|---|---|---|
| team-sync.vtt | Claude Code — blocked | —/— | Not graded | Not graded | 0.05 s | Prep PASS; 420 est tokens; 0 parts; source=subtitles |
| lecture-youtube.vtt | Claude Code — blocked | —/— | Not graded | Not graded | 0.05 s | Prep PASS; 265 est tokens; 0 parts; source=subtitles; 793 → 265 tokens (66.6% reduction) |
| interview.srt | Claude Code — blocked | —/— | Not graded | Not graded | 0.05 s | Prep PASS; 297 est tokens; 0 parts; source=subtitles |
| notes-plain.txt | Claude Code — blocked | —/— | Not graded | Not graded | 0.05 s | Prep PASS; 3,155 est tokens; 0 parts; source=text |
| whisper.json | Claude Code — blocked | —/— | Not graded | Not graded | 0.05 s | Prep PASS; 172 est tokens; 0 parts; source=text |
| long-allhands.txt | Claude Code — blocked | —/— | Not graded | Not graded | 0.06 s | Prep PASS; 130,516 est tokens; 7 parts; source=text; parts reconstruct body; live map-reduce blocked |
| media-sample.mp4 | Claude Code — blocked | —/— | Not graded | Not graded | 0.12 s | Prep PASS; 95 est tokens; 0 parts; source=subtitles; real embedded-subtitle extraction |
| podcast.srt | Claude Code — blocked | —/— | Not graded | Not graded | 0.05 s | Prep PASS; 308 est tokens; 0 parts; source=subtitles |
| team-sync.vtt | ChatGPT — manual pending | —/— | Not graded | Not graded | — | Run chatgpt-manual-test.md and return outputs |
| lecture-youtube.vtt | ChatGPT — manual pending | —/— | Not graded | Not graded | — | Run chatgpt-manual-test.md and return outputs |
| whisper.json | ChatGPT — manual pending | —/— | Not graded | Not graded | — | Run chatgpt-manual-test.md and return outputs |
| long-allhands.txt | ChatGPT — manual pending | —/— | Not graded | Not graded | — | Run chatgpt-manual-test.md and return outputs |
| podcast.srt | ChatGPT — manual pending | —/— | Not graded | Not graded | — | Run chatgpt-manual-test.md and return outputs |

## Executed verification

- The assert-based suite exercised the real CLI: VTT/SRT cleanup, voices, rolling dedupe, thirty-second paragraphs, JSON list/object forms, DOCX, plain text and timestamps, hour formatting, part limits/body reconstruction, cache/force, batch isolation and errors, and safe output collisions. The no-subtitle failure was checked with a real WAV while faster-whisper was absent; mocked Whisper checks covered arguments, progress, lazy imports and stdout isolation.
- Every timed run checked the expected duration, exactly one stdout JSON line, exact `len(text) // 4` token estimates and matching header metadata. The 130,516-token long fixture produced seven parts, each ≤20,000 tokens, concatenating exactly to the transcript body. This proves preparation, not model reduction.
- The media generator read three complete lines from team-sync.vtt and muxed the 20-second video. Real ffprobe/ffmpeg extraction returned `source=subtitles`; no Whisper invocation was needed.
- Generated large/media fixtures, normalized transcripts and timing logs were kept outside the repository. Neither generated fixture was added to the package.
- `quick_validate.py briefly` → **Skill is valid!** The Markdown template matches section C, followed by its JSON schema; D1–D9 remain verbatim in both instruction sets.
- `wc -c chatgpt/instructions.md` → **7,968 bytes** (7,952 characters), under 8,000 either way. README.md has **24 lines**, under 40.
- `briefly.zip` contains exactly `briefly/SKILL.md`, `briefly/scripts/prep.py`, `briefly/scripts/test_prep.py` and `briefly/references/template.md`. All archived bytes match the sources; CRC verification passed. Archive size: **12,308 bytes**.

## Trigger review

Reviewed each query in `evals/trigger-queries.md` against the SKILL.md description alone: **15/15 match the expected routing**. This is a description review, not an observed automatic-routing test. No description change was needed.

| Query | Expected | Judgment | Description evidence |
|---|---|---|---|
| SHOULD 1 | Trigger | Trigger | Video summary and MP4 are explicit. |
| SHOULD 2 | Trigger | Trigger | Zoom transcripts, meeting notes and minutes are explicit. |
| SHOULD 3 | Trigger | Trigger | Teams recordings, recaps and MOV are explicit. |
| SHOULD 4 | Trigger | Trigger | Meet exports, action items and call to-dos are explicit. |
| SHOULD 5 | Trigger | Trigger | “What did we decide” and VTT are explicit. |
| SHOULD 6 | Trigger | Trigger | Lecture videos, takeaways and SRT are explicit. |
| SHOULD 7 | Trigger | Trigger | Podcasts, recordings and MP3 are explicit. |
| SHOULD 8 | Trigger | Trigger | Interviews, recordings and M4A are explicit. |
| SHOULD 9 | Trigger | Trigger | Pasted transcripts, YouTube captions and tutorials are explicit. |
| SHOULD 10 | Trigger | Trigger | Non-English/code-mixed transcript requests and English output are explicit. |
| SHOULD NOT 1 | Do not trigger | Do not trigger | Written reports that are not transcripts are excluded. |
| SHOULD NOT 2 | Do not trigger | Do not trigger | Video script writing is excluded. |
| SHOULD NOT 3 | Do not trigger | Do not trigger | Written articles that are not transcripts are excluded. |
| SHOULD NOT 4 | Do not trigger | Do not trigger | Creating a blank agenda is outside transcript/recording extraction. |
| SHOULD NOT 5 | Do not trigger | Do not trigger | A written proposal explicitly identified as non-transcript is excluded. |

## Fixes and packaging changes

No executed check failed in this run, so no new parser or extraction-rule change was made. No rule was added to address an unobserved model slip.

- `briefly/scripts/prep.py`: prior fixes verified: three-field segments with separate end metadata, body-only parts, strict merge boundaries, literal plain text, voice spans, long durations, output collisions and model-import stdout isolation.
- `briefly/scripts/test_prep.py`: prior fixes verified: real WAV fallback, missing-backend --help, macOS path resolution and CLI-only fixtures.
- `evals/chatgpt-manual-test.md`: add the requested ten-minute active-time checklist for fixtures 1, 2, 5, 6 and 8, including actual ffprobe/ffmpeg evidence and output-return fields.
- `evals/RESULTS.md`: record timed preparation, description-only routing judgments and explicit ungraded platform blockers.
- `README.md`: add concise installation for Claude Code, claude.ai and ChatGPT, local checks and optional faster-whisper.
- `briefly.zip`: package the exact canonical skill folder and verify its root, contents and CRCs.

## Remaining limitations

- **Claude quality blocked:** signing in is required before fresh-context briefs, all MUST/MUST NOT/Format grades and the parallel map-reduce path can be evaluated. The user explicitly chose not to wait for sign-in. No Claude scores or zero-violation claims are available.
- **ChatGPT quality pending:** follow `evals/chatgpt-manual-test.md` and return full outputs/downloaded files for grading. Record of `!which ffprobe`: **unknown; no human answer supplied**. Knowledge full-file access, sequential map-reduce, file downloads and JSON behavior remain live-platform checks.
- **Real Whisper accuracy untested:** local optional-backend behavior was tested without downloading a model. Hosted media requires available subtitle tools or a supplied transcript.
- Token counts are estimates, including the complete transcript header. Parts exclude that header. A single line above the part limit returns an error; increase the limit rather than splitting within a line.
- Plain transcript duration uses its last supplied timestamp; untimed input has null duration. Cache follows source/output mtimes; use --force after a model change. Directory discovery skips generated Briefly artifacts, and colliding output names require separate directories.
