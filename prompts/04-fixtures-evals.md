# Prompt 4: Eval fixtures + expected results

Read `prompts/00-spec.md` first. This step doesn't depend on any code, so it can run in parallel with Prompt 1.

## Task
Create realistic, hand-written fixtures in `evals/fixtures/` and the grading key in `evals/expected.md`.

## Fixtures (write content with planted facts the grader can check)
1. `team-sync.vtt`: a 12-minute product meeting, 4 speakers with `<v Name>` tags. Plant: 3 explicit action items with owners (one with a due phrase, "by Thursday"), 1 task said with **no owner** ("someone should look at the logs"), 2 decisions, 1 decision that gets **reversed** later in the call, 1 open question, and 2 next steps.
2. `lecture-youtube.vtt`: a 15-minute lecture in **YouTube auto-caption rolling format** (lines repeated across cues, `<c>` tags, inline timestamps). No speaker tags. Plant: 1 homework assignment and no decisions.
3. `interview.srt`: a 10-minute interview with `Name:` prefixes in the cue text. Plant: 0 action items. TL;DR, Summary and Key Points are written normally; Decisions, Action Items, Next Steps and Open Questions should come out as "None stated."
4. `notes-plain.txt`: a pasted transcript with no timestamps and speaker prefixes, about 2,000 words. Plant: 2 action items.
5. `whisper.json`: Whisper segments format, about 5 minutes, Hindi-English code-mixed (Hinglish). Plant: 1 action item. Checks that the output is **fully English** (translated), with names kept as spoken, and the `⚠ Translated from` warning.
6. `long-allhands.txt`: generate it with a small script `evals/make_long.py` (commit the script, not a giant file). A synthetic transcript of about 130k est tokens: repeat varied filler sections, plant 5 action items spread across the start, the middle and the end, plus 1 action item that is marked done later. Checks map-reduce and the final-state rule.
7. `media-sample.mp4`: **don't commit it.** Add `evals/make_media.sh`, which uses ffmpeg to make a 20 s video with a test tone **and** a muxed SRT subtitle track built from 3 lines of fixture 1. Checks the subtitle fast path.
8. `podcast.srt`: an 8-minute podcast, a host and a guest with `Name:` prefixes. Plant: 2 audience recommendations (→ Action Items, owner `Unassigned` or the audience), 1 guest claim that must be attributed to the guest, and 1 announced next episode (→ Next Steps).

## `evals/expected.md`
For each fixture, list:
- **MUST contain**: the planted items, with owner, due phrase and approximate timestamp (±30 s).
- **MUST NOT contain**: the unowned task attributed to anyone, the reversed decision shown as final, invented dates, the done item listed as open, and section headings missing.
- **Format checks**: all 7 template headings are present and in order, the Action Items table has 5 columns, the content-type line is correct, and `<stem>.brief.md` was saved and matches the chat output.
- **Speed budget**: prep.py time for fixtures 1–5, 7 and 8 (target < 2 s each), est_tokens before vs after normalization for fixture 2 (target ≥ 40% reduction).

## Done when
- Every fixture exists, or can be generated. `python3 briefly/scripts/prep.py evals/fixtures/` runs with no `error` (once prep.py exists).
- Reply with a table: fixture → planted facts count → what it tests.
