# AI Usage Documentation

## Tools Used

- **Claude (Claude Code, in VS Code)** – the AI assistant used throughout the project for planning, writing Flask routes and templates, reviewing my SQL, debugging, and testing.

## Key Prompts

1. "Can you provide me with a step-by-step list of tasks in order to complete this project."
2. "I already wrote schema.sql, can you check it?" (and again after I fixed the issues)
3. "Can you check my app.py"
4. "How can I make sure that it is already using mysql?" (after the dashboard showed the wrong count)
5. "I would like to change the styling to have a bit more personality…" followed by "Can you make the styling similar to something like this" with a screenshot of a dashboard design I liked.
6. Small UI requests: widen the status filter dropdown, make the Edit/Delete buttons the same width, and stack them vertically.

## What Worked Well

- **A task plan first.** Asking for an ordered list of tasks gave me a roadmap (database → CRUD → dashboard → Job Match → docs) that matched the course timeline.
- **Reviewing my own work.** Claude read my `schema.sql` and found two missing commas that would have stopped the script. It also suggested improvements I adopted: `NOT NULL` on foreign keys, a default status, and `DROP DATABASE IF EXISTS` so the script can be re-run.
- **Boilerplate-heavy CRUD.** Once Companies was done, the same pattern (list, add, edit, POST-only delete, shared add/edit form) carried over to the other three tables quickly.
- **Explaining and diagnosing problems.** When the dashboard showed 8 applications instead of 3, Claude inspected the database and found the `schema.sql` script had never actually been run against it, because `mysql` wasn't on my PATH. When the app "no longer opened", it found macOS's AirPlay Receiver was answering on port 5000 and that my Job Match and styling commit hadn't reached the branch I was on.
- **Testing as it built.** Each feature was checked with Flask's test client: invalid inputs, 404s, and the database state before and after.

## What I Changed / Decided

- **Wrote `schema.sql` myself** (the 4 tables, foreign keys, ENUMs, JSON columns, and sample data), then fixed the issues Claude flagged.
- **Chose the JSON shape** for `jobs.requirements` (`{"skills": [...], "experience": "..."}`) and kept it consistent between the Jobs form and Job Match.
- **Directed the design.** I asked for a livelier look and supplied a reference screenshot; the sidebar layout, frosted-glass cards and green palette came from that. I then asked for follow-up tweaks (dropdown width, button width, stacked Edit/Delete).
- **Ran the setup myself:** installed MySQL, created `.env` with my own password, re-ran `schema.sql`, and verified the dashboard.
- **Managed Git myself:** created the feature branches, committed the work, merged the pull requests, and approved the cherry-pick that recovered the styling commit.
- **Chose to change the port** to 5001 after the AirPlay conflict.

## Lessons Learned

- **Always test AI-written code.** It worked in tests but still needed checking in a real browser. The "8 vs 3" mismatch showed the database I was looking at wasn't the one I assumed. Confirming what the code actually talks to matters.
- **Review the AI's output for security and correctness.** Examples: SQL queries use `%s` parameters instead of string-building, delete routes accept POST only, passwords live in a git-ignored `.env`, and form input is validated on the server.
- **Environment problems aren't always code problems.** A missing PATH entry, a macOS service on port 5000, and being on the wrong Git branch all looked like "the app is broken".
- **Asking for explanations helps me learn.** Understanding *why* each fix worked (for example, MySQL returns JSON columns as strings, so the code has to `json.loads` them) made the code easier to maintain.
- **Keep commits organized.** Work that isn't committed to the right branch is easy to lose track of.
