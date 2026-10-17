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

## JSON mode

JSON mode, when the user asks for JSON: the same fields, with keys `title, content_type, duration, source, tldr, summary, key_points[{text,ref}], decisions[{text,ref}], action_items[{task,owner,due,ref}], next_steps[{text,ref}], open_questions[{text,ref}]`. Use `null` where the Markdown uses "—" or "Unassigned".

Use strings for title, content_type, source, tldr and summary; use a string or null for duration. Use arrays for all five item sections, with the object shapes above. Use strings for item text and task; use strings or null for ref, owner and due. Use null for missing refs and [] for empty item sections.
