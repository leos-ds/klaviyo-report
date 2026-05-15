---
name: klaviyo-deliverability-check
description: Diagnose deliverability problems for the connected Klaviyo client — validates DKIM, DMARC, and SPF for the sending domain, pulls actual open-rate breakdown by inbox provider (seznam.cz, gmail.com, atlas.cz, post.cz, email.cz, etc.), and flags providers where the client is silently bulk-foldered. Use when the user says "deliverability check", "zkontroluj doručitelnost", "DKIM check", "spam folder problem", "low open rate diagnosis", "email authentication", or whenever an audit flagged red open rates and the next step is root cause analysis. This is the skill to run when Cart/Checkout abandonment opens are anomalously low.
---

# Klaviyo Deliverability Check

Two-part diagnostic that catches the most common cause of low open rates on Czech ecommerce: misconfigured email authentication on the sending domain, combined with provider-specific bulk-foldering that Klaviyo doesn't surface in its standard reports.

## Workflow

### Step 1 — Identify the sending domain

Call `klaviyo_get_account_details`. Capture `defaultSenderEmail`. Extract the domain (after the `@`).

### Step 2 — DNS authentication check

Run these DNS lookups (use `dig` in bash, or fall back to `nslookup` / `python3 -c "import dns.resolver"`):

```bash
DOMAIN="krekry.cz"  # replace with extracted domain
echo "=== SPF ===" && dig +short TXT $DOMAIN | grep -i spf
echo "=== DMARC ===" && dig +short TXT _dmarc.$DOMAIN
echo "=== DKIM (Klaviyo selectors) ==="
for selector in klaviyo1 klaviyo2 k1 k2 km1 km2; do
  echo "  $selector._domainkey.$DOMAIN:"
  dig +short TXT $selector._domainkey.$DOMAIN
done
```

Interpret results against the rules in `references/dns_rules.md`. Flag every issue:

- **No SPF record** → critical, immediate fix
- **SPF includes Klaviyo (e.g. `include:_spf.klaviyo.com`)?** if missing → critical
- **DMARC missing** → high, install `p=none` to start collecting reports, target `p=quarantine` within 4-6 weeks
- **DMARC `p=none` but no `rua` reporting URI** → medium, no visibility
- **DMARC `p=quarantine` or `p=reject` already** → good, but check alignment (`adkim=s; aspf=s` is strict; `r` is relaxed)
- **No Klaviyo DKIM selector responding** → critical for deliverability; client domain is not authenticated on Klaviyo sends

### Step 3 — Inbox provider mix breakdown

Call `klaviyo_get_metrics` and find the metric ID for "Opened Email" (this is internal Klaviyo, not Shopify-integration).

Then call `klaviyo_query_metric_aggregates` with:

- `metricId`: Opened Email metric ID
- `measurements`: `["unique"]`
- `groupBy`: `["Email Domain"]`
- `interval`: `month`
- `startDate`: 90 days ago in ISO format (without Z suffix; use `timezone: "Europe/Prague"`)
- `endDate`: today in ISO format

Then call the same aggregate but for the metric "Received Email" (or fall back to "Email Sent" / "Delivered Email") to compute deliveries-by-domain.

Compute open rate per provider:
```
provider_open_rate = unique_opens_per_domain / unique_deliveries_per_domain
```

Sort providers by send volume descending. Surface the top 8.

### Step 4 — Flag silent bulk-foldering

For each provider, compare its open rate to that provider's expected baseline:

| Provider | Expected open rate (CZ ecommerce) |
|---|---|
| seznam.cz | 25-35% |
| email.cz | 25-35% |
| atlas.cz | 25-35% |
| centrum.cz | 22-32% |
| post.cz | 20-30% |
| gmail.com | 28-38% |
| googlemail.com | 28-38% |
| icloud.com / me.com | 30-40% |
| outlook.com / hotmail.com / live.com | 25-35% |
| firma email (others) | varies |

If a provider's actual is more than 15 percentage points below expected, flag as **silently bulk-foldered**. This is the "smoking gun" for low open rates that authentication doesn't fully explain.

### Step 5 — Output deliverability report

Write `<client>_deliverability.md` to outputs:

```markdown
# {{Client}} — Deliverability Check
> Date: {{ISO date}}

## Sending domain
- Domain: {{domain}}
- Sender: {{sender email}}

## Authentication (DNS)
| Record | Status | Value | Issue |
|---|---|---|---|
| SPF | ✅/❌ | ... | ... |
| DMARC | ✅/⚠️/❌ | p=... rua=... | ... |
| DKIM (Klaviyo) | ✅/❌ | selectors ... | ... |

## Inbox provider mix (last 90 days)
| Provider | Sends | Opens | Open rate | Expected | Verdict |
|---|---:|---:|---:|---:|---|
| seznam.cz | ... | ... | XX % | 25-35 % | ✅/⚠️/🚨 |
| ...

## Findings
- {{key issue 1}}
- {{key issue 2}}

## Fix order (ranked by impact)
1. **{{highest impact fix}}** — owner: client / agency, ETA: ...
2. ...

## Validation plan
After fixes ship, re-run this skill in 14 days. Expected lift: ...
```

### Step 6 — Suggest creating ClickUp tasks

If the user has the `klaviyo-clickup-sync` skill available and an environment variable `CLICKUP_API_TOKEN` is set, offer to convert the fix list into ClickUp tasks under the client's flows folder. Do not auto-create — ask first.

## Critical rules

- Never invent DNS results. If `dig` fails or returns empty, report exactly that. Do not assume "probably configured."
- Czech-market providers (seznam.cz, email.cz, atlas.cz) silently bulk-folder more aggressively than gmail. A provider showing 5 % open rate when it has 30 % of your sends is the highest-impact problem.
- Klaviyo uses two DKIM selectors by default (`klaviyo1`, `klaviyo2`). Some accounts use `km1`/`km2` after re-authentication. If neither pair returns a TXT, the domain is unauthenticated.
- DMARC `p=reject` without proper SPF + DKIM alignment will harm deliverability instead of helping. Walk before running: `p=none` → monitor `rua` reports → `p=quarantine pct=10` → ramp up.
- The skill produces a report only. Fixes ship via ClickUp tasks (if sync skill is enabled) or manually by the agency / client.
