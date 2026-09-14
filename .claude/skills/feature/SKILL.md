---
name: feature
description: Plan a new feature. Engineer explains the feature and their implementation idea, Claude researches and returns a plan for approval. No code until approved.
disable-model-invocation: true
---

# Feature planning

The engineer will describe the feature and how they think it should be built. Your job is to turn that into a plan they can approve, not to start building.

## Steps
1. Read the engineer's description. Ask up to three clarifying questions if anything is ambiguous. Wait for answers.
2. Explore the repo first: find existing patterns, packages and components this should reuse. List them.
3. Research: search the web for how this is typically implemented with our stack, known pitfalls, and whether a maintained library already does it. Cite sources.
4. Compare the engineer's approach with what you found. If you disagree, say so plainly and why.

## Plan format (always end with exactly this)
**Feature:** one line
**Approach:** the simplest design that works, in plain language
**Files to change or create:** each with one line on what changes
**Reuses:** existing code in the repo this builds on
**New dependencies:** none, or each one with why it cannot be written in a few lines
**Data changes:** schema or migration changes, if any
**Tests:** what will be tested and how
**Out of scope:** what this deliberately does not do
**Open questions:** anything the engineer must decide
**Sources:** links used

Then stop and ask: "Approve this plan, or what should change?"

Do not write code until the engineer approves in a new message.

## After approval: implement in this order
1. Implement the feature following the plan. If the plan turns out to be wrong, stop and say so rather than improvising.
2. Write the tests listed in the plan's Tests section, no more and no fewer. New logic (pricing, permissions, calculations, data transforms) gets unit tests. New endpoints get an API test. New user-facing flows on a core path get a smoke test.
3. Run the suite for the affected packages. Everything passes.
4. Tell the engineer to run `/review`. The diff must contain the tests from the plan.
