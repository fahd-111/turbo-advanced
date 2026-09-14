---
name: commit
description: Prepare a commit. Runs the pre-commit checks, drafts a conventional commit message from the staged diff, and hands the command to the engineer to run. Claude never commits itself.
disable-model-invocation: true
allowed-tools: Read, Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(pnpm:*)
---

# Prepare a commit

You draft, the engineer commits. The hook blocks you from running git commit, so do not try.

## Steps
1. Run `git status` and `git diff --staged`. If nothing is staged, say so and stop. Do not stage files yourself.
2. Confirm `/review` has been completed for this change. If the engineer says no, stop and tell them to run `/review` first.
3. Run lint and typecheck on the changed files. If either fails, report it and stop.
4. Check the staged diff for anything that should not be committed: env files, credentials, real personal data, debug logging, commented-out code, files outside the task.
5. Draft one commit message in conventional format:
   - type: feat, fix, chore, refactor, test, docs
   - scope: the app or package touched
   - subject: under 70 characters, imperative, says what changed
   - body: one to three lines on why, only if the why is not obvious from the diff
6. If the staged changes cover more than one logical change, say so and suggest how to split them. Do not draft a single message for unrelated changes.

## Output
Findings from step 4, if any, then:

```
git commit -m "<type>(<scope>): <subject>" -m "<body>"
```

Tell the engineer to copy and run it. If they want the message changed, revise it. Nothing else.
