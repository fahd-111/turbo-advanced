---
name: bug
description: Diagnose a bug. Read-only. Produces a cause report and proposed fix for the engineer to approve. Use for anything described as broken, failing, erroring or behaving wrongly.
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(git log:*), Bash(git diff:*), Bash(pnpm test:*), WebSearch, WebFetch
---

# Bug diagnosis

You are diagnosing, not fixing. Do not edit, write or create any file. If you find yourself about to, stop and finish the report instead.

## Steps
1. Restate the bug in one sentence and confirm you can reproduce it, or say exactly what you would need to reproduce it.
2. Trace the cause through the code. Read the actual files. Do not guess from names.
3. If the cause involves a library, framework behaviour, or anything you are not certain about, search the web and cite what you found. Prefer official docs and the library's GitHub issues.
4. Check whether the same cause exists elsewhere in the repo.

## Report format (always end with exactly this)
**Bug:** one line
**Root cause:** what is actually wrong and why it happens, with file and line references
**Why it was introduced:** best assessment, or "unknown"
**Proposed fix:** the smallest change that resolves the root cause. Name the files. No code yet
**Alternatives considered:** one or two, and why the proposed one is better
**Risk:** what else this fix could affect
**Regression test:** the test that should be added so this cannot come back (Verification Standard rule 5)
**Sources:** links if web research was used

Then stop and ask: "Approved to implement this fix, or do you want changes to the approach?"

Do not implement until the engineer says approved in a new message.

## After approval: implement in this order
1. Write the regression test named in the report. Run it. It must fail. If it passes before any fix, the diagnosis was wrong: stop, say so, and return to the report.
2. Implement the smallest fix from the report. Nothing else.
3. Run the regression test again. It must pass. Then run the full suite for the affected package. Nothing else may break.
4. Tell the engineer to run `/review`. The diff must contain both the fix and the test.

Never skip step 1. A test that would have passed anyway is worse than no test.
