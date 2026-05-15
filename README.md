# Klaviyo Agency Toolkit

Internal Digismoothie tooling for managing Klaviyo email marketing across 10+ ecommerce clients.

## Quick start

```bash
git clone <repo-url> klaviyo-agency-toolkit
cd klaviyo-agency-toolkit
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# get keys from agency secret manager, paste into .env
python scripts/smoke_test.py
```

## What it does

- **Audit:** flow performance vs industry benchmarks, per-message drilldown, Czech-market deliverability notes
- **Brand voice extract:** analyze sent campaign content to derive consistent style guide
- **Deliverability check:** DNS validation + inbox provider mix (seznam.cz, gmail, etc.)
- **ClickUp sync:** push audit findings as tasks to shared list `901515412227`
- **Weekly digest:** cross-client status report posted to team Slack

## Common commands

```bash
python scripts/smoke_test.py              # verify all 10 connections
python scripts/audit.py --client krekry_cz # audit one client
python scripts/audit.py --all              # audit all clients (parallel)
python scripts/weekly_digest.py            # Monday morning team digest
python scripts/clickup_sync.py --client krekry_cz --dry-run  # preview ClickUp push
```

## For Claude Code

Read `CLAUDE.md` first. It contains the full project context, architecture, conventions, and critical rules.

## Adding a team member

1. Add them to the private git repo
2. Share the secret bundle (1Password vault / signed file) with all 10 Klaviyo keys + ClickUp token
3. They follow Quick start above
4. Verify with `python scripts/smoke_test.py` → all 10 green

## Adding a new client

1. Edit `accounts.yml` — add entry with slug, display_name, env_var, locale, industry
2. Add the key to `.env` (and to agency secret manager)
3. `python scripts/smoke_test.py --client <new_slug>` to verify
4. `python scripts/audit.py --client <new_slug>` to generate first audit

## Security

- `.env` is gitignored. Never commit keys.
- Rotate any key that leaks into chat / screenshot / email immediately.
- The agency secret manager (1Password vault `agency/klaviyo`) is the source of truth for current keys.
- Audit reports in `outputs/` are also gitignored — they contain client data.
