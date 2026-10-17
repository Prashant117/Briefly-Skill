# Briefly — Shared Spec (read this before any build step)

You are building **Briefly**, a skill that takes a video transcript or a video/audio file and extracts a structured brief. It ships for **Claude** (Agent Skills format: `SKILL.md` + scripts) and for **ChatGPT** (Custom GPT: instructions + Knowledge files + Code Interpreter). Both platforms share the same script and the same template.

Priorities, in this order: **correct (no hallucination) → fast → scalable → small.**
Write the least code that meets the spec. No frameworks, no config files, no abstractions with a single implementation.

---

## A. Folder layout

```
Briefly/
├── briefly/                    # the Claude skill folder (name must be exactly `briefly`)
│   ├── SKILL.md
│   ├── scripts/prep.py         # stdlib only, Python 3.9+ compatible
│   ├── scripts/test_prep.py    # assert-based, runs with plain `python3`
│   └── references/template.md  # the output template (single source of truth)
├── chatgpt/
│   ├── instructions.md         # ≤ 8,000 characters
│   └── SETUP.md
└── evals/
    ├── fixtures/
    ├── expected.md
    └── RESULTS.md
```

## B. `prep.py` contract (the build steps must match it exactly)

```
python3 prep.py INPUT [INPUT ...] [--out DIR] [--part-tokens 20000] [--model small] [--force]
```

- `INPUT` is a file or a directory. A directory means every supported file inside it, non-recursive. In a directory, a media file is skipped when a transcript file with the same stem sits beside it (`lecture.mp4` + `lecture.srt` → use the `.srt`).
- Supported text inputs: `.txt .md .vtt .srt .json .docx`
- Supported media inputs: `.mp4 .mov .mkv .webm .m4v .mp3 .m4a .wav .aac .flac .ogg`
- `--out` defaults to the directory of each input.
- **Output per input:** `<stem>.transcript.txt`. If the transcript is larger than `--part-tokens`, the script also writes `<stem>.part01.txt`, `<stem>.part02.txt` and so on, split on line boundaries. Each part is ≤ part-tokens.
- **Cache:** if `<stem>.transcript.txt` exists and its mtime ≥ the input's mtime, reuse it (no Whisper, no reparse) unless `--force` is given.
- **stdout:** exactly one JSON line per input, nothing else on stdout:
  `{"input": "...", "transcript": "...", "parts": ["..."], "source": "text|subtitles|whisper|cache", "duration": "hh:mm:ss or null", "est_tokens": 12345, "error": null}`
  When `parts` is `[]`, the transcript is a single part.
- **stderr:** human progress messages only.
- **Exit code:** 0 if at least one input succeeded, 1 if every input failed. A failure in one input never stops the others. That input's JSON line gets `error` set.
- Token estimate = `len(text) // 4`.

### Normalized transcript format (what the LLM reads)

```
# source: team-sync.vtt | duration: 00:47:12 | est_tokens: 9800
[00:00] Alice: Okay, let's get started. First item is the launch date.
[00:34] Bob: Design is blocked on the copy review...
[01:02] Unknown text without a speaker gets no label, just the timestamp.
```

Rules:
1. One line = one paragraph. Merge consecutive cues into the current paragraph while the speaker stays the same **and** the paragraph covers < 30 s. Start a new line when the speaker changes or 30 s pass.
2. Timestamps: `[mm:ss]` when the total duration is < 1 h, `[h:mm:ss]` otherwise. Use the paragraph's start time.
3. Speakers: take them from VTT `<v Name>` tags, `Name:` prefixes, or JSON `speaker` fields. Never guess.
4. Strip VTT/SRT cue numbers, cue settings, `<c>`/`<i>`/timestamp inline tags, `WEBVTT`/`NOTE`/`STYLE` blocks and HTML entities.
5. **Dedupe rolling captions** (YouTube auto-subs repeat each line across cues): after stripping tags, drop any text line identical to the previously emitted line.
6. Plain `.txt`/`.md`: if the lines already contain timestamps (`00:12`, `[00:12]`, `(00:12:03)`), keep them and normalize them to the format above. Otherwise pass the text through with whitespace collapsed, no timestamps, and `duration: null`.
7. `.json`: accept `{"segments":[{"start":sec,"end":sec,"text":..., "speaker"?:...}]}` (Whisper) or a top-level list of the same objects.
8. `.docx`: read `word/document.xml` with `zipfile` and turn `<w:p>` into lines. Then treat it like `.txt`.

### Media pipeline (fastest first)

1. If `ffprobe` is on PATH and the file has a subtitle stream, extract the first one with `ffmpeg -i IN -map 0:s:0 -f srt -` and parse it as SRT. `source = "subtitles"`.
2. Else, if `faster_whisper` can be imported: `WhisperModel(model, device="auto", compute_type="int8")`, `transcribe(path, vad_filter=True, beam_size=1)`, then use the segments. `source = "whisper"`. Print progress to stderr every ~60 s of audio processed.
3. Else, set `error` to: `"No subtitles found and faster-whisper is not installed. Run: pip install faster-whisper — or provide a transcript file."`

Import `faster_whisper` lazily, inside the function, so the script runs fine without it.

## C. Output template (exact; this is what `references/template.md` must contain)

```markdown
# {Title — inferred from content, ≤ 8 words}
*{Content type: Meeting | Lecture | Interview | Tutorial | Podcast | Other} · {Duration or "—"} · Source: {filename or "pasted text"}*

## TL;DR
{2–3 sentences. What it was about and the single most important outcome.}

## Summary
{One paragraph of 80–200 words, scaled to length. Neutral, past tense.}

## Key Points
- {Point} [mm:ss]
  (5–10 bullets, ordered by importance, not by time)

## Decisions
- {Decision that was explicitly agreed} [mm:ss]

## Action Items
| # | Task | Owner | Due | Ref |
|---|------|-------|-----|-----|
| 1 | {Verb-first task} | {Name or "Unassigned"} | {Date/phrase as stated or "—"} | [mm:ss] |

## Next Steps
- {Agreed direction or plan not tied to a specific owner/task} [mm:ss]

## Open Questions
- {Raised but not resolved} [mm:ss]
```

JSON mode, when the user asks for JSON: the same fields, with keys `title, content_type, duration, source, tldr, summary, key_points[{text,ref}], decisions[{text,ref}], action_items[{task,owner,due,ref}], next_steps[{text,ref}], open_questions[{text,ref}]`. Use `null` where the Markdown uses "—" or "Unassigned".

## D. Extraction rules (go into SKILL.md and the GPT instructions verbatim)

1. **Ground everything.** Every bullet and every row cites the timestamp where it was said. If the transcript has no timestamps, omit the refs. Never fabricate them.
2. **Never invent** owners, dates, numbers or decisions. Use an owner only when the transcript states it ("Priya will…", "Can you take this, Sam?" "Yes."), or when a known speaker says "I'll…". Otherwise write `Unassigned`. Due = the stated phrase ("by Friday"). Never convert it to a calendar date. Tasks aimed at the audience (students, listeners) get `Unassigned`.
3. **Action Item** = a concrete task someone committed to or was assigned. **Next Step** = an agreed direction with no specific task or owner. **Decision** = something explicitly agreed or settled, including a firm "we will…" choice nobody challenged. Put each item in exactly one section.
4. If something was later reversed or completed in the same recording, report only the final state.
5. **Empty section** → write `None stated.` Never remove headings, so the output stays machine-consistent.
6. **Content type** sets what goes in each section. The headings never change:
   - **Meeting:** standard. Decisions and Action Items carry the most weight.
   - **Lecture / course / tutorial:** Key Points = concepts and definitions taught. Action Items = homework, readings or exercises the speaker assigns. Decisions = usually `None stated.` Open Questions = questions the speaker left open or deferred.
   - **YouTube / podcast:** Key Points = main takeaways and claims (who made the claim, if it's a guest). Action Items = explicit recommendations to the audience ("try X", "read Y"). Next Steps = upcoming episodes or follow-ups the host announced.
   - **Interview:** Key Points = the interviewee's main answers and insights. Action Items = only explicit follow-ups agreed on ("I'll send you the deck"). Decisions = outcomes stated in the call (e.g. "we'll move you to the next round").
7. **Output is always English.** Translate non-English and code-mixed (e.g. Hinglish) transcripts. Keep people's names, product names and titles in their original spelling. If anything was translated, the warning line says `⚠ Translated from {language}.`
8. No preamble or closing chatter. Output the brief only. After it, add one line with any warnings, e.g. `⚠ Auto-generated captions; names may be misspelled.`
9. **Save the brief** when the input was a file: write the exact same Markdown to `<stem>.brief.md` in the same directory as `<stem>.transcript.txt` (JSON mode: `<stem>.brief.json`), and put the saved path on the last line. Batch roll-up → `rollup.brief.md`. Pasted text → chat only, unless the user asks for a file. Claude Code: next to the input. claude.ai: the outputs folder. ChatGPT: `/mnt/data/` plus a download link.

## E. Scale workflow (the model follows this in SKILL.md and in the GPT)

1. Run `prep.py` and read the JSON line.
2. `est_tokens ≤ 100,000`: read the transcript, or every part in order, then write the brief in **one pass**.
3. `est_tokens > 100,000` (map-reduce):
   - **Map:** for each part, extract notes: key points, decisions, action items, next steps, open questions, each with refs. Keep them terse.
     Claude Code: run one subagent per part **in parallel**. Other platforms: work through the parts in sequence.
   - **Reduce:** merge the notes, dedupe near-identical items (keep the earliest ref), apply rule D4 (final state wins), cap Key Points at 10, then write the brief from the template.
4. **Batch** (several inputs): one brief per input, in input order. If there are 3 or more inputs, end with a `## Roll-up` section covering cross-recording themes and every action item, grouped by owner.

## F. Non-goals (v1)

No speaker diarization from audio. No URL/YouTube downloading. No cloud transcription APIs. No integrations. No GUI.
