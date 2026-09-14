---
name: deploy
description: Guided deployment to a client VPS following the Credminds Deployment Policy. Claude never connects to the server. It gives the engineer each command to copy and run, checks the output, and only produces the completion message after public health checks pass.
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(pnpm:*), Bash(git status:*), Bash(git branch:*), Bash(curl:*), Bash(openssl s_client:*), Bash(dig:*)
---

# Guided deployment

You are a guide, not an operator. You never run ssh, scp, or any command on the client's server. You give the engineer one step at a time, with the exact command to copy and paste into their own terminal, then wait for their output before moving on. If you find yourself about to connect to a remote machine, stop.

Never ask for, read, or echo credentials. The engineer pulls them from 1Password themselves.

## Phase 0: Preflight (local repo only)
Check and report each, stop if any fail:
1. `docker-compose` files exist for staging and production
2. `.env.example` exists and lists every variable the app reads
3. `pnpm turbo build` passes
4. Working tree is clean and the branch is `staging` or `main`

Then ask for: client name, VPS IP, staging domain, production domain. Use these to fill in every command below. Do not proceed without all four.

## Phase 1: VPS preparation
Present each block, wait for pasted output or confirmation, compare it to what is expected before the next block.
1. SSH login line (engineer runs it, you never do)
2. Ubuntu version check. Expected: LTS 20.04, 22.04 or 24.04. Anything else: stop and tell them to consult the Senior
3. System update
4. Firewall: ssh, 80, 443, 8000, then enable. Ask them to paste the status output

## Phase 2: Coolify
5. Coolify install command. Ask for the last lines of output
6. Dashboard URL on port 8000. Confirm: admin account created with client or Credminds email, credentials saved to 1Password. Wait for yes
7. Confirm: deployment target Localhost, project created with the client name. Wait for yes
8. Confirm: Servers, localhost, Proxy set to None. Wait for yes. Explain why: nginx handles public traffic, two proxies conflict

## Phase 3: nginx and SSL
9. nginx and certbot install command. Ask for `systemctl status nginx` output, expected active
10. Generate the two nginx server blocks with the real domains and container ports filled in. Tell them the file paths in sites-available and the symlink commands
11. `nginx -t`. Do not continue until they paste a successful test
12. Ask them to confirm the client has pointed both A records to the VPS IP. You may verify from here with `dig` on the public domains
13. certbot command with both domains. Ask for the output

## Phase 4: Connect repo and deploy
14. Confirm: GitHub source added in Coolify using the Credminds org app, repo authorised, both branches visible. Wait for yes
15. Staging resource: Docker Compose, staging branch, staging compose file, name `<client>-staging`. Wait for yes
16. Environment variables: list every key from `.env.example` so nothing is skipped. Tell them to mark secrets as Secret. Do not ask for values. Wait for yes
17. Deploy staging. Ask for the final build log lines
18. Repeat 15 to 17 for production with the main branch and production env vars
19. Demo data: staging is seeded by default. Production is seeded only if the client asked for it. Ask which applies and record the answer

## Phase 5: Verify from outside
Run these yourself from the local machine, against the public domains only:
- `curl` the health route on staging and production. Expected: OK, no missing env vars reported
- Check the certificate on both domains is valid and not self-signed
- Both URLs load over HTTPS

If any check fails, say which one, explain the likely cause, and give the engineer the next command to run themselves. Do not produce the completion message.

## Phase 6: Handoff message
Only after every Phase 5 check passes, confirm credentials are all in the client's 1Password vault (SSH, Coolify admin, database, third-party keys, domain registrar if applicable), then generate:

```
Deployment complete.
Staging: https://<staging domain>
Production: https://<production domain>
Coolify dashboard: http://<vps ip>:8000
All credentials saved in 1Password vault: <vault name>
Demo data seeded on staging: Yes. Production: <Yes or No>
Health checks: passed on both environments at <time>
```

Tell the engineer to post it in the project Slack channel. The PM takes over from there.

## If a deploy goes wrong
Do not troubleshoot on production. Give the engineer the rollback instruction from the Deployment Policy: Coolify, Deployments tab, redeploy the last working version, verify the public URL, notify the PM. Then debug on staging.

## When to send them to the Senior
Ubuntu is not LTS, Coolify install fails, proxy setting is unclear, GitHub source will not connect, compose build fails for more than 30 minutes, nginx test fails twice, certbot fails, or anything has been stuck for an hour. Say so plainly and stop.
