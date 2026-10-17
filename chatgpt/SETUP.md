# Set up Briefly

Use the same two canonical files on both platforms; do not maintain copied scripts or templates in this folder.

## Custom GPT

In an account that exposes the GPT builder, open **Explore GPTs → Create → Configure** (labels may vary by account).

1. Name: **Briefly**.
2. Description: **Turn transcripts and recordings into grounded English briefs with decisions, action items and timestamp references.**
3. Paste the complete contents of `instructions.md` into **Instructions**.
4. Add these **Knowledge** files from the repository:
   - `briefly/scripts/prep.py`
   - `briefly/references/template.md`
5. Turn **Code Interpreter & Data Analysis ON**. Turn **Web search OFF** and **Image generation OFF**. No Actions or external integrations are needed.
6. Add these conversation starters:
   - “Turn this meeting transcript into a brief with owners and due phrases.”
   - “Summarize this lecture video and list the assigned exercises.”
   - “Extract the key takeaways from these podcast or YouTube captions.”
   - “Brief this interview recording and capture any agreed follow-ups.”
7. Save privately and test in Preview before sharing.

Knowledge resources must be accessible as complete files to the Python tool. Test access to `prep.py` and `template.md` first; if the environment exposes only retrieval snippets, upload the original files in the chat. Do not recreate the script from snippets. Media works only with suitable local subtitle/transcription tools; when unavailable, provide a transcript. No model download or transcription service is required for text inputs.

OpenAI documents a transition of custom GPTs to plugins; builder availability depends on the account/workspace. This delivery retains the requested Custom GPT format. If creation is unavailable, keep these files for an existing editable GPT or a supported skills workflow; do not assume a local copy installs a ChatGPT plugin. See [OpenAI’s migration guide](https://learn.chatgpt.com/docs/migrate-custom-gpts) and [GPT customization overview](https://developers.openai.com/api/docs/actions/introduction). Setup instructions were reviewed on 18 October 2026; no account setup or publication was performed here.

## Claude

- Claude Code: copy the `briefly/` folder into your chosen project's `.claude/skills/` directory or your personal `~/.claude/skills/` directory. Keep the folder name `briefly`. Run Python 3.9 or later.
- claude.ai: upload the `briefly/` folder as a skill using the account's skill-upload interface; if it requires a ZIP, archive the folder with `briefly/SKILL.md` at the archive root. Enable code execution/file creation. The skill uses the environment's outputs folder.
- Local media: `ffprobe` and `ffmpeg` enable embedded subtitle extraction. Optional local audio transcription: `pip install faster-whisper` (model weights must be available). Neither dependency is required for transcript files.

## Test it

- Run `python3 briefly/scripts/test_prep.py` from the repository root; expect `OK`.
- Upload `evals/fixtures/team-sync.vtt`. Verify all seven headings, the final launch decision, the three assigned tasks, the unchanged phrase “by Thursday”, and a working `.brief.md` download containing the exact displayed brief (excluding its download-link line).
- Upload `lecture-youtube.vtt`; verify one homework task and no decisions.
- Upload `whisper.json`; verify English output, original names and a translation warning.
- Request JSON; download and parse it as JSON. Missing owners/due dates/refs are null and empty item sections are arrays.
- Test three inputs together; confirm individual files plus `rollup.brief.md`, with tasks grouped by owner and source references.
- For full grading, use `evals/expected.md` and the live-platform checklist in `evals/RESULTS.md`. Do not count a local script test as a Claude or Custom GPT quality test.
