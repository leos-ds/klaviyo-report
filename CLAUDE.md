# Digismoothie Klaviyo Agency Toolkit — Claude Code Handoff

> This is the system prompt / context for Claude Code working on this repo.
> Read this completely before doing anything in this codebase.

## What this repo is

A Python toolkit for Digismoothie agency to manage Klaviyo email marketing across **10+ ecommerce clients** in parallel. Built to replace per-chat manual work in Cowork mode with scripted, scheduled, git-versionable workflows.

**Scope:**
- Cross-client flow performance audit (real metrics vs industry benchmarks)
- Brand voice extraction from sent campaigns
- Deliverability check (DNS + inbox provider mix)
- Sync findings to ClickUp shared task list
- Weekly agency digest

**Out of scope (for now):**
- Sending campaigns programmatically (Klaviyo UI stays the source of truth)
- Real-time monitoring (jobs run scheduled, not streaming)
- Klaviyo segment manipulation (read-only access pattern)

## Architecture summary

```
┌─────────────────┐    ┌──────────────────────┐    ┌────────────────┐
│ accounts.yml    │───▶│ Python scripts in    │───▶│ outputs/       │
│ (client list +  │    │  scripts/            │    │  per-client    │
│  ENV var names) │    │  - audit.py          │    │  markdown      │
└─────────────────┘    │  - deliverability.py │    │  reports       │
                       │  - brand_voice.py    │    └────────────────┘
┌─────────────────┐    │  - clickup_sync.py   │
│ .env (gitignore)│───▶│  - weekly_digest.py  │    ┌────────────────┐
│  KLAVIYO_*_KEY  │    │                      │───▶│ ClickUp tasks  │
│  CLICKUP_TOKEN  │    │ shared in lib/:      │    │ (901515412227) │
└─────────────────┘    │  - klaviyo.py        │    └────────────────┘
                       │  - clickup.py        │
                       │  - benchmarks.py     │
                       └──────────────────────┘
```

## Where I came from (context for Claude Code)

This toolkit was bootstrapped from a Cowork mode session that built a `digismoothie-klaviyo-ops` plugin (skills: client onboarding, flow audit, brand voice extract, deliverability check, ClickUp sync). The Cowork plugin works per-client-chat but doesn't scale to 10+ accounts because Cowork's Klaviyo MCP is one-account-per-chat.

The Cowork plugin's SKILL.md files are the **source of truth for what each workflow does**. They're copied into `docs/skills_reference/` in this repo for reference. When porting a skill to Python, read its SKILL.md first.

Key learnings from the Cowork pilot on Krekry.cz that the Python toolkit must encode:
- Industry benchmarks (food/beverage): Welcome 35 %+ open, Cart 40 %+, Checkout 45 %+, Post-purchase 40 %+
- Czech market deliverability: seznam.cz / email.cz are ~50-60 % of CZ ecom send volume and very sensitive to DKIM/DMARC misconfiguration
- Per-message drilldown is mandatory — flow-level averages mask the actual broken email
- LEADS vs CUSTOMERS segmentation typical in Klaviyo flows — performance varies dramatically

## Clients in scope

10 Klaviyo accounts as of May 2026. Each maps to an env var. **Never put the key value into a tracked file.**

| Slug | Display name | Env var | Locale | Industry |
|---|---|---|---|---|
| outdoorline | Outdoorline | `KLAVIYO_OUTDOORLINE_KEY` | CZ | Sports & Outdoor |
| lejaan_cz | Lejaan CZ | `KLAVIYO_LEJAAN_CZ_KEY` | CZ | Fashion |
| lejaan_sk | Lejaan SK | `KLAVIYO_LEJAAN_SK_KEY` | SK | Fashion |
| lejaan_pl | Lejaan PL | `KLAVIYO_LEJAAN_PL_KEY` | PL | Fashion |
| krekry_cz | Krekry CZ | `KLAVIYO_KREKRY_CZ_KEY` | CZ | Food & Beverage |
| krekry_com | Krekry.com | `KLAVIYO_KREKRY_COM_KEY` | EN | Food & Beverage |
| kruschiki | Kruschiki | `KLAVIYO_KRUSCHIKI_KEY` | PL? | Food & Beverage |
| kintsugi | Kintsugi | `KLAVIYO_KINTSUGI_KEY` | TBD | TBD |
| ourte | Ourte | `KLAVIYO_OURTE_KEY` | TBD | TBD |
| made_in_japan | Made in Japan | `KLAVIYO_MADE_IN_JAPAN_KEY` | CZ | Lifestyle/Retail |

Industry and locale fields are best-guess — confirm by calling `klaviyo_get_account_details` on first run per account and update `accounts.yml`.

The canonical mapping lives in `accounts.yml`. Always read accounts from there, never hardcode.

## Setup for a new team member

```bash
# 1. Clone
git clone <repo-url> klaviyo-agency-toolkit
cd klaviyo-agency-toolkit

# 2. Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Secrets
cp .env.example .env
# edit .env, get keys from agency secret manager (NOT from chat history)

# 4. Smoke test — verify all 10 connections work
python scripts/smoke_test.py
# Expected: 10 lines, each "✅ {client}: connected as {account_name}"
# Any FAIL means wrong key or revoked

# 5. Run first audit
python scripts/audit.py --client krekry_cz --timeframe 90d
# Output: outputs/krekry_cz/audit_2026-05-14.md
```

## Common tasks for Claude Code in this repo

### "Run audit for [client]"
Use `scripts/audit.py --client <slug>`. Reads `accounts.yml` for the slug, pulls flow_report from Klaviyo, computes grades vs `lib/benchmarks.py`, writes `outputs/<slug>/audit_<date>.md`.

### "Run audit for all clients"
`python scripts/audit.py --all`. Iterates accounts.yml, parallel up to 4 at a time (Klaviyo rate limit).

### "Push audit findings to ClickUp"
`python scripts/clickup_sync.py --client <slug> --from outputs/<slug>/audit_<date>.md`. Idempotent — checks if task with same title exists, updates instead of duplicating.

### "Weekly agency digest"
`python scripts/weekly_digest.py`. Runs audit on all clients, computes WoW deltas, identifies red flags, writes one digest markdown + posts to Slack channel `#email-marketing-team` if `SLACK_WEBHOOK_URL` is set.

### "Add a new client"
1. Edit `accounts.yml` — add new entry
2. Add key to `.env` (and to agency secret manager)
3. Run `python scripts/smoke_test.py --client <new_slug>` to verify
4. Run first audit: `python scripts/audit.py --client <new_slug>`

### "Update benchmarks"
Edit `lib/benchmarks.py`. Industry tiers: food_beverage, fashion, sports_outdoor, default. Each client in accounts.yml has an `industry` field that picks the benchmark set.

## Critical rules for Claude Code

1. **Never print or log API keys.** Read from `os.environ`, mask in any logs. Use `lib.klaviyo.Client(key)` which auto-masks the key in `__repr__`.

2. **Always check rate limits.** Klaviyo limits: 350 req/min steady, 700 req/min burst per account. The `lib.klaviyo.Client` wraps with backoff. If you write new endpoints, use the same wrapper.

3. **Idempotency for ClickUp.** Before creating a task, search the target list for a task with the same `name`. If exists, PUT (update) instead of POST.

4. **Markdown reports must be readable by non-technical PMs.** Lead with executive summary, then specific numbers, then action items. No JSON dumps, no log spam.

5. **Per-message drilldown is mandatory in audits.** Flow-level open rate is an average — fixes happen at the message level. Always include the per-message table in audit output.

6. **Czech / Slovak / Polish locale awareness.** Account locale (from `klaviyo_get_account_details`) determines report language and benchmark adjustments. CZ accounts: include seznam.cz/email.cz deliverability section. PL: include onet.pl/wp.pl/o2.pl.

7. **Never auto-execute destructive ops.** Pushing tasks to ClickUp = OK after preview. Modifying Klaviyo flows = never, this toolkit is read-only on Klaviyo.

8. **All scripts must accept `--dry-run`.** Especially `clickup_sync.py` — must print what it would do without doing it.

## Code conventions

- Python 3.11+
- Type hints everywhere (`from __future__ import annotations`)
- `httpx` for HTTP (sync mode, no asyncio overhead for this scale)
- `pydantic` v2 for data models (Klaviyo responses → typed structs)
- `rich` for CLI output (color-coded grades, progress bars)
- `pyyaml` for accounts.yml
- `python-dotenv` for .env loading
- Black format, ruff lint

## Repo layout

```
klaviyo-agency-toolkit/
├── CLAUDE.md                  ← this file (system prompt for Claude Code)
├── README.md                  ← team onboarding (short)
├── accounts.yml               ← canonical client list
├── .env.example               ← template
├── .env                       ← real keys, GITIGNORED
├── .gitignore
├── requirements.txt
├── lib/
│   ├── __init__.py
│   ├── klaviyo.py             ← API client with rate limit + masking
│   ├── clickup.py             ← API client
│   ├── benchmarks.py          ← industry benchmark thresholds
│   ├── grading.py             ← grade(value, benchmark) → green/yellow/red
│   └── accounts.py            ← loads accounts.yml + env vars
├── scripts/
│   ├── smoke_test.py
│   ├── audit.py
│   ├── deliverability.py
│   ├── brand_voice.py
│   ├── clickup_sync.py
│   └── weekly_digest.py
├── outputs/                   ← per-client reports, GITIGNORED
│   └── {client_slug}/
│       └── audit_YYYY-MM-DD.md
└── docs/
    ├── skills_reference/      ← copied SKILL.md files from Cowork plugin
    ├── benchmarks_2025.md
    └── deliverability_notes.md
```

## When you're stuck

1. Read the relevant SKILL.md in `docs/skills_reference/` — it has the human-readable workflow
2. Check Klaviyo API docs: https://developers.klaviyo.com/en/reference/api_overview
3. Test against a single account with `--dry-run` before running across all 10
4. Print intermediate state to terminal generously; `rich.print` is your friend

## Roadmap (informational, not a backlog)

- v0.1 (now): smoke test, audit per client, audit --all
- v0.2: deliverability.py with provider mix + DNS check
- v0.3: brand_voice.py with campaign content extraction
- v0.4: clickup_sync.py with idempotent task push
- v0.5: weekly_digest.py with Slack post
- v0.6: scheduled via cron / GitHub Actions
- v1.0: static HTML dashboard generated nightly, served from S3 / Cloudflare Pages for non-CLI team members
