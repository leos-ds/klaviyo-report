---
name: klaviyo-clickup-sync
description: Push Klaviyo audit findings, deliverability fixes, flow build tasks, and campaign briefs into ClickUp under Digismoothie's "Email marketing" space → client folder → flows/campaigns subfolders. Use when the user says "push to ClickUp", "create ClickUp tasks", "sync audit to ClickUp", "udělej tasky v ClickUpu", "vytvoř tasky pro [klient]", "převeď audit do ClickUp", or any phrase about converting an audit/brief into actionable ClickUp tasks. Auto-discovers the client folder structure on first run and persists the IDs.
---

# Klaviyo ClickUp Sync

Converts Klaviyo audit outputs (flow audit, deliverability check, content briefs) into ClickUp tasks under the Digismoothie agency's standard structure: **Email marketing space → {Client} folder → flows/campaigns subfolders**.

## Prerequisites

Set the ClickUp Personal API Token as an environment variable. Two acceptable patterns:

```bash
export CLICKUP_API_TOKEN="pk_xxxxxxxx_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

or pass it inline per-call. Never paste the token into chat output, file contents, or commit it to git. If the token is exposed (e.g. shared in chat), rotate it immediately at https://app.clickup.com/settings/apps.

## First-run discovery

On first invocation in a chat, run discovery to find IDs. Persist results to `<workspace>/.clickup_config.json` so subsequent runs are instant.

### Step 1 — Find team

```bash
curl -s -H "Authorization: $CLICKUP_API_TOKEN" "https://api.clickup.com/api/v2/team" | jq '.teams[] | {id, name}'
```

If multiple teams, prompt the user to pick one. Capture `team_id`.

### Step 2 — Find Email marketing space

```bash
curl -s -H "Authorization: $CLICKUP_API_TOKEN" "https://api.clickup.com/api/v2/team/{team_id}/space?archived=false" | jq '.spaces[] | {id, name}'
```

Match exactly `"Email marketing"` (case-insensitive). Capture `space_id`. If absent, halt and tell the user — do not create the space yourself.

### Step 3 — Find client folder

```bash
curl -s -H "Authorization: $CLICKUP_API_TOKEN" "https://api.clickup.com/api/v2/space/{space_id}/folder?archived=false" | jq '.folders[] | {id, name}'
```

Match the client name (e.g. `Krekry`). If multiple matches, prompt the user. Capture `folder_id` and `folder_name`.

### Step 4 — Find flows and campaigns lists

The folder contains lists. Find which lists correspond to flows vs campaigns:

```bash
curl -s -H "Authorization: $CLICKUP_API_TOKEN" "https://api.clickup.com/api/v2/folder/{folder_id}/list?archived=false" | jq '.lists[] | {id, name}'
```

Match by name (case-insensitive substring): `flow`, `campaign`. Capture `flows_list_id` and `campaigns_list_id`. If the folder has different naming, prompt the user once and remember.

### Step 5 — Persist config

Write `<workspace>/.clickup_config.json`:

```json
{
  "team_id": "...",
  "space_id": "...",
  "client": {
    "name": "Krekry",
    "folder_id": "...",
    "flows_list_id": "...",
    "campaigns_list_id": "..."
  },
  "discovered_at": "ISO timestamp"
}
```

On subsequent runs, read this file first; only re-discover if a key is missing or the user explicitly asks to re-discover.

## Task creation

### From a flow audit punch list

For each P1/P2/P3 item, create a ClickUp task in `flows_list_id`:

```bash
curl -s -X POST \
  -H "Authorization: $CLICKUP_API_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.clickup.com/api/v2/list/{flows_list_id}/task" \
  -d '{
    "name": "[P1] Cart Abandonment — fix open rate (15.9% vs 40% benchmark)",
    "description": "Audit found CA open rate ~60% below benchmark. Hypotheses: subject lines, send timing, deliverability. Per-message data attached.\n\n**Action items:**\n- A/B test subject lines (urgency vs personalization)\n- Verify send delay waterfall (1h / 4h / 24h)\n- Run deliverability check on krekry.cz domain\n\n**Source:** krekry_audit.md (90-day data, 2026-05-09)",
    "tags": ["digismoothie-audit", "p1", "cart-abandon"],
    "priority": 1,
    "due_date_time": null,
    "notify_all": false
  }' | jq '{id, name, url}'
```

Priority mapping:
- P1 → ClickUp priority `1` (urgent)
- P2 → `2` (high)
- P3 → `3` (normal)

Tag taxonomy:
- Always: `digismoothie-audit`
- Severity: `p1` / `p2` / `p3`
- Category: `cart-abandon` / `checkout-abandon` / `welcome` / `post-purchase` / `deliverability` / `naming-cleanup` / `replenishment` / `winback` / `browse-abandon`
- Source: `audit` / `deliverability-check` / `brand-voice`

### From a deliverability check

Create one task per RED/YELLOW finding. Always tag `deliverability`. Description must include the actual DNS lookup output (so the client / IT person can verify):

```
**Current state:**
- SPF: missing
- DMARC: present, p=none, no rua
- DKIM: only klaviyo1 selector responds; klaviyo2 missing

**Required fix:**
Add TXT record at klaviyo2._domainkey.krekry.cz with value provided in Klaviyo Settings → Domains → DNS records.

**Owner:** Krekry IT / domain registrar
**Validation:** Re-run deliverability check after 24h DNS propagation
```

### From a campaign brief

Create in `campaigns_list_id`. Include the full subject line, preview text, body angle, and proposed send time. Tag with the season (`christmas`, `easter`, `back-to-school`, `bf-cm`, etc.).

### Bulk creation

When pushing a multi-item audit, batch the calls but pause 200ms between them to avoid ClickUp rate limits (100 req/min for personal tokens).

## Output

After every push, return to the user:
- Number of tasks created per list
- ClickUp URL for the folder so they can review
- Any tasks that failed (with reason)

Example summary:

```
Pushed to ClickUp:
✅ 4 tasks → flows list (P1: 2, P2: 1, P3: 1)
✅ 2 tasks → campaigns list (Q3 seasonal hooks)

Review: https://app.clickup.com/t/{folder_id}
```

## Critical rules

- Never write the API token to any output file or chat message. Read from env var only.
- Never auto-create folders, lists, or spaces. If the expected structure is missing, halt and tell the user.
- Always show the user a preview of the tasks (titles + priorities) before pushing. Get explicit confirmation. Tasks are not free to undo.
- Idempotency: when re-running, check if a task with the same title already exists in the target list. If yes, update it (PUT) instead of creating a duplicate.
- Honor the agency's existing tag conventions if you discover them (call `list/{list_id}` and inspect existing tasks for tag patterns) before introducing new tags.
