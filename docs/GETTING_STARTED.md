# Getting Started — for a Claude Code session

Read this first if you're a Claude Code agent picking up work in this repo.

## The 5-minute orientation

1. **What's built right now** (v0.1):
   - `lib/accounts.py` — loads `accounts.yml` + `.env`
   - `lib/klaviyo.py` — typed Klaviyo API client with rate-limit retries
   - `lib/benchmarks.py` — per-industry flow performance thresholds
   - `scripts/smoke_test.py` — verifies all 10 client connections
   - `scripts/audit.py` — runs audit per client or `--all`, writes markdown reports

2. **What's missing** (you may be asked to build):
   - `scripts/deliverability.py` — DNS + provider mix per client
   - `scripts/brand_voice.py` — extract brand voice from campaign content
   - `scripts/clickup_sync.py` — push audit findings to shared ClickUp list
   - `scripts/weekly_digest.py` — Monday cross-client digest + Slack post
   - `lib/clickup.py` — ClickUp API client (parallel to lib/klaviyo.py)
   - `lib/report_renderers.py` — extract markdown generation from audit.py

3. **The Cowork pilot** that bootstrapped this is documented in `docs/skills_reference/`. Each `.md` file there is the human workflow that should be ported to Python:
   - `client-onboarding.md` — first-touch setup per client
   - `flow-audit.md` — already implemented in `scripts/audit.py`
   - `brand-voice.md` — TODO
   - `deliverability.md` — TODO
   - `clickup-sync.md` — TODO

## Tasks you'll likely be asked

### "Implement deliverability.py"

Read `docs/skills_reference/deliverability.md` and `docs/dns_rules.md`. Then:
1. For DNS validation, use `dnspython` (add to requirements) and query SPF, DMARC, DKIM
2. For provider mix, use `KlaviyoClient.query_metric_aggregate` with `group_by=["Email Domain"]` against the "Opened Email" and "Received Email" metric IDs
3. Output markdown to `outputs/{slug}/deliverability_{date}.md`
4. Mirror the structure of `audit.py` (Click CLI, rich progress)

### "Build clickup_sync.py"

Read `docs/skills_reference/clickup-sync.md` and `docs/clickup_api_cheatsheet.md`. First-run discovery flow:
1. List teams → space "Email marketing" → folder matching client → lists "flows" and "campaigns"
2. Persist IDs to `outputs/{slug}/.clickup_config.json`
3. Parse most recent `audit_*.md` for action items (look for "P1", "P2", "P3" patterns in markdown)
4. For each, check shared list (901515412227 — in accounts.yml under clickup.shared_list_id) for existing task by title
5. If exists: update + post urgency comment if >7 days old
6. If missing: create

`--dry-run` flag is mandatory — prints what it would do without doing it.

### "Add a new client"

1. Edit `accounts.yml` — add entry under `accounts:`
2. Add env var to `.env`
3. Run `python scripts/smoke_test.py --client <new_slug>`
4. Run `python scripts/audit.py --client <new_slug>`

### "Fix a broken account"

Smoke test failed for client X. Steps:
1. Check `.env` — is the env var name right? (must match `env_var` in accounts.yml)
2. Verify the key in 1Password matches `.env`
3. If key is right but auth fails, check it in Klaviyo UI — may have been revoked
4. Generate a new key in Klaviyo Settings → API Keys, update `.env`, re-run smoke_test

## Hard rules

- **Never log API keys.** Even in error messages. Use `acc.mask()` from `lib/accounts.py`.
- **Always test on one client first.** Then `--all`.
- **Markdown reports must be readable by a PM, not a developer.** Lead with the worst finding.
- **Idempotency for ClickUp.** Never create duplicate tasks.
- **No async/await** in this codebase. Keep it simple sync HTTPX. 10 clients × few endpoints is not enough volume to need asyncio overhead.

## Tools you have

In Claude Code:
- Read/Write/Edit/Bash — full local filesystem access
- WebSearch / WebFetch — for Klaviyo / ClickUp API docs
- Pip can install anything in `.venv`
- Git for version control — commit each working slice

## Testing approach

No formal test suite yet (overkill for this volume). Verification pattern:
1. After implementing a script, run on `krekry_cz` first (has the most context)
2. Inspect the markdown output manually — does it make sense to a PM?
3. Run `--all` only after a single client looks right
4. Diff the report file against a saved "known good" version if you've run before

If you add a test suite later: pytest + httpx mock for Klaviyo client, real account only for smoke test.

## When in doubt

Read `CLAUDE.md` (root of repo). It has the system prompt and conventions.
The Cowork session that started this work has full context in `docs/skills_reference/` — those `.md` files are the "human design doc" for each workflow.
