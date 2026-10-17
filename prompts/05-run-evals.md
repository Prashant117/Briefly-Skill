# Prompt 5: Run evals, fix, and package

Read `prompts/00-spec.md`, `evals/expected.md` and `evals/trigger-queries.md`. Everything from Prompts 1–4 now exists.

## Task
1. **Script checks:** run `test_prep.py`, `make_long.py`, `make_media.sh`, then `prep.py` on every fixture with `time`. Record the times, est_tokens, parts and source for each.
2. **Brief quality (Claude):** with the `briefly` skill installed (`cp -r briefly ~/.claude/skills/`), produce a brief for each fixture in a fresh context. Grade each one against `expected.md`: MUST / MUST NOT / Format. Fixture 6 must go through the map-reduce path.
3. **Brief quality (ChatGPT):** if you can't operate ChatGPT, write `evals/chatgpt-manual-test.md`, a 10-minute checklist the human runs. Upload fixtures 1, 2, 5, 6 and 8, paste the outputs back, and you grade them. Also have the human confirm whether `ffprobe` exists in Code Interpreter (`!which ffprobe`), and record the answer.
4. **Trigger check:** for each query in `trigger-queries.md`, judge from the SKILL.md description alone whether it would trigger. Rewrite the description if any query is misclassified.
5. **Fix loop:** for every failure, fix the root cause (the rule wording in SKILL.md/instructions.md, or the parser in prep.py), re-run only the affected fixture, and repeat until it's green. Don't add rules for one-off model slips that don't reproduce.
6. **Package:**
   - `briefly.zip` (the `briefly/` folder at the zip root) for claude.ai → Settings → Capabilities → Skills → Upload.
   - Make sure `chatgpt/instructions.md` is still ≤ 8000 chars after the fixes.
   - `README.md` at the repo root, ≤ 40 lines: what it is, install for Claude Code / claude.ai / ChatGPT, and the optional `pip install faster-whisper`.

## `evals/RESULTS.md` format
| Fixture | Platform | MUST (x/y) | MUST NOT violations | Format | prep time | Notes |

Then: a list of the fixes made (file + one line each), and the remaining known limitations.

## Done when
Every MUST passes on Claude with 0 MUST NOT violations, the ChatGPT checklist exists (or has been graded), and the zip + README exist. Reply with the RESULTS.md table.
