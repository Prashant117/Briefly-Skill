# Prompt 2: Write `SKILL.md` + `references/template.md`

Read `prompts/00-spec.md` (sections C, D, E) and `briefly/scripts/prep.py` first.

## Task
1. `briefly/references/template.md`: the spec C template exactly, plus the JSON-mode schema. Nothing else.
2. `briefly/SKILL.md`: the Agent Skills entry point.

## SKILL.md requirements
- YAML frontmatter with exactly `name: briefly` and a `description` of ≤ 1024 characters. The description decides whether the skill triggers, so write it to trigger on: transcripts, recordings, meeting/lecture/podcast/interview videos, `.vtt .srt .mp4 .mov .mp3 .m4a`, Zoom/Teams/Meet exports, and phrases like "summarize this video", "meeting notes", "minutes", "recap", "key takeaways", "action items", "to-dos from this call", "what did we decide". Also trigger on non-English video/transcript requests (the output is always English). State when **not** to use it: a written article or document that isn't a transcript.
- Body ≤ 150 lines, imperative voice, in this order:
  1. **Quick path**: if the user pasted transcript text directly, skip the script and extract straight away (fastest path).
  2. **File path**: run `python3 <skill_dir>/scripts/prep.py <files> --out <scratch dir>`, then parse the JSON line.
  3. Error handling for each `error` case (missing whisper → offer the `pip install faster-whisper` command or ask for a transcript; corrupt file → report it and continue with the others).
  4. The scale workflow from spec E, including "Claude Code: one subagent per part in parallel for the map step; give each subagent the part path and the notes format".
  5. Extraction rules D1–D9 **verbatim**, including the per-type rules in D6, always-English (D7) and saving the `.brief.md` file (D9).
  6. "Read `references/template.md` and fill it in exactly." Never restate the template in SKILL.md, so it has a single source of truth.
  7. Batch + roll-up rule.
- Use relative paths from the skill dir only. No absolute paths, no platform-specific assumptions beyond "python3 is available".
- No explanation of *why*. Only what to do.

## Also produce `evals/trigger-queries.md`
Ten prompts that SHOULD trigger the skill and five that should NOT (for example "summarize this PDF report" or "write a video script"). This file is used in Prompt 5.

## Done when
- SKILL.md has valid frontmatter, ≤ 150 body lines, and references only files that exist.
- Reply with the full SKILL.md content and its line count.
