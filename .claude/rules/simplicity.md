# Simplicity

Over-engineering is the most common way Claude-written code fails review at Credminds. These are hard rules.

- Solve the stated problem only. No handling of cases nobody asked for.
- Before writing anything new, search the repo for an existing pattern and use it, even if you would have designed it differently.
- No new abstraction (helper, base class, generic wrapper, factory) until the same logic exists in at least two places.
- No new dependency without a line in the plan explaining why it cannot be written in roughly 10 lines.
- No new config options, feature flags, or environment variables unless the task requires them.
- No comments that restate the code. Comment only the why.
- Do not refactor, rename or reformat code outside the files the task touches. Suggest it as a separate task instead.
- If the diff is growing past roughly 300 lines, stop and tell the engineer before continuing.
- When two approaches are equal, choose the one with fewer files and fewer moving parts.
- Do not add error handling for errors that cannot happen. Do add it for network, filesystem, database and user input.
