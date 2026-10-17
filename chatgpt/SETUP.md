# Set up Briefly

## Custom GPT

Use an account/workspace that exposes the GPT builder. Open **Explore GPTs → Create → Configure**; labels may vary by account.

1. Set **Name** to `Briefly`.
2. Set **Description** to: “Turn transcripts and recordings into grounded English briefs with decisions, action items and timestamp references.”
3. Open `chatgpt/instructions.md` and paste its entire contents into **Instructions**. Do not paste `SKILL.md` into this field.
4. Under **Knowledge**, upload the two canonical repository files:
   - `briefly/scripts/prep.py`
   - `briefly/references/template.md`
5. Under **Capabilities**, turn **Code Interpreter & Data Analysis ON**, **Web search OFF**, and **Image generation OFF**. Leave Actions/integrations unset.
6. Add these four **Conversation starters**:
   - “Turn this meeting transcript into a brief with decisions, owners and due phrases.”
   - “Summarize this lecture video and capture the assigned homework.”
   - “Extract takeaways and audience recommendations from these podcast or YouTube captions.”
   - “Brief this interview recording and capture any agreed follow-ups.”
7. Save privately. Open **Preview** and complete the checks below before sharing.

Knowledge resources must be readable as complete files by the Python tool. If only retrieval snippets are available, upload the original `prep.py` and `template.md` files in the chat. Keep one source copy of each in the repository; upload those same files to the GPT. Prepared transcripts/parts go to `/mnt/data/out`; completed briefs go to `/mnt/data/` with download links. Media without extractable subtitles needs a transcript: this workflow does not install Whisper or download models in Code Interpreter.

OpenAI documents a transition from custom GPTs to plugins; builder availability depends on the account/workspace. This package retains the requested Custom GPT format. If creation is unavailable, retain these files for an editable existing GPT or a supported Skills workflow. See [OpenAI's migration guide](https://learn.chatgpt.com/docs/migrate-custom-gpts). Reviewed on 18 October 2026; no account setup or publication was performed here.

## Test it

- Upload `evals/fixtures/team-sync.vtt` in Preview and ask for a brief. Confirm the Python tool ran `prep.py`, rather than summarizing retrieval snippets.
- Confirm these seven headings appear in order: **TL;DR**, **Summary**, **Key Points**, **Decisions**, **Action Items**, **Next Steps**, **Open Questions**.
- Confirm the final launch decision is Friday, Priya's due phrase remains “by Thursday”, and the log task remains Unassigned. Grade all four action items using `evals/expected.md`.
- Download `team-sync.brief.md`. Confirm its content matches the displayed brief, including any warning and excluding the final download-link line.
- Request JSON. Confirm the downloaded `.brief.json` parses, has the schema's fields, and uses null for missing owners/due dates/refs and [] for empty item sections.
- Upload `whisper.json`; confirm English output, original names and a translation warning. Upload `lecture-youtube.vtt`; confirm homework is captured without invented decisions.
- Submit three inputs together; confirm individual files plus `rollup.brief.md`, with tasks grouped by owner and source refs.
- For a no-subtitle recording, confirm the GPT asks for a transcript instead of inventing a brief. For full platform grading, use `evals/expected.md` and the checklist in `evals/RESULTS.md`.

## Use the same folder with ChatGPT/Codex Skills

If your plan and workspace support Skills, reuse the entire `briefly/` folder without changing its internal layout: `SKILL.md` is the standard Agent Skills entry point, and `scripts/` and `references/` travel with it. For Codex, copy the folder to the project's `.agents/skills/briefly/` directory (or an approved personal skill location); for ChatGPT, copy or import the same folder through the supported Skills interface. In ChatGPT desktop, open **Skills** in the sidebar to inspect available skills. Keep the canonical source folder here and test Python execution in the destination; the Custom GPT Instructions field is a separate setup route. See [OpenAI's Skills guide](https://learn.chatgpt.com/docs/build-skills).
