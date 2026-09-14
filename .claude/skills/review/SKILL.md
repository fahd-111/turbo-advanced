---
name: review
description: Review the current diff against the Credminds Engineering Policy, then quiz the engineer so they understand every change before committing. Run after any implementation, before git commit.
disable-model-invocation: true
---

# Review before commit

Three parts, in order. The engineer commits by hand only after part 3.

## Part 1: Run the full test suite
Run `pnpm turbo test` for the whole workspace. If anything fails, report which tests and stop. There is no review of a red suite. The engineer fixes or asks you to fix, then runs `/review` again.

## Part 2: Self review of the diff
Run `git diff` and review it as a strict senior engineer would. Check:
- Does the change match the approved plan or fix, and nothing more
- For a feature, do the tests in the diff cover every item in the plan's Tests section. List anything missing
- Any new file, dependency, abstraction or config that was not in the plan
- Functions over 60 lines, unclear names, duplicated logic
- Secrets, real personal data, hardcoded values
- Missing env var in `.env.example` or README
- Missing or weak tests. For a bug fix this is a hard fail: if the diff has no test file, stop and say the fix cannot be reviewed until the regression test is added and shown to fail before the fix and pass after
- Anything that changes behaviour outside the task

Report findings as a list. Fix only what the engineer tells you to fix.

## Part 3: Reviewer walkthrough and quiz
Produce a short walkthrough of the diff, file by file, in plain language: what changed and why.

Then ask the engineer three questions about the change that they should be able to answer if they have read it. Pick the parts most likely to surprise them: a non-obvious line, an edge case, a reason for a choice. For example: "Why does the handler return early on line 42?" or "What happens if the user has no organisation?"

Wait for their answers. If an answer is wrong or missing, explain that part again and ask a follow-up. Do not say the review is complete until they have answered all three correctly.

End with: "Review complete. Run `/commit`."
