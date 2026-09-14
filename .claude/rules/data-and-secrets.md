---
paths:
  - "**/*.env*"
  - "**/seed*"
  - "**/fixtures/**"
  - "**/migrations/**"
---
# Data, secrets and migrations

- Never write a real value into any .env file. Placeholders only in .env.example. Real values live in 1Password and Coolify.
- Seeds and fixtures use generated fake data. No real names, emails, phone numbers or client data.
- Migrations are append-only. Never edit a migration that has been merged. Create a new one.
- Any schema change must be listed in the plan before it is written.
