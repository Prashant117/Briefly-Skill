# Prompt 3: ChatGPT Custom GPT version

Read `prompts/00-spec.md`, `briefly/SKILL.md`, `briefly/references/template.md` and `briefly/scripts/prep.py` first.

## Task
1. `chatgpt/instructions.md`: the text that goes in the GPT builder's **Instructions** field. **Hard limit: 8,000 characters**. Check it with `wc -c` and report the count.
2. `chatgpt/SETUP.md`: click-by-click setup.

## instructions.md requirements
It mirrors SKILL.md's behaviour, adapted for ChatGPT:
- **Pasted text** → extract directly.
- **Uploaded file** → ALWAYS use Code Interpreter. Never rely on retrieval or search over the file (it misses content). Steps:
  `!python /mnt/data/prep.py /mnt/data/<file> --out /mnt/data/out --part-tokens 15000`
  Then print each part **one at a time** and read every part before writing anything. (15k is lower than Claude's 20k because Code Interpreter truncates long stdout. If output appears truncated, re-print in smaller slices with Python string slicing.)
  Note: Knowledge files live under `/mnt/data/`. If `prep.py` isn't found there, locate it with `glob` first.
- Video without subtitles: Code Interpreter cannot run Whisper (no internet). Say so in one sentence and ask the user for a transcript, or tell them how to export one from Zoom/Teams/Meet/YouTube in one short line each.
- Map-reduce over 100k tokens: do it sequentially. Keep the per-part notes in a Python variable or file, not in chat.
- Rules D1–D9 verbatim (D9 on ChatGPT: save to `/mnt/data/<stem>.brief.md` and give a download link) (compress the wording only if needed to fit under 8,000 chars; never drop a rule).
- Template: "Use the template in `template.md` exactly." It's a Knowledge file, so don't paste it into the instructions unless the character budget allows.
- No preamble. The output is the brief.

## SETUP.md contents
- Name: `Briefly`. A one-line description. 4 conversation starters (meeting transcript, lecture video, podcast/YouTube captions, interview recording).
- Knowledge files to upload: `briefly/scripts/prep.py`, `briefly/references/template.md`.
- Capabilities: **Code Interpreter & Data Analysis ON**. Web search OFF. Image generation OFF.
- A "Test it" checklist: upload one fixture from `evals/fixtures/` and confirm the output matches the template headings.
- One paragraph: how to use the same `briefly/` folder in ChatGPT/Codex Skills, if the user's plan supports Skills (copy the folder; `SKILL.md` is the standard format).

## Done when
- `wc -c chatgpt/instructions.md` ≤ 8000. Reply with the count and the full instructions text.
