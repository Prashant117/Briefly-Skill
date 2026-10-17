# Briefly: ten-minute Custom GPT check

Budget about ten minutes of active checking, plus model processing/upload time. Run this in the private Briefly GPT configured using `chatgpt/SETUP.md`. Use a fresh chat for each fixture. Keep all model output; do not repair it before grading.

## 0–2 minutes: resources and sandbox

1. Confirm the GPT has the exact repository `briefly/scripts/prep.py` and `briefly/references/template.md` Knowledge files and Code Interpreter & Data Analysis enabled. Web search and image generation stay off.
2. Ask: “Using the Python tool, locate prep.py and template.md under /mnt/data and confirm both full files are readable. Then run `!which ffprobe` and `!which ffmpeg`, and show their output and exit status.”
3. Record the actual paths or missing-tool results below. Do not infer sandbox tools from this repository's local test machine. If Knowledge is available only as retrieval snippets, upload the original two files in the chat.

## 2–7 minutes: five fresh chats

Ask “Use Briefly to brief this file.” Upload each of the following separately. Confirm the Python tool runs the shared script with `--out /mnt/data/out --part-tokens 15000` and reads every listed part in order. Save the displayed brief and its downloaded file.

| Fixture | Quick checks before full grading |
|---|---|
| 1. team-sync.vtt | Four actions: Priya/copy/by Thursday; Sam/accessibility/no due; Mina/invoices/no due; logs/Unassigned/before next review. Friday is final; chat-only support is agreed; retention is unresolved. Two next steps. |
| 2. lecture-youtube.vtt | One causal-diagram homework task, Unassigned, no due date; no invented decisions. No duplicated concepts from rolling captions. |
| 5. whisper.json | English prose; Priya, Aarav and Sahyog preserved; Priya sends the onboarding draft tomorrow morning; Hindi/Hinglish translation warning. No calendar date conversion. |
| 6. long-allhands.txt | Above 100,000 est tokens; sequential map of every part, notes stored internally, then reduction. Five outstanding actions survive; the completed screenshot task is absent from open actions. |
| 8. podcast.srt | Two audience recommendations; no named listener owner; attribute the context-switching claim to Omar; next episode appears under Next Steps. |

Generate fixture 6 locally before uploading:

```sh
python3 evals/make_long.py /tmp/long-allhands.txt
```

Upload `/tmp/long-allhands.txt`. Record the manifest's est_tokens and part count. At 15,000 tokens per part, expect approximately nine parts; use the actual manifest as the authority. Confirm every part was read/mapped rather than trusting only the final answer. Do not paste the giant transcript back here.

## 7–10 minutes: format, saving and report

- Check all seven headings, in order: TL;DR, Summary, Key Points, Decisions, Action Items, Next Steps, Open Questions. Retain a normal TL;DR for interviews; empty item sections read `None stated.`
- Check five Action Items columns. Every timed bullet/row cites the supporting passage; do not accept an unrelated timestamp within the tolerance. Never invent names, numbers or due dates.
- Download each `.brief.md` from `/mnt/data/`. Compare it to the displayed brief including any warning, excluding the final download-link line.
- In the team-sync chat, request JSON as an additional check. Parse the downloaded `.brief.json`; check the template's eleven keys, nulls for missing values and [] for empty item sections. No warnings or links inside the JSON file.
- Paste the full brief outputs back into the build chat, or attach the downloaded brief files, together with the report below. They can then be graded against every MUST/MUST NOT/Format check in `evals/expected.md`. Quick checks alone are not a passing grade.

## Report to return

```text
Date and GPT/model used:
prep.py and template.md full-file access: yes / no
!which ffprobe output and exit status:
!which ffmpeg output and exit status:
team-sync: attach/paste brief and saved file
lecture-youtube: attach/paste brief and saved file
whisper.json: attach/paste brief and saved file
long-allhands: est_tokens, part count, evidence all parts mapped, brief and saved file
podcast: attach/paste brief and saved file
JSON file parses: yes / no / not run
Observed errors or truncated reads:
```

Current recorded answer: **ChatGPT ffprobe availability unknown; human check pending.** No Custom GPT output has been supplied for grading yet.
